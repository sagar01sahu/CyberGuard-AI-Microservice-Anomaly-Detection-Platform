

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:


    USER_POOL_SIZE: int = 500

    TICK_INTERVAL_SECONDS: float = 2.0

    TIME_ACCELERATION_FACTOR: int = 15

    ANOMALY_PROBABILITY: float = 0.02



    API_URL: str = "http://localhost:8080/api/v1/logs/ingest"

    API_KEY: str = "change-this-static-api-key-in-production"

    REQUEST_TIMEOUT: int = 5

    MAX_RETRIES: int = 5

    INITIAL_BACKOFF: float = 1.0



    LOGIN_STD_DEV: float = 1.0

    SESSION_MINUTES_MIN: int = 30

    SESSION_MINUTES_MAX: int = 480

    IDLE_PROBABILITY: float = 0.12

    LOGOUT_PROBABILITY: float = 0.05

    RESOURCE_ACCESS_PROBABILITY: float = 0.75