from discord.ext import commands
import discord
from discord import app_commands
from voicelink.player import Player
import function


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def is_admin(self, ctx: commands.Context):
        """Check whether the user is an Admin."""
        return ctx.author.guild_permissions.kick_members
    

    @commands.hybrid_command(name='volume', with_app_command=True, description="Change the volume")
    @app_commands.describe(volume="Volume int.")
    async def volume(self, ctx: commands.Context, volume: int):
        if not 0 < volume < 101:
            return await ctx.reply("Volume must be between 1 and 100.")
        
        if self.is_admin(ctx):
            try:
                player: Player = ctx.voice_client
            except Exception:
                player = None
            if player:
                function.db.update_one("settings", "volume", volume, ctx.message.guild.id)
                await player.set_volume(volume)
            else:
                function.db.update_one("settings", "volume", volume, ctx.message.guild.id)
                

            return await ctx.reply(f"Volume is set to {volume}")
        else:
            return await ctx.reply("You must be an admin or mod")
        

    @commands.hybrid_command(name='prefix', with_app_command=True, description="Change the volume")
    @app_commands.describe(prefix="prefix str.")
    async def prefix(self, ctx: commands.Context, prefix: str):

        if self.is_admin(ctx):
            try:
                function.db.update_one("settings", "prefix", prefix, ctx.message.guild.id)
            except Exception as e:
                 raise f"Erreur : {e}"
                
            return await ctx.reply(f"Prefix is set to {prefix}")
        
        else:
            return await ctx.reply("You must be an admin or mod")
        

    @commands.hybrid_command(name='settings', with_app_command=True, description="See server settings")
    async def settings(self, ctx: commands.Context):
        server = function.db.find_one("settings", ctx.message.guild.id, "id")
        if server == None:
            function.db.set_settings(ctx.message.guild.id)

        prefix = function.db.find_one("settings", ctx.message.guild.id, "prefix")
        volume = function.db.find_one("settings", ctx.message.guild.id, "volume")
        time = function.db.find_one("settings", ctx.message.guild.id, "time")

        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)

        time_format = ""
    
        if hours > 0:
            time_format += f"{hours}h "
        if minutes > 0:
            time_format += f"{minutes}m "
        if seconds > 0:
            time_format += f"{seconds}s "
        if not time_format:
            time_format = "0s"

        embed = discord.Embed(
            description=f"**Prefix: `{prefix}`**\n"
            f"**Volume: `{volume}%`**\n"
            f"**Time played: `{time_format.strip()}`**\n"
        )
        embed.set_author(name=ctx.guild.name, icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="FLAYX", icon_url=self.bot.user.avatar.url)
        return await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))