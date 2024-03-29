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
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded {filename[:-3]}")
                except Exception as e:
                    print(traceback.format_exc())

        update.check_version()

        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            print("Error:", e)


    async def on_ready(self) -> None:
        print("------------------")
        print(f"Logging As {self.user}")
        print(f"Bot ID: {self.user.id}")
        print("------------------")
        print(f"Discord Version: {discord.__version__}")
        print(f"Python Version: {sys.version}")
        print("------------------")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='/help'))


async def get_prefix(self, message: Message):
        prefix = function.db.find_one("settings", message.guild.id, "prefix")
        if prefix == None:
            function.db.set_settings(message.guild.id)
            prefix = "+"
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
    update.check_version(with_msg=True)
    bot.run(function.TOKEN) #, log_handler=None