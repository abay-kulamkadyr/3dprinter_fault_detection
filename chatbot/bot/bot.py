import telebot
from config import BOT_TOKEN
from bot.commands import register_commands

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Register all command handlers
register_commands(bot)


def start_bot_polling():
    """Start the bot in polling mode."""
    bot.infinity_polling()


if __name__ == "__main__":
    start_bot_polling()
