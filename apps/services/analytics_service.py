import time
import threading
import numpy as np
from typing import Dict, List

from app.config import (
    PIXELS_PER_METER,
    FPS,
    SPEED_LIMIT
)

# =========================================================
# THREAD LOCK (For Safe Multi-Worker Access)
# =========================================================
_lock = threading.Lock()

# =========================================================
# IN-MEMORY STATE (Can be replaced with Redis/DB later)
# =========================================================
_vehicle_positions: Dict[int, tuple] = {}
_vehicle_speeds: Dict[int, float] = {}
_violations: List[dict] = []

_latest_stats = {
    "active_vehicles": 0,
    "average_speed": 0.0,
    "overspeed_count": 0,
    "total_tracked_vehicles": 0,
    "last_updated": None
}


# =========================================================
# MAIN ANALYTICS FUNCTION
# =========================================================
def process_detections(detections) -> Dict:
    """
    Processes tracked detections and updates traffic statistics.

    Args:
        detections: Supervision detections object with tracker IDs

    Returns:
        Dictionary containing latest traffic statistics
    """

    global _latest_stats

    active_count = 0
    speed_sum = 0.0
    overspeed_count = 0

    for box, tracker_id in zip(detections.xyxy, detections.tracker_id):

        if tracker_id is None:
            continue

        active_count += 1

        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        # ---------------------------------------------
        # SPEED ESTIMATION (Pixel-to-Meter Conversion)
        # ---------------------------------------------
        if tracker_id in _vehicle_positions:
            px, py = _vehicle_positions[tracker_id]

            pixel_distance = np.hypot(cx - px, cy - py)
            meters = pixel_distance / PIXELS_PER_METER
            speed_mps = meters * FPS
            speed_kmh = speed_mps * 3.6
        else:
            speed_kmh = 0.0

        _vehicle_positions[tracker_id] = (cx, cy)
        _vehicle_speeds[tracker_id] = speed_kmh

        speed_sum += speed_kmh

        # ---------------------------------------------
        # OVERSPEED DETECTION
        # ---------------------------------------------
        if speed_kmh > SPEED_LIMIT:
            overspeed_count += 1

            _violations.append({
                "type": "overspeed",
                "vehicle_id": int(tracker_id),   
                "speed_kmh": float(round(speed_kmh, 2)),
                "limit": float(SPEED_LIMIT),
                "timestamp": float(time.time())
            })

    # ---------------------------------------------
    # CALCULATE AVERAGE SPEED
    # ---------------------------------------------
    average_speed = (
        round(speed_sum / active_count, 2)
        if active_count > 0
        else 0.0
    )

    # ---------------------------------------------
    # THREAD-SAFE UPDATE
    # ---------------------------------------------
    with _lock:
        _latest_stats = {
            "active_vehicles": active_count,
            "average_speed": average_speed,
            "overspeed_count": overspeed_count,
            "total_tracked_vehicles": len(_vehicle_positions),
            "last_updated": time.time()
        }

    return _latest_stats


# =========================================================
# GETTERS (Used by API Layer)
# =========================================================
def get_latest_stats() -> Dict:
    with _lock:
        return _latest_stats.copy()


def get_recent_violations(limit: int = 20) -> Dict:
    with _lock:
        latest = _violations[-limit:] if len(_violations) > 0 else []
        return {
            "count": len(_violations),
            "latest": latest
        }


# =========================================================
# RESET FUNCTION (Optional Admin Use)
# =========================================================
def reset_analytics():
    """
    Clears tracking state (useful for testing or admin reset)
    """
    global _vehicle_positions, _vehicle_speeds, _violations, _latest_stats

    with _lock:
        _vehicle_positions.clear()
        _vehicle_speeds.clear()
        _violations.clear()

        _latest_stats = {
            "active_vehicles": 0,
            "average_speed": 0.0,
            "overspeed_count": 0,
            "total_tracked_vehicles": 0,
            "last_updated": None
        }