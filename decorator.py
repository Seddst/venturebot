import logging
from functools import wraps

from sqlalchemy.exc import SQLAlchemyError
from telegram import Bot, Update

from typing import AdminType, check_admin, check_ban, log, Session

Session()


def admin_allowed(adm_type=AdminType.FULL, ban_enable=True, allowed_types=()):
    def decorate(func):
        def wrapper(bot: Bot, update, *args, **kwargs):
            Session()
            try:
                allowed = check_admin(update, adm_type, allowed_types)
                if ban_enable:
                    allowed &= check_ban(update)
                if allowed:
                    if func.__name__ not in ['manage_all', 'trigger_show', 'user_panel', 'wrapper', 'welcome']:
                        log(
                            update.effective_user.id,
                            update.effective_chat.id,
                            func.__name__,
                            update.message.text if update.message else None or update.callback_query.data if update.callback_query else None
                        )
                    # Fixme: Issues a message-update even if message did not change. This
                    # raises a telegram.error.BadRequest exception!
                    func(bot, update, Session, *args, **kwargs)
            except SQLAlchemyError as err:
                bot.logger.error(str(err))
                Session.rollback()
        return wrapper
    return decorate
    
    
def user_allowed(ban_enable=True):
    if callable(ban_enable):
        return admin_allowed(AdminType.NOT_ADMIN)(ban_enable)
    else:
        def wrap(func):
            return admin_allowed(AdminType.NOT_ADMIN, ban_enable)(func)
    return wrap
