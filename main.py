#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Greetings, soldier! I am the Soul Bot of 🥔Nomadic Entrepreneurs!  \
                    ' '')
    
def admin_panel(bot, update):
   if update.message.chat.type == ['private']:
     update.message.reply_text("""Welcome commands:
/enable_welcome — enable welcome message.
/disable_welcome — disable welcome message.
/set_welcome <text> — set welcome message. \
->Can contain %username% — will be shown as @username, %ign% - will show user ingame name, \
if not set to First and Last name, or ID, 
using %last_name%, %first_name%, %id%. <-i don't think this still exists *deleted probably*
/show_welcome — show welcome message.
Trigger commands:
Reply to a message or file with /set_trigger <trigger text> — \
set message to reply with on a trigger (only current chat)
/del_trigger <trigger> — delete trigger.
/list_triggers — show all triggers.
Reply to a message or file with /set_global_trigger <trigger text> — \
set message to reply with on a trigger (all chats)
/del_global_trigger <trigger> — delete trigger.
Super administrator commands:
/add_admin <user> — add administrator to current chat.
/del_admin <user> — delete administrator from current chat.
/list_admins — show list of current chat administrators.
/enable_trigger — allow everyone to call trigger.
/disable_trigger — forbid everyone to call trigger.
/find <user> - Show user status by telegram user name  *might be removed*
/findc <ign> - Show user status by ingame name        *might be removed*
/findi <id> - Show user status by telegram uquique id  *might be removed*
Free text commands:
allow everyone to trigger - Allow every member to call triggers
prevent everyone from triggering - Allow only admins to call triggers
allow everyone to pin - Allow all members to pin messages 
prevent everyone from pinning - Allow only admins to pin messages
Reply any message with Pin to Pin it (admins always can do that, other members if its enabled)
Reply any message with Pin and notify to pin and send notificaion
Reply any message with Delete to delete it 
""")
    

def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text("/list_triggers — show all triggers.")

def ping(bot, update):
    send_async(bot, chat_id=update.message.chat.id, text=MSG_PING.format(update.message.from_user.username))
    

def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def add_trigger(bot, update, session):
    msg = update.message.text.split(' ', 1)
    if len(msg) == 2 and len(msg[1]) > 0 and update.message.reply_to_message:
        trigger_text = msg[1].strip()
        trigger = session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id, trigger=trigger_text).first()
        if trigger is None:
            data = update.message.reply_to_message
            add_trigger_db(data, update.message.chat, trigger_text, session)
            send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_NEW.format(trigger_text))
        else:
            send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_EXISTS.format(trigger_text))
    else:
        send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_NEW_ERROR)
        
 
def set_trigger(bot, update, session):
    msg = update.message.text.split(' ', 1)
    if len(msg) == 2 and len(msg[1]) > 0 and update.message.reply_to_message:
        trigger = msg[1].strip()
        data = update.message.reply_to_message
        add_trigger_db(data, update.message.chat, trigger, session)
        send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_NEW.format(trigger))
    else:
        send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_NEW_ERROR)
        
 def del_trigger(bot, update, session):
    msg = update.message.text.split(' ', 1)[1]
    trigger = session.query(LocalTrigger).filter_by(trigger=msg).first()
    if trigger is not None:
        session.delete(trigger)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_DEL.format(msg))
    else:
        send_async(bot, chat_id=update.message.chat.id, text=MSG_TRIGGER_DEL_ERROR)
        
def list_triggers(bot, update, session):
    triggers = session.query(Trigger).all()
    local_triggers = session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id).all()
    msg = MSG_TRIGGER_LIST_HEADER + \
          MSG_TRIGGER_GLOBAL + ('\n'.join([trigger.trigger for trigger in triggers]) or MSG_EMPTY) + \
          MSG_TRIGGER_LOCAL + ('\n'.join([trigger.trigger for trigger in local_triggers]) or MSG_EMPTY)
    send_async(bot, chat_id=update.message.chat.id, text=msg, parse_mode=ParseMode.HTML)
    
def set_welcome(bot, update, session):
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        welcome_msg = session.query(WelcomeMsg).filter_by(chat_id=group.id).first()
        if welcome_msg is None:
            welcome_msg = WelcomeMsg(chat_id=group.id, message=update.message.text.split(' ', 1)[1])
        else:
            welcome_msg.message = update.message.text.split(' ', 1)[1]
        session.add(welcome_msg)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text=MSG_WELCOME_SET)
      
def enable_welcome(bot: Bot, update: Update, session):
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        group.welcome_enabled = True
        session.add(group)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text=MSG_WELCOME_ENABLED)        

def disable_welcome(bot: Bot, update: Update, session):
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        group.welcome_enabled = False
        session.add(group)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text=MSG_WELCOME_DISABLED)  
        
def show_welcome(bot, update, session):
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        welcome_msg = session.query(WelcomeMsg).filter_by(chat_id=group.id).first()
        if welcome_msg is None:
            welcome_msg = WelcomeMsg(chat_id=group.id, message=MSG_WELCOME_DEFAULT)
            session.add(welcome_msg)
            session.commit()
        send_async(bot, chat_id=group.id, text=welcome_msg.message) 
        
def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    
@admin_allowed()
def kick(bot: Bot, update: Update):
    bot.leave_chat(update.message.chat.id)

def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater('618668131:AAG57FawPhzS5FEBsyGRsSZ1aIxbh871Ei0')

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("help", help_msg))
    disp.add_handler(CommandHandler("ping", ping))
    disp.add_handler(CommandHandler("set_trigger", set_trigger))
    disp.add_handler(CommandHandler("add_trigger", add_trigger))
    disp.add_handler(CommandHandler("del_trigger", del_trigger))
    disp.add_handler(CommandHandler("list_triggers", list_triggers))
    disp.add_handler(CommandHandler("set_welcome", set_welcome))
    disp.add_handler(CommandHandler("enable_welcome", enable_welcome))
    disp.add_handler(CommandHandler("disable_welcome", disable_welcome))
    disp.add_handler(CommandHandler("show_welcome", show_welcome))
    disp.add_handler(CommandHandler("add_admin", set_admin))
    disp.add_handler(CommandHandler("del_admin", del_admin))
    disp.add_handler(CommandHandler("list_admins", list_admins))
    disp.add_handler(CommandHandler("kick", kick))
    
    disp.add_handler(CommandHandler("ban", ban))
    disp.add_handler(CommandHandler("unban", unban))    
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
