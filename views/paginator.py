import discord
from discord.ui import View

class PaginationMenu(View):
    def __init__(self, ctx, pages):
        super().__init__()
        self.ctx = ctx
        self.pages = pages
        self.current_page = 0
        self.message = None


    async def show_page(self):
        page = self.pages[self.current_page]
        embed = discord.Embed(title=f"Page {self.current_page + 1}/{len(self.pages)}", description=page, color=discord.Color.blurple())

        if self.message:
            await self.message.edit(embed=embed, view=self)
        else:
            self.message = await self.ctx.send(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)


    @discord.ui.button(emoji="⬅️", custom_id="prev_button")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.show_page()
        await interaction.response.defer()

    @discord.ui.button(emoji="➡️", custom_id="next_button")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.show_page()
        await interaction.response.defer()