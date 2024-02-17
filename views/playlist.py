import discord


class agree(discord.ui.Button):
    def __init__(self) -> None:
        self.view: CreateView
        super().__init__(label="Agree", style=discord.ButtonStyle.green)
    
    async def callback(self, interaction: discord.Interaction) -> None:
        self.label = "Created"
        self.disabled = True
        self.style=discord.ButtonStyle.primary
        embed = discord.Embed(description="Your account has been successfully created", color=0x55e27f)
        await interaction.response.edit_message(embed=embed, view=self.view)
        self.view.value = True
        self.view.stop()


class CreateView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=20)
        self.value: bool = None
        self.response: discord.Message = None

        self.add_item(agree())

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            await self.response.edit(view=self)
        except TimeoutError:
            pass