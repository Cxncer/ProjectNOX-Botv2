import logging
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import os
from dotenv import load_dotenv
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variable
TOKEN = os.getenv('TOKEN')

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

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Tos Book! Please enter the Client Name:")
    return CLIENT_NAME

async def restart(update: Update, context: CallbackContext):
    await update.message.reply_text("Restarting the booking process. Please enter the Client Name:")
    return CLIENT_NAME

async def client_name(update: Update, context: CallbackContext):
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

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Booking cancelled.")
    return ConversationHandler.END

async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)],
            PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, people)],
            TOTAL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, total_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('restart', restart)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_handler(CommandHandler('restart', restart))

    TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    response = requests.post(TELEGRAM_API_URL, data={"url": webhook_url})
    print(response.json())

    webhook_url = f"https://noxtelegrambot-rdhwj.ondigitalocean.app/webhook"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

if __name__ == '__main__':
    asyncio.run(main())
