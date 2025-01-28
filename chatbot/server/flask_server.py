from flask import Flask, request, jsonify
import os
from bot.bot import bot
from config import CHAT_IDS

app = Flask(__name__)


@app.route("/detection_event", methods=["POST"])
def detection_event():
    data = request.json or {}
    image_path = data.get("image_path", None)
    print("from chatbot image path" + image_path)
    alert_text = "⚠️ Fault detected during 3D printing! ⚠️"
    for chat_id in CHAT_IDS:
        bot.send_message(chat_id, alert_text)
        if image_path and os.path.isfile(image_path):
            with open(image_path, "rb") as f:
                bot.send_photo(chat_id, f)

    return jsonify({"status": "ok"}), 200
