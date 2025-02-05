from flask import Flask, request, jsonify
import os
from bot.bot import bot
from config import CHAT_IDS
from telebot import types
from bot.commands import create_main_markup

from api.klippy_api import KlippyAPI
from config import KLIPPER_BASE_URL

app = Flask(__name__)

# Create an instance of your printer control API if needed
klippy = KlippyAPI(KLIPPER_BASE_URL)

@app.route("/detection_event", methods=["POST"])
def detection_event():
    data = request.json or {}
    image_path = data.get("image_path", None)
    alert_text = "⚠️ Fault detected during 3D printing! ⚠️"
    
    # Check if a print is active and attempt to stop it.
    try:
        job_status = klippy.get_print_job_status()
        print_stats = job_status.get("result", {}).get("status", {}).get("print_stats", {})
        state = print_stats.get("state", "").lower()
        if state == "printing":
            # Stop the printing process
            response = klippy.pause()
            alert_text += "\nPrinting has been stopped."
        else:
            alert_text += "\nNo active print was found."
    except Exception as e:
        # In case of error, update the alert text accordingly.
        alert_text += f"\nCould not stop printing: {e}"
    
    # Now, for every authorized chat, send a message (or photo if an image is provided)
    for chat_id in CHAT_IDS:
        if image_path and os.path.isfile(image_path):
            with open(image_path, "rb") as f:
                bot.send_photo(
                    chat_id, 
                    f, 
                    caption=alert_text, 
                    parse_mode="HTML", 
                    reply_markup=create_main_markup()
                )
        else:
            bot.send_message(
                chat_id, 
                alert_text, 
                parse_mode="HTML", 
                reply_markup=create_main_markup()
            )
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

