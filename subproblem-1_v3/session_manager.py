"""
session_manager.py

Maintains persistent sessions for every simulated user.

Responsibilities
----------------
• Create sessions
• Login users
• Logout users
• Track idle time
• Track last activity
• Store session IDs
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict
from uuid import uuid4

from models import UserProfile
from models import UserSession


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Stores and manages all active user sessions.
    """

    def __init__(self) -> None:

        self.sessions: Dict[str, UserSession] = {}

    # ======================================================

    def create_session(
        self,
        user: UserProfile
    ) -> UserSession:
        """
        Creates an OFFLINE session if one doesn't exist.
        """

        if user.entity_id not in self.sessions:

            self.sessions[user.entity_id] = UserSession(
                entity_id=user.entity_id
            )

        return self.sessions[user.entity_id]

    # ======================================================

    def get_session(
        self,
        entity_id: str
    ) -> UserSession:
        """
        Return session object.
        """

        return self.sessions[entity_id]

    # ======================================================

    def login(
        self,
        user: UserProfile
    ) -> UserSession:
        """
        Logs in a user.
        """

        session = self.create_session(user)

        session.state = "ACTIVE_SESSION"

        session.is_logged_in = True

        session.session_id = uuid4().hex

        session.current_ip = user.primary_ip

        session.current_device = user.primary_device_id

        session.last_login = datetime.utcnow()

        session.last_activity = session.last_login

        session.failed_login_attempts = 0

        session.idle_minutes = 0

        session.resources_accessed.clear()

        logger.info(
            "%s logged in",
            user.entity_id
        )

        return session

    # ======================================================

    def logout(
        self,
        entity_id: str
    ) -> None:
        """
        Logout user.
        """

        session = self.sessions[entity_id]

        session.state = "OFFLINE"

        session.is_logged_in = False

        session.session_id = None

        session.last_activity = datetime.utcnow()

        logger.info(
            "%s logged out",
            entity_id
        )

    # ======================================================

    def update_activity(
        self,
        entity_id: str,
        resource: str
    ) -> None:
        """
        Updates last activity.
        """

        session = self.sessions[entity_id]

        session.last_activity = datetime.utcnow()

        session.resources_accessed.append(resource)

        session.idle_minutes = 0

    # ======================================================

    def increase_idle(
        self,
        entity_id: str,
        minutes: int = 1
    ) -> None:
        """
        Increase idle time.
        """

        session = self.sessions[entity_id]

        session.idle_minutes += minutes

    # ======================================================

    def failed_login(
        self,
        entity_id: str
    ) -> None:
        """
        Record failed authentication.
        """

        session = self.sessions[entity_id]

        session.failed_login_attempts += 1

    # ======================================================

    def reset_failed_login(
        self,
        entity_id: str
    ) -> None:
        """
        Reset failed attempts.
        """

        session = self.sessions[entity_id]

        session.failed_login_attempts = 0

    # ======================================================

    def is_logged_in(
        self,
        entity_id: str
    ) -> bool:
        """
        Check login status.
        """

        return self.sessions[entity_id].is_logged_in

    # ======================================================

    def total_sessions(self) -> int:
        """
        Total session objects.
        """

        return len(self.sessions)

    # ======================================================

    def active_sessions(self) -> int:
        """
        Number of active sessions.
        """

        return sum(
            1
            for session in self.sessions.values()
            if session.is_logged_in
        )

    # ======================================================

    def summary(self) -> dict:
        """
        Runtime statistics.
        """

        return {

            "total_users": len(self.sessions),

            "active_users": self.active_sessions(),

            "offline_users":
                len(self.sessions)
                - self.active_sessions()

        }