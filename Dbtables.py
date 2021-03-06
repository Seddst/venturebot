# -*- coding: utf-8 -*-
from datetime import datetime
from enum import Enum
import logging

from sqlalchemy import (
    create_engine,
    Column, Integer, TIMESTAMP, Boolean, ForeignKey, BigInteger, text, VARCHAR, DateTime, func, String
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from telegram import Bot

from config import DB


class AdminType(Enum):
    SUPER = 0
    FULL = 1
    GROUP = 2

    NOT_ADMIN = 100


class MessageType(Enum):
    TEXT = 0
    VOICE = 1
    DOCUMENT = 2
    STICKER = 3
    CONTACT = 4
    VIDEO = 5
    VIDEO_NOTE = 6
    LOCATION = 7
    AUDIO = 8
    PHOTO = 9


ENGINE = create_engine(DB,
                       echo=False,
                       pool_size=200,
                       max_overflow=50,
                       isolation_level="READ UNCOMMITTED")

# FIX: имена констант(constant names)?
LOGGER = logging.getLogger('sqlalchemy.engine')
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=ENGINE))
Session()


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)  # FIX: invalid name
    username = Column(String)
    title = Column(String)
    welcome_enabled = Column(Boolean, default=False)  # if errors change back to default of false
    allow_trigger_all = Column(Boolean, default=False)
    allow_pin_all = Column(Boolean, default=False)
    bot_in_group = Column(Boolean, default=True)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    date_added = Column(DateTime, default=func.now())

    def __repr__(self):
        user = ''
        if self.first_name:
            user += self.first_name + ' '
        if self.last_name:
            user += self.last_name + ' '
        if self.username:
            user += '(@' + self.username + ')'
        return user

    def __str__(self):
        user = ''
        if self.first_name:
            user += self.first_name + ' '
        if self.last_name:
            user += self.last_name
        return user


class WelcomeMsg(Base):
    __tablename__ = 'welcomes'

    chat_id = Column(Integer, primary_key=True)
    message = Column(String)


class Wellcomed(Base):
    __tablename__ = 'wellcomed'

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    chat_id = Column(Integer, ForeignKey(WelcomeMsg.chat_id), primary_key=True)


class Trigger(Base):
    __tablename__ = 'triggers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger = Column(String)
    message = Column(String)
    message_type = Column(Integer, default=0)


class Admin(Base):
    __tablename__ = 'admins'

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    admin_type = Column(Integer)
    admin_group = Column(Integer, primary_key=True, default=0)


class LocalTrigger(Base):
    __tablename__ = 'local_triggers'

    id = Column(Integer, autoincrement=True, primary_key=True)
    chat_id = Column(Integer, ForeignKey(Group.id))
    trigger = Column(String)
    message = Column(String)
    message_type = Column(Integer, default=0)


class Ban(Base):
    __tablename__ = 'banned_users'

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    reason = Column(String)
    from_date = Column(DateTime, default=func.now())
    to_date = Column(DateTime, default=func.now())


class Log(Base):
    __tablename__ = 'log'

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    chat_id = Column(Integer)
    date = Column(DateTime, default=func.now())
    func_name = Column(String)
    args = Column(String)


class Auth(Base):
    __tablename__ = 'auth'

    id = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)


def check_admin(update, adm_type, allowed_types=()):
    allowed = False
    if adm_type == AdminType.NOT_ADMIN:
        allowed = True
    else:
        admins = Session().query(Admin).filter_by(user_id=update.message.from_user.id).all()
        for adm in admins:
            if (AdminType(adm.admin_type) in allowed_types or adm.admin_type <= adm_type.value) and \
                    (adm.admin_group in [0, update.message.chat.id] or
                     update.message.chat.id == update.message.from_user.id):
                if adm.admin_group != 0:
                    group = Session().query(Group).filter_by(id=adm.admin_group).first()
                    if group and group.bot_in_group:
                        allowed = True
                        break
                else:
                    allowed = True
                    break
    return allowed


def check_ban(update):
    ban = Session().query(Ban).filter_by(user_id=update.message.from_user.id).first()
                                       

    if ban is None or ban.to_date < TIMESTAMP:
        return True
    else:
        return False

    
def log(user_id, chat_id, func_name, args):
    if user_id:
        log_item = Log()
        log_item.date = datetime.now()
        log_item.user_id = user_id
        log_item.chat_id = chat_id
        log_item.func_name = func_name
        log_item.args = args
        s = Session()
        s.add(log_item)
        s.commit()
        #Session.remove()


Base.metadata.create_all(ENGINE)
