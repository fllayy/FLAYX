from discord.ext import commands
import discord
from discord import app_commands
from voicelink.player import Player
import function
from views.help import HelpView
import pomice


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
    @app_commands.describe(name="Name or link of the song.")
    async def add(self, ctx: commands.Context, name):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)

        track = await pomice.NodePool.get_node().get_tracks(query=name, ctx=ctx)

        if track == None:
            await ctx.reply("Track was not found", ephemeral=True)
        elif track[0].is_stream:
            await ctx.reply("Can't add stream to playlist", ephemeral=True)
        else:
            playlist = function.db.find_one("playlist", ctx.author.id, "tracks")

            if playlist == "":
                playlist = track[0].uri + ','
                function.db.update_one("playlist", "tracks", playlist, ctx.author.id)
            else:
                playlist = playlist + track[0].uri + ","
                function.db.update_one("playlist", "tracks", playlist, ctx.author.id)

            await ctx.reply(f"**[{track[0].title}](<{track[0].uri}>)** is added to ❤️", ephemeral=True)

        
    @playlist.command(name="remove", with_app_command = True, description = "Remove a song to your playlist")
    @app_commands.describe(link="Link of the song.")
    async def remove(self, ctx: commands.Context, link):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)

        track = await pomice.NodePool.get_node().get_tracks(query=link, ctx=ctx)
        
        playlist = function.db.find_one("playlist", ctx.author.id, "tracks")

        try:
            playlist = playlist.replace(track[0].uri+',', "")
            function.db.update_one("playlist", "tracks", playlist, ctx.author.id)
            await ctx.reply(f"**[{track[0].title}](<{track[0].uri}>)** is removed from ❤️", ephemeral=True)
        except Exception as e:
            print("Error on remove song from playlist:", e)
            await ctx.reply("An error occured", ephemeral=True)

    @playlist.command(name="play", with_app_command = True, description = "Play your playlist")
    async def play(self, ctx: commands.Context):
        pass #todo


    @playlist.command(name="show", with_app_command = True, description = "Show your playlist")
    async def show(self, ctx: commands.Context):
        pass #todo
            


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlist(bot))