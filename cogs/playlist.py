from discord.ext import commands
import discord
from discord import app_commands
from voicelink.player import Player
import function
from views.help import HelpView


class Playlist(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="playlist",
        invoke_without_command=True
    )

    async def playlist(self, ctx: commands.Context):
        view = HelpView(self.bot, ctx.author)
        embed = view.build_embed(self.qualified_name)
        message = await ctx.send(embed=embed, view=view)
        view.response = message


    @playlist.command(name='rank', with_app_command = True, description = "playlist test")
    async def rank(self, ctx: commands.Context):
        rank = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)
        else:
            return await ctx.reply(f"Your rank is `{rank}`")
            


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlist(bot))


#playlist create
#playlist delete
#playlist add
#playlist remove
#playlist see