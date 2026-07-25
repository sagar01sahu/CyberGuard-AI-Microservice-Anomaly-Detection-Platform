"""
anomaly_injector.py

Injects realistic cybersecurity attack scenarios.

This module never modifies the original log in-place.
Every attack returns newly created log events.

Author:
    Synthetic Log Generator Project
"""

from __future__ import annotations

import copy
import logging
import random

from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List

from faker import Faker

from config import Config
from models import UserProfile
from utils import iso_timestamp

logger = logging.getLogger(__name__)

fake = Faker()


class AnomalyInjector:
    """
    Responsible for generating attack events.

    Overall anomaly rate is controlled by

        Config.ANOMALY_PROBABILITY

    Supported attacks

        1. Brute Force

        2. Impossible Travel

        3. Lateral Movement

        4. Device Spoofing

        5. Credential Stuffing

        6. Low-and-Slow Exfiltration
    """

    def __init__(

        self,

        users: List[UserProfile]

    ):

        self.users = users

        self.attack_functions = [

            self._brute_force,

            self._impossible_travel,

            self._lateral_movement,

            self._device_spoofing,

            self._credential_stuffing,

            self._low_and_slow

        ]

    # =======================================================
    # Public API
    # =======================================================

    def inject_anomaly(

        self,

        user: UserProfile,

        base_log: Dict

    ) -> List[Dict]:
        """
        Returns

        Either

            [normal_log]

        or

            anomaly events
        """

        probability = random.random()

        if probability > Config.ANOMALY_PROBABILITY:

            return [base_log]

        attack = random.choice(self.attack_functions)

        logger.info("Selected attack: %s", attack.__name__)

        logger.warning(
        "Injecting anomaly: %s for user %s",
        attack.__name__,
        user.entity_id
    )

        return attack(

            user,

            base_log

        )

    # =======================================================
    # Helper Methods
    # =======================================================

    @staticmethod
    def _clone(

        log: Dict

    ) -> Dict:

        return copy.deepcopy(log)

    # -------------------------------------------------------

    @staticmethod
    def _future_time(

        minutes: int = 0,

        seconds: int = 0

    ) -> str:

        return iso_timestamp(

            datetime.utcnow()

            +

            timedelta(

                minutes=minutes,

                seconds=seconds

            )

        )

    # -------------------------------------------------------

    @staticmethod
    def _random_public_ip() -> str:

        return (

            f"{random.randint(11,223)}."

            f"{random.randint(0,255)}."

            f"{random.randint(0,255)}."

            f"{random.randint(1,254)}"

        )

    # -------------------------------------------------------

    @staticmethod
    def _germany_location():

        return {

            "lat": 52.5200,

            "lon": 13.4050

        }

    # -------------------------------------------------------

    @staticmethod
    def _india_location():

        return {

            "lat": 19.0760,

            "lon": 72.8777

        }

    # =======================================================
    # Attack Placeholders
    # =======================================================

        # =======================================================
    # Attack 1 : Brute Force
    # =======================================================

    def _brute_force(
        self,
        user: UserProfile,
        base_log: Dict
    ) -> List[Dict]:
        """
        Generate 15–30 failed login attempts within 10 seconds.
        """

        logger.warning(
            "Generating Brute Force attack for %s",
            user.entity_id
        )

        events: List[Dict] = []

        attempts = random.randint(15, 30)

        start_time = datetime.utcnow()

        for i in range(attempts):

            log = self._clone(base_log)

            log["auth_method"] = "password"

            log["auth_status"] = "failure"

            log["resource_accessed"] = "/login"

            log["timestamp"] = iso_timestamp(
                start_time + timedelta(
                    milliseconds=random.randint(
                        100,
                        9000
                    )
                )
            )

            events.append(log)

        return events

    # =======================================================
    # Attack 2 : Impossible Travel
    # =======================================================

    def _impossible_travel(
        self,
        user: UserProfile,
        base_log: Dict
    ) -> List[Dict]:
        """
        Successful login from home location
        followed by another login
        2–5 minutes later
        from Germany.
        """

        logger.warning(
            "Generating Impossible Travel for %s",
            user.entity_id
        )

        first_login = self._clone(base_log)

        first_login["auth_status"] = "success"

        first_login["timestamp"] = iso_timestamp()

        first_login["geo_location"] = {

            "lat": user.home_geo[0],

            "lon": user.home_geo[1]

        }

        second_login = self._clone(base_log)

        second_login["auth_status"] = "success"

        second_login["source_ip"] = self._random_public_ip()

        second_login["geo_location"] = self._germany_location()

        second_login["timestamp"] = self._future_time(

            minutes=random.randint(2, 5)

        )

        return [

            first_login,

            second_login

        ]

    # -------------------------------------------------------

        # =======================================================
    # Attack 3 : Lateral Movement
    # =======================================================

    def _lateral_movement(
        self,
        user: UserProfile,
        base_log: Dict
    ) -> List[Dict]:
        """
        Simulate unauthorized access to high-value resources.

        A non-privileged user attempts to access
        Engineering/Finance sensitive resources.
        """

        logger.warning(
            "Generating Lateral Movement for %s",
            user.entity_id
        )

        sensitive_resources = [

            "/api/v1/finance/payroll_2026.csv",

            "/api/v1/finance/employee_salary.xlsx",

            "/api/v1/engineering/prod_keys.pem",

            "/api/v1/engineering/source_code.zip",

            "/api/v1/engineering/database_backup.sql",

            "/api/v1/finance/audit_report.pdf"

        ]

        event = self._clone(base_log)

        event["auth_status"] = "success"

        event["resource_accessed"] = random.choice(
            sensitive_resources
        )

        event["timestamp"] = iso_timestamp()

        return [event]

    # =======================================================
    # Attack 4 : Device Spoofing
    # =======================================================

    def _device_spoofing(
        self,
        user: UserProfile,
        base_log: Dict
    ) -> List[Dict]:
        """
        Mid-session device changes unexpectedly.
        """

        logger.warning(
            "Generating Device Spoofing for %s",
            user.entity_id
        )

        spoof_devices = [

            "kali_linux_vm",

            "parrot_security",

            "ubuntu_server",

            "attacker_laptop",

            "windows_hacker_pc"

        ]

        spoof_os = [

            "Kali Linux 2026",

            "Parrot Security OS",

            "Ubuntu 24.04",

            "Windows 11",

            "Debian 12"

        ]

        spoof_agents = [

            "Firefox ESR",

            "curl/8.0",

            "Python Requests",

            "Chrome/128",

            "Headless Chrome"

        ]

        event = self._clone(base_log)

        event["device_id"] = random.choice(
            spoof_devices
        )

        event["os_version"] = random.choice(
            spoof_os
        )

        event["user_agent"] = random.choice(
            spoof_agents
        )

        event["timestamp"] = self._future_time(
            seconds=random.randint(30, 180)
        )

        return [event]

    # -------------------------------------------------------

        # =======================================================
    # Attack 5 : Credential Stuffing
    # =======================================================

    def _credential_stuffing(
        self,
        user: UserProfile,
        base_log: Dict
    ) -> List[Dict]:
        """
        Generate failed login attempts against many users
        from the same malicious IP address.
        """

        logger.warning(
            "Generating Credential Stuffing attack"
        )

        attacker_ip = "185.199.111.99"

        events: List[Dict] = []

        victims = random.sample(
            self.users,
            min(20, len(self.users))
        )

        timestamp = datetime.utcnow()

        for victim in victims:

            event = self._clone(base_log)

            event["entity_id"] = victim.entity_id

            event["auth_status"] = "failure"

            event["auth_method"] = "password"

            event["source_ip"] = attacker_ip

            event["device_id"] = victim.primary_device_id

            event["os_version"] = victim.primary_os

            event["user_agent"] = victim.user_agent

            event["geo_location"] = {
                "lat": victim.home_geo[0],
                "lon": victim.home_geo[1]
            }

            event["resource_accessed"] = "/login"

            event["timestamp"] = iso_timestamp(
                timestamp +
                timedelta(milliseconds=random.randint(50, 500))
            )

            events.append(event)

        return events

    # =======================================================
    # Attack 6 : Low-and-Slow Exfiltration
    # =======================================================

    def _low_and_slow(
        self,
        user: UserProfile,
        base_log: Dict
    ) -> List[Dict]:
        """
        Simulates stealthy exfiltration of sensitive data
        during off-hours.
        """

        logger.warning(
            "Generating Low-and-Slow Exfiltration for %s",
            user.entity_id
        )

        events: List[Dict] = []

        sensitive_chunks = [

            "/api/v1/finance/payroll_chunk_1",

            "/api/v1/finance/payroll_chunk_2",

            "/api/v1/finance/payroll_chunk_3",

            "/api/v1/finance/payroll_chunk_4"

        ]

        base_time = datetime.utcnow().replace(
            hour=3,
            minute=15,
            second=0,
            microsecond=0
        )

        for index, resource in enumerate(sensitive_chunks):

            event = self._clone(base_log)

            event["resource_accessed"] = resource

            event["auth_status"] = "success"

            event["timestamp"] = iso_timestamp(
                base_time +
                timedelta(minutes=index * 3)
            )

            events.append(event)

        return events
    