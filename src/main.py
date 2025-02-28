import logging
import time
import cv2
import numpy as np
import os 
from typing import Optional, Tuple
from config import settings
from utils.camera import Camera, FrameProcessor
from detectors.detectron2_detector import Detectron2Detector
from utils.notifications import NotificationHandler
from interfaces.boundary_manager import BoundaryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class FaultDetectionSystem:
    """Main application controller for fault detection system."""

    def __init__(self):
        self.camera = Camera()
        self.detector = Detectron2Detector()
        self.notifier = NotificationHandler()
        self.boundary_manager = BoundaryManager()
        self.detection_interval = settings.DETECTION_CONFIG["detection_interval"]
        self.boundary: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        self.last_frame_time = time.time()
        self.last_detection_time = 0.0
        self.last_frame = None

    def run(self):
        """Main execution flow."""
        initial_frame = self._get_initial_frame()
        if initial_frame is None:
            return
        if os.environ.get("HOST") == 1:
            self.boundary = self.boundary_manager.set_boundary(initial_frame)
        else:
            self.boundary = ((0, 0), (960, 540))
        if not self.boundary:
            return

        self._main_loop()

    def _get_initial_frame(self) -> Optional[bytes]:
        """Capture initial frame for boundary selection."""
        try:
            with self.camera.session():
                frame = self.camera.read()
                if frame is not None:
                    # Convert to BGR if needed (some cameras return RGB)
                    if frame.shape[2] == 3:  # Assuming OpenCV default BGR
                        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    return frame
                logger.error("Failed to capture initial frame")
                return None
        except Exception as e:
            logger.error(f"Camera initialization failed: {str(e)}")
            return None

    def _main_loop(self):
        """Main processing loop with camera resource management."""
        while True:
            current_time = time.time()

            # Capture and process frame only at detection intervals
            if current_time - self.last_detection_time >= self.detection_interval:
                self._perform_detection_capture()
                self.last_detection_time = current_time

            # Display the latest frame or standby message
            self._display_status()

            # Exit condition
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def _display_status(self):
        """Display system status with camera resource management."""
        display_frame = np.zeros((500, 500, 3), dtype=np.uint8)  # Black background
        time_remaining = self.detection_interval - (time.time() - self.last_detection_time)

        if self.last_frame is not None:
            # Show last detection result
            resized = cv2.resize(self.last_frame, (500, 500))
            display_frame = resized

            # Add time remaining overlay
            cv2.putText(
                display_frame,
                f"Next capture in: {max(0, int(time_remaining))}s",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2
            )
        else:
            # Show standby message
            cv2.putText(
                display_frame,
                f"System Ready - Waiting for first detection,\nNext capture in: {max(0, int(time_remaining))}s",
                (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2
            )
        if os.environ.get("HOST") == 1:
            cv2.imshow("Fault Detection System", display_frame)

    def _perform_detection_capture(self):
        """Handle camera acquisition and detection processing."""
        try:
            with self.camera.session():
                frame = self.camera.read()
                if frame is not None:
                    self._process_detection_frame(frame)
        except Exception as e:
            logger.error(f"Detection capture failed: {str(e)}")

    def _process_detection_frame(self, frame: bytes):
        """Process and store detection results."""
        cropped = FrameProcessor.crop_frame(frame, *self.boundary)
        processed = self.detector.process_frame(cropped, time.time())

        if processed is not None:
            x1, y1 = self.boundary[0]
            x2, y2 = self.boundary[1]
            frame[y1:y2, x1:x2] = processed
            self.last_frame = frame
            timestamp = int(time.time())
            self.detector._save_detection(frame, timestamp)
            self.notifier.send_detection_alert(
                str(self.detector.config["detections_dir"] / f"detection_{timestamp}.jpg")
            )
        self.detector._save_latest_frame(frame, time.time)

    def _display_frame(self, frame: bytes):
        """Handle frame display with FPS calculation and boundary drawing."""
        try:
            # Calculate FPS
            current_time = time.time()
            fps = 1 / (current_time - self.last_frame_time)
            self.last_frame_time = current_time

            # Add FPS overlay
            FrameProcessor.add_fps(frame, fps)

            # Display the frame
 
            if os.environ.get("HOST") == 1:
                cv2.imshow("Fault Detection System", frame)

        except Exception as e:
            logger.error(f"Frame display error: {str(e)}")


if __name__ == "__main__":
    try:
        system = FaultDetectionSystem()
        system.run()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        cv2.destroyAllWindows()
        logger.info("Application shutdown complete")
