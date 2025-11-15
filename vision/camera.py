import cv2
import sys


class VisionSensor:
    def __init__(self, camera_index: int = 0, width: int | None = None, height: int | None = None, backend: int | None = None):
        # Select backend automatically if not provided
        if backend is None:
            if sys.platform.startswith("win"):
                backend = cv2.CAP_DSHOW
            elif sys.platform.startswith("linux"):
                backend = cv2.CAP_V4L2
            else:
                backend = None  # Use default backend
        
        if backend is not None:
            self.cap = cv2.VideoCapture(camera_index, backend)
        else:
            self.cap = cv2.VideoCapture(camera_index)
        
        if width is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {camera_index}")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
