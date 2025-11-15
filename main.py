import cv2
import numpy as np
import yaml

from vision.camera import VisionSensor
from vision.grid_detector import detect_zones, draw_box
from vision.object_detector import detect_object_in_origin, draw_object_center
from arm.roarm_client import RoArmClient
from controller.pick_place import PickPlaceController, PickPlaceConfig
from telemetry.logger import TelemetryLogger


def load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    settings = load_settings()

    cam_cfg = settings["camera"]
    vision_cfg = settings["vision"]
    arm_cfg = settings["arm"]
    ctrl_cfg = settings["controller"]

    # --- Vision setup ---
    vision = VisionSensor(
        camera_index=cam_cfg.get("index", 0),
        width=cam_cfg.get("width"),
        height=cam_cfg.get("height"),
    )

    blue_lower = np.array(vision_cfg["blue_lower"], dtype=np.uint8)
    blue_upper = np.array(vision_cfg["blue_upper"], dtype=np.uint8)
    black_lower = np.array(vision_cfg["black_lower"], dtype=np.uint8)
    black_upper = np.array(vision_cfg["black_upper"], dtype=np.uint8)
    min_zone_area = int(vision_cfg.get("min_zone_area", 2000))
    min_object_area = int(vision_cfg.get("min_object_area", 800))

    # --- Arm + controller setup ---
    arm = RoArmClient(ip=arm_cfg["ip"])

    pick_place_config = PickPlaceConfig(
        pose_home=ctrl_cfg["pose_home"],
        pose_above_origin=ctrl_cfg["pose_above_origin"],
        pose_pick_origin=ctrl_cfg["pose_pick_origin"],
        pose_above_target=ctrl_cfg["pose_above_target"],
        pose_place_target=ctrl_cfg["pose_place_target"],
        spd=ctrl_cfg["speed_deg_per_s"],
        acc=ctrl_cfg["acc_deg_per_s2"],
        grip_closed_rad=ctrl_cfg["grip_closed_rad"],
        grip_open_rad=ctrl_cfg["grip_open_rad"],
    )

    controller = PickPlaceController(arm, pick_place_config)
    logger = TelemetryLogger("telemetry.log")

    busy = False

    try:
        while True:
            frame = vision.get_frame()
            if frame is None:
                print("No frame from camera, exiting.")
                break

            origin_box, target_box = detect_zones(
                frame,
                blue_lower,
                blue_upper,
                black_lower,
                black_upper,
                min_zone_area,
            )

            if origin_box:
                draw_box(frame, origin_box, (255, 0, 0), "ORIGIN")
            if target_box:
                draw_box(frame, target_box, (0, 0, 0), "TARGET")

            object_center = None
            if origin_box:
                object_center = detect_object_in_origin(
                    frame,
                    origin_box,
                    min_object_area=min_object_area,
                )
                if object_center:
                    draw_object_center(frame, object_center)

            # Display
            cv2.imshow("Overhead View", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

            # Trigger pick & place if object detected in origin and not currently busy
            if not busy and origin_box and target_box and object_center:
                busy = True
                logger.log(
                    "pick_place_start",
                    {
                        "origin_box": origin_box.__dict__,
                        "target_box": target_box.__dict__,
                        "object_center": object_center,
                    },
                )
                try:
                    controller.execute_pick_place()
                    logger.log("pick_place_success", {})
                except Exception as e:
                    logger.log("pick_place_error", {"error": str(e)})
                    print("Error during pick & place:", e)
                finally:
                    busy = False

    finally:
        vision.release()
        cv2.destroyAllWindows()
        logger.close()


if __name__ == "__main__":
    main()
