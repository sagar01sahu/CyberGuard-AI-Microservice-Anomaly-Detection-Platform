

from datetime import datetime
from uuid import uuid4

from models import UserProfile


def generate_device_id() -> str:
    return f"device-{uuid4().hex[:10]}"


def generate_session_id() -> str:
    return uuid4().hex


def iso_timestamp(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat(timespec="milliseconds") + "Z"


def create_log(
        user: UserProfile,
        resource: str,
        auth_status: str = "success"
):
    return {
        "entity_id": user.entity_id,
        "role": getattr(user, "role", "UNKNOWN"),  # <--- ADDED ROLE HERE
        "auth_method": "password",
        "auth_status": auth_status,
        "timestamp": iso_timestamp(),
        "source_ip": user.primary_ip,
        "geo_location": {
            "lat": user.home_geo[0],
            "lon": user.home_geo[1]
        },
        "device_id": user.primary_device_id,
        "os_version": user.primary_os,
        "user_agent": user.user_agent,
        "resource_accessed": resource
    }