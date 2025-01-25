import subprocess
import logging
from config import GST_PIPELINE

class StreamLauncher:
    def __init__(self):
        self.process = None

    def start_stream(self):
        """Start the GStreamer pipeline."""
        try:
            self.process = subprocess.Popen(GST_PIPELINE)
            logging.info("GStreamer pipeline started.")
        except Exception as e:
            logging.error(f"Failed to start GStreamer pipeline: {e}")

    def stop_stream(self):
        """Stop the GStreamer pipeline."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logging.info("GStreamer pipeline stopped.")
        else:
            logging.warning("No active GStreamer process to stop.")

    def is_stream_running(self) -> bool:
        """Check if the stream is running."""
        return self.process is not None and self.process.poll() is None
