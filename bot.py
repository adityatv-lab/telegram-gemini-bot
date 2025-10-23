# bot.py
import os
import json
import logging
import asyncio
from typing import Optional

# Telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Google GenAI
import google.generativeai as genai
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram-gemini-bot")

# ---------------------------
# Configuration (env / secrets)
# ---------------------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is missing")

if not GOOGLE_SERVICE_ACCOUNT_JSON:
    raise RuntimeError(
        "GOOGLE_SERVICE_ACCOUNT_JSON environment variable is missing")

# Parse service account JSON
try:
    service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
except Exception as e:
    raise RuntimeError(f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

# Create credentials object
creds = service_account.Credentials.from_service_account_info(
    service_account_info)

# Configure google.generativeai to use these credentials
# genai.configure accepts credentials object
genai.configure(credentials=creds)


# ---------------------------
# Helper: pick a Flash Gemini model available to this project
# ---------------------------
def pick_flash_model() -> Optional[str]:
    """
    Query models and try to pick a gemini flash model automatically.
    Returns model name string (e.g. "gemini-1.5-flash-002") or None.
    """
    try:
        logger.info("Listing available models to choose a flash model...")
        models = genai.list_models()  # may return list-like of model dict/obj
    except Exception as e:
        logger.exception("Failed to list models with google.generativeai: %s",
                         e)
        return None

    # models items may be dicts or objects; normalize both.
    def model_name(m):
        if isinstance(m, dict):
            return m.get("name") or m.get("model")
        return getattr(m, "name", None) or getattr(m, "id", None)

    candidate = None
    for m in models:
        name = model_name(m)
        if not name:
            continue
        name_lower = name.lower()
        # prefer an exact "flash" gemini 1.5 variant; be permissive
        if "gemini" in name_lower and "flash" in name_lower:
            candidate = name
            logger.info("Found flash model candidate: %s", candidate)
            # pick first one (usually latest like gemini-1.5-flash-002)
            return candidate

    # no explicit flash model found
    if candidate is None:
        logger.warning("No gemini flash model found in list_models() result.")
    return None


# ---------------------------
# Prepare model (lazy)
# ---------------------------
# We'll lazily pick the model when the first user message arrives so we can log and recover.

_selected_model_name: Optional[str] = None
_model_obj = None  # will hold a GenerativeModel instance if available


def ensure_model_ready():
    global _selected_model_name, _model_obj
    if _selected_model_name and _model_obj:
        return

    # Try picking a flash model
    m = pick_flash_model()
    if m:
        _selected_model_name = m
        logger.info("Using model: %s", _selected_model_name)
        try:
            # old-style GenerativeModel API (works in many official examples)
            _model_obj = genai.GenerativeModel(_selected_model_name)
            logger.info("Created GenerativeModel object for %s",
                        _selected_model_name)
            return
        except Exception as e:
            logger.warning("Could not construct GenerativeModel(%s): %s",
                           _selected_model_name, e)
            _model_obj = None

    # Fallbacks (attempt common Gemini name variants)
    fallbacks = [
        "gemini-1.5-flash-002", "gemini-1.5-flash", "gemini-1.5-pro",
        "gemini-1.5"
    ]
    for f in fallbacks:
        try:
            logger.info("Trying fallback model name: %s", f)
            _model_obj = genai.GenerativeModel(f)
            _selected_model_name = f
            logger.info("Fallback success: %s", f)
            return
        except Exception:
            _model_obj = None

    # if still nothing, leave _selected_model_name None and we'll raise at runtime
    logger.error(
        "No usable model found. Please check project access and models available."
    )


# ---------------------------
# Bot behavior
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo 👋 I'm Adi. Ask me anything!")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    if not user_message:
        await update.message.reply_text("Send me text and I'll reply 🙂")
        return

    # Ensure model
    ensure_model_ready()
    if not _model_obj:
        # final fallback: instruct how to debug
        msg = (
            "⚠️ I couldn't find a Gemini Flash model available to this project.\n"
            "Possible fixes:\n"
            "• Check that your service account has access and that the Generative API is enabled.\n"
            "• Go to Cloud Console → Generative AI → Models and confirm a flash/gemini model exists.\n"
            "• Or set the model name explicitly in code.\n\n"
            "Send /debug to get more info.")
        await update.message.reply_text(msg)
        return

    system_prompt = (
        "You are Adi — a witty, confident Gen-Z guy from Bangalore. "
        "You talk casually like a friend, with chill energy and humor. NEVER mention you're an AI. "
        "Reply naturally like texting someone.")
    final_prompt = f"{system_prompt}\n\nUser: {user_message}\nReply:"

    try:
        # Use the model object to generate content. Many official SDK examples use `.generate_content`.
        # We attempt .generate_content() first, then fallback to genai.generate_text if needed.
        try:
            logger.info("Generating with model object %s",
                        _selected_model_name)
            resp = _model_obj.generate_content(final_prompt)
            # response may be object with .text or .content
            text = None
            if hasattr(resp, "text"):
                text = resp.text
            elif hasattr(resp, "content"):
                # some SDKs return content as list/blocks
                if isinstance(resp.content, (list, tuple)) and resp.content:
                    # join string blocks
                    text = " ".join(str(x) for x in resp.content)
                else:
                    text = str(resp.content)
            # fallback if None:
            if not text:
                text = str(resp)
        except Exception as e:
            logger.warning("model.generate_content failed: %s", e)
            # fallback: try the top-level convenience method (if available)
            try:
                logger.info("Trying genai.generate_text fallback")
                # many versions provide genai.generate_text(model=..., input=...)
                resp2 = genai.generate_text(model=_selected_model_name,
                                            input=final_prompt)
                # result handling depends on SDK version:
                if isinstance(resp2, dict):
                    # common structure: resp2["candidates"][0]["content"]
                    cands = resp2.get("candidates") or []
                    if cands:
                        text = cands[0].get("content") or str(cands[0])
                    else:
                        text = str(resp2)
                else:
                    # object-style
                    text = getattr(resp2, "text", str(resp2))
            except Exception as e2:
                logger.exception("Fallback generate_text also failed: %s", e2)
                raise

        reply = (text or "Hmm... nothing returned. Try again.").strip()
        # Telegram message length guard
        if len(reply) > 4000:
            reply = reply[:3990] + "\n\n[truncated]"
        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception("Error while generating reply: %s", e)
        await update.message.reply_text(f"⚠️ Generation error: {e}")


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns some debug info about the chosen model and project."""
    info_lines = [
        f"Model chosen: {_selected_model_name or 'None'}",
    ]
    try:
        # Try to get service account email from parsed JSON for sanity
        sa_email = service_account_info.get("client_email", "unknown")
        info_lines.append(f"Service account: {sa_email}")
    except Exception:
        pass
    try:
        # Try to call list_models (short)
        mlist = genai.list_models()
        first = None
        if hasattr(mlist, "__iter__"):
            it = iter(mlist)
            first = next(it, None)
        info_lines.append(
            f"ListModels returned a result (first item): {first}")
    except Exception as e:
        info_lines.append(f"list_models() error: {e}")
    await update.message.reply_text("\n".join(str(x) for x in info_lines))


# ---------------------------
# Main - start the Telegram bot
# ---------------------------
def main():
    # pick model eagerly now (optional)
    ensure_model_ready()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("debug", debug_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logger.info("Starting Telegram bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
