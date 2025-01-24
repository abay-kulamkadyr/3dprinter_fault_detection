
import os
import threading
import logging
import telebot
from flask import Flask, request, jsonify
from klippy_api.KlippyAPI import KlippyAPI

################################################################################
#                       CONFIGURATION & LOGGING
################################################################################

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables.")

# Authorized users
CHAT_IDS = [
    1969139002,
    1430460059,
    52338470,
    987449095,
    471938014
]

# Klipper base URL
base_url = "http://192.168.31.100:7125"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Initialize Klippy API
klippy = KlippyAPI(base_url)

# Create Flask app
app = Flask(__name__)

################################################################################
#                          HELPER PARSING FUNCTIONS
################################################################################

def parse_printer_info(info: dict) -> str:
    """
    Extracts and formats the most important fields from the /info command result.
    Example raw structure:
        {
          "result": {
            "state": "ready",
            "state_message": "Printer is ready",
            "hostname": "orangepizero3",
            "software_version": "...",
            "config_file": "...",
            ...
          }
        }
    """
    result = info.get("result", {})
    state = result.get("state", "unknown")
    state_msg = result.get("state_message", "N/A")
    hostname = result.get("hostname", "N/A")
    software_version = result.get("software_version", "N/A")
    config_file = result.get("config_file", "N/A")

    # Construct a user-friendly text with emojis
    text = (
        f"🖨 <b>Printer Info</b>:\n"
        f"• <b>State</b>: {state}  ✅\n"
        f"• <b>Status</b>: {state_msg}\n"
        f"• <b>Hostname</b>: {hostname}\n"
        f"• <b>Software Version</b>: {software_version}\n"
        f"• <b>Config File</b>: {config_file}\n"
    )
    return text

def parse_printer_objects(objects_data: dict) -> str:
    """
    Parse the response from /list which looks like:
      { "result": { "objects": [ ... ] } }
    We'll list them in a bullet format with emojis.
    """
    result = objects_data.get("result", {})
    obj_list = result.get("objects", [])
    if not obj_list:
        return "🤔 No objects found."

    # Join them as bullet points
    bullet_items = "\n".join([f"• {obj}" for obj in obj_list])
    return f"🗃 <b>Printer Objects</b>:\n{bullet_items}"

def parse_extruder_status(data: dict) -> str:
    """
    Parse the /extruder result:
      {
        "eventtime": ...,
        "status": {
          "gcode_move": {...},
          "toolhead": {...},
          "extruder": {
            "target": 0.0,
            "temperature": 30.2
          }
        }
      }
    We'll focus on extruder target & temperature.
    """
    status = data.get("status", {})
    extruder = status.get("extruder", {})
    temperature = extruder.get("temperature", 0.0)
    target = extruder.get("target", 0.0)

    text = (
        f"🔧 <b>Extruder Status</b>:\n"
        f"• Temperature: {temperature:.1f}°C\n"
        f"• Target: {target:.1f}°C\n"
    )
    return text

def parse_motion_state(data: dict) -> str:
    """
    Parse the /motion_state result:
      {
        "result": {
          "eventtime": ...,
          "status": {
            "toolhead": {
              "homed_axes": "...",
              "position": [...],
              ...
            }
          }
        }
      }
    We'll show if axes are homed, plus current position.
    """
    result = data.get("result", {})
    status = result.get("status", {})
    toolhead = status.get("toolhead", {})
    homed_axes = toolhead.get("homed_axes", "N/A")
    position = toolhead.get("position", [0, 0, 0, 0])

    text = (
        f"🕹 <b>Motion State</b>:\n"
        f"• Homed Axes: '{homed_axes}'\n"
        f"• Current Position: X={position[0]:.2f}, Y={position[1]:.2f}, Z={position[2]:.2f}\n"
    )
    return text

def parse_job_status(job_status: dict) -> str:
    """
    Parse the /job_status result, which might look like:
      {
        "result": {
          "job": {"file": {"name": None}, ...},
          "progress": {"completion": None, ...},
          "state": "Operational"
        }
      }
    We'll show state, file name, etc.
    """
    result = job_status.get("result", {})
    job_info = result.get("job", {})
    progress_info = result.get("progress", {})
    state = result.get("state", "Unknown")

    # Extract relevant fields
    file_name = job_info.get("file", {}).get("name", "N/A")
    completion = progress_info.get("completion", None)

    # Format completion nicely
    if completion is not None:
        completion_str = f"{completion:.1f}%" if completion <= 100 else f"{completion}%"
    else:
        completion_str = "N/A"

    text = (
        f"📄 <b>Job Status</b>:\n"
        f"• State: {state}\n"
        f"• File: {file_name}\n"
        f"• Completion: {completion_str}\n"
    )
    return text

################################################################################
#                         BOT FLASK ROUTE (DETECTION)
################################################################################

@app.route("/detection_event", methods=["POST"])
def detection_event():
    """
    Receives a POST request when a fault/detection occurs.
    Example JSON: { "image_path": "/path/to/detection.jpg" }
    """
    data = request.json or {}
    image_path = data.get("image_path", None)

    alert_text = "⚠️ Fault detected during 3D printing! ⚠️"
    for chat_id in CHAT_IDS:
        bot.send_message(chat_id, alert_text)
        if image_path and os.path.isfile(image_path):
            with open(image_path, "rb") as f:
                bot.send_photo(chat_id, f)

    return jsonify({"status": "ok"}), 200

################################################################################
#                        HELPER / ACTION LIST COMMAND
################################################################################

def send_action_list(chat_id):
    """
    Sends a list of all available actions with emojis.
    """
    actions = (
        "• /info - Get printer info\n"
        "• /list - List printer objects\n"
        "• /restart_host - Restart the host\n"
        "• /restart_firmware - Restart firmware\n"
        "• /extruder - Get extruder status\n"
        "• /emergency_stop - Emergency stop\n"
        "• /pause - Pause the print\n"
        "• /resume - Resume the print\n"
        "• /temperatures - Get current temperatures\n"
        "• /motion_state - Get motion state\n"
        "• /status - Get a snapshot + job status\n"
    )
    bot.send_message(chat_id, f"🤖 <b>Available Actions</b>:\n{actions}", parse_mode="HTML")

################################################################################
#                            TELEGRAM COMMANDS
################################################################################

@bot.message_handler(commands=['start'])
def cmd_start(message):
    """
    /start: Greet and show actions.
    """
    if message.chat.id in CHAT_IDS:
        bot.reply_to(message, "🤖 Howdy! I’m your 3D Printer Bot. How can I help?")
        send_action_list(message.chat.id)
    else:
        print(message.chat.id)
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")

@bot.message_handler(commands=['info'])
def cmd_info(message):
    """
    /info: Show printer info in a user-friendly way.
    """
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return

    try:
        info = klippy.get_printer_info()  # { "result": {...} }
        text = parse_printer_info(info)
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in /info command: {e}")
        bot.reply_to(message, "❌ Could not retrieve printer info.")

@bot.message_handler(commands=['list'])
def cmd_list(message):
    """
    /list: Show printer objects in a bullet list.
    """
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return

    try:
        objects_data = klippy.list_printer_objects()  # { "result": { "objects": [ ... ] } }
        text = parse_printer_objects(objects_data)
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in /list command: {e}")
        bot.reply_to(message, "❌ Could not list printer objects.")

@bot.message_handler(commands=['extruder'])
def cmd_extruder(message):
    """
    /extruder: Show current extruder temperature/target.
    """
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return

    try:
        # For example, you might call a specialized method or generic object query
        data = klippy.query_printer_object_status({
            "gcode_move": None,
            "toolhead": None,
            "extruder": "target,temperature",
        })
        text = parse_extruder_status(data)
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in /extruder command: {e}")
        bot.reply_to(message, "❌ Could not retrieve extruder status.")

@bot.message_handler(commands=['motion_state'])
def cmd_motion_state(message):
    """
    /motion_state: Show homing and position from toolhead.
    """
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return

    try:
        ms_data = klippy.get_motion_state()  # { "result": { "status": { "toolhead": {...} } } }
        text = parse_motion_state(ms_data)
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in /motion_state command: {e}")
        bot.reply_to(message, "❌ Could not retrieve motion state.")

@bot.message_handler(commands=['restart_host'])
def cmd_restart_host(message):
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return
    try:
        response = klippy.restart_host()
        bot.reply_to(message, f"🔄 Host restart response:\n{response}")
    except Exception as e:
        logging.error(f"Error in /restart_host command: {e}")
        bot.reply_to(message, "❌ Could not restart host.")

@bot.message_handler(commands=['restart_firmware'])
def cmd_restart_firmware(message):
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return
    try:
        response = klippy.firmware_restart()
        bot.reply_to(message, f"🔄 Firmware restart response:\n{response}")
    except Exception as e:
        logging.error(f"Error in /restart_firmware command: {e}")
        bot.reply_to(message, "❌ Could not restart firmware.")

@bot.message_handler(commands=['emergency_stop'])
def cmd_emergency_stop(message):
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return
    try:
        response = klippy.emergency_stop()
        bot.reply_to(message, f"🛑 Emergency Stop:\n{response}")
    except Exception as e:
        logging.error(f"Error in /emergency_stop command: {e}")
        bot.reply_to(message, "❌ Could not perform emergency stop.")

@bot.message_handler(commands=['pause'])
def cmd_pause(message):
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return
    try:
        response = klippy.pause()
        bot.reply_to(message, f"⏸ Pausing print:\n{response}")
    except Exception as e:
        logging.error(f"Error in /pause command: {e}")
        bot.reply_to(message, "❌ Could not pause print.")

@bot.message_handler(commands=['resume'])
def cmd_resume(message):
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return
    try:
        response = klippy.resume()
        bot.reply_to(message, f"▶️ Resuming print:\n{response}")
    except Exception as e:
        logging.error(f"Error in /resume command: {e}")
        bot.reply_to(message, "❌ Could not resume print.")

@bot.message_handler(commands=['temperatures'])
def cmd_temperatures(message):
    """
    /temperatures: Show bed + extruder temperatures in a user-friendly way.
    """
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return

    try:
        temps_data = klippy.get_current_temperatures()  # e.g. { "result": { "status": { "heater_bed": {...}, "extruder": {...} } } }
        result = temps_data.get("result", {})
        status = result.get("status", {})

        bed = status.get("heater_bed", {})
        extruder = status.get("extruder", {})

        bed_temp = bed.get("temperature", 0.0)
        bed_target = bed.get("target", 0.0)
        extr_temp = extruder.get("temperature", 0.0)
        extr_target = extruder.get("target", 0.0)

        text = (
            f"🌡 <b>Current Temperatures</b>:\n"
            f"🛏 Bed: {bed_temp:.1f}°C (Target: {bed_target:.1f}°C)\n"
            f"🔧 Extruder: {extr_temp:.1f}°C (Target: {extr_target:.1f}°C)"
        )
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in /temperatures command: {e}")
        bot.reply_to(message, "❌ Could not retrieve temperatures.")

################################################################################
#                            /status COMMAND
################################################################################

def is_temp_ok(current_temp: float, target_temp: float, tolerance: float = 5.0) -> bool:
    return abs(current_temp - target_temp) <= tolerance



@bot.message_handler(commands=['status'])
def cmd_status(message):
    """
    /status:
      - Fetch job status (print_stats) from Moonraker
      - If printing, show a user-friendly status, including progress in %
      - Otherwise, show idle info + last camera frame
    """
    if message.chat.id not in CHAT_IDS:
        bot.reply_to(message, "🚫 You are not authorized to use this bot.")
        return

    # 1) Get job status from Moonraker
    try:
        data = klippy.get_print_job_status()  # or your method to get JSON
        print_stats = data["result"]["status"]["print_stats"]

        job_filename = print_stats.get("filename", "N/A")
        job_state = print_stats.get("state", "idle")
        print_duration = print_stats.get("print_duration", 0.0)
        total_duration = print_stats.get("total_duration", 0.0) 
        filament_used = print_stats.get("filament_used", 0.0)
        
        if total_duration > 0:
            progress = (print_duration / total_duration) * 100
        else:
            progress = 0.0
        progress_text = f"{progress:.1f}%"
        # Possibly layer-based progress if not null
        info = print_stats.get("info", {})
        current_layer = info.get("current_layer")
        total_layer = info.get("total_layer")

        # Attempt to calculate progress if layers are known
        if current_layer is not None and total_layer is not None:
            if total_layer > 0:
                progress_percent = (current_layer / total_layer) * 100
            else:
                progress_percent = 0.0
        else:
            progress_percent = None  # no layer info available
    except Exception as e:
        logging.error(f"Error fetching job status: {e}")
        # Fallback if something goes wrong
        job_filename = "N/A"
        job_state = "idle"
        print_duration = 0.0
        filament_used = 0.0
        progress_percent = None

    # 2) (Optional) Get bed/extruder temps (if you show them in /status)
    try:
        temps_data = klippy.get_current_temperatures()
        r = temps_data.get("result", {})
        s = r.get("status", {})

        bed_stat = s.get("heater_bed", {})
        extr_stat = s.get("extruder", {})

        bed_temp = bed_stat.get("temperature", 0.0)
        bed_target = bed_stat.get("target", 0.0)
        extr_temp = extr_stat.get("temperature", 0.0)
        extr_target = extr_stat.get("target", 0.0)
    except Exception as e:
        logging.error(f"Error fetching temperatures: {e}")
        bed_temp, bed_target, extr_temp, extr_target = 0, 0, 0, 0

    # 3) Build user-friendly message
    latest_frame_path = os.path.join("../data/frames/", "latest_frame.jpg")

    # Quick example: convert `print_duration` seconds to minutes
    print_mins = int(print_duration // 60)
    fil_used_str = f"{filament_used:.1f} mm"  # Just show raw mm

    # If we can show progress in %, do so
    if progress_percent is not None:
        progress_str = f"{progress_percent:.1f}%"
    else:
        progress_str = "N/A"

    if job_state.lower() == "printing":
        status_text = (
            f"🤖 <b>Printer is currently printing!</b>\n"
            f"📄 <b>File:</b> {job_filename}\n"
            f"⏱ <b>Print Duration:</b> {print_mins} min\n"
            f"📈 <b>Progress:</b> {progress_text}\n"
            f"🌀 <b>Filament Used:</b> {fil_used_str}\n"
            f"🛏 Bed: {bed_temp:.1f}/{bed_target:.1f}\n"
            f"🔧 Extruder: {extr_temp:.1f}/{extr_target:.1f}\n"
            f"<i>Latest camera frame below:</i>"
        )

        bot.send_message(message.chat.id, status_text, parse_mode="HTML")

        if os.path.isfile(latest_frame_path):
            with open(latest_frame_path, "rb") as f:
                bot.send_photo(message.chat.id, f)
        else:
            bot.send_message(message.chat.id, "No recent frame found on disk.")

    else:
        # Idle or other states
        idle_text = (
            f"🚦 <b>State:</b> {job_state.capitalize()}\n"
            "No job is currently running.\n\n"
            f"📄 <b>File:</b> {job_filename}\n"
            f"🌀 <b>Filament Used:</b> {fil_used_str}\n"
            f"🛏 Bed: {bed_temp:.1f}/{bed_target:.1f}\n"
            f"🔧 Extruder: {extr_temp:.1f}/{extr_target:.1f}"
        )

        if os.path.isfile(latest_frame_path):
            with open(latest_frame_path, "rb") as f:
                bot.send_photo(message.chat.id, f, caption=idle_text, parse_mode="HTML")
        else:
            bot.reply_to(message, idle_text + "\n\nNo recent frame found.")

################################################################################
#                      STARTING BOT + FLASK SERVER
################################################################################

def start_bot_polling():
    bot.infinity_polling()

if __name__ == "__main__":
    # 1) Start the bot in a background thread
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()

    # 2) Start the Flask server (blocking)
    logging.info("Starting Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5000)

