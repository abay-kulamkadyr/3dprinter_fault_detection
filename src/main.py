import os
import cv2
import time
import logging
import requests
import numpy as np
from detection.detectron2_detection import Detectron2Detection
from utils.camera_gstreamer_module import CameraGStreamerPipeline

# Global variables for mouse positions and boundary state
mouse_positions = []
boundary_set = False


def send_telegram_notification(bot_token, chat_id, message, image_path=None):
    """
    Sends a notification to a Telegram chat with an optional image.
    """
    try:
        api_url_message = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(api_url_message, json=payload, timeout=30)
        response.raise_for_status()

        if image_path:
            api_url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(image_path, "rb") as photo_file:
                files = {"photo": photo_file}
                data = {"chat_id": chat_id}
                response = requests.post(api_url_photo, data=data, files=files, timeout=30)
                response.raise_for_status()
        logging.info("Notification sent successfully")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram notification: {e}")


def notify_on_detection(image_path):
    """
    Callback function triggered on detection.
    """
    bot_token = os.getenv('BOT_TOKEN')
    message = "\u26A0\uFE0F Fault detected during 3D printing! \u26A0\uFE0F"

    chat_ids = [1969139002, 1430460059, 52338470, 987449095]
    for chat_id in chat_ids:
        send_telegram_notification(bot_token, chat_id, message, image_path)


def mouse_callback(event, x, y, flags, param):
    """
    Handles mouse clicks to set the boundary.
    """
    global mouse_positions, boundary_set
    if event == cv2.EVENT_LBUTTONDOWN:
        logging.info(f"Click registered at: ({x}, {y})")
        mouse_positions.append((x, y))
        if len(mouse_positions) == 2:
            boundary_set = True


def main():
    global mouse_positions, boundary_set

    # Configuration
    weights_file = "../data/models/model_final.pth"
    detections_dir = "../data/detections"
    detection_interval = 60  # Interval between detections in seconds

    # Initialize detection and video pipeline
    detectron2 = Detectron2Detection(weights_file, detections_dir, detection_callback=notify_on_detection)
    gstreamer = CameraGStreamerPipeline()

    try:
        gstreamer.open_pipeline()
        frame = gstreamer.read_frame()

        cv2.namedWindow("Set Boundary")
        cv2.setMouseCallback("Set Boundary", mouse_callback)

        # Boundary setup loop
        while not boundary_set:
            frame_copy = frame.copy()

            # Draw all registered circles
            for position in mouse_positions:
                cv2.circle(frame_copy, position, 20, (0, 255, 0), -1)

            cv2.imshow("Set Boundary", frame_copy)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Exiting boundary setup.")
                return

        top_left, bottom_right = mouse_positions[0], mouse_positions[1]
        logging.info(f"Boundary set: Top-left: {top_left}, Bottom-right: {bottom_right}")

        # Show the final boundary
        frame_copy = frame.copy()
        cv2.rectangle(frame_copy, top_left, bottom_right, (0, 255, 0), 2)
        cv2.imshow("Set Boundary", frame_copy)

        # Wait for user confirmation to proceed
        logging.info("Press any key to continue or 'q' to exit.")
        if cv2.waitKey(0) & 0xFF == ord('q'):
            logging.info("Exiting after boundary setup.")
            return

        cv2.destroyWindow("Set Boundary")

        prev_frame_time = 0
        last_detection_time = time.time()

        # Main detection loop
        while True:
            frame = gstreamer.read_frame()

            # Crop the frame based on boundary
            x1, y1 = top_left
            x2, y2 = bottom_right
            cropped_frame = frame[y1:y2, x1:x2]

            # Perform detection at intervals
            current_time = time.time()
            if current_time - last_detection_time >= detection_interval:
                logging.info("Running detection on cropped region...")
                img_counter = int(time.time())
                processed_frame = detectron2.process_frame(cropped_frame, img_counter)

                if processed_frame is not None:
                    frame[y1:y2, x1:x2] = processed_frame
                last_detection_time = current_time

            # Draw boundary and show FPS
            new_frame_time = time.time()
            fps = 1 / (new_frame_time - prev_frame_time)
            prev_frame_time = new_frame_time
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(frame, fps_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            # Display the live feed
            cv2.imshow("Detectron2 Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        gstreamer.close_pipeline()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

