import subprocess
import threading
import time
import logging
import os
import signal

class StreamLauncher:
    def __init__(self, gst_command, pid_file='/tmp/stream_launcher.pid'):
        """
        Initialize the StreamLauncher with the GStreamer command.

        :param gst_command: List of command arguments for GStreamer.
        :param pid_file: Path to the pid file.
        """
        self.gst_command = gst_command
        self.pid_file = pid_file
        self.process = None
        self.logger = self.setup_logger()
        self.stop_event = threading.Event()

    def setup_logger(self):
        """
        Set up the logger for the module.

        :return: Configured logger instance.
        """
        logger = logging.getLogger('StreamLauncher')
        logger.setLevel(logging.DEBUG)
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # Create formatter and add to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        # Add handlers to logger
        if not logger.handlers:
            logger.addHandler(ch)
        return logger

    def is_stream_running(self):
        """
        Check if the stream is already running by checking the pid file and if the process exists.

        :return: True if running, False otherwise.
        """
        if os.path.isfile(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read())
                if self.check_process(pid):
                    self.logger.info(f"Detected existing stream with PID {pid}.")
                    return True
                else:
                    self.logger.info(f"No matching process with PID {pid}. Removing pid file.")
                    os.remove(self.pid_file)
            except Exception as e:
                self.logger.error(f"Error reading pid file: {e}")
                os.remove(self.pid_file)
        return False

    def check_process(self, pid):
        """
        Check if a process with the given PID exists and matches the gst_command.

        :param pid: Process ID to check.
        :return: True if process exists and matches, False otherwise.
        """
        try:
            with open(f"/proc/{pid}/cmdline", 'r') as f:
                cmdline = f.read().replace('\0', ' ').strip()
            existing_cmd = cmdline.split(' ')
            # Check if all parts of gst_command are present in the existing command
            return all(part in existing_cmd for part in self.gst_command)
        except Exception as e:
            self.logger.debug(f"Process with PID {pid} not found or does not match: {e}")
            return False

    def start_stream(self):
        """
        Start the GStreamer pipeline as a subprocess.
        """
        if self.is_stream_running():
            self.logger.warning("GStreamer pipeline is already running.")
            return

        try:
            self.logger.info("Starting GStreamer pipeline...")
            self.process = subprocess.Popen(
                self.gst_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Allows killing the whole process group
            )
            # Write the pid to the pid file
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
            self.logger.info(f"GStreamer pipeline started with PID {self.process.pid}.")

            # Start threads to log stdout and stderr
            threading.Thread(target=self.log_stream, args=(self.process.stdout, logging.INFO), daemon=True).start()
            threading.Thread(target=self.log_stream, args=(self.process.stderr, logging.ERROR), daemon=True).start()

            # Start a thread to monitor the process
            threading.Thread(target=self.monitor_process, daemon=True).start()

        except Exception as e:
            self.logger.error(f"Failed to start GStreamer pipeline: {e}")

    def log_stream(self, stream, log_level):
        """
        Log the output streams from the subprocess.

        :param stream: The stdout or stderr stream.
        :param log_level: The logging level.
        """
        for line in iter(stream.readline, b''):
            if line:
                self.logger.log(log_level, line.decode().rstrip())
        stream.close()

    def monitor_process(self):
        """
        Monitor the subprocess for unexpected termination.
        """
        while not self.stop_event.is_set():
            if self.process:
                retcode = self.process.poll()
                if retcode is not None:
                    self.logger.warning(f"GStreamer pipeline terminated with return code {retcode}. Restarting...")
                    os.remove(self.pid_file)  # Remove pid file as process is no longer running
                    self.start_stream()  # Restart the pipeline
                    break  # Exit current monitor thread
            time.sleep(5)  # Check every 5 seconds

    def stop_stream(self):
        """
        Stop the GStreamer pipeline subprocess.
        """
        self.logger.info("Stopping GStreamer pipeline...")
        self.stop_event.set()
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=10)
                self.logger.info("GStreamer pipeline stopped successfully.")
            except Exception as e:
                self.logger.error(f"Error stopping GStreamer pipeline: {e}")
        else:
            self.logger.warning("GStreamer pipeline is not running.")

        # Remove pid file
        if os.path.isfile(self.pid_file):
            try:
                os.remove(self.pid_file)
                self.logger.debug(f"Removed pid file {self.pid_file}.")
            except Exception as e:
                self.logger.error(f"Failed to remove pid file: {e}")

