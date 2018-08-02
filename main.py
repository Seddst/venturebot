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
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from json import loads
from typing import User, Admin, Ban, WelcomeMsg, LocalTrigger, Trigger, MessageType, AdminType, check_admin, Session
from decorator import get_admin_ids
from config import TOKEN
from utils import send_async, update_group
from telegram import Update, Bot, Message, ParseMode 
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

Session()

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(self, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Greetings, soldier! I am the Soul Bot of 🥔Nomadic Entrepreneurs!  \
                    ' '')


def admin_panel(bot: Bot, update: Update):
    
     send_async(bot, chat_id=update.message.chat.id, text=("""Welcome commands:
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
"""))


def help_msg(self, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text("/list_triggers — show all triggers.")


def ping(bot: Bot, update: Update):
    send_async(bot, chat_id=update.message.chat.id, text=('Go and dig some soulz, @{}!').format(update.message.from_user.username))


# def echo(self, update: Update):
  #  """Echo the user message."""
 #   update.message.reply_text(update.message.text)


def trigger_show(bot: Bot, update: Update):
    trigger = Session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id, trigger=update.message.text).first()
    if trigger is None:
        trigger = Session.query(Trigger).filter_by(trigger=update.message.text).first()
    if trigger is not None:
        if trigger.message_type == MessageType.AUDIO.value:
            bot.send_audio(update.message.chat.id, trigger.message)
        elif trigger.message_type == MessageType.DOCUMENT.value:
            bot.send_document(update.message.chat.id, trigger.message)
        elif trigger.message_type == MessageType.VOICE.value:
            bot.send_voice(update.message.chat.id, trigger.message)
        elif trigger.message_type == MessageType.STICKER.value:
            bot.send_sticker(update.message.chat.id, trigger.message)
        elif trigger.message_type == MessageType.CONTACT.value:
            msg = trigger.message.replace('\'', '"')
            contact = loads(msg)
            if 'phone_number' not in contact.keys():
                contact['phone_number'] = None
            if 'first_name' not in contact.keys():
                contact['first_name'] = None
            if 'last_name' not in contact.keys():
                contact['last_name'] = None
            bot.send_contact(update.message.chat.id,
                             contact['phone_number'],
                             contact['first_name'],
                             contact['last_name'])
        elif trigger.message_type == MessageType.VIDEO.value:
            bot.send_video(update.message.chat.id, trigger.message)
        elif trigger.message_type == MessageType.VIDEO_NOTE.value:
            bot.send_video_note(update.message.chat.id, trigger.message)
        elif trigger.message_type == MessageType.LOCATION.value:
            msg = trigger.message.replace('\'', '"')
            location = loads(msg)
            bot.send_location(update.message.chat.id, location['latitude'], location['longitude'])
        elif trigger.message_type == MessageType.PHOTO.value:
            bot.send_photo(update.message.chat.id, trigger.message)
        else:
            send_async(bot, chat_id=update.message.chat.id, text=trigger.message, disable_web_page_preview=True)

            
def list_triggers(bot, update): 
    triggers = Session.query(Trigger).all()
    local_triggers = Session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id).all()
    msg = 'List of current triggers: \n' + \
          '<b>Global:</b>\n' + ('\n'.join([trigger.trigger for trigger in triggers]) or '[Empty]\n') + \
          '\n<b>Local:</b>\n' + ('\n'.join([trigger.trigger for trigger in local_triggers]) or '[Empty]\n')
    send_async(bot, chat_id=update.message.chat.id, text=msg, parse_mode=ParseMode.HTML)


def add_trigger_db(msg: Message, chat, trigger_text: str):
      
    trigger = Session.query(LocalTrigger).filter_by(chat_id=chat.id, trigger=trigger_text).first()
    if trigger is None:
        trigger = LocalTrigger()
        trigger.chat_id = chat.id
        trigger.trigger = trigger_text
    if msg.Audio:
        trigger.message = msg.Audio.file_id
        trigger.message_type = MessageType.AUDIO.value
    elif msg.Document:
        trigger.message = msg.Document.file_id
        trigger.message_type = MessageType.DOCUMENT.value
    elif msg.Voice:
        trigger.message = msg.Voice.file_id
        trigger.message_type = MessageType.VOICE.value
    elif msg.Sticker:
        trigger.message = msg.Sticker.file_id
        trigger.message_type = MessageType.STICKER.value
    elif msg.Contact:
        trigger.message = str(msg.Contact)
        trigger.message_type = MessageType.CONTACT.value
    elif msg.Video:
        trigger.message = msg.Video.file_id
        trigger.message_type = MessageType.VIDEO.value
    elif msg.video_note:
        trigger.message = msg.video_note.file_id
        trigger.message_type = MessageType.VIDEO_NOTE.value
    elif msg.Location:
        trigger.message = str(msg.Location)
        trigger.message_type = MessageType.LOCATION.value
    elif msg.Photo:
        trigger.message = msg.Photo[-1].file_id
        trigger.message_type = MessageType.PHOTO.value
    else:
        trigger.message = msg.Text
        trigger.message_type = MessageType.TEXT.value
    Session.add(trigger)
    Session.commit()

    
def set_trigger(bot: Bot, update: Update, session):
    msg = update.message.text.split(' ', 1)
    if len(msg) == 2 and len(msg[1]) > 0 or update.message.reply_to_message:
        trigger = msg[1].strip()
        data = update.message.reply_to_message
        add_trigger_db(data, update.message.chat, trigger, session)
        send_async(bot, chat_id=update.message.chat.id, text='The trigger for the phrase "{}" is set.'.format(trigger))
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Your thoughts are not clear, try one more time')    
    
 
def add_trigger(bot: Bot, update: Update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        msg = update.message.text.split(' ', 1)
        if len(msg) == 2 and len(msg[1]) > 0 or update.message.reply_to_message:
            trigger_text = msg[1].strip()
            trigger = Session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id, trigger=trigger_text).first()
            if trigger is None:
                data = update.message.reply_to_message
                add_trigger_db(data, update.message.chat, trigger_text)
                send_async(bot, chat_id=update.message.chat.id,
                           text='The trigger for the phrase "{}" is set.'.format(trigger_text))
            else:
                send_async(bot, chat_id=update.message.chat.id,
                           text='Trigger "{}" already exists, select another one.'.format(trigger_text))
        else:
            send_async(bot, chat_id=update.message.chat.id, text='Your thoughts are not clear, try one more time')

        
def del_trigger(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):  
        msg = update.message.text.split(' ', 1)[1]
        trigger = Session.query(LocalTrigger).filter_by(trigger=msg).first()
        if trigger is not None:
            Session.delete(trigger)
            Session.commit()
            send_async(bot, chat_id=update.message.chat.id, text='The trigger for "{}" has been deleted.'.format(msg))
        else:
            send_async(bot, chat_id=update.message.chat.id, text='Where did you see such a trigger? 0_o')    
    
    
def set_welcome(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id): 
        if update.message.chat.type in ['group']:
            group = update_group(update.message.chat, session)
            welcome_msg = Session.query(WelcomeMsg).filter_by(chat_id=group.id).first()
            if welcome_msg is None:
                welcome_msg = WelcomeMsg(chat_id=group.id, message=update.message.text.split(' ', 1)[1])
            else:
                welcome_msg.message = update.message.text.split(' ', 1)[1]
            Session.add(welcome_msg)
            Session.commit()
            send_async(bot, chat_id=update.message.chat.id, text='The welcome text is set.')


def enable_welcome(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        if update.message.chat.type in ['group']:
            group = update_group(update.message.chat)
            group.welcome_enabled = True
            Session.add(group)
            Session.commit()
            send_async(bot, chat_id=update.message.chat.id, text='Welcome enabled')


def disable_welcome(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        if update.message.chat.type in ['group']:
            group = update_group(update.message.chat)
            group.welcome_enabled = False
            Session.add(group)
            Session.commit()
            send_async(bot, chat_id=update.message.chat.id, text='Welcome disabled')

        
def show_welcome(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        if update.message.chat.type in ['group']:
            group = update_group(update.message.chat)
            welcome_msg = Session.query(WelcomeMsg).filter_by(chat_id=group.id).first()
            if welcome_msg is None:
                welcome_msg = WelcomeMsg(chat_id=group.id, message='Hi, %username%!')
                Session.add(welcome_msg)
                Session.commit()
                      
            send_async(bot, chat_id=group.id, text=welcome_msg.message)



def set_admin(bot: Bot, update: Update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id): 
        msg = update.message.text.split(' ', 1)[1]
        msg = msg.replace('@', '')
        if msg != '':
            user = Session.query(User).filter_by(username=msg).first()
            if user is None:
                send_async(bot,
                           chat_id=update.message.chat.id,
                           text='No such user')

            else:
                adm = Session.query(Admin).filter_by(user_id=user.id,
                                                     admin_group=update.message.chat.id).first()

                if adm is None:
                    new_group_admin = Admin(user_id=user.id,
                                            admin_type=AdminType.GROUP.value,
                                            admin_group=update.message.chat.id)

                    Session.add(new_group_admin)
                    Session.commit()
                    send_async(bot,
                               chat_id=update.message.chat.id,
                               text="""Welcome our new administrator: @{}!
    Check the commands list with /help command""".format(user.username))

                else:
                    send_async(bot,
                               chat_id=update.message.chat.id,
                               text='@{} already has administrator rights'.format(user.username))



def del_admin(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id): 
        msg = update.message.text.split(' ', 1)[1]
        if msg.find('@') != -1:
            msg = msg.replace('@', '')
            if msg != '':
                user = Session.query(User).filter_by(username=msg).first()
                if user is None:
                    send_async(bot,
                               chat_id=update.message.chat.id,
                               text='No such user')

                else:
                    del_adm(bot, update.message.chat.id, user, session)
        else:
            user = Session.query(User).filter_by(id=msg).first()
            if user is None:
                send_async(bot,
                           chat_id=update.message.chat.id,
                           text='No such user')

            else:
                del_adm(bot, update.message.chat.id, user)


def del_adm(bot, chat_id, user):
    adm = Session.query(Admin).filter_by(user_id=user.id,
                                         admin_group=chat_id).first()

    if adm is None:
        send_async(bot,
                   chat_id=chat_id,
                   text='@{} never had any power here!'.format(user.username))

    else:
        Session.delete(adm)
        Session.commit()
        send_async(bot,
                   chat_id=chat_id,
                   text='@{}, now you have no power here!'.format(user.username))



def list_admins(bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):  
        admins = Session.query(Admin).filter(Admin.admin_group == update.message.chat.id).all()
        users = []
        for admin_user in admins:
            users.append(Session.query(User).filter_by(id=admin_user.user_id).first())
        msg = 'Administrators list:\n'
        for user in users:
            msg += '{} @{} {} {}\n'.format(user.id,
                                           user.username,
                                           user.first_name,
                                           user.last_name)

        send_async(bot, chat_id=update.message.chat.id, text=msg)



def ban(self, bot: Bot, update: Update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id): 
        username, reason = update.message.text.split(' ', 2)[1:]
        username = username.replace('@', '')
        user = Session.query(User).filter_by(username=username).first()
        if user:
            banned = Session.query(Ban).filter_by(user_id=user.id).first()
            if banned:
                send_async(bot, chat_id=update.message.chat.id,
                           text='This user is already banned. The reason is: .'.format(banned.to_date, banned.reason))
            else:
                banned = Ban()
                banned.user_id = user.id
                banned.from_date = datetime.now()
                banned.to_date = datetime.max
                banned.reason = reason or 'Reason not specified'
                member = Session.query().filter_by(user_id=user.id).first()
                if member:
                    Session.delete(member)
                admins = Session.query(Admin).filter_by(user_id=user.id).all()
                for admin in admins:
                    Session.delete(admin)
                Session.add(banned)
                Session.commit()
                send_async(bot, chat_id=user.id, text='You were banned because: {}'.format(banned.reason))
                send_async(bot, chat_id=update.message.chat.id, text='Soldier successfully banned')
        else:
            send_async(bot, chat_id=update.message.chat.id, text='No such user')



def unban(self, bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id): 
        username = update.message.text.split(' ', 1)[1]
        username = username.replace('@', '')
        user = Session.query(User).filter_by(username=username).first()
        if user:
            banned = Session.query(Ban).filter_by(user_id=user.id).first()
            if banned:
                Session.delete(banned)
                Session.commit()
                send_async(bot, chat_id=user.id, text='We can talk again 🌚')
                send_async(bot, chat_id=update.message.chat.id, text='{} is no longer banned.'.format('@' + user.username))
            else:
                send_async(bot, chat_id=update.message.chat.id, text='This soldier is not banned')
        else:
            send_async(bot, chat_id=update.message.chat.id, text='No such user')


def error(self, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)



def kick(self, bot, update):
    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
        bot.leave_chat(update.message.chat.id)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_msg))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CommandHandler("ping", ping))
    dp.add_handler(CommandHandler("trigger_show", trigger_show))
    dp.add_handler(CommandHandler("set_trigger", set_trigger))
    dp.add_handler(CommandHandler("add_trigger", add_trigger))
    dp.add_handler(CommandHandler("del_trigger", del_trigger))
    dp.add_handler(CommandHandler("list_triggers", list_triggers))
    dp.add_handler(CommandHandler("set_welcome", set_welcome))
    dp.add_handler(CommandHandler("enable_welcome", enable_welcome))
    dp.add_handler(CommandHandler("disable_welcome", disable_welcome))
    dp.add_handler(CommandHandler("show_welcome", show_welcome))
    dp.add_handler(CommandHandler("add_admin", set_admin))
    dp.add_handler(CommandHandler("del_admin", del_admin))
    dp.add_handler(CommandHandler("list_admins", list_admins))
    dp.add_handler(CommandHandler("kick", kick))

    dp.add_handler(CommandHandler("ban", ban))
    dp.add_handler(CommandHandler("unban", unban))
    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

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
