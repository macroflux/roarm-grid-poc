import time
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
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Failed to load configuration file '{path}': {e}") from e
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML in configuration file '{path}': {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading configuration file '{path}': {e}") from e


def main():
    settings = load_settings()

    # Validate required configuration sections
    required_sections = ["camera", "vision", "arm", "controller"]
    missing_sections = [section for section in required_sections if section not in settings]
    if missing_sections:
        raise ValueError(f"Missing required configuration sections in settings.yaml: {', '.join(missing_sections)}")

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
    red_lower = np.array(vision_cfg["red_lower"], dtype=np.uint8)
    red_upper = np.array(vision_cfg["red_upper"], dtype=np.uint8)
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
        z_lift=ctrl_cfg.get("z_lift_mm", 0.0),
        pause_between_moves=ctrl_cfg.get("pause_between_moves", 0.5),
    )

    controller = PickPlaceController(arm, pick_place_config)
    logger = TelemetryLogger("telemetry.log")

    # Move to home pose once at startup, then wait a bit before arming automation
    system_ready = False
    homing_delay = float(settings.get("startup_homing_delay_s", 4.0))
    print("Moving to home position...")
    try:
        controller.go_home()
        # Give the arm time to physically reach home before enabling auto pick/place
        print(f"Waiting {homing_delay}s for arm to reach home position...")
        time.sleep(homing_delay)
        system_ready = True
        print("Home position reached. System ready.")
    except Exception as e:
        print("Warning: failed to move to home pose at startup. Automation will remain disabled:", e)

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
                red_lower,
                red_upper,
                min_zone_area,
            )

            if origin_box:
                draw_box(frame, origin_box, (255, 0, 0), "ORIGIN")
            if target_box:
                draw_box(frame, target_box, (0, 0, 255), "TARGET")

            object_center = None
            if origin_box:
                object_center = detect_object_in_origin(
                    frame,
                    origin_box,
                    min_object_area=min_object_area,
                    min_object_saturation=int(vision_cfg.get("min_object_saturation", 60)),
                )
                if object_center:
                    draw_object_center(frame, object_center)

            # Display
            cv2.imshow("Overhead View", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('h') or key == ord('H'):  # H key to go home
                print("Returning to home position...")
                try:
                    controller.go_home()
                    print("Home position reached.")
                except Exception as e:
                    print("Error moving to home:", e)

            # Trigger pick & place only after homing, if object detected in origin and not currently busy
            if system_ready and not busy and origin_box and target_box and object_center:
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
