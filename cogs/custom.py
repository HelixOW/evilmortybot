from io import BytesIO
from typing import List, AsyncGenerator, Tuple

import PIL.Image as ImageLib
import aiohttp
import discord
from PIL.Image import Image
from discord.ext import commands
from discord.ext.commands import Context, MemberConverter

from utilities import embeds, ask, image_to_discord
from utilities.banners import create_custom_unit_banner
from utilities.image_composer import compose_unit_list
from utilities.units import compose_icon, Type, Race, Affection, Grade, \
    Unit, unit_list, Event, unit_by_id, all_affections, map_affection, map_race, map_grade, \
    map_attribute, unit_by_vague_name
from utilities.sql_helper import fetch_item, execute, rows, exists


async def get_next_custom_unit_id() -> int:
    return await fetch_item('SELECT unit_id FROM units WHERE event=? ORDER BY unit_id', ("custom",)) - 1


async def add_custom_unit(name: str, creator: int, type_enum: Type, grade: Grade, url: str, race: Race,
                          affection_str: str) -> None:
    u: Unit = Unit(unit_id=await get_next_custom_unit_id(),
                   name=name,
                   type_enum=type_enum,
                   grade=grade,
                   race=race,
                   event=Event.CUS,
                   affection_str=affection_str,
                   simple_name=str(creator),
                   icon_path=url)

    unit_list.append(u)
    await create_custom_unit_banner()

    await execute(
        'INSERT INTO "units" (unit_id, name, simple_name, type, grade, race, event, affection, icon_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (u.unit_id, u.name, str(creator), type_enum.value, grade.value, race.value, u.event.value, affection_str, url)
    )


async def remove_custom_unit(unit_name: str) -> None:
    await execute('DELETE FROM "units" WHERE name=? AND event=?', (unit_name, "custom"))


async def parse_custom_unit_ids(owner: int) -> AsyncGenerator[int, None]:
    async for row in rows('SELECT unit_id FROM "units" WHERE simple_name=?', (owner,)):
        yield row[0]


async def edit_custom_unit(to_set: str, values: List[str]) -> None:
    await execute('UPDATE "units" SET ' + to_set + ' WHERE name=?', tuple(values))


async def unit_exists(name: str) -> bool:
    return await exists('SELECT unit_id FROM "units" WHERE name=? AND event=?', (name, "custom"))


async def add_affection(name: str, owner: int) -> None:
    await execute('INSERT OR IGNORE INTO "affections" VALUES (?, ?)', (name.lower(), owner))


async def affection_exist(name: str) -> bool:
    return await exists('SELECT * FROM "affections" WHERE name=?', (name.lower(),))


async def get_affection_creator(name: str) -> int:
    return await fetch_item('SELECT creator FROM "affections" WHERE name=?', (name.lower(),))


async def update_affection_name(old_name: str, new_name: str) -> None:
    await execute('UPDATE "affections" SET name=? WHERE name=?', (new_name.lower(), old_name.lower()))


async def update_affection_owner(name: str, owner: int) -> None:
    await execute('UPDATE "affections" SET creator=? WHERE name=?', (owner, name.lower()))


async def remove_affection(name: str) -> None:
    await execute('DELETE FROM "affections" WHERE name=?', (name.lower(),))


async def convert_url_to_image(url: str) -> Tuple[Image, str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            with BytesIO(await resp.read()) as image_bytes:
                cop = ImageLib.open(image_bytes).copy()
    return cop, url


class CustomCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group()
    @commands.guild_only()
    async def custom(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await embeds.Custom.send_help(ctx, ctx.author.mention)

    @custom.command(name="add", aliases=["create", "+"])
    async def custom_create(self, ctx: Context):
        name = await ask(ctx,
                         "What do you want to name your unit?",
                         convert=str,
                         no_input="You need to provide a name for your unit.",
                         timeout=180)

        if name is None:
            return

        url: Tuple[Image, str] = await ask(ctx,
                                           "Please send a link to a image.",
                                           convert=convert_url_to_image,
                                           convert_failed="Did not provide a valid image url.",
                                           no_input="Your unit needs a icon.",
                                           timeout=180)

        if url is None:
            return

        race = await ask(ctx,
                         "What race is your unit?",
                         convert=map_race,
                         default_val=Race.UNKNOWN,
                         no_input="No race provided, assuming Unknown",
                         timeout=120)

        if race is None:
            race = Race.UNKNOWN

        grade = await ask(ctx,
                          "What grade is your unit? `R, SR, SSR, UR [WIP]`",
                          convert=map_grade,
                          default_val=Grade.SSR,
                          no_input="No grade provided, assuming SSR",
                          timeout=120)

        if grade is None:
            grade = Grade.SSR

        _type = await ask(ctx,
                          "What type is your unit? `(Red, Green, Blue)`",
                          convert=map_attribute,
                          default_val=Type.RED,
                          no_input="No type provided, assuming Red",
                          timeout=120)

        if _type is None:
            _type = Type.RED

        affection = await ask(ctx,
                              "What affection does your unit have? `affection list`",
                              convert=map_affection,
                              no_input="No affection provided, assuming no affection",
                              timeout=120)

        if affection is None:
            affection = Affection.NONE.value

        if await unit_exists(name):
            await ctx.reply(embed=embeds.Custom.already_exist(name))
            return await ctx.send(content=f"{ctx.author.mention}: {name} exists already!")

        with url[0] as img:
            _icon: Image = await compose_icon(attribute=_type, grade=grade, background=img)

        await ctx.send(
            file=await image_to_discord(img=_icon, image_name="unit.png", quality=200),
            content=f"{ctx.author.mention} this is your created unit",
            embed=discord.Embed(
                title=name,
                color=_type.to_discord_color()
            ).set_image(url="attachment://unit.png"))

        await add_custom_unit(name=name,
                              type_enum=_type,
                              grade=grade,
                              race=race,
                              affection_str=affection,
                              url=url[1],
                              creator=ctx.author.id)

    @custom.command(name="remove", aliases=["delete", "-"])
    async def custom_remove(self, ctx: Context):
        edit_unit: Unit = (await ask(ctx,
                                     "Which unit would you like to remove?",
                                     convert=unit_by_vague_name,
                                     convert_failed=lambda x: f"Unit '{x}' doesn't exist!",
                                     timeout=180,
                                     no_input="No unit provided."))[0]

        if edit_unit is None:
            return

        if int(edit_unit.simple_name) != ctx.author.id:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Custom.wrong_owner(edit_unit.name))

        await remove_custom_unit(edit_unit.name)
        unit_list.remove(edit_unit)
        await create_custom_unit_banner()
        return await ctx.send(content=ctx.author.mention, embed=embeds.Custom.Remove.success(edit_unit.name))

    @custom.command(name="list")
    async def custom_list(self, ctx: Context, owner: discord.Member = None):
        if not owner:
            owner = ctx.author

        owners_units: List[Unit] = [
            unit_by_id(unit_id)
            async for unit_id in parse_custom_unit_ids(owner.id)
        ]

        if len(owners_units) == 0:
            return await ctx.send(ctx.author.mention, embed=embeds.Custom.no_units(owner.display_name))

        with ctx.typing():
            await ctx.send(file=await image_to_discord(await compose_unit_list(owners_units)),
                           embed=embeds.DrawEmbed())

    @custom.command(name="edit")
    async def custom_edit(self, ctx: Context):
        edit_unit: Unit = (await ask(ctx,
                                     "Which unit would you like to edit?",
                                     convert=unit_by_vague_name,
                                     convert_failed=lambda a: f"Unit '{a}' doesn't exist!",
                                     timeout=180,
                                     no_input="No unit provided."))[0]

        if int(edit_unit.simple_name) != ctx.author.id:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Custom.wrong_owner(edit_unit.name))

        old_name: str = edit_unit.name

        to_set: List[str] = []
        values: List[str] = []
        changed: List[str] = []

        for attr, sql, change, question, conversion, post in [("grade", "grade", "Grade",
                                                               "What's the grade of your unit? `R, SR, SSR, UR [WIP]`",
                                                               map_grade, lambda a: a.value),
                                                              ("simple_name", "creator", "Owner",
                                                               "Who do you want to transfer Ownership to?",
                                                               str, None),
                                                              ("type", "type", "Type",
                                                               "What's the type of your unit? `(Red, Green, Blue)`",
                                                               map_attribute, lambda a: a.value),
                                                              ("name", "name", "Name",
                                                               "What's the name of your unit?", str, None),
                                                              ("icon_path", "url", "Icon",
                                                               "Please provide a link to a image. (Used for icon)",
                                                               convert_url_to_image, None),
                                                              ("race", "race", "Race",
                                                               "What's the race of your unit?",
                                                               map_race, lambda a: a.value),
                                                              ("affection", "affection", "Affection",
                                                               "What's the affection of your unit? (`list affection`)",
                                                               map_affection)]:
            x = await ask(ctx,
                          question,
                          convert=conversion)

            if isinstance(x, Tuple):
                if x[2]:
                    continue
                elif x[1]:
                    break

            if attr == "simple_name":
                x = await MemberConverter().convert(ctx, x)

            edit_unit.__setattr__(attr, x)

            if post:
                x = post(x)

            to_set.append(sql + "=?")
            values.append(x)
            changed.append(change)

        if len(to_set) == 0:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Custom.Edit.nothing_changed(edit_unit.name))

        to_set: str = ", ".join(to_set)

        values.append(old_name)
        await edit_custom_unit(to_set, values)

        await edit_unit.refresh_icon()
        return await ctx.send(content=ctx.author.mention, embed=embeds.Custom.Edit.success(edit_unit.name,
                                                                                           ", ".join(changed)))

    @commands.group()
    @commands.guild_only()
    async def affection(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            return await embeds.Affection.send_help(ctx, ctx.author.mention)

    @affection.command(name="add", aliases=["create", "plus", "+"])
    async def affection_add(self, ctx: Context, *, name: str):
        if name.lower in [Affection.SIN.value, Affection.KNIGHT.value, Affection.NONE.value, Affection.ANGEL.value,
                          Affection.CATASTROPHE.value,
                          Affection.COMMANDMENTS.value]:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.unmutable(name))

        if await affection_exist(name.lower()):
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.exists(name))

        await add_affection(name, ctx.author.id)
        all_affections.append(name.lower())
        await ctx.send(content=ctx.author.mention, embed=embeds.Affection.Add.success(name))

    @affection.command(name="edit")
    async def affection_edit(self, ctx: Context, old_name: str, *, new_name: str):
        if old_name.lower() not in all_affections:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.not_existing(old_name))

        if await get_affection_creator(old_name.lower()) != ctx.author.id:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.wrong_owner(old_name))

        await update_affection_name(old_name, new_name)
        all_affections.append(new_name.lower())
        await ctx.send(content=ctx.author.mention, embed=embeds.Affection.Edit.success(old_name, new_name))

    @affection.command(name="transfer", aliases=["move", ">"])
    async def affection_transfer(self, ctx: Context, name: str, owner: discord.Member):
        if name.lower() not in all_affections:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.not_existing(name))

        if await get_affection_creator(name.lower()) != ctx.author.id:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.wrong_owner(name))

        await update_affection_owner(name, owner.id)
        await ctx.send(content=ctx.author.mention, embed=embeds.Affection.Transfer.success(name, owner.display_name))

    @affection.command(name="remove", aliases=["delete", "minus", "-"])
    async def affection_remove(self, ctx: Context, *, name: str):
        if name.lower() not in all_affections:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.not_existing(name))

        if await get_affection_creator(name.lower()) != ctx.author.id:
            return await ctx.send(content=ctx.author.mention, embed=embeds.Affection.wrong_owner(name))

        await remove_affection(name)
        all_affections.remove(name.lower())
        await ctx.send(content=ctx.author.mention, embed=embeds.Affection.Remove.success(name))

    @affection.command(name="list")
    async def affection_list(self, ctx: Context):
        return await ctx.send(content=ctx.author.mention,
                              embed=embeds.DefaultEmbed(title="All Affections", description=",\n".join(all_affections)))

    @affection_add.error
    async def affection_add_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(ctx.author.mention, embed=embeds.Affection.Add.usage)

    @affection_edit.error
    async def affection_edit_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(ctx.author.mention, embed=embeds.Affection.Edit.usage)

    @affection_transfer.error
    async def affection_transfer_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(ctx.author.mention, embed=embeds.Affection.Transfer.usage)

    @affection_remove.error
    async def affection_remove_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(ctx.author.mention, embed=embeds.Affection.Remove.usage)


def setup(_bot):
    _bot.add_cog(CustomCog(_bot))
