import sqlite3
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time

# Create a new SQLite database
conn = sqlite3.connect('shills.db')
c = conn.cursor()

# Create a table to store shills
c.execute('''CREATE TABLE IF NOT EXISTS shills
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              shill TEXT,
              user_id INTEGER,
              chat_id INTEGER)''')

# Define a function to check if a user is an admin
def is_admin(update):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    
    return user_id == context.bot.get_chat_administrators(chat_id)[0].user.id

# Define a function to handle the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Hi there! Send me a shill to save it to the database.')

# Define a function to handle text messages
def save_shill(update, context):
    shill = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    
    # Check if the shill is being saved for another user
    if len(context.args) > 0:
        # Get the user ID for the target user
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Invalid user ID.')
            return
        
        # Check if the user is an admin or the shill is being saved for the user who posted it
        if is_admin(update) or user_id == target_user_id:
            # Insert the shill into the database with the target user ID
            c.execute('INSERT INTO shills (shill, user_id, chat_id) VALUES (?, ?, ?)', (shill, target_user_id, chat_id))
            conn.commit()
            
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Shill "{shill}" has been saved for user {target_user_id}.')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='You do not have permission to save a shill for another user.')
    else:
        # Insert the shill into the database with the user ID of the person who posted it
        c.execute('INSERT INTO shills (shill, user_id, chat_id) VALUES (?, ?, ?)', (shill, user_id, chat_id))
        conn.commit()
        
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Shill "{shill}" has been saved to the database.')

# Define a function to handle the /list_shills command
def list_shills(update, context):
    chat_id = update.message.chat.id
    
    # Get all the shills for the current chat
    c.execute('SELECT user_id, shill FROM shills WHERE chat_id=?', (chat_id,))
    shills = c.fetchall()
    
    if shills:
        # Group the shills by user ID
        shills_by_user = {}
        for shill in shills:
            user_id = shill[0]
            shill_text = shill[1]
            if user_id not in shills_by_user:
                shills_by_user[user_id] = []
            shills_by_user[user_id].append(shill_text)
        
        # Create a string of all the shills, grouped by user
        shills_str = ''
        for user_id, shills in shills_by_user.items():
            shills_str += f'Shills for user {user_id}:\n'
            shills_str += '\n'.join(shills)
            shills_str += '\n\n'
        
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=shills_str,
                                 parse_mode=ParseMode.HTML)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='No shills found.')


# Define a function to handle the /get_shills command
def get_user_shills(update, context):
    chat_id = update.message.chat.id
    
    # Get the user ID for the target user
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Invalid user ID.')
        return
    
    # Get all the shills for the target user in the current chat
    c.execute('SELECT shill FROM shills WHERE user_id=? AND chat_id=?', (target_user_id, chat_id))
    shills = c.fetchall()
    
    if shills:
        # Join the shills into a string
        shills_str = '\n'.join([shill[0] for shill in shills])
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Shills for user {target_user_id}:\n{shills_str}',
                                 parse_mode=ParseMode.HTML)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'No shills found for user {target_user_id}.')
        
        
# Define a function to handle the /latest_shills command
def latest_shills(update, context):
    chat_id = update.message.chat.id
    now = int(time.time())
    last_24h = now - 24 * 60 * 60
    
    # Get the latest shills in the past 24 hours for the current chat
    c.execute('SELECT shills.user_id, shills.shill, users.username FROM shills INNER JOIN users ON shills.user_id=users.user_id WHERE shills.chat_id=? AND shills.timestamp > ? ORDER BY shills.timestamp DESC', (chat_id, last_24h))
    shills = c.fetchall()
    
    if shills:
        # Create a string of the latest shills with usernames
        shills_str = ''
        for shill in shills:
            user_id = shill[0]
            shill_text = shill[1]
            username = shill[2]
            shills_str += f'<b>@{username}</b>: {shill_text}\n'
        
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=shills_str,
                                 parse_mode=ParseMode.HTML)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='No shills found in the past 24 hours.')
        

# Create an Updater for the bot
updater = Updater('BOT_TOKEN', use_context=True)

# Add handlers for the commands
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('save_shill', save_shill))
updater.dispatcher.add_handler(CommandHandler('list_shills', list_shills))
updater.dispatcher.add_handler(CommandHandler('get_shills', get_user_shills))
updater.dispatcher.add_handler(CommandHandler('latest_shills', latest_shills))

# Add a handler for text messages
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save_shill))

# Start the bot
updater.start_polling()
updater.idle()

# Close the database connection when the bot is stopped
conn.close()
