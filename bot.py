# bot.py
import os
import logging
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}"

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise RuntimeError("Missing TELEGRAM_TOKEN or GEMINI_API_KEY in environment")

# Configure Gemini (Google GenAI SDK)
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TELEGRAM_SEND_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def send_telegram(chat_id: int, text: str):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    r = requests.post(TELEGRAM_SEND_URL, json=payload, timeout=15)
    logging.info("Telegram sendMessage status: %s %s", r.status_code, r.text)
    return r

@app.route("/")
def root():
    return "Telegram Gemini webhook up"

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    logging.info("Received update: %s", data)

    # minimal validation and handling text messages
    message = data.get("message") or data.get("edited_message")
    if not message:
        return jsonify({"status":"ok"})

    chat_id = message["chat"]["id"]
    user_text = message.get("text", "")
    if not user_text:
        send_telegram(chat_id, "Sorry, I only handle text messages for now.")
        return jsonify({"status":"ok"})

    try:
        # Call Gemini to generate a reply
        # Use the simple text generation call. Adjust model name if needed.
        # NOTE: this uses google.generativeai SDK methods. If your SDK version differs,
        # consult the SDK docs — this is the typical pattern.
        response = genai.generate_text(model="gemini-1.5-flash", prompt=user_text, max_output_tokens=512)
        reply = response.text if hasattr(response, "text") else str(response)
        if not reply:
            reply = "I couldn't make a reply — try again later."
    except Exception as e:
        logging.exception("Gemini error")
        reply = "Sorry, Gemini returned an error."

    send_telegram(chat_id, reply)
    return jsonify({"status":"ok"})
