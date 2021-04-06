import discord
import aiohttp
import utilities.embeds as embeds
import PIL.Image as ImageLib
from discord.ext import commands
from discord.ext.commands import Context
from typing import Dict, Any, Optional, List, AsyncGenerator
from io import BytesIO
from PIL.Image import Image
from sqlite3 import Cursor
from utilities import connection
from utilities.units import parse_custom_unit_args, compose_icon, image_to_discord, Type, Race, Affection, Grade, \
    Unit, unit_list, Event, unit_by_name, unit_by_id, all_affections
from utilities.banners import create_custom_unit_banner
from utilities.image_composer import compose_unit_list


async def get_next_custom_unit_id() -> int:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT unit_id FROM units WHERE event=? ORDER BY unit_id', ("custom",)).fetchone()[0] - 1


async def add_custom_unit(name: str, creator: int, type_enum: Type, grade: Grade, url: str, race: Race,
                          affection_str: str) -> None:
    cursor: Cursor = connection.cursor()
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
    create_custom_unit_banner()

    cursor.execute(
        'INSERT INTO units (unit_id, name, simple_name, type, grade, race, event, affection, icon_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (u.unit_id, u.name, str(creator), type_enum.value, grade.value, race.value, u.event.value, affection_str, url)
    )
    connection.commit()


async def remove_custom_unit(unit_name: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('DELETE FROM main.units WHERE name=? AND event=?', (unit_name, "custom"))
    connection.commit()


async def parse_custom_unit_ids(owner: int) -> AsyncGenerator[int, None]:
    cursor = connection.cursor()
    for row in cursor.execute('SELECT unit_id FROM units WHERE simple_name=?', (owner,)).fetchall():
        yield row[0]


async def edit_custom_unit(to_set: str, values: List[str]) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute("UPDATE custom_units SET " + to_set + " WHERE name=?", tuple(values))
    connection.commit()


async def unit_exists(name: str) -> bool:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT unit_id FROM units WHERE name=? AND event=?', (name, "custom")).fetchone() is not None


async def add_affection(name: str, owner: int) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('INSERT OR IGNORE INTO affections VALUES (?, ?)', (name.lower(), owner))
    connection.commit()


async def affection_exist(name: str) -> bool:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT * FROM affections WHERE name=?', (name.lower(),)).fetchone() is not None


async def get_affection_creator(name: str) -> int:
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT creator FROM affections WHERE name=?', (name.lower(),)).fetchone()[0]


async def update_affection_name(old_name: str, new_name: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('UPDATE affections SET name=? WHERE name=?', (new_name.lower(), old_name.lower()))
    connection.commit()


async def update_affection_owner(name: str, owner: int) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('UPDATE affections SET creator=? WHERE name=?', (owner, name.lower()))
    connection.commit()


async def remove_affection(name: str) -> None:
    cursor: Cursor = connection.cursor()
    cursor.execute('DELETE FROM affections WHERE name=?', (name.lower(),))
    connection.commit()


class CustomCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group()
    @commands.guild_only()
    async def custom(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"{ctx.author.mention}:", embed=embeds.CUSTOM_HELP_EMBED)

    @custom.command(name="add", aliases=["create", "+"])
    async def custom_create(self, ctx: Context, *, args: Optional[str] = ""):
        data: Dict[str, Any] = parse_custom_unit_args(args)

        if data["url"] == "" or data["name"] == "" or data["type"] is None or data["grade"] is None:
            return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_ADD_COMMAND_USAGE_EMBED)

        if await unit_exists(data["name"]):
            return await ctx.send(content=f"{ctx.author.mention}: {data['name']} exists already!")

        async with aiohttp.ClientSession() as session:
            async with session.get(data["url"]) as resp:
                with BytesIO(await resp.read()) as image_bytes:
                    _icon: Image = await compose_icon(attribute=data["type"], grade=data["grade"],
                                                      background=ImageLib.open(image_bytes))

                    await ctx.send(
                        file=await image_to_discord(img=_icon, image_name="unit.png"),
                        content=f"{ctx.author.mention} this is your created unit",
                        embed=discord.Embed(
                            title=data["name"],
                            color=discord.Color.red() if data["type"] == Type.RED
                            else discord.Color.blue() if data["type"] == Type.BLUE
                            else discord.Color.green()
                        ).set_image(url="attachment://unit.png"))

                    if data["race"] is None:
                        data["race"]: Race = Race.UNKNOWN

                    if data["affection"] is None:
                        data["affection"]: str = Affection.NONE.value

                    await add_custom_unit(name=data["name"],
                                          type_enum=data["type"],
                                          grade=data["grade"],
                                          race=data["race"],
                                          affection_str=data["affection"],
                                          url=data["url"],
                                          creator=ctx.author.id)

    @custom.command(name="remove", aliases=["delete", "-"])
    async def custom_remove(self, ctx: Context, *, args: Optional[str] = ""):
        data: Dict[str, Any] = parse_custom_unit_args(args)
        if data["name"] == "":
            return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_REMOVE_COMMAND_USAGE_EMBED)

        edit_unit: Unit = unit_by_name(data["name"])

        if int(edit_unit.simple_name) != ctx.author.id:
            return await ctx.send(content=f"{ctx.author.mention}", embed=discord.Embed(
                title="Error with ..custom remove", colour=discord.Color.dark_red(),
                description=f"**{edit_unit.name}** wasn't created by you!"))

        await remove_custom_unit(data["name"])
        unit_list.remove(edit_unit)
        create_custom_unit_banner()
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED)

    @custom.command(name="list")
    async def custom_list(self, ctx: Context, *, args: Optional[str] = ""):
        data: Dict[str, Any] = parse_custom_unit_args(args)
        if data["owner"] == 0:
            return await ctx.send(content=f"{ctx.author.mention}: Specified Owner didn't create any custom units yet")

        owners_units: List[Unit] = [
            unit_by_id(unit_id)
            async for unit_id in parse_custom_unit_ids(data["owner"])
        ]

        loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Units",
                                                  embed=embeds.LOADING_EMBED)
        await ctx.send(file=await image_to_discord(await compose_unit_list(owners_units), "units.png"),
                       embed=discord.Embed().set_image(url="attachment://units.png"))
        await loading.delete()

    @custom.command(name="edit")
    async def custom_edit(self, ctx: Context, *, args: Optional[str] = ""):
        data: Dict[str, Any] = parse_custom_unit_args(args)
        if data["name"] == "":
            return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_USAGE_EMBED)

        edit_unit: Unit = unit_by_name(data["name"])

        if int(edit_unit.simple_name) != ctx.author.id:
            return await ctx.send(content=f"{ctx.author.mention}", embed=discord.Embed(
                title="Error with ..custom remove", colour=discord.Color.dark_red(),
                description=f"**{edit_unit.name}** wasn't created by you!"))

        to_set: List[str] = []
        values: List[str] = []
        if data["grade"] is not None:
            edit_unit.grade = data["grade"]
            to_set.append("grade=?")
            values.append(data["grade"].value)
        if data["owner"] != 0:
            to_set.append("creator=?")
            values.append(data["owner"])
        if data["type"] is not None:
            edit_unit.type = data["type"]
            to_set.append("type=?")
            values.append(data["type"].value)
        if data["updated_name"] != "":
            edit_unit.name = data["updated_name"]
            to_set.append("name=?")
            values.append(data["updated_name"])
        if data["url"] != "":
            edit_unit.icon_path = data["url"]
            to_set.append("url=?")
            values.append(data["url"])
        if data["race"] is not None:
            edit_unit.race = data["race"]
            to_set.append("race=?")
            values.append(data["race"].value)
        if data["affection"] is not None:
            edit_unit.affection = data["affection"]
            to_set.append("affection=?")
            values.append(data["affection"])

        if len(to_set) == 0:
            return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)

        to_set: str = ", ".join(to_set)

        values.append(data["name"])
        await edit_custom_unit(to_set, values)

        await edit_unit.refresh_icon()
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)

    @commands.group()
    @commands.guild_only()
    async def affection(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            return await embeds.affection_help(ctx, ctx.author.mention)

    @affection.command(name="add", aliases=["create", "plus", "+"])
    async def affection_add(self, ctx: Context, *, name: str):
        if name.lower in [Affection.SIN.value, Affection.KNIGHT.value, Affection.NONE.value, Affection.ANGEL.value,
                          Affection.CATASTROPHE.value,
                          Affection.COMMANDMENTS.value]:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.Affection.unmutable_error)

        if await affection_exist(name.lower()):
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.Affection.exists_error)

        await add_affection(name, ctx.author.id)
        all_affections.append(name.lower())
        await ctx.send(content=f"{ctx.author.mention}", embed=embeds.Affection.Add.success)

    @affection.command(name="edit")
    async def affection_edit(self, ctx: Context, old_name: str, *, new_name: str):
        if old_name.lower() not in all_affections:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.Affection.edited)

        if await get_affection_creator(old_name.lower()) != ctx.author.id:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error with ..affections edit",
                                                      colour=discord.Color.dark_red(),
                                                      description=f"**{old_name.lower()}** is not your affection!"))

        await update_affection_name(old_name, new_name)
        all_affections.append(new_name.lower())
        await ctx.send(content=f"{ctx.author.mention}", embed=embeds.Affection.edited)

    @affection.command(name="transfer", aliases=["move", ">"])
    async def affection_transfer(self, ctx: Context, name: str, owner: discord.Member):
        if name.lower() not in all_affections:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.Affection.edited)

        if await get_affection_creator(name.lower()) != ctx.author.id:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error with ..affections edit",
                                                      colour=discord.Color.dark_red(),
                                                      description=f"**{name.lower()}** is not your affection!"))

        await update_affection_owner(name, owner.id)
        await ctx.send(content=f"{ctx.author.mention}", embed=embeds.Affection.edited)

    @affection.command(name="remove", aliases=["delete", "minus", "-"])
    async def affection_remove(self, ctx: Context, *, name: str):
        if name.lower() not in all_affections:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.Affection.removed)

        if await get_affection_creator(name.lower()) != ctx.author.id:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=discord.Embed(title="Error with ..affections edit",
                                                      colour=discord.Color.dark_red(),
                                                      description=f"**{name.lower()}** is not your affection!"))
        await remove_affection(name)
        all_affections.remove(name.lower())
        await ctx.send(content=f"{ctx.author.mention}", embed=embeds.Affection.removed)

    @affection.command(name="list")
    async def affection_list(self, ctx: Context):
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="All Affections", description=",\n".join(all_affections)))

    @affection_add.error
    async def affection_add_error(self, ctx: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(ctx.author.mention, embed=embeds.Affection.Add.usage)

def setup(_bot):
    _bot.add_cog(CustomCog(_bot))
