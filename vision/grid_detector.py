import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)


def _largest_contour_box(mask: np.ndarray, min_area: int) -> Optional[Box]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < min_area:
        return None

    x, y, w, h = cv2.boundingRect(largest)
    return Box(x, y, w, h)


def detect_zones(
    frame_bgr: np.ndarray,
    blue_lower: np.ndarray,
    blue_upper: np.ndarray,
    red_lower: np.ndarray,
    red_upper: np.ndarray,
    min_zone_area: int,
) -> Tuple[Optional[Box], Optional[Box]]:
    """
    Returns (origin_box, target_box) detected from frame, or (None, None)
    if no suitable contours are found.
    """
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    red_mask = cv2.inRange(hsv, red_lower, red_upper)

    origin_box = _largest_contour_box(blue_mask, min_zone_area)
    target_box = _largest_contour_box(red_mask, min_zone_area)

    return origin_box, target_box


def draw_box(frame: np.ndarray, box: Box, color: Tuple[int, int, int], label: str):
    cv2.rectangle(frame, (box.x, box.y), (box.x + box.w, box.y + box.h), color, 2)
    cx, cy = box.center
    cv2.circle(frame, (cx, cy), 4, color, -1)
    cv2.putText(
        frame,
        label,
        (box.x, box.y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
        cv2.LINE_AA,
    )
