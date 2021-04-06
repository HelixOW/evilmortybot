import asyncio
import utilities.embeds as embeds
import utilities.reactions as emojis

from discord.ext import commands
from discord.ext.commands import Context
from utilities.units import *
from utilities.image_composer import compose_team, compose_pvp, compose_random_select_team, compose_tarot


team_time_check: List[discord.Member] = []
pvp_time_check: List[discord.Member] = []

team_reroll_emojis = [emojis.NO_1, emojis.NO_2, emojis.NO_3, emojis.NO_4]


class PvPCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

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
                           embed=discord.Embed(title=random_unit.name, colour=random_unit.discord_color())
                           .set_image(url="attachment://unit.png"),
                           file=await random_unit.discord_icon())
        except LookupError:
            await ctx.send(content=f"{ctx.author.mention}",
                           embed=embeds.Unit.lookup_error)

    @commands.command()
    @commands.guild_only()
    async def pvp(self, ctx: Context, enemy: discord.Member, *, attr: str = ""):
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
                                  embed=embeds.Team.lookup_error)

        player1 = ctx.author

        if player1 in pvp_time_check or enemy in pvp_time_check:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.PvP.cooldown_error)

        changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

        async def send(player: discord.Member, last_message: Optional[discord.Message] = None) -> None:
            if last_message is not None:
                await last_message.delete()

            if player not in pvp_time_check:
                pvp_time_check.append(player)

            loading_message: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED)
            team_message: discord.Message = await ctx.send(
                file=await image_to_discord(await compose_team(
                    rerolled_team=proposed_team_p1 if player == player1 else proposed_team_p2,
                    re_units=changed_units), "team.png"),
                content=f"{player.mention} please check if you have those units",
                embed=discord.Embed().set_image(url="attachment://team.png"))
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
                if player in pvp_time_check:
                    pvp_time_check.remove(player)
                await team_message.delete()

        await send(player1)

        changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

        await send(enemy)

        await ctx.send(file=await image_to_discord(await compose_pvp(player1=player1,
                                                                     player2=enemy,
                                                                     team1=proposed_team_p1,
                                                                     team2=proposed_team_p2),
                                                   "pvp.png"))

    @commands.command()
    @commands.guild_only()
    async def team(self, ctx: Context, *, args: str = ""):
        attr: Dict[str, Any] = parse_arguments(args)
        amount: int = 1

        if len(attr["unparsed"]) != 0:
            try:
                amount: int = int(attr["unparsed"][0])
            except ValueError:
                pass

        if amount > 1:
            amount: int = min(amount, 15)

            loading: discord.Message = await ctx.send(content=ctx.author.mention, embed=embeds.LOADING_EMBED)
            possible: List[Unit] = [get_random_unit_from_dict(attr) for _ in range(amount * 4)]
            teams: List[Unit] = [[possible[i + 0], possible[i + 1], possible[i + 2], possible[i + 3]] for i in
                                 range(0, amount * 4, 4)]
            for i, ele in enumerate(teams):
                replace_duplicates_in_team(attr, ele)
            possible: List[Unit] = [item for sublist in teams for item in sublist]
            await ctx.send(ctx.author.mention,
                           file=await image_to_discord(await compose_random_select_team(possible),
                                                       "random_select_team.png"))
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
                                      embed=embeds.Team.lookup_error)

            if ctx.message.author in team_time_check:
                return await ctx.send(content=f"{ctx.author.mention}",
                                      embed=embeds.Team.cooldown_error)

            changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

            async def send_message(last_team_message=None):
                if last_team_message is not None:
                    await last_team_message.delete()

                if ctx.message.author not in team_time_check:
                    team_time_check.append(ctx.message.author)

                loading_message: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED)
                team_message: discord.Message = await ctx.send(
                    file=await image_to_discord(await compose_team(
                        rerolled_team=proposed_team, re_units=changed_units), "units.png"),
                    content=f"{ctx.author.mention} this is your team",
                    embed=discord.Embed().set_image(url="attachment://units.png"))
                await loading_message.delete()

                for emoji in team_reroll_emojis:
                    await team_message.add_reaction(emoji)

                def check_reroll(added_reaction, user):
                    return user == ctx.author and str(added_reaction.emoji) in team_reroll_emojis \
                           and added_reaction.message == team_message

                try:
                    reaction, _ = await self.bot.wait_for("reaction_add", check=check_reroll, timeout=5)
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
                    if ctx.message.author in team_time_check:
                        team_time_check.remove(ctx.author)
                    await team_message.clear_reactions()

            await send_message()
        except LookupError:
            await ctx.send(content=f"{ctx.author.mention}",
                           embed=embeds.Team.lookup_error)

    @commands.command()
    @commands.guild_only()
    async def tarot(self, ctx: Context):
        __units: List[int] = [ra.randint(1, 22) for _ in range(4)]
        __food: List[int] = ra.randint(1, 4)

        async def send_msg(_units, _food) -> None:
            while any(_units.count(element) > 1 for element in _units):
                _units: List[int] = [ra.randint(1, 22) for _ in range(4)]

            loading: discord.Message = await ctx.send(content=ctx.author.mention, embed=embeds.LOADING_EMBED)
            msg: discord.Message = await ctx.send(
                file=await image_to_discord(await compose_tarot(_units[0], _units[1], _units[2], _units[3], _food),
                                            "tarot.png"),
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


def setup(_bot):
    _bot.add_cog(PvPCog(_bot))
