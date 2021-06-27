import discord
import PIL.Image as Images
from discord.ext import commands
from discord.ext.commands import Context
from typing import Dict, List, Tuple, Optional, Any
from utilities import half_img_size, img_size, link_img_size, half_link_img_size, get_text_dimensions, text_with_shadow, \
    image_to_discord, SkipError
from utilities.units import Unit, unit_by_id, unit_by_vague_name
from utilities import embeds, dialogue, ask
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
                 demon_teams: Dict[str, Tuple[str, ...]],
                 pvp_teams: Dict[str, Tuple[str, ...]]):

        self.demon_teams: Dict[str, Tuple[Optional[Unit]], ...] = {
            demon: tuple(unit_by_id(int(x)) for x in demon_teams[demon] if x) for demon in
            demon_teams}
        self.pvp_teams: Dict[str, Tuple[Optional[Unit]], ...] = {
            mode: tuple(unit_by_id(int(x)) for x in pvp_teams[mode] if x) for mode in pvp_teams
        }
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
                'INSERT INTO "bot_users" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (self.discord_id, self.name, self.team_cc, self.box_cc, self.friendcode,
                 self.offered_demons["red"], self.offered_demons["gray"], self.offered_demons["crimson"],
                 ",".join([str(x) for x in self.demon_teams["red"]]),
                 ",".join([str(x) for x in self.demon_teams["gray"]]),
                 ",".join([str(x) for x in self.demon_teams["crimson"]]),
                 ",".join([str(x) for x in self.demon_teams["bellmoth"]]),
                 self.offered_demons["bellmoth"],
                 ",".join([str(x) for x in self.pvp_teams["ungeared"]]),
                 ",".join([str(x) for x in self.pvp_teams["geared"]]))
            )

        return self

    async def create_team_image(self, demon: str):
        if len(self.demon_teams[demon]) == 0:
            image: Image = Images.new('RGBA', get_text_dimensions(f"No team provided for {demon} demon"))
            draw: ImageDraw = ImageDraw.Draw(image)
            text_with_shadow(draw, f"No team provided for {demon} demon", (0, 0))
            return image

        team: List[Unit] = [self.demon_teams[demon][x] for x in range(4) if len(self.demon_teams[demon]) > x]
        links: List[Unit] = [self.demon_teams[demon][x] for x in range(4, 8) if len(self.demon_teams[demon]) > x]
        i: Image = Images.new('RGBA', (
            (img_size * 4) + (5 * 3),
            img_size
        ))

        x: int = 0
        for index, main_unit in enumerate(team):
            if main_unit:
                i.paste(await main_unit.set_icon(), (x, 0))
            if index < len(links):
                i.paste((await links[index].set_icon()).resize((link_img_size, link_img_size)),
                        (x + img_size - link_img_size, img_size - link_img_size))
            x += 5 + img_size

        return i

    async def create_pvp_image(self, mode: str):
        if len(self.pvp_teams[mode]) == 0:
            image: Image = Images.new('RGBA', get_text_dimensions(f"No team provided for {mode} PvP"))
            draw: ImageDraw = ImageDraw.Draw(image)
            text_with_shadow(draw, f"No team provided for {mode} PvP", (0, 0))
            return image

        team: List[Unit] = [self.pvp_teams[mode][x] for x in range(4) if len(self.pvp_teams[mode]) > x]
        links: List[Unit] = [self.pvp_teams[mode][x] for x in range(4, 8) if len(self.pvp_teams[mode]) > x]
        i: Image = Images.new('RGBA', (
            (img_size * 4) + (5 * 3),
            img_size
        ))

        x: int = 0
        for index, main_unit in enumerate(team):
            if main_unit:
                i.paste(await main_unit.set_icon(), (x, 0))
            if index < len(links):
                i.paste((await links[index].set_icon()).resize((link_img_size, link_img_size)),
                        (x + img_size - link_img_size, img_size - link_img_size))
            x += 5 + img_size

        return i

    async def create_all_team_image(self):
        red_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for red Demon")
        gray_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for gray Demon")
        crimson_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for crimson Demon")
        bellmoth_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for bellmoth Demon")
        ungeared_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for ungeared PvP")
        geared_dimension: Tuple[int, int] = get_text_dimensions(f"{self.name}'s Team for geared PvP")
        x: int = (4 * half_img_size) + (3 * 5)
        image: Image = Images.new('RGBA', (
            x if x > bellmoth_dimension[0] else bellmoth_dimension[0],
            (red_dimension[1] + gray_dimension[1] + crimson_dimension[1] + bellmoth_dimension[1] + ungeared_dimension[
                1] + geared_dimension[1]) + (9 * 5) + (half_img_size * 6)
        ))
        draw: ImageDraw = ImageDraw.Draw(image)

        y: int = 0
        for demon in self.demon_teams:
            text_with_shadow(draw, f"{self.name}'s Team for {demon} Demon", (0, y))
            y += crimson_dimension[1] + 3
            x: int = 0

            team: List[Unit] = [self.demon_teams[demon][z] for z in range(4) if len(self.demon_teams[demon]) > z]
            links: List[Unit] = [self.demon_teams[demon][z] for z in range(4, 8) if len(self.demon_teams[demon]) > z]

            for i, team_unit in enumerate(team):
                if team_unit:
                    image.paste((await team_unit.set_icon()).resize((half_img_size, half_img_size)), (x, y))
                if i < len(links):
                    image.paste((await links[i].set_icon()).resize((half_link_img_size, half_link_img_size)),
                                (x + half_img_size - half_link_img_size, y + half_img_size - half_link_img_size))
                x += 5 + half_img_size
            y += half_img_size + 6

        for pvp in self.pvp_teams:
            text_with_shadow(draw, f"{self.name}'s Team for {pvp} PvP", (0, y))
            y += ungeared_dimension[1] + 3
            x: int = 0

            team: List[Unit] = [self.pvp_teams[pvp][z] for z in range(4) if len(self.pvp_teams[pvp]) > z]
            links: List[Unit] = [self.pvp_teams[pvp][z] for z in range(4, 8) if len(self.pvp_teams[pvp]) > z]

            for i, team_unit in enumerate(team):
                if team_unit:
                    image.paste((await team_unit.set_icon()).resize((half_img_size, half_img_size)), (x, y))
                if i < len(links):
                    image.paste((await links[i].set_icon()).resize((half_link_img_size, half_link_img_size)),
                                (x + half_img_size - half_link_img_size, y + half_img_size - half_link_img_size))
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

    async def set_pvp_team(self, mode: str, team: Tuple[int, ...]):
        self.pvp_teams[mode] = tuple(unit_by_id(x) for x in team)
        if mode == "ungeared":
            await execute(
                'UPDATE "bot_users" SET ungeared_team=? WHERE discord_id=?',
                (",".join((str(x) for x in team)), self.discord_id)
            )
        elif mode == "geared":
            await execute(
                'UPDATE "bot_users" SET geared_team=? WHERE discord_id=?',
                (",".join((str(x) for x in team)), self.discord_id)
            )

    async def set_demon_team(self, demon: str, team: Tuple[int, ...]):
        self.demon_teams[demon] = tuple(unit_by_id(x) for x in team)
        if demon == "red":
            await execute(
                'UPDATE "bot_users" SET red_team=? WHERE discord_id=?',
                (",".join((str(x) for x in team)), self.discord_id)
            )
        elif demon == "gray":
            await execute(
                'UPDATE "bot_users" SET gray_team=? WHERE discord_id=?',
                (",".join((str(x) for x in team)), self.discord_id)
            )
        elif demon == "crimson":
            await execute(
                'UPDATE "bot_users" SET crimson_team=? WHERE discord_id=?',
                (",".join((str(x) for x in team)), self.discord_id)
            )
        elif demon == "bellmoth":
            await execute(
                'UPDATE "bot_users" SET bellmoth_team=? WHERE discord_id=?',
                (",".join((str(x) for x in team)), self.discord_id)
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

    async def add_bellmoth_offer(self, amount: int = 1):
        self.offered_demons["bellmoth"] = self.offered_demons["bellmoth"] + amount
        await execute(
            'UPDATE "bot_users" SET bellmoth_offered=? WHERE discord_id=?',
            (self.offered_demons["bellmoth"], self.discord_id)
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
            name="SSR percentage",
            value=f"```{self.get_luck(guild)}%```"
        ).add_blank_field().add_field(
            name="Red demons offered",
            value=f"```{self.offered_demons['red']}```"
        ).add_blank_field(True).add_field(
            name="Gray demons offered",
            value=f"```{self.offered_demons['gray']}```"
        ).add_field(
            name="Crimson demons offered",
            value=f"```{self.offered_demons['crimson']}```"
        ).add_blank_field(True).add_field(
            name="Bellmoth demons offered",
            value=f"```{self.offered_demons['bellmoth']}```"
        ).set_thumbnail(url=image_url)

    async def create_team_info(self, demon: str, image_url: str):
        return embeds.DrawEmbed(
            title=f"{self.name if self.name != '' else str(self.discord_id)}'s team for {demon} demon").set_thumbnail(
            url=image_url)

    async def create_pvp_team_info(self, mode: str, image_url: str):
        return embeds.DrawEmbed(
            title=f"{self.name if self.name != '' else str(self.discord_id)}'s team for {mode} PvP").set_thumbnail(
            url=image_url)


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
                                          "crimson": x[7],
                                          "bellmoth": x[12]
                                      },
                                      demon_teams={
                                          "red": () if len(x[8]) == 0 else x[8].split(","),
                                          "gray": () if len(x[9]) == 0 else x[9].split(","),
                                          "crimson": () if len(x[10]) == 0 else x[10].split(","),
                                          "bellmoth": () if len(x[11]) == 0 else x[11].split(",")
                                      },
                                      pvp_teams={
                                          "ungeared": () if len(x[13]) == 0 else x[13].split(","),
                                          "geared": () if len(x[14]) == 0 else x[14].split(",")
                                      }
                                  ),
                                  (member.id,))).init_db()


def convert(team) -> Tuple[int, ...]:
    return tuple(unit_by_vague_name(x)[0].unit_id for x in team.split(",") if len(unit_by_vague_name(x)) > 0)


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

    @profile_cmd.command(name="code", aliases=["friendcode", "friend"])
    async def profile_code_cmd(self, ctx: Context, of: Optional[discord.Member]):
        if not of:
            of = ctx.author

        bot_user = await read_bot_user(of)

        if not bot_user:
            return await ctx.send(ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"{of.display_name} didn't create a profile yet",
                                                          description=f"Use `..profile create` to create one"))

        await ctx.send(str(bot_user.friendcode))

    @profile_cmd.command(name="pvp")
    async def profile_pvp_cmd(self, ctx: Context, of: Optional[discord.Member], mode: str = None):
        if not of:
            of = ctx.author

        if not mode:
            mode = await ask(ctx,
                             question="Which PvP team do you want to see? __Ungeared__ or __Geared__",
                             convert=str,
                             default_val="ungeared")

        bot_user = await read_bot_user(of)

        if not bot_user:
            return await ctx.send(ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"{of.display_name} didn't create a profile yet",
                                                          description=f"Use `..profile create` to create one"))

        mode = mode.lower().strip()

        if mode in ["ungeared", "normal"]:
            mode = "ungeared"
        else:
            mode = "geared"

        await ctx.send(ctx.author.mention,
                       embed=await bot_user.create_pvp_team_info(mode, of.avatar_url),
                       file=await image_to_discord(await bot_user.create_pvp_image(mode)))

    @profile_cmd.command(name="demon", aliases=["teams", "team"])
    async def profile_demon_cmd(self, ctx: Context, of: Optional[discord.Member], demon: str = None):
        if not of:
            of = ctx.author

        bot_user = await read_bot_user(of)

        if not bot_user:
            return await ctx.send(ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"{of.display_name} didn't create a profile yet",
                                                          description=f"Use `..profile create` to create one"))

        if demon is None:
            demon = await ask(ctx,
                              question="Which demon team you want to see?",
                              convert=str,
                              default_val="red")

        demon = demon.lower().strip()

        if demon in ["reds", "red"]:
            demon = "red"
        elif demon in ["grays", "gray", "greys", "grey"]:
            demon = "gray"
        elif demon in ["crimsons", "crimson", "howlex"]:
            demon = "crimson"
        elif demon in ["bellmoths", "bellmoth", "belmos"]:
            demon = "bellmoth"

        await ctx.send(ctx.author.mention,
                       embed=await bot_user.create_team_info(demon, of.avatar_url),
                       file=await image_to_discord(await bot_user.create_team_image(demon)))

    @profile_cmd.command(name="create", aliases=["+", "add"])
    async def profile_create_cmd(self, ctx: Context,
                                 name: str = None, team_cc: int = None, box_cc: int = None, friendcode: int = None,
                                 red_team: str = None, gray_team: str = None, crimson_team: str = None,
                                 bellmoth_team: str = None, ungeared_team: str = None, geared_team: str = None):

        bot_user = await read_bot_user(ctx.author)

        if bot_user:
            return await self.profile_edit_cmd(ctx, None, name, team_cc, box_cc, friendcode, red_team, gray_team,
                                               crimson_team, bellmoth_team, ungeared_team, geared_team)

        changelog: Dict[str, Any] = {
            "name": name,
            "team_cc": team_cc,
            "box_cc": box_cc,
            "friendcode": friendcode,
            "red_team": red_team,
            "gray_team": gray_team,
            "crimson_team": crimson_team,
            "bellmoth_team": bellmoth_team,
            "ungeared_team": ungeared_team,
            "geared_team": geared_team
        }

        for changed, provide_question, follow_question, no_input, conversion, default_val, convert_fail, follow_timeout in (
            ("name",
             f"{ctx.author.mention}: Do you want to provide your Grand Cross account name? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your Grand Cross account name?",
             "No name provided.", str, None, None, 30),
            ("friendcode",
             f"{ctx.author.mention}: Do you want to provide your Grand Cross Friendcode? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
             "No Friendcode provided.", int, -1, "Provided Friendcode needs to be a natural number.", 30),
            ("team_cc",
             f"{ctx.author.mention}: Do you want to provide your Grand Cross Team CC? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your Grand Cross Team CC?",
             "No Team CC provided.", convert_team_cc, -1, "Provided Team CC is not a number.", 30),
            ("box_cc",
             f"{ctx.author.mention}: Do you want to provide your Grand Cross Box CC? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your Grand Cross Box CC?",
             "No Box CC provided.", convert_box_cc, -1, "Provided Box CC is not a number.", 30),
            ("red_team",
             f"{ctx.author.mention}: Do you want to provide your team for red demons? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `t1, beastin, bslater, bsrjericho`)*",
             "No team for red demons provided.", convert, tuple(), "Can't find any team like this.", 60*5),
            ("gray_team",
             f"{ctx.author.mention}: Do you want to provide your team for gray demons? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `danaforliz, lolimerlin, ggowther, deathpierce`)*",
             "No team for gray demons provided.", convert, tuple(), "Can't find any team like this.", 60*5),
            ("crimson_team",
             f"{ctx.author.mention}: Do you want to provide your team for crimson demons? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `rderi, rzel, rgowther, rsrjericho`)*",
             "No team for gray demons provided.", convert, tuple(), "Can't find any team like this.", 60*5),
            ("bellmoth_team",
             f"{ctx.author.mention}: Do you want to provide your team for bellmoth demons? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your team for bellmoth demons? *(Please format it like `ggowther, danaforliz, gjericho, deathpierce`)*",
             "No team for bellmoth demons provided.", convert, tuple(), "Can't find any team like this.", 60*5),
            ("ungeared_team",
             f"{ctx.author.mention}: Do you want to provide your team for ungeared pvp? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your team for ungeared pvp? *(Please format it like `ggowther, t1, gliz, deathpierce`)*",
             "No team for ungeared pvp provided.", convert, tuple(), "Can't find any team like this.", 60*5),
            ("geared_team",
             f"{ctx.author.mention}: Do you want to provide your team for geared pvp? __Yes__ _or_ __No__",
             f"{ctx.author.mention}: What's your team for geared pvp? *(Please format it like `ggowther, t1, gliz, deathpierce`)*",
             "No team for geared pvp provided.", convert, tuple(), "Can't find any team like this.", 60 * 5)
        ):
            if not changelog[changed]:
                try:
                    changelog[changed] = await dialogue(ctx, provide_question=provide_question,
                                                        followed_question=follow_question,
                                                        convert=conversion, no_input=no_input, default_val=default_val,
                                                        convert_failed=convert_fail, follow_timeout=follow_timeout)
                except InterruptedError:
                    break
                except SkipError:
                    continue

        async with ctx.typing():
            await BotUser(
                discord_id=ctx.author.id,
                name=name if name else "Not provided",
                team_cc=team_cc if team_cc else -1,
                box_cc=box_cc if box_cc else -1,
                friendcode=friendcode if friendcode else -1,
                demon_teams={
                    "red": red_team if red_team else (),
                    "gray": gray_team if gray_team else (),
                    "crimson": crimson_team if crimson_team else (),
                    "bellmoth": bellmoth_team if bellmoth_team else ()
                },
                offered_demons={"red": 0, "gray": 0, "crimson": 0, "bellmoth": 0},
                pvp_teams={"ungeared": ungeared_team if ungeared_team else (),
                           "geared": geared_team if geared_team else ()}
            ).init_db()

            return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Added your profile!"))

    @profile_cmd.command(name="edit", aliases=["update"])
    async def profile_edit_cmd(self, ctx: Context, what: Optional[str] = None):

        bot_user: BotUser = await read_bot_user(ctx.author)

        if bot_user is None:
            return await ctx.send(ctx.author.mention,
                                  embed=embeds.ErrorEmbed(f"You didn't create a profile yet",
                                                          description=f"Use `..profile create` to create one"))

        async def ask_name():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross account name? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross account name?",
                    no_input="No name provided!",
                    convert=str), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_code():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross Friendcode? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Friendcode?",
                    no_input="No Friendcode provided!",
                    convert=int,
                    convert_failed="Provided Friendcode is not a number!"), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_team_cc():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross Team CC? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Team CC?",
                    no_input="No Team CC provided!",
                    convert=convert_team_cc,
                    convert_failed="Provided Team CC is not a number!"), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_box_cc():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your Grand Cross Box CC? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your Grand Cross Box CC?",
                    no_input="No Box CC provided!",
                    convert=convert_box_cc,
                    convert_failed="Provided Box CC is not a number!"), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_red():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for red demons? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your team for red demons? *(Please format it like `t1, beastin, bslater, bsrjericho`)*",
                    no_input="No Team for red demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60 * 5), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_gray():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for gray demons? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your team for gray demons? *(Please format it like `danaforliz, lolimerlin, ggowther, deathpierce`)*",
                    no_input="No Team for gray demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60 * 5), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_crimson():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for crimson demons? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your team for crimson demons? *(Please format it like `rderi, rzel, rgowther, rsrjericho`)*",
                    no_input="No Team for crimson demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60 * 5), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_bellmoth():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for bellmoth demons? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your team for bellmoth demons? *(Please format it like `ggowther, danaforliz, gjericho, deathpierce`)*",
                    no_input="No Team for bellmoth demons provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60 * 5), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_ungeared():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for ungeared pvp? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your team for ungeared pvp? *(Please format it like `ggowther, t1, gliz, deathpierce`)*",
                    no_input="No Team for ungeared pvp provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60 * 5), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        async def ask_geared():
            try:
                return await dialogue(
                    ctx,
                    provide_question=f"{ctx.author.mention}: Do you want to update your team for geared pvp? __Yes__ _or_ __No__",
                    followed_question=f"{ctx.author.mention}: What's your team for geared pvp? *(Please format it like `ggowther, t1, gliz, deathpierce`)*",
                    no_input="No Team for geared pvp provided!",
                    convert=convert,
                    convert_failed="Can't find any team like this!",
                    follow_timeout=60 * 5), False, False
            except InterruptedError:
                return None, True, False
            except SkipError:
                return None, False, True

        changelog: Dict[str, Any] = {}

        if what:
            for field, possible, func in (
                    ("name", ("name", "account name", "account"), ask_name),
                    ("friendcode", ("code", "friend", "friendcode", "fc"), ask_code),
                    ("team_cc", ("team", "team cc", "teamcc", "tcc"), ask_team_cc),
                    ("box_cc", ("box cc", "boxcc", "bcc"), ask_box_cc),
                    ("red_team", ("red", "red team", "rteam"), ask_red),
                    ("gray_team", ("gray", "grey", "gray team", "grey team", "gteam"), ask_gray),
                    ("crimson_team", ("crimson", "howlex", "crimson team", "howlex team", "cteam", "hteam"), ask_crimson),
                    ("bellmoth_team", ("bellmoth", "belmos", "bellmos", "belmoth"), ask_bellmoth),
                    ("ungeared_team", ("ungeared",), ask_ungeared),
                    ("geared_team", ("geared",), ask_geared)
            ):
                if what in possible:
                    changelog[field] = (await func())[0]

        if len(changelog) == 0:
            for field, func in (
                    ("name", ask_name),
                    ("friendcode", ask_code),
                    ("team_cc", ask_team_cc),
                    ("box_cc", ask_box_cc),
                    ("red_team", ask_red),
                    ("gray_team", ask_gray),
                    ("crimson_team", ask_crimson),
                    ("bellmoth_team", ask_bellmoth),
                    ("ungeared_team", ask_ungeared),
                    ("geared_team", ask_geared)
            ):
                question = await func()
                changelog[field] = question[0]

                if question[1]:
                    break
                elif question[2]:
                    continue

        async with ctx.typing():
            if "name" in changelog:
                await bot_user.set_name(changelog["name"])

            if "friendcode" in changelog:
                await bot_user.set_friendcode(changelog["friendcode"])

            if "team_cc" in changelog:
                await bot_user.set_team_cc(changelog["team_cc"])

            if "box_cc" in changelog:
                await bot_user.set_box_cc(changelog["box_cc"])

            if "red_team" in changelog:
                await bot_user.set_demon_team("red", changelog["red_team"])

            if "gray_team" in changelog:
                await bot_user.set_demon_team("gray", changelog["gray_team"])

            if "crimson_team" in changelog:
                await bot_user.set_demon_team("crimson", changelog["crimson_team"])

            if "bellmoth_team" in changelog:
                await bot_user.set_demon_team("bellmoth", changelog["bellmoth_team"])

            if "ungeared_team" in changelog:
                await bot_user.set_pvp_team("ungeared", changelog["ungeared_team"])

            if "geared_team" in changelog:
                await bot_user.set_pvp_team("geared", changelog["geared_team"])

            return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Updated your profile!"))


def setup(_bot):
    _bot.add_cog(ProfileCog(_bot))
