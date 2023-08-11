import sqlite3
import os
import html
from telegram import Update, ChatMember
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from threading import Thread
from datetime import datetime, timedelta
from dateutil.parser import parse
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')


# Define a function for each thread to use

def thread_function(update, user_id, username, skill, message_reference):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Use the cursor object to execute some SQL statements
    c.execute(
        'CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skills (user_id INTEGER, skill TEXT, message_reference TEXT, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id))')
    c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
              (user_id, username))

    # Check if the user has already added 3 skills in the last 24 hours
    c.execute('SELECT COUNT(*) FROM skills WHERE user_id = ? AND date_added > ?',
              (user_id, datetime.utcnow() - timedelta(hours=24)))
    skill_count = c.fetchone()[0]

    if skill_count < 5:
        # Check if the message reference already exists in the database
        c.execute(
            'SELECT COUNT(*) FROM skills WHERE message_reference = ?', (message_reference,))
        reference_count = c.fetchone()[0]

        if reference_count > 0:
            conn.close()
            update.message.reply_text(
                "The same shill has already been added before.")
        else:
            c.execute('INSERT INTO skills (user_id, skill, message_reference) VALUES (?, ?, ?)',
                      (user_id, skill, message_reference))
            # Commit the changes and close the connection
            conn.commit()
            conn.close()
            update.message.reply_text(
                f"Shill '{skill}' added for {username} ({user_id})")
    else:
        conn.close()
        update.message.reply_text(
            "You have already added the maximum limit of 5 shills in the last 24 hours 🤡")


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

                if not update.message.reply_to_message.text:
                    update.message.reply_text("The shill message is empty 🤡")
                    return
                else:
                    # Start a new thread to handle the database update
                    thread = Thread(target=thread_function,
                                    args=(update, user_id, username, update.message.reply_to_message.text, update.message.reply_to_message.link))
                    thread.start()
            else:
                # If the user is not a chat admin or the original message sender, send an error message
                update.message.reply_text(
                    "Only chat jannies can save other users shills 🤡")
        else:

            # Check if the message is empty
            if not message:
                update.message.reply_text("The shill message is empty 🤡")
                return

            else:
                # Start a new thread to handle the database update
                thread = Thread(target=thread_function,
                                args=(update, user_id, username, message, update.message.link))
                thread.start()

# ...

def list_skills(update: Update, context: CallbackContext):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Get the current datetime
    now = datetime.utcnow()

    # Get all the users and their skills added in the last 24 hours from the database
    c.execute(
        'SELECT users.username, users.user_id, skills.skill, skills.message_reference, skills.date_added FROM users JOIN skills ON users.user_id = skills.user_id WHERE skills.date_added > ?',
        (now - timedelta(hours=24),))
    skills = c.fetchall()

    # Sort the skills based on the time elapsed in ascending order
    skills.sort(key=lambda x: now - parse(x[4]))

    # Create a dictionary to store the shills for each user
    shills_by_user = {}

    # Group the shills by user
    for username, user_id, skill, message_reference, date_added in skills:
        if username or user_id:
            if not username:
                username = user_id
            if username not in shills_by_user:
                shills_by_user[username] = []
            shills_by_user[username].append(
                (message_reference, parse(date_added)))

    # Create a formatted list of shills with sorted usernames and message references
    skill_list = ''
    previous_elapsed_hours = None

    for username in shills_by_user:
        shills_by_user[username].sort(key=lambda x: now - x[1])
        elapsed_hours = (now - shills_by_user[username][0][1]).seconds // 3600
        print("now", now)
        print("saved", shills_by_user[username][0][1])
        
        if elapsed_hours < 1:
            elapsed_hours = "&lt 1"

        if elapsed_hours != previous_elapsed_hours:
            skill_list += f"\n<b>{elapsed_hours} {'hour' if elapsed_hours == 1 else 'hours'} ago:</b>\n"

        skill_list += f"{username}: " + ', '.join(['<a href=\'' + ref[0] + '\'>' + ref[0].split(
            "/")[-1] + '</a>' for ref in shills_by_user[username]]) + '\n'
        previous_elapsed_hours = elapsed_hours

    # Close the connection
    conn.close()

    # Send the shill list as a message with sorted usernames and message references
    update.message.reply_html(
        f"🤡<b>Latest Shills in the last 24 hours:</b>{skill_list}")



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
