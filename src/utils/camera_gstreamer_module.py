import cv2

class CameraGStreamerPipeline:
    def __init__(self, device="/dev/video0", width=1920, height=1080, framerate=30):
        self.pipeline = (
            f"v4l2src device={device} ! "
            f"image/jpeg, width={width}, height={height}, framerate={framerate}/1 ! "
            "jpegdec ! videoconvert ! appsink"
        )
        self.cap = None

    def open_pipeline(self):
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise RuntimeError("Error: Unable to open GStreamer pipeline.")

    def read_frame(self):
        if not self.cap:
            raise RuntimeError("Error: GStreamer pipeline is not open.")
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Error: Unable to read frame from GStreamer pipeline.")
        return frame

    def close_pipeline(self):
        if self.cap:
            self.cap.release()
            self.cap = None

if __name__ == "__main__":
    gstreamer = GStreamerPipeline()
    try:
        gstreamer.open_pipeline()
        while True:
            frame = gstreamer.read_frame()
            cv2.imshow("GStreamer Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        gstreamer.close_pipeline()
        cv2.destroyAllWindows()
