import logging
import asyncio
import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

daily_data = {"code": None, "start_id": 0, "end_id": 0}

# --- KEEP ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running! (Status: Live)"
def run_http(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_http); t.start()

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! 📂\nPlease send the daily access code to receive videos.")

async def set_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin Command: /setcode CODE START END"""
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID): return
    try:
        args = context.args
        daily_data["code"] = args[0]
        daily_data["start_id"] = int(args[1])
        daily_data["end_id"] = int(args[2])
        await update.message.reply_text(f"✅ Config Set!\nCode: {daily_data['code']}\nRange: {daily_data['start_id']}-{daily_data['end_id']}")
    except: await update.message.reply_text("❌ Error in command format.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_data["code"]:
        await update.message.reply_text("⚠️ No content ready for today.")
        return
    if update.message.text.strip() == daily_data["code"]:
        await update.message.reply_text("✅ Code Accepted! Sending videos...")
        try:
            for msg_id in range(daily_data["start_id"], daily_data["end_id"] + 1):
                try:
                    await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=int(CHANNEL_ID), message_id=msg_id)
                    await asyncio.sleep(0.5)
                except: continue
            await update.message.reply_text("🎉 All videos sent!")
        except Exception as e: await update.message.reply_text("❌ Error sending videos.")
    else: await update.message.reply_text("❌ Invalid Code!")

# --- MAIN ---
if __name__ == '__main__':
    keep_alive()
    if BOT_TOKEN:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('setcode', set_code))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        application.run_polling()
