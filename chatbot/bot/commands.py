from telebot import TeleBot
from bot.helpers import (
    parse_printer_info,
    parse_printer_objects,
    parse_extruder_status,
    parse_motion_state,
    parse_job_status,
    send_action_list,
    needs_confirmation,
    remove_from_pending_confirmation
)

from api.klippy_api import KlippyAPI
from config import CHAT_IDS, KLIPPER_BASE_URL, STREAM_URL
from bot.stream import StreamLauncher
from bot.shared_state import pending_confirmations
from telebot import types
import logging
import time
import threading
import os

# Initialize Klippy API
klippy = KlippyAPI(KLIPPER_BASE_URL)

# Initialize StreamLauncher
stream_launcher = StreamLauncher()

# ======================
# INLINE KEYBOARD LAYOUTS
# ======================
def create_main_markup():
    """Create the main inline keyboard layout"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Status and Monitoring
    markup.row(
        types.InlineKeyboardButton("🖨 Printer Status", callback_data="status"),
        types.InlineKeyboardButton("🌡 Temperatures", callback_data="temperatures")
    )

    # Print Controls
    markup.row(
        types.InlineKeyboardButton("▶️ Resume Print", callback_data="resume"), 
        types.InlineKeyboardButton("⏸ Pause Print", callback_data="pause"),
    )

    # Advanced Controls
    markup.row(
        types.InlineKeyboardButton("📷 Start Stream", callback_data="stream"),
        types.InlineKeyboardButton("🛑 Stop Stream", callback_data="stop_stream")
    )

    # System Controls
    markup.row(
        types.InlineKeyboardButton("🔁 Restart Host", callback_data="restart_host"),
        types.InlineKeyboardButton("⚠️ Emergency Stop", callback_data="emergency_stop")
    )

    # Additional Info
    markup.row(
        types.InlineKeyboardButton("📊 Motion State", callback_data="motion_state"),
        types.InlineKeyboardButton("📜 Printer Objects", callback_data="list")
    )

    return markup


def create_confirmation_markup(command):
    """Create confirmation buttons for critical actions"""
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ confirm", callback_data=f"confirm_{command}"),
        types.InlineKeyboardButton("❌ cancel", callback_data="cancel_action")
    )
    return markup


def register_commands(bot: TeleBot):
    """Register all command handlers with the bot."""
    @bot.message_handler(commands=['start', 'help'])
    def cmd_start(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 Unauthorized access.")
            return

        welcome_msg = (
            "🤖 *3D Printer Bot Ready!*\n"
            "Use the buttons below to control your printer:\n"
            "_________________________________\n"
            "• 🖨 Status: Current printer state & snapshot\n"
            "• 🌡 Temps: Extruder/Bed temperatures\n"
            "• ⏸/▶️: Pause/Resume ongoing print\n"
            "• 📷 Stream: Live camera monitoring\n"
            "• 🔁 System: Host/Firmware controls\n"
        )
        bot.send_message(
            message.chat.id,
            welcome_msg,
            parse_mode="HTML",
            reply_markup=create_main_markup(),
        )

    @bot.message_handler(commands=['info'])
    def cmd_info(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        try:
            info = klippy.get_printer_info()
            text = parse_printer_info(info)
            bot.reply_to(message, text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Error in /info command: {e}")
            bot.reply_to(message, "❌ Could not retrieve printer info.")

    @bot.message_handler(commands=['list'])
    def cmd_list(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        try:
            objects_data = klippy.list_printer_objects()
            text = parse_printer_objects(objects_data)
            bot.reply_to(message, text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Error in /list command: {e}")
            bot.reply_to(message, "❌ Could not list printer objects.")

    @bot.message_handler(commands=['extruder'])
    def cmd_extruder(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        try:
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
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        try:
            ms_data = klippy.get_motion_state()
            text = parse_motion_state(ms_data)
            bot.reply_to(message, text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Error in /motion_state command: {e}")
            bot.reply_to(message, "❌ Could not retrieve motion state.")

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
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        try:
            temps_data = klippy.get_current_temperatures()
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

    @bot.message_handler(commands=['status'])
    def cmd_status(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        try:
            data = klippy.get_print_job_status()
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

            info = print_stats.get("info", {})
            current_layer = info.get("current_layer")
            total_layer = info.get("total_layer")

            if current_layer is not None and total_layer is not None:
                if total_layer > 0:
                    progress_percent = (current_layer / total_layer) * 100
                else:
                    progress_percent = 0.0
            else:
                progress_percent = None

            temps_data = klippy.get_current_temperatures()
            r = temps_data.get("result", {})
            s = r.get("status", {})

            bed_stat = s.get("heater_bed", {})
            extr_stat = s.get("extruder", {})

            bed_temp = bed_stat.get("temperature", 0.0)
            bed_target = bed_stat.get("target", 0.0)
            extr_temp = extr_stat.get("temperature", 0.0)
            extr_target = extr_stat.get("target", 0.0)

            latest_frame_path = os.path.join("../data/frames/", "latest_frame.jpg")
            print_mins = int(print_duration // 60)
            fil_used_str = f"{filament_used:.1f} mm"

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
                        bot.send_photo(message.chat.id, f, caption=idle_text, parse_mode="HTML", reply_markup=create_main_markup())
                else:
                    bot.reply_to(message, idle_text + "\n\nNo recent frame found.")

        except Exception as e:
            latest_frame_path = os.path.join("../data/frames/", "latest_frame.jpg")
            if os.path.isfile(latest_frame_path):
                with open(latest_frame_path, "rb") as f:
                    bot.send_photo(message.chat.id, f)
            else:
                bot.send_message(message.chat.id, "No recent frame found on disk.")
            logging.error(f"Error in /status command: {e}")
            bot.reply_to(message, "❌ Could not retrieve printer status.", reply_markup=create_main_markup())

    @bot.message_handler(commands=['emergency_stop', 'restart_host', 'restart_firmware'])
    def handle_dangerous_commands(message):
        command = message.text.split('@')[0][1:]
        if needs_confirmation(message.chat.id, command):
            print("needs confirmation")
            bot.reply_to(
                message,
                f"⚠️ Confirm {command.replace('_', ' ').title()}?",
                reply_markup=create_confirmation_markup(command)
            )
        else:
            execute_dangerous_command(command, message)

    # ======================
    # CALLBACK HANDLERS
    # ======================
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        if call.data.startswith("confirm_"):
            # Handle confirmation of dangerous commands
            command = call.data.split("confirm_")[1]
            execute_dangerous_command(command, call.message)

        elif call.data == "cancel_action":
            # Handle cancellation of dangerous commands
            bot.edit_message_text(
                "⚠️ Action cancelled.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_main_markup()
            )
            remove_from_pending_confirmation(call.message.chat.id)

        elif call.data in ['restart_host', 'emergency_stop', 'restart_firmware']:
            # Handle dangerous commands initiated via button click
            if needs_confirmation(call.message.chat.id, call.data):
                bot.edit_message_text(
                    f"⚠️ Confirm {call.data.replace('_', ' ').title()}?",
                    chat_id=call.message.chat.id,          # Correct: chat_id
                    message_id=call.message.message_id,    # Correct: message_id
                    reply_markup=create_confirmation_markup(call.data)
                )
            else:
                execute_dangerous_command(call.data, call.message)

        else:
            # Handle other regular commands
            command_mapping = {
                'status': cmd_status,
                'temperatures': cmd_temperatures,
                'pause': cmd_pause,
                'resume': cmd_resume,
                'stream': cmd_stream,
                'stop_stream': cmd_stop_stream,
                'motion_state': cmd_motion_state,
                'list': cmd_list
            }
            if call.data in command_mapping:
                command_mapping[call.data](call.message)
            else:
                bot.answer_callback_query(call.id, "⚠️ Command not implemented")

    # ======================
    # HELPER FUNCTIONS
    # ======================
    def execute_dangerous_command(command, message):
        try:
            if command == "emergency_stop":
                response = klippy.emergency_stop()
            elif command == "restart_host":
                response = klippy.restart_host()
            elif command == "restart_firmware":
                response = klippy.firmware_restart()
            bot.reply_to(message, f"✅ {command.replace('_', ' ').title()} executed!")

        except Exception as e:
            logging.error(f"{command} error: {e}")
            bot.reply_to(message, f"❌ {command.replace('_', ' ').title()} failed!")

    @bot.message_handler(commands=['stream'])
    def cmd_stream(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this command.")
            return

        def handle_stream():
            if stream_launcher.is_stream_running():
                bot.send_message(message.chat.id, "🔄 The stream is already running.")
                return

            stream_launcher.start_stream()
            time.sleep(2)  # Allow stream to start

            if stream_launcher.is_stream_running():
                stream_url = STREAM_URL
                kbot.send_message(message.chat.id, f"✅ Stream started successfully!\nWatch it here: {stream_url}")
            else:
                bot.send_message(message.chat.id, "❌ Failed to start the stream. Please check the server logs.")

        threading.Thread(target=handle_stream, daemon=True).start()

    @bot.message_handler(commands=['stop_stream'])
    def cmd_stop_stream(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this command.")
            return

        def handle_stop_stream():
            if not stream_launcher.is_stream_running():
                bot.send_message(message.chat.id, "⚠️ The stream is not currently running.")
                return

            stream_launcher.stop_stream()

            #TODO CHECK IF THISE REQUIRED 
            time.sleep(2)  # Allow stream to stop

            if not stream_launcher.is_stream_running():
                bot.send_message(message.chat.id, "🛑 Stream stopped successfully.")
            else:
                bot.send_message(message.chat.id, "❌ Failed to stop the stream. Please check the server logs.")
        threading.Thread(target=handle_stop_stream, daemon=True).start()
