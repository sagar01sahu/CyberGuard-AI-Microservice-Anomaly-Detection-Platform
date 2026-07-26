
from __future__ import annotations

import json
import logging
from datetime import datetime

from profile_generator import ProfileGenerator
from session_manager import SessionManager
from state_machine import ProbabilisticStateMachine
from anomaly_injector import AnomalyInjector
from dispatcher import NetworkDispatcher
from utils import create_log

logging.basicConfig(

    level=logging.INFO,

    format="%(message)s"

)

logger = logging.getLogger(__name__)


def print_header(title: str):

    print()

    print("=" * 70)

    print(title)

    print("=" * 70)


def main():



    print_header(

        "1. Generating User Profiles"

    )

    generator = ProfileGenerator()

    users = generator.generate_user_pool(500)

    print(f"✓ Generated {len(users)} users")

    from dataclasses import asdict
    print(
        json.dumps(
            asdict(users[0]),
            indent=4,
            default=str
        )
    )



    print_header(

        "2. Testing Session Manager"

    )

    session_manager = SessionManager()

    session = session_manager.login(users[0])

    print(session)

    print(

        "✓ Session Created"

    )

    session_manager.logout(

        users[0].entity_id

    )

    print(

        "✓ Logout Successful"

    )



    print_header(

        "3. Testing State Machine"

    )

    state_machine = ProbabilisticStateMachine(

        session_manager

    )

    result = state_machine.next_state(

        users[0],

        datetime.utcnow()

    )

    print(result)

    print("✓ State Machine OK")



    print_header(

        "4. Creating Base Log"

    )

    log = create_log(

        users[0],

        users[0].allowed_resources[0]

    )

    print(

        json.dumps(

            log,

            indent=4

        )

    )

    print("✓ JSON OK")



    print_header(

        "5. Testing Anomaly Injector"

    )

    injector = AnomalyInjector(

        users

    )

    attacks = [

        injector._brute_force,

        injector._impossible_travel,

        injector._lateral_movement,

        injector._device_spoofing,

        injector._credential_stuffing,

        injector._low_and_slow

    ]

    names = [

        "Brute Force",

        "Impossible Travel",

        "Lateral Movement",

        "Device Spoofing",

        "Credential Stuffing",

        "Low Slow Exfiltration"

    ]

    for attack, name in zip(

        attacks,

        names

    ):

        logs = attack(

            users[0],

            log

        )

        print(

            f"✓ {name:<25} {len(logs)} events"

        )



    print_header(

        "6. Testing Dispatcher"

    )

    dispatcher = NetworkDispatcher()

    print(

        "If Spring Boot (or fake_server.py) "

        "is NOT running, retries are expected."

    )

    dispatcher.send_log(log)

    print("✓ Dispatcher executed")



    print_header(

        "7. Integration Test"

    )

    for i in range(5):

        result = state_machine.next_state(

            users[0],

            datetime.utcnow()

        )

        print(result)

    print()

    print("✓ State Machine Integration OK")



    print_header(

        "PROJECT VERIFIED"

    )

    print()

    print("Everything executed successfully.")

    print()

    print("Next Step:")

    print()

    print("1. Run Spring Boot")

    print()

    print("2. Run synthetic_log_generator.py")

    print()

    print("Watch logs streaming continuously.")


if __name__ == "__main__":

    main()