import cv2
import numpy as np
from typing import Optional, Tuple

from .grid_detector import Box


def detect_object_in_origin(
    frame_bgr: np.ndarray,
    origin_box: Box,
    min_object_area: int,
    object_min_saturation: int = 60,
    object_min_value: int = 60,
    object_max_value: int = 220,
) -> Optional[Tuple[int, int]]:
    """
    Detect a 'real' object inside the origin zone.

    We assume:
      - Background is white-ish (low saturation, high value)
      - Robot arm is black-ish (low value)
      - Object is reasonably colorful and mid-bright

    Returns (cx, cy) in full-frame coordinates, or None if nothing found.
    """
    x, y, w, h = origin_box.x, origin_box.y, origin_box.w, origin_box.h

    # Optionally crop a bit inside the box to avoid tape edges
    margin = int(min(w, h) * 0.10)
    x0 = x + margin
    y0 = y + margin
    x1 = x + w - margin
    y1 = y + h - margin

    # Bounds checking to ensure coordinates don't exceed frame boundaries
    y0 = max(0, y0)
    x0 = max(0, x0)
    y1 = min(frame_bgr.shape[0], y1)
    x1 = min(frame_bgr.shape[1], x1)

    if x1 <= x0 or y1 <= y0:
        return None

    roi = frame_bgr[y0:y1, x0:x1]
    if roi.size == 0:
        return None

    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    _, s_ch, v_ch = cv2.split(hsv)

    # Sufficiently colorful
    sat_mask = cv2.inRange(s_ch, object_min_saturation, 255)
    # Not too dark, not too bright
    val_mask = cv2.inRange(v_ch, object_min_value, object_max_value)

    # Combined mask: colorful AND mid-bright
    mask = cv2.bitwise_and(sat_mask, val_mask)

    # Optional: clean up noise
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < min_object_area:
        return None

    M = cv2.moments(largest)
    if M["m00"] == 0:
        return None

    cx_local = int(M["m10"] / M["m00"])
    cy_local = int(M["m01"] / M["m00"])

    # Map back into full-frame coords (remember we cropped with margin)
    cx = x0 + cx_local
    cy = y0 + cy_local
    return cx, cy


def draw_object_center(frame: np.ndarray, center: Tuple[int, int]):
    cx, cy = center
    cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1)
    cv2.putText(
        frame,
        "OBJECT",
        (cx + 5, cy - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )
