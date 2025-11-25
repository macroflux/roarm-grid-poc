# controller/visual_push.py
from dataclasses import dataclass
from typing import Tuple

from arm.roarm_client import RoArmClient


@dataclass
class VisualPushConfig:
    safe_z: float           # cartesian Z height for sliding (mm)
    gain_xy: float          # scale from pixel error -> (x,y) delta in mm
    max_step_mm: float      # clamp per-step motion
    align_tolerance_px: int # how close in image before we start pushing
    push_steps: int         # how many increments to push
    push_step_px: float     # how far in image per push step


class VisualPushController:
    """
    Image-based visual servoing controller for pushing objects.
    
    Uses the camera view to:
    1. Align the robot tip with the object center in image space
    2. Push the object from origin toward target in image space
    
    This is a simple "poor man's IBVS" that assumes flat table and
    approximately linear mapping between workspace XY and image coordinates.
    """
    
    def __init__(self, arm: RoArmClient, cfg: VisualPushConfig):
        self.arm = arm
        self.cfg = cfg

    def _get_cartesian(self):
        """Get current cartesian position from arm feedback."""
        fb = self.arm.get_feedback()
        return fb["x"], fb["y"], fb["z"], fb.get("t", 0.0)

    def _nudge_xy(self, dx_px: float, dy_px: float):
        """
        Move the arm based on pixel delta in image space.
        
        Very simple mapping: pixel delta -> workspace delta.
        dx_px, dy_px are in image coordinates (right, down).
        We map them linearly with cfg.gain_xy and clamp length.
        
        Note: You may need to tune the sign/mapping based on your
        camera orientation relative to the workspace.
        """
        x, y, _, t = self._get_cartesian()

        # Image right (+u) ~= +x, image down (+v) ~= +y (tune sign as needed)
        dx_mm = dx_px * self.cfg.gain_xy
        dy_mm = dy_px * self.cfg.gain_xy

        # Clamp step magnitude
        mag = (dx_mm ** 2 + dy_mm ** 2) ** 0.5
        if mag > self.cfg.max_step_mm and mag > 0:
            scale = self.cfg.max_step_mm / mag
            dx_mm *= scale
            dy_mm *= scale

        self.arm.move_cartesian(x + dx_mm, y + dy_mm, self.cfg.safe_z, t)

    def align_tip_to_object(
        self,
        tip_center: Tuple[int, int],
        obj_center: Tuple[int, int],
    ) -> bool:
        """
        Move the tip towards the object center in image space.
        
        Call this in a loop while updating tip_center/obj_center from vision
        each iteration. Returns True when aligned within tolerance.
        
        Args:
            tip_center: (u, v) pixel coordinates of robot tip marker
            obj_center: (u, v) pixel coordinates of object center
            
        Returns:
            True if already aligned within tolerance, False otherwise
        """
        tip_u, tip_v = tip_center
        obj_u, obj_v = obj_center

        du = obj_u - tip_u
        dv = obj_v - tip_v

        if abs(du) < self.cfg.align_tolerance_px and abs(dv) < self.cfg.align_tolerance_px:
            return True  # Already aligned

        # Move tip towards object
        self._nudge_xy(du, dv)
        return False

    def push_towards_target_direction(
        self,
        from_center: Tuple[int, int],
        to_center: Tuple[int, int],
    ):
        """
        Push the object along the line from origin square to target square.
        
        After alignment, this executes a series of small steps in the
        direction from origin->target in image space.
        
        Args:
            from_center: (u, v) pixel coordinates of origin square center
            to_center: (u, v) pixel coordinates of target square center
        """
        fu, fv = from_center
        tu, tv = to_center

        dir_u = tu - fu
        dir_v = tv - fv
        norm = (dir_u ** 2 + dir_v ** 2) ** 0.5
        if norm == 0:
            return

        # Unit direction vector scaled by step size
        step_u = (dir_u / norm) * self.cfg.push_step_px
        step_v = (dir_v / norm) * self.cfg.push_step_px

        for _ in range(self.cfg.push_steps):
            self._nudge_xy(step_u, step_v)
