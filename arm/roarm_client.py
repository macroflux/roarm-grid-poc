import json
import urllib.parse
from typing import Dict, Any, List

import requests


class RoArmClient:
    """
    Thin HTTP JSON client for Waveshare RoArm-M2-S.

    Uses the /js?json=... HTTP interface described in the official docs.
    """

    def __init__(self, ip: str):
        self.ip = ip.rstrip("/")

    def _send_json(self, payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload)
        encoded = urllib.parse.quote(raw)
        url = f"http://{self.ip}/js?json={encoded}"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            raise RuntimeError(f"Network error during arm command: {payload} to {url}: {e}") from e

    # --- Basic motion commands ---

    def move_init(self) -> str:
        """Move to the initial position. CMD_MOVE_INIT (T=100)."""
        return self._send_json({"T": 100})

    def move_joints_deg(self, b: float, s: float, e: float, h: float, spd: float = 10, acc: float = 10) -> str:
        """
        Control all joints in degrees using CMD_JOINTS_ANGLE_CTRL (T=122).
        """
        cmd = {"T": 122, "b": b, "s": s, "e": e, "h": h, "spd": spd, "acc": acc}
        return self._send_json(cmd)

    def move_cartesian(self, x: float, y: float, z: float, t: float, spd: float = 0.25) -> str:
        """
        Move end effector in XYZ + T (radians) using CMD_XYZT_GOAL_CTRL (T=104).
        """
        cmd = {"T": 104, "x": x, "y": y, "z": z, "t": t, "spd": spd}
        return self._send_json(cmd)

    def get_feedback(self) -> Dict[str, Any]:
        """
        Get coordinates, joint angles, and torque using CMD_SERVO_RAD_FEEDBACK (T=105).
        """
        text = self._send_json({"T": 105})
        # Typically returns a JSON string like {"T":1051,"x":...}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    # --- Gripper control (EoAT) ---

    def set_grip_angle_rad(self, rad: float, spd: float = 0, acc: float = 0) -> str:
        """
        Clamp/wrist control via CMD_EOAT_HAND_CTRL (T=106).
        Default clamp range is ~1.08 (open) to 3.14 (closed).
        """
        cmd = {"T": 106, "cmd": rad, "spd": spd, "acc": acc}
        return self._send_json(cmd)

    def open_grip(self, rad_open: float = 1.20) -> str:
        return self.set_grip_angle_rad(rad_open)

    def close_grip(self, rad_closed: float = 3.14) -> str:
        return self.set_grip_angle_rad(rad_closed)

    # --- Helper for joint lists ---

    def move_joints_deg_list(self, angles: List[float], spd: float = 10, acc: float = 10) -> str:
        """
        Convenience wrapper: angles as [b, s, e, h].
        """
        if len(angles) != 4:
            raise ValueError("Expected 4 joint angles [base, shoulder, elbow, hand]")
        return self.move_joints_deg(angles[0], angles[1], angles[2], angles[3], spd=spd, acc=acc)
