"""
synthetic_log_generator.py

Entry point for the Synthetic Cybersecurity Log Generator.

This script initializes logging, creates the simulation runner,
and starts continuous log generation.

Author:
    Sagar Kumar Sahu
"""

from __future__ import annotations

import logging
import signal
import sys

from simulation import SimulationRunner
from config import Config


def configure_logging() -> None:
    """
    Configure application logging.
    """

    logging.basicConfig(

        level=logging.INFO,

        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),

        datefmt="%Y-%m-%d %H:%M:%S"

    )


def signal_handler(sig, frame):
    """
    Gracefully shutdown the simulator.
    """

    logging.getLogger(__name__).info(
        "Received shutdown signal..."
    )

    logging.getLogger(__name__).info(
        "Stopping simulation."
    )

    sys.exit(0)


def main() -> None:
    """
    Main entry point.
    """

    configure_logging()

    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("Synthetic Cybersecurity Log Generator")
    logger.info("=" * 70)

    logger.info(
        "Users               : %d",
        Config.USER_POOL_SIZE
    )

    logger.info(
        "Anomaly Probability : %.2f%%",
        Config.ANOMALY_PROBABILITY * 100
    )

    logger.info(
        "API Endpoint        : %s",
        Config.API_URL
    )

    logger.info(
        "Time Acceleration   : x%d",
        Config.TIME_ACCELERATION_FACTOR
    )

    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    signal.signal(
        signal.SIGTERM,
        signal_handler
    )

    runner = SimulationRunner(
        time_acceleration_factor=Config.TIME_ACCELERATION_FACTOR
    )

    runner.run()


if __name__ == "__main__":
    main()