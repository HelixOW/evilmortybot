import discord
import PIL.Image as Images
from discord.ext import commands
from discord.ext.commands import Bot, Context
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
                 demon_teams: Dict[str, List[int]],
                 pulled_ssrs: Dict[int, int],
                 pulled_overall: Dict[int, int],
                 shafts: Dict[int, int]):
        self.shafts: Dict[int, int] = shafts
        self.pulled_overall: Dict[int, int] = pulled_overall
        self.pulled_ssrs: Dict[int, int] = pulled_ssrs
        self.demon_teams: Dict[str, List[Unit]] = {demon: [unit_by_id(int(x)) for x in demon_teams[demon]] for demon in demon_teams}
        self.offered_demons: Dict[str, int] = offered_demons
        self.friendcode: int = friendcode
        self.box_cc: float = box_cc
        self.team_cc: float = team_cc
        self.name: str = name
        self.discord_id: int = discord_id

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

    async def set_demon_team(self, demon: str, team: List[int]):
        self.demon_teams[demon] = team
        cursor: Cursor = connection.cursor()
        if demon == "red":
            cursor.execute(
                'UPDATE "bot_users" SET red_demon_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        elif demon == "gray":
            cursor.execute(
                'UPDATE "bot_users" SET gray_demon_team=? WHERE discord_id=?',
                (",".join(team), self.discord_id)
            )
        elif demon == "crimson":
            cursor.execute(
                'UPDATE "bot_users" SET crimson_demon_team=? WHERE discord_id=?',
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
        return embeds.DrawEmbed(title=f"Info about {self.name}").add_field(
            name="Team CC",
            value=f"```{self.team_cc}```"
        ).add_field(
            name="Box CC",
            value=f"```{self.box_cc}```"
        ).add_field(
            name="Friendcode",
            value=f"```{self.friendcode}```"
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


async def read_bot_user(bot: Bot, member: discord.Member):
    cursor: Cursor = connection.cursor()
    row = cursor.execute('SELECT * FROM "bot_users" WHERE discord_id=?', (member.id,)).fetchone()

    if row is None:
        return None

    ssr_data = {}
    pull_data = {}
    shaft_data = {}

    for guild in bot.guilds:
        user_data = cursor.execute(
            'SELECT ssr_amount, pull_amount, shafts FROM "user_pulls" WHERE user_id=? AND guild=?', (member.id, guild.id)
        ).fetchone()
        ssr_data[guild.id] = user_data[0]
        pull_data[guild.id] = user_data[1]
        shaft_data[guild.id] = user_data[2]

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
        },
        pulled_ssrs=ssr_data,
        pulled_overall=pull_data,
        shafts=shaft_data
    )


class ProfileCog(commands.Cog):
    def __init__(self, _bot):
        self.bot = _bot

    @commands.group(name="profile")
    async def profile_cmd(self, ctx: Context, of: Optional[discord.Member]):
        if of is None:
            of = ctx.author

        if ctx.invoked_subcommand is None:
            bot_user = await read_bot_user(self.bot, of)

            if bot_user is None:
                return await ctx.send(ctx.author.mention,
                                      embed=embeds.ErrorEmbed(f"{of.display_name} didn't create a profile yet",
                                                              description=f"Use `..profile create` to create one"))

            await ctx.send(ctx.author.mention,
                           embed=await bot_user.create_info(ctx.guild, ctx.author.avatar_url),
                           file=await image_to_discord(await bot_user.create_all_team_image()))

    @profile_cmd.command(name="create", aliases=["+", "add"])
    async def profile_create_cmd(self, ctx, team_cc):

        pass


def setup(_bot):
    _bot.add_cog(ProfileCog(_bot))
