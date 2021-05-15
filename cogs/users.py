import asyncio
import typing

import discord
import PIL.Image as Images
from discord.ext import commands
from discord.ext.commands import Context
from typing import Dict, List, Tuple, Optional
from utilities import half_img_size, get_text_dimensions, text_with_shadow, image_to_discord
from utilities.units import Unit, unit_by_id, unit_by_vague_name
from utilities import embeds
from utilities.sql_helper import fetch_rows, exists, execute, fetch_row
from PIL import Image, ImageDraw


async def has_profile(discord_id: int):
    return await exists('SELECT * FROM "bot_users" WHERE discord_id=?', (discord_id,))


class BotUser:
    def __init__(self,
                 discord_id: int,
                 name: str,
                 team_cc: float,
                 box_cc: float,
                 friendcode: int,
                 offered_demons: Dict[str, int],
                 demon_teams: Dict[str, List[str]]):
        self.demon_teams: Dict[str, List[Unit]] = {
            demon: [unit_by_id(int(x)) for x in demon_teams[demon] if len(x) != 0] for demon in
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

    async def init_db(self):
        for data in await fetch_rows(
                'SELECT ssr_amount, pull_amount, shafts, guild FROM "user_pulls" WHERE user_id=?',
                lambda x: {
                    "ssrs": x[0],
                    "overall": x[1],
                    "shafts": x[2],
                    "guild": x[3]
                },
                (self.discord_id,)):
            self.pulled_ssrs[data["guild"]] = data["ssrs"]
            self.pulled_overall[data["guild"]] = data["overall"]
            self.shafts[data["guild"]] = data["shafts"]

        if not await has_profile(self.discord_id):
            await execute(
                'INSERT INTO "bot_users" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (self.discord_id, self.name, self.team_cc, self.box_cc, self.friendcode,
                 self.offered_demons["red"], self.offered_demons["gray"], self.offered_demons["crimson"],
                 ",".join([str(x) for x in self.demon_teams["red"]]),
                 ",".join([str(x) for x in self.demon_teams["gray"]]),
                 ",".join([str(x) for x in self.demon_teams["crimson"]]))
            )

        return self

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
        await execute(
            'UPDATE "bot_users" SET name=? WHERE discord_id=?',
            (name, self.discord_id)
        )

    async def set_demon_team(self, demon: str, team: List[str]):
        self.demon_teams[demon] = [unit_by_id(int(x)) for x in team]
        if demon == "red":
            await execute(
                'UPDATE "bot_users" SET red_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        elif demon == "gray":
            await execute(
                'UPDATE "bot_users" SET gray_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        elif demon == "crimson":
            await execute(
                'UPDATE "bot_users" SET crimson_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )

    async def set_friendcode(self, friendcode: int):
        self.friendcode = friendcode
        await execute(
            'UPDATE "bot_users" SET friendcode=? WHERE discord_id=?',
            (friendcode, self.discord_id)
        )

    async def set_box_cc(self, box_cc: float):
        self.box_cc = box_cc
        await execute(
            'UPDATE "bot_users" SET box_cc=? WHERE discord_id=?',
            (box_cc, self.discord_id)
        )

    async def set_team_cc(self, team_cc: float):
        self.team_cc = team_cc
        await execute(
            'UPDATE "bot_users" SET team_cc=? WHERE discord_id=?',
            (team_cc, self.discord_id)
        )

    async def add_red_offer(self, amount: int = 1):
        self.offered_demons["red"] = self.offered_demons["red"] + amount
        await execute(
            'UPDATE "bot_users" SET red_offered=? WHERE discord_id=?',
            (self.offered_demons["red"], self.discord_id)
        )

    async def add_gray_offer(self, amount: int = 1):
        self.offered_demons["gray"] = self.offered_demons["gray"] + amount
        await execute(
            'UPDATE "bot_users" SET gray_offered=? WHERE discord_id=?',
            (self.offered_demons["gray"], self.discord_id)
        )

    async def add_crimson_offer(self, amount: int = 1):
        self.offered_demons["crimson"] = self.offered_demons["crimson"] + amount
        await execute(
            'UPDATE "bot_users" SET crimson_offered=? WHERE discord_id=?',
            (self.offered_demons["crimson"], self.discord_id)
        )

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
    return await (await fetch_row('SELECT * FROM "bot_users" WHERE discord_id=?',
                                  lambda x: BotUser(
                                      discord_id=x[0],
                                      name=x[1],
                                      team_cc=x[2],
                                      box_cc=x[3],
                                      friendcode=x[4],
                                      offered_demons={
                                          "red": x[5],
                                          "gray": x[6],
                                          "crimson": x[7]
                                      },
                                      demon_teams={
                                          "red": x[8].split(","),
                                          "gray": x[9].split(","),
                                          "crimson": x[10].split(",")
                                      }
                                  ),
                                  (member.id,))).init_db()


def convert(team):
    return [str(unit_by_vague_name(x)[0].unit_id) for x in team.split(",") if len(unit_by_vague_name(x)) > 0]


class ProfileCog(commands.Cog):
    def __init__(self, _bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = _bot

    async def re_ask_info(self, ctx: Context, message: str, no_input_error_message: str) -> typing.Any:

        def msg_check(msg: discord.Message):
            return msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id

        asking_message: discord.Message = await ctx.send(message)

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
            return await self.re_ask_info(ctx, follow_up_message, no_input_error_message)

    async def ask(self, ctx, question, follow, no_input, _convert, default_val, convert_failed):
        if question is not None:
            provided = await self.ask_for_information(ctx, question, follow, no_input)
        else:
            provided = await self.re_ask_info(ctx, follow, no_input)

        if provided is None:
            return default_val
        else:
            try:
                return _convert(provided)
            except ValueError:
                await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed(convert_failed))
                return await self.ask(ctx, None, follow, no_input, _convert, default_val, convert_failed)

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
            friendcode = await self.ask(ctx,
                                        f"{ctx.author.mention}: Do you want to provide your Grand Cross Friendcode?",
                                        f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                                        "No Friendcode provided!",
                                        int,
                                        -1,
                                        "Provided Friendcode is not a number!")

        if team_cc is None:
            team_cc = await self.ask(ctx,
                                     f"{ctx.author.mention}: Do you want to provide your Grand Cross Team CC?",
                                     f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                                     "No Team CC provided!",
                                     int,
                                     -1,
                                     "Provided Team CC is not a number!")

        if box_cc is None:
            box_cc = await self.ask(ctx,
                                    f"{ctx.author.mention}: Do you want to provide your Grand Cross Box CC?",
                                    f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                                    "No Box CC provided!",
                                    int,
                                    -1,
                                    "Provided Box CC is not a number!")

        if red_team is None:
            red_team: List[str] = await self.ask(ctx,
                                                 f"{ctx.author.mention}: Do you want to provide your team for red demons?",
                                                 f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `t1,beastin,bslater,bsrjericho`)*",
                                                 "No Team for red demons provided!",
                                                 convert,
                                                 [],
                                                 "Can't find any team like this!")

        if gray_team is None:
            gray_team: List[str] = await self.ask(ctx,
                                                  f"{ctx.author.mention}: Do you want to provide your team for gray demons?",
                                                  f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `danaforliz,lolimerlin,ggowther,deathpierce`)*",
                                                  "No Team for gray demons provided!",
                                                  convert,
                                                  [],
                                                  "Can't find any team like this!")

        if crimson_team is None:
            crimson_team: List[str] = await self.ask(ctx,
                                                     f"{ctx.author.mention}: Do you want to provide your team for crimson demons?",
                                                     f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `rderi,rzel,rgowther,rsrjericho`)*",
                                                     "No Team for crimson demons provided!",
                                                     convert,
                                                     [],
                                                     "Can't find any team like this!")

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
            friendcode = await self.ask(ctx,
                                        f"{ctx.author.mention}: Do you want to update your Grand Cross Friendcode?",
                                        f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                                        "No Friendcode provided!",
                                        int,
                                        -1,
                                        "Provided Friendcode is not a number!")

        if team_cc is None:
            team_cc = await self.ask(ctx,
                                     f"{ctx.author.mention}: Do you want to update your Grand Cross Team CC?",
                                     f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                                     "No Team CC provided!",
                                     int,
                                     -1,
                                     "Provided Team CC is not a number!")

        if box_cc is None:
            box_cc = await self.ask(ctx,
                                    f"{ctx.author.mention}: Do you want to update your Grand Cross Box CC?",
                                    f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                                    "No Box CC provided!",
                                    int,
                                    -1,
                                    "Provided Box CC is not a number!")

        if red_team is None:
            red_team: List[str] = await self.ask(ctx,
                                                 f"{ctx.author.mention}: Do you want to update your team for red demons?",
                                                 f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `t1,beastin,bslater,bsrjericho`)*",
                                                 "No Team for red demons provided!",
                                                 convert,
                                                 [],
                                                 "Can't find any team like this!")

        if gray_team is None:
            gray_team: List[str] = await self.ask(ctx,
                                                  f"{ctx.author.mention}: Do you want to update your team for gray demons?",
                                                  f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `danaforliz,lolimerlin,ggowther,deathpierce`)*",
                                                  "No Team for gray demons provided!",
                                                  convert,
                                                  [],
                                                  "Can't find any team like this!")

        if crimson_team is None:
            crimson_team: List[str] = await self.ask(ctx,
                                                     f"{ctx.author.mention}: Do you want to update your team for crimson demons?",
                                                     f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `rderi,rzel,rgowther,rsrjericho`)*",
                                                     "No Team for crimson demons provided!",
                                                     convert,
                                                     [],
                                                     "Can't find any team like this!")

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
