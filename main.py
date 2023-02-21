import sqlite3
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Connect to the SQLite database
conn = sqlite3.connect('users.db')
cur = conn.cursor()

# Create a 'users' table if it doesn't exist
cur.execute('''CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY,
               first_name TEXT NOT NULL,
               last_name TEXT NOT NULL,
               user_id INTEGER NOT NULL UNIQUE,
               chat_id INTEGER NOT NULL
             )''')

# Initialize the Telegram bot
bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = Bot(token=bot_token)

# Start the webhook server
updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

# Define the /start command handler
def start_handler(update, context):
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Insert user into 'users' table
    cur.execute('INSERT OR IGNORE INTO users (first_name, last_name, user_id, chat_id) VALUES (?, ?, ?, ?)',
                (first_name, last_name, user_id, chat_id))
    conn.commit()

    context.bot.send_message(chat_id=chat_id, text=f"Welcome, {first_name}!")

# Define the message handler for authentication
def authenticate_handler(update, context):
    user_id = update.message.from_user.id

    # Find user in 'users' table
    cur.execute('SELECT first_name, last_name FROM users WHERE user_id = ?', (user_id,))
    result = cur.fetchone()

    if result:
        first_name, last_name = result
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Authenticated as {first_name} {last_name}.")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Unauthorized.")

# Add command and message handlers to dispatcher
start_handler = CommandHandler('start', start_handler)
authenticate_handler = MessageHandler(Filters.text('/authenticate'), authenticate_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(authenticate_handler)

# Start the webhook server
updater.start_webhook(listen='0.0.0.0', port=5000, url_path=bot_token)
updater.bot.setWebhook(url='https://YOUR_HOST/YOUR_WEBHOOK_PATH/' + bot_token)

# Start the bot
updater.idle()

# Close the database connection
conn.close()
