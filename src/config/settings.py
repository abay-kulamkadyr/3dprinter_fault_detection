from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Camera Configuration
CAMERA_CONFIG = {
    "device": "/dev/video0",
    "width": 1920,
    "height": 1080,
    "framerate": 30,
    "pipeline": (
        "v4l2src device={device} ! "
        "image/jpeg, width={width}, height={height}, framerate={framerate}/1 ! "
        "jpegdec ! videoconvert ! appsink"
    )
}

# Detection Configuration
DETECTION_CONFIG = {
    "model_weights": PROJECT_ROOT / "data/models/model_final.pth",
    "detections_dir": PROJECT_ROOT / "data/detections",
    "frames_dir": PROJECT_ROOT / "data/frames",
    "detection_interval": 60,  # seconds
    "confidence_threshold": 0.5,
    "device": "cpu"  # or "cuda"
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "api_endpoint": "http://127.0.0.1:5000/detection_event",
    "chat_ids": [1969139002, 1430460059, 52338470, 987449095],
    "retries": 3,
    "timeout": 10
}

# Boundary Configuration
BOUNDARY_CONFIG = {
    "window_name": "Set Boundary",
    "circle_radius": 20,
    "rectangle_color": (0, 255, 0),
    "thickness": 2
}
