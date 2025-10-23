# Telegram Bot with Google Gemini AI

## Overview
This is a Telegram chatbot that uses Google's Gemini AI to respond to messages in a personalized, conversational style. The bot is configured to respond as "Adi," a witty, confident Gen-Z personality from Bangalore.

## Project Structure
```
.
├── bot.py              # Main bot application
├── pyproject.toml      # Python dependencies
├── .gitignore         # Git ignore file (prevents sensitive data commits)
└── replit.md          # This documentation file
```

## Technologies Used
- **Python 3.12** - Programming language
- **python-telegram-bot** - Telegram Bot API wrapper
- **google-generativeai** - Google Gemini AI integration
- **google-auth** - Google authentication

## Configuration

### Environment Variables (Secrets)
The bot requires two environment secrets to function:

1. **TELEGRAM_BOT_TOKEN** - Your Telegram bot token from BotFather
2. **GOOGLE_SERVICE_ACCOUNT_JSON** - Your Google Cloud service account credentials (JSON format)

These are configured in Replit Secrets and automatically loaded as environment variables.

### Security
- All sensitive credentials are stored as environment variables
- The `.gitignore` file prevents accidental commits of sensitive data
- No hardcoded API keys or tokens in the codebase

## How It Works
1. The bot connects to Telegram using the provided bot token
2. When a user sends a message, it forwards the text to Google Gemini AI
3. Gemini generates a response based on the configured personality prompt
4. The bot sends the AI-generated response back to the user

## Running the Bot
The bot is configured to run automatically via the "Telegram Bot" workflow. It runs continuously and listens for incoming messages.

To manually start the bot:
```bash
python bot.py
```

## Recent Changes (October 23, 2025)
- Migrated from hardcoded credentials to environment variables for security
- Fixed package dependencies (removed conflicting telegram package)
- Added .gitignore to prevent sensitive file commits
- Configured Replit workflow for continuous operation
- Documented project setup and configuration

## User Preferences
- Security-focused: Always use environment variables for credentials
- Clean code structure with proper error handling
- Conversational AI personality customization
