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


    @playlist.command(name="rank", with_app_command = True, description = "Show your rank level.")
    async def rank(self, ctx: commands.Context):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)
        else:
            return await ctx.reply(f"Your rank is `{rank}` ({maxTrack} tracks per playlist)")


    @playlist.command(name="add", with_app_command = True, description = "Add a song to your playlist")
    @app_commands.describe(link="Link of the song.")
    async def add(self, ctx: commands.Context, link):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)

        actual = function.db.find_one("playlist", ctx.author.id, "tracks")
        if actual == "":
            actual = link + ','
            print(actual)
            function.db.update_one("playlist", "tracks", actual, ctx.author.id)
        else:
            actual = actual.split(',')
            actual[len(actual)-1] = link
            actual = (str(actual)).replace("[", "")
            actual = actual.replace("]", "")
            print(actual)
            function.db.update_one("playlist", "tracks", actual, ctx.author.id)


    @playlist.command(name="remove", with_app_command = True, description = "Remove a song to your playlist")
    async def remove(self, ctx: commands.Context):
        pass #todo


    @playlist.command(name="show", with_app_command = True, description = "Show your playlist")
    async def show(self, ctx: commands.Context):
        pass #todo
            


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlist(bot))