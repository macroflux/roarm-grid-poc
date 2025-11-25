# vision/arm_detector.py
import cv2
import numpy as np
from typing import Optional, Tuple


def detect_tip(
    frame_bgr: np.ndarray,
    lower_hsv: np.ndarray,
    upper_hsv: np.ndarray,
    min_area: int = 50,
) -> Optional[Tuple[int, int]]:
    """
    Detect the pink marker on the robot arm's end effector (gripper tip).
    
    Args:
        frame_bgr: Input frame in BGR color space
        lower_hsv: Lower HSV threshold for pink marker
        upper_hsv: Upper HSV threshold for pink marker
        min_area: Minimum contour area to consider as valid marker
        
    Returns:
        (cx, cy) tuple of marker center in image coordinates, or None if not found
    """
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

    # Clean up noise with morphological operations
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < min_area:
        return None

    M = cv2.moments(largest)
    if M["m00"] == 0:
        return None

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return cx, cy
