from typing import List, Union
import discord
import re
import os
import traceback
import sys
from discord.ext import commands
from discord import app_commands
from discord.message import Message
import function
import update


class FLAYX(commands.Bot):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


    async def setup_hook(self):
        print("--- Loading of cogs: ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"{filename[:-3]} loaded")
                except Exception as e:
                    print(traceback.format_exc())

        update.check_version()

        # try:
        #     print("--- Sync of slash commands: ---")
        #     await self.tree.sync()
        #     print(f"Slash commands synced\n")
        # except Exception as e:
        #     print("Error:", e, "\n")


    async def on_ready(self) -> None:
        print("\n--- Bot info: ---")
        print(f"Logging As {self.user} ({self.user.id})")
        print(f"{self.user} is in {len(bot.guilds)} server")
        print(f"discord.py version: {discord.__version__}")
        print(f"Python Version: {sys.version}")
        print("--------------\n")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='/help'))


async def get_prefix(self, message: discord.Message):
    setting = function.db.find_one(function.Setting, message.guild.id)
    if setting is None:
        function.db.set_settings(message.guild.id)
        prefix = "+"
    else:
        prefix = setting.prefix
    return prefix


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = FLAYX(command_prefix=get_prefix,
            help_command=None,
            intents=intents,
            activity=discord.Activity(type=discord.ActivityType.listening, name='Starting...')
            )
if __name__ == "__main__":
    print(" _____ __    _____ __ __ __ __ ")
    print("|   __|  |  |  _  |  |  |  |  |")
    print("|   __|  |__|     |_   _|-   -|")
    print("|__|  |_____|__|__| |_| |__|__|\n")
    update.check_version(with_msg=True)
    bot.run(function.TOKEN) #, log_handler=None