import logging
from functools import wraps

from sqlalchemy.exc import SQLAlchemyError
from telegram import Bot, Update
from MWT import MWT
from typing import AdminType, check_admin, check_ban, log, Session

Session()


@MWT(timeout=60*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]

def admin_allowed(bot, update):

    if update.message.from_user.id in get_admin_ids(bot, update.message.chat_id):
            
            
            update.message.reply_text("access accepted?")
            if update.message.from_user.id not in get_admin_ids:
                update.message.reply_text("Unauthorized access denied for {}.")
                return 


def user_allowed(ban_enable=True):
    if callable(ban_enable):
        return admin_allowed
    else:
        def wrap(func):
            return admin_allowed(func)
    return wrap
