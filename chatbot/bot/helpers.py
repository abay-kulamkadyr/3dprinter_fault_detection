from bot.shared_state import pending_confirmations
from telebot import types


def parse_printer_info(info: dict) -> str:
    """Extracts and formats the most important fields from the /info command result."""
    result = info.get("result", {})
    state = result.get("state", "unknown")
    state_msg = result.get("state_message", "N/A")
    hostname = result.get("hostname", "N/A")
    software_version = result.get("software_version", "N/A")
    config_file = result.get("config_file", "N/A")

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
    """Parse the response from /list."""
    result = objects_data.get("result", {})
    obj_list = result.get("objects", [])
    if not obj_list:
        return "🤔 No objects found."

    bullet_items = "\n".join([f"• {obj}" for obj in obj_list])
    return f"🗃 <b>Printer Objects</b>:\n{bullet_items}"


def parse_extruder_status(data: dict) -> str:
    """Parse the /extruder result."""
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
    """Parse the /motion_state result."""
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
    """Parse the /job_status result."""
    result = job_status.get("result", {})
    job_info = result.get("job", {})
    progress_info = result.get("progress", {})
    state = result.get("state", "Unknown")

    file_name = job_info.get("file", {}).get("name", "N/A")
    completion = progress_info.get("completion", None)
    completion_str = f"{completion:.1f}%" if completion is not None else "N/A"

    text = (
        f"📄 <b>Job Status</b>:\n"
        f"• State: {state}\n"
        f"• File: {file_name}\n"
        f"• Completion: {completion_str}\n"
    )
    return text


def send_action_list(bot, chat_id, reply_markup=None):
    """Sends a list of all available actions with emojis."""
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
        "• /stream - Start the live stream\n"
        "• /stop_stream - Stop the live stream\n"
    )
    bot.send_message(chat_id, f"🤖 <b>Available Actions</b>:\n{actions}", parse_mode="HTML", reply_markup=reply_markup)


def needs_confirmation(user_id: int, command_name: str) -> bool:
    """Checks if a command requires confirmation."""
    if pending_confirmations.get(user_id) == command_name:
        pending_confirmations.pop(user_id, None)
        return False
    else:
        pending_confirmations[user_id] = command_name
        return True


def remove_from_pending_confirmation(user_id: int) -> None:
    pending_confirmations.pop(user_id, None)
