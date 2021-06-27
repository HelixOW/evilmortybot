import asyncio
from typing import Callable, List, Any, Dict
from PIL.Image import Image

import discord
from discord.ext.commands import Context

import utilities.reactions
from utilities import image_to_discord


pending_tasks = {}


class Page:
    def __init__(self, content: str = None,
                 embed: discord.Embed = None,
                 image: Image = None,
                 buttons: Dict[str, Callable[[Context, discord.Message], Any]] = None,
                 holding: Any = None):
        self.content: str = content
        self.embed: discord.Embed = embed
        self.image: Image = image
        self.buttons: Dict[str, Callable[[Context, discord.Message, Any], Any]] = buttons if buttons else {}
        self.holding: Any = holding

    async def send(self, ctx: Context, previous_page: discord.Message) -> discord.Message:
        if not previous_page:
            async with ctx.typing():
                page: discord.Message = await ctx.send(content=self.content,
                                                       embed=self.embed,
                                                       file=await image_to_discord(
                                                           self.image) if self.image else None)
        else:
            if not self.image:
                async with ctx.typing():
                    await previous_page.edit(content=self.content, embed=self.embed)
                await previous_page.clear_reactions()
                page: discord.Message = previous_page
            else:
                async with ctx.typing():
                    page: discord.Message = await ctx.send(content=self.content,
                                                           embed=self.embed,
                                                           file=await image_to_discord(
                                                               self.image) if self.image else None)
                await previous_page.delete()

        return page

    async def add_buttons(self, message: discord.Message):
        for button in self.buttons:
            if button:
                await message.add_reaction(button)

    async def press_button(self, label: str, ctx: Context, page: discord.Message):
        if label not in self.buttons:
            return

        return await self.buttons[label](ctx, page, self.holding)


class Paginator:
    def __init__(self,
                 bot: discord.ext.commands.Bot,
                 check_function: Callable[[discord.Reaction, discord.User], bool],
                 timeout: int = 60,
                 after_page_function: Callable[[Context, discord.Message], Any] = None):
        self.bot = bot
        self.check_function: Callable[[discord.Reaction, discord.User], bool] = check_function
        self.timeout: int = timeout
        self.pages: List[Page] = []
        self.previous_page: discord.Message = None
        self.after_page_function: Callable[[Context, discord.Message], Any] = after_page_function

    def add_page(self, page: Page):
        self.pages.append(page)

    async def send(self, ctx: Context, page_index: int = 0):
        page: discord.Message = await self.pages[page_index].send(ctx, self.previous_page)

        self.previous_page = page

        if self.after_page_function:
            try:
                await self.after_page_function(ctx, page)
            except:
                pass

        if len(self.pages) < 2:
            return

        if ctx.message.author in pending_tasks:
            pending_tasks[ctx.author.id].stop()

        await page.add_reaction(utilities.reactions.LEFT_ARROW)

        await self.pages[page_index].add_buttons(page)

        await page.add_reaction(utilities.reactions.RIGHT_ARROW)

        try:
            pending_tasks[ctx.author.id] = self.bot.wait_for('reaction_add', check=self.check_function, timeout=self.timeout)
            reaction, _ = await pending_tasks[ctx.author.id]
            clicked: str = str(reaction.emoji)

            await page.clear_reactions()

            if ctx.author.id in pending_tasks:
                pending_tasks.pop(ctx.author.id)

            if clicked == utilities.reactions.LEFT_ARROW:
                if page_index > 0:
                    return await self.send(ctx, page_index - 1)
                else:
                    return await self.send(ctx, len(self.pages) - 1)

            if clicked == utilities.reactions.RIGHT_ARROW:
                if page_index < len(self.pages) - 1:
                    return await self.send(ctx, page_index + 1)
                else:
                    return await self.send(ctx, 0)

            await self.pages[page_index].press_button(clicked, ctx, page)
        except asyncio.TimeoutError:
            if ctx.author.id in pending_tasks:
                pending_tasks.pop(ctx.author.id)
            await page.clear_reactions()

