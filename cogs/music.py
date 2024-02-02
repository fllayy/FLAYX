import pomice
import math
from discord.ext import commands
import discord
from discord import app_commands
from views.paginator import PaginationMenu
from views.help import HelpView
import function
from typing import List
from voicelink.player import Player
import asyncio
import time


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.pomice = pomice.NodePool()

        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        await self.pomice.create_node(
            bot=self.bot,
            host=function.LAVALINK_HOST,
            port=int(function.LAVALINK_PORT),
            password=function.LAVALINK_PASSWORD,
            identifier="MAIN",
        )
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

        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members


    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: pomice.Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: pomice.Player, track, _):
        try:
            await player.context.send(f"Please wait for 10 seconds.", delete_after=10)
            await asyncio.sleep(10)
        except Exception:
            pass
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: pomice.Player, track, _):
        try:
            await player.context.send(f"Please wait for 10 seconds.", delete_after=10)
            await asyncio.sleep(10)
        except Exception:
            pass
        await player.do_next()



    @commands.hybrid_command(name='help', with_app_command = True, description = "Lists all the commands in FLAYX.")
    async def help(self, ctx: commands.Context) -> None:
        "Lists all the commands in FLAYX."
        category = "News"
        view = HelpView(self.bot, ctx.author)
        embed = view.build_embed(category)
        message = await ctx.send(embed=embed, view=view)
        view.response = message



    @commands.hybrid_command(name='ping', with_app_command = True, description = "Test if the bot is alive, and see the delay between your commands and my response.")
    async def ping(self, ctx: commands.Context):
        "Test if the bot is alive, and see the delay between your commands and my response."
        embed = discord.Embed()
        botPing = self.bot.latency
        if botPing > 5: botemoji = '😭'
        elif botPing > 1: botemoji = '😨'
        else: botemoji = '👌'
        nodePing = (self.pomice.nodes['MAIN'].latency)/1000
        if nodePing > 5: nodeemoji = '😭'
        elif nodePing > 1: nodeemoji = '😨'
        else: nodeemoji = '👌'
        dbPing = function.db.ping_mysql()
        if dbPing > 5: dbemoji = '😭'
        elif dbPing > 1: dbemoji = '😨'
        else: dbemoji = '👌'
        embed.add_field(name='Bot info:', value=f"```Bot: {botPing:.3f}s {botemoji}\nNode: {nodePing:.3f}s {nodeemoji}\nDatabase: {dbPing:.3f}s {dbemoji}```")
        await ctx.send(embed=embed)


    @commands.hybrid_command(name='play', with_app_command = True, description = "Play a song")
    @app_commands.describe(search="Input a query or a searchable link.")
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        if not ctx.author.voice:
            return await ctx.reply("You must be in a voice channel.", delete_after=7)
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

        results = await player.get_tracks(search, ctx=ctx)

        if not results:
            return await ctx.reply("No results were found for that search term", delete_after=7)

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                player.queue.put(track)
            await ctx.reply(f"Added **[{track.title}](<{track.uri}>)** [`{function.convertMs(track.length)}`] is add to queue.")
        else:
            track = results[0]
            await ctx.reply(f"Added **[{track.title}](<{track.uri}>)** [`{function.convertMs(track.length)}`] is add to queue.")
            player.queue.put(track)


        if not player.is_playing:
            await player.do_next()

        if len(player.history) >= 5:
            player.history.pop(0)
        player.history.append(player.current)

    
    @commands.hybrid_command(name='stop', with_app_command = True, description = "Stop the player")
    async def stop(self, ctx: commands.Context) -> None:
        if not (player := ctx.voice_client):
            return await ctx.reply(
            "You must have the bot in a channel in order to use this command",
            delete_after=7,
            )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.reply("Player has been stopped.", delete_after=10)
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send("Vote to stop passed. Stopping the player.", delete_after=10)
            await player.teardown()
        else:
            await ctx.send(
            f"{ctx.author.mention} has voted to stop the player. Votes: {len(player.stop_votes)}/{required}",
            delete_after=15,
            )


    @commands.hybrid_command(name='skip', with_app_command = True, description = "Skip the currently playing song")
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the currently playing song."""
        if not (player := ctx.voice_client):
            return await ctx.reply(
            "You must have the bot in a channel in order to use this command",
            delete_after=7,
            )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.reply("Song has been skipped.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.reply("The song requester has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send("Vote to skip passed. Skipping song.", delete_after=10)
            player.skip_votes.clear()
            await player.stop()
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
                "The bot is not in a voice channel.",
                delete_after=7,
            )

        if not player.is_connected:
            return await ctx.reply(
                "The bot must be in a voice channel to shuffle the queue.",
                delete_after=7,
            )

        if len(player.queue.get_queue()) < 3:
            return await ctx.reply(
                "The queue must have at least 3 tracks to be shuffled.",
                delete_after=15,
            )
        
        if self.is_privileged(ctx):
            player.queue.shuffle()
            await ctx.reply("The queue has been shuffled.")
            return player.queue.shuffle()

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send("Vote to shuffle passed. Shuffle queue.", delete_after=10)
            player.shuffle_votes.clear()
            await player.queue.shuffle()
        else:
            await ctx.send(
            f"{ctx.author.mention} has voted to shuffle the queue. Votes: {len(player.shuffle_votes)}/{required} ",
            delete_after=15,
            )



    @commands.hybrid_command(name='queue', with_app_command=True, description="View the queue of songs")
    async def queue(self, ctx: commands.Context):
        if not (player := ctx.voice_client):
            return await ctx.reply(
            "You must have the bot in a channel in order to use this command",
            delete_after=7,
            )
        
        if len(player.queue.get_queue()) < 1:
            return await ctx.reply(
                "Queue is empty.",
                delete_after=15,
            )
        
        player: Player = ctx.voice_client
        queue_list = player.queue.get_queue()
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

    
    @commands.hybrid_command(name='pause', with_app_command=True, description="Pause the currently playing song.")
    async def pause(self, ctx: commands.Context):
        """Pause the currently playing song."""
        if not (player := ctx.voice_client):
            return await ctx.reply(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )

        if player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.reply("The player has been paused", delete_after=10)
            player.pause_votes.clear()

            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send("Vote to pause passed. Pausing player.", delete_after=10)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.reply(
                f"{ctx.author.mention} has voted to pause the player. Votes: {len(player.pause_votes)}/{required}",
                delete_after=15,
            )


    @commands.hybrid_command(name='resume', with_app_command=True, description="Resume a currently paused player.")
    async def resume(self, ctx: commands.Context):
        """Resume a currently paused player."""
        if not (player := ctx.voice_client):
            return await ctx.reply(
                "You must have the bot in a channel in order to use this command",
                delete_after=7,
            )

        if not player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.reply("The player has been resumed.", delete_after=10)
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send("Vote to resume passed. Resuming player.", delete_after=10)
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.reply(
                f"{ctx.author.mention} has voted to resume the player. Votes: {len(player.resume_votes)}/{required}",
                delete_after=15,
            )


    @commands.hybrid_command(name='playtop', with_app_command=True, description="Put the song at top of the queue")
    @app_commands.describe(search="Input a query or a searchable link.")
    async def playtop(self, ctx: commands.Context, *, search: str) -> None:
        if not ctx.author.voice:
            return await ctx.reply("You must be in a voice channel.", delete_after=7)
        else:
            if not (player := ctx.voice_client):
                await ctx.author.voice.channel.connect(cls=Player)
                player: Player = ctx.voice_client
                await player.set_context(ctx=ctx)

        if self.is_privileged(ctx):
            results = await player.get_tracks(search, ctx=ctx)

            if not results:
                return await ctx.reply("No results were found for that search term", delete_after=7)

            if isinstance(results, pomice.Playlist):
                for track in results.tracks:
                    player.queue.put_at_front(track)
            else:
                track = results[0]
                player.queue.put_at_front(track)

            await ctx.reply(f"Added **[{track.title}](<{track.uri}>)** [`{function.convertMs(track.length)}`] is add to top of the queue.")

            if not player.is_playing:
                await player.do_next()

            if len(player.history) >= 5:
                player.history.pop(0)
            player.history.append(player.current)
        else:
            return await ctx.reply("You must be an admin or dj")



    @commands.hybrid_command(name='playnow', with_app_command=True, description="Play the song RIGHT NOW")
    @app_commands.describe(search="Input a query or a searchable link.")
    async def playnow(self, ctx: commands.Context, *, search: str) -> None:
        if not ctx.author.voice:
            return await ctx.reply("You must be in a voice channel.", delete_after=7)
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

        if self.is_privileged(ctx):

            results = await player.get_tracks(search, ctx=ctx)

            if not results:
                return await ctx.reply("No results were found for that search term", delete_after=7)

            if isinstance(results, pomice.Playlist):
                for track in results.tracks:
                    player.queue.put_at_front(track)
                await player.stop()
            else:
                track = results[0]
                player.queue.put_at_front(track)
                await player.stop()

            await ctx.reply(f"Play **[{track.title}](<{track.uri}>)** [`{function.convertMs(track.length)}`] now.")

            if not player.is_playing:
                await player.do_next()

            if len(player.history) >= 5:
                player.history.pop(0)
            player.history.append(player.current)
        
        else:
            return await ctx.reply("You must be an admin or dj")



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
                "The bot is not in a voice channel.",
                delete_after=7,
            )

        if not player.is_connected:
            return await ctx.reply(
                "The bot must be in a voice channel to set a loop mode.",
                delete_after=7,
            )

        mode = mode.lower()
        loop_mode = {
            "track": pomice.LoopMode.TRACK,
            "queue": pomice.LoopMode.QUEUE
        }
        if mode not in loop_mode and mode != "off":
            return await ctx.reply(
                "This loop mode does not exist.",
                delete_after=15,
            )

        if len(player.queue.get_queue()) < 1 and mode == "queue":
            return await ctx.reply(
                "The queue must have at least 1 tracks to be looped.",
                delete_after=15,
            )
        
        if mode == "off":
            if self.is_privileged(ctx):
                player.queue.disable_loop()
                return await ctx.reply("loop has been stoped.")
            
            required = self.required(ctx)
            player.loop_votes.add(ctx.author)

            if len(player.skip_votes) >= required:
                await ctx.send("Vote to stop the loop passed.", delete_after=10)
                player.loop_votes.clear()
                return await player.queue.disable_loop()
            else:
                await ctx.send(
                f"{ctx.author.mention} has voted to stop the loop. Votes: {len(player.loop_votes)}/{required} ",
                delete_after=15,
                )

        else:
            if self.is_privileged(ctx):
                player.queue.set_loop_mode(loop_mode[mode])
                return await ctx.reply("queue/track is looped.")


            required = self.required(ctx)
            player.loop_votes.add(ctx.author)

            if len(player.skip_votes) >= required:
                await ctx.send("Vote to loop passed.", delete_after=10)
                player.loop_votes.clear()
                return await player.queue.set_loop_mode(loop_mode[mode])
            else:
                await ctx.send(
                f"{ctx.author.mention} has voted to loop. Votes: {len(player.loop_votes)}/{required} ",
                delete_after=15,
                )


    @commands.hybrid_command(name='remove', with_app_command = True, description = "Remove a song from the queue")
    @app_commands.describe(index="Index of the song in the queue.")
    async def remove(self, ctx: commands.Context, *, index: int) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                "The bot is not in a voice channel.",
                delete_after=7,
            )

        if not player.is_connected:
            return await ctx.reply(
                "The bot must be in a voice channel to set a loop mode.",
                delete_after=7,
            )
        
        if player.queue.size < index or index < 1:
            return await ctx.reply(
                "This index is not in the queue.",
                delete_after=7,
            )
        
        track = player.queue[index - 1]
        if self.is_privileged(ctx):
            player.queue.remove(track)
            await ctx.reply(f"The track `[{track.title}](<{track.uri}>)` is removed from the queue.")
        else:
            await ctx.reply("You don't have permission to do this.")

    
    @commands.hybrid_command(name='clear', with_app_command = True, description = "clear the queue")
    async def clear(self, ctx: commands.Context) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                "The bot is not in a voice channel.",
                delete_after=7,
            )

        if not player.is_connected:
            return await ctx.reply(
                "The bot must be in a voice channel to set a loop mode.",
                delete_after=7,
            )
        
        if player.queue.size < 1:
            return await ctx.reply(
                "This index is not in the queue.",
                delete_after=7,
            )
        
        if self.is_privileged(ctx):
            player.queue.clear()
            await ctx.reply(f"The queue has been cleaned.")
        else:
            await ctx.reply("You don't have permission to do this.")




    async def autoplay_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        autoplays = ['True', 'False']
        return [app_commands.Choice(name=autoplay, value=autoplay) for autoplay in autoplays]
    

    @commands.hybrid_command(name='autoplay', with_app_command = True, description = "Toggle autoplay.")
    @app_commands.autocomplete(status=autoplay_autocomplete)
    @app_commands.describe(status="True or False.")
    async def autoplay(self, ctx: commands.Context, *, status) -> None:
        player: Player = ctx.voice_client

        if not player:
            return await ctx.reply(
                "The bot is not in a voice channel.",
                delete_after=7,
            )

        if not player.is_connected:
            return await ctx.reply(
                "The bot must be in a voice channel to set autoplay mode.",
                delete_after=7,
            )
        
        if status == "False":
            status = 0
        else:
            status = 1
        status = bool(status)
        
        if self.is_privileged(ctx):
            player.autoplay = status
            await ctx.reply(f"Autoplay is now on {player.autoplay}.")
        else:
            await ctx.reply("You don't have permission to do this.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))