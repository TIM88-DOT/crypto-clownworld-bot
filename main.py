import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from threading import Thread
from datetime import datetime, timedelta


# Define a function for each thread to use
def thread_function(user_id, username, skill):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Use the cursor object to execute some SQL statements
    c.execute(
        'CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skills (user_id INTEGER, skill TEXT, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id))')
    c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
              (user_id, username))
    c.execute('INSERT INTO skills (user_id, skill) VALUES (?, ?)',
              (user_id, skill))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def add_skill(update: Update, context: CallbackContext):
    # Check if the message is a reply and save the skill from the replied message
    if update.message.reply_to_message:
        user_id = update.effective_user.id
        username = update.effective_user.username
        message = update.message.reply_to_message.text or update.message.reply_to_message.caption

        # Start a new thread to handle the database update
        thread = Thread(target=thread_function,
                        args=(user_id, username, message))
        thread.start()

        # Send a confirmation message
        update.message.reply_text(
            f"Skill '{message}' added for {username} ({user_id})")
    else:
        # Check if the message is in a group
        if update.message.chat.type == "group" or update.message.chat.type == "supergroup":
            # Get the user ID, username, and skill from the message text
            user_id = update.effective_user.id
            username = update.effective_user.username
            message = update.message.text

            # Exclude the command itself from being saved as a skill
            if message.startswith('/save_shill'):
                message = message[len('/save_shill'):].strip()

            # Start a new thread to handle the database update
            thread = Thread(target=thread_function,
                            args=(user_id, username, message))
            thread.start()

            # Send a confirmation message
            update.message.reply_text(
                f"Skill '{message}' added for {username} ({user_id})")
        else:
            # If the message is not a reply and not in a group, handle it as before
            user_id = update.effective_user.id
            username = update.effective_user.username
            message = update.message.text

            # Start a new thread to handle the database update
            thread = Thread(target=thread_function,
                            args=(user_id, username, message))
            thread.start()

            # Send a confirmation message
            update.message.reply_text(
                f"Skill '{message}' added for {username} ({user_id})")


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

    # Create a formatted list of skills
    skill_list = '\n'.join(
        [f'{username}: {skill}' for (username, skill) in skills])

    # Close the connection
    conn.close()

    # Send the skill list as a message
    update.message.reply_text(f"Latest shills added in the last 24 hours:\n{skill_list}")



# Create the bot and add the command handlers
updater = Updater('6002292363:AAHftRSdNeXZ-BB4KAtvGwagRGlpR1n7JaU')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('save_shill', add_skill))
dispatcher.add_handler(CommandHandler('shill_list', list_skills))
dispatcher.add_handler(MessageHandler(Filters.text, add_skill))

# Start the bot
updater.start_polling()
updater.idle()
