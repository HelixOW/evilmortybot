from typing import Optional, Dict, List, Union
import discord
from discord.ext import commands
from discord.ext.commands import Context

import utilities.reactions as emojis

from utilities import embeds
from utilities.embeds import DrawEmbed
from utilities import all_banner_list, MemberMentionConverter, ssr_pattern
from utilities.banners import Banner, banner_by_name, unit_with_chance, BannerType, add_shaft, \
    find_banner_containing_any_unit, banner_starting_names
from utilities.image_composer import compose_banner_rotation, compose_multi_draw, compose_five_multi_draw, \
    compose_draw, compose_unit_multi_draw, compose_unit_five_multi_draw, compose_box
from utilities.paginator import Paginator, Page
from utilities.units import Unit, image_to_discord, unit_by_vague_name, Grade
from utilities.sql_helper import fetch_rows

loading_image_url: str = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"


async def read_box(user: discord.Member) -> Dict[int, int]:
    return {u_id: amount for u_id, amount in await fetch_rows(
        'SELECT box_units.unit_id, box_units.amount FROM box_units INNER JOIN units u ON u.unit_id = box_units.unit_id WHERE user_id=? AND guild=? ORDER BY u.grade DESC, box_units.amount DESC',
        lambda x: (x[0], x[1]),
        (user.id, user.guild.id))
            }


def join_banner(other_str: str, banner_name: str):
    if other_str in ["banner", "part", "gssr", "race", "humans", "soluna", "commandments", "jp", "custom"]:
        return None, other_str + " " + banner_name
    return other_str, banner_name


class DrawCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.command()
    @commands.guild_only()
    async def multi(self, ctx: Context, person: Optional[discord.Member], amount: Union[str, int] = 1, *,
                    banner_name: str = None):
        if person is None:
            person: discord.Member = ctx.author

        if isinstance(amount, str) and amount not in ["rotation", "rot"]:
            banner_name = amount + (banner_name if banner_name else "")

        if not banner_name:
            banner_name = "banner one"

        from_banner: Optional[Banner] = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"Can't find the \"{banner_name}\" banner")
                                  )

        if amount in ["rotation", "rot"]:
            with ctx.typing():
                units: Dict[Unit, int] = {}
                for _ in range(int(from_banner.loyality / 30) * 11):
                    _unit: Unit = await unit_with_chance(from_banner, person)
                    if _unit in units:
                        units[_unit] += 1
                    else:
                        units[_unit]: int = 1

                return await ctx.send(
                    file=await image_to_discord(await compose_banner_rotation(
                        dict(sorted(units.keys(), key=lambda u: u[0].grade.to_int())))),
                    content=f"{person.display_name} those are the units you pulled in 1 rotation" if person is ctx.author
                    else f"{person.display_name} those are the units you pulled in 1 rotation coming from {ctx.author.display_name}",
                    embed=embeds.DrawEmbed(
                        title=f"{from_banner.pretty_name} ~ 1 Rotation ({from_banner.loyality} Gems)"))

        paginator: Paginator = Paginator(self.bot,
                                         lambda reaction, usr: usr == ctx.message.author or usr == person and str(
                                             reaction.emoji) in [emojis.LEFT_ARROW, emojis.RIGHT_ARROW],
                                         timeout=30)

        for x, y in enumerate([await compose_multi_draw(from_banner=from_banner, user=person)
                               if from_banner.banner_type == BannerType.ELEVEN else
                               await compose_five_multi_draw(from_banner=from_banner, user=person)
                               for _ in range(amount)]):
            paginator.add_page(Page(
                content=f"{person.display_name} this is your {x + 1}. multi" if person is ctx.author else f"{person.display_name} this is your {x + 1}. multi coming from {ctx.author.display_name}",
                embed=embeds.DrawEmbed(
                    title=f"{from_banner.pretty_name} ({11 if from_banner.banner_type == BannerType.ELEVEN else 5}x summon)"
                ),
                image=y)
            )

        await paginator.send(ctx)

    @commands.command()
    @commands.guild_only()
    async def summon(self, ctx: Context):
        summon_menu_emojis: List[str] = [emojis.LEFT_ARROW,
                                         emojis.NO_1,
                                         emojis.NO_10, emojis.NO_5,
                                         emojis.WHALE,
                                         emojis.INFO,
                                         emojis.RIGHT_ARROW]

        async def no_1(_ctx: Context, msg: discord.Message, _banner: Banner):
            async with _ctx.typing():
                await msg.delete()
                return await _ctx.send(file=await compose_draw(_banner, _ctx.author),
                                       content=f"{_ctx.author.mention} this is your single",
                                       embed=embeds.DrawEmbed(title=f"{_banner.pretty_name} (1x summon)"))

        async def no_10(_ctx: Context, msg: discord.Message, _banner: Banner):
            async with _ctx.typing():
                await msg.delete()
                await _ctx.send(
                    content=f"{ctx.author.display_name} this is your multi",
                    file=await image_to_discord(
                        await compose_multi_draw(from_banner=_banner, user=_ctx.author)
                        if _banner.banner_type == BannerType.ELEVEN else
                        await compose_five_multi_draw(from_banner=_banner, user=_ctx.author)),
                    embed=embeds.DrawEmbed(
                        title=f"{_banner.pretty_name}"
                              f"({11 if _banner.banner_type == BannerType.ELEVEN else 5}x summon)")
                )

        async def whale(_ctx: Context, msg: discord.Message, _banner: Banner):
            await msg.delete()
            return await self.shaft(_ctx, person=ctx.author, banner_name=_banner.name[0])

        async def banner_info(_ctx: Context, msg: discord.Message, _banner: Banner):
            await msg.delete()
            return await self.banner(_ctx, banner_name=_banner.name[0])

        paginator: Paginator = Paginator(self.bot,
                                         lambda r, u: u == ctx.author and str(r.emoji) in summon_menu_emojis)

        for banner in all_banner_list:
            paginator.add_page(Page(
                ctx.author.display_name,
                DrawEmbed(title=banner.pretty_name).set_image(url=banner.background),
                holding=banner,
                buttons={
                    emojis.NO_1: no_1,
                    emojis.NO_10 if banner.banner_type == BannerType.ELEVEN else emojis.NO_5: no_10,
                    emojis.WHALE if banner.shaftable else None: whale,
                    emojis.INFO: banner_info
                }
            ))

        await paginator.send(ctx)

    @commands.command()
    @commands.guild_only()
    async def single(self, ctx: Context, person: Optional[discord.Member], *,
                     banner_name: str = "banner 1"):
        if person is None:
            person: discord.Member = ctx.author

        from_banner: Optional[Banner] = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"Can't find the `{banner_name}` banner"))

        return await ctx.send(file=await compose_draw(from_banner, person),
                              content=f"{person.mention} this is your single"
                              if person is ctx.message.author else
                              f"{person.mention} this is your single coming from {ctx.author.mention}",
                              embed=embeds.DrawEmbed(title=f"{from_banner.pretty_name} (1x summon)"))

    @commands.command()
    @commands.guild_only()
    async def shaft(self, ctx: Context, person: Optional[MemberMentionConverter],
                    unit_name: Optional[str] = None, *, banner_name: str = None):
        if person is None:
            person: discord.Member = ctx.author

        if unit_name in banner_starting_names():
            banner_name = unit_name + (banner_name if banner_name else "")
            unit_name = None

        if banner_name is None:
            banner_name = "banner one"

        from_banner: Banner = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"Can't find the `{banner_name}` banner"))

        unit_ssr: bool = True

        if unit_name is not None:
            if ssr_pattern.match(unit_name, 0):
                unit_name: str = ssr_pattern.sub("", unit_name)
            else:
                unit_ssr: bool = False

            possible_units: List[Unit] = unit_by_vague_name(unit_name)

            if not from_banner.contains_any_unit(possible_units):
                try:
                    from_banner = find_banner_containing_any_unit(possible_units)
                except ValueError:
                    return await ctx.send(content=ctx.author.mention,
                                          embed=embeds.ErrorEmbed(
                                              error_message=f"Can't find any banner with {unit_name} in it"
                                          ))

        if from_banner is None:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(
                                      error_message=f"Can't find any banner with {unit_name} in it"
                                  ))

        if not from_banner.shaftable:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(
                                      f"Can't get shafted on the `{from_banner.pretty_name}` banner"
                                  ))

        unit_to_draw: List[Unit] = [a for a in unit_by_vague_name(unit_name)
                                    if a.unit_id in [b.unit_id for b in from_banner.all_units]] \
            if unit_name is not None else [a for a in from_banner.all_units if a.grade == Grade.SSR]

        async with ctx.typing():
            rang: int = 11 if from_banner.banner_type == BannerType.ELEVEN else 5

            def contains_any_unit(drawn: List[Unit]) -> bool:
                for u in drawn:
                    if u in unit_to_draw:
                        if unit_ssr:
                            if u.grade == Grade.SSR:
                                return True
                        else:
                            return True
                return False

            i: int = 0
            drawn_units: List[Unit] = [await unit_with_chance(from_banner, person) for _ in range(rang)]
            drawn_ssrs: Dict[Unit, int] = {}
            for x in drawn_units:
                if x.grade == Grade.SSR:
                    if x not in drawn_ssrs:
                        drawn_ssrs[x] = 1
                    else:
                        drawn_ssrs[x] += 1

            while not contains_any_unit(drawn_units) and i < 1000:
                i += 1
                drawn_units: List[Unit] = [await unit_with_chance(from_banner, person) for _ in range(rang)]
                for x in drawn_units:
                    if x.grade == Grade.SSR:
                        if x not in drawn_ssrs:
                            drawn_ssrs[x] = 1
                        else:
                            drawn_ssrs[x] += 1

            multi_msg: str = "Multi" if i == 0 else "Multis"

            await ctx.send(
                file=await image_to_discord(
                    await compose_unit_multi_draw(units=drawn_units,
                                                  ssrs=drawn_ssrs) if from_banner.banner_type == BannerType.ELEVEN
                    else await compose_unit_five_multi_draw(units=drawn_units)),
                content=f"{person.mention}: Your shaft" if person is ctx.author
                else f"{person.mention}: Your shaft coming from {ctx.author.mention}",
                embed=embeds.DrawEmbed(
                    title=f"{from_banner.pretty_name} ({rang}x summon)",
                    description=f"You did {i + 1}x {multi_msg}. \n With this being your final pull:"))
            await add_shaft(person, i)

    @commands.command()
    @commands.guild_only()
    async def banner(self, ctx: Context, *, banner_name: str = "banner one"):
        from_banner: Banner = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.ErrorEmbed(f"Can't find the `{banner_name}` banner"))

        title: str = f"Units in {from_banner.pretty_name} ({round(from_banner.ssr_chance, 4)}%)"
        paginator: Paginator = Paginator(self.bot,
                                         check_function=lambda r, u: u == ctx.author and str(r.emoji) in
                                                                     [emojis.LEFT_ARROW, emojis.RIGHT_ARROW])

        for i, unit_page in enumerate(from_banner.unit_list_image):
            paginator.add_page(
                Page(
                    embed=DrawEmbed(title=title + f" [{i + 1}/{len(from_banner.unit_list_image)}]"),
                    image=unit_page
                )
            )

        await paginator.send(ctx, 0)

    @commands.command()
    @commands.guild_only()
    async def box(self, ctx: Context, user: Optional[discord.Member]):
        if user is None:
            user: discord.Member = ctx.author
        box_d: Dict[int, int] = await read_box(user)
        if len(box_d) == 0:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"{user.display_name} has no units!"))

        async with ctx.typing():
            await ctx.send(file=await image_to_discord(await compose_box(box_d), "box.png"),
                           content=ctx.author.mention,
                           embed=discord.Embed(title=f"{user.display_name}'s box", colour=discord.Color.gold()).set_image(
                               url="attachment://box.png"))


def setup(_bot):
    _bot.add_cog(DrawCog(_bot))
