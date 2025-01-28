import logging
import cv2
from typing import List, Tuple, Optional
from config.settings import BOUNDARY_CONFIG

logger = logging.getLogger(__name__)

class BoundaryManager:
    """Handles ROI boundary selection through user input."""
    
    def __init__(self):
        self.config = BOUNDARY_CONFIG
        self.positions: List[Tuple[int, int]] = []
        self.boundary_set = False

    def set_boundary(self, frame: bytes) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Interactive boundary setting process."""
        cv2.namedWindow(self.config["window_name"])
        cv2.setMouseCallback(self.config["window_name"], self._mouse_callback)

        while not self.boundary_set:
            display_frame = self._annotate_frame(frame.copy())
            cv2.imshow(self.config["window_name"], display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("Boundary setup cancelled")
                cv2.destroyAllWindows()
                return None

        # Show final rectangle for confirmation
        final_display = frame.copy()
        cv2.rectangle(
            final_display,
            self.positions[0],
            self.positions[1],
            self.config["rectangle_color"],
            self.config["thickness"] * 2  # Thicker line for confirmation
        )
        cv2.imshow(self.config["window_name"], final_display)
        
        # Wait for user confirmation
        logger.info("Press any key to confirm or 'q' to cancel")
        key = cv2.waitKey(0)
        cv2.destroyAllWindows()
        if key & 0xFF == ord('q'):
            logger.info("Boundary setup cancelled")
            return None

        return self._get_verified_coordinates(frame.shape)    

    def _mouse_callback(self, event, x: int, y: int, *args):
        """Mouse click handler for boundary selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            logger.info(f"Boundary point registered at ({x}, {y})")
            self.positions.append((x, y))
            
            if len(self.positions) == 2:
                self.boundary_set = True

    def _annotate_frame(self, frame: bytes) -> bytes:
        """Annotate frame with current boundary points and temporary rectangle."""
        # Draw circles for clicked points
        for pos in self.positions:
            cv2.circle(
                frame, pos,
                self.config["circle_radius"],
                self.config["rectangle_color"],
                -1
            )
        
        # Draw temporary rectangle if both points are set
        if len(self.positions) == 2:
            cv2.rectangle(
                frame,
                self.positions[0],
                self.positions[1],
                self.config["rectangle_color"],
                self.config["thickness"]
            )
        
        return frame

    def _get_verified_coordinates(self, frame_shape: tuple) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Validate and format boundary coordinates."""
        y_max, x_max = frame_shape[:2]
        
        x1 = max(0, min(self.positions[0][0], self.positions[1][0]))
        y1 = max(0, min(self.positions[0][1], self.positions[1][1]))
        x2 = min(x_max, max(self.positions[0][0], self.positions[1][0]))
        y2 = min(y_max, max(self.positions[0][1], self.positions[1][1]))
        
        logger.info(f"Final boundary coordinates: ({x1}, {y1}) - ({x2}, {y2})")
        return ((x1, y1), (x2, y2))
