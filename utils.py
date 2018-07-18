from telegram import Bot
from telegram.error import TelegramError
from telegram.ext.dispatcher import run_async
from typing import Session, Group


@run_async
def send_async(bot: Bot, *args, **kwargs):
    try:
        return bot.sendMessage(*args, **kwargs)

    except TelegramError as err:
        bot.logger.error(err.message)
        session = Session()
        group = session.query(Group).filter_by(id=kwargs['chat_id']).first()
        if group is not None:
            group.bot_in_group = False
            session.add(group)
            session.commit()
        return None


def update_group(self, grp, session):
    if grp.type in ['group', 'supergroup' 'channel']:
        group = session.query(Group).filter_by(id=grp.id).first()
        if group is None:
            group = Group(id=grp.id, title=grp.title,
                          username=grp.username)
            session.add(group)

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
                session.add(group)

        session.commit()
        return group
    return None
