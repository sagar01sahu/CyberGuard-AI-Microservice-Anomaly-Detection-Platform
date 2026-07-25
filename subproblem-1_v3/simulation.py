"""
simulation.py

Main orchestration engine for the synthetic log generator.

Responsibilities
----------------
• Generate users
• Maintain simulation clock
• Execute state machine
• Generate logs
• Inject anomalies
• Send logs to Spring Boot
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from config import Config
from profile_generator import ProfileGenerator
from session_manager import SessionManager
from state_machine import ProbabilisticStateMachine
from anomaly_injector import AnomalyInjector
from dispatcher import NetworkDispatcher
from utils import create_log

logger = logging.getLogger(__name__)


class SimulationRunner:
    """
    Controls the complete simulation.
    """

    def __init__(
        self,
        time_acceleration_factor: int = Config.TIME_ACCELERATION_FACTOR
    ) -> None:

        self.time_factor = time_acceleration_factor

        self.profile_generator = ProfileGenerator()

        self.users = self.profile_generator.generate_user_pool(
            Config.USER_POOL_SIZE
        )

        self.session_manager = SessionManager()

        self.state_machine = ProbabilisticStateMachine(
            self.session_manager
        )

        self.anomaly_injector = AnomalyInjector(
            self.users
        )

        self.dispatcher = NetworkDispatcher()

        self.current_time = datetime.utcnow()

        logger.info(
            "Simulation initialized with %d users.",
            len(self.users)
        )

    # ======================================================

    def simulation_tick(self) -> None:
        """
        Execute one simulation cycle.
        """

        generated_logs = 0

        for user in self.users:

            result = self.state_machine.next_state(
                user,
                self.current_time
            )

            state = result["state"]

            # -----------------------------
            # User is offline
            # -----------------------------

            if state == "OFFLINE":

                continue

            # -----------------------------
            # Login event
            # -----------------------------

            if state == "LOGIN":

                log = create_log(
                    user,
                    "/login"
                )

            # -----------------------------
            # Logout
            # -----------------------------

            elif state == "LOGOUT":

                log = create_log(
                    user,
                    "/logout"
                )

            # -----------------------------
            # Idle
            # -----------------------------

            elif state == "IDLE":

                log = create_log(
                    user,
                    "/idle"
                )

            # -----------------------------
            # Resource Access
            # -----------------------------

            else:

                log = create_log(
                    user,
                    result["resource"]
                )

            logs = self.anomaly_injector.inject_anomaly(
                user,
                log
            )

            for payload in logs:

                self.dispatcher.send_log(
                    payload
                )

                generated_logs += 1

        logger.info(
            "Tick completed | Logs Generated : %d",
            generated_logs
        )

    # ======================================================

    def advance_time(self) -> None:
        """
        Move simulated time.
        """

        self.current_time += timedelta(
            minutes=self.time_factor
        )

    # ======================================================

    def run(
        self,
        realtime_delay: float = Config.TICK_INTERVAL_SECONDS
    ) -> None:
        """
        Run forever.
        """

        logger.info(
            "Simulation started..."
        )

        while True:

            self.simulation_tick()

            self.advance_time()

            time.sleep(realtime_delay)