"""
state_machine.py

Probabilistic user behaviour engine.

Responsibilities
----------------
• Login behaviour
• Session lifecycle
• Resource access
• Idle behaviour
• Logout behaviour

This module works together with SessionManager.
"""

from __future__ import annotations

import logging
import random

from datetime import datetime
from typing import Dict
from typing import Optional

import numpy as np

from config import Config
from models import UserProfile
from session_manager import SessionManager


logger = logging.getLogger(__name__)


class ProbabilisticStateMachine:
    """
    Simulates realistic employee behaviour.

    States

        OFFLINE
            ↓
        LOGIN_ATTEMPT
            ↓
        ACTIVE_SESSION
            ↓
        RESOURCE_ACCESS
            ↓
        IDLE
            ↓
        LOGOUT
    """

    def __init__(

        self,

        session_manager: SessionManager

    ):

        self.sessions = session_manager

    # ======================================================

    @staticmethod
    def _login_probability(

        user: UserProfile,

        current_time: datetime

    ) -> float:
        """
        Probability of logging in.

        Gaussian around habitual login hour.
        """

        hour = current_time.hour + current_time.minute / 60

        sigma = Config.LOGIN_STD_DEV

        probability = np.exp(

            -((hour - user.habitual_start_hour) ** 2)

            /

            (2 * sigma * sigma)

        )

        return float(probability)

    # ======================================================

    @staticmethod
    def _choose_resource(

        user: UserProfile

    ) -> str:

        return random.choice(

            user.allowed_resources

        )

    # ======================================================

    def next_state(

        self,

        user: UserProfile,

        current_time: datetime

    ) -> Dict:

        """
        Decide user's next action.

        Returns

        {

            state

            resource

        }
        """

        session = self.sessions.create_session(

            user

        )

        # ===========================================
        # OFFLINE
        # ===========================================

        if session.state == "OFFLINE":

            if random.random() < self._login_probability(

                user,

                current_time

            ):

                self.sessions.login(user)

                return {

                    "state": "LOGIN",

                    "resource": None

                }

            return {

                "state": "OFFLINE",

                "resource": None

            }

        # ===========================================
        # ACTIVE SESSION
        # ===========================================

        if session.state == "ACTIVE_SESSION":

            # logout

            if random.random() < Config.LOGOUT_PROBABILITY:

                self.sessions.logout(

                    user.entity_id

                )

                return {

                    "state": "LOGOUT",

                    "resource": None

                }

            # idle

            if random.random() < Config.IDLE_PROBABILITY:

                session.state = "IDLE"

                self.sessions.increase_idle(

                    user.entity_id

                )

                return {

                    "state": "IDLE",

                    "resource": None

                }

            # resource access

            resource = self._choose_resource(

                user

            )

            self.sessions.update_activity(

                user.entity_id,

                resource

            )

            return {

                "state": "RESOURCE_ACCESS",

                "resource": resource

            }

        # ===========================================
        # IDLE
        # ===========================================

        if session.state == "IDLE":

            if random.random() < 0.60:

                session.state = "ACTIVE_SESSION"

                resource = self._choose_resource(

                    user

                )

                self.sessions.update_activity(

                    user.entity_id,

                    resource

                )

                return {

                    "state": "RESOURCE_ACCESS",

                    "resource": resource

                }

            self.sessions.increase_idle(

                user.entity_id

            )

            return {

                "state": "IDLE",

                "resource": None

            }

        return {

            "state": "OFFLINE",

            "resource": None

        }