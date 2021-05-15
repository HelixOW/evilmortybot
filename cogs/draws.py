from typing import Optional, Dict, List

import discord
from discord.ext import commands
from discord.ext.commands import Context

import utilities.embeds as embeds
import utilities.reactions as emojis
from utilities.embeds import DefaultEmbed
from utilities import remove_trailing_whitespace, all_banner_list, MemberMentionConverter, ssr_pattern, \
    send_paged_message
from utilities.banners import Banner, banner_by_name, unit_with_chance, BannerType, add_shaft, \
    find_banner_containing_any_unit
from utilities.image_composer import compose_banner_rotation, compose_multi_draw, compose_five_multi_draw, \
    compose_draw, compose_unit_multi_draw, compose_unit_five_multi_draw, compose_banner_list, compose_box
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
    async def multi(self, ctx: Context, person: Optional[discord.Member], *, banner_name: str = "1 banner 1"):
        if person is None:
            person: discord.Member = ctx.author

        amount_str: str = ""
        amount: int = 1
        rot: bool = False

        if banner_name.startswith("rot") or banner_name.startswith("rotation"):
            rot: bool = True
            banner_name: str = remove_trailing_whitespace(banner_name.replace("rotation", "").replace("rot", ""))
            if banner_name.replace(" ", "") == "":
                banner_name: str = "banner 1"
        else:
            while banner_name.startswith(tuple(str(i) for i in range(50))):
                amount_str += remove_trailing_whitespace(banner_name[0])
                banner_name: str = remove_trailing_whitespace(banner_name[1:])
                amount: int = int(amount_str)

            if banner_name.replace(" ", "") == "":
                banner_name: str = "banner 1"

        from_banner: Optional[Banner] = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"Can't find the \"{banner_name}\" banner")
                                  )

        draw: discord.Message = await ctx.send(embed=embeds.loading().set_image(url=loading_image_url))

        if rot:
            units: Dict[Unit, int] = {}
            for _ in range(30 * 11):
                _unit: Unit = await unit_with_chance(from_banner, person)
                if _unit in units:
                    units[_unit] += 1
                else:
                    units[_unit]: int = 1
            await ctx.send(
                file=await image_to_discord(await compose_banner_rotation(
                    dict(sorted(units.items(), key=lambda x: x[0].grade.to_int())))),
                content=f"{person.display_name} those are the units you pulled in 1 rotation" if person is ctx.author
                else f"{person.display_name} those are the units you pulled in 1 rotation coming from {ctx.author.display_name}",
                embed=embeds.DrawEmbed(title=f"{from_banner.pretty_name} ~ 1 Rotation (900 Gems)"))
            return await draw.delete()

        await send_paged_message(
            self.bot, ctx,
            check_func=lambda x, y: y == ctx.message.author or y == person and str(x.emoji) in [emojis.LEFT_ARROW,
                                                                                                emojis.RIGHT_ARROW],
            timeout=30,
            pages=[
                {
                    "file": y,
                    "embed": embeds.DrawEmbed(
                        title=f"{from_banner.pretty_name}"
                              f"({11 if from_banner.banner_type == BannerType.ELEVEN else 5}x summon)"),
                    "content": f"{person.display_name} this is your {x + 1}. multi"
                    if person is ctx.author else
                    f"{person.display_name} this is your {x + 1}. multi coming from {ctx.author.display_name}",
                }
                for x, y in enumerate([await compose_multi_draw(from_banner=from_banner, user=person)
                                       if from_banner.banner_type == BannerType.ELEVEN else
                                       await compose_five_multi_draw(from_banner=from_banner, user=person)
                                       for _ in range(amount)])
            ],
            after_message=draw.delete
        )

    @commands.command()
    @commands.guild_only()
    async def summon(self, ctx: Context):
        loading_message: discord.Message = await ctx.send(embed=embeds.loading())
        summon_menu_emojis: List[str] = [emojis.LEFT_ARROW,
                                         emojis.NO_1,
                                         emojis.NO_10, emojis.NO_5,
                                         emojis.WHALE,
                                         emojis.INFO,
                                         emojis.RIGHT_ARROW]

        async def no_1(msg: discord.Message, _page: int):
            await msg.delete()
            return await ctx.send(file=await compose_draw(all_banner_list[_page], ctx.author),
                                  content=f"{ctx.author.mention} this is your single",
                                  embed=embeds.DrawEmbed(title=f"{all_banner_list[_page].pretty_name} (1x summon)"))

        async def no_10(msg: discord.Message, _page: int):
            await msg.delete()
            await ctx.send(
                content=f"{ctx.author.display_name} this is your multi",
                file=await image_to_discord(
                    await compose_multi_draw(from_banner=all_banner_list[_page], user=ctx.author)
                    if all_banner_list[_page].banner_type == BannerType.ELEVEN else
                    await compose_five_multi_draw(from_banner=all_banner_list[_page], user=ctx.author)),
                embed=embeds.DrawEmbed(
                    title=f"{all_banner_list[_page].pretty_name}"
                          f"({11 if all_banner_list[_page].banner_type == BannerType.ELEVEN else 5}x summon)")
            )

        async def whale(msg: discord.Message, _page: int):
            await msg.delete()
            return await self.shaft(ctx, person=ctx.author, banner_name=all_banner_list[_page].name[0])

        async def banner_info(msg: discord.Message, _page: int):
            await msg.delete()
            return await self.banner(ctx, banner_name=all_banner_list[_page].name[0])

        await loading_message.delete()

        await send_paged_message(
            self.bot, ctx,
            check_func=lambda r, u: u == ctx.author and str(r.emoji) in summon_menu_emojis,
            timeout=60,
            pages=[{
                "content": ctx.author.mention,
                "embed": DefaultEmbed(
                    title=x.pretty_name
                ).set_image(url=x.background),
                "file": None
            } for x in all_banner_list],
            buttons=[{
                emojis.NO_1: no_1,
                emojis.NO_10 if x.banner_type == BannerType.ELEVEN else emojis.NO_5: no_10,
                emojis.WHALE if x.shaftable else None: whale,
                emojis.INFO: banner_info
            } for x in all_banner_list]
        )

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
                    unit_name: Optional[str] = None, *, banner_name: str = "banner 1"):
        if person is None:
            person: discord.Member = ctx.author

        joined = join_banner(unit_name, banner_name)
        unit_name = joined[0]
        banner_name = joined[1]

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

        draw = await ctx.send(
            content=f"{person.mention} you are getting shafted" if person is ctx.author
            else f"{person.mention} you are getting shafted from {ctx.author.mention}",
            embed=embeds.loading("Shafting..."))

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
        await draw.delete()
        await add_shaft(person, i)

    @commands.command()
    @commands.guild_only()
    async def banner(self, ctx: Context, *, banner_name: str = "banner one"):
        from_banner: Banner = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.ErrorEmbed(f"Can't find the `{banner_name}` banner"))

        loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Banner",
                                                  embed=embeds.loading())
        await ctx.send(
            file=await image_to_discord(await compose_banner_list(from_banner, "custom" in from_banner.name)),
            embed=embeds.DrawEmbed(title=f"SSRs in {from_banner.pretty_name} ({from_banner.ssr_chance}%)"),
            content=ctx.author.mention)
        await loading.delete()

    @commands.command()
    @commands.guild_only()
    async def box(self, ctx: Context, user: Optional[discord.Member]):
        if user is None:
            user: discord.Member = ctx.author
        box_d: Dict[int, int] = await read_box(user)
        if len(box_d) == 0:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"{user.display_name} has no units!"))

        loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading {user.display_name}'s box",
                                                  embed=embeds.loading())
        await ctx.send(file=await image_to_discord(await compose_box(box_d), "box.png"),
                       content=ctx.author.mention,
                       embed=discord.Embed(title=f"{user.display_name}'s box", colour=discord.Color.gold()).set_image(
                           url="attachment://box.png"))
        await loading.delete()


def setup(_bot):
    _bot.add_cog(DrawCog(_bot))
