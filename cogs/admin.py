from discord.ext import commands
import discord
from discord import app_commands
import function
from views.help import HelpView
import wavelink

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def is_admin(self, ctx: commands.Context):
        """Check whether the user is an Admin."""
        return ctx.author.guild_permissions.kick_members
    
    @commands.hybrid_group(
        name="settings",
        invoke_without_command=True
    )

    async def settings(self, ctx: commands.Context):
        view = HelpView(self.bot, ctx.author)
        embed = view.build_embed(self.qualified_name)
        message = await ctx.send(embed=embed, view=view)
        view.response = message
    

    @settings.command(name='volume', with_app_command=True, description="Change the volume")
    @app_commands.describe(volume="Volume int.")
    async def volume(self, ctx: commands.Context, volume: int):
        if not 0 < volume < 101:
            return await ctx.reply(embed=discord.Embed(description="Volume must be between **1** and **100**.", color=discord.Color.red()))
        
        if self.is_admin(ctx):
            try:
                player: wavelink.Player = ctx.voice_client
            except Exception:
                player = None
            if player:
                function.db.update_one(function.Setting, ctx.message.guild.id, {"volume": volume})
                await player.set_volume(volume)
            else:
                function.db.update_one(function.Setting, ctx.message.guild.id, {"volume": volume})
                

            return await ctx.reply(embed=discord.Embed(description=f"Volume is set to **{volume}**", color=discord.Color.green()))
        else:
            return await ctx.reply(embed=discord.Embed(description="You must be an **admin** or **mod**.", color=discord.Color.red()))
        

    @settings.command(name='prefix', with_app_command=True, description="Change the prefix")
    @app_commands.describe(prefix="prefix str.")
    async def prefix(self, ctx: commands.Context, prefix: str):

        if self.is_admin(ctx):
            try:
                function.db.update_one(function.Setting, ctx.message.guild.id, {"prefix": prefix})
            except Exception as e:
                 raise f"Erreur : {e}"
                
            return await ctx.reply(embed=discord.Embed(description=f"Prefix is set to {prefix}", color=discord.Color.green()))
        
        else:
            return await ctx.reply(embed=discord.Embed(description="You must be an **admin** or **mod**.", color=discord.Color.red()))
        

    async def dj_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        roles = interaction.guild.roles
        return [
            app_commands.Choice(name=role.name, value=str(role.id))
            for role in roles if current.lower() in role.name.lower()
        ][:25] 
        
    @settings.command(name='dj', with_app_command=True, description="Change/remove the dj role")
    @app_commands.describe(role="DJ role.")
    @app_commands.autocomplete(role=dj_autocomplete)
    async def dj(self, ctx: commands.Context, enable: bool, role: str = None):

        if self.is_admin(ctx):
            try:
                if enable:
                    if not role:
                        return await ctx.reply(embed=discord.Embed(description="You need to select a role.", color=discord.Color.red()))
                    function.db.update_one(function.Setting, ctx.message.guild.id, {"dj": int(role)})
                else:
                    function.db.update_one(function.Setting, ctx.message.guild.id, {"dj": None})
                    return await ctx.reply(embed=discord.Embed(description="DJ role has been disabled.", color=discord.Color.green()))
            except Exception as e:
                 raise f"Erreur : {e}"
                
            return await ctx.reply(embed=discord.Embed(description=f"DJ role is now **{ctx.guild.get_role(int(role))}**", color=discord.Color.green()))
        
        else:
            return await ctx.reply(embed=discord.Embed(description="You must be an **admin** or **mod**.", color=discord.Color.red()))
        
    
        

    @settings.command(name="view", with_app_command=True, description="See server settings")
    async def view(self, ctx: commands.Context):
        server = function.db.find_one(function.Setting, ctx.message.guild.id)
        if server is None:
            function.db.set_settings(ctx.message.guild.id)

        prefix = function.db.find_one(function.Setting, ctx.message.guild.id).prefix
        volume = function.db.find_one(function.Setting, ctx.message.guild.id).volume
        time = function.db.find_one(function.Setting, ctx.message.guild.id).time
        dj = function.db.find_one(function.Setting, ctx.message.guild.id).dj

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
            f"**DJ: `{ctx.guild.get_role(dj)}%`**\n"
            f"**Time played: `{time_format.strip()}`**\n"
        )
        embed.set_author(name=ctx.guild.name, icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="FLAYX", icon_url=self.bot.user.avatar.url)
        return await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))