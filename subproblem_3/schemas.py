"""
schemas.py

Pydantic request/response models for the FastAPI orchestration layer.
Field names use snake_case to exactly match the JSON payload contract
defined by the Spring Boot backend (Sub-Problem 2).

Component 1 of Sub-Problem 3.3 (FastAPI Wrapper).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class GeoLocation(BaseModel):
    lat: float
    lon: float


class LogEvent(BaseModel):
    """A single access-log record, supporting both snake_case and camelCase."""

    entity_id: str = "UNKNOWN"
    role: Optional[str] = Field(default="UNKNOWN", description="Job role, e.g. MARKETING")
    auth_method: str = "password"
    auth_status: str = "success"
    timestamp: str
    source_ip: str = "127.0.0.1"
    geo_location: GeoLocation = Field(default_factory=lambda: GeoLocation(lat=0.0, lon=0.0))
    device_id: str = "unknown_device"
    os_version: str = "UNKNOWN"
    user_agent: str = "UNKNOWN"
    resource_accessed: str = "/unknown"

    @model_validator(mode="before")
    @classmethod
    def preprocess_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            field_map = {
                "entityId": "entity_id",
                "authMethod": "auth_method",
                "authStatus": "auth_status",
                "sourceIp": "source_ip",
                "deviceId": "device_id",
                "osVersion": "os_version",
                "userAgent": "user_agent",
                "resourceAccessed": "resource_accessed",
            }
            for camel, snake in field_map.items():
                if camel in data and snake not in data:
                    data[snake] = data[camel]

            if "geo_location" not in data:
                lat = data.get("geoLat", 0.0)
                lon = data.get("geoLon", 0.0)
                data["geo_location"] = {
                    "lat": lat if lat is not None else 0.0,
                    "lon": lon if lon is not None else 0.0,
                }

            if "timestamp" in data and not isinstance(data["timestamp"], str):
                data["timestamp"] = str(data["timestamp"])

        return data


class LogPayload(BaseModel):
    """
    Request body for POST /predict.
    Accepts both current_event/historical_logs and currentEvent/historicalEvents.
    """

    current_event: LogEvent
    historical_logs: List[LogEvent] = Field(
        default_factory=list,
        max_length=5,
        description="Up to 5 most recent prior logs for this entity_id, oldest first.",
    )

    @model_validator(mode="before")
    @classmethod
    def preprocess_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "currentEvent" in data and "current_event" not in data:
                data["current_event"] = data["currentEvent"]
            if "historicalEvents" in data and "historical_logs" not in data:
                data["historical_logs"] = data["historicalEvents"]
        return data


class PredictionResponse(BaseModel):
    """Response body for POST /predict -- returned to Spring Boot."""

    risk_score: float = Field(..., ge=0.0, le=1.0)
    anomaly_type: str
    explainability: str
    explainability_factors: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def populate_factors(cls, data: Any) -> Any:
        if isinstance(data, dict):
            exp = data.get("explainability", "")
            if exp and not data.get("explainability_factors"):
                data["explainability_factors"] = [exp]
        return data


class ErrorResponse(BaseModel):
    error: str
    detail: str

