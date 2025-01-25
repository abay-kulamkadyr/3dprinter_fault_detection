import threading
import signal
import sys
import logging
from bot.bot import start_bot_polling
from server.flask_server import app
from bot.stream import StreamLauncher

stream_launcher = StreamLauncher()

def signal_handler(sig, frame):
    logging.info("Received termination signal. Stopping stream and exiting...")
    stream_launcher.stop_stream()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()

    logging.info("Starting Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5000)
