import pomice
import discord
from discord.ext import commands
from contextlib import suppress
import function
from discord.ui import View
from views.player import MusicControlsView
import time

class Player(pomice.Player):
    """Custom pomice Player class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.queue = pomice.Queue()
        self.controller: discord.Message = None
        self.context: commands.Context = None
        self.voicechannel: discord.VoiceChannel = None
        self.dj: discord.Member = None
        self.autoplay: bool = False
        self.track = None
        self.history: list = []
        self.joinTime: int = round(time.time())

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()
        self.loop_votes = set()

    async def do_next(self) -> None:
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()
        self.loop_votes.clear()

        if self.controller:
            with suppress(discord.HTTPException):
                await self.controller.delete()

        try:
            track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            if self.autoplay and len(self.voicechannel.members) > 1:
                new = await self.get_recommendations(track=self.track)
                for track in new.tracks:
                    if track != self.track and track not in self.history:
                        newtrack = track
                        break
                self.track = newtrack
                if len(self.history) >= 5:
                    self.history.pop(0)
                self.history.append(self.track)
            else:
                return await self.teardown()

        await self.play(track)

        if track.requester == None:
            track.requester = self.bot.user


        if track.is_stream:
            embed = discord.Embed(
            description = (
                    f":red_circle: **LIVE: ```{track.title}```**\n"
                    f"**Link: [Click Me]({track.uri}) | Requester: {track.requester.mention}**"
                )
            )
        else:
            embed = discord.Embed(
                description = (
                    f"**Now Playing: ```{track.title}```\n"
                    f"Link: [Click Me]({track.uri}) | Requester: {track.requester.mention}**"
                )
            )

        if track.thumbnail:
            embed.set_image(url=track.thumbnail)

        embed.set_author(name=f"Music Controller | {self.context.author.voice.channel.name}", icon_url=self.bot.user.avatar.url)

        embed.set_footer(
        text=f"Queue Length: {len(self.queue)} | Duration: {function.convertMs(track.length)} | Volume: {self.volume}%",
        )

        self.controller = await self.context.send(embed=embed, view=MusicControlsView(self))

        

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        with suppress((discord.HTTPException), (KeyError)):
            actualTime = function.db.find_one("settings", self.context.message.guild.id, "time")
            timePlayed = actualTime + (round(time.time()) - self.joinTime)
            function.db.update_one("settings", "time", timePlayed, self.context.message.guild.id)
            await self.destroy()
            if self.controller:
                await self.controller.delete()
            


    async def set_context(self, ctx: commands.Context):
        """Set context for the player"""
        self.context = ctx
        self.voicechannel = ctx.author.voice.channel
        self.dj = ctx.author