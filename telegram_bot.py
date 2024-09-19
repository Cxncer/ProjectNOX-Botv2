import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters
from telegram.ext import CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv('TOKEN')

# Conversation states
CLIENT_NAME, CONTACT, SESSION_TYPE, DATE, TIME, PEOPLE, TOTAL_PRICE = range(7)

# Start command
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Welcome! Let's start your order. What is your name?"
    )
    return CLIENT_NAME

# Handlers for each step
async def client_name(update: Update, context: CallbackContext) -> int:
    context.user_data['client_name'] = update.message.text
    await update.message.reply_text("Got it! What's your contact information?")
    return CONTACT

async def contact(update: Update, context: CallbackContext) -> int:
    context.user_data['contact'] = update.message.text
    await update.message.reply_text("What type of session would you like to book?")
    return SESSION_TYPE

async def session_type(update: Update, context: CallbackContext) -> int:
    context.user_data['session_type'] = update.message.text
    await update.message.reply_text("Please provide the date of the session (dd/mm/yyyy).")
    return DATE

async def date(update: Update, context: CallbackContext) -> int:
    context.user_data['date'] = update.message.text
    await update.message.reply_text("What time would you like to book (HH:MM)?")
    return TIME

async def time(update: Update, context: CallbackContext) -> int:
    context.user_data['time'] = update.message.text
    await update.message.reply_text("How many people will be attending?")
    return PEOPLE

async def people(update: Update, context: CallbackContext) -> int:
    try:
        people = int(update.message.text)
        if people <= 0:
            raise ValueError
        context.user_data['people'] = people
        await update.message.reply_text("Finally, what's the total price for the session?")
        return TOTAL_PRICE
    except ValueError:
        await update.message.reply_text("Please enter a valid number of people.")
        return PEOPLE

async def total_price(update: Update, context: CallbackContext) -> int:
    try:
        price = float(update.message.text)
        if price <= 0:
            raise ValueError
        context.user_data['total_price'] = price
        
        # Summary of the order
        summary = (
            f"Order Summary:\n"
            f"Client Name: {context.user_data['client_name']}\n"
            f"Contact: {context.user_data['contact']}\n"
            f"Session Type: {context.user_data['session_type']}\n"
            f"Date: {context.user_data['date']}\n"
            f"Time: {context.user_data['time']}\n"
            f"Number of People: {context.user_data['people']}\n"
            f"Total Price: {context.user_data['total_price']}\n"
        )
        await update.message.reply_text(summary)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid price.")
        return TOTAL_PRICE

# Cancel the order
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Order has been canceled. You can start a new one anytime with /start.")
    return ConversationHandler.END

# Restart the order
async def restart(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Let's restart your order. What is your name?")
    return CLIENT_NAME

# Fallback handler for unrecognized input
async def fallback(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("I didn't understand that. Use /start to begin or /cancel to stop.")
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    # Define the conversation handler steps
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            SESSION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, session_type)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time)],
            PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, people)],
            TOTAL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, total_price)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('restart', restart)]
    )

    # Add handlers
    application.add_handler(conv_handler)

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
