import discord
import PIL.Image as Images
from discord.ext import commands
from discord.ext.commands import Context
from typing import Dict, List, Tuple, Optional
from utilities import half_img_size, get_text_dimensions, text_with_shadow, image_to_discord
from utilities.units import Unit, unit_by_id, unit_by_vague_name
from utilities import embeds, dialogue
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
                 demon_teams: Dict[str, Tuple[str, ...]]):

        self.demon_teams: Dict[str, Tuple[Optional[Unit]], ...] = {
            demon: tuple(unit_by_id(int(x)) for x in demon_teams[demon] if x is not None) for demon in
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
        if guild.id not in self.pulled_overall:
            return 0
        return self.pulled_overall[guild.id]

    def get_pulled_ssrs(self, guild: discord.Guild):
        if guild.id not in self.pulled_ssrs:
            return 0
        return self.pulled_ssrs[guild.id]

    def get_shafts(self, guild: discord.Guild):
        if guild.id not in self.shafts:
            return 0
        return self.shafts[guild.id]

    def get_luck(self, guild: discord.Guild):
        if self.get_pulled_overall(guild) == 0:
            return 0
        return round((self.get_pulled_ssrs(guild) / self.get_pulled_overall(guild)) * 100, 2)

    async def set_name(self, name: str):
        self.name = name
        await execute(
            'UPDATE "bot_users" SET name=? WHERE discord_id=?',
            (name, self.discord_id)
        )

    async def set_demon_team(self, demon: str, team: Tuple[str, ...]):
        self.demon_teams[demon] = tuple(unit_by_id(int(x)) for x in team)
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
            value=f"```{float(self.team_cc / 1000) if self.team_cc != -1 else '0'}k```"
        ).add_field(
            name="Box CC",
            value=f"```{float(self.box_cc / 1000000) if self.box_cc != -1 else '0'}M```"
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
    if not await exists('SELECT * FROM "bot_users" WHERE discord_id=?', (member.id,)):
        return None

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
                                          "red": () if len(x[8]) == 0 else x[8].split(","),
                                          "gray": () if len(x[9]) == 0 else x[9].split(","),
                                          "crimson": () if len(x[10]) == 0 else x[10].split(",")
                                      }
                                  ),
                                  (member.id,))).init_db()


def convert(team) -> Tuple[str, ...]:
    return tuple(str(unit_by_vague_name(x)[0].unit_id) for x in team.split(",") if len(unit_by_vague_name(x)) > 0)


def convert_team_cc(cc: str):
    if "." in cc or "," in cc:
        cc = float(cc) * 1000
    try:
        return int(cc)
    except ValueError:
        raise ValueError


def convert_box_cc(cc: str):
    if "." in cc or "," in cc:
        cc = float(cc) * 1000000
    try:
        return int(cc)
    except ValueError:
        raise ValueError


class ProfileCog(commands.Cog):
    def __init__(self, _bot: discord.ext.commands.Bot):
        self.bot: discord.ext.commands.Bot = _bot

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
                           embed=await bot_user.create_info(ctx.guild, of.avatar_url),
                           file=await image_to_discord(await bot_user.create_all_team_image()))

    @profile_cmd.command(name="create", aliases=["+", "add"])
    async def profile_create_cmd(self, ctx: Context,
                                 name: str = None, team_cc: int = None, box_cc: int = None, friendcode: int = None,
                                 red_team: str = None, gray_team: str = None, crimson_team: str = None):

        rupted = False

        if name is None:
            try:
                name = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your Grand Cross account name?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross account name?",
                    no_input="No name provided!",
                    convert=str
                )
            except InterruptedError:
                rupted = True

        if friendcode is None and not rupted:
            try:
                friendcode = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your Grand Cross Friendcode?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                    no_input="No Friendcode provided!",
                    convert=int,
                    default_val=-1,
                    convert_failed="Provided Friendcode is not a number!")
            except InterruptedError:
                rupted = True

        if team_cc is None and not rupted:
            try:
                team_cc = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your Grand Cross Team CC?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                    no_input="No Team CC provided!",
                    convert=convert_team_cc,
                    default_val=-1,
                    convert_failed="Provided Team CC is not a number!")
            except InterruptedError:
                rupted = True

        if box_cc is None and not rupted:
            try:
                box_cc = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your Grand Cross Box CC?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                    no_input="No Box CC provided!",
                    convert=convert_box_cc,
                    default_val=-1,
                    convert_failed="Provided Box CC is not a number!")
            except InterruptedError:
                rupted = True

        if red_team is None and not rupted:
            try:
                red_team: Tuple[str, ...] = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your team for red demons?",
                    followed_question=f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `t1,beastin,bslater,bsrjericho`)*",
                    no_input="No Team for red demons provided!",
                    convert=convert,
                    default_val=tuple(),
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60)
            except InterruptedError:
                rupted = True

        if gray_team is None and not rupted:
            try:
                gray_team: Tuple[str, ...] = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your team for gray demons?",
                    followed_question=f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `danaforliz,lolimerlin,ggowther,deathpierce`)*",
                    no_input="No Team for gray demons provided!",
                    convert=convert,
                    default_val=tuple(),
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60)
            except InterruptedError:
                rupted = True

        if crimson_team is None and not rupted:
            try:
                crimson_team: Tuple[str, ...] = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to provide your team for crimson demons?",
                    followed_question=f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `rderi,rzel,rgowther,rsrjericho`)*",
                    no_input="No Team for crimson demons provided!",
                    convert=convert,
                    default_val=tuple(),
                    convert_failed="Can't find any team like this!")
            except InterruptedError:
                pass

        await BotUser(
            discord_id=ctx.author.id,
            name="Not provided" if name is None else name,
            team_cc=-1 if team_cc is None else team_cc,
            box_cc=-1 if box_cc is None else box_cc,
            friendcode=-1 if friendcode is None else friendcode,
            demon_teams={
                "red": red_team if red_team is not None else (),
                "gray": gray_team if gray_team is not None else (),
                "crimson": crimson_team if crimson_team is not None else ()
            },
            offered_demons={"red": 0, "gray": 0, "crimson": 0}
        ).init_db()

        return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Added your profile!"))

    @profile_cmd.command(name="edit", aliases=["update"])
    async def profile_edit_cmd(self, ctx: Context,
                               name: str = None, team_cc: int = None, box_cc: int = None, friendcode: int = None,
                               red_team: str = None, gray_team: str = None, crimson_team: str = None):

        bot_user: BotUser = await read_bot_user(ctx.author)

        if bot_user is None:
            return await ctx.send(ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"You didn't create a profile yet",
                                                          description=f"Use `..profile create` to create one"))

        rupted = False

        if name is None:
            try:
                name = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross account name?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross account name?",
                    no_input="No name provided!",
                    convert=str)
            except InterruptedError:
                rupted = True

        if friendcode is None and not rupted:
            try:
                friendcode = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross Friendcode?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                    no_input="No Friendcode provided!",
                    convert=int,
                    convert_failed="Provided Friendcode is not a number!")
            except InterruptedError:
                rupted = True

        if team_cc is None and not rupted:
            try:
                team_cc = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross Team CC?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                    no_input="No Team CC provided!",
                    convert=convert_team_cc,
                    convert_failed="Provided Team CC is not a number!")
            except InterruptedError:
                rupted = True

        if box_cc is None and not rupted:
            try:
                box_cc = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross Box CC?",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                    no_input="No Box CC provided!",
                    convert=convert_box_cc,
                    convert_failed="Provided Box CC is not a number!")
            except InterruptedError:
                rupted = True

        if red_team is None and not rupted:
            try:
                red_team: Tuple[str, ...] = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for red demons?",
                    followed_question=f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `t1,beastin,bslater,bsrjericho`)*",
                    no_input="No Team for red demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!")
            except InterruptedError:
                rupted = True

        if gray_team is None and not rupted:
            try:
                gray_team: Tuple[str, ...] = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for gray demons?",
                    followed_question=f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `danaforliz,lolimerlin,ggowther,deathpierce`)*",
                    no_input="No Team for gray demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!")
            except InterruptedError:
                rupted = True

        if crimson_team is None and not rupted:
            try:
                crimson_team: Tuple[str, ...] = await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for crimson demons?",
                    followed_question=f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `rderi,rzel,rgowther,rsrjericho`)*",
                    no_input="No Team for crimson demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!")
            except InterruptedError:
                pass

        if name is not None:
            await bot_user.set_name(name)

        if friendcode is not None:
            await bot_user.set_friendcode(friendcode)

        if team_cc is not None:
            await bot_user.set_team_cc(team_cc)

        if box_cc is not None:
            await bot_user.set_box_cc(box_cc)

        if red_team is not None:
            await bot_user.set_demon_team("red", red_team)

        if gray_team is not None:
            await bot_user.set_demon_team("gray", gray_team)

        if crimson_team is not None:
            await bot_user.set_demon_team("crimson", crimson_team)

        return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Updated your profile!"))


def setup(_bot):
    _bot.add_cog(ProfileCog(_bot))
