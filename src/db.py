from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, BigInteger, DateTime, PasswordType, Text, Float
import os
import uuid
import datetime, time

Base = declarative_base()
#postgresql://user:password@host/database
engine = create_engine(os.environ.get('PG_CONNSTR'))

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#create database structure
def dbInit():
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    fb_token = Column(String(255))
    session_token = Column(String(255))
    session_token_expires_at = Column(DateTime)
    gcm_id = Column(String(512))
    blood_type = Column(String(3))

    def __init__(self, user_id, fb_token='', gcm_id='', blood_type=''):
        self.user_id = user_id
        self.fb_token = fb_token
        self.gcm_id = gcm_id
        self.blood_type = blood_type
        self.session_token, self.session_token_expires_at = User.generate_session_token()

    def  __repr__(self):
        return "<User %r %r >" % (self.id, self.username)

    @classmethod
    def generate_session_token(cls):
        token = ''.join([uuid.uuid4().hex for x in range(4)])
        expires_at = datetime.datetime.now() + datetime.timedelta(days=10)
        return (token, expires_at)

class Hospital(Base):
    __tablename__ = 'hospitals'

    hospital_id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    username = Column(String(255), unique=True)
    password = Column(PasswordType)
    address = Column(String(255))
    contact = Column(String(255))

    def __init__(self, hospital_id, name, username, password, address, contact):
        self.hospital_id = hospital_id
        self.name = name
        self.username = username
        self.password = password
        self.address = address
        self.contact = contact

    def  __repr__(self):
        return "<Hospital %r %r >" % (self.id, self.name)

class Campain(Base):
    __tablename__ = 'campains'

    campain_id = Column(BigInteger, primary_key=True)
    hospital_id = Column(BigInteger) # TODO: FK to hospitals.hospital_id
    start_date = Column(DateTime, default=)
    title = Column(String(255))
    message = Column(Text)

    def __init__(self, campain_id, hospital_id, title, message, start_date=None):
        self.campain_id = campain_id
        self.hospital_id = hospital_id
        self.title = title
        self.message = message
        self.start_date = start_date or datetime.datetime.now()

    def  __repr__(self):
        return "<Campain %r by hospital %r >" % (self.campain_id, self.hospital_id)

class BloodReserve(Base):
    __tablename__ = 'blood_reserves'

    hospital_id = Column(BigInteger) # TODO: FK to hospitals.hospital_id
    a_positive = Column(Float)
    a_negative = Column(Float)
    b_positive = Column(Float)
    b_negative = Column(Float)
    ab_positive = Column(Float)
    ab_negative = Column(Float)
    zero_positive = Column(Float)
    zero_negative = Column(Float)

    def __repr__(self):
        return "<BloodReserve (A+: %r), (A-: %r), (B+: %r), (B-: %r), (AB+: %r), (AB-: %r), (0+: %r), (0-: %r)>"
            % (self.a_positive, self.a_negative, self.b_positive, self.b_negative, self.ab_positive, self.ab_negative, self.zero_positive, self.zero_negative)
