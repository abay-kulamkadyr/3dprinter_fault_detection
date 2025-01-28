import logging
import requests
from typing import Optional
from config.settings import NOTIFICATION_CONFIG

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handles detection event notifications."""

    def __init__(self):
        self.config = NOTIFICATION_CONFIG

    def send_detection_alert(self, image_path: str) -> bool:
        """Send detection notification to backend service."""
        for attempt in range(self.config["retries"]):
            try:
                response = requests.post(
                    self.config["api_endpoint"],
                    json={"image_path": image_path},
                    timeout=self.config["timeout"]
                )
                response.raise_for_status()
                logger.info("Detection notification sent successfully")
                return True

            except Exception as e:
                logger.warning(f"Notification attempt {attempt+1} failed: {str(e)}")

        logger.error("All notification attempts failed")
        return False
