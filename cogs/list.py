import discord
import math
import asyncio
import utilities.reactions as emojis

from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional, Dict, Any, List
from utilities import all_banner_list, embeds
from utilities.paginator import Paginator, Page
from utilities.units import parse_arguments, Unit, get_units_matching, image_to_discord
from utilities.image_composer import compose_paged_unit_list, compose_tarot_list, compose_paged_tarot_list
from utilities.tarot import tarot_name
from PIL.Image import Image


class ListCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group(name="list")
    async def cmd_list(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            return await self.list_units(ctx)

    @cmd_list.command(name="unit", aliases=["units"])
    async def list_units(self, ctx: Context, units_per_page: Optional[int] = 5, *, criteria: str = "event: custom"):
        async with ctx.typing():
            attr: Dict[str, Any] = parse_arguments(criteria)
            matching_units: List[Unit] = get_units_matching(races=attr["race"],
                                                            grades=attr["grade"],
                                                            types=attr["type"],
                                                            events=attr["event"],
                                                            affections=attr["affection"],
                                                            names=attr["name"],
                                                            jp=attr["jp"])
            paged_unit_list: List[Image] = await compose_paged_unit_list(matching_units, units_per_page)
            max_pages: float = math.ceil(len(matching_units) / units_per_page) - 1

        async def display(page: int):
            async with ctx.typing():
                message: discord.Message = await ctx.send(file=await image_to_discord(paged_unit_list[page]),
                                                          embed=embeds.DrawEmbed(
                                                              title=f"Units matching {criteria} ({page + 1}/{max_pages + 1})"
                                                          ),
                                                          content=ctx.author.mention)

            if page != 0:
                await message.add_reaction(emojis.LEFT_ARROW)

            if page != max_pages:
                await message.add_reaction(emojis.RIGHT_ARROW)

            try:
                def check_page(added_reaction, user):
                    return user == ctx.message.author and str(added_reaction.emoji) in ["⬅️", "➡️"]

                reaction, _ = await self.bot.wait_for("reaction_add", check=check_page, timeout=20)

                if "➡️" in str(reaction.emoji):
                    await message.delete()
                    await display(page + 1)
                elif "⬅️" in str(reaction.emoji):
                    await message.delete()
                    await display(page - 1)
            except asyncio.TimeoutError:
                await message.clear_reactions()

        await display(0)

    @cmd_list.command(name="banner", aliases=["banners"])
    async def list_banners(self, ctx: Context):
        async with ctx.typing():
            await ctx.send(content=ctx.author.mention,
                           embed=embeds.DefaultEmbed(title="All Banners",
                                                     description="\n\n".join(
                                                         [f"**{x.name[0]}**: `{x.pretty_name}`" for x in all_banner_list])))

    @cmd_list.command(name="tarot")
    async def list_tarot(self, ctx: Context, paged: str = "paged"):
        if paged != "paged":
            async with ctx.typing():
                await ctx.send(content=ctx.author.mention,
                               file=await image_to_discord(await compose_tarot_list()),
                               embed=embeds.DrawEmbed()
                               )

        paginator: Paginator = Paginator(self.bot,
                                         lambda rea, usr: usr == ctx.author and str(rea.emoji) in [emojis.LEFT_ARROW,
                                                                                                   emojis.RIGHT_ARROW])

        for x in range(22):
            paginator.add_page(Page(
                embed=embeds.DrawEmbed(title=tarot_name(x + 1)),
                image=await compose_paged_tarot_list(x + 1)
            ))

        await paginator.send(ctx)


def setup(_bot):
    _bot.add_cog(ListCog(_bot))
