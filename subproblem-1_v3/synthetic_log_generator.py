from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request

# Setup Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-18s | %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv("API_URL", "http://backend:8080/api/v1/logs/ingest")
PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "0.0.0.0")


class AttackControlHandler(BaseHTTPRequestHandler):
    """HTTP Server on port 8001 to handle Attack Simulator requests from the React UI."""

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        if "/inject-attack" in self.path:
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = (
                    self.rfile.read(length).decode("utf-8")
                    if length > 0
                    else "{}"
                )
                payload = json.loads(body)

                attack_type = payload.get("attack_type", "brute_force")
                logger.warning(
                    f"[ATTACK-SIMULATOR] Injected attack scenario requested: {attack_type}"
                )

                # Send an attack log immediately to the backend
                self.dispatch_attack_log(payload)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._set_cors()
                self.end_headers()

                response = {
                    "status": "success",
                    "message": f"Attack '{attack_type}' successfully injected into simulation stream!",
                    "data": payload,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                logger.error(
                    f"[ATTACK-SIMULATOR] Error processing attack injection: {e}"
                )
                self.send_response(500)
                self._set_cors()
                self.end_headers()
        else:
            self.send_response(404)
            self._set_cors()
            self.end_headers()

    def dispatch_attack_log(self, attack_payload):
        """Dispatches an anomalous log packet directly to the Spring Boot backend."""
        try:
            user_id = attack_payload.get("target_user", "user_16")
            log_data = {
                "entity_id": user_id,
                "role": "MARKETING",
                "auth_method": "password",
                "auth_status": "failure",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "source_ip": "10.250.81.24",
                "geo_location": {"lat": 35.6895, "lon": 139.6917},
                "device_id": "device-505bb5ad47",
                "os_version": "Windows 11",
                "user_agent": "Chrome/126",
                "resource_accessed": "/login",
            }
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(log_data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": "change-this-static-api-key-in-production",
                },
                method="POST",
            )
            with urllib.request.urlopen(req) as response:
                logger.info(f"Attack log dispatched successfully: {response.status}")
        except Exception as ex:
            logger.error(f"Failed to dispatch attack log to backend: {ex}")

    def log_message(self, format, *args):
        return  # Suppress default HTTP server noise


def start_control_server():
    server = HTTPServer((HOST, PORT), AttackControlHandler)
    logger.info(
        f"[ATTACK-SIMULATOR] Control API listening on http://{HOST}:{PORT}/api/v1/generator/inject-attack"
    )
    server.serve_forever()


def run_log_generator():
    """Continuously generates normal synthetic logs and sends them to the Spring Boot backend."""
    logger.info(f"Starting continuous log stream to backend at {API_URL}...")

    roles = ["ENGINEERING", "HR", "FINANCE", "MARKETING", "IT"]
    resources = ["/api/v1/engineering/github", "/api/v1/hr/recruitment", "/api/v1/finance/payroll", "/api/v1/it/monitoring"]

    while True:
        try:
            user_num = random.randint(1, 500)
            log_data = {
                "entity_id": f"user_{user_num}",
                "role": random.choice(roles),
                "auth_method": "token",
                "auth_status": "success",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "source_ip": f"{random.randint(10, 200)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
                "geo_location": {"lat": 52.52, "lon": 13.405},
                "device_id": f"device-{user_num}eebc2c2a",
                "os_version": "Windows 11",
                "user_agent": "Mozilla/5.0",
                "resource_accessed": random.choice(resources),
            }

            req = urllib.request.Request(
                API_URL,
                data=json.dumps(log_data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": "change-this-static-api-key-in-production",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        logger.info(f"Successfully sent log for user_{user_num}")
            except Exception as net_err:
                logger.warning(f"Backend connection waiting... ({net_err})")

            time.sleep(2.0)  # Tick delay between logs
        except Exception as ex:
            logger.exception(f"Error in generator loop: {ex}")
            time.sleep(3.0)


def main():
    logger.info("=" * 70)
    logger.info("Starting CyberGuard AI Synthetic Log & Control Service...")
    logger.info("=" * 70)

    # 1. Start the HTTP Attack Control Server on a background thread (Port 8001)
    control_thread = threading.Thread(target=start_control_server, daemon=True)
    control_thread.start()

    # 2. Run the continuous log generation stream on the main thread
    run_log_generator()


if __name__ == "__main__":
    main()