from dotenv import load_dotenv
import os
import time
import discord
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
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

# Creating the engine with connection pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=True
)

Session = scoped_session(sessionmaker(bind=engine))
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
        self.session = Session()


    def ping_mysql(self):
        try:
            start_time = time.time()
            conn = engine.connect()
            end_time = time.time()
            ping_time = (end_time - start_time)
            conn.close()
            return ping_time
        except Exception as e:
            return f"Error: {e}"


    def find_one(self, model, id):
        try:
            result = self.session.query(model).filter_by(id=id).first()
            return result
        except Exception as e:
            self.session.rollback()
            print("Error in find_one:", e)
            return None


    def set_settings(self, id):
        try:
            new_setting = Setting(id=id, prefix='+', volume=100, time=0, dj=None)
            self.session.add(new_setting)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print("Error in set_settings:", e)


    def update_one(self, model, id, updates):
        try:
            self.session.query(model).filter_by(id=id).update(updates)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print("Error in update_one:", e)


    def set_user(self, id):
        try:
            new_user = User(id=id, rankLvl=0)
            self.session.add(new_user)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print("Error in set_user:", e)


    def create_playlist(self, id, name):
        try:
            new_playlist = Playlist(id=id, name=name, tracks="")
            self.session.add(new_playlist)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print("Error in create_playlist:", e)

try:
    db = DBClass()
    print("\nSuccessfully connected to MySQL\n")
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
