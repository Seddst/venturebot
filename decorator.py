import logging
from functools import wraps

from sqlalchemy.exc import SQLAlchemyError
from telegram import Bot, Update
from MWT import MWT
from Dbtables import AdminType, check_admin, check_ban, log, Session

Session()


@MWT(timeout=60*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
