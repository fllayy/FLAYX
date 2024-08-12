from dotenv import load_dotenv
import os
import time
import discord
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import logging

logging.getLogger('sqlalchemy.engine.Engine').disabled = True

def convertMs(milliseconds):
    seconds = milliseconds // 1000
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, remaining_minutes = divmod(minutes, 60)

    time_string = ""

    if hours > 0:
        time_string += f"{hours:02d}:"

    time_string += f"{remaining_minutes:02d}:{remaining_seconds:02d}"

    return time_string


#-------------- API Clients --------------
load_dotenv()
TOKEN = os.getenv("TOKEN")
LAVALINK_HOST = os.getenv("LAVALINK_HOST")
LAVALINK_PORT = os.getenv("LAVALINK_PORT")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

#--------------- Database Configuration ---------------
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

#--------------- ORM Models ---------------
class Setting(Base):
    __tablename__ = 'settings'
    id = Column(BigInteger, primary_key=True)
    prefix = Column(String(5))
    volume = Column(Integer)
    time = Column(Integer)
    dj = Column(BigInteger, nullable=True)

class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    rankLvl = Column(Integer)

class Playlist(Base):
    __tablename__ = 'playlist'
    id = Column(BigInteger, primary_key=True)
    name = Column(Text)
    tracks = Column(Text)

#--------------- Database Initialization ---------------
Base.metadata.create_all(engine)

#--------------- Database Class ---------------
class DBClass:
    
    def __init__(self):
        self.session = session
    
    def check(self):
        try:
            self.session.execute(text('SELECT 1'))
        except Exception as e:
            print("Database ping failed:", e)

    def ping_mysql(self):
        self.check()
        try:
            start_time = time.time()
            conn = engine.connect()
            end_time = time.time()
            ping_time = (end_time - start_time)
            conn.close()
            return ping_time
        except Exception as e:
            return f"Erreur : {e}"

    def find_one(self, model, id):
        self.check()
        result = self.session.query(model).filter_by(id=id).first()
        if result is not None:
            return result
        else:
            return None

    def set_settings(self, id):
        self.check()
        new_setting = Setting(id=id, prefix='+', volume=100, time=0, dj=None)
        self.session.add(new_setting)
        self.session.commit()

    def update_one(self, model, id, updates):
        self.check()
        self.session.query(model).filter_by(id=id).update(updates)
        self.session.commit()

    def set_user(self, id):
        self.check()
        new_user = User(id=id, rankLvl=0)
        self.session.add(new_user)
        self.session.commit()

    def create_playlist(self, id, name):
        self.check()
        new_playlist = Playlist(id=id, name=name, tracks="")
        self.session.add(new_playlist)
        self.session.commit()

try:
    db = DBClass()
    print("\nSuccesfully connected to MySQL\n")
except Exception as e:
    raise Exception("\nNot able to connect to MySQL! Reason:", e, "\n")

#--------------- Functions ---------------
async def get_user_rank(userId):
    user = db.find_one(User, userId)
    if user is None:
        rank, maxTrack = None, None
    elif user.rankLvl == 0:
        rank, maxTrack = "Base", 75
    elif user.rankLvl == 1:
        rank, maxTrack = "Premium", 500
    return rank, maxTrack

async def create_account(ctx):
    from views.playlist import CreateView
    view = CreateView()
    embed = discord.Embed(title="Do you want to create an account on FLAYX ?")
    embed.description = f"> Plan: Base | 75 tracks in the playlist."
    embed.add_field(name="Terms of Service:", value="‌➥ We assure you that all your data on FLAYX will not be disclosed to any third party\n"
                                                    "➥ We will not perform any data analysis on your data\n"
                                                    "➥ You have the right to immediately stop the services we offer to you\n"
                                                    "➥ Please do not abuse our services, such as affecting other users\n", inline=False)
    
    try:
        message = await ctx.send(embed=embed, view=view, ephemeral=True)
        view.response = message

        await view.wait()
        if view.value:
            db.set_user(ctx.author.id)
            db.create_playlist(ctx.author.id, "❤️")

    except Exception as WasAnInteraction:
        message = await ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        view.response = message

        await view.wait()
        if view.value:
            db.set_user(ctx.user.id)
            db.create_playlist(ctx.user.id, "❤️")