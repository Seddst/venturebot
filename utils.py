from telegram import Bot
from telegram.error import TelegramError
from telegram.ext.dispatcher import run_async
from typing import Session, Group

Session()

@run_async
def send_async(bot: Bot, *args, **kwargs):
    try:
        return bot.sendMessage(*args, **kwargs)

    except TelegramError as err:
        bot.logger.error(err.message)
        
        group = Session.query(Group).filter_by(id=kwargs['chat_id']).first()
        if group is not None:
            group.bot_in_group = False
            Session.add(group)
            Session.commit()
        return None


def update_group(grp):
    if grp.type in ['group', 'supergroup' 'channel']:
        group = Session.query(Group).filter_by(id=grp.id).first()
        if group is None:
            group = Group(id=grp.id, title=grp.title,
                          username=grp.username)
            Session.add(group)

        else:
            updated = False
            if group.username != grp.username:
                group.username = grp.username
                updated = True
            if group.title != grp.title:
                group.title = grp.title
                updated = True
            if not group.bot_in_group:
                group.bot_in_group = True
                updated = True
            if updated:
                Session.add(group)

        Session.commit()
        return group
    return None
