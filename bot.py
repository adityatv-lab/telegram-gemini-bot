import os
import logging
import asyncio
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I am your Gemini-powered assistant. Send me a message and I'll help you."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await update.message.reply_text("Sorry, an error occurred.")

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

async def main_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async with application:
        await application.initialize()
        await application.updater.start_polling()
        await application.start()
        await asyncio.Event().wait()

def run_bot_in_thread():
    asyncio.run(main_bot())

bot_thread = threading.Thread(target=run_bot_in_thread)
bot_thread.daemon = True
bot_thread.start()
