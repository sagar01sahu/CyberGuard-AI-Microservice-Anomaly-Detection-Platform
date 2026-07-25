"""
=============================================================
Synthetic Cybersecurity Log Generator Validator

This file validates the entire project.

Run

python project_validator.py

=============================================================
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

from config import Config
from constants import *
from models import UserProfile
from profile_generator import ProfileGenerator
from session_manager import SessionManager
from state_machine import ProbabilisticStateMachine
from anomaly_injector import AnomalyInjector
from dispatcher import NetworkDispatcher
from simulation import SimulationRunner
from utils import create_log

logging.basicConfig(

    level=logging.INFO,

    format="%(message)s"

)

logger = logging.getLogger(__name__)


# ==========================================================
# Fake Spring Boot Server
# ==========================================================

received_logs = []


class FakeHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        if self.path != "/api/v1/logs/ingest":

            self.send_response(404)

            self.end_headers()

            return

        length = int(self.headers["Content-Length"])

        body = self.rfile.read(length)

        payload = json.loads(body.decode())

        received_logs.append(payload)

        self.send_response(200)

        self.end_headers()

    def log_message(self, format, *args):

        return


def start_fake_server():

    server = HTTPServer(

        ("localhost", 8080),

        FakeHandler

    )

    thread = threading.Thread(

        target=server.serve_forever,

        daemon=True

    )

    thread.start()

    return server


# ==========================================================
# Validator
# ==========================================================

class ProjectValidator:

    def __init__(self):

        self.total = 0

        self.pass_count = 0

        self.fail_count = 0

        self.users = []

        self.session_manager = None

        self.state_machine = None

        self.injector = None

        self.dispatcher = None

    # ======================================================

    def title(self, text):

        print()

        print("=" * 70)

        print(text)

        print("=" * 70)

    # ======================================================

    def success(self, text):

        self.total += 1

        self.pass_count += 1

        print(f"[PASS] {text}")

    # ======================================================

    def fail(self, text):

        self.total += 1

        self.fail_count += 1

        print(f"[FAIL] {text}")