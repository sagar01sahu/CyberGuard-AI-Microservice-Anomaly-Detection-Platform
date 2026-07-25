"""
main.py

FastAPI orchestration layer wrapping the HGNN anomaly detector
(Sub-Problem 3.1) and the Federated cold-start evaluator
(Sub-Problem 3.2) behind a single POST /predict endpoint consumed by
the Spring Boot backend (Sub-Problem 2).

Run locally with:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from typing import Dict

import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from schemas import ErrorResponse, LogPayload, PredictionResponse
from graph_builder import CyberGraphBuilder
from hgnn_model import SecurityHGNN
from anomaly_detector import AnomalyDetector
from federated_aggregator import FederatedPeerAggregator
from cold_start import ColdStartEvaluator, BaselineTransitioner, PEER_EMBEDDING_DIM

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("anomaly-api")

app = FastAPI(
    title="Cybersecurity Anomaly Detection Engine",
    description="HGNN + Federated cold-start anomaly scoring service.",
    version="1.0.0",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from train_hgnn import train_security_hgnn, MODEL_SAVE_PATH

# Track runtime stats
MODEL_STATS = {
    "is_trained": False,
    "last_trained": None,
    "loss_history": [],
    "total_predictions": 0,
    "predictions_cold_start": 0,
    "predictions_hgnn": 0,
}

hgnn_model = SecurityHGNN(hidden_channels=32, out_channels=PEER_EMBEDDING_DIM)
_PEER_BASELINE_CACHE: Dict[str, Dict[str, torch.Tensor]] = {}

if os.path.exists(MODEL_SAVE_PATH):
    try:
        hgnn_model.load_state_dict(torch.load(MODEL_SAVE_PATH))
        logger.info(f"Loaded trained SecurityHGNN checkpoint from {MODEL_SAVE_PATH}")
        MODEL_STATS["is_trained"] = True
    except Exception as e:
        logger.warning(f"Could not load checkpoint from {MODEL_SAVE_PATH}: {e}")

# Pre-train baseline on startup if needed so model status and baselines are fully populated
try:
    logger.info("Initializing startup training & baseline calculation for HGNN...")
    trained_model, baselines, loss_hist = train_security_hgnn(epochs=10)
    hgnn_model = trained_model
    _PEER_BASELINE_CACHE = baselines
    from datetime import datetime
    MODEL_STATS["is_trained"] = True
    MODEL_STATS["last_trained"] = datetime.now().isoformat()
    MODEL_STATS["loss_history"] = loss_hist
    logger.info("Startup HGNN training and baseline calculation completed successfully.")
except Exception as e:
    logger.warning(f"Startup HGNN training failed: {e}")

hgnn_model.eval()

anomaly_detector = AnomalyDetector(hgnn_model)
peer_aggregator = FederatedPeerAggregator()
cold_start_evaluator = ColdStartEvaluator()
baseline_transitioner = BaselineTransitioner()

COLD_START_LOG_THRESHOLD = 5


def _get_peer_baseline(role: str) -> Dict[str, torch.Tensor]:
    if role not in _PEER_BASELINE_CACHE:
        logger.warning(
            "No cached federated peer baseline for role='%s'; using neutral "
            "zero-mean/unit-std defaults.",
            role,
        )
        _PEER_BASELINE_CACHE[role] = {
            "mean": torch.zeros(PEER_EMBEDDING_DIM),
            "std": torch.ones(PEER_EMBEDDING_DIM),
        }
    return _PEER_BASELINE_CACHE[role]


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={500: {"model": ErrorResponse}},
)
async def predict(payload: LogPayload) -> PredictionResponse:
    """
    Routes an incoming event to either:
      - ColdStartEvaluator, if the entity has < 5 historical logs, or
      - AnomalyDetector (HGNN), if it has >= 5 historical logs.

    Input  (JSON body): LogPayload
        {
          "current_event": { ...LogEvent fields... },
          "historical_logs": [ up to 5 LogEvent objects ]
        }

    Output (JSON body): PredictionResponse
        {
          "risk_score": 0.0-1.0,
          "anomaly_type": "None" | "Impossible Travel" | "Lateral Movement" |
                           "Device Spoofing" | "Brute Force" | "Cold-Start Deviation",
          "explainability": "human-readable reason string"
        }
    """
    try:
        current = payload.current_event.model_dump()
        historical = [log.model_dump() for log in payload.historical_logs]
        log_count = len(historical)

        MODEL_STATS["total_predictions"] += 1
        
        # Fast heuristic pre-checks (Always run these first regardless of log count if history exists)
        local_builder = CyberGraphBuilder()
        detector = AnomalyDetector(hgnn_model, graph_builder=local_builder)
        heuristic_res = None
        for check in (detector._check_impossible_travel, detector._check_device_spoofing, detector._check_brute_force):
            res = check(historical, current)
            if res is not None:
                heuristic_res = res
                break
        
        if heuristic_res is not None:
            MODEL_STATS["predictions_hgnn"] += 1
            logger.info("entity_id=%s flagged by heuristic rule: %s", current["entity_id"], heuristic_res["anomaly_type"])
            result = heuristic_res
        elif log_count < COLD_START_LOG_THRESHOLD:
            MODEL_STATS["predictions_cold_start"] += 1
            logger.info(
                "entity_id=%s routed to ColdStartEvaluator (log_count=%d)",
                current["entity_id"], log_count,
            )
            baseline = _get_peer_baseline(current.get("role", "UNKNOWN"))
            result = cold_start_evaluator.evaluate_new_user(
                incoming_log=current,
                global_peer_tensor=baseline["mean"],
                peer_std_tensor=baseline["std"],
            )
        else:
            MODEL_STATS["predictions_hgnn"] += 1
            logger.info(
                "entity_id=%s routed to AnomalyDetector/HGNN (log_count=%d)",
                current["entity_id"], log_count,
            )
            historical_graph = local_builder.build_historical_graph(historical)
            result = detector.score_incoming_event(
                hgnn_model=hgnn_model,
                historical_graph=historical_graph,
                historical_logs=historical,
                incoming_log=current,
            )

        return PredictionResponse(**result)

    except (KeyError, ValueError, RuntimeError) as exc:
        logger.exception("Model inference failed for entity_id=%s", payload.current_event.entity_id)
        raise HTTPException(status_code=500, detail=f"Inference error: {type(exc).__name__}: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error scoring event.")
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {type(exc).__name__}: {exc}") from exc


@app.get("/model/status")
async def get_model_status() -> Dict[str, object]:
    """Returns current HGNN model training state, parameter counts, and prediction stats."""
    param_count = sum(p.numel() for p in hgnn_model.parameters())
    return {
        "status": "ok",
        "is_trained": MODEL_STATS["is_trained"],
        "architecture": "2-Layer Heterogeneous GraphSAGE",
        "total_parameters": param_count,
        "peer_embedding_dim": PEER_EMBEDDING_DIM,
        "cached_roles": list(_PEER_BASELINE_CACHE.keys()),
        "last_trained": MODEL_STATS["last_trained"],
        "loss_history": MODEL_STATS["loss_history"],
        "total_predictions": MODEL_STATS["total_predictions"],
        "predictions_cold_start": MODEL_STATS["predictions_cold_start"],
        "predictions_hgnn": MODEL_STATS["predictions_hgnn"],
    }


@app.post("/model/train")
async def trigger_training(epochs: int = 20) -> Dict[str, object]:
    """Triggers self-supervised training for SecurityHGNN and recalculates federated peer baselines."""
    global hgnn_model, _PEER_BASELINE_CACHE
    try:
        logger.info(f"Triggering HGNN model training for {epochs} epochs...")
        trained_model, baselines, loss_hist = train_security_hgnn(epochs=epochs)
        hgnn_model = trained_model
        hgnn_model.eval()
        _PEER_BASELINE_CACHE = baselines

        from datetime import datetime
        MODEL_STATS["is_trained"] = True
        MODEL_STATS["last_trained"] = datetime.now().isoformat()
        MODEL_STATS["loss_history"] = loss_hist

        return {
            "status": "success",
            "message": f"SecurityHGNN trained successfully for {epochs} epochs.",
            "final_loss": loss_hist[-1] if loss_hist else 0.0,
            "loss_history": loss_hist,
            "roles_trained": [r for r in baselines.keys() if r != "UNKNOWN"],
        }
    except Exception as exc:
        logger.exception("Failed to train HGNN model")
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}") from exc


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "prediction_failed", "detail": str(exc.detail)},
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

