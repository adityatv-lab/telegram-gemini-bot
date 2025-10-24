import os
import logging
import asyncio
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Setup ---
# Set your environment variables in Render's "Environment" section
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- Bot Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message for the /start command."""
    await update.message.reply_text(
        "Hi! I am your Gemini-powered assistant. Send me a message and I'll help you."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages and gets a response from Gemini."""
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await update.message.reply_text("Sorry, an error occurred.")

# --- Web Server and Bot Runner ---

# 1. Define the Flask app (the web server part)
# The variable name MUST be 'app' for Gunicorn to find it.
app = Flask(__name__)

@app.route('/')
def index():
    """A simple route to prove the web server is running."""
    return "Bot is running!"

# 2. Define the bot's asynchronous main function
async def main_bot():
    """Initializes and runs the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async with application:
        await application.initialize()
        await application.updater.start_polling()
        await application.start()
        # This keeps the bot running in the background
        await asyncio.Event().wait()

def run_bot_in_thread():
    """Function to run the bot's async loop in a new thread."""
    asyncio.run(main_bot())

# 3. Start the bot in a background thread when the script starts
# This ensures the bot starts when Render runs your web server
bot_thread = threading.Thread(target=run_bot_in_thread)
bot_thread.daemon = True
bot_thread.start()

# Note: We don't need `if __name__ == '__main__': app.run()` because
# Gunicorn (from the start command) will run the 'app' object.
