import logging
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import os
from dotenv import load_dotenv
import asyncio
from telegram.error import RetryAfter, TelegramError
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variable
TOKEN = os.getenv('TOKEN')
logger.info(f"TOKEN loaded: {TOKEN}")

# Ensure the token is set
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# Channel username or chat ID to send the summary to
TARGET_CHANNEL = '@projectnox_booking'  # Replace this with your channel's username or chat ID

# Define states for the conversation
CLIENT_NAME, CONTACT, TYPE, DATE, TIME, PEOPLE, TOTAL_PRICE = range(7)

# Initialize FastAPI app
app = FastAPI()

class WebhookRequest(BaseModel):
    update_id: int
    message: dict

@app.post('/webhook')
async def process_webhook(update: WebhookRequest):
    await application.update_queue.put(Update.de_json(update.dict(), application.bot))
    return "OK"

# Define the command handlers
async def tos(update: Update, context: CallbackContext):
    logger.info(f"TOS command received from: {update.message.chat_id}")
    await update.message.reply_text("Welcome to the Booking bot! Please enter the Client Name:")
    return CLIENT_NAME

async def restart(update: Update, context: CallbackContext):
    await update.message.reply_text("Restarting the booking process. Please enter the Client Name:")
    return CLIENT_NAME

async def bach(update: Update, context: CallbackContext):
    await update.message.reply_text("Booking cancelled.")
    return ConversationHandler.END

# Define the message handlers for the conversation states
async def client_name(update: Update, context: CallbackContext):
    logger.info(f"Client name received: {update.message.text}")
    context.user_data['client_name'] = update.message.text
    await update.message.reply_text("Got it! Now, please enter the Contact:")
    return CONTACT

async def contact(update: Update, context: CallbackContext):
    context.user_data['contact'] = update.message.text
    await update.message.reply_text("Please enter the Type:")
    return TYPE

async def type_(update: Update, context: CallbackContext):
    context.user_data['type'] = update.message.text
    await update.message.reply_text("Please enter the Date (dd/mm/yyyy):")
    return DATE

async def date(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Please enter the Time:")
    return TIME

async def time(update: Update, context: CallbackContext):
    context.user_data['time'] = update.message.text
    await update.message.reply_text("Please enter the number of People:")
    return PEOPLE

async def people(update: Update, context: CallbackContext):
    context.user_data['people'] = update.message.text
    await update.message.reply_text("Finally, please enter the Total Price:")
    return TOTAL_PRICE

async def total_price(update: Update, context: CallbackContext):
    context.user_data['total_price'] = update.message.text

    summary = (
        f"Client Name: {context.user_data['client_name']}\n"
        f"Contact: {context.user_data['contact']}\n"
        f"Type: {context.user_data['type']}\n"
        f"Date: {context.user_data['date']}\n"
        f"Time: {context.user_data['time']}\n"
        f"People: {context.user_data['people']}\n"
        f"Total Price: {context.user_data['total_price']}"
    )

    await context.bot.send_message(chat_id=TARGET_CHANNEL, text=summary)
    await update.message.reply_text("Booking created successfully!")
    return ConversationHandler.END

async def set_webhook_with_retry(webhook_url):
    """Sets the webhook with exponential backoff retries."""
    delay = 1  # Initial delay of 1 second
    max_retries = 5  # Maximum number of retries

    for attempt in range(max_retries):
        try:
            # Set the webhook with Telegram
            TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
            response = requests.post(TELEGRAM_API_URL, data={"url": webhook_url})
            response.raise_for_status()
            logger.info(f"Webhook set via Telegram API: {response.json()}")
            return True  # Webhook successfully set
        except RetryAfter as e:
            logger.warning(f"Rate limit exceeded. Retrying in {e.retry_after} seconds.")
            await asyncio.sleep(e.retry_after)  # Wait for the retry_after time specified by Telegram
        except TelegramError as e:
            logger.error(f"TelegramError occurred: {e}")
            return False  # Fail if Telegram returns an error other than rate-limiting
        except requests.RequestException as e:
            logger.error(f"Request error: {e}. Retrying in {delay} seconds.")
        except Exception as e:
            logger.error(f"An error occurred: {e}. Retrying in {delay} seconds.")

        await asyncio.sleep(delay)  # Exponential backoff delay
        delay *= 2  # Double the delay with each retry

    logger.error("Max retries exceeded. Failed to set the webhook.")
    return False

async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    # Initialize the application
    await application.initialize()

    # Set the webhook URL
    webhook_url = "https://128.199.148.109/webhook"  # Replace with your actual webhook URL

    # Attempt to set the webhook with retry mechanism
    if not await set_webhook_with_retry(webhook_url):
        logger.error("Failed to set the webhook after maximum retries. Exiting.")
        return

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('tos', tos)],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)],
            PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, people)],
            TOTAL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, total_price)],
        },
        fallbacks=[CommandHandler('bach', bach), CommandHandler('restart', restart)],
        allow_reentry=True
    )

    # Add the conversation handler to the application
    application.add_handler(conv_handler)

    # Start the bot
    await application.start()

    # Idle to keep the bot running
    await application.idle()

# Run the bot with asyncio
if __name__ == '__main__':
    asyncio.run(main())
