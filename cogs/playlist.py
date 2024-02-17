from discord.ext import commands
import discord
from discord import app_commands
from voicelink.player import Player
import function
from views.help import HelpView
import pomice
from views.paginator import PaginationMenu


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

        playlist = function.db.find_one("playlist", ctx.author.id, "tracks")

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
                if len(playlist.split(',')) >= maxTrack:
                    await ctx.reply("You playlist is full", ephemeral=True)
                playlist = playlist + track[0].uri + ","
                function.db.update_one("playlist", "tracks", playlist, ctx.author.id)

            await ctx.reply(f"**[{track[0].title}](<{track[0].uri}>)** is added to **❤️**", ephemeral=True)

        
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
            await ctx.reply(f"**[{track[0].title}](<{track[0].uri}>)** is removed from **❤️**", ephemeral=True)
        except Exception as e:
            print("Error on remove song from playlist:", e)
            await ctx.reply("An error occured", ephemeral=True)


    @playlist.command(name="play", with_app_command = True, description = "Play your playlist")
    async def play(self, ctx: commands.Context):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)

        playlist = function.db.find_one("playlist", ctx.author.id, "tracks")
        playlist = playlist.split(",")
        playlist.pop()

        if not ctx.author.voice:
            return await ctx.reply("You must be in a voice channel.", delete_after=7)
        elif len(playlist) <= 0:
            return await ctx.reply("Your playlist is empty.", delete_after=7)
        else:
            if not (player := ctx.voice_client):
                await ctx.author.voice.channel.connect(cls=Player)
                player: Player = ctx.voice_client
                volume = function.db.find_one("settings", ctx.message.guild.id, "volume")
                if volume == None:
                    function.db.set_settings(ctx.message.guild.id)
                    volume = 100
                await player.set_volume(volume=volume)
                await player.set_context(ctx=ctx)

        for uri in playlist:
            track = await player.get_tracks(query=uri, ctx=ctx)
            player.queue.put(track[0])
        await ctx.reply("You play the playlist **❤️**")

        if not player.is_playing:
            await player.do_next()

        if len(player.history) >= 5:
            player.history.pop(0)
        player.history.append(player.current)


    @playlist.command(name="show", with_app_command = True, description = "Show your playlist")
    async def show(self, ctx: commands.Context):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank == None:
            await function.create_account(ctx)

        playlist = function.db.find_one("playlist", ctx.author.id, "tracks")
        playlist = playlist.split(",")
        playlist.pop()

        if len(playlist) <= 0:
            return await ctx.reply("Your playlist is empty.", delete_after=7)

        queue_list = []

        node = pomice.NodePool.get_node()

        for tracks in playlist:
            track = await node.get_tracks(query=tracks, ctx=ctx)
            queue_list.append(track[0])

        pages = []

        for i in range(0, len(queue_list), 15):
            page = queue_list[i:i + 15]
            page_content = []

            for index, track in enumerate(page, start=i + 1):
                time = function.convertMs(track.length)
                truncated_title = track.title[:25] if len(track.title) > 25 else track.title
                if track.requester == None:
                    track.requester = self.bot.user
                page_content.append(f"`{index}.` `[{time}]` [{truncated_title}]({track.uri}) {track.requester.mention}")

            pages.append("\n".join(page_content))

        
        menu = PaginationMenu(ctx, pages)
        await menu.show_page()
            


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlist(bot))