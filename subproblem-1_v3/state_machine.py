

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


    def __init__(

        self,

        session_manager: SessionManager

    ):

        self.sessions = session_manager



    @staticmethod
    def _login_probability(

        user: UserProfile,

        current_time: datetime

    ) -> float:


        hour = current_time.hour + current_time.minute / 60

        sigma = Config.LOGIN_STD_DEV

        probability = np.exp(

            -((hour - user.habitual_start_hour) ** 2)

            /

            (2 * sigma * sigma)

        )

        return float(probability)



    @staticmethod
    def _choose_resource(

        user: UserProfile

    ) -> str:

        return random.choice(

            user.allowed_resources

        )



    def next_state(

        self,

        user: UserProfile,

        current_time: datetime

    ) -> Dict:



        session = self.sessions.create_session(

            user

        )



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