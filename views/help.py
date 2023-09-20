import discord
from discord.ext import commands
from discord.ui import View, Button

class HelpDropdown(discord.ui.Select):
    def __init__(self, categorys:list):
        options = [
            discord.SelectOption(emoji="🆕", label="News", description="View new updates of FLAYX."),
            discord.SelectOption(emoji="🕹️", label="Tutorial", description="How to use FLAYX."),
        ]
        cog_emojis = ["3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        for category, emoji in zip(categorys, cog_emojis):
            options.append(discord.SelectOption(emoji=emoji, 
                                                label=f"{category} Commands",
                                                description=f"This is {category.lower()} Category."))
    
        super().__init__(
            placeholder="Select Category!",
            min_values=1, max_values=1,
            options=options, custom_id="select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        embed = self.view.build_embed(self.values[0].split(" ")[0])
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, author: discord.Member):
        super().__init__(timeout=60)

        self.author = author
        self.bot = bot
        self.response = None
        self.categorys = [ name.capitalize() for name, cog in bot.cogs.items() if len([c for c in cog.walk_commands()]) ]

        self.add_item(discord.ui.Button(label='Support', emoji=':support:915152950471581696', url="https://discord.com/invite/mtuRkqMr4u"))
        self.add_item(discord.ui.Button(label='Invite', emoji=':invite:915152589056790589', url='https://discord.com/api/oauth2/authorize?client_id=1132750661197516831&permissions=8&scope=bot%20applications.commands'))
        self.add_item(HelpDropdown(self.categorys))
    
    async def on_error(self, error, item, interaction):
        return

    async def on_timeout(self):
        for child in self.children:
            if child.custom_id == "select":
                child.disabled = True
        try:
            await self.response.edit(view=self)
        except TimeoutError:
            pass

    async def interaction_check(self, interaction):
        if interaction.user == self.author:
            return True
        return False

    def build_embed(self, category: str):
        category = category.lower()
        if category == "news":
            embed = discord.Embed(title="FLAYX Help Menu")
            embed.add_field(name=f"Available Categories: [{2 + len(self.categorys)}]",
                            value="```py\n👉 News\n2. Tutorial\n{}```".format("".join(f"{i}. {c}\n" for i, c in enumerate(self.categorys, start=3))),
                            inline=True)

            update = "> Update Contents\n" \
                     "> ➥ In dev\n" \
                     "> ➥ Actualy v0.x\n" \

            embed.add_field(name="📰 Latest News: \n", value=update, inline=True)
            embed.add_field(name="Get Started", value="```Join a voice channel and /play a song. (Names, Links or Playlist, Spotify links)```", inline=False)
            
            return embed

        embed = discord.Embed(title=f"Category: {category.capitalize()}")
        embed.add_field(name=f"Categories: [{2 + len(self.categorys)}]", value="```py\n" + "\n".join(("👉 " if c == category.capitalize() else f"{i}. ") + c for i, c in enumerate(['News', 'Tutorial'] + self.categorys, start=1)) + "```", inline=True)

        if category == 'tutorial':
            embed.description = "How to use FLAYX? Just see the Music category."
            embed.add_field(name="Tutorial", value="```Join a voice channel and /play a song.```", inline=False)
        else:
            cog = [c for _, c in self.bot.cogs.items() if _.lower() == category][0]

            commands = [command for command in cog.walk_commands()]
            embed.description = cog.description
            embed.add_field(name=f"{category} Commands: [{len(commands)}]",
                            value="```{}```".format("".join(f"/{command.qualified_name}\n" for command in commands if not command.qualified_name == cog.qualified_name)))

        return embed