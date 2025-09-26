import telebot
from telebot import types
import threading
import csv
import os

# ---------------- CONFIG ----------------
TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ['ADMIN_ID'])
MAX_RETRIES = 3
INACTIVITY_MINUTES = 5
SLOTS_FILE = "slots.csv"

bot = telebot.TeleBot(TOKEN)
users = {}
slots = []

if os.path.exists(SLOTS_FILE):
    with open(SLOTS_FILE, newline='') as f:
        reader = csv.reader(f)
        slots = [row for row in reader]

def save_slots():
    with open(SLOTS_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(slots)

def send_inactivity_reminder(user_id):
    if user_id in users and users[user_id]["screenshot"] is None:
        bot.send_message(user_id, "⚠️ You haven’t sent your payment screenshot yet.\nPlease complete your payment to claim your VIP channels.")

def start_inactivity_timer(user_id):
    if users[user_id].get("timer"):
        users[user_id]["timer"].cancel()
    timer = threading.Timer(INACTIVITY_MINUTES*60, send_inactivity_reminder, args=[user_id])
    timer.start()
    users[user_id]["timer"] = timer

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Buy VIP Channels"))
    bot.send_message(message.chat.id, "💎 Avail / Buy VIP Channels", reply_markup=markup)

@bot.message_handler(commands=['addslot'])
def add_slot(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not authorized to use this command.")
        return
    args = message.text.split(maxsplit=2)
    if len(args)<3:
        bot.send_message(message.chat.id, "Usage: /addslot LINK1 LINK2")
        return
    new_slot = [args[1], args[2]]
    slots.append(new_slot)
    save_slots()
    bot.send_message(message.chat.id, f"✅ New VIP slot added:\n1️⃣ {new_slot[0]}\n2️⃣ {new_slot[1]}")

@bot.message_handler(func=lambda message: message.text=="Buy VIP Channels")
def buy_vip(message):
    user_id = message.from_user.id
    if not slots:
        bot.send_message(message.chat.id, "⚠️ Sorry, VIP slots are sold out.")
        return
    if user_id not in users:
        users[user_id] = {"attempts":0,"slot":None,"screenshot":None,"timer":None}
    start_inactivity_timer(user_id)
    bot.send_message(message.chat.id, f"⚡ Available VIP slots: {len(slots)}\nChoose your payment method:\n1️⃣ Maya\n2️⃣ GCash\n\nAfter payment, send your screenshot here.")

@bot.message_handler(content_types=['photo'])
def receive_screenshot(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"attempts":0,"slot":None,"screenshot":None,"timer":None}
    if users[user_id].get("timer"):
        users[user_id]["timer"].cancel()
    users[user_id]["screenshot"] = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✅ Screenshot received, waiting for verification.")
    start_inactivity_timer(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}"))
    markup.add(types.InlineKeyboardButton("Reject", callback_data=f"reject_{user_id}"))
    bot.send_message(ADMIN_ID, f"📩 New Payment Screenshot!\n👤 User: @{message.from_user.username}\n🆔 {user_id}\n⚡ Actions: Approve / Reject", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = int(call.data.split("_")[1])
    action = call.data.split("_")[0]
    if user_id not in users:
        bot.answer_callback_query(call.id, "User not found.")
        return
    if action=="approve":
        if slots:
            slot = slots.pop(0)
            save_slots()
            users[user_id]["slot"] = slot
            bot.send_message(user_id, f"🎉 Payment verified!\nHere are your VIP links:\n1️⃣ {slot[0]}\n2️⃣ {slot[1]}")
        else:
            bot.send_message(user_id, "⚠️ Sorry, VIP slots are sold out.")
        bot.answer_callback_query(call.id, "Payment approved.")
    elif action=="reject":
        users[user_id]["attempts"] += 1
        if users[user_id]["attempts"]>=3:
            bot.send_message(user_id, "❌ Maximum attempts reached. Contact admin.")
        else:
            users[user_id]["screenshot"]=None
            start_inactivity_timer(user_id)
            bot.send_message(user_id, f"⚠️ Payment not verified.\n🔁 Attempts: {users[user_id]['attempts']}/3\nResend screenshot for review.")
        bot.answer_callback_query(call.id, "Payment rejected.")

print("Bot is running...")
bot.polling()
