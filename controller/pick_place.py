import time
from dataclasses import dataclass
from typing import List

from arm.roarm_client import RoArmClient


@dataclass
class PickPlaceConfig:
    pose_home: List[float]
    pose_above_origin: List[float]
    pose_pick_origin: List[float]
    pose_above_target: List[float]
    pose_place_target: List[float]
    spd: float
    acc: float
    grip_closed_rad: float
    grip_open_rad: float
    z_lift: float = 0.0
    pause_between_moves: float = 0.5


class PickPlaceController:
    def __init__(self, arm: RoArmClient, config: PickPlaceConfig):
        self.arm = arm
        self.cfg = config

    def go_home(self):
        """Move the arm to the configured home pose."""
        self.arm.move_joints_deg_list(
            self.cfg.pose_home,
            spd=self.cfg.spd,
            acc=self.cfg.acc,
        )

    def _lift_z(self, delta_z: float):
        """
        Lift the current end-effector position along Z by delta_z (same units as feedback).

        If something goes wrong (e.g., feedback is unavailable or malformed), returns without lifting.
        The arm will continue from its current position. This is to fail silently so we don't crash the POC.
        """
        if delta_z == 0:
            return

        fb = self.arm.get_feedback()
        if not isinstance(fb, dict):
            print("Warning: Failed to get valid arm feedback for z-lift. Skipping lift operation.")
            return

        try:
            x = fb["x"]
            y = fb["y"]
            z = fb["z"]
            t = fb.get("t", 0.0)
        except KeyError as e:
            key_name = e.args[0] if e.args else 'unknown'
            print(f"Warning: Arm feedback missing expected key '{key_name}'. Skipping lift operation.")
            return

        # Move slightly up (or down) from current pose
        self.arm.move_cartesian(x, y, z + delta_z, t)

    def _pause(self):
        """Small delay to let a motion segment settle before the next one."""
        time.sleep(self.cfg.pause_between_moves)

    def execute_pick_place(self):
        """
        Simple scripted routine:
        - Move to safe home first
        - Go to origin
        - Pick object
        - Move to target
        - Place object
        - Return home
        
        Raises:
            RuntimeError: If network communication with the arm fails
            requests.RequestException: If HTTP request to arm controller fails
            ValueError: If joint angles are invalid or out of range
        """
        spd = self.cfg.spd
        acc = self.cfg.acc

        # Move to safe home first
        self.go_home()
        self._pause()

        # Go to origin
        self.arm.move_joints_deg_list(self.cfg.pose_above_origin, spd=spd, acc=acc)
        self._pause()
        self._lift_z(self.cfg.z_lift)

        self.arm.move_joints_deg_list(self.cfg.pose_pick_origin, spd=spd, acc=acc)
        self._pause()
        self.arm.close_grip(self.cfg.grip_closed_rad)
        self._pause()

        self.arm.move_joints_deg_list(self.cfg.pose_above_origin, spd=spd, acc=acc)
        self._pause()
        self._lift_z(self.cfg.z_lift)

        # Go to target
        self.arm.move_joints_deg_list(self.cfg.pose_above_target, spd=spd, acc=acc)
        self._pause()
        self._lift_z(self.cfg.z_lift)

        self.arm.move_joints_deg_list(self.cfg.pose_place_target, spd=spd, acc=acc)
        self._pause()
        self.arm.open_grip(self.cfg.grip_open_rad)
        self._pause()

        self.arm.move_joints_deg_list(self.cfg.pose_above_target, spd=spd, acc=acc)
        self._pause()
        self._lift_z(self.cfg.z_lift)

        # Return home
        self.go_home()
        self._pause()
