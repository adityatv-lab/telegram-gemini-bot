import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Make sure to set your environment variables in Render
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

# ---- Your Bot's Functions ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! I am your Gemini-powered assistant. Send me a message, and I will do my best to help you."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles regular text messages and gets a response from Gemini."""
    user_message = update.message.text
    
    try:
        # Send the user's message to the Gemini model
        response = model.generate_content(user_message)
        
        # Reply to the user with the model's response
        await update.message.reply_text(response.text)
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await update.message.reply_text("Sorry, I encountered an error while processing your request.")

# ---- Main Section to Run the Bot ----

def main() -> None:
    """Start the bot."""
    logging.info("Starting bot...")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers for different commands and messages
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    # The bot will run until you press Ctrl-C or the process receives a signal to stop.
    application.run_polling()

if __name__ == '__main__':
    main()
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    flask_app.run(host="0.0.0.0", port=PORT)
