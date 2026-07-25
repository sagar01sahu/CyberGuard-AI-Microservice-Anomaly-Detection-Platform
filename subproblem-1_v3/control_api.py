"""
control_api.py

Lightweight FastAPI HTTP service that exposes controls for the Synthetic Log Generator.
Allows the React UI to trigger specific cyber attack scenarios (Brute Force,
Impossible Travel, Lateral Movement, Device Spoofing) on demand and monitor stream state.
"""

import random
import requests
import logging
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from profile_generator import ProfileGenerator
from anomaly_injector import AnomalyInjector
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generator-control")

app = FastAPI(title="Synthetic Log Generator Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize synthetic users and injector
logger.info("Generating synthetic user profiles for attack controller...")
user_profiles = ProfileGenerator().generate_user_pool(count=50)
injector = AnomalyInjector(user_profiles)

SPRING_BOOT_INGEST_URL = Config.API_URL
API_KEY = Config.API_KEY

STATS = {
    "total_logs_dispatched": 0,
    "attacks_injected": 0,
    "attack_counts": {
        "Brute Force": 0,
        "Impossible Travel": 0,
        "Lateral Movement": 0,
        "Device Spoofing": 0,
        "Credential Stuffing": 0,
        "Low-and-Slow Exfiltration": 0,
    }
}


class AttackRequest(BaseModel):
    attack_type: str  # "brute_force", "impossible_travel", "lateral_movement", "device_spoofing"
    target_role: str = "MARKETING"


@app.get("/api/v1/generator/status")
def get_status():
    return {
        "status": "active",
        "user_pool_size": len(user_profiles),
        "target_ingest_url": SPRING_BOOT_INGEST_URL,
        "stats": STATS,
    }


@app.post("/api/v1/generator/inject-attack")
def inject_attack(req: AttackRequest):
    """Triggers an immediate attack scenario and dispatches generated attack logs to Spring Boot."""
    matching_users = [u for u in user_profiles if u.role == req.target_role.upper()]
    user = random.choice(matching_users) if matching_users else random.choice(user_profiles)

    base_log = {
        "entity_id": user.entity_id,
        "role": user.role,
        "auth_method": "password",
        "auth_status": "success",
        "timestamp": "2026-07-25T08:30:00.000Z",
        "source_ip": user.primary_ip,
        "geo_location": user.home_geo,
        "device_id": user.primary_device_id,
        "os_version": user.primary_os,
        "user_agent": user.user_agent,
        "resource_accessed": "/api/v1/dashboard",
    }

    attack_map = {
        "brute_force": (injector._brute_force, "Brute Force"),
        "impossible_travel": (injector._impossible_travel, "Impossible Travel"),
        "lateral_movement": (injector._lateral_movement, "Lateral Movement"),
        "device_spoofing": (injector._device_spoofing, "Device Spoofing"),
    }

    if req.attack_type.lower() not in attack_map:
        raise HTTPException(status_code=400, detail=f"Unknown attack_type. Supported: {list(attack_map.keys())}")

    fn, label = attack_map[req.attack_type.lower()]
    attack_logs = fn(user, base_log)

    dispatched = 0
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    for log in attack_logs:
        # Sanitize geo_location if list/tuple
        if isinstance(log.get("geo_location"), (list, tuple)) and len(log["geo_location"]) == 2:
            log["geo_location"] = {"lat": float(log["geo_location"][0]), "lon": float(log["geo_location"][1])}
        try:
            res = requests.post(SPRING_BOOT_INGEST_URL, json=log, headers=headers, timeout=3)
            if res.status_code in (200, 201):
                dispatched += 1
            else:
                logger.warning(f"Spring boot returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Failed to post attack log to {SPRING_BOOT_INGEST_URL}: {e}")

    STATS["total_logs_dispatched"] += dispatched
    STATS["attacks_injected"] += 1
    STATS["attack_counts"][label] += 1

    return {
        "status": "success",
        "attack_type": label,
        "target_user": user.entity_id,
        "role": user.role,
        "logs_dispatched": dispatched,
        "sample_payload": attack_logs[0] if attack_logs else {},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("control_api:app", host="0.0.0.0", port=8001, reload=True)
