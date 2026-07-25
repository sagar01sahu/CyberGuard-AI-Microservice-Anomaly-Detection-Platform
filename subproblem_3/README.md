# Sub-Problem 3 — AI Anomaly Detection Engine (Python / FastAPI)

Implements all three parts:
- **3.1** `graph_builder.py`, `hgnn_model.py`, `anomaly_detector.py` — Heterogeneous GNN detector
- **3.2** `federated_aggregator.py`, `cold_start.py` — Federated peer-group cold-start
- **3.3** `schemas.py`, `main.py` — FastAPI orchestrator exposing `POST /predict`

## Run it

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Exact input contract (what Spring Boot must send)

`POST http://localhost:8000/predict`

```json
{
  "current_event": {
    "entity_id": "user_4589",
    "role": "MARKETING",
    "auth_method": "password",
    "auth_status": "success",
    "timestamp": "2026-07-25T08:15:00.000Z",
    "source_ip": "45.33.20.11",
    "geo_location": { "lat": 52.5200, "lon": 13.4050 },
    "device_id": "macbook_pro_m2_xyz",
    "os_version": "macOS 14",
    "user_agent": "Chrome/114.0",
    "resource_accessed": "/api/v1/finance/payroll_2026.csv"
  },
  "historical_logs": [
    { "...": "up to 5 prior LogEvent objects, same shape, oldest first" }
  ]
}
```

Required per-log fields: `entity_id, auth_method, auth_status, timestamp, source_ip, geo_location{lat,lon}, device_id, os_version, user_agent, resource_accessed`.
`role` is optional (defaults to `"UNKNOWN"`) — **I'd recommend adding `role` to the AccessLog entity in Sub-Problem 2 and to the ingestion DTO in Sub-Problem 1**, since both the HGNN's User node feature and the federated cold-start peer-grouping depend on it. Right now Sub-Problem 1/2's schemas don't carry `role` on the wire — only `UserProfile` has it internally — so this is the one change you need to backport.

### Routing logic (handled internally by `main.py`, mirrors Sub-Problem 3.3 spec)
- `len(historical_logs) < 5` → `ColdStartEvaluator` (federated peer baseline)
- `len(historical_logs) >= 5` → `AnomalyDetector` (personal HGNN baseline)

## Exact output contract (what Spring Boot receives back)

```json
{
  "risk_score": 0.9231,
  "anomaly_type": "Lateral Movement",
  "explainability": "Accessing '/api/v1/finance/payroll_2026.csv' shifted the user's structural behavioral embedding by a cosine distance of 0.923, exceeding the 0.85 baseline-deviation threshold."
}
```

- `risk_score`: float in `[0.0, 1.0]`
- `anomaly_type`: one of `"None"`, `"Impossible Travel"`, `"Lateral Movement"`, `"Device Spoofing"`, `"Brute Force"`, `"Cold-Start Deviation"`
- `explainability`: human-readable string — Spring Boot should store this straight into `RiskAlert.explainabilityFactors` (wrap it as a 1-element list, or extend the entity to store a single string if you'd rather not force it into a list)

On failure (bad payload, tensor shape mismatch, model error), the server returns **HTTP 500** with:
```json
{ "error": "prediction_failed", "detail": "Inference error: ..." }
```
This matches the shape your Sub-Problem 2 `try/catch` around the WebClient call expects, so it can fall back to `"pending_analysis"` cleanly.

## What each attack type is detected by

| Attack Type | Detection mechanism | Module |
|---|---|---|
| Impossible Travel | Haversine distance / time between last two logins | `anomaly_detector.py` |
| Device Spoofing | Unseen `device_id` + unseen `os_version` mid-session | `anomaly_detector.py` |
| Brute Force | ≥3 prior `auth_status=failure` + current failure | `anomaly_detector.py` |
| Lateral Movement | HGNN cosine-distance spike (novel Resource edge) | `hgnn_model.py` + `anomaly_detector.py` |
| Cold-start anomalies (any type, new user) | 3-sigma deviation from federated peer-group projection | `cold_start.py` |
| Credential Stuffing | **Not detectable from a single entity's graph** — it's a cross-entity, same-source-IP pattern. This needs a stateful, windowed check across many `entity_id`s sharing one `source_ip`. Recommend doing this in Spring Boot (a `sourceIp` + time-window count query) or a separate streaming job, not per-event in this service. |
| Low-and-Slow Exfiltration | **Needs long-window aggregation** (many small accesses over hours/days) — a single-event/5-log API call can't see that pattern. Recommend a scheduled batch job in Spring Boot/Postgres that flags entities with abnormal *cumulative* access counts to sensitive resources over a rolling 24–72h window, independent of this real-time `/predict` call. |

**This is the important thing to change upstream:** Sub-Problem 2's `LogProcessingService` is currently designed as a pure per-event synchronous pipeline (log in → call AI → get score). That's correct for the first 4 attack types above, but Credential Stuffing and Low-and-Slow Exfiltration are structurally cross-event/cross-entity patterns that no single `/predict` call can see. You'll want a second, async batch/streaming detector in Sub-Problem 2 (e.g. a `@Scheduled` job querying `AccessLogRepository` with GROUP BY windows) for those two, rather than trying to force them through this endpoint.

## Notes on production-readiness gaps (be aware before you wire this up)

1. **The HGNN is untrained** in `main.py` (`SecurityHGNN(...)` gets random init weights). There's no training loop in the spec — you'll need to add one (self-supervised, e.g. contrastive loss between normal-session subgraphs) before `risk_score` numbers are meaningful. Right now it will run and return well-formed output, but the actual anomaly signal is noise until trained.
2. **The federated peer-baseline cache (`_PEER_BASELINE_CACHE`) is in-memory and empty on startup** — every role falls back to a neutral zero-mean/unit-std baseline until you build the offline job that runs `FederatedPeerAggregator` over your 500 synthetic users per role and populates it (Redis or a Postgres table read on startup would both work).
3. Both gaps are intentionally left as clearly-marked seams (`# NOTE:` / `# In production` comments in `main.py`, `cold_start.py`) rather than silently faked, so you know exactly what to plug in next.
