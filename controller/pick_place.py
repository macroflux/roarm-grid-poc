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


class PickPlaceController:
    def __init__(self, arm: RoArmClient, config: PickPlaceConfig):
        self.arm = arm
        self.cfg = config

    def execute_pick_place(self):
        """
        Simple scripted routine:
        - Move above origin
        - Descend to pick pose, close grip
        - Move back up
        - Move above target
        - Descend to place pose, open grip
        - Move back up
        """
        spd = self.cfg.spd
        acc = self.cfg.acc

        # Move to safe home first (optional)
        self.arm.move_joints_deg_list(self.cfg.pose_home, spd=spd, acc=acc)

        # Go to origin
        self.arm.move_joints_deg_list(self.cfg.pose_above_origin, spd=spd, acc=acc)
        self.arm.move_joints_deg_list(self.cfg.pose_pick_origin, spd=spd, acc=acc)
        self.arm.close_grip(self.cfg.grip_closed_rad)
        self.arm.move_joints_deg_list(self.cfg.pose_above_origin, spd=spd, acc=acc)

        # Go to target
        self.arm.move_joints_deg_list(self.cfg.pose_above_target, spd=spd, acc=acc)
        self.arm.move_joints_deg_list(self.cfg.pose_place_target, spd=spd, acc=acc)
        self.arm.open_grip(self.cfg.grip_open_rad)
        self.arm.move_joints_deg_list(self.cfg.pose_above_target, spd=spd, acc=acc)

        # Optionally return home
        self.arm.move_joints_deg_list(self.cfg.pose_home, spd=spd, acc=acc)
