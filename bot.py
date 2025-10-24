import os
import logging
import asyncio
import threading
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Flask app for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Telegram Gemini Bot is up and running!", 200

# Load keys from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.error("❌ Missing TELEGRAM_TOKEN or GEMINI_API_KEY in environment variables.")
    raise Exception("Missing TELEGRAM_TOKEN or GEMINI_API_KEY in environment variables.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Telegram bot setup
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hey there 👋! I’m your *AditvGPT*, powered by Gemini AI.\n\n"
        "Ask me *anything* — text, ideas, or even coding questions!"
    )

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    logging.info(f"📩 User said: {user_message}")

    try:
        # Run Gemini API call in executor to prevent blocking async loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, user_message)

        # Send Gemini response back to Telegram
        await update.message.reply_text(response.text)

    except Exception as e:
        logging.error(f"💥 Error in handle_message: {e}")
        await update.message.reply_text("Sorry, an error occurred. 😢")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Flask Webhook endpoint for Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
        return "Webhook received!", 200
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return "Error", 500

# Function to start bot in background
def run_polling():
    logging.info("✅ Starting bot polling...")
    application.run_polling()

# Main entry point
if __name__ == "__main__":
    # Run Flask app and bot together
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
    run_polling()

