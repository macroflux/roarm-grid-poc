import cv2


class VisionSensor:
    def __init__(self, camera_index: int = 0, width: int | None = None, height: int | None = None):
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
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
