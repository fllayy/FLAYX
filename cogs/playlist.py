from discord.ext import commands
import discord
from discord import app_commands
import function
from views.help import HelpView
import wavelink
from views.paginator import PaginationMenu
from cogs.music import Player

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
            return await function.create_account(ctx)

        playlist = function.db.find_one(function.Playlist, ctx.author.id)

        track_results: wavelink.Search = await wavelink.Playable.search(name)

        if not track_results:
            return await ctx.reply("Track was not found", ephemeral=True)

        if isinstance(track_results, wavelink.Playlist):
            return await ctx.reply("Can't add playlist to playlist", ephemeral=True)

        track: wavelink.Playable = track_results[0]
        if track.is_stream:
            return await ctx.reply("Can't add stream to playlist", ephemeral=True)

        if track.uri in playlist.tracks.split(','):
            return await ctx.reply("This is already in your playlist", ephemeral=True)

        if len(playlist.tracks.split(',')) >= maxTrack:
            return await ctx.reply("Your playlist is full", ephemeral=True)

        if playlist.tracks == "":
            new_tracks = track.uri + ','
        else:
            new_tracks = playlist.tracks + track.uri + ','

        function.db.update_one(function.Playlist, ctx.author.id, {"tracks": new_tracks})
        await ctx.reply(f"**[{track.title}](<{track.uri}>)** is added to **❤️**", ephemeral=True)

        
    @playlist.command(name="remove", with_app_command = True, description = "Remove a song to your playlist")
    @app_commands.describe(name="Link of the song.")
    async def remove(self, ctx: commands.Context, name: str):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank is None:
            await function.create_account(ctx)

        track_results: wavelink.Search = await wavelink.Playable.search(name)
        
        if not track_results:
            return await ctx.reply("Track was not found", ephemeral=True)

        track: wavelink.Playable = track_results[0]

        playlist = function.db.find_one(function.Playlist, ctx.author.id)

        if playlist is None or track.uri not in playlist.tracks.split(','):
            await ctx.reply("This is not in your playlist.", ephemeral=True)
            return

        try:
            new_tracks = playlist.tracks.replace(track.uri + ',', "")
            function.db.update_one(function.Playlist, ctx.author.id, {"tracks": new_tracks})
            await ctx.reply(f"**[{track.title}](<{track.uri}>)** is removed from **❤️**", ephemeral=True)
        except Exception as e:
            print("Error on remove song from playlist:", e)
            await ctx.reply("An error occurred", ephemeral=True)


    @playlist.command(name="play", with_app_command = True, description = "Play your playlist")
    async def play(self, ctx: commands.Context):
        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank is None:
            await function.create_account(ctx)

        playlist_entry = function.db.find_one(function.Playlist, ctx.author.id)
        if playlist_entry is None or playlist_entry.tracks == "":
            return await ctx.reply("Your playlist is empty.", delete_after=7)

        playlist = playlist_entry.tracks.split(",")
        if playlist[-1] == "":
            playlist.pop()

        if not ctx.author.voice:
            return await ctx.reply("You must be in a voice channel.", delete_after=7)
        else:
            player: Player = ctx.voice_client

            if not player:
                try:
                    player = await ctx.author.voice.channel.connect(cls=Player)  # type: ignore
                except AttributeError:
                    await ctx.send("Please join a voice channel first before using this command.")
                    return
                except discord.ClientException:
                    await ctx.send("I was unable to join this voice channel. Please try again.")
                    return

            player.autoplay = wavelink.AutoPlayMode.disabled

            if not hasattr(player, "home"):
                player.home = ctx.channel
            elif player.home != ctx.channel:
                await ctx.send(f"You can only play songs in {player.home.mention}, as the player has already started there.")
                return

        for uri in playlist:
            try:
                track_results = await wavelink.Playable.search(uri)
                if not track_results:
                    await ctx.reply(f"Track for URI {uri} was not found.", ephemeral=True)
                    continue
                await player.queue.put_wait(track_results[0])
            except Exception as e:
                await ctx.reply(f"Error retrieving track for URI {uri}, remove the song by doing **/playlist show**", ephemeral=True)
                continue

        if not player.playing:
            setting = function.db.find_one(function.Setting, ctx.message.guild.id)
            if setting is None:
                function.db.set_settings(ctx.message.guild.id)
                volume = 100
            else:
                volume = setting.volume
            await player.play(player.queue.get(), volume=volume)

        await ctx.reply("Playing your playlist **❤️**")


    @playlist.command(name="show", with_app_command = True, description = "Show your playlist")
    async def show(self, ctx: commands.Context):
        await ctx.defer()  # Indicate that the bot is processing the command

        rank, maxTrack = await function.get_user_rank(ctx.author.id)
        if rank is None:
            await function.create_account(ctx)

        playlist_entry = function.db.find_one(function.Playlist, ctx.author.id)
        if playlist_entry is None or playlist_entry.tracks == "":
            return await ctx.reply("Your playlist is empty.", delete_after=7)

        playlist = playlist_entry.tracks.split(",")
        if playlist[-1] == "":
            playlist.pop()  # Remove the last empty element due to trailing comma

        if len(playlist) <= 0:
            return await ctx.reply("Your playlist is empty.", delete_after=7)

        queue_list = []

        uris_to_remove = []

        for track_uri in playlist:
            try:
                track_results = await wavelink.Playable.search(track_uri)
                if not track_results:
                    uris_to_remove.append(track_uri)
                    continue
                queue_list.append(track_results[0])
            except KeyError as e:
                uris_to_remove.append(track_uri)
                continue
            except Exception as e:
                uris_to_remove.append(track_uri)
                continue

        # Remove invalid URIs from the playlist
        if uris_to_remove:
            new_tracks = ','.join([uri for uri in playlist if uri not in uris_to_remove])
            function.db.update_one(function.Playlist, ctx.author.id, {"tracks": new_tracks})

        if not queue_list:
            return await ctx.reply("All tracks in your playlist are invalid or not available.", ephemeral=True)

        pages = []

        for i in range(0, len(queue_list), 15):
            page = queue_list[i:i + 15]
            page_content = []

            for index, track in enumerate(page, start=i + 1):
                time = function.convertMs(track.length)
                truncated_title = track.title[:25] if len(track.title) > 25 else track.title
                page_content.append(f"`{index}.` `[{time}]` [{truncated_title}]({track.uri})")

            pages.append("\n".join(page_content))

        menu = PaginationMenu(ctx, pages)
        await menu.show_page()
            

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlist(bot))