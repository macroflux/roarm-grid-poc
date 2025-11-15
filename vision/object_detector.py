import cv2
import numpy as np
from typing import Optional, Tuple

from .grid_detector import Box


def detect_object_in_origin(
    frame_bgr: np.ndarray,
    origin_box: Box,
    min_object_area: int,
) -> Optional[Tuple[int, int]]:
    """
    Returns (cx, cy) of the largest non-background blob inside origin box,
    or None if no significant object is detected.
    """

    x, y, w, h = origin_box.x, origin_box.y, origin_box.w, origin_box.h
    roi = frame_bgr[y : y + h, x : x + w]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Simple adaptive threshold; you may want to adjust this depending on your table/lighting.
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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

    # Convert to frame coordinates
    cx = x + cx_local
    cy = y + cy_local
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
