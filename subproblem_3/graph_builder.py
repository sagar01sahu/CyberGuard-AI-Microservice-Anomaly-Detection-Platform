"""
graph_builder.py

Builds a PyTorch Geometric HeteroData baseline graph from historical
access-log JSON records for a single entity (user).

Component 1 of Sub-Problem 3.1 (HGNN Anomaly Detector).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import torch
from torch_geometric.data import HeteroData

# ----------------------------------------------------------------------
# Feature encoding configuration
# ----------------------------------------------------------------------

ROLE_VOCAB = ["MARKETING", "ENGINEERING", "FINANCE", "HR", "IT", "LEGAL", "EXECUTIVE", "SALES", "UNKNOWN"]
OS_VOCAB = ["macOS", "Windows", "Linux", "iOS", "Android", "UNKNOWN"]
BROWSER_VOCAB = ["Chrome", "Firefox", "Safari", "Edge", "UNKNOWN"]

ROLE_EMBED_DIM = len(ROLE_VOCAB)          # one-hot, 5
OS_EMBED_DIM = len(OS_VOCAB)              # one-hot, 6
BROWSER_EMBED_DIM = len(BROWSER_VOCAB)    # one-hot, 5
URI_HASH_DIM = 16                         # hashed bag-of-chars embedding
GEO_DIM = 2                               # lat, lon (scaled)
SENSITIVITY_DIM = 1

USER_FEAT_DIM = ROLE_EMBED_DIM                                    # 5
DEVICE_FEAT_DIM = OS_EMBED_DIM + BROWSER_EMBED_DIM                 # 11
LOCATION_FEAT_DIM = GEO_DIM                                        # 2
RESOURCE_FEAT_DIM = SENSITIVITY_DIM + URI_HASH_DIM                 # 17


def _one_hot(value: str, vocab: List[str]) -> torch.Tensor:
    """Return a 1-D one-hot tensor of shape [len(vocab)]."""
    idx = vocab.index(value) if value in vocab else vocab.index("UNKNOWN")
    vec = torch.zeros(len(vocab), dtype=torch.float32)
    vec[idx] = 1.0
    return vec


def _hash_embed(text: str, dim: int = URI_HASH_DIM) -> torch.Tensor:
    """
    Deterministically hash an arbitrary string (e.g. a resource URI)
    into a fixed-size float embedding in [-1, 1]. Shape: [dim]
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals = [(digest[i % len(digest)] / 127.5) - 1.0 for i in range(dim)]
    return torch.tensor(vals, dtype=torch.float32)


def _sensitivity_of(uri: str) -> float:
    """
    Heuristic sensitivity score in [0, 1] based on resource path keywords.
    In production this should come from a resource-classification table
    maintained by the Spring Boot backend rather than string matching.
    """
    uri_lower = uri.lower()
    high_value_markers = ("payroll", "prod_keys", "secrets", ".pem", "finance", "salary")
    medium_value_markers = ("engineering", "hr", "internal")
    if any(marker in uri_lower for marker in high_value_markers):
        return 1.0
    if any(marker in uri_lower for marker in medium_value_markers):
        return 0.6
    return 0.2


def _scale_geo(lat: float, lon: float) -> torch.Tensor:
    """Scale lat/lon from [-90,90]/[-180,180] into roughly [-1, 1]."""
    return torch.tensor([lat / 90.0, lon / 180.0], dtype=torch.float32)


@dataclass
class _EntityRegistry:
    """
    Stable node-index mapping per node type so repeated entities (same
    device_id, location, resource URI) map to the same graph node
    instead of duplicating nodes.
    """
    user: Dict[str, int] = field(default_factory=dict)
    device: Dict[str, int] = field(default_factory=dict)
    location: Dict[str, int] = field(default_factory=dict)
    resource: Dict[str, int] = field(default_factory=dict)

    def get_or_create(self, table: Dict[str, int], key: str) -> Tuple[int, bool]:
        """Returns (index, is_new)."""
        if key in table:
            return table[key], False
        idx = len(table)
        table[key] = idx
        return idx, True


class CyberGraphBuilder:
    """
    Constructs a per-user baseline HeteroData graph from up to 5
    historical access-log records supplied by the Spring Boot backend.
    """

    def __init__(self) -> None:
        self.registry = _EntityRegistry()
        self._user_feats: List[torch.Tensor] = []
        self._device_feats: List[torch.Tensor] = []
        self._location_feats: List[torch.Tensor] = []
        self._resource_feats: List[torch.Tensor] = []

        self._edge_logged_in_from: List[Tuple[int, int]] = []  # (user, device)
        self._edge_accessed: List[Tuple[int, int]] = []        # (user, resource)
        self._edge_located_in: List[Tuple[int, int]] = []      # (device, location)

    # -- internal helpers ---------------------------------------------
    def _add_user(self, entity_id: str, role: str) -> int:
        idx, is_new = self.registry.get_or_create(self.registry.user, entity_id)
        if is_new:
            self._user_feats.append(_one_hot(role, ROLE_VOCAB))
        return idx

    def _add_device(self, device_id: str, os_version: str, user_agent: str) -> int:
        idx, is_new = self.registry.get_or_create(self.registry.device, device_id)
        if is_new:
            os_family = next((o for o in OS_VOCAB if o.lower() in os_version.lower()), "UNKNOWN")
            browser_family = next((b for b in BROWSER_VOCAB if b.lower() in user_agent.lower()), "UNKNOWN")
            feat = torch.cat([_one_hot(os_family, OS_VOCAB), _one_hot(browser_family, BROWSER_VOCAB)])
            self._device_feats.append(feat)
        return idx

    def _add_location(self, lat: float, lon: float) -> int:
        key = f"{round(lat, 3)}_{round(lon, 3)}"
        idx, is_new = self.registry.get_or_create(self.registry.location, key)
        if is_new:
            self._location_feats.append(_scale_geo(lat, lon))
        return idx

    def _add_resource(self, uri: str) -> int:
        idx, is_new = self.registry.get_or_create(self.registry.resource, uri)
        if is_new:
            feat = torch.cat([
                torch.tensor([_sensitivity_of(uri)], dtype=torch.float32),
                _hash_embed(uri),
            ])
            self._resource_feats.append(feat)
        return idx

    def _ingest_log(self, log: Dict) -> None:
        entity_id = log["entity_id"]
        role = log.get("role", "UNKNOWN")
        geo = log.get("geo_location", {"lat": 0.0, "lon": 0.0})

        u = self._add_user(entity_id, role)
        d = self._add_device(
            log.get("device_id", "unknown_device"),
            log.get("os_version", "UNKNOWN"),
            log.get("user_agent", "UNKNOWN"),
        )
        loc = self._add_location(geo.get("lat", 0.0), geo.get("lon", 0.0))
        r = self._add_resource(log.get("resource_accessed", "/unknown"))

        self._edge_logged_in_from.append((u, d))
        self._edge_located_in.append((d, loc))
        if log.get("auth_status", "success") == "success":
            self._edge_accessed.append((u, r))

    # -- public API -----------------------------------------------------
    def build_historical_graph(self, historical_logs: List[Dict]) -> HeteroData:
        """
        Parses up to 5 historical JSON logs (as forwarded by the Spring
        Boot backend) and constructs the baseline heterogeneous graph
        for that entity.

        Args:
            historical_logs: list of raw log dicts, e.g.:
                {
                    "entity_id": "user_4589",
                    "role": "MARKETING",
                    "auth_method": "password",
                    "auth_status": "success",
                    "timestamp": "2026-07-25T08:00:00.000Z",
                    "source_ip": "192.168.1.50",
                    "geo_location": {"lat": 19.076, "lon": 72.8777},
                    "device_id": "macbook_pro_m2_xyz",
                    "os_version": "macOS 14",
                    "user_agent": "Chrome/114.0",
                    "resource_accessed": "/api/v1/marketing/budget.pdf"
                }

        Returns:
            HeteroData with node types {user, device, location, resource}
            and edge types {logged_in_from, accessed, located_in} plus
            their reverse edges (added for bidirectional message passing).
        """
        for log in historical_logs:
            self._ingest_log(log)
        return self._finalize()

    def inject_event(self, graph: HeteroData, incoming_log: Dict) -> HeteroData:
        """
        Returns a *new* HeteroData (the original is left untouched) with
        the incoming_log's device/location/resource nodes and edges
        merged in. Used by AnomalyDetector to compute a "what-if"
        embedding without mutating the stored baseline.
        """
        graph_copy = graph.clone()
        registries = graph_copy.node_key_registry  # type: ignore[attr-defined]

        def _get_or_append(node_type: str, key: str, feat_fn) -> int:
            table = registries[node_type]
            if key in table:
                return table[key]
            idx = len(table)
            table[key] = idx
            new_feat = feat_fn().unsqueeze(0)
            graph_copy[node_type].x = torch.cat([graph_copy[node_type].x, new_feat], dim=0)
            return idx

        entity_id = incoming_log["entity_id"]
        role = incoming_log.get("role", "UNKNOWN")
        geo = incoming_log.get("geo_location", {"lat": 0.0, "lon": 0.0})

        u_idx = _get_or_append("user", entity_id, lambda: _one_hot(role, ROLE_VOCAB))

        device_id = incoming_log.get("device_id", "unknown_device")
        os_version = incoming_log.get("os_version", "UNKNOWN")
        user_agent = incoming_log.get("user_agent", "UNKNOWN")

        def _device_feat():
            os_family = next((o for o in OS_VOCAB if o.lower() in os_version.lower()), "UNKNOWN")
            browser_family = next((b for b in BROWSER_VOCAB if b.lower() in user_agent.lower()), "UNKNOWN")
            return torch.cat([_one_hot(os_family, OS_VOCAB), _one_hot(browser_family, BROWSER_VOCAB)])

        d_idx = _get_or_append("device", device_id, _device_feat)

        loc_key = f"{round(geo.get('lat', 0.0), 3)}_{round(geo.get('lon', 0.0), 3)}"
        loc_idx = _get_or_append(
            "location", loc_key, lambda: _scale_geo(geo.get("lat", 0.0), geo.get("lon", 0.0))
        )

        uri = incoming_log.get("resource_accessed", "/unknown")

        def _resource_feat():
            return torch.cat([torch.tensor([_sensitivity_of(uri)], dtype=torch.float32), _hash_embed(uri)])

        r_idx = _get_or_append("resource", uri, _resource_feat)

        def _append_edge(edge_type, src_idx, dst_idx):
            new_edge = torch.tensor([[src_idx], [dst_idx]], dtype=torch.long)
            graph_copy[edge_type].edge_index = torch.cat([graph_copy[edge_type].edge_index, new_edge], dim=1)
            rev_type = (edge_type[2], f"rev_{edge_type[1]}", edge_type[0])
            new_rev_edge = torch.tensor([[dst_idx], [src_idx]], dtype=torch.long)
            graph_copy[rev_type].edge_index = torch.cat([graph_copy[rev_type].edge_index, new_rev_edge], dim=1)

        _append_edge(("user", "logged_in_from", "device"), u_idx, d_idx)
        _append_edge(("device", "located_in", "location"), d_idx, loc_idx)
        if incoming_log.get("auth_status", "success") == "success":
            _append_edge(("user", "accessed", "resource"), u_idx, r_idx)

        return graph_copy

    def _finalize(self) -> HeteroData:
        data = HeteroData()

        def _stack(feats: List[torch.Tensor], dim: int) -> torch.Tensor:
            return torch.stack(feats, dim=0) if feats else torch.zeros((0, dim), dtype=torch.float32)

        data["user"].x = _stack(self._user_feats, USER_FEAT_DIM)
        data["device"].x = _stack(self._device_feats, DEVICE_FEAT_DIM)
        data["location"].x = _stack(self._location_feats, LOCATION_FEAT_DIM)
        data["resource"].x = _stack(self._resource_feats, RESOURCE_FEAT_DIM)

        def _edge_tensor(pairs: List[Tuple[int, int]]) -> torch.Tensor:
            if not pairs:
                return torch.zeros((2, 0), dtype=torch.long)
            return torch.tensor(pairs, dtype=torch.long).t().contiguous()

        data["user", "logged_in_from", "device"].edge_index = _edge_tensor(self._edge_logged_in_from)
        data["user", "accessed", "resource"].edge_index = _edge_tensor(self._edge_accessed)
        data["device", "located_in", "location"].edge_index = _edge_tensor(self._edge_located_in)

        # Reverse edges so HeteroConv message-passes in both directions.
        data["device", "rev_logged_in_from", "user"].edge_index = (
            data["user", "logged_in_from", "device"].edge_index.flip(0)
        )
        data["resource", "rev_accessed", "user"].edge_index = (
            data["user", "accessed", "resource"].edge_index.flip(0)
        )
        data["location", "rev_located_in", "device"].edge_index = (
            data["device", "located_in", "location"].edge_index.flip(0)
        )

        # Stash string->index registries so inject_event() can extend
        # this exact graph consistently later.
        data.node_key_registry = {
            "user": dict(self.registry.user),
            "device": dict(self.registry.device),
            "location": dict(self.registry.location),
            "resource": dict(self.registry.resource),
        }
        return data
