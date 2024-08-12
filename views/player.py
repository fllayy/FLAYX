from discord.ui import View, Button
import discord
import math
import function
import wavelink
import time

class MusicControlsView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Skip", emoji="➡️", style=discord.ButtonStyle.grey, custom_id="skip_button")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip the currently playing song."""
        player = interaction.guild.voice_client

        if not player.playing:
            return

        if interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(embed=discord.Embed(description="Song has been skipped.", color=discord.Color.green()), delete_after=10)
            player.skip_votes.clear()
            return await player.stop()
        elif function.db.find_one(function.Setting, interaction.message.guild.id).dj in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(embed=discord.Embed(description="Song has been skipped.", color=discord.Color.green()), delete_after=10)
            player.skip_votes.clear()
            return await player.stop()

        required = math.ceil((len(interaction.user.voice.channel.members)-1) / 2.5)
        player.skip_votes.add(interaction.user)

        if len(player.skip_votes) >= required:
            await interaction.response.send_message(embed=discord.Embed(description="Vote to skip passed. Skipping song.", color=discord.Color.green()), delete_after=10)
            player.skip_votes.clear()
            await player.stop()
        else:
            await interaction.response.send_message(
            f"{interaction.user.mention} has voted to skip the song. Votes: {len(player.skip_votes)}/{required} ",
            delete_after=15,
            )


    @discord.ui.button(label="Pause/Resume", emoji="⏯️", style=discord.ButtonStyle.grey, custom_id="pause_resume_button")
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client

        if not player.playing:
            return

        if player.paused:
            if interaction.user.guild_permissions.kick_members:
                await interaction.response.send_message(embed=discord.Embed(description="The player has been resumed", color=discord.Color.green()), delete_after=10)
                player.resume_votes.clear()
                return await player.pause(False)
            elif function.db.find_one(function.Setting, interaction.message.guild.id).dj in [role.id for role in interaction.user.roles]:
                await interaction.response.send_message(embed=discord.Embed(description="The player has been resumed", color=discord.Color.green()), delete_after=10)
                player.resume_votes.clear()
                return await player.pause(False)
            
            required = math.ceil((len(interaction.user.voice.channel.members)-1) / 2.5)
            player.resume_votes.add(interaction.user)

            if len(player.resume_votes) >= required:
                await interaction.response.send_message("Vote to resume passed. Resuming player.", delete_after=10)
                player.resume_votes.clear()
                await player.pause(False)
            else:
                await interaction.response.send_message(
                    f"{interaction.user.mention} has voted to resume the player. Votes: {len(player.resume_votes)}/{required}",
                    delete_after=15,
                )
            
        else:
            if interaction.user.guild_permissions.kick_members:
                await interaction.response.send_message(embed=discord.Embed(description="The player has been resumed", color=discord.Color.green()), delete_after=10)
                player.pause_votes.clear()
                return await player.pause(True)
            elif function.db.find_one(function.Setting, interaction.message.guild.id).dj in [role.id for role in interaction.user.roles]:
                await interaction.response.send_message(embed=discord.Embed(description="The player has been resumed", color=discord.Color.green()), delete_after=10)
                player.resume_votes.clear()
                return await player.pause(False)
            
            required = math.ceil((len(interaction.user.voice.channel.members)-1) / 2.5)
            player.pause_votes.add(interaction.user)

            if len(player.pause_votes) >= required:
                await interaction.response.send_message("Vote to pause passed. Pausing player.", delete_after=10)
                player.pause_votes.clear()
                await player.pause(True)
            else:
                await interaction.response.send_message(
                    f"{interaction.user.mention} has voted to pause the player. Votes: {len(player.pause_votes)}/{required}",
                    delete_after=15,
                )


    @discord.ui.button(label="Stop", emoji="◾", style=discord.ButtonStyle.red, custom_id="stop_button")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client
        if not player.playing:
            return

        if interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(embed=discord.Embed(description="Player has been stopped.", color=discord.Color.green()), delete_after=10)
            playerUptime = time.time() - player.start_time
            setting = function.db.find_one(function.Setting, player.guild.id)
            if setting is None:
                function.db.set_settings(player.guild.id)
                previousTime = 0
            else:
                previousTime = setting.time
            newTime = previousTime + playerUptime
            function.db.update_one(function.Setting, player.guild.id, {"time": newTime})
            if player.now_playing_message:
                try:
                    await player.now_playing_message.delete()
                except discord.HTTPException:
                    pass
                player.now_playing_message = None
            return await player.disconnect()
        
        elif function.db.find_one(function.Setting, interaction.message.guild.id).dj in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(embed=discord.Embed(description="Player has been stopped.", color=discord.Color.green()), delete_after=10)
            playerUptime = time.time() - player.start_time
            setting = function.db.find_one(function.Setting, player.guild.id)
            if setting is None:
                function.db.set_settings(player.guild.id)
                previousTime = 0
            else:
                previousTime = setting.time
            newTime = previousTime + playerUptime
            function.db.update_one(function.Setting, player.guild.id, {"time": newTime})
            if player.now_playing_message:
                try:
                    await player.now_playing_message.delete()
                except discord.HTTPException:
                    pass
                player.now_playing_message = None
            return await player.disconnect()

        required = math.ceil((len(interaction.user.voice.channel.members)-1) / 2.5)
        player.stop_votes.add(interaction.user)

        if len(player.stop_votes) >= required:
            await interaction.response.send_message(embed=discord.Embed(description="Vote to stop passed. Stopping the player.", color=discord.Color.green()), delete_after=10)
            playerUptime = time.time() - player.start_time
            setting = function.db.find_one(function.Setting, player.guild.id)
            if setting is None:
                function.db.set_settings(player.guild.id)
                previousTime = 0
            else:
                previousTime = setting.time
            newTime = previousTime + playerUptime
            function.db.update_one(function.Setting, player.guild.id, {"time": newTime})
            if player.now_playing_message:
                try:
                    await player.now_playing_message.delete()
                except discord.HTTPException:
                    pass
                player.now_playing_message = None
            await player.disconnect()
        else:
            await interaction.response.send_message(
            f"{interaction.user.mention} has voted to stop the player. Votes: {len(player.stop_votes)}/{required}",
            delete_after=15,
            )

    @discord.ui.button(label="Autoplay", emoji="💡", style=discord.ButtonStyle.blurple, custom_id="autoplay_button")
    async def autoplay_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client

        if interaction.user.guild_permissions.kick_members:
            if player.autoplay == wavelink.AutoPlayMode.disabled:
                player.autoplay = wavelink.AutoPlayMode.enabled
                await interaction.response.send_message(embed=discord.Embed(description=f"Autoplay is now enabled.", color=discord.Color.green()))
            else:
                player.autoplay = wavelink.AutoPlayMode.disabled
                await interaction.response.send_message(embed=discord.Embed(description=f"Autoplay is now disabled.", color=discord.Color.green()))
        elif function.db.find_one(function.Setting, interaction.message.guild.id).dj in [role.id for role in interaction.user.roles]:
            if player.autoplay == wavelink.AutoPlayMode.disabled:
                player.autoplay = wavelink.AutoPlayMode.enabled
                await interaction.response.send_message(embed=discord.Embed(description=f"Autoplay is now enabled.", color=discord.Color.green()))
            else:
                player.autoplay = wavelink.AutoPlayMode.disabled
                await interaction.response.send_message(embed=discord.Embed(description=f"Autoplay is now disabled.", color=discord.Color.green()))
        else:
            await interaction.response.send_message(embed=discord.Embed(description="You don't have permission to do this.", color=discord.Color.red()))

            
    @discord.ui.button(label="Favorite", emoji="❤️", style=discord.ButtonStyle.blurple, custom_id="favorite_button")
    async def favorite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = interaction.guild.voice_client

        rank, maxTrack = await function.get_user_rank(interaction.user.id)
        if rank is None:
            await function.create_account(interaction)

        playlist_entry = function.db.find_one(function.Playlist, interaction.user.id)
        if playlist_entry is None:
            await function.create_account(interaction)
            playlist_entry = function.db.find_one(function.Playlist, interaction.user.id)

        playlist = playlist_entry.tracks

        if player.current.uri not in playlist.split(','):
            if playlist == "":
                new_tracks = player.current.uri + ','
            else:
                if len(playlist.split(',')) >= maxTrack:
                    return await interaction.response.send_message(embed=discord.Embed(description="Your playlist is full", color=discord.Color.red()), ephemeral=True)
                new_tracks = playlist + player.current.uri + ","

            function.db.update_one(function.Playlist, interaction.user.id, {"tracks": new_tracks})
            await interaction.response.send_message(embed=discord.Embed(description=f"**[{player.current.title}](<{player.current.uri}>)** is added to **❤️**", color=discord.Color.green()), ephemeral=True)
        else:
            await interaction.response.send_message(embed=discord.Embed(description="This is already in your playlist", color=discord.Color.red()), ephemeral=True)
