# CyberGuard AI — Microservice Anomaly Detection Platform

A complete, enterprise-grade, end-to-end cybersecurity anomaly detection system built with a microservice architecture. The platform ingests real-time synthetic access logs, analyzes user behavioral structural patterns using Heterogeneous Graph Neural Networks (HGNN) & Federated Cold-Start baselines, and presents real-time threat intelligence on a dark-mode SOC dashboard.

---

## 🏛️ System Architecture

```
[ Python Synthetic Generator ] ──(HTTP POST /api/v1/logs/ingest)──▶ [ Spring Boot Backend (Port 8080) ]
       │ (Port 8001 Control API)                                                  │
       │                                                                  (WebClient POST /predict)
       ▼                                                                          ▼
[ Attack Simulator Control ]                                         [ Python AI Engine (Port 8000) ]
                                                                      (FastAPI + PyTorch Geometric)
                                                                                  │
                                                                           (REST JSON Response)
                                                                                  ▼
[ React + Vite SOC Dashboard (Port 5173) ] ◀──(Polling GET /api/v1/alerts/live)───┘
```

---

## 📦 Components Breakdown & Directory Structure

### 1. `subproblem-1_v3/` — Synthetic Cybersecurity Log Generator
* **Role**: Simulates continuous enterprise cybersecurity access logs for 500 entity profiles with probabilistic state machine behavioral transitions and injects 6 major cyber attack patterns.
* **Key Files**:
  * `synthetic_log_generator.py`: Main continuous loop streaming logs to Spring Boot via `NetworkDispatcher`.
  * `simulation.py`: Simulation runner supporting time acceleration.
  * `state_machine.py`: Probabilistic State Machine (OFFLINE, AUTHENTICATING, ACTIVE_SESSION, IDLE, LOGGED_OUT).
  * `anomaly_injector.py`: Injects Brute Force, Impossible Travel, Lateral Movement, Device Spoofing, Credential Stuffing, and Low-and-Slow Exfiltration.
  * `control_api.py`: FastAPI control service on port 8001 to trigger on-demand attack injections from the React dashboard.

### 2. `anomaly-detection-backend_v2/` — Spring Boot Middle-Layer Orchestrator
* **Role**: Ingests logs, maintains transactional state in PostgreSQL/H2, queries historical context, orchestrates WebClient calls to the AI microservice, persists alerts, and exposes secured endpoints for the React dashboard.
* **Key Components**:
  * `IngestionController`: Exposes `POST /api/v1/logs/ingest` (secured via `X-API-Key`).
  * `DashboardController`: Exposes `GET /api/v1/alerts/live`, `/dashboard/stats`, `/dashboard/telemetry`, and `/dashboard/logs`.
  * `LogProcessingService`: Handles data ingestion, fetches last 5 historical logs per entity, calls AI Engine `POST /predict`, creates `RiskAlert` if `riskScore > 0.85`, and handles retry fallbacks (`PENDING_ANALYSIS`).
  * `SecurityConfig` & JWT Filters: Dual auth mechanism (`ApiKeyAuthFilter` for ingestion, `JwtAuthenticationFilter` for dashboard).

### 3. `subproblem_3/` — AI Anomaly Detection Engine (FastAPI + PyTorch Geometric)
* **Role**: Heterogeneous Graph Neural Network (HGNN) & Federated Learning microservice on port 8000.
* **Key Files**:
  * `main.py`: FastAPI server exposing `POST /predict`, `GET /model/status`, and `POST /model/train`.
  * `graph_builder.py`: Constructs PyG `HeteroData` graphs (Nodes: User, Device, Location, Resource; Edges: logged_in_from, accessed, located_in).
  * `hgnn_model.py` & `security_hgnn.pt`: 2-layer Heterogeneous Convolutional Network (`HeteroConv` with `SAGEConv`).
  * `anomaly_detector.py`: Computes structural user embedding shifts (cosine distance) and heuristic checks (Haversine for Impossible Travel).
  * `cold_start.py` & `federated_aggregator.py`: Handles cold-start users (< 5 historical logs) using role-based Federated Averaging (`FedAvg`) peer baselines.

### 4. `frontend/` — React JS + Vite SOC Dashboard
* **Role**: Modern dark-mode SOC Analyst Dashboard on port 5173.
* **Key Tabs**:
  * **OverviewTab**: System health, active KPI metrics, live alert feed with color-coded severity badges and human-readable explainability.
  * **MicroservicesTab**: Visual interactive data flow pipeline displaying live HTTP payload inspection across generator, backend, AI engine, and database.
  * **AiEngineTab**: Technical model architecture, PyTorch Geometric GraphSAGE tensor metadata, and 1-click live self-supervised training trigger.
  * **AttackSimulatorTab**: On-demand attack injection control panel (Brute Force, Impossible Travel, Lateral Movement, Device Spoofing) and live access log stream table.

---

## ⚡ Quick Start / How to Run

You can launch all 4 microservices simultaneously using the root unified orchestrator:

```bash
python run_all.py
```

### Individual Service Ports & URLs:
- **React Frontend**: [http://localhost:5173](http://localhost:5173)
- **Spring Boot Backend**: [http://localhost:8080/api/v1/alerts/live](http://localhost:8080/api/v1/alerts/live)
- **AI Engine Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Generator Control API**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 🔒 Security & Data Contracts

### Ingestion Payload Schema (Generator ➔ Spring Boot):
```json
{
  "entity_id": "user_4589",
  "auth_method": "password",
  "auth_status": "success",
  "timestamp": "2026-07-25T08:00:00.000Z",
  "source_ip": "192.168.1.50",
  "geo_location": {
    "lat": 19.0760,
    "lon": 72.8777
  },
  "device_id": "macbook_pro_m2_xyz",
  "os_version": "macOS 14",
  "user_agent": "Chrome/114.0",
  "resource_accessed": "/api/v1/marketing/budget.pdf"
}
```

### Dashboard Live Alert Response Schema (Spring Boot ➔ React):
```json
[
  {
    "alert_id": 1045,
    "timestamp": "2026-07-25T08:15:00Z",
    "entity_id": "user_4589",
    "risk_score": 0.96,
    "severity": "CRITICAL",
    "anomaly_type": "Lateral Movement",
    "explainability_factors": [
      "Access to /marketing/budget.pdf was 4 standard deviations from normal.",
      "Graph edge probability for this resource is 0.012."
    ]
  }
]
```
