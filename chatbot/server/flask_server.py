import re
import os
from flask import Flask, request, jsonify
from bot.bot import bot
from config import CHAT_IDS, KLIPPER_BASE_URL
from bot.commands import create_main_markup
from api.klippy_api import KlippyAPI

app = Flask(__name__)

# Create an instance of your printer control API
klippy = KlippyAPI(KLIPPER_BASE_URL)

def escape_markdown_v2(text: str) -> str:
    """
    Escape all special characters for Telegram MarkdownV2.
    Characters to escape include: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    escape_chars = r'_*[\]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

@app.route("/detection_event", methods=["POST"])
def detection_event():
    data = request.json or {}
    image_path = data.get("image_path", None)
    
    # Build the alert text.
    # (If you plan to include exception messages later, remember to escape them as well.)
    alert_text = "⚠️ Fault detected during 3D printing! ⚠️\n"
    #alert_text += "Could not stop printing: "  # This could be extended with an error message.
    
    # Escape alert_text for MarkdownV2
    alert_text = escape_markdown_v2(alert_text)
    
    # Log the image_path (converted to string in case it is None)
    print("image path: " + str(image_path))
    
    # Now, for every authorized chat, send a message (or photo if an image is provided)
    for chat_id in CHAT_IDS:
        try:
            if image_path and os.path.isfile(image_path):
                with open(image_path, "rb") as f:
                    bot.send_photo(
                        chat_id,
                        f,
                        caption=alert_text,
                        parse_mode="MarkdownV2",
                        reply_markup=create_main_markup()
                    )
            else:
                bot.send_message(
                    chat_id,
                    alert_text,
                    parse_mode="MarkdownV2",
                    reply_markup=create_main_markup()
                )
        except Exception as e:
            # Log the error and continue with the next chat id.
            print(f"Error sending message to {chat_id}: {e}")
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__": app.run(host="0.0.0.0", port=5000)
