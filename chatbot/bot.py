import os
import telebot
from klippy_api.KlippyAPI import KlippyAPI

CHAT_IDS = [
    1969139002,
    1430460059,
    52338470,
    1430460059,
]

def compose_message(data: dict) -> str:
    """
    Compose a formatted message from a dictionary.

    :param data: Dictionary containing key-value pairs.
    :return: Formatted string.
    """
    return "\n".join(f"{key}: {value}" for key, value in data.items())

def main() -> None:
    """
    Main function to initialize and run the Telegram bot.
    """
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in environment variables.")

    bot = telebot.TeleBot(BOT_TOKEN)
    base_url = "http://192.168.31.100:7125"
    klippy = KlippyAPI(base_url)

    def send_action_list(chat_id):
        """
        Sends a list of available actions to the user.
        """
        actions = (
            "/info - Get printer info\n"
            "/list - List printer objects\n"
            "/restart_host - Restart the host\n"
            "/restart_firmware - Restart firmware\n"
            "/extruder - Get extruder status\n"
            "/emergency_stop - Emergency stop\n"
            "/pause - Pause the print\n"
            "/resume - Resume the print\n"
            "/temperatures - Get current temperatures\n"
            "/motion_state - Get motion state\n"
            "/job_status - Get print job status\n"
        )
        bot.send_message(chat_id, f"Available actions:\n{actions}")

    @bot.message_handler(commands=['start', 'hello'])
    def send_welcome(message):
        """
        Handle the /start and /hello commands.
        """
        if message.chat.id in CHAT_IDS:
            bot.reply_to(message, "Howdy, how are you doing?")
        else:
            bot.reply_to(message, "You are not authorized to use this bot.")

    @bot.message_handler(commands=['info'])
    def get_info(message):
        """
        Handle the /info command to fetch printer info.
        """
        if message.chat.id in CHAT_IDS:
            printer_info = klippy.get_printer_info()
            bot.reply_to(message, compose_message(printer_info))

    @bot.message_handler(commands=['list'])
    def list_printer_objects(message):
        """
        Handle the /list command to list printer objects.
        """
        if message.chat.id in CHAT_IDS:
            printer_objects = klippy.list_printer_objects()
            bot.reply_to(message, "Printer Objects:\n" + compose_message(printer_objects))

    @bot.message_handler(commands=['restart_host'])
    def restart_host(message):
        """
        Handle the /restart_host command.
        """
        if message.chat.id in CHAT_IDS:
            response = klippy.restart_host()
            bot.reply_to(message, f"Printer's response: {response}")

    @bot.message_handler(commands=['restart_firmware'])
    def restart_firmware(message):
        """
        Handle the /restart_firmware command.
        """
        if message.chat.id in CHAT_IDS:
            response = klippy.firmware_restart()
            bot.reply_to(message, f"Printer's response: {response}")

    @bot.message_handler(commands=['extruder'])
    def get_extruder_status(message):
        """
        Handle the /extruder command to fetch extruder status.
        """
        if message.chat.id in CHAT_IDS:
            status = klippy.query_printer_object_status({
                "gcode_move": None,
                "toolhead": None,
                "extruder": "target,temperature",
            })
            bot.reply_to(message, "Printer status:\n" + compose_message(status))

    @bot.message_handler(commands=['emergency_stop'])
    def emergency_stop(message):
        """
        Handle the /emergency_stop command.
        """
        if message.chat.id in CHAT_IDS:
            response = klippy.emergency_stop()
            bot.reply_to(message, f"Printer's response: {response}")

    @bot.message_handler(commands=['pause'])
    def pause_print(message):
        """
        Handle the /pause command to pause the print.
        """
        if message.chat.id in CHAT_IDS:
            response = klippy.pause()
            bot.reply_to(message, f"Printer's response: {response}")

    @bot.message_handler(commands=['resume'])
    def resume_print(message):
        """
        Handle the /resume command to resume the print.
        """
        if message.chat.id in CHAT_IDS:
            response = klippy.resume()
            bot.reply_to(message, f"Printer's response: {response}")

    @bot.message_handler(commands=['temperatures'])
    def get_temperatures(message):
        """
        Handle the /temperatures command to fetch current temperatures.
        """
        if message.chat.id in CHAT_IDS:
            temperatures = klippy.get_current_temperatures()
            bot.reply_to(message, "Current Temperatures:\n" + compose_message(temperatures))

    @bot.message_handler(commands=['motion_state'])
    def get_motion_state(message):
        """
        Handle the /motion_state command to fetch the motion state.
        """
        if message.chat.id in CHAT_IDS:
            motion_state = klippy.get_motion_state()
            bot.reply_to(message, "Motion State:\n" + compose_message(motion_state))

    @bot.message_handler(commands=['job_status'])
    def get_job_status(message):
        """
        Handle the /job_status command to fetch the print job status.
        """
        if message.chat.id in CHAT_IDS:
            job_status = klippy.get_print_job_status()
            bot.reply_to(message, "Print Job Status:\n" + compose_message(job_status))

    def handle_detection_event(chat_id):
        """
        Handle an external detection event and provide action options.
        """
        if chat_id in CHAT_IDS:
            bot.send_message(chat_id, "⚠️ Detection Event Received! ⚠️")
            send_action_list(chat_id)

    @bot.message_handler(func=lambda msg: True)
    def echo_all(message):
        """
        Echo any unrecognized messages back to the sender.
        """
        bot.reply_to(message, "Unknown command. Please use a valid command.")

    # Example external detection event trigger (replace or integrate as needed)
    # This should be called from an external module when detection occurs.
    handle_detection_event(1969139002)

    # Start the bot's polling loop
    bot.infinity_polling()

if __name__ == '__main__':
    main()

