"""
profile_generator.py

Generates persistent enterprise user profiles.

Responsibilities
----------------
- Generate realistic enterprise employees
- Weighted role distribution
- Realistic IP addresses
- Geographic distribution
- Habitual working hours
- Device information
"""

from __future__ import annotations

import random
import logging
from typing import List

import numpy as np
from faker import Faker

from constants import (
    UserRole,
    ROLE_DISTRIBUTION,
    ROLE_RESOURCES,
    WORLD_LOCATIONS,
    OPERATING_SYSTEMS,
    BROWSERS,
)

from models import UserProfile
from utils import generate_device_id


logger = logging.getLogger(__name__)

fake = Faker()


class ProfileGenerator:
    """
    Generates persistent enterprise users.
    """

    def __init__(self) -> None:

        self.roles = list(ROLE_DISTRIBUTION.keys())

        self.role_weights = list(ROLE_DISTRIBUTION.values())

    # ----------------------------------------------------------

    @staticmethod
    def _random_private_ip() -> str:
        """
        Generates a realistic private IPv4 address.
        """

        subnet = random.choice(
            [
                "10",
                "172",
                "192"
            ]
        )

        if subnet == "10":

            return (
                f"10."
                f"{random.randint(0,255)}."
                f"{random.randint(0,255)}."
                f"{random.randint(1,254)}"
            )

        if subnet == "172":

            return (
                f"172."
                f"{random.randint(16,31)}."
                f"{random.randint(0,255)}."
                f"{random.randint(1,254)}"
            )

        return (
            f"192.168."
            f"{random.randint(0,255)}."
            f"{random.randint(1,254)}"
        )

    # ----------------------------------------------------------

    @staticmethod
    def _working_hours():

        start = int(
            round(
                np.random.normal(
                    loc=9,
                    scale=1
                )
            )
        )

        start = max(6, min(start, 11))

        end = start + random.randint(7, 9)

        return start, end

    # ----------------------------------------------------------

    def _choose_role(self) -> UserRole:

        return random.choices(

            self.roles,

            weights=self.role_weights,

            k=1

        )[0]

    # ----------------------------------------------------------

    @staticmethod
    def _manager_name() -> str:

        return fake.name()

    # ----------------------------------------------------------

    @staticmethod
    def _risk_score(role: UserRole) -> float:

        mapping = {

            UserRole.ENGINEERING: 0.35,

            UserRole.IT: 0.50,

            UserRole.FINANCE: 0.70,

            UserRole.HR: 0.45,

            UserRole.MARKETING: 0.30,

            UserRole.LEGAL: 0.60,

            UserRole.EXECUTIVE: 0.90

        }

        return mapping[role]

    # ----------------------------------------------------------

    def _generate_profile(

        self,

        index: int

    ) -> UserProfile:

        role = self._choose_role()

        city, country, lat, lon = random.choice(

            WORLD_LOCATIONS

        )

        start_hour, end_hour = self._working_hours()

        profile = UserProfile(

            entity_id=f"user_{index+1}",

            role=role.value,

            department=role.value,

            primary_ip=self._random_private_ip(),

            home_geo=(lat, lon),

            primary_device_id=generate_device_id(),

            primary_os=random.choice(

                OPERATING_SYSTEMS

            ),

            user_agent=random.choice(

                BROWSERS

            ),

            habitual_start_hour=start_hour,

            habitual_end_hour=end_hour,

            allowed_resources=ROLE_RESOURCES[role],

            manager=self._manager_name(),

            country=country,

            city=city,

            timezone="UTC",

            risk_score=self._risk_score(role)

        )

        return profile

    # ----------------------------------------------------------

    def generate_user_pool(

        self,

        count: int = 500

    ) -> List[UserProfile]:
        """
        Generate persistent enterprise users.
        """

        logger.info(

            "Generating %d users...",

            count

        )

        users = [

            self._generate_profile(i)

            for i in range(count)

        ]

        logger.info(

            "Finished generating users."

        )

        return users