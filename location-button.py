from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

TOKEN = '7366095687:AAEtaLEmSlXK6nHn2Fj1t1zYHzRUfG5Mze8'  # Replace this with your bot token from BotFather

def start(update: Update, context: CallbackContext):
    # Create a button that asks for the user's location
    location_button = KeyboardButton(text="Share Location", request_location=True)
    keyboard = [[location_button]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text("Please share your location:", reply_markup=reply_markup)

def handle_location(update: Update, context: CallbackContext):
    # Extract user's location
    user_location = update.message.location
    latitude = user_location.latitude
    longitude = user_location.longitude
    
    # Send location to the FastAPI backend
    # You need to replace the URL with your FastAPI endpoint
    response = requests.post('https://3aa3-196-1-114-254.ngrok-free.app /webhook', json={'latitude': latitude, 'longitude': longitude})
    
    # Send the response from FastAPI back to the user
    update.message.reply_text(f"Here are the nearby places: {response.json()}")

def main():
    # Set up the Updater and Dispatcher
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Register handlers for start command and location sharing
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.location, handle_location))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
