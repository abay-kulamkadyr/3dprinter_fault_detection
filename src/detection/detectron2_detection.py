import cv2
import time
import os
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
from detectron2 import model_zoo
from utils.camera_gstreamer_module import CameraGStreamerPipeline     

class Detectron2Detection:
    def __init__(self, weights_file, detections_dir, device="cpu", threshold=0.5, detection_callback=None):
        self.cfg = self.setup_config(weights_file, threshold, device)
        self.predictor = DefaultPredictor(self.cfg)
        self.detections_dir = detections_dir
        os.makedirs(detections_dir, exist_ok=True)
        self.detection_callback = detection_callback

    def setup_config(self, weights_file, threshold, device):
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_X_101_32x8d_FPN_3x.yaml"))        
        cfg.MODEL.WEIGHTS = weights_file
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
        cfg.MODEL.DEVICE = device
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        MetadataCatalog.get("custom_metadata").set(thing_classes=["fail"])
        return cfg

    def process_frame(self, frame, img_counter):
        outputs = self.predictor(frame)
        instances = outputs["instances"].to("cpu")

        if len(instances) > 0:
            print("Detections found!")
            visualizer = Visualizer(
                frame[:, :, ::-1],
                MetadataCatalog.get("custom_metadata"),
                scale=1.0
            )
            output = visualizer.draw_instance_predictions(instances)
            detection_frame = output.get_image()[:, :, ::-1]

            detection_path = os.path.join(self.detections_dir, f"detection_{img_counter}.jpg")
            cv2.imwrite(detection_path, detection_frame)
            print(f"Detection image saved to: {detection_path}")

            #Callback function
            if self.detection_callback:
                self.detection_callback(detection_path)

            # Pause if a fault is detected
            #cv2.imshow("Fault Detected", detection_frame)
            #print("Fault detected. Press any key to continue or 'q' to exit.")
            #key = cv2.waitKey(0)  # Wait indefinitely for a key press

            #if key == ord('q'):
            #    print("Exiting detection loop.")
            #    return None
            return detection_frame
        else:
            print("No detections found.")
            return frame

def main():
    weights_file = "../data/models/model_final.pth"
    detections_dir = "../data/detections"

    detectron2_detection = Detectron2Detection(weights_file, detections_dir)

    gstreamer = CameraGStreamerPipeline()     

    try:
        gstreamer.open_pipeline()
        prev_frame_time = 0
        last_detection_time = time.time()

        while True:
            frame = gstreamer.read_frame()

            # Calculate FPS
            new_frame_time = time.time()
            fps = 1 / (new_frame_time - prev_frame_time)
            prev_frame_time = new_frame_time
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(frame, fps_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            # Perform detection at intervals
            current_time = time.time()
            if current_time - last_detection_time >= 20:
                print("Running detection...")
                img_counter = int(time.time())  # Use current time as image counter
                frame = detectron2_detection.process_frame(frame, img_counter)
                if frame is None:  # Exit if 'q' was pressed during fault detection
                    break
                last_detection_time = current_time

            # Display the live feed
            cv2.imshow("Detectron2 Detection", frame)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        gstreamer.close_pipeline()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

