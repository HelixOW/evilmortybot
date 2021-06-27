import discord
import random
from discord.ext import commands
from discord.ext.commands import Context, MemberConverter
from typing import Dict, List, Optional
from utilities.units import Unit, unit_by_vague_name, Event, unit_by_id
from utilities import unit_list, flatten, ask, image_to_discord
from utilities.sql_helper import execute, exists, fetch_item, fetch_rows
from utilities.embeds import SuccessEmbed, ErrorEmbed, DrawEmbed
from utilities.image_composer import compose_draftable_units, compose_draft_trade, compose_drafted_units

# guild_id -> group name -> discord_user_id -> drafted units
draft_boards: Dict[int, Dict[str, Dict[int, List[Unit]]]] = {}

draft_channels: Dict[str, discord.TextChannel] = {}


def add_drafted_unit(group: str, drafted_unit: Unit, user: discord.Member):
    draft_boards[user.guild.id][group][user.id].append(drafted_unit)


def get_draftable_units(group: str, guild: discord.Guild):
    return [x for x in unit_list if
            x not in flatten(draft_boards[guild.id][group].values()) and not x.is_jp and x.event != Event.CUS]


async def allowed_draft_group(group: str, guild: discord.Guild):
    return await exists('SELECT * FROM "draft_groups" WHERE group_name=? AND guild=?', (group.lower(), guild.id))


async def register_usr(usr: discord.Member, group: str):
    await execute('INSERT OR IGNORE INTO "draft_users" (group_name, guild, usr) VALUES (?, ?, ?)',
                  (group.lower(), usr.guild.id, usr.id))


async def register_group(group: str, rounds: int, channel: discord.TextChannel):
    await execute(
        'INSERT OR IGNORE INTO "draft_groups" (group_name, guild, channel, closed, rounds) VALUES (?, ?, ?, 0, ?)',
        (group.lower(), channel.guild.id, channel.id, rounds))


async def close_group(group: str, guild: discord.Guild):
    await execute('UPDATE "draft_groups" SET closed=1 WHERE guild=? AND group_name=?',
                  (guild.id, group.lower()))


async def is_closed_group(group: str, guild: discord.Guild):
    return (await fetch_item('SELECT closed FROM "draft_groups" WHERE group_name=? AND guild=?',
                             (group.lower(), guild.id))) == 1


async def get_group_usrs(group: str, guild: discord.Guild) -> List[int]:
    return await fetch_rows('SELECT usr FROM "draft_users" WHERE group_name=? AND guild=?',
                            lambda x: x[0],
                            (group.lower(), guild.id))


async def get_group_rotations(group: str, guild: discord.Guild):
    return await fetch_item('SELECT rounds FROM "draft_groups" WHERE guild=? AND group_name=?', (guild.id, group.lower()))


async def add_draft_picks(usr: int, guild: discord.Guild, group: str, picks: List[Unit]):
    await execute('INSERT OR IGNORE INTO "draft_picks" (group_name, guild, usr, picked) VALUES (?, ?, ?, ?)',
                  (group.lower(), guild.id, usr, ",".join([str(x.unit_id) for x in picks])))


async def change_draft_picks(usr: int, guild: discord.Guild, group: str, picks: List[Unit]):
    await execute('UPDATE "draft_picks" SET picked=? WHERE guild=? AND group_name=? AND usr=?',
                  (",".join([str(x.unit_id) for x in picks]), guild.id, group.lower(), usr))


async def get_all_draft_picks(group: str, guild: discord.Guild) -> Dict[int, List[Unit]]:
    return {x: y for x, y in await fetch_rows('SELECT usr, picked FROM "draft_picks" WHERE group_name=? AND guild=?',
                                              lambda a: (a[0], [unit_by_id(int(b)) for b in a[1].split(",")]),
                                              (group.lower(), guild.id))}


async def get_draft_picks(usr: discord.Member, group: str) -> List[Unit]:
    return [unit_by_id(int(x)) for x in
            (await fetch_item('SELECT picked FROM "draft_picks" WHERE usr=? AND group_name=? AND guild=?',
                              (usr.id, group.lower(), usr.guild.id))).split(",")]


async def get_draft_picks_with_guild(usr: discord.Member, group: str, guild: discord.Guild) -> List[Unit]:
    return [unit_by_id(int(x)) for x in
           (await get_text(usr, group.lower(), guild)).split(",") if x.strip() != ""]


async def get_text(usr: discord.Member, group: str, guild: discord.Guild):
    re = await fetch_item('SELECT picked FROM "draft_picks" WHERE usr=? AND group_name=? AND guild=?',
                          (usr.id, group.lower(), guild.id))
    if not re:
        return ""
    return re


async def end_draft_group(group: str, guild: discord.Guild):
    await execute('DELETE FROM "draft_groups" WHERE guild=? AND group_name=?', (guild.id, group.lower()))


def cont_conv(x: str):
    if x.lower() in ("true", "yes", "y", "ye", "yeah", "1", "yup", "ok"):
        return "continue"
    elif x.lower() in ("stop", "s", "end"):
        return "stop"


async def ask_group(ctx: Context, msg: str, check: bool = True):
    group = await ask(ctx, msg, convert=str)

    if not group:
        return None

    group = group.strip().lower()

    if check:
        if not (await allowed_draft_group(group, ctx.guild)):
            await ctx.send(ctx.author.mention, embed=ErrorEmbed("No such group found."))
            return None

    return group


async def create_draft_board(guild: discord.Guild) -> List[str]:
    return await fetch_rows('SELECT group_name FROM "draft_groups" WHERE guild=?', lambda x: x[0], (guild.id, ))


class DraftCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    async def usrs_from_draft_board(self, guild: discord.Guild, group: str):
        return [(await self.bot.fetch_user(x)).display_name for x in draft_boards[guild.id][group]]

    async def draft_board_convert(self, guild: discord.Guild, group: str):
        return {await self.bot.fetch_user(x): draft_boards[guild.id][group][x] for x in draft_boards[guild.id][group]}

    @commands.group()
    async def draft(self, ctx: Context):
        draft_boards[ctx.guild.id] = {
            group.lower(): {
                usr: [u for u in await get_draft_picks_with_guild(await self.bot.fetch_user(usr), group, ctx.guild)]
                for usr in await get_group_usrs(group, ctx.guild)
            }
            for group in await create_draft_board(ctx.guild)
        }

        if ctx.invoked_subcommand:
            return

        group = await ask_group(ctx, ctx.author.mention + ": Which draft group would you like to start?")

        if not group:
            return

        await close_group(group, ctx.guild)

        usrs = await get_group_usrs(group, ctx.guild)
        random.shuffle(usrs)

        draft_boards[ctx.guild.id] = {
            group: {

            }
        }

        for usr in usrs:
            draft_boards[ctx.guild.id][group][usr] = []

        await ctx.send(ctx.author.mention, embed=SuccessEmbed(f"Draft {group} is ready to draft"))

        rounds = await get_group_rotations(group, ctx.guild)
        forward: bool = True

        for i in range(rounds):
            li = [await self.bot.fetch_user(u) for u in usrs]

            if not forward:
                li = reversed(li)

            forward = not forward

            for usr in li:
                draftable_units = get_draftable_units(group, ctx.guild)
                question = await ctx.send(f"{usr.mention}: Please select your unit",
                                          embed=DrawEmbed(title="Available Units"),
                                          file=await image_to_discord(await compose_draftable_units(draftable_units)))
                drafted_unit = await ask(ctx, question, lambda x: unit_by_vague_name(x.strip("-"), draftable_units),
                                         timeout=60 * 15, asked_person=usr,
                                         convert_failed="Can't find that unit",
                                         additional_check=lambda m: m.content.startswith("-"))

                while len(drafted_unit) == 0:
                    await ctx.send(f"Can't find that unit, or it's already been picked.")
                    drafted_unit = await ask(ctx,
                                             await ctx.send(f"{usr.mention}: Please select your unit",
                                                            embed=DrawEmbed(title="Available Units"),
                                                            file=await image_to_discord(
                                                                await compose_draftable_units(draftable_units))),
                                             lambda x: unit_by_vague_name(x.strip("-"), draftable_units),
                                             timeout=60 * 15,
                                             asked_person=usr,
                                             convert_failed="Can't find that unit",
                                             additional_check=lambda m: m.content.startswith("-"))

                if not isinstance(drafted_unit, Unit):
                    drafted_unit = drafted_unit[0]

                question = await ctx.send(f"{usr.mention}: Please confirm that `{drafted_unit.name}` is your unit.",
                                          embed=DrawEmbed(),
                                          file=await image_to_discord(await drafted_unit.set_icon()))
                confirm = await ask(ctx, question, cont_conv, timeout=60 * 2, asked_person=usr)

                while confirm != "continue":
                    question = await ctx.send(f"{usr.mention}: Please select your unit",
                                              embed=DrawEmbed(title="Available Units"),
                                              file=await image_to_discord(
                                                  await compose_draftable_units(draftable_units)))
                    drafted_unit = await ask(ctx, question, lambda x: unit_by_vague_name(x.strip("-"), draftable_units),
                                             timeout=60 * 15, asked_person=usr,
                                             convert_failed="Can't find that unit",
                                             additional_check=lambda m: m.content.startswith("-"))

                    while len(drafted_unit) == 0:
                        await ctx.send(f"Can't find that unit, or it's already been picked.")
                        drafted_unit = await ask(ctx,
                                                 await ctx.send(f"{usr.mention}: Please select your unit",
                                                                embed=DrawEmbed(title="Available Units"),
                                                                file=await image_to_discord(
                                                                    await compose_draftable_units(draftable_units))),
                                                 lambda x: unit_by_vague_name(x.strip("-"), draftable_units),
                                                 timeout=60 * 15,
                                                 asked_person=usr,
                                                 convert_failed="Can't find that unit",
                                                 additional_check=lambda m: m.content.startswith("-"))

                    if not isinstance(drafted_unit, Unit):
                        drafted_unit = drafted_unit[0]

                    question = await ctx.send(f"{usr.mention}: Please confirm that `{drafted_unit.name}` is your unit.",
                                              embed=DrawEmbed(),
                                              file=await image_to_discord(await drafted_unit.set_icon()))
                    confirm = await ask(ctx, question, cont_conv, timeout=60 * 2, asked_person=usr)

                draft_boards[ctx.guild.id][group][usr.id].append(drafted_unit)
                await ctx.send(f"{usr.mention} picked `{drafted_unit.name}`")

        for usr in draft_boards[ctx.guild.id][group]:
            await add_draft_picks(usr, ctx.guild, group, draft_boards[ctx.guild.id][group][usr])

        await ctx.send(
            embed=SuccessEmbed(f"Draft for {group} completed. Use `..draft list <group>` to see your drafted units."))

    @draft.command(name="trade")
    async def draft_trade(self, ctx: Context, wth: Optional[discord.Member] = None, *, group: Optional[str] = None):
        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": What group draft are you in?")

        if not group:
            return

        if not wth:
            wth = await MemberConverter().convert(ctx, await ask(ctx, f"{ctx.author.mention} Who do you want to trade with?", str))

        wth_picks = await get_draft_picks(wth, group)
        have_picks = await get_draft_picks(ctx.author, group)

        wanted_unit = (await ask(ctx, f"{ctx.author.mention} Which unit do you want?",
                                 lambda x: unit_by_vague_name(x, wth_picks)))[0]
        offered_unit = (await ask(ctx, f"{ctx.author.mention} What unit do you offer?",
                                  lambda x: unit_by_vague_name(x, have_picks)))[0]

        question = await ctx.send(f"{wth.mention}: Do you want to trade with `{ctx.author.display_name}`?",
                                  embed=DrawEmbed(),
                                  file=await image_to_discord(await compose_draft_trade(wanted_unit, offered_unit)))
        cont = await ask(ctx, question, cont_conv, timeout=60 * 15, asked_person=wth)

        if cont != "continue":
            return await ctx.send(f"{ctx.author.mention}: {wth.display_name} declined your trade offer")

        wth_picks.remove(wanted_unit)
        have_picks.remove(offered_unit)

        wth_picks.append(offered_unit)
        have_picks.append(wanted_unit)

        await change_draft_picks(wth.id, ctx.guild, group, wth_picks)
        await change_draft_picks(ctx.author.id, ctx.guild, group, have_picks)

        draft_boards[ctx.guild.id] = {
            group: await get_all_draft_picks(group, ctx.guild)
        }

        await ctx.send(ctx.author.mention, embed=SuccessEmbed("Trade successful."))

    @draft.command(name="list")
    async def draft_list(self, ctx: Context, of: Optional[discord.Member], *, group: Optional[str] = None):
        if not of:
            of = ctx.author

        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": What group draft should be shown?")

        if not group:
            return

        if ctx.guild.id not in draft_boards:
            draft_boards[ctx.guild.id] = {
                group: await get_all_draft_picks(group, ctx.guild)
            }

        if ctx.guild.id not in draft_boards:
            return await ctx.send(ctx.author.mention, embed=ErrorEmbed("No Draft existing."))

        if of.id not in draft_boards[ctx.guild.id][group]:
            return await ctx.send(ctx.author.mention, embed=ErrorEmbed(f"`{of.display_name}` didn't participate in draft."))

        await ctx.send(f"{ctx.author.mention}: {of.display_name} drafted units",
                       embed=DrawEmbed(),
                       file=await image_to_discord(
                           await compose_draftable_units(draft_boards[ctx.guild.id][group][of.id],
                                                         await get_group_rotations(group, ctx.guild))))

    @draft.command(name="export")
    async def draft_export(self, ctx: Context, *, group: Optional[str] = None):
        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": What draft group do you want to export?")

        if not group:
            return

        await ctx.send(file=await image_to_discord(await compose_drafted_units(self.draft_board_convert(ctx.guild, group))))

    @draft.command(name="end")
    async def draft_end(self, ctx: Context, *, group: Optional[str] = None):
        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": What draft group do you want to end?")

        if not group:
            return

        await end_draft_group(group, ctx.guild)
        await ctx.send(ctx.author.mention, embed=SuccessEmbed("Draft ended."))

    @draft.command(name="order")
    async def draft_order(self, ctx: Context, *, group: Optional[str] = None):
        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": What draft group do you want to see the order of?")

        if not group:
            return

        await ctx.send(ctx.author.mention, embed=DrawEmbed(title=f"Draft order of draft {group}",
                                                           description=",\n".join(
                                                               await self.usrs_from_draft_board(ctx.guild, group))))

    @draft.command(name="register")
    async def draft_register(self, ctx: Context, *, group: Optional[str] = None):
        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": What draft group do you want to register for?")

        if not group:
            return

        if await is_closed_group(group, ctx.guild):
            return await ctx.send(ctx.author.mention, embed=ErrorEmbed("Group is already closed."))

        await register_usr(ctx.author, group)
        await ctx.send(ctx.author.mention, embed=SuccessEmbed(f"Registered you for draft group {group}."))

    @draft.command(name="channel")
    async def draft_channel_register(self, ctx: Context, group: Optional[str] = None, closed: bool = False):
        if closed:
            if not group:
                group = await ask_group(ctx, ctx.author.mention + ": Which draft group should be closed?")

            if not group:
                return

            await close_group(group, ctx.guild)
            return await ctx.send(ctx.author.mention, embed=SuccessEmbed(f"Closed draft group {group}."))

        if not group:
            group = await ask_group(ctx, ctx.author.mention + ": Which group should use this channel?", check=False)

        if not group:
            return

        rounds = await ask(ctx, "How many draft rounds should be done?", int)

        await register_group(group, rounds, ctx.channel)
        await ctx.send(ctx.author.mention, embed=SuccessEmbed(f"Registered draft group {group} in this channel."))


def setup(_bot):
    _bot.add_cog(DraftCog(_bot))
