import logging
import cv2
from typing import Optional
from contextlib import contextmanager
from config.settings import CAMERA_CONFIG

logger = logging.getLogger(__name__)


class Camera:
    """GStreamer camera pipeline manager with context support."""

    def __init__(self):
        self.config = CAMERA_CONFIG
        self.cap: Optional[cv2.VideoCapture] = None

    def _build_pipeline(self) -> str:
        """Build GStreamer pipeline string from config."""
        return self.config["pipeline"].format(**self.config)

    def open(self):
        """Initialize the camera pipeline."""
        if self.cap and self.cap.isOpened():
            logger.warning("Camera already opened")
            return

        pipeline = self._build_pipeline()
        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera pipeline: {pipeline}")

    def read(self) -> Optional[bytes]:
        """Capture a single frame."""
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError("Camera not initialized")

        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to capture frame")
            return None

        return frame

    def close(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info("Camera resources released")

    @contextmanager
    def session(self):
        """Context manager for camera usage."""
        try:
            self.open()
            yield self
        finally:
            self.close()


class FrameProcessor:
    """Utility class for frame processing operations."""

    @staticmethod
    def add_fps(frame: bytes, fps: float) -> bytes:
        """Annotate frame with FPS counter."""
        cv2.putText(
            frame, f"FPS: {int(fps)}", (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA
        )
        return frame

    @staticmethod
    def crop_frame(frame: bytes, top_left: tuple, bottom_right: tuple) -> bytes:
        """Crop frame to specified coordinates."""
        y1, y2 = sorted([top_left[1], bottom_right[1]])
        x1, x2 = sorted([top_left[0], bottom_right[0]])
        return frame[y1:y2, x1:x2]
