from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# =========================================================
# SYSTEM SCHEMAS
# =========================================================

class ServiceInfo(BaseModel):
    service: str = Field(..., example="Smart Traffic AI Backend")
    version: str = Field(..., example="1.0.0")
    status: str = Field(..., example="running")


class HealthStatus(BaseModel):
    status: str = Field(..., example="healthy")
    tracker: dict
    message: str = Field(..., example="System operational")


# =========================================================
# TRAFFIC ANALYTICS SCHEMAS
# =========================================================

class TrafficStats(BaseModel):
    active_vehicles: int = Field(..., example=8)
    average_speed: float = Field(..., example=45.3)
    overspeed_count: int = Field(..., example=2)
    total_tracked_vehicles: int = Field(..., example=54)
    last_updated: Optional[float] = Field(
        None,
        description="Unix timestamp of last analytics update"
    )


class TrafficStatsResponse(BaseModel):
    success: bool = True
    data: TrafficStats


# =========================================================
# VIOLATION SCHEMAS
# =========================================================

class Violation(BaseModel):
    type: str = Field(..., example="overspeed")
    vehicle_id: int = Field(..., example=12)
    speed_kmh: float = Field(..., example=78.5)
    limit: float = Field(..., example=60.0)
    timestamp: float = Field(
        ...,
        description="Unix timestamp when violation occurred"
    )


class ViolationsResponse(BaseModel):
    success: bool = True
    count: int
    latest: List[Violation]


# =========================================================
# ADMIN SCHEMAS
# =========================================================

class ResetResponse(BaseModel):
    success: bool = True
    message: str = Field(..., example="Analytics state reset successfully.")


# =========================================================
# FUTURE EXTENSIONS (Optional)
# =========================================================

class EmergencyVehicleStatus(BaseModel):
    detected: bool = Field(..., example=True)
    vehicle_id: Optional[int] = Field(None, example=25)


class RedLightViolation(BaseModel):
    vehicle_id: int
    timestamp: float
    intersection_id: Optional[str] = None


class WrongLaneViolation(BaseModel):
    vehicle_id: int
    lane_id: str
    timestamp: float