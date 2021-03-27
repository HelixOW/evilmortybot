import discord
import utilities.embeds as embeds
from discord.ext import commands
from discord.ext.commands import Context
from typing import List, Optional, Tuple, Dict, Union, AsyncGenerator
from utilities import connection
from utilities.units import Unit, unit_by_id, image_to_discord, get_random_unit
from utilities.image_composer import compose_team, compose_pvp
from sqlite3 import Cursor, IntegrityError


async def create_tourney_profile(of: discord.Member, gc_id: int, cc: float, team: List[int]) -> bool:
    cursor: Cursor = connection.cursor()
    try:
        cursor.execute('INSERT INTO "tourney_profiles" VALUES (?, ?, ?, ?, ?, ?)',
                       (of.id, gc_id, cc, 0, 0, ",".join([str(x) for x in team])))
        connection.commit()
        return True
    except IntegrityError:
        return False


async def edit_tourney_friendcode(of: discord.Member, gc_id: int) -> bool:
    cursor: Cursor = connection.cursor()

    if cursor.execute('SELECT * FROM "tourney_profiles" WHERE discord_id=?', (of.id,)).fetchone() is None:
        return False

    cursor.execute('UPDATE "tourney_profiles" SET gc_code=? WHERE discord_id=?', (gc_id, of.id))
    connection.commit()
    return True


async def edit_tourney_cc(of: discord.Member, cc: float) -> bool:
    cursor: Cursor = connection.cursor()

    if cursor.execute('SELECT * FROM "tourney_profiles" WHERE discord_id=?', (of.id,)).fetchone() is None:
        return False

    cursor.execute('UPDATE "tourney_profiles" SET team_cc=? WHERE discord_id=?', (cc, of.id))
    connection.commit()
    return True


async def edit_tourney_team(of: discord.Member, team: List[int]) -> bool:
    cursor: Cursor = connection.cursor()

    if cursor.execute('SELECT * FROM "tourney_profiles" WHERE discord_id=?', (of.id,)).fetchone() is None:
        return False

    cursor.execute('UPDATE "tourney_profiles" SET team_unit_ids=? WHERE discord_id=?',
                   (",".join([str(x) for x in team]), of.id))
    connection.commit()
    return True


async def get_tourney_profile(of: discord.Member) -> Optional[Dict[str, Union[int, float, List[int]]]]:
    cursor: Cursor = connection.cursor()
    data: Optional[Tuple[int, float, int, int, str]] = cursor.execute(
        'SELECT gc_code, team_cc, won, lost, team_unit_ids FROM "tourney_profiles" WHERE discord_id=?',
        (of.id,)).fetchone()
    if data is None:
        return None
    return {
        "gc_code": data[0],
        "team_cc": data[1],
        "won": data[2],
        "lost": data[3],
        "team": [int(x) for x in data[4].split(",")]
    }


async def get_tourney_top_profiles() -> AsyncGenerator[Dict[str, int], None]:
    cursor: Cursor = connection.cursor()
    i: int
    row: Tuple[int, int]
    for i, row in enumerate(cursor.execute('SELECT won, discord_id'
                                           ' FROM "tourney_profiles"'
                                           ' ORDER BY won DESC'
                                           ' LIMIT 10').fetchall()):
        yield {
            "place": i + 1,
            "won": row[0],
            "member_id": row[1]
        }


async def add_tourney_challenge(author: discord.Member, to_fight: discord.Member) -> bool:
    cursor: Cursor = connection.cursor()

    try:
        cursor.execute('INSERT INTO "tourney_challenges" VALUES (?, ?)', (to_fight.id, author.id))
        connection.commit()
        return True
    except IntegrityError:
        return False


async def get_tourney_challengers(of: discord.Member) -> AsyncGenerator[int, None]:
    cursor: Cursor = connection.cursor()

    for row in cursor.execute('SELECT challenger_discord_id FROM "tourney_challenges" WHERE challenged_discord_id=?',
                              (of.id,)):
        yield row[0]


async def accept_challenge(challenged: discord.Member, challenger: discord.Member) -> None:
    return await start_tourney_game(challenged, challenger)


async def decline_challenge(challenged: discord.Member, challenger: discord.Member) -> None:
    cursor: Cursor = connection.cursor()

    cursor.execute('DELETE FROM "tourney_challenges" WHERE challenged_discord_id=? AND challenger_discord_id=?',
                   (challenged.id, challenger.id))

    connection.commit()


async def start_tourney_game(challenged: discord.Member, challenger: discord.Member) -> None:
    cursor: Cursor = connection.cursor()

    cursor.execute('DELETE FROM "tourney_challenges" WHERE challenged_discord_id=? AND challenger_discord_id=?',
                   (challenged.id, challenger.id))

    cursor.execute('INSERT INTO "tourney_games" VALUES (?, ?)', (challenged.id, challenger.id))
    connection.commit()


async def report_tourney_game(winner: discord.Member, looser: discord.Member) -> bool:
    cursor: Cursor = connection.cursor()

    if not await tourney_in_game_with(winner, looser):
        return False

    cursor.execute('DELETE FROM "tourney_games" WHERE (person1=? AND person2=?) OR (person1=? AND person2=?)',
                   (winner.id, looser.id, looser.id, winner.id))

    cursor.execute('UPDATE "tourney_profiles" SET won = won + 1 WHERE discord_id=?', (winner.id,))
    cursor.execute('UPDATE "tourney_profiles" SET lost = lost + 1 WHERE discord_id=?', (looser.id,))

    return True


async def tourney_in_game(player: discord.Member) -> bool:
    cursor: Cursor = connection.cursor()
    return len(cursor.execute('SELECT * FROM "tourney_games" WHERE person1=? OR person2=?',
                              (player.id, player.id)).fetchall()) != 0


async def tourney_in_game_with(p1: discord.Member, p2: discord.Member) -> bool:
    cursor: Cursor = connection.cursor()
    return len(
        cursor.execute('SELECT * FROM "tourney_games" WHERE (person1=? AND person2=?) OR (person1=? AND person2=?)',
                       (p1.id, p2.id, p2.id, p1.id)).fetchall()) != 0


class TournamentCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group(no_pm=True, aliases=["tourney"])
    @commands.guild_only()
    async def tournament(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

    @tournament.command(name="signup")
    async def tournament_signup(self, ctx: Context, gc_code: int = 0, team_cc: float = 0,
                                unit1: int = 0, unit2: int = 0, unit3: int = 0, unit4: int = 0):
        if 0 in [gc_code, team_cc, unit1, unit2, unit3, unit4]:
            return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

        _team: List[Unit] = []

        for unit_id in [unit1, unit2, unit3, unit4]:
            u: Unit = unit_by_id(unit_id)
            if u is None:
                return await ctx.send(f"{ctx.author.mention}: No Unit with ID: {unit_id} found!")

            _team.append(u)

        if await create_tourney_profile(ctx.author, gc_code, team_cc, [unit1, unit2, unit3, unit4]):
            await ctx.send(f"{ctx.author.mention}:",
                           file=await image_to_discord(await compose_team(_team), "team.png"),
                           embed=discord.Embed(
                               title="Registered Profile!",
                               colour=discord.Color.green(),
                               description=f"""
                CC: `{team_cc}`

                To edit your Team CC: 
                    `..tourney cc <new cc>`

                Friend code: `{gc_code}`

                To edit your Friend code:
                    `..tourney code <new friend code>`

                Registered Team:
                """
                           ).set_image(url="attachment://team.png"))
        else:
            await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Profile already exist",
                colour=discord.Color.red(),
                description="""
                To edit your team cc: `..tourney cc <new cc>`

                To edit your friend code: `..tourney code <new friend code>`
                """
            ))

    @tournament.command(name="code")
    async def tournament_code(self, ctx: Context, gc_code: int = 0):
        if gc_code == 0:
            return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

        if await edit_tourney_friendcode(ctx.author, gc_code):
            await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Updated Profile!",
                colour=discord.Color.green(),
                description=f"Your new friend code is: {gc_code}"
            ))
        else:
            await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Profile doesn't exist",
                colour=discord.Color.red(),
                description="To create one: `..tourney signup <friend code> <team cc>`"
            ))

    @tournament.command(name="cc")
    async def tournament_cc(self, ctx: Context, cc: float = 0):
        if cc == 0:
            return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

        if await edit_tourney_cc(ctx.author, cc):
            await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Updated Profile!",
                colour=discord.Color.green(),
                description=f"Your new cc is: {cc}"
            ))
        else:
            await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Profile doesn't exist",
                colour=discord.Color.red(),
                description="To create one: `..tourney signup <friend code> <team cc>`"
            ))

    @tournament.command(name="team")
    async def tournament_team(self, ctx: Context, unit1: int = 0, unit2: int = 0, unit3: int = 0, unit4: int = 0):
        if 0 in [unit1, unit2, unit3, unit4]:
            return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

        _team: List[Unit] = []

        for unit_id in [unit1, unit2, unit3, unit4]:
            u: Unit = unit_by_id(unit_id)
            if u is None:
                return await ctx.send(f"{ctx.author.mention}: No Unit with ID: {unit_id} found!")

            _team.append(u)

        if await edit_tourney_team(ctx.author, [unit1, unit2, unit3, unit4]):
            await ctx.send(f"{ctx.author.mention}:",
                           file=await image_to_discord(await compose_team(_team), "team.png"),
                           embed=discord.Embed(
                               title="Updated Profile!",
                               colour=discord.Color.green(),
                               description="Your new team is:"
                           ).set_image(url="attachment://team.png"))
        else:
            await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Profile doesn't exist",
                colour=discord.Color.red(),
                description="To create one: `..tourney signup <friend code> <team cc>`"
            ))

    @tournament.command(name="stats", aliases=["profile"])
    async def tournament_stats(self, ctx: Context, of: Optional[discord.Member]):
        if of is None:
            of: discord.Member = ctx.author

        data: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(of)
        if data is None:
            return await ctx.send(content=ctx.author.mention, embed=discord.Embed(
                title="Error",
                colour=discord.Color.red(),
                description=f"{of.display_name} has no registered profile"
            ))

        _team: List[Unit] = [unit_by_id(x) for x in data["team"]]

        return await ctx.send(content=ctx.author.mention,
                              file=await image_to_discord(await compose_team(_team), "team.png"),
                              embed=discord.Embed(
                                  title=f"Profile of: {of.display_name}",
                                  description=f"""
            Friend code: `{data["gc_code"]}` 

            Team CC: `{data["team_cc"]}`

            Won: `{data["won"]}`

            Lost: `{data["lost"]}`

            Registered Team:
            """
                              ).set_image(url="attachment://team.png"))

    @tournament.command(name="challenge", aliases=["fight"])
    async def tournament_challenge(self, ctx: Context, enemy: Optional[discord.Member]):
        if enemy is None or enemy == ctx.author:
            return await ctx.send(f"{ctx.author.mention}: Please provide a enemy you want to challenge")

        author_data: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(ctx.author)
        enemy_data: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(enemy)

        if author_data is None or enemy_data is None:
            return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Profile doesn't exist",
                colour=discord.Color.red(),
                description="To create one: `..tourney signup <friend code> <team cc>`"
            ))

        if author_data["team_cc"] > enemy_data["team_cc"]:
            return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Too high CC",
                colour=discord.Color.red(),
                description="You can't challenge someone who has __less__ CC then you."
            ))

        await add_tourney_challenge(ctx.author, enemy)
        await ctx.send(f"{enemy.mention}: {ctx.author.mention} has challenged you!")

    @tournament.command(name="accept")
    async def tournament_accept(self, ctx: Context, enemy: Optional[discord.Member]):
        if enemy is None or enemy == ctx.author:
            return await ctx.send(f"{ctx.author.mention}: Please provide a challenger you want to accept")

        if await tourney_in_game(enemy):
            return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Enemy still in a game",
                colour=discord.Color.red(),
                description=f"{enemy.display_name} is still in a game!"
            ))
        if await tourney_in_game(ctx.author):
            return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
                title="Error: Enemy still in a game",
                colour=discord.Color.red(),
                description="You are still in a game! \n\n `..tourney report <@Winner> <@Looser>` to finish the game"
            ))
        if enemy.id not in [x async for x in get_tourney_challengers(ctx.author)]:
            return await ctx.send(f"{ctx.author.mention}: {enemy.display_name} didn't challenge you!")

        p1_profile: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(ctx.author)
        p2_profile: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(enemy)

        p1_team: List[Unit] = [unit_by_id(x) for x in p1_profile["team"]]
        p2_team: List[Unit] = [unit_by_id(x) for x in p2_profile["team"]]

        await accept_challenge(ctx.author, enemy)
        await ctx.send(f"{ctx.author.mention} ({p1_profile['gc_code']}) vs {enemy.mention} ({p2_profile['gc_code']})",
                       file=await image_to_discord(await compose_pvp(ctx.author, p1_team, enemy, p2_team), "match.png"),
                       embed=discord.Embed(
                           title=f"{ctx.author.display_name} vs {enemy.display_name}",
                           description=f"{p1_profile['team_cc']}CC vs {p2_profile['team_cc']}CC \n\n Please do `..tourney report <@Winner> <@Looser>` to end the game!"
                       ).set_image(url="attachment://match.png"))

    @tournament.command(name="decline")
    async def tournament_decline(self, ctx: Context, enemy: Optional[discord.Member]):
        if enemy is None or enemy == ctx.author:
            return await ctx.send(f"{ctx.author.mention}: Please provide a challenger you want to accept")

        if enemy.id not in [x async for x in get_tourney_challengers(ctx.author)]:
            return await ctx.send(f"{ctx.author.mention}: {enemy.display_name} didn't challenge you!")

        await decline_challenge(ctx.author, enemy)
        await ctx.send(f"{enemy.mention} {ctx.author.mention} has declined your challenge.")

    @tournament.command(name="challengers")
    async def tournament_challengers(self, ctx: Context):
        if len([x async for x in get_tourney_challengers(ctx.author)]) == 0:
            return await ctx.send(f"{ctx.author.mention}: No challengers.")
        await ctx.send(ctx.author.mention, embed=discord.Embed(
            title=f"{ctx.author.display_name}'s challengers",
            description="\n".join(
                [(await self.bot.fetch_user(x)).display_name async for x in get_tourney_challengers(ctx.author)])
        ))

    @tournament.command(name="report")
    async def tournament_report(self, ctx: Context, winner: Optional[discord.Member], looser: Optional[discord.Member]):
        if winner == looser:
            return await ctx.send(f"{ctx.author.mention} Winner and looser can't be the same person!")

        if ctx.author not in (winner, looser):
            return await ctx.send(f"{ctx.author.mention}: You can't report the game of someone else.")

        if not tourney_in_game_with(winner, looser):
            return await ctx.send(f"{winner.display_name} & {looser.display_name} were not in a game!")

        await report_tourney_game(winner, looser)

        unit_to_build = get_random_unit()

        await ctx.send(f"{winner.mention} won against {looser.mention}",
                       file=await image_to_discord(unit_to_build.icon, "unit.png"),
                       embed=discord.Embed(
                           title=f"{looser.display_name} you now have to build out:",
                           description=unit_to_build.name
                       ).set_image(url="attachment://unit.png"))

    @tournament.command(name="top")
    async def tournament_top(self, ctx: Context):
        await ctx.send(ctx.author.mention, embed=discord.Embed(
            title="Tournament Participants with most wins",
            description="\n".join(
                [f"**{x['place']}.** {(await self.bot.fetch_user(x['member_id'])).mention} with {x['won']} wins"
                 async for x in get_tourney_top_profiles()])
        ))


def setup(_bot):
    _bot.add_cog(TournamentCog(_bot))
