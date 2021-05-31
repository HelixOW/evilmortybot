import discord
import aiohttp
from discord.ext import commands
from discord.ext.commands import Context, has_permissions
from utilities.cc_register import *
from utilities.sql_helper import execute, fetch_item, rows
from io import BytesIO
from typing import Optional, AsyncGenerator


async def add_cc_role(role: discord.Role, cc: float, guild_cc: bool) -> None:
    await execute('INSERT INTO "cc_roles" VALUES (?, ?, ?, ?)', (role.id, role.guild.id, cc, 1 if guild_cc else 0))


async def is_cc_knighthood(guild: discord.Guild) -> bool:
    data: Optional[int] = await fetch_item('SELECT knighthood_cc FROM "cc_roles" WHERE guild=?',
                                           (guild.id,))

    return data == 1 if data is not None else False


async def get_cc_role(guild: discord.Guild, cc: float) -> Optional[int]:
    return await fetch_item('SELECT role_id FROM "cc_roles" WHERE guild=? AND cc<=? ORDER BY CC DESC',
                            (guild.id, cc))


async def get_cc_roles(guild: discord.Guild) -> AsyncGenerator[int, None]:
    async for row in rows('SELECT role_id FROM "cc_roles" WHERE guild=?', (guild.id,)):
        yield row[0]


class CCCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group(name="cc")
    @commands.guild_only()
    async def cc_cmd(self, ctx: Context):
        if ctx.invoked_subcommand is not None:
            return

        if len(ctx.message.attachments) == 0:
            return await ctx.send(f"{ctx.author.mention}: no image attached!")

        loading: discord.Message = await ctx.send(f"{ctx.author.mention}: Reading your CC...")
        async with aiohttp.ClientSession() as session:
            async with session.get(ctx.message.attachments[0].url) as resp:
                with BytesIO(await resp.read()) as a:
                    if await is_cc_knighthood(ctx.guild):
                        read_cc = await read_kh_cc_from_image(Image.open(a))

                        if read_cc == -1:
                            return await loading.edit(
                                content=f"{ctx.author.mention} Can't read CC from Image. Please make sure to provide a full screenshot")
                    else:
                        read_cc: float = await read_base_cc_from_image(Image.open(a))

                        if read_cc == -1:
                            return await loading.edit(
                                content=f"{ctx.author.mention} Can't read CC from Image. Please make sure to provide a full screenshot")
                    role_id: Optional[int] = await get_cc_role(ctx.guild, read_cc)

                    if role_id is None:
                        return await loading.edit(
                            content=f"{ctx.author.mention} no CC roles registered for {read_cc} CC!")

                    role: discord.Role = ctx.guild.get_role(role_id)

                    for cc_role in [ctx.guild.get_role(x) async for x in get_cc_roles(ctx.guild)]:
                        if cc_role in ctx.author.roles:
                            await ctx.author.remove_roles(cc_role)

                    await ctx.author.add_roles(role)
                    await loading.edit(content=f"Gave {role.name} to {ctx.author.mention}")

    @cc_cmd.command(name="role")
    @has_permissions(manage_roles=True)
    async def cc_role_register(self, ctx: Context, role: discord.Role, min_cc: float, is_knighthood_only: bool):
        await add_cc_role(role, min_cc, is_knighthood_only)
        await ctx.send(f"Role: {role.name} added!")


def setup(_bot):
    _bot.add_cog(CCCog(_bot))
