import sqlite3
import os
import html
from telegram import Update, ChatMember
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from threading import Thread
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

# Define a function for each thread to use


def thread_function(update, user_id, username, skill):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Use the cursor object to execute some SQL statements
    c.execute(
        'CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skills (user_id INTEGER, skill TEXT, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id))')
    c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
              (user_id, username))

    # Check if the user has already added 3 skills in the last 24 hours
    c.execute('SELECT COUNT(*) FROM skills WHERE user_id = ? AND date_added > ?',
              (user_id, datetime.now() - timedelta(hours=24)))
    skill_count = c.fetchone()[0]

    if skill_count < 3:
        c.execute('INSERT INTO skills (user_id, skill) VALUES (?, ?)',
                  (user_id, skill))
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        update.message.reply_text(
            f"Shill '{skill}' added for {username} ({user_id})")
    else:
        conn.close()
        update.message.reply_text(
            "You have already added the maximum limit of 3 shills in the last 24 hours.")


# Define the function for handling the /add_skill command
def add_skill(update: Update, context: CallbackContext):
    # Get the user ID, username, and skill from the command arguments
    user_id = update.effective_user.id
    username = update.effective_user.username
    message = update.message.text

    if message.startswith('/save_shill') or message.startswith('/save_shill@crypto_clown_bot'):
        # Exclude the command itself from being saved as a skill
        command = message.split()[0]
        message = message[len(command):].strip()

        # Check if the message is a reply
        if update.message.reply_to_message:
            # Check if the user is a chat admin or the same user who sent the original message
            chat_id = update.effective_chat.id
            message_caller_id = update.effective_user.id
            user_id = update.message.reply_to_message.from_user.id
            username = update.message.reply_to_message.from_user.username
            chat_member = context.bot.get_chat_member(
                chat_id, message_caller_id)

            if (chat_member.status == ChatMember.ADMINISTRATOR or
                    chat_member.status == ChatMember.CREATOR or
                    message_caller_id == user_id):

                # Check if the skill message exceeds the character limit (e.g., 100 characters)
                character_limit = 100
                if len(update.message.reply_to_message.text) > character_limit:
                    update.message.reply_text(
                        f"The skill message exceeds the character limit of {character_limit} characters.")
                else:
                    # Start a new thread to handle the database update
                    thread = Thread(target=thread_function,
                                    args=(update, user_id, username, update.message.reply_to_message.text))
                    thread.start()
            else:
                # If the user is not a chat admin or the original message sender, send an error message
                update.message.reply_text(
                    "Only chat admins can save other users' shills.")
        else:
            # Check if the skill message exceeds the character limit (e.g., 100 characters)
            character_limit = 100
            if len(message) > character_limit:
                update.message.reply_text(
                    f"The skill message exceeds the character limit of {character_limit} characters.")
            else:
                # Start a new thread to handle the database update
                thread = Thread(target=thread_function,
                                args=(update, user_id, username, message))
                thread.start()


def list_skills(update: Update, context: CallbackContext):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Get the datetime 24 hours ago
    datetime_24h_ago = datetime.now() - timedelta(hours=24)

    # Get all the users and their skills added in the last 24 hours from the database
    c.execute(
        'SELECT users.username, skills.skill FROM users JOIN skills ON users.user_id = skills.user_id WHERE skills.date_added > ?',
        (datetime_24h_ago,))
    skills = c.fetchall()

    # Create a formatted list of skills with monospace usernames
    skill_list = '\n'.join(
        [f'<code>{html.escape(username)}</code>: {skill}' for (username, skill) in skills])

    # Close the connection
    conn.close()

    # Send the skill list as a message with monospace usernames
    update.message.reply_html(
        f"<b>Latest SHILLS in the last 24 hours:</b>\n{skill_list}")


# Create the bot and add the command handlers
updater = Updater(bot_token)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('save_shill', add_skill))
dispatcher.add_handler(CommandHandler('shill_list', list_skills))
dispatcher.add_handler(MessageHandler(Filters.text, add_skill))

# Start the bot
print("Bot started...")
try:
    updater.start_polling()
    updater.idle()
except Exception as e:
    print("An exception occurred:", str(e))
