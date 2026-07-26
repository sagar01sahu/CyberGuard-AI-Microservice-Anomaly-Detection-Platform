

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Optional

import torch


PEER_EMBEDDING_DIM = 16

STD_DEV_THRESHOLD = 3.0


def _hour_of_day(timestamp: str) -> int:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
    except (ValueError, AttributeError):
        return 12  # neutral fallback


def _ip_network_type(source_ip: str) -> str:

    private_prefixes = ("10.", "172.16.", "192.168.")
    if any(source_ip.startswith(p) for p in private_prefixes):
        return "internal"
    return "external"


def _uri_bucket(uri: str) -> float:

    digest = hashlib.sha256(uri.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def _project_log_features(incoming_log: Dict, dim: int = PEER_EMBEDDING_DIM) -> torch.Tensor:

    hour = _hour_of_day(incoming_log.get("timestamp", ""))
    net_type = _ip_network_type(incoming_log.get("source_ip", ""))
    uri_val = _uri_bucket(incoming_log.get("resource_accessed", "/unknown"))

    hour_norm = hour / 23.0
    net_val = 1.0 if net_type == "external" else 0.0

    seed = f"{hour_norm:.4f}_{net_val}_{uri_val:.4f}"
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    vals = [(digest[i % len(digest)] / 127.5) - 1.0 for i in range(dim)]
    return torch.tensor(vals, dtype=torch.float32)


class ColdStartEvaluator:


    def evaluate_new_user(
        self,
        incoming_log: Dict,
        global_peer_tensor: torch.Tensor,
        peer_std_tensor: Optional[torch.Tensor] = None,
    ) -> Dict[str, object]:

        dim = global_peer_tensor.shape[0]
        std = peer_std_tensor if peer_std_tensor is not None else torch.ones(dim)
        std = torch.clamp(std, min=1e-4)  # guard divide-by-zero for tight peer groups

        projected = _project_log_features(incoming_log, dim=dim)  # [embedding_dim]

        # Per-dimension z-score: how many peer-group standard
        # deviations the new event's projected features sit from the
        # federated peer mean.
        z_scores = (projected - global_peer_tensor) / std          # [embedding_dim]
        max_abs_z = torch.max(torch.abs(z_scores)).item()

        role = incoming_log.get("role", "UNKNOWN")

        if max_abs_z > STD_DEV_THRESHOLD:
            risk_score = min(1.0, 0.7 + (max_abs_z - STD_DEV_THRESHOLD) * 0.05)
            hour = _hour_of_day(incoming_log.get("timestamp", ""))
            resource = incoming_log.get("resource_accessed", "unknown resource")
            return {
                "risk_score": round(risk_score, 4),
                "anomaly_type": "Cold-Start Deviation",
                "explainability": (
                    f"New entity (role={role}) has no personal history yet. Action "
                    f"deviated significantly from the federated baseline for {role} "
                    f"peers: accessing '{resource}' at hour {hour} produced a "
                    f"{max_abs_z:.2f}-sigma deviation from the peer-group mean, "
                    f"exceeding the {STD_DEV_THRESHOLD}-sigma cold-start threshold."
                ),
            }

        return {
            "risk_score": round(min(1.0, max_abs_z / STD_DEV_THRESHOLD), 4),
            "anomaly_type": "None",
            "explainability": (
                f"New entity (role={role}) behavior is within {max_abs_z:.2f} sigma "
                f"of the federated peer baseline for its role; consistent with "
                f"cold-start expectations."
            ),
        }


class BaselineTransitioner:


    COLD_START_MAX = 5   # < 5 logs => 100% federated
    STABLE_MIN = 50       # > 50 logs => 100% personal HGNN

    def calculate_confidence(self, user_log_count: int) -> float:

        if user_log_count < self.COLD_START_MAX:
            return 0.0
        if user_log_count > self.STABLE_MIN:
            return 1.0
        span = self.STABLE_MIN - self.COLD_START_MAX  # 45
        progressed = user_log_count - self.COLD_START_MAX
        return round(progressed / span, 4)

    def blend_scores(self, federated_result: Dict, personal_result: Dict, user_log_count: int) -> Dict:

        personal_weight = self.calculate_confidence(user_log_count)
        federated_weight = 1.0 - personal_weight

        blended_score = (
            federated_weight * federated_result["risk_score"] + personal_weight * personal_result["risk_score"]
        )
        dominant = personal_result if personal_weight >= federated_weight else federated_result

        return {
            "risk_score": round(blended_score, 4),
            "anomaly_type": dominant["anomaly_type"],
            "explainability": (
                f"[Blended {personal_weight * 100:.0f}% personal HGNN / "
                f"{federated_weight * 100:.0f}% federated peer] {dominant['explainability']}"
            ),
        }
