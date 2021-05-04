import asyncio
import typing

import discord
import PIL.Image as Images
from discord.ext import commands
from discord.ext.commands import Context
from typing import Dict, List, Tuple, Optional
from utilities import connection, half_img_size, get_text_dimensions, text_with_shadow, image_to_discord
from utilities.units import Unit, unit_by_id
from utilities import embeds
from PIL import Image, ImageDraw
from sqlite3 import Cursor


def has_profile(discord_id: int):
    cursor: Cursor = connection.cursor()
    return cursor.execute('SELECT * FROM "bot_users" WHERE discord_id=?', (discord_id,)).fetchone() is not None


class BotUser:
    def __init__(self,
                 discord_id: int,
                 name: str,
                 team_cc: float,
                 box_cc: float,
                 friendcode: int,
                 offered_demons: Dict[str, int],
                 demon_teams: Dict[str, List[int]]):
        self.demon_teams: Dict[str, List[Unit]] = {demon: [unit_by_id(x) for x in demon_teams[demon]] for demon in
                                                   demon_teams}
        self.offered_demons: Dict[str, int] = offered_demons
        self.friendcode: int = friendcode
        self.box_cc: float = box_cc
        self.team_cc: float = team_cc
        self.name: str = name
        self.discord_id: int = discord_id
        self.pulled_ssrs: Dict[int, int] = {}
        self.pulled_overall: Dict[int, int] = {}
        self.shafts: Dict[int, int] = {}

        cursor: Cursor = connection.cursor()
        for guild_row in cursor.execute(
                'SELECT ssr_amount, pull_amount, shafts, guild FROM "user_pulls" WHERE user_id=?',
                (discord_id,)):
            self.pulled_ssrs[guild_row[3]] = guild_row[0]
            self.pulled_overall[guild_row[3]] = guild_row[1]
            self.shafts[guild_row[3]] = guild_row[2]

        if not has_profile(discord_id):
            cursor: Cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO "bot_users" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (discord_id, name, team_cc, box_cc, friendcode, offered_demons["red"], offered_demons["gray"],
                 offered_demons["crimson"], ",".join(demon_teams["red"]), ",".join(demon_teams["gray"]),
                 ",".join(demon_teams["crimson"]))
            )
            connection.commit()

    async def create_team_image(self, demon: str):
        if len(self.demon_teams[demon]) == 0:
            image: Image = Images.new('RGBA', get_text_dimensions(f"No team provided for {demon} demon"))
            draw: ImageDraw = ImageDraw.Draw(image)
            text_with_shadow(draw, f"No team provided for {demon} demon", (0, 0))
            return image

        team: List[Unit] = [unit_by_id(x) for x in self.demon_teams[demon]]
        demon_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for {demon} Demon")
        image: Image = Images.new('RGBA', (
            (4 * half_img_size) + (3 * 5),
            half_img_size + 3 + demon_dimension[1]
        ))
        draw: ImageDraw = ImageDraw.Draw(image)

        text_with_shadow(draw, f"{self.name}'s Team for {demon} Demon", (0, 0))

        x: int = 0
        for team_unit in team:
            image.paste(await team_unit.set_icon(), (x, 3 + demon_dimension[1]))
            x += 5

        return image

    async def create_all_team_image(self):
        red_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for red Demon")
        gray_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for gray Demon")
        crimson_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for crimson Demon")
        image: Image = Images.new('RGBA', (
            (4 * half_img_size) + (3 * 5),
            (red_dimension[1] + gray_dimension[1] + crimson_dimension[1]) + (9 * 3) + (half_img_size * 3)
        ))
        draw: ImageDraw = ImageDraw.Draw(image)

        y: int = 0
        for demon in self.demon_teams:
            text_with_shadow(draw, f"{self.name}'s Team for {demon} Demon", (0, y))
            y += crimson_dimension[1] + 3
            x: int = 0
            for team_unit in self.demon_teams[demon]:
                if team_unit is not None:
                    image.paste((await team_unit.set_icon()).resize((half_img_size, half_img_size)), (x, y))
                x += 5 + half_img_size
            y += half_img_size + 6

        return image

    def get_pulled_overall(self, guild: discord.Guild):
        return self.pulled_overall[guild.id]

    def get_pulled_ssrs(self, guild: discord.Guild):
        return self.pulled_ssrs[guild.id]

    def get_shafts(self, guild: discord.Guild):
        return self.shafts[guild.id]

    def get_luck(self, guild: discord.Guild):
        return round((self.get_pulled_ssrs(guild) / self.get_pulled_overall(guild)) * 100, 2)

    async def set_name(self, name: str):
        self.name = name
        cursor: Cursor = connection.cursor()
        cursor.execute(
            'UPDATE "bot_users" SET name=? WHERE discord_id=?',
            (name, self.discord_id)
        )
        connection.commit()

    async def set_demon_team(self, demon: str, team: List[int]):
        self.demon_teams[demon] = team
        cursor: Cursor = connection.cursor()
        if demon == "red":
            cursor.execute(
                'UPDATE "bot_users" SET red_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        elif demon == "gray":
            cursor.execute(
                'UPDATE "bot_users" SET gray_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        elif demon == "crimson":
            cursor.execute(
                'UPDATE "bot_users" SET crimson_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        connection.commit()

    async def set_friendcode(self, friendcode: int):
        self.friendcode = friendcode
        cursor: Cursor = connection.cursor()
        cursor.execute(
            'UPDATE "bot_users" SET friendcode=? WHERE discord_id=?',
            (friendcode, self.discord_id)
        )
        connection.commit()

    async def set_box_cc(self, box_cc: float):
        self.box_cc = box_cc
        cursor: Cursor = connection.cursor()
        cursor.execute(
            'UPDATE "bot_users" SET box_cc=? WHERE discord_id=?',
            (box_cc, self.discord_id)
        )
        connection.commit()

    async def set_team_cc(self, team_cc: float):
        self.team_cc = team_cc
        cursor: Cursor = connection.cursor()
        cursor.execute(
            'UPDATE "bot_users" SET team_cc=? WHERE discord_id=?',
            (team_cc, self.discord_id)
        )
        connection.commit()

    async def create_info(self, guild: discord.Guild, image_url: str):
        return embeds.DrawEmbed(title=f"Info about {self.name if self.name != '' else str(self.discord_id)}").add_field(
            name="Team CC",
            value=f"```{self.team_cc if self.team_cc != -1 else 'Not provided'}```"
        ).add_field(
            name="Box CC",
            value=f"```{self.box_cc if self.box_cc != -1 else 'Not provided'}```"
        ).add_field(
            name="Friendcode",
            value=f"```{self.friendcode if self.friendcode != -1 else 'Not provided'}```"
        ).add_blank_field().add_field(
            name="SSRs pulled",
            value=f"```{self.get_pulled_ssrs(guild)}```"
        ).add_blank_field(True).add_field(
            name="Units pulled",
            value=f"```{self.get_pulled_overall(guild)}```"
        ).add_field(
            name="Shafts",
            value=f"```{self.get_shafts(guild)}```"
        ).add_blank_field(True).add_field(
            name="SSR Percentage",
            value=f"```{self.get_luck(guild)}%```"
        ).add_blank_field().add_field(
            name="Red Demons offered",
            value=f"```{self.offered_demons['red']}```"
        ).add_field(
            name="Gray Demons offered",
            value=f"```{self.offered_demons['gray']}```"
        ).add_field(
            name="Crimson Demons offered",
            value=f"```{self.offered_demons['crimson']}```"
        ).set_thumbnail(url=image_url)


async def read_bot_user(member: discord.Member):
    cursor: Cursor = connection.cursor()
    row = cursor.execute('SELECT * FROM "bot_users" WHERE discord_id=?', (member.id,)).fetchone()

    if row is None:
        return None

    return BotUser(
        discord_id=row[0],
        name=row[1],
        team_cc=row[2],
        box_cc=row[3],
        friendcode=row[4],
        offered_demons={
            "red": row[5],
            "gray": row[6],
            "crimson": row[7]
        },
        demon_teams={
            "red": row[8].split(","),
            "gray": row[9].split(","),
            "crimson": row[10].split(",")
        }
    )


class ProfileCog(commands.Cog):
    def __init__(self, _bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = _bot

    async def ask_for_information(self, ctx: Context, want_to_provide_msg: str, follow_up_message: str,
                                  no_input_error_message: str) -> typing.Any:
        def msg_check(message: discord.Message):
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id

        asking_message: discord.Message = await ctx.send(want_to_provide_msg)

        try:
            provide_val_message: discord.Message = await self.bot.wait_for("message", check=msg_check, timeout=5)
            provide_val: bool = provide_val_message.content.lower() in ["true", "yes", "y", "ye", "yeah",
                                                                        "1", "yup", "ok"]
            await asking_message.delete()
            await provide_val_message.delete()
        except asyncio.TimeoutError:
            await asking_message.delete()
            return None

        if provide_val:
            asking_message: discord.Message = await ctx.send(follow_up_message)

            try:
                val_message: discord.Message = await self.bot.wait_for("message", check=msg_check, timeout=30)
                val = val_message.content
                await asking_message.delete()
                await val_message.delete()
                return val
            except asyncio.TimeoutError:
                await asking_message.delete()
                await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed(no_input_error_message))
                return None

    @commands.group(name="profile")
    async def profile_cmd(self, ctx: Context, of: Optional[discord.Member]):
        if of is None:
            of = ctx.author

        if ctx.invoked_subcommand is None:
            bot_user = await read_bot_user(of)

            if bot_user is None:
                return await ctx.send(ctx.author.mention,
                                      embed=embeds.ErrorEmbed(f"{of.display_name} didn't create a profile yet",
                                                              description=f"Use `..profile create` to create one"))

            await ctx.send(ctx.author.mention,
                           embed=await bot_user.create_info(ctx.guild, ctx.author.avatar_url),
                           file=await image_to_discord(await bot_user.create_all_team_image()))

    @profile_cmd.command(name="create", aliases=["+", "add"])
    async def profile_create_cmd(self, ctx: Context,
                                 name: str = None, team_cc: int = None, box_cc: int = None, friendcode: int = None,
                                 red_team: str = None, gray_team: str = None, crimson_team: str = None):

        if name is None:
            name = await self.ask_for_information(ctx,
                                                  f"{ctx.author.mention}: Do you want to provide your Grand Cross account name?",
                                                  f"{ctx.author.mention}: What's your Grand Cross account name?",
                                                  "No name provided!")

        if friendcode is None:
            msg_val = await self.ask_for_information(ctx,
                                                     f"{ctx.author.mention}: Do you want to provide your Grand Cross Friendcode?",
                                                     f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                                                     "No Friendcode provided!")

            if msg_val is None:
                friendcode = -1
            else:
                try:
                    friendcode = int(msg_val)
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Provided Friendcode is not a number!"))

        if team_cc is None:
            msg_val = await self.ask_for_information(ctx,
                                                     f"{ctx.author.mention}: Do you want to provide your Grand Cross Team CC?",
                                                     f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                                                     "No Team CC provided!")

            if msg_val is None:
                team_cc = -1
            else:
                try:
                    team_cc = int(msg_val)
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Provided Team CC is not a number!"))

        if box_cc is None:
            msg_val = await self.ask_for_information(ctx,
                                                     f"{ctx.author.mention}: Do you want to provide your Grand Cross Box CC?",
                                                     f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                                                     "No Box CC provided!")

            if msg_val is None:
                box_cc = -1
            else:
                try:
                    box_cc = int(msg_val)
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Provided Box CC is not a number!"))

        if red_team is None:
            red_team: str = await self.ask_for_information(ctx,
                                                           f"{ctx.author.mention}: Do you want to provide your team for red demons?",
                                                           f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `1,178,15,76`)*",
                                                           "No Team for red demons provided!")

            if red_team is not None:
                try:
                    red_team: List[int] = [int(x) for x in red_team.split(",")]
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Can't find any team like this!"))
            else:
                red_team = []

        if gray_team is None:
            gray_team: str = await self.ask_for_information(ctx,
                                                            f"{ctx.author.mention}: Do you want to provide your team for gray demons?",
                                                            f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `1,178,15,76`)*",
                                                            "No Team for gray demons provided!")

            if gray_team is not None:
                try:
                    gray_team: List[int] = [int(x) for x in gray_team.split(",")]
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Can't find any team like this!"))
            else:
                gray_team = []

        if crimson_team is None:
            crimson_team: str = await self.ask_for_information(ctx,
                                                               f"{ctx.author.mention}: Do you want to provide your team for crimson demons?",
                                                               f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `1,178,15,76`)*",
                                                               "No Team for crimson demons provided!")

            if crimson_team is not None:
                try:
                    crimson_team: List[int] = [int(x) for x in crimson_team.split(",")]
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Can't find any team like this!"))
            else:
                crimson_team = []

        BotUser(
            discord_id=ctx.author.id,
            name="Not provided" if name is None else name,
            team_cc=team_cc,
            box_cc=box_cc,
            friendcode=friendcode,
            demon_teams={
                "red": red_team,
                "gray": gray_team,
                "crimson": crimson_team
            },
            offered_demons={"red": 0, "gray": 0, "crimson": 0}
        )

        return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Added your profile!"))

    @profile_cmd.command(name="edit", aliases=["update"])
    async def profile_edit_cmd(self, ctx: Context,
                               name: str = None, team_cc: int = None, box_cc: int = None, friendcode: int = None,
                               red_team: str = None, gray_team: str = None, crimson_team: str = None):

        if name is None:
            name = await self.ask_for_information(ctx,
                                                  f"{ctx.author.mention}: Do you want to update your Grand Cross account name?",
                                                  f"{ctx.author.mention}: What's your Grand Cross account name?",
                                                  "No name provided!")

        if friendcode is None:
            msg_val = await self.ask_for_information(ctx,
                                                     f"{ctx.author.mention}: Do you want to update your Grand Cross Friendcode?",
                                                     f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                                                     "No Friendcode provided!")

            if msg_val is None:
                friendcode = -1
            else:
                try:
                    friendcode = int(msg_val)
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Provided Friendcode is not a number!"))

        if team_cc is None:
            msg_val = await self.ask_for_information(ctx,
                                                     f"{ctx.author.mention}: Do you want to update your Grand Cross Team CC?",
                                                     f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                                                     "No Team CC provided!")

            if msg_val is None:
                team_cc = -1
            else:
                try:
                    team_cc = int(msg_val)
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Provided Team CC is not a number!"))

        if box_cc is None:
            msg_val = await self.ask_for_information(ctx,
                                                     f"{ctx.author.mention}: Do you want to update your Grand Cross Box CC?",
                                                     f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                                                     "No Box CC provided!")

            if msg_val is None:
                box_cc = -1
            else:
                try:
                    box_cc = int(msg_val)
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Provided Box CC is not a number!"))

        if red_team is None:
            red_team: str = await self.ask_for_information(ctx,
                                                           f"{ctx.author.mention}: Do you want to update your team for red demons?",
                                                           f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `1,178,15,76`)*",
                                                           "No Team for red demons provided!")

            if red_team is not None:
                try:
                    red_team: List[int] = [int(x) for x in red_team.split(",")]
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Can't find any team like this!"))
            else:
                red_team = []

        if gray_team is None:
            gray_team: str = await self.ask_for_information(ctx,
                                                            f"{ctx.author.mention}: Do you want to update your team for gray demons?",
                                                            f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `1,178,15,76`)*",
                                                            "No Team for gray demons provided!")

            if gray_team is not None:
                try:
                    gray_team: List[int] = [int(x) for x in gray_team.split(",")]
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Can't find any team like this!"))
            else:
                gray_team = []

        if crimson_team is None:
            crimson_team: str = await self.ask_for_information(ctx,
                                                               f"{ctx.author.mention}: Do you want to update your team for crimson demons?",
                                                               f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `1,178,15,76`)*",
                                                               "No Team for crimson demons provided!")

            if crimson_team is not None:
                try:
                    crimson_team: List[int] = [int(x) for x in crimson_team.split(",")]
                except ValueError:
                    return await ctx.send(ctx.author.mention,
                                          embed=embeds.ErrorEmbed("Can't find any team like this!"))
            else:
                crimson_team = []

        bot_user: BotUser = await read_bot_user(ctx.author)

        if name is not None:
            await bot_user.set_name(name)

        if friendcode != -1:
            await bot_user.set_friendcode(friendcode)

        if team_cc != -1:
            await bot_user.set_team_cc(team_cc)

        if box_cc != -1:
            await bot_user.set_box_cc(box_cc)

        if len(red_team) != 0:
            await bot_user.set_demon_team("red", red_team)

        if len(gray_team) != 0:
            await bot_user.set_demon_team("gray", gray_team)

        if len(crimson_team) != 0:
            await bot_user.set_demon_team("crimson", crimson_team)

        return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Updated your profile!"))


def setup(_bot):
    _bot.add_cog(ProfileCog(_bot))
