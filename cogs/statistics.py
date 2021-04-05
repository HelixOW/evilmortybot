import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import List, Dict, Any, AsyncGenerator, Union, Tuple, Optional
from enum import Enum
from sqlite3 import Cursor
from utilities import StatsContext, connection
from utilities.banners import get_user_pull
from utilities.embeds import Stats as embeds


class LeaderboardType(Enum):
    LUCK: str = "luck"
    MOST_SSR: str = "ssrs"
    MOST_UNITS: str = "units"
    MOST_SHAFTS: str = "shafts"


def map_leaderboard(raw_leaderboard: str) -> LeaderboardType:
    raw_leaderboard = raw_leaderboard.replace(" ", "").lower()
    if raw_leaderboard in ["ssr", "ssrs", "mostssr", "mostssrs"]:
        return LeaderboardType.MOST_SSR
    if raw_leaderboard in ["units", "unit", "mostunits", "mostunit"]:
        return LeaderboardType.MOST_UNITS
    if raw_leaderboard in ["shaft", "shafts", "mostshafts", "mostshaft"]:
        return LeaderboardType.MOST_SHAFTS
    return LeaderboardType.LUCK


class TopCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    async def get_top_shafts(self, guild: discord.Guild, limit: int = 10) -> AsyncGenerator[Dict[str, Union[int, str]], None]:
        cursor: Cursor = connection.cursor()
        i: int
        row: Tuple[int, int]
        for i, row in enumerate(cursor.execute(
                'SELECT user_id,'
                ' shafts'
                ' FROM user_pulls'
                ' WHERE guild=? AND pull_amount > 99'
                ' ORDER BY shafts'
                ' DESC LIMIT ?',
                (guild.id, limit)).fetchall()):
            try:
                yield {"place": i + 1, "name": (await self.bot.fetch_user(row[0])).mention, "shafts": row[1]}
            except discord.NotFound:
                connection.cursor().execute(
                    'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                    (guild.id, row[0]))
                yield {"place": i + 1, "name": "User", "shafts": row[1]}

    async def get_top_lucky(self, guild: discord.Guild, limit: int = 10) -> AsyncGenerator[Dict[str, Union[int, str, float]], None]:
        cursor: Cursor = connection.cursor()
        i: int
        row: Tuple[int, int, float]
        for i, row in enumerate(cursor.execute(
                'SELECT user_id,'
                ' pull_amount,'
                ' round((CAST(ssr_amount as REAL)/CAST(pull_amount as REAL)), 4) * 100 percent '
                'FROM user_pulls'
                ' WHERE guild=? AND pull_amount > 99'
                ' ORDER BY percent'
                ' DESC LIMIT ?',
                (guild.id, limit))):
            try:
                yield {"place": i + 1, "name": (await self.bot.fetch_user(row[0])).mention, "luck": round(row[2], 2),
                       "pull-amount": row[1]}
            except discord.NotFound:
                connection.cursor().execute(
                    'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                    (guild.id, row[0]))
                yield {"place": i + 1, "name": "User", "luck": round(row[2], 2), "pull-amount": row[1]}

    async def get_top_ssrs(self, guild: discord.Guild, limit: int = 10) -> AsyncGenerator[Dict[str, Union[int, str]], None]:
        cursor: Cursor = connection.cursor()
        i: int
        row: Tuple[int, int, int]
        for i, row in enumerate(cursor.execute(
                'SELECT user_id,'
                ' ssr_amount,'
                ' pull_amount'
                ' FROM user_pulls WHERE guild=? AND pull_amount > 99'
                ' ORDER BY ssr_amount'
                ' DESC LIMIT ?',
                (guild.id, limit))):
            try:
                yield {"place": i + 1, "name": (await self.bot.fetch_user(row[0])).mention, "ssrs": row[1],
                       "pull-amount": row[2]}
            except discord.NotFound:
                connection.cursor().execute(
                    'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                    (guild.id, row[0]))
                yield {"place": i + 1, "name": "User", "ssrs": row[1], "pull-amount": row[2]}

    async def get_top_units(self, guild: discord.Guild, limit: int = 10) -> AsyncGenerator[Dict[str, Union[int, str]], None]:
        cursor: Cursor = connection.cursor()
        i: int
        row: Tuple[int, int]
        for i, row in enumerate(cursor.execute(
                'SELECT user_id,'
                ' pull_amount'
                ' FROM user_pulls'
                ' WHERE guild=? AND pull_amount > 99'
                ' ORDER BY pull_amount'
                ' DESC LIMIT ?',
                (guild.id, limit))):
            try:
                yield {"place": i + 1, "name": (await self.bot.fetch_user(row[0])).mention, "pull-amount": row[1]}
            except discord.NotFound:
                connection.cursor().execute(
                    'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                    (guild.id, row[0]))
                yield {"place": i + 1, "name": "User", "pull-amount": row[1]}

    async def get_top_users(self, guild: discord.Guild, action: LeaderboardType = LeaderboardType.LUCK, limit: int = 10) -> \
            List[Dict[str, Any]]:
        if action == LeaderboardType.MOST_SHAFTS:
            return [x async for x in self.get_top_shafts(guild, limit)]
        if action == LeaderboardType.LUCK:
            return [x async for x in self.get_top_lucky(guild, limit)]
        if action == LeaderboardType.MOST_SSR:
            return [x async for x in self.get_top_ssrs(guild, limit)]
        if action == LeaderboardType.MOST_UNITS:
            return [x async for x in self.get_top_units(guild, limit)]

    @commands.group()
    async def top(self, ctx: Context):
        if ctx.invoked_subcommand is not None:
            return
        lucky: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.LUCK, 5)
        most_ssr: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.MOST_SSR, 5)
        most_pulled: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.MOST_UNITS, 5)
        most_shafted: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.MOST_SHAFTS, 5)

        if len(lucky) == 0:
            return await ctx.send(embed=embeds.NO_SUMMON_EMBED)

        await ctx.send(
            embed=discord.Embed()
            .add_field(
                name="Lucky",
                value="\n".join([f"**{data['place']}.** {data['name']} (*{data['luck']}%*)" for data in lucky])
            ).add_field(
                name="SSRs",
                value="\n".join([f"**{data['place']}.** {data['name']} (*{data['ssrs']}*)" for data in most_ssr])
            ).add_field(
                name="\u200b",
                value="\u200b"
            ).add_field(
                name="Units",
                value="\n".join([f"**{data['place']}.** {data['name']} (*{data['pull-amount']}*)" for data in most_pulled]),
            ).add_field(
                name="Shafts",
                value="\n".join([f"**{data['place']}.** {data['name']} (*{data['shafts']}*)" for data in most_shafted])
            ).add_field(
                name="\u200b"*2,
                value="\u200b"
            ).set_footer(
                text="Do ..top [luck, ssr, unit, shaft] for top 10"
            ).set_thumbnail(url=ctx.guild.icon_url)
            .set_author(
                name=f"Leaderboard in {ctx.guild.name}",
                icon_url="http://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/leaderboard_icon.png"
            )
        )

    @top.command(name="luck", aliases=["lucky", "luckiness"])
    async def top_luck(self, ctx: Context):
        top_users: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.LUCK)
        if len(top_users) == 0:
            return await ctx.send(embed=embeds.NO_SUMMON_EMBED)

        await ctx.send(
            embed=discord.Embed(
                description='\n'.join([
                    "**{}.** {} with a *{}%* SSR drop rate in their pulls. (Total: *{}*)".format(top_user["place"],
                                                                                                 top_user["name"],
                                                                                                 top_user["luck"],
                                                                                                 top_user[
                                                                                                     "pull-amount"])
                    for top_user in top_users]),
                colour=discord.Colour.gold()
            ).set_thumbnail(url=ctx.guild.icon_url)
            .set_author(
                name=f"Luckiest Members in {ctx.guild.name}",
                icon_url="http://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/data/images/leaderboard_icon.png"
            )
        )

    @top.command(name="ssrs", aliases=["ssr"])
    async def top_ssrs(self, ctx: Context):
        top_users: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.MOST_SSR)
        if len(top_users) == 0:
            return await ctx.send(embed=embeds.NO_SUMMON_EMBED)
        await ctx.send(
            embed=discord.Embed(
                title=f"Members with most drawn SSRs in {ctx.guild.name}",
                description='\n'.join([
                    "**{}.** {} with *{} SSRs*. (Total: *{}*)".format(top_user["place"],
                                                                      top_user["name"],
                                                                      top_user["ssrs"],
                                                                      top_user["pull-amount"])
                    for top_user in top_users]),
                colour=discord.Colour.gold()
            ).set_thumbnail(url=ctx.guild.icon_url)
        )

    @top.command(name="units", aliases=["unit"])
    async def top_units(self, ctx: Context):
        top_users: List[Dict[str, Any]] = await self.get_top_users(ctx.guild, LeaderboardType.MOST_UNITS)
        if len(top_users) == 0:
            return await ctx.send(embed=embeds.NO_SUMMON_EMBED)
        await ctx.send(
            embed=discord.Embed(
                title=f"Members with most drawn Units in {ctx.guild.name}",
                description='\n'.join([
                    "**{}.** {} with *{} Units*".format(top_user["place"],
                                                        top_user["name"],
                                                        top_user["pull-amount"])
                    for top_user in top_users]),
                colour=discord.Colour.gold()
            ).set_thumbnail(url=ctx.guild.icon_url)
        )

    @top.command(name="shafts", aliases=["shaft"])
    async def top_shafts(self, ctx: Context):
        top_users: List[Dict[str, Any]] = await self.get_top_users(ctx.message.guild, LeaderboardType.MOST_SHAFTS)
        if len(top_users) == 0:
            return await ctx.send(embed=embeds.NO_SUMMON_EMBED)
        return await ctx.send(
            embed=discord.Embed(
                title=f"Members with most Shafts in {ctx.guild.name}",
                description='\n'.join([
                    "**{}.** {} with *{} Shafts*".format(top_user["place"],
                                                         top_user["name"],
                                                         top_user["shafts"])
                    for top_user in top_users]),
                colour=discord.Colour.gold()
            ).set_thumbnail(url=ctx.guild.icon_url)
        )

    @commands.group()
    async def stats(self, ctx: StatsContext, person: Optional[discord.Member]):
        if person is None:
            person: discord.Member = ctx.author

        data: Dict[str, int] = await get_user_pull(person)

        ctx.save_stats({
            "data": data,
            "ssrs": data["ssr_amount"] if len(data) != 0 else 0,
            "pulls": data["pull_amount"] if len(data) != 0 else 0,
            "shafts": data["shafts"] if len(data) != 0 else 0,
            "percent": round((data["ssr_amount"] / data["pull_amount"] if len(data) != 0 else 0) * 100, 2),
            "person": person
        })

        if ctx.invoked_subcommand is None:
            return await self.stats_luck(ctx)

    @stats.command(name="luck", aliases=["lucky", "luckiness"])
    async def stats_luck(self, ctx: StatsContext):
        person: discord.Member = ctx.data["person"]
        await ctx.send(
            content=f"{person.mention}'s luck:" if person == ctx.author
            else f"{ctx.author.mention}: {person.display_name}'s luck:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently got a *{ctx.data['percent']}%* SSR droprate in their pulls, with *{ctx.data['ssrs']} SSRs* in *{ctx.data['pulls']} Units*"
            )
        )

    @stats.command(name="ssrs", aliases=["ssr"])
    async def stats_ssrs(self, ctx: StatsContext):
        person: discord.Member = ctx.data["person"]
        await ctx.send(
            content=f"{person.mention}'s SSRs:" if person == ctx.author
            else f"{ctx.author.mention}: {person.display_name}'s SSRs:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently has *{ctx.data['ssrs']} SSRs*"
            )
        )

    @stats.command(name="units", aliases=["unit"])
    async def stats_units(self, ctx: StatsContext):
        person: discord.Member = ctx.data["person"]
        await ctx.send(
            content=f"{person.mention}'s Units:" if person == ctx.author
            else f"{ctx.author.mention}: {person.display_name}'s Units:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently has *{ctx.data['pulls']} Units*"
            )
        )

    @stats.command(name="shafts", aliases=["shaft"])
    async def stats_shafts(self, ctx: StatsContext):
        person: discord.Member = ctx.data["person"]
        await ctx.send(
            content=f"{person.mention}'s Shafts:" if person == ctx.author
            else f"{ctx.author.mention}: {person.display_name}'s Shafts:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently got shafted {ctx.data['shafts']}x"
            )
        )


def setup(_bot):
    _bot.add_cog(TopCog(_bot))
