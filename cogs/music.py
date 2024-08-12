import wavelink
import math
from discord.ext import commands
import discord
from discord import app_commands
import function
import asyncio
import time
from views.player import MusicControlsView
from views.paginator import PaginationMenu


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()
        self.loop_votes = set()
        self.inactive_timeout = 300
        self.now_playing_message = None

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        node_uri = f"ws://{function.LAVALINK_HOST}:{function.LAVALINK_PORT}"
        nodes = [wavelink.Node(uri=node_uri, password=function.LAVALINK_PASSWORD)]
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)
        print(f"Node is ready!")

    def required(self, ctx: commands.Context):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = ctx.voice_client
        channel = self.bot.get_channel(int(player.channel.id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == "stop":
            if len(channel.members) == 3:
                required = 2

        return required

    def is_privileged(self, ctx: commands.Context):
        """Check whether the user is an Admin or DJ."""
        player: Player = ctx.voice_client
        if ctx.author.guild_permissions.kick_members:
            return True
        elif function.db.find_one(function.Setting, ctx.message.guild.id).dj in [role.id for role in ctx.author.roles]:
            return True
        else:
            return False
    

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: Player | None = payload.player
        if not player:
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        if track.is_stream:
            embed = discord.Embed(
            description = (
                    f":red_circle: **LIVE:**\n\n **[{track.title}]({track.uri})  by `{track.author}`**"
                )
            )
        else:
            embed = discord.Embed(
                description = (
                    f"**Now Playing:**\n\n **[{track.title}]({track.uri}) by `{track.author}`**"
                )
            )

        if track.artwork:
            embed.set_image(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`This track was recommended via {track.source}`"

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)

        embed.set_author(name=f"Music Controller | {player.channel.name}", icon_url=self.bot.user.avatar.url)

        embed.set_footer(
        text=f"Queue Length: {len(player.queue)} | Duration: {function.convertMs(track.length)} | Volume: {player.volume}% | Autoplay: {player.autoplay.name}",
        )

        player.now_playing_message = await player.home.send(embed=embed, view=MusicControlsView())

    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player: Player | None = payload.player
        if not player:
            return
        
        if player.now_playing_message:
            try:
                await player.now_playing_message.delete()
            except discord.HTTPException:
                pass
            player.now_playing_message = None
        
        if not player.queue.is_empty:
            await player.play(player.queue.get())


    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        player: Player = player
        playerUptime = time.time() - player.start_time
        setting = function.db.find_one(function.Setting, player.guild.id)
        if setting is None:
            function.db.set_settings(player.guild.id)
            previousTime = 0
        else:
            previousTime = setting.time
        newTime = previousTime + playerUptime
        function.db.update_one(function.Setting, player.guild.id, {"time": newTime})
        await player.disconnect()


    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload):
        player = payload.player
        try:
            await player.home.send(f"Please wait for 10 seconds.", delete_after=10)
            await asyncio.sleep(10)
        except Exception as e:
            print("Error: ", e)
        await player.stop()


    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        player = payload.player
        try:
            await player.home.send(f"Please wait for 10 seconds.", delete_after=10)
            await asyncio.sleep(10)
        except Exception as e:
            print("Error: ", e)
        await player.stop()

    
    async def source_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        souces = ['Youtube', 'YoutubeMusic', 'SoundCloud']
        return [app_commands.Choice(name=souce, value=souce) for souce in souces]

    @commands.hybrid_command(name='play', with_app_command=True, description="Play a song")
    @app_commands.autocomplete(source=source_autocomplete)
    @app_commands.describe(search="Input a query or a searchable link.")
    async def play(self, ctx: commands.Context, *, search: str, source = "Youtube") -> None:
        if not ctx.guild:
            return
        
        player: Player = ctx.voice_client  # type: ignore

        sources = {
            "Youtube": wavelink.TrackSource.YouTube,
            "YoutubeMusic": wavelink.TrackSource.YouTubeMusic,
            "SoundCloud": wavelink.TrackSource.SoundCloud
        }

        if source not in sources:
            await ctx.reply(embed=discord.Embed(description="This is not a valid mode.", color=discord.Color.red()))

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=Player)  # type: ignore
            except AttributeError:
                return await ctx.reply(embed=discord.Embed(description="Please join a voice channel first before using this command.", color=discord.Color.yellow()))
            except discord.ClientException:
                return await ctx.reply(embed=discord.Embed(description="I was unable to join this voice channel. Please try again.", color=discord.Color.red()))

        player.autoplay = wavelink.AutoPlayMode.disabled

        if not hasattr(player, "home"):
            player.home = ctx.channel
        elif player.home != ctx.channel:
            await ctx.send(embed=discord.Embed(description=f"You can only play songs in {player.home.mention}, as the player has already started there.", color=discord.Color.red()))
            return
        try:
            tracks: wavelink.Search = await wavelink.Playable.search(search, source=sources[source])
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(description="⚠️ An error occured", color=discord.Color.red()))

        if not tracks:
            return await ctx.reply(embed=discord.Embed(description="No results were found for that search term", color=discord.Color.red()))

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            await ctx.reply(embed=discord.Embed(description=f"Added the playlist **{tracks.name}** ({added} videos) to the queue.", color=discord.Color.green()))
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await ctx.reply(embed=discord.Embed(description=f"Added **[{track.title}](<{track.uri}>)** [`{function.convertMs(track.length)}`] to queue.", color=discord.Color.green()))

        if not player.playing:
            setting = function.db.find_one(function.Setting, ctx.message.guild.id)
            if setting is None:
                function.db.set_settings(ctx.message.guild.id)
                volume = 100
            else:
                volume = setting.volume
            await player.play(player.queue.get(), volume=volume)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass


    @commands.hybrid_command(name='stop', with_app_command = True, description = "Stop the player")
    async def stop(self, ctx: commands.Context) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )

        if self.is_privileged(ctx):
            await ctx.reply(embed=discord.Embed(description="Player has been stopped.", color=discord.Color.green()), delete_after=10)
            playerUptime = time.time() - player.start_time
            setting = function.db.find_one(function.Setting, ctx.message.guild.id)
            if setting is None:
                function.db.set_settings(ctx.message.guild.id)
                previousTime = 0
            else:
                previousTime = setting.time
            newTime = previousTime + playerUptime
            function.db.update_one(function.Setting, ctx.message.guild.id, {"time": newTime})
            if player.now_playing_message:
                try:
                    await player.now_playing_message.delete()
                except discord.HTTPException:
                    pass
                player.now_playing_message = None
            return await player.disconnect()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send(embed=discord.Embed(description="Vote to stop passed. Stopping the player.", color=discord.Color.green()), delete_after=10)
            playerUptime = time.time() - player.start_time
            setting = function.db.find_one(function.Setting, ctx.message.guild.id)
            if setting is None:
                function.db.set_settings(ctx.message.guild.id)
                previousTime = 0
            else:
                previousTime = setting.time
            newTime = previousTime + playerUptime
            function.db.update_one(function.Setting, ctx.message.guild.id, {"time": newTime})
            if player.now_playing_message:
                try:
                    await player.now_playing_message.delete()
                except discord.HTTPException:
                    pass
                player.now_playing_message = None
            await player.disconnect()
        else:
            await ctx.send(
            f"{ctx.author.mention} has voted to stop the player. Votes: {len(player.stop_votes)}/{required}",
            delete_after=15,
            )


    @commands.hybrid_command(name='skip', with_app_command = True, description = "Skip the currently playing song")
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the currently playing song."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            ) 

        if self.is_privileged(ctx):
            await ctx.reply(embed=discord.Embed(description="Song has been skipped.", color=discord.Color.green()), delete_after=10)
            player.skip_votes.clear()
            await player.skip(force=True)

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send(embed=discord.Embed(description="Vote to skip passed. Skipping song.", color=discord.Color.green()), delete_after=10)
            player.skip_votes.clear()
            await player.skip(force=True)
        else:
            await ctx.send(
            f"{ctx.author.mention} has voted to skip the song. Votes: {len(player.skip_votes)}/{required} ",
            delete_after=15,
            )


    @commands.hybrid_command(name='shuffle', with_app_command=True, description="Shuffle the players queue")
    async def shuffle(self, ctx: commands.Context) -> None:
        """Shuffle the players queue."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )

        if len(player.queue) < 3:
            return await ctx.reply(
                "The queue must have at least 3 tracks to be shuffled.",
                delete_after=15,
            )
        
        if self.is_privileged(ctx):
            player.queue.shuffle()
            await ctx.reply(embed=discord.Embed(description="The queue has been shuffled.", color=discord.Color.green()))
            return player.queue.shuffle()

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send(embed=discord.Embed(description="Vote to shuffle passed. Shuffle queue.", color=discord.Color.green()), delete_after=10)
            player.shuffle_votes.clear()
            await player.queue.shuffle()
        else:
            await ctx.send(
            f"{ctx.author.mention} has voted to shuffle the queue. Votes: {len(player.shuffle_votes)}/{required} ",
            delete_after=15,
            )



    @commands.hybrid_command(name='queue', with_app_command=True, description="View the queue of songs")
    async def queue(self, ctx: commands.Context):
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )
        
        if player.queue.count < 1:
            return await ctx.reply(
                embed=discord.Embed(description="Queue is empty.", color=discord.Color.green()),
                delete_after=15,
            )
        
        player: Player = ctx.voice_client
        queue_list = player.queue
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

    
    @commands.hybrid_command(name='pause', with_app_command=True, description="Pause the currently playing song.")
    async def pause(self, ctx: commands.Context):
        """Pause the currently playing song."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )

        if player.paused or not player.playing:
            return

        if self.is_privileged(ctx):
            await ctx.reply(embed=discord.Embed(description="The player has been paused", color=discord.Color.green()), delete_after=10)
            player.pause_votes.clear()

            return await player.pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            player.pause_votes.clear()
            await player.pause(True)
            await ctx.reply(embed=discord.Embed(description="Vote to pause passed. Pausing player.", color=discord.Color.green()), delete_after=10)
        else:
            await ctx.reply(
                f"{ctx.author.mention} has voted to pause the player. Votes: {len(player.pause_votes)}/{required}",
                delete_after=15,
            )


    @commands.hybrid_command(name='resume', with_app_command=True, description="Resume a currently paused player.")
    async def resume(self, ctx: commands.Context):
        """Resume a currently paused player."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )

        if not player.paused or not player.playing:
            return

        if self.is_privileged(ctx):
            await ctx.reply(embed=discord.Embed(description="The player has been resumed.", color=discord.Color.green()), delete_after=10)
            player.resume_votes.clear()

            return await player.pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            player.resume_votes.clear()
            await player.pause(False)
            await ctx.reply(embed=discord.Embed(description="Vote to resume passed. Resuming player.", color=discord.Color.green()), delete_after=10)
        else:
            await ctx.reply(
                f"{ctx.author.mention} has voted to resume the player. Votes: {len(player.resume_votes)}/{required}",
                delete_after=15,
            )


    async def loop_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        loops = ['Track', 'Queue', 'Off']
        return [app_commands.Choice(name=loop, value=loop) for loop in loops]


    @commands.hybrid_command(name='loop', with_app_command=True, description="Loop the queue/song.")
    @app_commands.autocomplete(mode=loop_autocomplete)
    @app_commands.describe(mode="Type of loop.")
    async def loop(self, ctx: commands.Context, mode: str) -> None:
        """loop the players queue."""
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )

        mode = mode.lower()
        loop_mode = {
            "track": wavelink.QueueMode.loop,
            "queue": wavelink.QueueMode.loop_all,
            "off": wavelink.QueueMode.normal
        }

        if mode not in loop_mode:
            return await ctx.reply(
                embed=discord.Embed(description="This loop mode does not exist.", color=discord.Color.red()),
                delete_after=15,
            )

        if player.queue.count < 1 and mode == "queue":
            return await ctx.reply(
                embed=discord.Embed(description="The queue must have at least 1 tracks to be looped.", color=discord.Color.red()),
                delete_after=15,
            )
        

        if self.is_privileged(ctx):
            player.queue.mode = loop_mode[mode]
            await player.queue.put_wait(player.current)
            return await ctx.reply(embed=discord.Embed(description=f"loop is on `{mode}`", color=discord.Color.green()))
        
        required = self.required(ctx)
        player.loop_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            player.loop_votes.clear()
            await player.queue.put_wait(player.current)
            player.queue.mode = loop_mode[mode]
            return await ctx.send(embed=discord.Embed(description=f"Vote to put loop on `{mode}` passed.", color=discord.Color.green()), delete_after=10)
        else:
            await ctx.send(
            f"{ctx.author.mention} has voted to put loop on `{mode}`. Votes: {len(player.loop_votes)}/{required} ",
            delete_after=15,
            )


    @commands.hybrid_command(name='remove', with_app_command = True, description = "Remove a song from the queue")
    @app_commands.describe(index="Index of the song in the queue.")
    async def remove(self, ctx: commands.Context, *, index: int) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )
        
        if player.queue.count < index or index < 1:
            return await ctx.reply(
                embed=discord.Embed(description="This index is not in the queue.", color=discord.Color.red()),
                delete_after=7,
            )
        
        track = player.queue[index - 1]
        if self.is_privileged(ctx):
            player.queue.remove(track)
            await ctx.reply(embed=discord.Embed(description=f"The track **[{track.title}](<{track.uri}>)** is removed from the queue.", color=discord.Color.green()))
        else:
            await ctx.reply(embed=discord.Embed(description="You don't have permission to do this.", color=discord.Color.red()))

    
    @commands.hybrid_command(name='clear', with_app_command = True, description = "clear the queue")
    async def clear(self, ctx: commands.Context) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )
        
        if player.queue.count < 1:
            return await ctx.reply(
                embed=discord.Embed(description="The queue is empty.", color=discord.Color.red()),
                delete_after=7,
            )
        
        if self.is_privileged(ctx):
            player.queue.clear()
            await ctx.reply(embed=discord.Embed(description="The queue has been cleaned.", color=discord.Color.green()))
        else:
            await ctx.reply(embed=discord.Embed(description="You don't have permission to do this.", color=discord.Color.red()))



    async def autoplay_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        autoplays = ['Enable', 'Disable']
        return [app_commands.Choice(name=autoplay, value=autoplay) for autoplay in autoplays]
    

    @commands.hybrid_command(name='autoplay', with_app_command = True, description = "Toggle autoplay.")
    @app_commands.autocomplete(status=autoplay_autocomplete)
    @app_commands.describe(status="Enable or Disable.")
    async def autoplay(self, ctx: commands.Context, *, status) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                embed=discord.Embed(description="The bot is not in a voice channel.", color=discord.Color.red()),
                delete_after=7,
            )
        
        autoplay_mode = {
            "Enable": wavelink.AutoPlayMode.enabled,
            "Disable": wavelink.AutoPlayMode.disabled
        }

        if status not in autoplay_mode:
            await ctx.reply(embed=discord.Embed(description="This is not a valid mode.", color=discord.Color.red()))
        
        
        if self.is_privileged(ctx):
            player.autoplay = autoplay_mode[status]
            await ctx.reply(embed=discord.Embed(description=f"Autoplay is now {status}.", color=discord.Color.green()))
        else:
            await ctx.reply(embed=discord.Embed(description="You don't have permission to do this.", color=discord.Color.red()))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))