import wavelink
from discord.ext import commands
import discord
from discord import app_commands
import function
import time
from views.help import HelpView


class Base(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name='help', with_app_command = True, description = "Lists all the commands in FLAYX.")
    async def help(self, ctx: commands.Context) -> None:
        "Lists all the commands in FLAYX."
        category = "News"
        view = HelpView(self.bot, ctx.author)
        embed = view.build_embed(category)
        message = await ctx.send(embed=embed, view=view)
        view.response = message

    @commands.hybrid_command(name='ping', with_app_command=True, description="Test if the bot is alive, and see the delay between your commands and my response.")
    async def ping(self, ctx: commands.Context):
        "Test if the bot is alive, and see the delay between your commands and my response."
        embed = discord.Embed()
        botPing = self.bot.latency
        botemoji = '👌' if botPing <= 1 else '😨' if botPing <= 5 else '😭'
        start_time = time.monotonic()
        node = wavelink.Pool.get_node()
        end_time = time.monotonic()
        nodePing = (end_time - start_time) * 1000
        nodeemoji = '👌' if nodePing <= 1 else '😨' if nodePing <= 5 else '😭'
        dbPing = function.db.ping_mysql()
        dbemoji = '👌' if dbPing <= 1 else '😨' if dbPing <= 5 else '😭'
        embed.add_field(name='Bot info:', value=f"""
        Bot: {botPing:.3f}s {botemoji}\nNode: {nodePing:.3f}s {nodeemoji}\nDatabase: {dbPing:.3f}s {dbemoji}
        """)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Base(bot))