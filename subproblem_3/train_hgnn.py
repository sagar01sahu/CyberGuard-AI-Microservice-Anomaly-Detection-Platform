

from __future__ import annotations

import os
import random
import logging
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from graph_builder import CyberGraphBuilder, ROLE_VOCAB
from hgnn_model import SecurityHGNN, EDGE_TYPES
from cold_start import PEER_EMBEDDING_DIM

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hgnn-trainer")

MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "security_hgnn.pt")

def generate_synthetic_user_logs(entity_id: str, role: str, num_logs: int = 10) -> List[Dict]:

    os_versions = {"ENGINEERING": "macOS 14", "MARKETING": "Windows 11", "FINANCE": "Windows 10", "HR": "macOS 13"}
    browsers = {"ENGINEERING": "Chrome/124.0", "MARKETING": "Edge/120.0", "FINANCE": "Firefox/118.0", "HR": "Safari/17.0"}
    geo_bases = {
        "ENGINEERING": {"lat": 37.7749, "lon": -122.4194},
        "MARKETING": {"lat": 40.7128, "lon": -74.0060},
        "FINANCE": {"lat": 51.5074, "lon": -0.1278},
        "HR": {"lat": 19.0760, "lon": 72.8777},
    }
    role_resources = {
        "ENGINEERING": ["/api/v1/github/repos", "/api/v1/jenkins/builds", "/api/v1/aws/ec2"],
        "MARKETING": ["/api/v1/marketing/campaigns", "/api/v1/cms/posts", "/api/v1/analytics/traffic"],
        "FINANCE": ["/api/v1/finance/reports", "/api/v1/billing/invoices", "/api/v1/accounting/ledger"],
        "HR": ["/api/v1/hr/employees", "/api/v1/hr/onboarding", "/api/v1/payroll/summary"],
    }

    logs = []
    base_geo = geo_bases.get(role, {"lat": 0.0, "lon": 0.0})
    resources = role_resources.get(role, ["/api/v1/general/news"])
    device = f"device_{entity_id}"
    os_ver = os_versions.get(role, "macOS 14")
    browser = browsers.get(role, "Chrome/124.0")

    for i in range(num_logs):
        lat_jitter = base_geo["lat"] + (random.random() - 0.5) * 0.01
        lon_jitter = base_geo["lon"] + (random.random() - 0.5) * 0.01
        res = random.choice(resources)

        logs.append({
            "entity_id": entity_id,
            "role": role,
            "auth_method": "password",
            "auth_status": "success",
            "timestamp": f"2026-07-25T08:{i:02d}:00.000Z",
            "source_ip": f"192.168.1.{10 + (hash(entity_id) % 200)}",
            "geo_location": {"lat": lat_jitter, "lon": lon_jitter},
            "device_id": device,
            "os_version": os_ver,
            "user_agent": browser,
            "resource_accessed": res,
        })
    return logs


def train_security_hgnn(epochs: int = 20, lr: float = 0.01) -> Tuple[SecurityHGNN, Dict[str, Dict[str, torch.Tensor]], List[float]]:
    logger.info("Initializing self-supervised HGNN training across enterprise roles...")

    model = SecurityHGNN(hidden_channels=32, out_channels=PEER_EMBEDDING_DIM)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    role_graphs = {}
    all_users = []
    roles_to_train = [r for r in ROLE_VOCAB if r != "UNKNOWN"]

    # 1. Build initial user baselines
    for role in roles_to_train:
        role_graphs[role] = []
        for u_idx in range(5):
            entity_id = f"user_{role.lower()}_{u_idx}"
            all_users.append((entity_id, role))
            logs = generate_synthetic_user_logs(entity_id, role, num_logs=8)
            builder = CyberGraphBuilder()
            graph = builder.build_historical_graph(logs)
            role_graphs[role].append((graph, logs))

    # 2. GENERATE A STABLE TRAINING DATASET (This fixes the flatlining loss)
    training_dataset = []
    for role in roles_to_train:
        for graph, logs in role_graphs[role]:
            builder = CyberGraphBuilder()

            # Create ONE stable positive example
            normal_log = generate_synthetic_user_logs(logs[0]["entity_id"], role, num_logs=1)[0]
            pos_graph = builder.inject_event(graph, normal_log)

            # Create ONE stable negative (anomalous) example
            anom_log = normal_log.copy()
            anom_log["resource_accessed"] = "/api/v1/admin/secrets.pem"
            anom_log["device_id"] = "untrusted_hacker_laptop"
            neg_graph = builder.inject_event(graph, anom_log)

            training_dataset.append((graph, pos_graph, neg_graph))

    # 3. Train against the stable dataset
    model.train()
    loss_history = []

    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        num_pairs = 0

        for graph, pos_graph, neg_graph in training_dataset:
            optimizer.zero_grad()

            def get_emb(g):
                edge_idx = {et: g[et].edge_index for et in EDGE_TYPES}
                x_dict = {nt: g[nt].x for nt in ("user", "device", "location", "resource")}
                return model.get_user_embedding(x_dict, edge_idx)

            emb_orig = get_emb(graph)
            emb_pos = get_emb(pos_graph)
            emb_neg = get_emb(neg_graph)

            pos_dist = 1.0 - F.cosine_similarity(emb_orig.unsqueeze(0), emb_pos.unsqueeze(0))
            neg_dist = 1.0 - F.cosine_similarity(emb_orig.unsqueeze(0), emb_neg.unsqueeze(0))

            loss = pos_dist + F.relu(0.85 - neg_dist)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_pairs += 1

        avg_loss = total_loss / max(1, num_pairs)
        loss_history.append(round(avg_loss, 4))
        if epoch % 5 == 0 or epoch == epochs:
            logger.info(f"Epoch {epoch:02d}/{epochs:02d} - Loss: {avg_loss:.4f}")

    model.eval()
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    logger.info(f"Trained HGNN weights saved to {MODEL_SAVE_PATH}")

    # 4. Calculate Federated Baselines
    federated_baselines = {}
    with torch.no_grad():
        for role in roles_to_train:
            embs = []
            for graph, _ in role_graphs[role]:
                edge_idx = {et: graph[et].edge_index for et in EDGE_TYPES}
                x_dict = {nt: graph[nt].x for nt in ("user", "device", "location", "resource")}
                user_emb = model.get_user_embedding(x_dict, edge_idx)
                embs.append(user_emb)

            emb_tensor = torch.stack(embs, dim=0)
            mean_tensor = emb_tensor.mean(dim=0)
            std_tensor = emb_tensor.std(dim=0) + 0.5

            federated_baselines[role] = {
                "mean": mean_tensor,
                "std": std_tensor,
            }

        federated_baselines["UNKNOWN"] = {
            "mean": torch.zeros(PEER_EMBEDDING_DIM),
            "std": torch.ones(PEER_EMBEDDING_DIM),
        }

    logger.info("Federated role baselines calculated successfully.")
    return model, federated_baselines, loss_history

if __name__ == "__main__":
    train_security_hgnn(epochs=20)