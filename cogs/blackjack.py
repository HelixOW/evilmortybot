import discord
import random as ra
import utilities.reactions as emojis
from discord.ext import commands
from discord.ext.commands import Context
from typing import List, Optional, Tuple, AsyncGenerator, Dict
from sqlite3 import Cursor
from utilities import connection


async def add_blackjack_game(user: discord.Member, won: bool) -> None:
    cursor: Cursor = connection.cursor()
    data: Optional[Tuple[int, int, int, int, int]] = cursor.execute(
        'SELECT won, lost, win_streak, highest_streak, last_result FROM blackjack_record WHERE user=? AND guild=?',
        (user.id, user.guild.id)).fetchone()
    if data is None:
        cursor.execute('INSERT INTO blackjack_record VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (user.id, user.guild.id, 1 if won else 0, 0 if won else 1, 1 if won else 0, 1 if won else 0,
                        1 if won else 0))
    else:
        if won:
            if data[4] == 1:  # last was won
                cursor.execute(
                    'UPDATE blackjack_record SET won=?, win_streak=?, highest_streak=?, last_result=1 WHERE user=? AND guild=?',
                    (data[0] + 1, data[2] + 1, data[2] + 1 if data[2] + 1 > data[3] else data[3], user.id,
                     user.guild.id))
            else:  # last was lost
                cursor.execute(
                    'UPDATE blackjack_record SET won=?, win_streak=1, highest_streak=?, last_result=1 WHERE user=? AND guild=?',
                    (data[0] + 1, data[3] + 1 if data[2] + 1 > data[3] else data[3], user.id, user.guild.id))
        else:
            cursor.execute('UPDATE blackjack_record SET lost=?, win_streak=0, last_result=0 WHERE user=? AND guild=?',
                           (data[1] + 1, user.id, user.guild.id))
    connection.commit()


async def get_blackjack_top(guild: discord.Guild) -> AsyncGenerator[Dict[str, int], None]:
    cursor: Cursor = connection.cursor()
    row: Tuple[int, int, int]
    for row in cursor.execute(
            'SELECT row_number() over (ORDER BY highest_streak), user, highest_streak FROM blackjack_record WHERE guild=? ORDER BY highest_streak DESC LIMIT 10',
            (guild.id,)):
        yield {"place": row[0], "user": row[1], "highest_streak": row[2]}


async def get_blackjack_stats(of: discord.Member) -> Optional[Tuple[int, int, int, int, int]]:
    cursor: Cursor = connection.cursor()
    return cursor.execute(
        'SELECT won, lost, win_streak, last_result, highest_streak FROM blackjack_record WHERE user=? AND guild=?',
        (of.id, of.guild.id)).fetchone()


class BlackJackCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group(aliases=["bj", "jack", "blackj"])
    @commands.guild_only()
    async def blackjack(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            bot_card_values: List[int] = [ra.randint(1, 11) for _ in range(2)]
            player_card_values: List[int] = [ra.randint(1, 11) for _ in range(2)]

            cards_msg: discord.Message = await ctx.send(content=f"""
                        {ctx.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
                        Bot card is: {bot_card_values[0]}""")

            async def play(last_msg: discord.Message = None):
                await last_msg.clear_reactions()
                if sum(player_card_values) > 21:
                    await add_blackjack_game(ctx.author, False)
                    return await last_msg.edit(
                        content=f"{ctx.author.mention} you lost! -> Hand of {sum(player_card_values)}")
                if sum(player_card_values) == 21:
                    await add_blackjack_game(ctx.author, True)
                    if last_msg is None:
                        return await ctx.send(content=f"{ctx.author.mention} you got a Blackjack and won!")
                    return await last_msg.edit(content=f"{ctx.author.mention} you got a Blackjack and won!")

                await last_msg.edit(content=f"""
                    {ctx.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
                    Bot card is: {bot_card_values[0]}""")

                await last_msg.add_reaction(emojis.HIT)
                await last_msg.add_reaction(emojis.STAND)

                def check(added_reaction, user):
                    return user == ctx.author and str(added_reaction.emoji) in [emojis.HIT, emojis.STAND]

                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', check=check)

                    if str(reaction.emoji) == emojis.HIT:
                        player_card_values.append(ra.randint(1, 11))
                        return await play(last_msg=cards_msg)
                    if str(reaction.emoji) == emojis.STAND:
                        await cards_msg.clear_reactions()
                        await add_blackjack_game(ctx.message.author,
                                                 21 - sum(player_card_values) < 21 - sum(bot_card_values))
                        return await last_msg.edit(
                            content=f"{ctx.author.mention} you won! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})" if 21 - sum(
                                player_card_values) < 21 - sum(bot_card_values)
                            else f"{ctx.author.mention} you lost! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})")
                except TimeoutError:
                    pass

            await play(cards_msg)

    @blackjack.command(name="top", aliases=["leaderboard", "lead", "leader", "leading"])
    async def blackjack_top(self, ctx: Context):
        if len([x async for x in get_blackjack_top(ctx.message.guild)]) is None:
            return await ctx.send(content="Nobody played Blackjack yet!")

        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(
                                  title=f"Blackjack Leaderboard in {ctx.guild.name} (Highest Winning Streaks)",
                                  description=",\n".join(["**{}.** *{}* ~ Streak of {} wins".format(
                                      data["place"],
                                      await self.bot.fetch_user(data["user"]),
                                      data["highest_streak"]
                                  ) async for data in get_blackjack_top(ctx.guild)])
                              ).set_thumbnail(url=ctx.guild.icon_url))

    @blackjack.command(name="record", aliases=["stats"])
    async def blackjack_record(self, ctx: Context, person: Optional[discord.Member] = None):
        if person is None:
            person: discord.Member = ctx.author
        data: Optional[Tuple[int, int, int, int, int]] = await get_blackjack_stats(person)

        if data is None:
            return await ctx.send(
                content=f"{ctx.author.mention}: You haven't played Blackjack yet!" if person == ctx.author
                else f"{ctx.author.mention}: {person.display_name} hasn't played Blackjack yet!")

        return await ctx.send(
            content=f"{ctx.author.mention} Blackjack History:" if person == ctx.author else f"{ctx.author.mention}: {person.display_name}'s Blackjack History:",
            embed=discord.Embed(
                title=f"History of {person.display_name}",
                description=f"""
                                  **Wins**: `{data[0]}`

                                  **Lost**: `{data[1]}`

                                  **Win Streak**: `{"No" if data[3] == 0 else data[2]}`

                                  **Highest Winning Streak**: `{data[4]}`
                                  """
            ))


def setup(_bot):
    _bot.add_cog(BlackJackCog(_bot))
