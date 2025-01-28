import os
import logging
import cv2
from typing import Optional
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
from detectron2 import model_zoo
from pathlib import Path
from config.settings import DETECTION_CONFIG

logger = logging.getLogger(__name__)

class Detectron2Detector:
    """Object detection handler using Detectron2 framework."""
    
    def __init__(self):
        self.config = DETECTION_CONFIG
        self._validate_paths()
        self.predictor = self._initialize_predictor()
        self.metadata = self._configure_metadata()

    def _validate_paths(self):
        """Ensure required paths exist."""
        self.config["detections_dir"].mkdir(parents=True, exist_ok=True)
        self.config["frames_dir"].mkdir(parents=True, exist_ok=True)
        
        if not self.config["model_weights"].exists():
            raise FileNotFoundError(f"Model weights not found at {self.config['model_weights']}")

    def _configure_metadata(self):
        """Configure dataset metadata."""
        metadata = MetadataCatalog.get("custom_metadata")
        metadata.set(thing_classes=["fail"])
        return metadata

    def _initialize_predictor(self) -> DefaultPredictor:
        """Initialize Detectron2 predictor with config."""
        cfg = get_cfg()
        cfg.merge_from_file(
            model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_X_101_32x8d_FPN_3x.yaml")
        )
        cfg.MODEL.WEIGHTS = str(self.config["model_weights"])
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = self.config["confidence_threshold"]
        cfg.MODEL.DEVICE = self.config["device"]
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        return DefaultPredictor(cfg)

    def process_frame(self, frame: bytes, timestamp: float) -> Optional[bytes]:
        """Process a frame through detection model."""
        try:
            outputs = self.predictor(frame)
            instances = outputs["instances"].to("cpu")

            if not len(instances):
                logger.debug("No detections found")
                return None

            logger.info(f"Detected {len(instances)} faults")
            return self._visualize_detections(frame, instances, timestamp)
            
        except Exception as e:
            logger.error(f"Detection failed: {str(e)}")
            return None

    def _visualize_detections(self, frame: bytes, instances, timestamp: float) -> bytes:
        """Visualize detections and save results."""
        visualizer = Visualizer(frame[:, :, ::-1], self.metadata, scale=1.0)
        output = visualizer.draw_instance_predictions(instances)
        processed_frame = output.get_image()[:, :, ::-1]
        return processed_frame

    def _save_detection(self, frame: bytes, timestamp: float) -> Path:
        """Save detection result to file."""
        path = self.config["detections_dir"] / f"detection_{timestamp}.jpg"
        cv2.imwrite(str(path), frame)
        logger.info(f"Detection saved to {path}")
        return path

    def _save_latest_frame(self, frame: bytes, timestamp: float):
        """Save reference frame for debugging."""
        path = self.config["frames_dir"] / "latest_frame.jpg"
        cv2.imwrite(str(path), frame)
        logger.debug(f"Latest frame updated at {path}")
