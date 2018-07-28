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
from typing import User, Admin, Ban, WelcomeMsg, LocalTrigger, Trigger, MessageType, AdminType, check_admin
from decorator import user_allowed, admin_allowed
from config import TOKEN
from utils import send_async, update_group
from telegram import Update, Bot, Message, ParseMode
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(self, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Greetings, soldier! I am the Soul Bot of 🥔Nomadic Entrepreneurs!  \
                    ' '')


def admin_panel(self, update):
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


def help_msg(self, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text("/list_triggers — show all triggers.")


def ping(bot: Bot, update: Update):
    send_async(bot, chat_id=update.message.chat.id, text=('Go and dig some soulz, @{}!').format(update.message.from_user.username))


def echo(self, update: Update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)
      
    
def trigger_decorator(func):
    @user_allowed
    def wrapper(bot, update, session, *args, **kwargs):
        group = update_group(update.message.chat, session)
        if group is None and \
                check_admin(update, session, AdminType.FULL) or \
                group is not None and \
                (group.allow_trigger_all or
                 check_admin(update, session, AdminType.GROUP)):
            func(bot, update, session, *args, **kwargs)
    return wrapper   
  

@trigger_decorator  
def add_trigger(bot, update, session):
    msg = update.message.text.split(' ', 1)
    if len(msg) == 2 and len(msg[1]) > 0 and update.message.reply_to_message:
        trigger_text = msg[1].strip()
        trigger = session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id, trigger=trigger_text).first()
        if trigger is None:
            data = update.message.reply_to_message
            add_trigger_db(data, update.message.chat, trigger_text, session)
            send_async(bot, chat_id=update.message.chat.id,
                       text='The trigger for the phrase "{}" is set.'.format(trigger_text))
        else:
            send_async(bot, chat_id=update.message.chat.id,
                       text='Trigger "{}" already exists, select another one.'.format(trigger_text))
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Your thoughts are not clear, try one more time')

        
@trigger_decorator
def set_trigger(bot, update, session):
    msg = update.message.text.split(' ', 1)
    if len(msg) == 2 and len(msg[1]) > 0 and update.message.reply_to_message:
        trigger = msg[1].strip()
        data = update.message.reply_to_message
        add_trigger_db(data, update.message.chat, trigger, session)
        send_async(bot, chat_id=update.message.chat.id, text='The trigger for the phrase "{}" is set.'.format(trigger))
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Your thoughts are not clear, try one more time')

        
@trigger_decorator
def del_trigger(bot, update, session):
    msg = update.message.text.split(' ', 1)[1]
    trigger = session.query(LocalTrigger).filter_by(trigger=msg).first()
    if trigger is not None:
        session.delete(trigger)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text='The trigger for "{}" has been deleted.'.format(msg))
    else:
        send_async(bot, chat_id=update.message.chat.id, text='Where did you see such a trigger? 0_o')

        
@trigger_decorator
def list_triggers(bot: Bot, update: Update, session):
    triggers = session.query(Trigger).all()
    local_triggers = session.query(LocalTrigger).filter_by(chat_id=update.message.chat.id).all()
    msg = 'List of current triggers: \n' + \
          '<b>Global:</b>\n' + ('\n'.join([trigger.trigger for trigger in triggers]) or '[Empty]\n') + \
          '\n<b>Local:</b>\n' + ('\n'.join([trigger.trigger for trigger in local_triggers]) or '[Empty]\n')
    send_async(bot, chat_id=update.message.chat.id, text=msg, parse_mode=ParseMode.HTML)


def add_trigger_db(msg: Message, chat, trigger_text: str, session):
    trigger = session.query(LocalTrigger).filter_by(chat_id=chat.id, trigger=trigger_text).first()
    if trigger is None:
        trigger = LocalTrigger()
        trigger.chat_id = chat.id
        trigger.trigger = trigger_text
    if msg.audio:
        trigger.message = msg.audio.file_id
        trigger.message_type = MessageType.AUDIO.value
    elif msg.document:
        trigger.message = msg.document.file_id
        trigger.message_type = MessageType.DOCUMENT.value
    elif msg.voice:
        trigger.message = msg.voice.file_id
        trigger.message_type = MessageType.VOICE.value
    elif msg.sticker:
        trigger.message = msg.sticker.file_id
        trigger.message_type = MessageType.STICKER.value
    elif msg.contact:
        trigger.message = str(msg.contact)
        trigger.message_type = MessageType.CONTACT.value
    elif msg.video:
        trigger.message = msg.video.file_id
        trigger.message_type = MessageType.VIDEO.value
    elif msg.video_note:
        trigger.message = msg.video_note.file_id
        trigger.message_type = MessageType.VIDEO_NOTE.value
    elif msg.location:
        trigger.message = str(msg.location)
        trigger.message_type = MessageType.LOCATION.value
    elif msg.photo:
        trigger.message = msg.photo[-1].file_id
        trigger.message_type = MessageType.PHOTO.value
    else:
        trigger.message = msg.text
        trigger.message_type = MessageType.TEXT.value
    session.add(trigger)
    session.commit()

    
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
        send_async(bot, chat_id=update.message.chat.id, text='The welcome text is set.')

@admin_allowed
def enable_welcome(bot, update, session):
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        group.welcome_enabled = True
        session.add(group)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text='Welcome enabled')

@admin_allowed
def disable_welcome(bot, update, session):
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        group.welcome_enabled = False
        session.add(group)
        session.commit()
        send_async(bot, chat_id=update.message.chat.id, text='Welcome disabled')

@admin_allowed
def show_welcome(bot, update, session):
  
    if update.message.chat.type in ['group']:
        group = update_group(update.message.chat, session)
        welcome_msg = session.query(WelcomeMsg).filter_by(chat_id=group.id).first()
        if welcome_msg is None:
            welcome_msg = WelcomeMsg(chat_id=group.id, message='Hi, %username%!')
            session.add(welcome_msg)
            session.commit()
        send_async(bot, chat_id=group.id, text=welcome_msg.message)


@admin_allowed
def set_admin(bot: Bot, update: Update, session):
    msg = update.message.text.split(' ', 1)[1]
    msg = msg.replace('@', '')
    if msg != '':
        user = session.query(User).filter_by(username=msg).first()
        if user is None:
            send_async(bot,
                       chat_id=update.message.chat.id,
                       text='No such user')

        else:
            adm = session.query(Admin).filter_by(user_id=user.id,
                                                 admin_group=update.message.chat.id).first()

            if adm is None:
                new_group_admin = Admin(user_id=user.id,
                                        admin_type=AdminType.GROUP.value,
                                        admin_group=update.message.chat.id)

                session.add(new_group_admin)
                session.commit()
                send_async(bot,
                           chat_id=update.message.chat.id,
                           text="""Welcome our new administrator: @{}!
Check the commands list with /help command""".format(user.username))

            else:
                send_async(bot,
                           chat_id=update.message.chat.id,
                           text='@{} already has administrator rights'.format(user.username))


@admin_allowed
def del_admin(bot, update, session):
    msg = update.message.text.split(' ', 1)[1]
    if msg.find('@') != -1:
        msg = msg.replace('@', '')
        if msg != '':
            user = session.query(User).filter_by(username=msg).first()
            if user is None:
                send_async(bot,
                           chat_id=update.message.chat.id,
                           text='No such user')

            else:
                del_adm(bot, update.message.chat.id, user, session)
    else:
        user = session.query(User).filter_by(id=msg).first()
        if user is None:
            send_async(bot,
                       chat_id=update.message.chat.id,
                       text='No such user')

        else:
            del_adm(bot, update.message.chat.id, user, session)


def del_adm(bot, chat_id, user, session):
    adm = session.query(Admin).filter_by(user_id=user.id,
                                         admin_group=chat_id).first()

    if adm is None:
        send_async(bot,
                   chat_id=chat_id,
                   text='@{} never had any power here!'.format(user.username))

    else:
        session.delete(adm)
        session.commit()
        send_async(bot,
                   chat_id=chat_id,
                   text='@{}, now you have no power here!'.format(user.username))


@admin_allowed
def list_admins(self, bot, update, session):
    admins = session.query(Admin).filter(Admin.admin_group == update.message.chat.id).all()
    users = []
    for admin_user in admins:
        users.append(session.query(User).filter_by(id=admin_user.user_id).first())
    msg = 'Administrators list:\n'
    for user in users:
        msg += '{} @{} {} {}\n'.format(user.id,
                                       user.username,
                                       user.first_name,
                                       user.last_name)

    send_async(bot, chat_id=update.message.chat.id, text=msg)


@admin_allowed
def ban(self, bot: Bot, update: Update, session):
    username, reason = update.message.text.split(' ', 2)[1:]
    username = username.replace('@', '')
    user = session.query(User).filter_by(username=username).first()
    if user:
        banned = session.query(Ban).filter_by(user_id=user.id).first()
        if banned:
            send_async(bot, chat_id=update.message.chat.id,
                       text='This user is already banned. The reason is: .'.format(banned.to_date, banned.reason))
        else:
            banned = Ban()
            banned.user_id = user.id
            banned.from_date = datetime.now()
            banned.to_date = datetime.max
            banned.reason = reason or 'Reason not specified'
            member = session.query().filter_by(user_id=user.id).first()
            if member:
                session.delete(member)
            admins = session.query(Admin).filter_by(user_id=user.id).all()
            for admin in admins:
                session.delete(admin)
            session.add(banned)
            session.commit()
            send_async(bot, chat_id=user.id, text='You were banned because: {}'.format(banned.reason))
            send_async(bot, chat_id=update.message.chat.id, text='Soldier successfully banned')
    else:
        send_async(bot, chat_id=update.message.chat.id, text='No such user')


@admin_allowed
def unban(self, bot, update, session):
    username = update.message.text.split(' ', 1)[1]
    username = username.replace('@', '')
    user = session.query(User).filter_by(username=username).first()
    if user:
        banned = session.query(Ban).filter_by(user_id=user.id).first()
        if banned:
            session.delete(banned)
            session.commit()
            send_async(bot, chat_id=user.id, text='We can talk again 🌚')
            send_async(bot, chat_id=update.message.chat.id, text='{} is no longer banned.'.format('@' + user.username))
        else:
            send_async(bot, chat_id=update.message.chat.id, text='This soldier is not banned')
    else:
        send_async(bot, chat_id=update.message.chat.id, text='No such user')


def error(self, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


@admin_allowed
def kick(self, bot, update):
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
