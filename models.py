from database import Base
from flask_security import UserMixin, RoleMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, String, ForeignKey


class Friends(Base):
    __tablename__ = 'friends'
    id = Column(Integer(), primary_key=True)
    user1_id = Column('user1_id', Integer(), ForeignKey('user.id'))
    user2_id = Column('user2_id', Integer())

    def __init__(self, user1_id=None, user2_id=None):
        self.user1_id = user1_id
        self.user2_id = user2_id


class RolesUsers(Base):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))


class Role(Base, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    country = Column(String(2))
    airport = Column(String(8))
    dest_countries = Column(String(255))
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))
    friends = relationship('User', secondary='friends',
                           backref=backref('users', lazy='dynamic'))
