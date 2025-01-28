from telebot import TeleBot
from bot.helpers import (
    parse_printer_info,
    parse_printer_objects,
    parse_extruder_status,
    parse_motion_state,
    parse_job_status,
    send_action_list,
    needs_confirmation
)
from api.klippy_api import KlippyAPI
from config import CHAT_IDS, KLIPPER_BASE_URL
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

#Markup buttons for when dection happen
markup_on_detection = types.InlineKeyboardMarkup(row_width=2)
resume_printing_btn = types.InlineKeyboardButton("Resume Printing", callback_data = "answer")
printer_status_btn = types.InlineKeyboardButton("Get Printer Status", callback_data="answer")
start_stream_btn = types.InlineKeyboardButton("View Live Stream", callback_data="stream")

markup_on_detection.add(resume_printing_btn, start_stream_btn, printer_status_btn)

#Markup for all actions 
markup_all = types.InlineKeyboardMarkup(row_width=3)
info_btn = types.InlineKeyboardButton("Printer info", callback_data = "answer")
list_btn = types.InlineKeyboardButton("List Printer Objects", callback_data = "answer")
restart_host_btn = types.InlineKeyboardButton("Restart Host", callback_data = "answer")
restart_firmware_btn = types.InlineKeyboardButton("Restart Firmware", callback_data = "answer")
extruder_btn = types.InlineKeyboardButton("Get Extruder Info", callback_data = "answer")
emergency_stop_btn = types.InlineKeyboardButton("Emergency Stop", callback_data = "answer")
pause_btn = types.InlineKeyboardButton("Pause Printing", callback_data = "answer")
temperatures_btn = types.InlineKeyboardButton("Get Temperatures", callback_data = "temperatures")
motion_state_btn = types.InlineKeyboardButton("Motion State Info", callback_data = "answer")
stop_steam_btn = types.InlineKeyboardButton("Stop Stream", callback_data = "stop_stream")
status_btn = types.InlineKeyboardButton("Get Status and SnapShot", callback_data = "status")

markup_all.add(info_btn, status_btn, temperatures_btn, motion_state_btn, start_stream_btn) 



def register_commands(bot: TeleBot):
    """Register all command handlers with the bot."""

    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        if message.chat.id in CHAT_IDS:
            bot.reply_to(message, "🤖 Howdy! I’m your 3D Printer Bot. How can I help?")
            send_action_list(bot, message.chat.id, reply_markup=markup_all)
        else:
            print("chat id = " + str(message.chat.id))
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")

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

    @bot.message_handler(commands=['restart_host'])
    def cmd_restart_host(message):
        if message.chat.id not in CHAT_IDS:
            bot.reply_to(message, "🚫 You are not authorized to use this bot.")
            return

        if needs_confirmation(message.chat.id, 'restart_host'):
            bot.reply_to(
                message,
                "⚠️ You are about to restart the host. Type /restart_host again to confirm."
            )
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

        if needs_confirmation(message.chat.id, 'restart_firmware'):
            bot.reply_to(
                message,
                "⚠️ You are about to restart the firmware. Type /restart_firmware again to confirm."
            )
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

        if needs_confirmation(message.chat.id, 'emergency_stop'):
            bot.reply_to(
                message,
                "⚠️ EMERGENCY STOP requested. Type /emergency_stop again to confirm."
            )
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
                        bot.send_photo(message.chat.id, f, caption=idle_text, parse_mode="HTML")
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
            bot.reply_to(message, "❌ Could not retrieve printer status.", reply_markup=markup_on_detection)

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
                stream_url = "http://192.168.31.109:8080/"
                bot.send_message(message.chat.id, f"✅ Stream started successfully!\nWatch it here: {stream_url}")
            else:
                bot.send_message(message.chat.id, "❌ Failed to start the stream. Please check the server logs.")

        threading.Thread(target=handle_stream, daemon=True).start()
    @bot.callback_query_handler(func=lambda call:True)
    def answer(callback):
        if callback.message:
            if callback.data == "stream":
                cmd_stream(callback.message)
            if callback.data == "stop_stream":
                cmd_stop_stream(callback.message)
            if callback.data == "status":
                cmd_status(callback.message)
            if callback.data == "temperatures":
                cmd_temperatures(callback.message)
                
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
            time.sleep(2)  # Allow stream to stop

            if not stream_launcher.is_stream_running():
                bot.send_message(message.chat.id, "🛑 Stream stopped successfully.")
            else:
                bot.send_message(message.chat.id, "❌ Failed to stop the stream. Please check the server logs.")
        

        threading.Thread(target=handle_stop_stream, daemon=True).start()
