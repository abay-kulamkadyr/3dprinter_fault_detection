import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class KlippyAPI:
    def __init__(self, base_url):
        """
        Initialize the Klippy API client with retry logic.

        :param base_url: Base URL of the Klippy server (e.g., http://hostname:port).
        """
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self):
        """
        Create a session with retry logic.

        :return: Configured requests session.
        """
        retries = Retry(
            total=5,                # Retry 5 times
            backoff_factor=1,       # 1 second delay between retries
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["GET", "POST"]       # Retry for these methods
        )
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_printer_info(self):
        """
        Get Klippy host information.

        :return: JSON response containing printer info.
        """
        url = f"{self.base_url}/printer/info"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_current_temperatures(self):
        """
        Get current and target temperatures for the extruder and heated bed.

        :return: JSON response containing temperatures.
        """
        url = f"{self.base_url}/printer/objects/query?heater_bed&extruder"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_motion_state(self):
        """
        Get the motion state of the printer, including position and velocity.

        :return: JSON response containing motion state.
        """
        url = f"{self.base_url}/printer/objects/query?toolhead"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_print_job_status(self):
        """
        Get the current print job status, including progress and estimated time remaining.

        :return: JSON response containing print job status.
        """
        url = f"{self.base_url}/printer/objects/query?print_stats"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def emergency_stop(self):
        """
        Trigger an emergency stop.

        :return: Response text (should be 'ok').
        """
        url = f"{self.base_url}/printer/emergency_stop"
        response = self.session.post(url)
        response.raise_for_status()
        return response.text

    def pause(self):
        """
        Pause the print.

        :return: Response text.
        """
        url = f"{self.base_url}/printer/print/pause"
        response = self.session.post(url)
        response.raise_for_status()
        return response.text

    def resume(self):
        """
        Resume the print.

        :return: Response text.
        """
        url = f"{self.base_url}/printer/print/resume"
        response = self.session.post(url)
        response.raise_for_status()
        return response.text

    def restart_host(self):
        """
        Restart the Klippy host.

        :return: Response text (should be 'ok').
        """
        url = f"{self.base_url}/printer/restart"
        response = self.session.post(url)
        response.raise_for_status()
        return response.text

    def firmware_restart(self):
        """
        Restart the Klippy firmware.

        :return: Response text (should be 'ok').
        """
        url = f"{self.base_url}/printer/firmware_restart"
        response = self.session.post(url)
        response.raise_for_status()
        return response.text

    def list_printer_objects(self):
        """
        List available printer objects.

        :return: JSON response containing available printer objects.
        """
        url = f"{self.base_url}/printer/objects/list"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def query_printer_object_status(self, query_params):
        """
        Query the status of specific printer objects.

        :param query_params: A dictionary of objects and their specific parameters to query.
                             Example: {"gcode_move": None, "toolhead": None, "extruder": "target,temperature"}
        :return: JSON response containing object statuses.
        """
        query_string = "&".join(
            f"{key}={value}" if value else f"{key}" for key, value in query_params.items()
        )
        url = f"{self.base_url}/printer/objects/query?{query_string}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    base_url = "http://192.168.31.100:7125"
    klippy = KlippyAPI(base_url)

    try:
        # Get printer info
        printer_info = klippy.get_printer_info()
        print("Printer Info:", printer_info)

        # Get current temperatures
        temperatures = klippy.get_current_temperatures()
        print("Temperatures:", temperatures)

        # Get motion state
        motion_state = klippy.get_motion_state()
        print("Motion State:", motion_state)

        # Get print job status
        job_status = klippy.get_print_job_status()
        print("Print Job Status:", job_status)

        # List printer objects
        printer_objects = klippy.list_printer_objects()
        print("Printer Objects:", printer_objects)

        # Query printer object status
        status = klippy.query_printer_object_status({"gcode_move": None, "toolhead": None, "extruder": "target,temperature"})
        print("Printer Status:", status)

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
