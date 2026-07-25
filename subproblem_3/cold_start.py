"""
cold_start.py

Solves the "cold-start" problem for brand-new entities with fewer than
5 historical logs: score their behavior against a Federated Peer
Group baseline (aggregated via FedAvg in federated_aggregator.py),
then provide a confidence-weighted blend as personal history accrues.

Components 2 and 3 of Sub-Problem 3.2 (Federated Cold-Start).
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Optional

import torch

# Must match SecurityHGNN's out_channels so cold-start scores live in
# the same embedding space as the personal HGNN -- this is what makes
# BaselineTransitioner's later blending mathematically meaningful.
PEER_EMBEDDING_DIM = 16

STD_DEV_THRESHOLD = 3.0


def _hour_of_day(timestamp: str) -> int:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
    except (ValueError, AttributeError):
        return 12  # neutral fallback


def _ip_network_type(source_ip: str) -> str:
    """Coarse classification; production should use a real IP-intel service."""
    private_prefixes = ("10.", "172.16.", "192.168.")
    if any(source_ip.startswith(p) for p in private_prefixes):
        return "internal"
    return "external"


def _uri_bucket(uri: str) -> float:
    """Deterministic hash of the resource URI into [0, 1]."""
    digest = hashlib.sha256(uri.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def _project_log_features(incoming_log: Dict, dim: int = PEER_EMBEDDING_DIM) -> torch.Tensor:
    """
    Projects the three cold-start-relevant raw signals -- time of day,
    IP network type, and resource URI -- into a fixed-size vector in
    the same dimensionality as the peer embedding space, via a
    deterministic (untrained) hash-based projection.

    This mirrors a feature-hashing / random-projection trick: it lets
    us compute a numeric distance against global_peer_tensor without a
    trained personal HGNN, at the cost of the projection itself being
    a fixed, non-learned mapping. In production this projector would
    typically be pre-trained jointly with the HGNN so it lands in a
    genuinely comparable space; swapping it in does not change any of
    the surrounding math below.

    Returns:
        Tensor[dim]
    """
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
    """
    Scores a brand-new (<5 historical logs) entity's incoming event
    against its role's Federated Peer baseline tensor.
    """

    def evaluate_new_user(
        self,
        incoming_log: Dict,
        global_peer_tensor: torch.Tensor,
        peer_std_tensor: Optional[torch.Tensor] = None,
    ) -> Dict[str, object]:
        """
        Args:
            incoming_log: raw event dict for the new user.
            global_peer_tensor: Tensor[embedding_dim] -- the FedAvg
                peer mean produced by
                FederatedPeerAggregator.aggregate_peer_weights() for
                this user's role.
            peer_std_tensor: Tensor[embedding_dim] -- per-dimension
                peer std from
                FederatedPeerAggregator.compute_peer_std(). If
                omitted, a conservative default std of 1.0 per
                dimension is used.

        Returns:
            {"risk_score": float, "anomaly_type": str, "explainability": str}
        """
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
    """
    Implements the sliding-window confidence scale that blends the
    Federated Peer baseline with the Personal HGNN baseline as a
    user's historical log count grows.
    """

    COLD_START_MAX = 5   # < 5 logs => 100% federated
    STABLE_MIN = 50       # > 50 logs => 100% personal HGNN

    def calculate_confidence(self, user_log_count: int) -> float:
        """
        Returns the *personal-HGNN* weight in [0.0, 1.0]:
            - 0.0 when user_log_count < 5    (100% federated)
            - linearly ramps 0.0 -> 1.0 across [5, 50]
            - 1.0 when user_log_count > 50   (100% personal HGNN)

        The federated weight is simply (1.0 - personal_weight).
        """
        if user_log_count < self.COLD_START_MAX:
            return 0.0
        if user_log_count > self.STABLE_MIN:
            return 1.0
        span = self.STABLE_MIN - self.COLD_START_MAX  # 45
        progressed = user_log_count - self.COLD_START_MAX
        return round(progressed / span, 4)

    def blend_scores(self, federated_result: Dict, personal_result: Dict, user_log_count: int) -> Dict:
        """
        Blends two already-computed risk_score outputs using
        calculate_confidence() as the mixing weight. Useful during the
        [5, 50] transition window if the FastAPI layer chooses to
        compute both signals rather than routing to just one.
        """
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
