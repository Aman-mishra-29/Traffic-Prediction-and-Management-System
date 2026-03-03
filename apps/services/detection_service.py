import logging
import threading
from typing import Optional

import numpy as np
from ultralytics import YOLO
import supervision as sv

from app.config import MODEL_PATH, CONFIDENCE_THRESHOLD

# =========================================================
# LOGGER
# =========================================================
logger = logging.getLogger(__name__)

# =========================================================
# THREAD LOCK FOR SAFE MODEL ACCESS
# =========================================================
_model_lock = threading.Lock()

# =========================================================
# MODEL INSTANCE (Lazy Loaded)
# =========================================================
_model: Optional[YOLO] = None


# =========================================================
# MODEL LOADER
# =========================================================
def _load_model() -> YOLO:
    """
    Loads YOLO model only once (singleton style).
    Safe for multi-worker production deployment.
    """
    global _model

    if _model is None:
        logger.info("Loading YOLO model...")
        _model = YOLO(MODEL_PATH)
        logger.info("YOLO model loaded successfully.")

    return _model


# =========================================================
# DETECTION FUNCTION
# =========================================================
def detect(frame: np.ndarray) -> sv.Detections:
    """
    Runs object detection on a single frame.

    Args:
        frame (np.ndarray): Input video frame

    Returns:
        supervision.Detections object
    """

    if frame is None:
        raise ValueError("Input frame is None.")

    model = _load_model()

    try:
        with _model_lock:
            results = model(
                frame,
                conf=CONFIDENCE_THRESHOLD,
                verbose=False
            )[0]

        detections = sv.Detections.from_ultralytics(results)

        return detections

    except Exception as e:
        logger.error(f"Detection error: {str(e)}")
        return sv.Detections.empty()


# =========================================================
# WARMUP FUNCTION
# =========================================================
def warmup():
    """
    Runs a dummy inference to warm up model (reduces first-frame latency).
    Useful in production environments.
    """
    logger.info("Warming up model...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    detect(dummy_frame)
    logger.info("Model warmup complete.")