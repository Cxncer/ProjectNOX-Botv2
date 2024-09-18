import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import os
from dotenv import load_dotenv
import asyncio
from telegram.error import RetryAfter, TelegramError
import requests

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

async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    # Initialize the application
    await application.initialize()

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

    # Keep the bot running
    try:
        await application.updater.start_polling()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Ensure the application is stopped when done
        await application.stop()

# Run the bot with asyncio
if __name__ == '__main__':
    asyncio.run(main())
