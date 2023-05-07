import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from threading import Thread

# Define a function for each thread to use


def thread_function(user_id, username, skill):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Use the cursor object to execute some SQL statements
    c.execute(
        'CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skills (user_id INTEGER, skill TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))')
    c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
              (user_id, username))
    c.execute('INSERT INTO skills (user_id, skill) VALUES (?, ?)',
              (user_id, skill))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Define the function for handling the /addskill command


def add_skill(update: Update, context: CallbackContext):
    # Get the user ID, username, and skill from the command arguments
    user_id = update.effective_user.id
    username = update.effective_user.username
    skill = context.args[0]

    # Start a new thread to handle the database update
    thread = Thread(target=thread_function, args=(user_id, username, skill))
    thread.start()

    # Send a confirmation message
    update.message.reply_text(
        f"Skill '{skill}' added for {username} ({user_id})")

# Define the function for handling the /listskills command


def list_skills(update: Update, context: CallbackContext):
    # Create a new connection and cursor object for this thread
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Get all the users and their skills from the database
    c.execute(
        'SELECT users.username, skills.skill FROM users JOIN skills ON users.user_id = skills.user_id')
    skills = c.fetchall()

    # Create a formatted list of skills
    skill_list = '\n'.join(
        [f'{username}: {skill}' for (username, skill) in skills])

    # Close the connection
    conn.close()

    # Send the skill list as a message
    update.message.reply_text(f"Current skills:\n{skill_list}")


# Create the bot and add the command handlers
updater = Updater('6002292363:AAHftRSdNeXZ-BB4KAtvGwagRGlpR1n7JaU')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('add_skill', add_skill))
dispatcher.add_handler(CommandHandler('list_skills', list_skills))

# Start the bot
updater.start_polling()
updater.idle()
