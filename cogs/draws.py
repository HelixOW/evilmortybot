import asyncio
from sqlite3 import Cursor
from typing import Optional, Dict, List, Tuple

import discord
from PIL.Image import Image
from discord.ext import commands
from discord.ext.commands import Context

import utilities.embeds as embeds
import utilities.reactions as emojis
from utilities import remove_trailing_whitespace, connection, all_banner_list, MemberMentionConverter, ssr_pattern, \
    send_paged_message
from utilities.banners import Banner, banner_by_name, unit_with_chance, BannerType, add_shaft
from utilities.image_composer import compose_banner_rotation, compose_multi_draw, compose_five_multi_draw, \
    compose_draw, compose_unit_multi_draw, compose_unit_five_multi_draw, compose_banner_list, compose_box
from utilities.units import Unit, image_to_discord, unit_by_vague_name, Grade

loading_image_url: str = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"


async def read_box(user: discord.Member) -> Dict[int, int]:
    cursor: Cursor = connection.cursor()
    row: Tuple[int, int]
    return {row[0]: row[1] for row in cursor.execute("""SELECT box_units.unit_id, box_units.amount
                                 FROM box_units INNER JOIN units u ON u.unit_id = box_units.unit_id
                                 WHERE user_id=? AND guild=?
                                 ORDER BY u.grade DESC, box_units.amount DESC;""", (user.id, user.guild.id))}


class DrawCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    async def display_draw_menu(self, ctx: Context, person: discord.Member,
                                from_banner: Banner, images: List[Image]):

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
                for x, y in enumerate(images)
            ]
        )

    async def build_menu(self, ctx: Context, prev_message: discord.Message, page: int = 0) -> None:
        of_banner: Banner = all_banner_list[page]
        summon_menu_emojis: List[str] = [emojis.LEFT_ARROW, emojis.NO_1,
                                         emojis.NO_10 if of_banner.banner_type == BannerType.ELEVEN else emojis.NO_5,
                                         emojis.WHALE, emojis.INFO, emojis.RIGHT_ARROW]
        await prev_message.clear_reactions()
        draw: discord.Message = prev_message

        await draw.edit(content=f"{ctx.message.author.mention}",
                        embed=discord.Embed(
                            title=all_banner_list[page].pretty_name
                        ).set_image(url=all_banner_list[page].background))

        if page == 0:
            await asyncio.gather(
                draw.add_reaction(summon_menu_emojis[1]),
                draw.add_reaction(summon_menu_emojis[2]),
                draw.add_reaction(summon_menu_emojis[3]),
                draw.add_reaction(summon_menu_emojis[4]),
                draw.add_reaction(summon_menu_emojis[5]),
            )
        elif page == len(all_banner_list) - 1:
            await asyncio.gather(
                draw.add_reaction(summon_menu_emojis[0]),
                draw.add_reaction(summon_menu_emojis[1]),
                draw.add_reaction(summon_menu_emojis[2]),
                draw.add_reaction(summon_menu_emojis[3]),
                draw.add_reaction(summon_menu_emojis[4]),
            )
        else:
            await asyncio.gather(
                draw.add_reaction(summon_menu_emojis[0]),
                draw.add_reaction(summon_menu_emojis[1]),
                draw.add_reaction(summon_menu_emojis[2]),
                draw.add_reaction(summon_menu_emojis[3]),
                draw.add_reaction(summon_menu_emojis[4]),
                draw.add_reaction(summon_menu_emojis[5]),
            )

        try:
            def check_banner(added_reaction, user):
                return user == ctx.message.author and str(added_reaction.emoji) in summon_menu_emojis

            reaction, _ = await self.bot.wait_for("reaction_add", check=check_banner)

            if emojis.RIGHT_ARROW in str(reaction.emoji):
                return await self.build_menu(ctx, prev_message=draw, page=page + 1)
            if emojis.LEFT_ARROW in str(reaction.emoji):
                return await self.build_menu(ctx, prev_message=draw, page=page - 1)
            if (emojis.NO_10 if all_banner_list[page].banner_type == BannerType.ELEVEN else emojis.NO_5) in str(
                    reaction.emoji):
                await draw.delete()
                return await self.multi(ctx, person=ctx.author, banner_name=all_banner_list[page].name[0])
            if emojis.NO_1 in str(reaction.emoji):
                await draw.delete()
                return await self.single(ctx, person=ctx.author, banner_name=all_banner_list[page].name[0])
            if emojis.WHALE in str(reaction.emoji):
                await draw.delete()
                return await self.shaft(ctx, person=ctx.author, banner_name=all_banner_list[page].name[0])
            if emojis.INFO in str(reaction.emoji):
                await draw.delete()
                return await self.banner(ctx, banner_name=all_banner_list[page].name[0])
        except asyncio.TimeoutError:
            pass

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
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                      description=f"Can't find the \"{banner_name}\" banner"
                                                      )
                                  )

        draw: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED.set_image(url=loading_image_url))

        if rot:
            units: Dict[Unit, int] = {}
            for _ in range(30 * 11):
                _unit: Unit = await unit_with_chance(from_banner, person)
                if _unit in units:
                    units[_unit] += 1
                else:
                    units[_unit]: int = 1
            connection.commit()
            await ctx.send(
                file=await image_to_discord(await compose_banner_rotation(
                    dict(sorted(units.items(), key=lambda x: x[0].grade.to_int()))
                ), "rotation.png"),
                content=f"{person.display_name} those are the units you pulled in 1 rotation" if person is ctx.author
                else f"{person.display_name} those are the units you pulled in 1 rotation coming from {ctx.author.display_name}",
                embed=discord.Embed(
                    title=f"{from_banner.pretty_name} ~ 1 Rotation (900 Gems)",
                ).set_image(url="attachment://rotation.png"))
            return await draw.delete()

        await self.display_draw_menu(ctx, person, from_banner,
                                     [await compose_multi_draw(from_banner=from_banner, user=person)
                                      if from_banner.banner_type == BannerType.ELEVEN else
                                      await compose_five_multi_draw(from_banner=from_banner, user=person)
                                      for _ in range(amount)])
        await draw.delete()

    @commands.command()
    @commands.guild_only()
    async def summon(self, ctx: Context):
        draw: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED)
        await self.build_menu(ctx, prev_message=draw)

    @commands.command()
    @commands.guild_only()
    async def single(self, ctx: Context, person: Optional[discord.Member], *, banner_name: str = "banner 1"):
        if person is None:
            person: discord.Member = ctx.author
        from_banner: Optional[Banner] = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                      description=f"Can't find the \"{banner_name}\" banner"))

        return await ctx.send(file=await compose_draw(from_banner, person),
                              content=f"{person.mention} this is your single"
                              if person is ctx.message.author else
                              f"{person.mention} this is your single coming from {ctx.author.mention}",
                              embed=discord.Embed(title=f"{from_banner.pretty_name} (1x summon)").set_image(
                                  url="attachment://unit.png"))

    @commands.command()
    @commands.guild_only()
    async def shaft(self, ctx: Context, person: Optional[MemberMentionConverter],
                    unit_name: Optional[str] = "Helix is awesome", *, banner_name: str = "banner 1"):
        if person is None:
            person: discord.Member = ctx.author

        if unit_name in ["banner", "part", "gssr", "race", "humans", "soluna", "commandments", "jp", "custom"]:
            banner_name: str = unit_name + " " + banner_name
            unit_name: str = "none"

        from_banner: Banner = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(
                                      title="Error",
                                      colour=discord.Color.dark_red(),
                                      description=f"Can't find the \"{banner_name}\" banner"
                                  ))

        unit_ssr: bool = False
        if ssr_pattern.match(unit_name, 0):
            unit_ssr: bool = True
            unit_name: str = ssr_pattern.sub("", unit_name)

        possible_units: List[int] = [a.unit_id for a in unit_by_vague_name(unit_name)]

        if len(possible_units) != 0 and len(
                [a for a in possible_units if a in [b.unit_id for b in from_banner.all_units]]) == 0:
            possible_other_banner: Optional[Banner] = None
            for b1 in all_banner_list:
                matching_units: List[Unit] = [x for x in b1.all_units if x.unit_id in possible_units]
                if len(matching_units) > 0:
                    possible_other_banner: Banner = b1
                    break
            from_banner: Banner = possible_other_banner

        if from_banner is None:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(
                                      title="Error",
                                      colour=discord.Color.dark_red(),
                                      description=f"Can't find any banner with {unit_name} in it"
                                  ))

        if not from_banner.shaftable:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(
                                      title="Error",
                                      colour=discord.Color.dark_red(),
                                      description=f"Can't get shafted on the \"{from_banner.pretty_name}\" banner"
                                  ))

        unit_to_draw: List[int] = [a.unit_id for a in unit_by_vague_name(unit_name)
                                   if a.unit_id in [b.unit_id for b in from_banner.all_units]]

        draw = await ctx.send(
            content=f"{person.mention} you are getting shafted" if person is ctx.author
            else f"{person.mention} you are getting shafted from {ctx.author.mention}",
            embed=discord.Embed(
                title="Shafting..."
            ).set_image(url=loading_image_url))

        rang: int = 11 if from_banner.banner_type == BannerType.ELEVEN else 5

        async def has_ssr(du: List[Unit]) -> bool:
            for u in du:
                if u.grade == Grade.SSR and len(unit_to_draw) == 0:
                    return True

                if u.unit_id in unit_to_draw:
                    if unit_ssr:
                        if u.grade == Grade.SSR:
                            return True
                    else:
                        return True
            return False

        i: int = 0
        drawn_units: List[Unit] = [(await unit_with_chance(from_banner, person)) for _ in range(rang)]
        drawn_ssrs: Dict[Unit, int] = {}
        for x in drawn_units:
            if x.grade == Grade.SSR:
                if x not in drawn_ssrs:
                    drawn_ssrs[x] = 1
                else:
                    drawn_ssrs[x] += 1

        while not await has_ssr(drawn_units) and i < 1000:
            i += 1
            drawn_units: List[Unit] = [(await unit_with_chance(from_banner, person)) for _ in range(rang)]
            for x in drawn_units:
                if x.grade == Grade.SSR:
                    if x not in drawn_ssrs:
                        drawn_ssrs[x] = 1
                    else:
                        drawn_ssrs[x] += 1

        connection.commit()
        multi_msg: str = "Multi" if i == 0 else "Multis"

        await ctx.send(
            file=await image_to_discord(
                await compose_unit_multi_draw(units=drawn_units,
                                              ssrs=drawn_ssrs) if from_banner.banner_type == BannerType.ELEVEN
                else await compose_unit_five_multi_draw(units=drawn_units),
                "units.png"),
            content=f"{person.mention}: Your shaft" if person is ctx.author
            else f"{person.mention}: Your shaft coming from {ctx.author.mention}",
            embed=discord.Embed(
                title=f"{from_banner.pretty_name} ({rang}x summon)",
                description=f"You did {i + 1}x {multi_msg}. \n With this being your final pull:").set_image(
                url="attachment://units.png"))
        await draw.delete()
        await add_shaft(person, i)

    @commands.command()
    @commands.guild_only()
    async def banner(self, ctx: Context, *, banner_name: str = "banner one"):
        from_banner: Banner = banner_by_name(banner_name)
        if from_banner is None:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                      description=f"Can't find the \"{banner_name}\" banner"
                                                      )
                                  )
        loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Banner",
                                                  embed=embeds.LOADING_EMBED)
        await ctx.send(
            file=await image_to_discord(await compose_banner_list(from_banner, "custom" in from_banner.name),
                                        "banner.png"),
            embed=discord.Embed(title=f"SSRs in {from_banner.pretty_name} ({from_banner.ssr_chance}%)").set_image(
                url="attachment://banner.png"),
            content=f"{ctx.author.mention}")
        await loading.delete()

    @commands.command()
    @commands.guild_only()
    async def box(self, ctx: Context, user: Optional[discord.Member]):
        if user is None:
            user: discord.Member = ctx.author
        box_d: Dict[int, int] = await read_box(user)
        if len(box_d) == 0:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                      description=f"{user.display_name} has no units!"))
        loading: discord.Member = await ctx.send(content=f"{ctx.author.mention} -> Loading {user.display_name}'s box",
                                                 embed=embeds.LOADING_EMBED)
        await ctx.send(file=await image_to_discord(await compose_box(box_d), "box.png"),
                       content=f"{ctx.author.mention}",
                       embed=discord.Embed(title=f"{user.display_name}'s box", colour=discord.Color.gold()).set_image(
                           url="attachment://box.png"))
        await loading.delete()


def setup(_bot):
    _bot.add_cog(DrawCog(_bot))
