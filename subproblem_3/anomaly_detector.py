"""
anomaly_detector.py

Combines the SecurityHGNN structural embedding distance with
explainable heuristic checks (Haversine impossible-travel, device
fingerprint drift, brute force) to score a single incoming access-log
event against a user's historical baseline graph.

Component 3 of Sub-Problem 3.1 (HGNN Anomaly Detector).
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F
from torch_geometric.data import HeteroData

from graph_builder import CyberGraphBuilder
from hgnn_model import SecurityHGNN, EDGE_TYPES

# Cosine-distance threshold above which the HGNN structural signal
# alone is treated as anomalous (per Sub-Problem 3.1 spec).
HGNN_DISTANCE_THRESHOLD = 0.85

EARTH_RADIUS_KM = 6371.0
IMPOSSIBLE_TRAVEL_SPEED_KMH = 900.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in km."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


class AnomalyDetector:
    """
    Scores a single incoming event against a per-user historical
    baseline HeteroData graph using the trained SecurityHGNN, backed
    by fast, explainable heuristic pre-checks.
    """

    def __init__(self, hgnn_model: SecurityHGNN, graph_builder: Optional[CyberGraphBuilder] = None):
        self.hgnn_model = hgnn_model
        self.hgnn_model.eval()
        self.graph_builder = graph_builder or CyberGraphBuilder()

    # -- HGNN structural signal -----------------------------------------
    def _embed(self, graph: HeteroData) -> torch.Tensor:
        edge_index_dict = {et: graph[et].edge_index for et in EDGE_TYPES}
        x_dict = {nt: graph[nt].x for nt in ("user", "device", "location", "resource")}
        with torch.no_grad():
            return self.hgnn_model.get_user_embedding(x_dict, edge_index_dict)  # [out_channels]

    def _structural_distance(self, historical_graph: HeteroData, incoming_log: Dict) -> float:
        baseline_emb = self._embed(historical_graph)                      # [out_channels]
        injected_graph = self.graph_builder.inject_event(historical_graph, incoming_log)
        new_emb = self._embed(injected_graph)                             # [out_channels]
        cosine_sim = F.cosine_similarity(baseline_emb.unsqueeze(0), new_emb.unsqueeze(0)).item()
        return 1.0 - cosine_sim  # cosine distance, typically in [0, 2]

    # -- Heuristic checks (run before the HGNN, cheap + high precision) --
    def _check_impossible_travel(self, historical_logs: List[Dict], incoming_log: Dict) -> Optional[Dict]:
        if not historical_logs:
            return None
        last_log = historical_logs[-1]
        last_geo, cur_geo = last_log.get("geo_location"), incoming_log.get("geo_location")
        if not last_geo or not cur_geo:
            return None
        try:
            t1, t2 = _parse_ts(last_log["timestamp"]), _parse_ts(incoming_log["timestamp"])
        except (KeyError, ValueError):
            return None
        hours = max((t2 - t1).total_seconds() / 3600.0, 1e-6)
        distance_km = _haversine_km(last_geo["lat"], last_geo["lon"], cur_geo["lat"], cur_geo["lon"])
        speed_kmh = distance_km / hours
        if speed_kmh > IMPOSSIBLE_TRAVEL_SPEED_KMH:
            return {
                "risk_score": round(min(1.0, 0.85 + (speed_kmh - IMPOSSIBLE_TRAVEL_SPEED_KMH) / 10000), 4),
                "anomaly_type": "Impossible Travel",
                "explainability": (
                    f"Implied travel speed of {speed_kmh:.0f} km/h between consecutive "
                    f"logins ({distance_km:.0f} km in {hours:.2f}h) exceeds the "
                    f"{IMPOSSIBLE_TRAVEL_SPEED_KMH:.0f} km/h physical travel threshold."
                ),
            }
        return None

    def _check_device_spoofing(self, historical_logs: List[Dict], incoming_log: Dict) -> Optional[Dict]:
        known_devices = {log.get("device_id") for log in historical_logs if log.get("device_id")}
        cur_device = incoming_log.get("device_id")
        if known_devices and cur_device and cur_device not in known_devices:
            known_os = {log.get("os_version") for log in historical_logs if log.get("os_version")}
            cur_os = incoming_log.get("os_version")
            if known_os and cur_os not in known_os:
                return {
                    "risk_score": 0.9,
                    "anomaly_type": "Device Spoofing",
                    "explainability": (
                        f"Entity switched from known device fingerprint(s) {sorted(known_devices)} "
                        f"to unseen device '{cur_device}' with unfamiliar OS '{cur_os}' mid-session."
                    ),
                }
        return None

    def _check_brute_force(self, historical_logs: List[Dict], incoming_log: Dict) -> Optional[Dict]:
        failures = [log for log in historical_logs if log.get("auth_status") == "failure"]
        if incoming_log.get("auth_status") == "failure" and len(failures) >= 3:
            return {
                "risk_score": round(min(1.0, 0.6 + 0.08 * len(failures)), 4),
                "anomaly_type": "Brute Force",
                "explainability": (
                    f"{len(failures) + 1} failed authentication attempts observed for this "
                    f"entity within the recent log window."
                ),
            }
        return None

    # -- Public entrypoint -------------------------------------------------
    def score_incoming_event(
        self,
        hgnn_model: SecurityHGNN,
        historical_graph: HeteroData,
        historical_logs: List[Dict],
        incoming_log: Dict,
    ) -> Dict[str, object]:
        """
        Args:
            hgnn_model: trained SecurityHGNN checkpoint to score with.
            historical_graph: baseline HeteroData from
                CyberGraphBuilder.build_historical_graph().
            historical_logs: the raw list of up to 5 historical logs
                (needed for heuristic checks that reason about
                timestamps/devices rather than graph structure alone).
            incoming_log: the new event dict to score.

        Returns:
            {"risk_score": float, "anomaly_type": str, "explainability": str}
        """
        self.hgnn_model = hgnn_model
        self.hgnn_model.eval()

        for check in (self._check_impossible_travel, self._check_device_spoofing, self._check_brute_force):
            result = check(historical_logs, incoming_log)
            if result is not None:
                return result

        # Structural (HGNN) signal -- catches Lateral Movement and any
        # behavior drift the heuristics above didn't already name.
        cosine_distance = self._structural_distance(historical_graph, incoming_log)

        if cosine_distance > HGNN_DISTANCE_THRESHOLD:
            resource = incoming_log.get("resource_accessed", "unknown resource")
            return {
                "risk_score": round(min(1.0, cosine_distance), 4),
                "anomaly_type": "Lateral Movement",
                "explainability": (
                    f"Accessing '{resource}' shifted the user's structural behavioral "
                    f"embedding by a cosine distance of {cosine_distance:.3f}, exceeding "
                    f"the {HGNN_DISTANCE_THRESHOLD} baseline-deviation threshold."
                ),
            }

        return {
            "risk_score": round(max(0.0, cosine_distance), 4),
            "anomaly_type": "None",
            "explainability": (
                f"Event is structurally consistent with the user's historical baseline "
                f"(cosine distance {cosine_distance:.3f})."
            ),
        }
