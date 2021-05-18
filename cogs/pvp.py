import asyncio
import traceback

import utilities.reactions as emojis

from typing import Union, Coroutine
from discord.ext import commands
from discord.ext.commands import Context
from utilities.units import *
from utilities.image_composer import compose_team, compose_pvp, compose_random_select_team, compose_tarot

team_time_check: Dict[int, Dict[str, Union[int, Coroutine]]] = {}
in_pvp: List[discord.Member] = []

team_reroll_emojis = [emojis.NO_1, emojis.NO_2, emojis.NO_3, emojis.NO_4]


class PvPCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.command(name="show")
    async def show_cmd(self, ctx: Context, *, team: str):
        for x in [y.strip() for y in team.split(",")]:
            print(unit_by_name_or_id(x))
        await ctx.send(" ".join([unit_by_name_or_id(x)[0].emoji for x in [y.strip() for y in team.split(",")] if len(unit_by_name_or_id(x)) != 0]))
        # await ctx.send(ctx.author.mention, embed=embeds.DrawEmbed(), file=await image_to_discord(
        #     await compose_team([find_unit(x)[0] for x in [y.strip() for y in team.split(",")]])
        # ))

    @commands.command()
    @commands.guild_only()
    async def unit(self, ctx: Context, *, args: str = ""):
        attributes: Dict[str, Any] = parse_arguments(args)
        try:
            random_unit: Unit = get_random_unit(grades=attributes["grade"],
                                                types=attributes["type"],
                                                races=attributes["race"],
                                                events=attributes["event"],
                                                affections=attributes["affection"],
                                                names=attributes["name"],
                                                jp=attributes["jp"])

            await random_unit.set_icon()

            await ctx.send(content=f"{ctx.author.mention} this is your unit",
                           embed=embeds.DefaultEmbed(title=random_unit.name, colour=random_unit.discord_color())
                           .set_image(url="attachment://image.png"),
                           file=await random_unit.discord_icon())
        except LookupError:
            await ctx.send(content=ctx.author.mention,
                           embed=embeds.Unit.lookup_error(args))

    @commands.command()
    @commands.guild_only()
    async def pvp(self, ctx: Context, enemy: discord.Member, *, attr: str = ""):
        criteria: str = attr
        attr: Dict[str, Any] = parse_arguments(attr)
        proposed_team_p1: List[Unit] = [
            get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                            affections=attr["affection"], names=attr["name"], jp=attr["jp"])
            for _ in range(4)]
        proposed_team_p2: List[Unit] = [
            get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                            affections=attr["affection"], names=attr["name"], jp=attr["jp"])
            for _ in range(4)]

        try:
            replace_duplicates_in_team(attr, proposed_team_p1)
            replace_duplicates_in_team(attr, proposed_team_p2)
        except ValueError as e:
            return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                                  embed=embeds.Team.lookup_error(criteria))

        player1 = ctx.author

        if player1 in in_pvp or enemy in in_pvp:
            return await ctx.send(content=ctx.author.mention,
                                  embed=embeds.PvP.cooldown_error)

        changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

        async def send(player: discord.Member, last_message: Optional[discord.Message] = None) -> None:
            if last_message is not None:
                await last_message.delete()

            if player not in in_pvp:
                in_pvp.append(player)

            loading_message: discord.Message = await ctx.send(embed=embeds.loading())
            team_message: discord.Message = await ctx.send(
                file=await image_to_discord(await compose_team(
                    rerolled_team=proposed_team_p1 if player == player1 else proposed_team_p2,
                    re_units=changed_units)),
                content=f"{player.mention} please check if you have those units",
                embed=embeds.DrawEmbed())
            await loading_message.delete()

            for emoji in team_reroll_emojis:
                await team_message.add_reaction(emoji)

            def check_reroll(added_reaction, from_user):
                return str(added_reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣",
                                                     "4️⃣"] and added_reaction.message == team_message \
                       and from_user == player

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check_reroll, timeout=5)
                reaction = str(reaction.emoji)

                c_index = -1
                if "1️⃣" in reaction:
                    c_index = 0
                elif "2️⃣" in reaction:
                    c_index = 1
                elif "3️⃣" in reaction:
                    c_index = 2
                elif "4️⃣" in reaction:
                    c_index = 3

                if user == player1:
                    changed_units[c_index].append(proposed_team_p1[c_index])
                    proposed_team_p1[c_index] = get_random_unit(races=attr["race"], grades=attr["grade"],
                                                                types=attr["type"],
                                                                events=attr["event"],
                                                                affections=attr["affection"], names=attr["name"],
                                                                jp=attr["jp"])
                    replace_duplicates_in_team(attr, proposed_team_p1)
                else:
                    changed_units[c_index].append(proposed_team_p2[c_index])
                    proposed_team_p2[c_index] = get_random_unit(races=attr["race"], grades=attr["grade"],
                                                                types=attr["type"],
                                                                events=attr["event"],
                                                                affections=attr["affection"], names=attr["name"],
                                                                jp=attr["jp"])
                    replace_duplicates_in_team(attr, proposed_team_p2)

                await send(player=user, last_message=team_message)
            except asyncio.TimeoutError:
                if player in in_pvp:
                    in_pvp.remove(player)
                await team_message.delete()

        await send(player1)

        changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

        await send(enemy)

        await ctx.send(file=await image_to_discord(await compose_pvp(player1=player1,
                                                                     player2=enemy,
                                                                     team1=proposed_team_p1,
                                                                     team2=proposed_team_p2)))

    @commands.command()
    @commands.guild_only()
    async def team(self, ctx: Context, *, args: str = ""):
        attr: Dict[str, Any] = parse_arguments(args)
        amount: int = 1

        if ctx.author.id in team_time_check:
            team_time_check[ctx.author.id]["thread"].close()
            try:
                await (await ctx.fetch_message(team_time_check[ctx.author.id]["message"])).clear_reactions()
            except discord.NotFound as e:
                print(str(e))

        if len(attr["unparsed"]) != 0:
            try:
                amount: int = int(attr["unparsed"][0])
            except ValueError:
                pass

        if amount > 1:
            amount: int = min(amount, 15)

            loading: discord.Message = await ctx.send(content=ctx.author.mention, embed=embeds.loading())
            possible: List[Unit] = [get_random_unit_from_dict(attr) for _ in range(amount * 4)]
            teams: List[List[Unit]] = [[possible[i + 0], possible[i + 1], possible[i + 2], possible[i + 3]] for i in
                                       range(0, amount * 4, 4)]
            for i, ele in enumerate(teams):
                replace_duplicates_in_team(attr, ele)
            possible: List[Unit] = [item for sublist in teams for item in sublist]
            await ctx.send(ctx.author.mention,
                           file=await image_to_discord(await compose_random_select_team(possible)))
            return await loading.delete()

        try:
            proposed_team: List[Unit] = [
                get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                                affections=attr["affection"], names=attr["name"], jp=attr["jp"])
                for _ in range(4)]

            try:
                replace_duplicates_in_team(criteria=attr, team_to_deduplicate=proposed_team)
            except ValueError as e:
                return await ctx.send(content=f"{ctx.author.mention} -> {e}",
                                      embed=embeds.Team.lookup_error(args))

            if ctx.message.author in team_time_check:
                return await ctx.send(content=ctx.author.mention,
                                      embed=embeds.Team.cooldown_error)

            changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

            async def send_message(last_team_message=None):
                if last_team_message is not None:
                    await last_team_message.delete()

                loading_message: discord.Message = await ctx.send(embed=embeds.loading())
                team_message: discord.Message = await ctx.send(
                    file=await image_to_discord(await compose_team(
                        rerolled_team=proposed_team, re_units=changed_units)),
                    content=f"{ctx.author.mention} this is your team",
                    embed=embeds.DrawEmbed())
                await loading_message.delete()

                if ctx.author.id not in team_time_check:
                    team_time_check[ctx.author.id] = {}

                team_time_check[ctx.author.id]["message"] = team_message.id

                for emoji in team_reroll_emojis:
                    await team_message.add_reaction(emoji)

                def check_reroll(added_reaction, user):
                    return user == ctx.author and str(added_reaction.emoji) in team_reroll_emojis \
                           and added_reaction.message == team_message

                try:
                    team_time_check[ctx.author.id]["thread"] = self.bot.wait_for("reaction_add", check=check_reroll, timeout=60)
                    reaction, _ = await team_time_check[ctx.author.id]["thread"]
                    reaction = str(reaction.emoji)

                    c_index = -1
                    if "1️⃣" in reaction:
                        c_index = 0
                    elif "2️⃣" in reaction:
                        c_index = 1
                    elif "3️⃣" in reaction:
                        c_index = 2
                    elif "4️⃣" in reaction:
                        c_index = 3

                    changed_units[c_index].append(proposed_team[c_index])
                    proposed_team[c_index] = get_random_unit(races=attr["race"], grades=attr["grade"],
                                                             types=attr["type"],
                                                             events=attr["event"], affections=attr["affection"],
                                                             names=attr["name"],
                                                             jp=attr["jp"])

                    replace_duplicates_in_team(criteria=attr, team_to_deduplicate=proposed_team)
                    await send_message(last_team_message=team_message)
                except asyncio.TimeoutError:
                    team_time_check.pop(ctx.author.id)
                    await team_message.clear_reactions()

            await send_message()
        except LookupError:
            traceback.print_exc()
            await ctx.send(content=ctx.author.mention,
                           embed=embeds.Team.lookup_error(args))

    @commands.group()
    @commands.guild_only()
    async def tarot(self, ctx: Context):
        if ctx.invoked_subcommand is not None:
            return

        __units: List[int] = [ra.randint(1, 22) for _ in range(4)]
        __food: int = ra.randint(1, 4)

        async def send_msg(_units, _food) -> None:
            while any(_units.count(element) > 1 for element in _units):
                _units: List[int] = [ra.randint(1, 22) for _ in range(4)]

            loading: discord.Message = await ctx.send(content=ctx.author.mention, embed=embeds.loading())
            msg: discord.Message = await ctx.send(
                file=await image_to_discord(await compose_tarot(_units[0], _units[1], _units[2], _units[3], _food)),
                content=ctx.author.mention)
            await loading.delete()

            for emoji in [emojis.NO_1, emojis.NO_2, emojis.NO_3, emojis.NO_4]:
                await msg.add_reaction(emoji)

            def check(added_reaction, user):
                return user == ctx.author and str(added_reaction.emoji) in [emojis.NO_1, emojis.NO_2, emojis.NO_3,
                                                                            emojis.NO_4]

            try:
                added_reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=15)

                await msg.delete()

                if str(added_reaction.emoji) == emojis.NO_1:
                    _units[0] = ra.randint(1, 22)
                elif str(added_reaction.emoji) == emojis.NO_2:
                    _units[1] = ra.randint(1, 22)
                elif str(added_reaction.emoji) == emojis.NO_3:
                    _units[2] = ra.randint(1, 22)
                elif str(added_reaction.emoji) == emojis.NO_4:
                    _units[3] = ra.randint(1, 22)

                await send_msg(_units, _food)
            except asyncio.TimeoutError:
                await msg.clear_reactions()

        await send_msg(__units, __food)

    @tarot.command(name="rules")
    async def tarot_rules(self, ctx):
        await ctx.send(embed=embeds.HelpEmbed(help_title="Tarot Rules", description=
                                              """> Select 1 Unit from each row 
> Select 1 Food from the list underneath the units
                                              """))


def setup(_bot):
    _bot.add_cog(PvPCog(_bot))
