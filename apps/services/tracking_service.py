import logging
import threading
from typing import Optional

import supervision as sv

from app.config import MAX_TRACKED_VEHICLES

# =========================================================
# LOGGER
# =========================================================
logger = logging.getLogger(__name__)

# =========================================================
# THREAD LOCK (Multi-worker safe)
# =========================================================
_tracker_lock = threading.Lock()

# =========================================================
# TRACKER INSTANCE (Singleton Pattern)
# =========================================================
_tracker: Optional[sv.ByteTrack] = None


# =========================================================
# TRACKER INITIALIZER
# =========================================================
def _initialize_tracker() -> sv.ByteTrack:
    """
    Initializes ByteTrack tracker with production-safe configuration.
    Ensures singleton instance per process.
    """
    global _tracker

    if _tracker is None:
        logger.info("Initializing ByteTrack tracker...")
        _tracker = sv.ByteTrack(
            track_activation_threshold=0.25,
            lost_track_buffer=30,
            minimum_matching_threshold=0.8,
            frame_rate=30
        )
        logger.info("ByteTrack tracker initialized successfully.")

    return _tracker


# =========================================================
# TRACKING FUNCTION
# =========================================================
def track(detections: sv.Detections) -> sv.Detections:
    """
    Applies ByteTrack tracking to detection results.

    Args:
        detections (sv.Detections): Output from detection_service

    Returns:
        sv.Detections with tracker IDs assigned
    """

    if detections is None:
        raise ValueError("Detections cannot be None.")

    tracker = _initialize_tracker()

    try:
        with _tracker_lock:
            tracked = tracker.update_with_detections(detections)

        # Optional safety limit
        if len(tracked) > MAX_TRACKED_VEHICLES:
            logger.warning("Exceeded max tracked vehicles limit.")
            tracked = tracked[:MAX_TRACKED_VEHICLES]

        return tracked

    except Exception as e:
        logger.error(f"Tracking error: {str(e)}")
        return detections  # fallback (no tracking)


# =========================================================
# RESET TRACKER (Admin/Recovery Use)
# =========================================================
def reset_tracker():
    """
    Resets tracker state safely.
    Useful in long-running production systems.
    """
    global _tracker

    with _tracker_lock:
        logger.warning("Resetting tracker instance...")
        _tracker = None


# =========================================================
# GET TRACKER STATUS
# =========================================================
def get_tracker_status() -> dict:
    """
    Returns tracker state for health monitoring.
    """
    return {
        "tracker_initialized": _tracker is not None
    }