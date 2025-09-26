import os
import threading
from flask import Flask
import telebot

# =======================
# Environment Variables
# =======================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    raise Exception("Please set BOT_TOKEN and ADMIN_ID environment variables")

# =======================
# Initialize Bot
# =======================
bot = telebot.TeleBot(BOT_TOKEN)
admin_id = int(ADMIN_ID)

# =======================
# Dummy Flask Web Server
# =======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram VIP Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # Render assigns PORT
    app.run(host="0.0.0.0", port=port)

# Start Flask in a separate thread
threading.Thread(target=run_flask).start()

# =======================
# Example Bot Handlers
# =======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "💎 Welcome! Use /buy to get VIP channels.")

@bot.message_handler(commands=['buy'])
def buy(message):
    bot.send_message(message.chat.id,
                     "Choose your payment method:\n1️⃣ Maya\n2️⃣ GCash\n\nSend screenshot after payment.")

# Add more handlers for payment screenshot, approve/reject, etc.

# =======================
# Start Bot
# =======================
print("Bot is running...")
bot.polling(non_stop=True)
