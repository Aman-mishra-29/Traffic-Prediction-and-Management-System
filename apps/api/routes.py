from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from app.services.analytics_service import (
    get_latest_stats,
    get_recent_violations,
    reset_analytics
)

from app.services.tracking_service import get_tracker_status

router = APIRouter()

# =========================================================
# ROOT INFO ENDPOINT
# =========================================================
@router.get("/", tags=["System"])
def root():
    return {
        "service": "Smart Traffic AI Backend",
        "version": "1.0.0",
        "status": "running"
    }


# =========================================================
# TRAFFIC STATISTICS ENDPOINT
# =========================================================
@router.get("/stats", tags=["Analytics"])
def get_stats():
    """
    Returns real-time traffic statistics.
    """
    stats = get_latest_stats()

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": stats
        }
    )


# =========================================================
# VIOLATIONS ENDPOINT (Paginated)
# =========================================================
from app.models.schemas import ViolationsResponse

@router.get(
    "/violations",
    tags=["Analytics"],
    response_model=ViolationsResponse
)
def get_violations(
    limit: Optional[int] = Query(20, ge=1, le=100)
):
    from app.services.analytics_service import get_recent_violations
    data = get_recent_violations(limit=limit)

    return {
        "success": True,
        "count": data["count"],
        "latest": data["latest"]
    }


# =========================================================
# HEALTH CHECK ENDPOINT
# =========================================================
@router.get("/health", tags=["System"])
def health_check():
    """
    Returns backend system health.
    """
    tracker_status = get_tracker_status()

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "tracker": tracker_status,
            "message": "System operational"
        }
    )


# =========================================================
# ADMIN RESET ENDPOINT
# =========================================================
@router.post("/admin/reset", tags=["Admin"])
def reset_system():
    """
    Resets analytics state.
    Use carefully in production.
    """
    try:
        reset_analytics()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Analytics state reset successfully."
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset system: {str(e)}"
        )
        
print("API ROUTES LOADED")