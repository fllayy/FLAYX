from discord.ext import commands
import discord
from discord import app_commands
from voicelink.player import Player
import function


class Playlist(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.hybrid_command(name='playlist', with_app_command = True, description = "playlist test")
    async def playlist(self, ctx: commands.Context):
        "playlist test"
        rank = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)
        else:
            return await ctx.reply(rank)
            


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlist(bot))