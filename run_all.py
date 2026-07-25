#!/usr/bin/env python3
"""
run_all.py

Unified 1-Command System Launcher for the Cybersecurity Anomaly Detection Platform.
Launches all microservices and the React frontend concurrently:

  1. Python AI Engine (FastAPI + HGNN): Port 8000
  2. Spring Boot Backend (Middle Layer): Port 8080 (dev profile with zero-config H2 DB)
  3. Synthetic Log Generator & Control API: Port 8001
  4. React + Vite Frontend Dashboard: Port 5173

Usage:
    python run_all.py
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
NODE_PATH = os.path.expanduser("~/.nvm/versions/node/v24.17.0/bin")
MAVEN_PATH = os.path.expanduser("~/.m2/wrapper/dists/apache-maven-3.9.16-bin/5grr65jo27hi51sujmtcldfovl/apache-maven-3.9.16/bin")
ENV = os.environ.copy()
ENV["PATH"] = f"{NODE_PATH}:{MAVEN_PATH}:{ENV.get('PATH', '')}"
ENV["SPRING_PROFILES_ACTIVE"] = "dev"
ENV["INGEST_API_KEY"] = "change-this-static-api-key-in-production"
ENV["AI_ENGINE_BASE_URL"] = "http://localhost:8000"

processes = []


def log_stream(process, prefix, color_code):
    """Stream stdout/stderr with colored service prefixes."""
    color = f"\033[{color_code}m"
    reset = "\033[0m"
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"{color}[{prefix}]{reset} {line.strip()}", flush=True)


def start_service(name, cmd, cwd, color_code):
    """Launches a microservice subprocess and streams logs."""
    print(f"\033[1;36m[LAUNCHER]\033[0m Starting {name}...")
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append((name, p))
    t = threading.Thread(target=log_stream, args=(p, name, color_code), daemon=True)
    t.start()
    return p


def main():
    print("=" * 70)
    print("\033[1;32m CYBERGUARD AI — UNIFIED MICROSERVICE SYSTEM LAUNCHER\033[0m")
    print("=" * 70)

    # 1. Start Python AI Microservice (subproblem_3)
    start_service(
        "AI-ENGINE",
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        ROOT_DIR / "subproblem_3",
        "35" # Magenta
    )

    # 2. Start Spring Boot Backend (anomaly-detection-backend_v2)
    # 2. Start Spring Boot Backend (anomaly-detection-backend_v2)
    start_service(
        "SPRING-BOOT",
        ["mvn", "spring-boot:run", "-Dspring-boot.run.profiles=dev", "-Dmaven.test.skip=true"],
        ROOT_DIR / "anomaly-detection-backend_v2",
        "34" # Blue
    )

    # 3. Start Generator Control API & Ingestion Stream (subproblem-1_v3)
    start_service(
        "LOG-CONTROL",
        [sys.executable, "-m", "uvicorn", "control_api:app", "--host", "0.0.0.0", "--port", "8001"],
        ROOT_DIR / "subproblem-1_v3",
        "33" # Yellow
    )

    start_service(
        "LOG-STREAM",
        [sys.executable, "synthetic_log_generator.py"],
        ROOT_DIR / "subproblem-1_v3",
        "32" # Green
    )

    # 4. Start React Frontend Dashboard (frontend)
    start_service(
        "FRONTEND",
        ["npm", "run", "dev"],
        ROOT_DIR / "frontend",
        "36" # Cyan
    )

    print("\n" + "=" * 70)
    print("\033[1;32m SYSTEM SUCCESSFULLY STARTED!\033[0m")
    print(" Dashboard URL:      \033[1;36mhttp://localhost:5173\033[0m")
    print(" Spring Boot API:    \033[1;34mhttp://localhost:8080/api/v1/alerts/live\033[0m")
    print(" AI Engine (FastAPI): \033[1;35mhttp://localhost:8000/docs\033[0m")
    print(" Press Ctrl+C to gracefully stop all services.")
    print("=" * 70 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\033[1;31m[LAUNCHER] Shutting down all microservices...\033[0m")
        for name, p in processes:
            print(f"Stopping {name}...")
            p.terminate()
        time.sleep(1)
        for name, p in processes:
            if p.poll() is None:
                p.kill()
        print("\033[1;32m[LAUNCHER] All microservices stopped cleanly.\033[0m")


if __name__ == "__main__":
    main()
