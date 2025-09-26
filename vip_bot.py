import os
import threading
import csv
from flask import Flask
import telebot

# =======================
# Environment Variables
# =======================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    raise Exception("Please set BOT_TOKEN and ADMIN_ID environment variables")

ADMIN_ID = int(ADMIN_ID)

# =======================
# Initialize Bot
# =======================
bot = telebot.TeleBot(BOT_TOKEN)

# =======================
# Dummy Flask Web Server
# =======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram VIP Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# =======================
# Load VIP Slots
# =======================
SLOTS_FILE = 'slots.csv'
slots = []

with open(SLOTS_FILE, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        slots.append(row)

# Track used slots and user attempts
user_attempts = {}   # {user_id: attempts_used}
user_slots = {}      # {user_id: assigned_slot_index}

MAX_ATTEMPTS = 3

# =======================
# Bot Handlers
# =======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "💎 Welcome! Use /buy to get VIP channels.")

@bot.message_handler(commands=['buy'])
def buy(message):
    bot.send_message(message.chat.id,
                     "Choose your payment method:\n1️⃣ Maya\n2️⃣ GCash\n\nSend screenshot after payment.")

@bot.message_handler(content_types=['photo'])
def receive_screenshot(message):
    user_id = message.from_user.id
    user_attempts.setdefault(user_id, 0)

    if user_attempts[user_id] >= MAX_ATTEMPTS:
        bot.send_message(user_id, "❌ You have reached the maximum number of attempts. Contact admin.")
        return

    # Notify admin
    bot.send_message(ADMIN_ID,
                     f"📩 New Payment Screenshot Received!\n👤 From: @{message.from_user.username}\n🆔 User ID: {user_id}\n⚡ Actions: /approve_{user_id} /reject_{user_id}")

    bot.send_message(user_id, "✅ Screenshot received, waiting for verification.")

# =======================
# Admin Commands
# =======================
@bot.message_handler(commands=lambda m: m.text.startswith('/approve_'))
def approve(message):
    try:
        user_id = int(message.text.split('_')[1])
        if user_id in user_slots:
            bot.send_message(message.chat.id, "⚠️ This user already has assigned VIP links.")
            return
        # Assign first available slot
        for i, slot in enumerate(slots):
            if slot != []:
                user_slots[user_id] = i
                bot.send_message(user_id,
                                 f"🎉 Payment verified!\nHere are your VIP channel links:\n1️⃣ {slot[0]}\n2️⃣ {slot[1]}")
                slots[i] = []  # mark as used
                bot.send_message(message.chat.id, f"✅ Assigned slot {i} to user {user_id}")
                return
        bot.send_message(message.chat.id, "❌ No more slots available.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.message_handler(commands=lambda m: m.text.startswith('/reject_'))
def reject(message):
    try:
        user_id = int(message.text.split('_')[1])
        user_attempts[user_id] += 1
        attempts = user_attempts[user_id]
        if attempts >= MAX_ATTEMPTS:
            bot.send_message(user_id, "❌ You have reached the maximum number of attempts. Contact admin.")
        else:
            bot.send_message(user_id,
                             f"⚠️ Payment could not be verified.\n🔁 Attempts used: {attempts}/{MAX_ATTEMPTS}\n📌 Send the correct screenshot again.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# =======================
# Start Bot
# =======================
print("Bot is running...")
bot.polling(non_stop=True)
