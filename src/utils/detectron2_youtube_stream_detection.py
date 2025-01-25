import subprocess
import cv2
import time
import os
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

def get_youtube_stream_url(youtube_url, format_code):
    """
    Extracts the direct video stream URL from a YouTube link using yt-dlp.
    """
    try:
        command = ["yt-dlp", "--format", format_code, "--get-url", youtube_url]
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
        stream_url = result.stdout.strip()
        return stream_url
    except subprocess.CalledProcessError as e:
        print(f"Error fetching stream URL: {e}")
        return None

def setup_detection(cfg_file, weights_file, threshold, device):
    """
    Sets up the Detectron2 configuration and predictor.
    """
    cfg = get_cfg()
    cfg.merge_from_file(cfg_file)
    cfg.MODEL.WEIGHTS = weights_file
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
    cfg.MODEL.DEVICE = device
    predictor = DefaultPredictor(cfg)
    return cfg, predictor

def perform_detection(frame, predictor, cfg, detections_dir, img_counter):
    """
    Performs object detection on the given frame and saves detection images.
    """
    outputs = predictor(frame)
    instances = outputs["instances"].to("cpu")

    if len(instances) > 0:
        print("Detections found!")
        v = Visualizer(frame[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1.0)
        out = v.draw_instance_predictions(instances)
        detection_frame = out.get_image()[:, :, ::-1]

        detection_path = os.path.join(detections_dir, f"detection_{img_counter}.jpg")
        cv2.imwrite(detection_path, detection_frame)
        print(f"Detection image saved to: {detection_path}")
        return True
    else:
        print("No detections found.")
        return False

def main():
    youtube_url = "https://www.youtube.com/watch?v=Xb7RW25WR-Y"
    format_code = "230"  # Medium resolution: 640x360, 30 FPS

    # Fetch the direct stream URL
    print("Fetching stream URL...")
    stream_url = get_youtube_stream_url(youtube_url, format_code)
    if not stream_url:
        print("Error: Unable to fetch the stream URL.")
        return

    print(f"Stream URL: {stream_url}")

    # Load the Detectron2 configuration
    cfg_file = "mask_rcnn_X_101_32x8d_FPN_3x.yaml"
    weights_file = "model_final.pth"
    threshold = 0.5
    device = "cpu"

    cfg, predictor = setup_detection(cfg_file, weights_file, threshold, device)

    # Define the GStreamer pipeline
    pipeline = f"""
    uridecodebin uri={stream_url} 
    ! queue 
    ! videoscale ! video/x-raw,width=640,height=480
    ! videoconvert 
    ! appsink
    """

    # Open the video stream with OpenCV
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: Unable to open video stream with GStreamer pipeline.")
        return

    # Set up directories
    detections_dir = "detections"
    os.makedirs(detections_dir, exist_ok=True)

    prev_frame_time = 0
    img_counter = 0
    last_detection_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to capture frame.")
                break

            # Calculate FPS
            new_frame_time = time.time()
            fps = 1 / (new_frame_time - prev_frame_time)
            prev_frame_time = new_frame_time
            fps_text = f"FPS: {int(fps)}"
            #print(fps_text)

            # Perform detection every 30 seconds
            current_time = time.time()
            if current_time - last_detection_time >= 30:
                print("Running detection...")
                detection_happened = perform_detection(frame, predictor, cfg, detections_dir, img_counter)

                if detection_happened:
                    img_counter += 1

                last_detection_time = current_time

            # Display the live feed with FPS
            cv2.putText(frame, fps_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow("Detectron2 Detection", frame)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

