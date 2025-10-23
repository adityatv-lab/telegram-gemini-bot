import os
import logging
import threading
from flask import Flask, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get keys from Render environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PORT = int(os.getenv("PORT", 8080))

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or GOOGLE_API_KEY environment variable")

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)

# Function to call Gemini API
def gemini_reply(prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error from Gemini: {e}")
        return "Sorry, I couldn’t process that right now 😅"

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! I’m your Gemini-powered AI bot 🤖 — ask me anything!")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = gemini_reply(user_text)
    await update.message.reply_text(response)

def start_telegram():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.run_polling()

# Flask healthcheck (Render requires a web service)
flask_app = Flask(__name__)

@flask_app.route("/healthz")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    threading.Thread(target=start_telegram, daemon=True).start()
    flask_app.run(host="0.0.0.0", port=PORT)
