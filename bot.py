import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask

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
    return "🚀 Telegram Gemini Bot is up and running!"

# Load keys from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.error("❌ Missing TELEGRAM_TOKEN or GEMINI_API_KEY in environment variables.")
    raise Exception("Missing TELEGRAM_TOKEN or GEMINI_API_KEY in environment variables.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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

        # Send the Gemini response back to Telegram
        await update.message.reply_text(response.text)

    except Exception as e:
        logging.error(f"💥 Error in handle_message: {e}")
        await update.message.reply_text("Sorry, an error occurred. 😢")

# Main bot runner
def run_bot():
    app_builder = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Commands and message handlers
    app_builder.add_handler(CommandHandler("start", start))
    app_builder.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("✅ Bot started successfully. Listening for messages...")

    # Start the Telegram bot
    app_builder.run_polling()

# Entry point
if __name__ == "__main__":
    import threading

    # Run Flask app and Telegram bot in parallel (for Render)
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
    run_bot()

