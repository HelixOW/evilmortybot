import asyncio
import random as ra
import sqlite3 as sql
import typing
from enum import Enum
from io import BytesIO
from typing import List

import discord
import requests
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from discord.ext import commands
from discord.ext.commands import HelpCommand

# Version 1.0
# TODO:
#   - maybe web interface for new units?
#   - box

with open("data/bot_token.txt", 'r') as file:
    TOKEN = file.read()
IMG_SIZE = 150
LOADING_IMAGE_URL = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
CONN = sql.connect('data/data.db')
CURSOR = CONN.cursor()

HELP_EMBED_1 = discord.Embed(
    title="Help 1/2",
    description="""
                __*Commands:*__
                    `..unit` -> `Check Info`
                    `..team` -> `Check Info`
                    `..pvp <@Enemy>` -> `Check Info`
                    `..single [@For] [banner="banner one"]` 
                    `..multi [@For] [banner="banner one"]`
                    `..shaft [@For] [banner="banner one"]`
                    `..summon [banner="banner one"]`
                    `..stats <luck, ssrs, units, shafts>`
                    `..top <luck, ssrs, units, shafts>`
                    `..create "<name>" <attribute> <grade> "<image url>" [race=unknown] [affection=none]`

                    __*Info:*__
                    You can use different attributes to narrow down the possibilities:
                     `race:` demons, giants, humans, fairies, goddess, unknown
                     `type:` blue, red, green
                     `grade:` r, sr, ssr
                     `event:` gc, slime, aot, kof, new year, halloween, festival, valentine
                     `affection:` sins, commandments, holy knights, catastrophes, archangels, none

                    If you want to define e.g. __multiple races append__ them with a `,` after each race
                    If you want to use __multiple attributes append__ a `&` after each attribute

                    `<>`, that means you **have to provide** this argument
                    `[]`, that means you **can provide** this argument
                    `=` inside a argument means, whatever comes after the equals is the **default value**

                    __Available banners:__ banner 1, banner 2, part 1, part 2, gssr part 1, gssr part 2, race 1, race 2, humans
                            """,
    colour=discord.Color.gold(),
)
HELP_EMBED_2 = discord.Embed(
    title="Help 2/2",
    description="""__Examples:__
                            `..unit` ~ returns a random unit
                            `..unit race: demons, giants & type: red` ~ returns a random red demon or red giant
                            `..team` ~ returns a random pvp team
                            `..team race: demons` ~ returns a random pvp team with only demons
                            `..single part two` ~ does a single summon on the Part 2 banner
                            `..multi race two` ~ does a 5x summon on the Demon/Fairy/Goddess banner
                            `..multi banner two` ~ does a 11x summon on the most recent banner                    
                            `..shaft` ~ does a 11x summon until you get a SSR
                            `..shaft race two` ~ does a 5x summon on the Demon/Fairy/Goddess banner until you get a SSR
                            `..create "[Demon Slayer] Tanjiro" red sr "URL to image" human` ~ Creates a Red SR Tanjiro
                            """,
    colour=discord.Color.gold(),
)
UNIT_LOOKUP_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                        description="Can't find any unit which meets those requirements")
TEAM_LOOKUP_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                        description="Can't find any team which meets those requirements")
TEAM_COOLDOWN_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                          description="Please wait before using another ..team")
PVP_COOLDOWN_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                         description="Please wait before using another ..pvp")
SUMMON_THROTTLE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                            description="Please don't summon more then 5x at once")
UNIT_CREATE_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                      description="""
                                                      `..create <name> <attribute> <grade> <file_url> [race] [affection]`

                                                      For more info please do `..help`
                                                      """)
CROP_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                               description="..crop requires at least a url of a file to crop (..help for more)")
RESIZE_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                 description="..resize requires at least a url of a file to crop (..help for more)")
LOADING_EMBED = discord.Embed(title="Loading...")
IMAGES_LOADED_EMBED = discord.Embed(title="Images loaded!")

TEAM_REROLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
PVP_REROLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣️"]


class CustomHelp(HelpCommand):
    async def send_bot_help(self, mapping):
        await self.get_destination().send(embed=HELP_EMBED_1)
        await self.get_destination().send(embed=HELP_EMBED_2)


BOT = commands.Bot(command_prefix='..', description='..help for Help', help_command=CustomHelp())


class Grade(Enum):
    R = "r"
    SR = "sr"
    SSR = "ssr"


class Type(Enum):
    RED = "red"
    GRE = "green"
    BLUE = "blue"


class Race(Enum):
    DEMON = "demon"
    GIANT = "giant"
    HUMAN = "human"
    FAIRY = "fairy"
    GODDESS = "goddess"
    UNKNOWN = "unknown"


class Event(Enum):
    GC = "gc"
    SLI = "slime"
    AOT = "aot"
    KOF = "kof"
    NEY = "newyear"
    HAL = "halloween"
    FES = "festival"
    VAL = "valentine"
    CUS = "custom"


class Affection(Enum):
    SIN = "sins"
    COMMANDMENTS = "commandments"
    KNIGHT = "holyknights"
    CATASTROPHE = "catastrophes"
    ANGEL = "archangels"
    NONE = "none"


class BannerType(Enum):
    ELEVEN = 11
    FIVE = 5


class LeaderboardType(Enum):
    LUCK = "luck"
    MOST_SSR = "ssrs"
    MOST_UNITS = "units"
    MOST_SHAFTS = "shafts"
    MOST_SSR_ROTATION = "rotation"


def strip_whitespace(arg: str) -> str:
    return arg.replace(" ", "")


def map_attribute(raw_att: str) -> Type:
    raw_att = raw_att.lower()
    if raw_att in ["blue", "speed", "b"]:
        return Type.BLUE
    elif raw_att in ["red", "strength", "r"]:
        return Type.RED
    elif raw_att in ["green", "hp", "g"]:
        return Type.GRE


def map_grade(raw_grade: str) -> Grade:
    raw_grade = raw_grade.lower()
    if raw_grade == "r":
        return Grade.R
    elif raw_grade == "sr":
        return Grade.SR
    elif raw_grade == "ssr":
        return Grade.SSR


def map_race(raw_race: str) -> Race:
    raw_race = raw_race.lower()
    if raw_race in ["demon", "demons"]:
        return Race.DEMON
    elif raw_race in ["giant", "giants"]:
        return Race.GIANT
    elif raw_race in ["fairy", "fairies"]:
        return Race.FAIRY
    elif raw_race in ["human", "humans"]:
        return Race.HUMAN
    elif raw_race in ["goddess", "god", "gods"]:
        return Race.GODDESS
    else:
        return Race.UNKNOWN


def map_event(raw_event: str) -> Event:
    raw_event = strip_whitespace(raw_event).lower()
    if raw_event in ["slime", "tensura"]:
        return Event.SLI
    elif raw_event in ["aot", "attackontitan", "titan"]:
        return Event.AOT
    elif raw_event in ["kof", "kingoffighter", "kingoffighters"]:
        return Event.KOF
    elif raw_event in ["valentine", "val"]:
        return Event.VAL
    elif raw_event in ["newyears", "newyear", "ny"]:
        return Event.NEY
    elif raw_event in ["halloween", "hal", "hw"]:
        return Event.HAL
    elif raw_event in ["festival", "fes", "fest"]:
        return Event.FES
    elif raw_event in ["custom"]:
        return Event.CUS
    else:
        return Event.GC


def map_affection(raw_affection: str) -> Affection:
    raw_affection = strip_whitespace(raw_affection).lower()
    if raw_affection in ["sins", "sin"]:
        return Affection.SIN
    elif raw_affection in ["holyknight", "holyknights", "knights", "knight"]:
        return Affection.KNIGHT
    elif raw_affection in ["commandments", "commandment", "command"]:
        return Affection.COMMANDMENTS
    elif raw_affection in ["catastrophes", "catastrophes"]:
        return Affection.CATASTROPHE
    elif raw_affection in ["arcangels", "angels", "angel", "arcangel"]:
        return Affection.ANGEL
    else:
        return Affection.NONE


def map_bannertype(raw_bannertype: int) -> BannerType:
    if raw_bannertype == 5:
        return BannerType.FIVE
    return BannerType.ELEVEN


def map_leaderboard(raw_leaderboard: str) -> LeaderboardType:
    raw_leaderboard = strip_whitespace(raw_leaderboard).lower()
    if raw_leaderboard in ["ssrs", "ssrs", "mostssr", "mostssrs"]:
        return LeaderboardType.MOST_SSR
    elif raw_leaderboard in ["units", "unit", "mostunits", "mostunit"]:
        return LeaderboardType.MOST_UNITS
    elif raw_leaderboard in ["shaft", "shafts", "mostshafts", "mostshaft"]:
        return LeaderboardType.MOST_SHAFTS
    elif raw_leaderboard in ["rotation", "rotations", "rot", "rots"]:
        return LeaderboardType.MOST_SSR_ROTATION
    return LeaderboardType.LUCK


FRAMES = {
    Type.BLUE: {
        Grade.R: "gc/frames/blue_r_frame.png",
        Grade.SR: "gc/frames/blue_sr_frame.png",
        Grade.SSR: "gc/frames/blue_ssr_frame.png"
    },
    Type.RED: {
        Grade.R: "gc/frames/red_r_frame.png",
        Grade.SR: "gc/frames/red_sr_frame.png",
        Grade.SSR: "gc/frames/red_ssr_frame.png"
    },
    Type.GRE: {
        Grade.R: "gc/frames/green_r_frame.png",
        Grade.SR: "gc/frames/green_sr_frame.png",
        Grade.SSR: "gc/frames/green_ssr_frame.png"
    },
}
FRAME_BACKGROUNDS = {
    Grade.R: "gc/frames/r_frame_background.png",
    Grade.SR: "gc/frames/sr_frame_background.png",
    Grade.SSR: "gc/frames/ssr_frame_background.png"
}


def image_to_discord(img: Image, image_name: str) -> discord.File:
    with BytesIO() as image_bin:
        img.save(image_bin, 'PNG')
        image_bin.seek(0)
        image_file = discord.File(fp=image_bin, filename=image_name)
    return image_file


class Unit:
    def __init__(self, unit_id: int,
                 name: str,
                 simple_name: str,
                 type: Type,
                 grade: Grade,
                 race: Race,
                 event: Event = Event.GC,
                 affection: Affection = Affection.NONE,
                 icon: str = "gc/icons/{}.png"):
        self.unit_id: int = unit_id
        self.name: str = name
        self.simple_name: str = simple_name
        self.type: Type = type
        self.grade: Grade = grade
        self.race: Race = race
        self.event: Event = event
        self.affection: Affection = affection
        img = Image.new('RGBA', (IMG_SIZE, IMG_SIZE))
        img.paste(Image.open(icon.format(unit_id)).resize((IMG_SIZE, IMG_SIZE)), (0, 0))
        self.icon: Image = img

    def discord_icon(self) -> discord.File:
        return image_to_discord(self.icon, "unit.png")

    def discord_color(self) -> discord.Color:
        if self.type == Type.RED:
            return discord.Color.red()
        elif self.type == Type.GRE:
            return discord.Color.green()
        elif self.type == Type.BLUE:
            return discord.Color.blue()
        else:
            return discord.Color.gold()


UNITS = []


def read_units_from_db():
    UNITS.clear()
    CONN.commit()
    data = CURSOR.execute('SELECT * FROM units').fetchall()
    for row in data:
        u = Unit(
            unit_id=row[0],
            name=row[1],
            simple_name=row[2],
            type=map_attribute(row[3]),
            grade=map_grade(row[4]),
            race=map_race(row[5]),
            event=map_event(row[6]),
            affection=map_affection(row[7])
        )
        UNITS.append(u)


read_units_from_db()


R_UNITS = list(filter(lambda x: x.grade == Grade.R, UNITS))
SR_UNITS = list(filter(lambda x: x.grade == Grade.SR and x.event == Event.GC, UNITS))
TEAMS = {
    "the one": {
        1: [157],
        2: [151, 137, 116],
        3: [134],
        4: [137, 116]
    },
    "the archangels": {
        1: [151],
        2: [152],
        3: [145, 125],
        4: [137]
    },
    "lv goddess": {
        1: [116],
        2: [8, 34, 120, 134],
        3: [137],
        4: [49]
    },
    "lv ult rush": {
        1: [116],
        2: [8, 79, 100],
        3: [134, 34, 137],
        4: [49, 105]
    },
    "3 debuffs": {
        1: [148],
        2: [149],
        3: [137, 131, 145, 150],
        4: [49, 153]
    },
    "pierce": {
        1: [133, 79, 145],
        2: [85],
        3: [87],
        4: [105, 35, 130]
    },
    "zeldris": {
        1: [125],
        2: [145],
        3: [143],
        4: [49, 105]
    }
}


class Banner:
    def __init__(self, name: List[str],
                 pretty_name: str,
                 units: List[Unit],
                 ssr_unit_rate: float,
                 sr_unit_rate: float,
                 bg_url: str,
                 r_unit_rate: float = 6.6667,
                 rate_up_units=None,
                 ssr_unit_rate_up: float = 0.5,
                 includes_all_sr: bool = True,
                 includes_all_r: bool = True,
                 banner_type: BannerType = BannerType.ELEVEN):
        if rate_up_units is None:
            rate_up_units = []
        self.name: List[str] = name
        self.pretty_name: str = pretty_name
        self.includes_all_sr: bool = includes_all_sr
        self.includes_all_r: bool = includes_all_r

        if sr_unit_rate != 0 and includes_all_sr:
            units += SR_UNITS
        if r_unit_rate != 0 and includes_all_r:
            units += R_UNITS

        self.units: List[Unit] = units
        self.rate_up_units: List[Unit] = rate_up_units
        self.ssr_unit_rate: float = ssr_unit_rate
        self.ssr_unit_rate_up: float = ssr_unit_rate_up
        self.sr_unit_rate: float = sr_unit_rate
        self.r_unit_rate: float = r_unit_rate
        self.banner_type: BannerType = banner_type
        self.r_units: List[Unit] = list(filter(lambda x: x.grade == Grade.R, self.units))
        self.sr_units: List[Unit] = list(filter(lambda x: x.grade == Grade.SR, self.units))
        self.ssr_units: List[Unit] = list(
            filter(lambda x: x.grade == Grade.SSR and x not in self.rate_up_units, self.units))
        self.ssr_chance: float = (self.ssr_unit_rate_up * len(self.rate_up_units)) + (
                self.ssr_unit_rate * (len(self.ssr_units)))
        self.ssr_rate_up_chance: float = (self.ssr_unit_rate_up * len(self.rate_up_units)) if len(
            self.rate_up_units) != 0 else 0
        self.sr_chance: float = (self.sr_unit_rate * len(self.sr_units))
        self.background: str = bg_url


def units_by_id(ids: List[int]) -> List[Unit]:
    found = list(filter(lambda x: x.unit_id in ids, UNITS))
    if len(found) == 0:
        raise LookupError
    return found


def unit_by_id(unit_id: int) -> Unit:
    return next((x for x in UNITS if unit_id == x.unit_id), None)


def banner_by_name(name: str) -> Banner:
    return next((x for x in ALL_BANNERS if name in x.name), None)


def banners_by_name(names: List[str]) -> List[Banner]:
    found = list(filter(lambda x: not set(x.name).isdisjoint(names), ALL_BANNERS))
    if len(found) == 0:
        raise ValueError
    return found


def file_exists(file) -> bool:
    try:
        with open(file):
            return True
    except FileNotFoundError:
        return False


ALL_BANNERS = []


def read_banners_from_db():
    ALL_BANNERS.clear()
    CONN.commit()
    banner_data = CURSOR.execute('SELECT * FROM banners').fetchall()
    for row in banner_data:
        banner_name_data = CURSOR.execute('SELECT alternative_name FROM banner_names WHERE name=?', (row[0],)).fetchall()
        banner_unit_data = CURSOR.execute('SELECT unit_id FROM banners_units WHERE banner_name=?', (row[0],)).fetchall()
        banner_rate_up_unit_data = CURSOR.execute('SELECT unit_id FROM banners_rate_up_units WHERE banner_name=?', (row[0],)).fetchall()
        banner_names = [row[0]]
        unit_list = []
        rate_up_unit_list = []

        for sql_banner_names in banner_name_data:
            banner_names.append(sql_banner_names[0])
        for sql_unit_id in banner_unit_data:
            unit_list.append(unit_by_id(sql_unit_id[0]))
        for sql_unit_id in banner_rate_up_unit_data:
            rate_up_unit_list.append(unit_by_id(sql_unit_id[0]))

        b = Banner(
            name=banner_names,
            pretty_name=row[1],
            ssr_unit_rate=row[2],
            sr_unit_rate=row[3],
            bg_url=row[4],
            r_unit_rate=row[5],
            ssr_unit_rate_up=row[6],
            includes_all_sr=True if row[7] == 1 else False,
            includes_all_r=True if row[8] == 1 else False,
            banner_type=map_bannertype(row[9]),
            units=unit_list,
            rate_up_units=rate_up_unit_list
        )
        ALL_BANNERS.append(b)


read_banners_from_db()


@BOT.event
async def on_ready():
    CURSOR.execute("""CREATE TABLE IF NOT EXISTS "custom_units" (
        unit_id INTEGER PRIMARY KEY,
        name Text,
        type Text,
        grade Text,
        race Text,
        affection Text)""")
    # CURSOR.execute("""CREATE TABLE IF NOT EXISTS "units" (
    #         unit_id INTEGER PRIMARY KEY,
    #         name Text,
    #         simple_name Text,
    #         type Text,
    #         grade Text,
    #         race Text,
    #         event Text,
    #         affection Text)""")
    CURSOR.execute("""CREATE TABLE IF NOT EXISTS "user_pulls" (
                user_id INTEGER,
                ssr_amount INTEGER,
                pull_amount INTEGER,
                guild INTEGER,
                shafts INTEGER
    )""")
    CURSOR.execute("""CREATE TABLE IF NOT EXISTS "channels" (
                    channel INTEGER
    )""")

    CONN.commit()

    for attr_key in FRAMES:
        for grade_key in FRAMES[attr_key]:
            FRAMES[attr_key][grade_key] = Image.open(FRAMES[attr_key][grade_key]).resize((IMG_SIZE, IMG_SIZE)).convert(
                "RGBA")
    for grade_key in FRAME_BACKGROUNDS:
        FRAME_BACKGROUNDS[grade_key] = Image.open(FRAME_BACKGROUNDS[grade_key]).resize((IMG_SIZE, IMG_SIZE)).convert(
            "RGBA")
    await BOT.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="..help"))

    read_custom_units_from_db()
    add_custom_units_to_banner()

    print('Logged in as')
    print(BOT.user.name)
    print(BOT.user.id)
    print('--------')


def get_user_pull(user: discord.Member) -> dict:
    # user_id, ssr_amount, pull_amount
    CONN.commit()
    data = CURSOR.execute('SELECT * FROM user_pulls WHERE user_id=? AND guild=?', (user.id, user.guild.id)).fetchone()
    if data is None:
        return {}
    return {"ssr_amount": data[1], "pull_amount": data[2], "guild": data[3], "shafts": data[4]}


async def get_top_users(guild: discord.Guild, action: LeaderboardType = LeaderboardType.LUCK) -> List[dict]:
    CONN.commit()
    data = CURSOR.execute('SELECT * FROM user_pulls WHERE guild=? LIMIT 1', (guild.id,)).fetchone()
    if data is None:
        return {}
    if action == LeaderboardType.MOST_SHAFTS:
        data = CURSOR.execute('SELECT * FROM user_pulls WHERE guild=? ORDER BY shafts DESC LIMIT 10',
                              (guild.id,)).fetchall()
        ret = []
        for i in range(10):
            if i == len(data):
                break
            user = await BOT.fetch_user(data[i][0])
            ret.append({
                "place": i + 1,
                "name": user.display_name,
                "shafts": data[i][4]
            })
        return ret
    elif action == LeaderboardType.LUCK:
        data = CURSOR.execute(
            'SELECT *, round((CAST(ssr_amount as REAL)/CAST(pull_amount as REAL)), 4) percent FROM user_pulls WHERE guild=? ORDER BY percent DESC LIMIT 10',
            (guild.id,)).fetchall()
        ret = []
        for i in range(10):
            if i == len(data):
                break
            user = await BOT.fetch_user(data[i][0])
            ret.append({
                "place": i + 1,
                "name": user.display_name,
                "luck": round((data[i][1] / data[i][2]) * 100, 2),
                "pull-amount": data[i][2]
            })
        return ret
    elif action == LeaderboardType.MOST_SSR:
        data = CURSOR.execute(
            'SELECT * FROM user_pulls WHERE guild=? ORDER BY ssr_amount DESC LIMIT 10',
            (guild.id,)).fetchall()
        ret = []
        for i in range(10):
            if i == len(data):
                break
            user = await BOT.fetch_user(data[i][0])
            ret.append({
                "place": i + 1,
                "name": user.display_name,
                "ssrs": data[i][1],
                "pull-amount": data[i][2]
            })
        return ret
    elif action == LeaderboardType.MOST_UNITS:
        data = CURSOR.execute(
            'SELECT * FROM user_pulls WHERE guild=? ORDER BY pull_amount DESC LIMIT 10',
            (guild.id,)).fetchall()
        ret = []
        for i in range(10):
            if i == len(data):
                break
            user = await BOT.fetch_user(data[i][0])
            ret.append({
                "place": i + 1,
                "name": user.display_name,
                "pull-amount": data[i][2]
            })
        return ret


@BOT.command()
async def top(ctx, action="luck"):
    action = map_leaderboard(action)
    tops = await get_top_users(ctx.message.guild, action)
    if len(tops) == 0:
        return await ctx.send(
            embed=discord.Embed(title="Nobody summoned yet", description="Use `..multi`, `..single` or `..shaft`"))

    if action == LeaderboardType.LUCK:
        top_str = '\n'.join(
            ["**{}.** {} with a *{}%* SSR droprate in their pulls. Total of {} Units".format(top["place"],
                                                                                             top["name"],
                                                                                             top["luck"],
                                                                                             top["pull-amount"])
             for top in tops])
        await ctx.send(embed=discord.Embed(title=f"Luckiest Members in {ctx.message.guild.name}", description=top_str,
                                           colour=discord.Colour.gold()).set_thumbnail(url=ctx.message.guild.icon_url))
    elif action == LeaderboardType.MOST_SSR:
        top_str = '\n'.join(["**{}.** {} with *{} SSRs*. Total of *{} Units*".format(
            top["place"], top["name"], top["ssrs"], top["pull-amount"])
            for top in tops])
        await ctx.send(embed=discord.Embed(title=f"Members with most drawn SSRs in {ctx.message.guild.name}",
                                           description=top_str, colour=discord.Colour.gold())
                       .set_thumbnail(url=ctx.message.guild.icon_url))
    elif action == LeaderboardType.MOST_UNITS:
        top_str = '\n'.join(["**{}.** {} with *{} Units*".format(
            top["place"], top["name"], top["pull-amount"])
            for top in tops])
        await ctx.send(embed=discord.Embed(title=f"Members with most drawn Units in {ctx.message.guild.name}",
                                           description=top_str, colour=discord.Colour.gold())
                       .set_thumbnail(url=ctx.message.guild.icon_url))
    elif action == LeaderboardType.MOST_SHAFTS:
        top_str = '\n'.join(["**{}.** {} with *{} Shafts*".format(
            top["place"], top["name"], top["shafts"])
            for top in tops])
        await ctx.send(embed=discord.Embed(title=f"Most Shafted Members in {ctx.message.guild.name}",
                                           description=top_str, colour=discord.Colour.gold())
                       .set_thumbnail(url=ctx.message.guild.icon_url))


def add_user_pull(user: discord.Member, got_ssr: bool):
    data = get_user_pull(user)
    if len(data) == 0:
        CURSOR.execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                       (user.id, 1 if got_ssr else 0, 1, user.guild.id, 0))
    else:
        if got_ssr:
            CURSOR.execute('UPDATE user_pulls SET ssr_amount=?, pull_amount=? WHERE user_id=? AND guild=?',
                           (data["ssr_amount"] + 1, data["pull_amount"] + 1, user.id, user.guild.id))
        else:
            CURSOR.execute('UPDATE user_pulls SET pull_amount=? WHERE user_id=? AND guild=?',
                           (data["pull_amount"] + 1, user.id, user.guild.id))


def add_shaft(user: discord.Member, amount: int):
    data = get_user_pull(user)
    if len(data) != 0:
        CURSOR.execute('UPDATE user_pulls SET shafts=? WHERE user_id=? AND guild=?',
                       (data["shafts"] + amount, user.id, user.guild.id))
    else:
        CURSOR.execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                       (user.id, 0, 0, user.guild.id, amount))


# ..stats
@BOT.command()
async def stats(ctx, person: typing.Optional[discord.Member], *, action="luck"):
    action = map_leaderboard(action)
    if person is None:
        person = ctx.message.author
    data = get_user_pull(person)
    ssrs = data["ssr_amount"] if len(data) != 0 else 0
    pulls = data["pull_amount"] if len(data) != 0 else 0
    percent = data["ssr_amount"] / data["pull_amount"] if len(data) != 0 else 0
    percent = round(percent * 100, 2)
    if action == LeaderboardType.LUCK:
        await ctx.send(
            content=f"{person.mention}'s luck:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s luck:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently got a *{percent}%* SSR droprate in their pulls, with *{ssrs} SSRs* in *{pulls} Units*"))
    elif action == LeaderboardType.MOST_SSR:
        await ctx.send(
            content=f"{person.mention}'s SSRs:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s SSRs:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently has *{ssrs} SSRs*"))
    elif action == LeaderboardType.MOST_UNITS:
        await ctx.send(
            content=f"{person.mention}'s Units:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s Units:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently has *{pulls} Units*"))


RACES = [Race.DEMON, Race.GIANT, Race.HUMAN, Race.FAIRY, Race.GODDESS, Race.UNKNOWN]
GRADES = [Grade.R, Grade.SR, Grade.SSR]
TYPES = [Type.RED, Type.GRE, Type.BLUE]
EVENTS = [Event.GC, Event.SLI, Event.AOT, Event.KOF, Event.FES, Event.NEY, Event.VAL, Event.HAL]
AFFECTIONS = [Affection.SIN, Affection.COMMANDMENTS, Affection.CATASTROPHE, Affection.ANGEL, Affection.KNIGHT,
              Affection.NONE]


def get_matching_units(grades: List[Grade] = None,
                       types: List[Type] = None,
                       races: List[Race] = None,
                       events: List[Event] = None,
                       affections: List[Affection] = None) -> List[Unit]:
    if races is None or races == []:
        races = RACES.copy()
    if grades is None or grades == []:
        grades = GRADES.copy()
    if types is None or types == []:
        types = TYPES.copy()
    if events is None or events == []:
        events = EVENTS.copy()
    if affections is None or affections == []:
        affections = AFFECTIONS.copy()

    possible_units = list(filter(lambda x:
                                 x.race in races and x.type in types and x.grade in grades and x.event in events
                                 and x.affection in affections,
                                 UNITS))

    if len(possible_units) == 0:
        raise LookupError

    return possible_units


def create_random_unit(grades: List[Grade] = None,
                       types: List[Type] = None,
                       races: List[Race] = None,
                       events: List[Event] = None,
                       affections: List[Affection] = None) -> Unit:
    possible_units = get_matching_units(grades=grades,
                                        types=types,
                                        races=races,
                                        events=events,
                                        affections=affections)
    return possible_units[ra.randint(0, len(possible_units) - 1)]


def lookup_possible_units(arg: str):
    args = strip_whitespace(arg.lower()).split("&")
    race = []
    races = {
        Race.HUMAN: 0,
        Race.FAIRY: 0,
        Race.GIANT: 0,
        Race.UNKNOWN: 0,
        Race.DEMON: 0,
        Race.GODDESS: 0
    }
    grade = []
    attribute = []
    event = []
    affection = []

    for i in range(len(args)):
        if args[i].startswith("race:"):
            race_str = args[i].replace("race:", "")

            if race_str.startswith("!"):
                inv_race = map_race(race_str.replace("!", "")).value
                race = list(filter(lambda x: x != inv_race, list(map(lambda x: x.value, RACES))))
            else:
                pre_race = race_str.split(",")
                for ii in range(len(pre_race)):
                    apr = pre_race[ii].split("*")
                    if len(apr) == 2:
                        race.append(apr[1])
                        races[map_race(apr[1])] += int(apr[0])
                    else:
                        race.append(pre_race[ii])
        elif args[i].startswith("grade:"):
            grade_str = args[i].replace("grade:", "")
            if grade_str.startswith("!"):
                inv_grade = grade_str.replace("!", "")
                grade = list(filter(lambda x: x != inv_grade, list(map(lambda x: x.value, GRADES))))
            else:
                grade = grade_str.split(",")
        elif args[i].startswith("attribute:") or args[i].startswith("type:"):
            type_str = args[i].replace("attribute:", "").replace("type:", "")
            if type_str.startswith("!"):
                inv_type = type_str.replace("!", "")
                attribute = list(filter(lambda x: x != inv_type, list(map(lambda x: x.value, TYPES))))
            else:
                attribute = type_str.split(",")
        elif args[i].startswith("event:") or args[i].startswith("collab:"):
            event_str = args[i].replace("event:", "").replace("collab:", "")
            if event_str.startswith("!"):
                inv_event = event_str.replace("!", "")
                event = list(filter(lambda x: x != inv_event, list(map(lambda x: x.value, EVENTS))))
            else:
                event = event_str.split(",")
        elif args[i].startswith("affection:"):
            affection_str = args[i].replace("affection:", "")
            if affection_str.startswith("!"):
                inv_affection = affection_str.replace("!", "")
                affection = list(filter(lambda x: x != inv_affection, list(map(lambda x: x.value, AFFECTIONS))))
            else:
                affection = affection_str.split(",")

    race = list(map(map_race, race))
    grade = list(map(map_grade, grade))
    attribute = list(map(map_attribute, attribute))
    event = list(map(map_event, event))
    affection = list(map(map_affection, affection))

    return {
        "race": race,
        "max race count": races,
        "grade": grade,
        "type": attribute,
        "event": event,
        "affection": affection
    }


# ..unit
@BOT.command()
async def unit(ctx, *, args: str = ""):
    attributes = lookup_possible_units(args)
    try:
        random_unit = create_random_unit(grades=attributes["grade"],
                                         types=attributes["type"],
                                         races=attributes["race"],
                                         events=attributes["event"],
                                         affections=attributes["affection"])
        await ctx.send(content=f"{ctx.message.author.mention} this is your unit",
                       embed=discord.Embed(title=random_unit.name, colour=random_unit.discord_color())
                       .set_image(url="attachment://unit.png"),
                       file=random_unit.discord_icon())
    except LookupError:
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=UNIT_LOOKUP_ERROR_EMBED)


team_time_check = []
pvp_time_check = []


def replace_duplicates(attr, team):
    team_simple_names = ["", "", "", ""]
    team_races = {
        Race.HUMAN: 0,
        Race.FAIRY: 0,
        Race.GIANT: 0,
        Race.UNKNOWN: 0,
        Race.DEMON: 0,
        Race.GODDESS: 0
    }
    max_races = attr["max race count"]

    checker = 0
    for i in max_races:
        checker += max_races[i]

    if checker != 4 and checker != 0:
        raise ValueError("Too many Races")

    def check_races(abba):
        if checker == 0:
            return True
        if team_races[team[abba].race] >= max_races[team[abba].race]:
            if team[abba].race in attr["race"]:
                attr["race"].remove(team[abba].race)
            team[abba] = create_random_unit(races=attr["race"], grades=attr["grade"],
                                            types=attr["type"],
                                            events=attr["event"], affections=attr["affection"])
            return False
        else:
            team_races[team[abba].race] += 1
            return True

    def check_names(abba):
        if team[abba].simple_name not in team_simple_names:
            team_simple_names[abba] = team[abba].simple_name
            return True
        else:
            team[abba] = create_random_unit(races=attr["race"], grades=attr["grade"],
                                            types=attr["type"],
                                            events=attr["event"], affections=attr["affection"])
            return False

    for i in range(len(team)):
        for b in range(500):
            if check_names(i) and check_races(i):
                break

        if team_simple_names[i] == "":
            raise ValueError("Not enough Units available")


# ..pvp
@BOT.command()
async def pvp(ctx, enemy: discord.Member, attr: str = ""):
    attr = lookup_possible_units(attr)
    proposed_team_p1 = [
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
    ]
    proposed_team_p2 = [
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"]),
    ]

    try:
        replace_duplicates(attr, proposed_team_p1)
        replace_duplicates(attr, proposed_team_p2)
    except ValueError as e:
        return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                              embed=TEAM_LOOKUP_ERROR_EMBED)

    player1 = ctx.message.author

    if player1 in pvp_time_check or enemy in pvp_time_check:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=PVP_COOLDOWN_ERROR_EMBED)

    changed_units = {
        0: [],
        1: [],
        2: [],
        3: []
    }

    async def send(player: discord.Member, last_message=None):
        if last_message is not None:
            await last_message.delete()

        if player not in pvp_time_check:
            pvp_time_check.append(player)

        loading_message = await ctx.send(embed=LOADING_EMBED)
        team_message = await ctx.send(file=image_to_discord(
            compose_rerolled_team(team=proposed_team_p1 if player == player1 else proposed_team_p2,
                                  re_units=changed_units),
            "team.png"),
            content=f"{player.mention} please check if you have those units",
            embed=discord.Embed().set_image(url="attachment://team.png"))
        await loading_message.delete()

        for emoji in TEAM_REROLL_EMOJIS:
            await team_message.add_reaction(emoji)

        def check_reroll(reaction, user):
            return str(reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"] and reaction.message == team_message \
                   and user == player

        try:
            reaction, user = await BOT.wait_for("reaction_add", check=check_reroll, timeout=5)
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
                proposed_team_p1[c_index] = create_random_unit(races=attr["race"], grades=attr["grade"],
                                                               types=attr["type"],
                                                               events=attr["event"],
                                                               affections=attr["affection"])
                replace_duplicates(attr, proposed_team_p1)
            else:
                changed_units[c_index].append(proposed_team_p2[c_index])
                proposed_team_p2[c_index] = create_random_unit(races=attr["race"], grades=attr["grade"],
                                                               types=attr["type"],
                                                               events=attr["event"],
                                                               affections=attr["affection"])
                replace_duplicates(attr, proposed_team_p2)

            await send(player=user, last_message=team_message)
        except asyncio.TimeoutError:
            if player in pvp_time_check:
                pvp_time_check.remove(player)
            await team_message.delete()

    await send(player1)

    changed_units = {0: [], 1: [], 2: [], 3: []}

    await send(enemy)

    await ctx.send(file=image_to_discord(compose_pvp(player1=player1, player2=enemy,
                                                     team1=proposed_team_p1,
                                                     team2=proposed_team_p2),
                                         "pvp.png"))


# ..team
@BOT.command()
async def team(ctx, *, args: str = ""):
    attr = lookup_possible_units(args)
    try:
        proposed_team = [
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"]),
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"]),
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"]),
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"]),
        ]

        try:
            replace_duplicates(attr=attr, team=proposed_team)
        except ValueError as e:
            return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                                  embed=TEAM_LOOKUP_ERROR_EMBED)

        if ctx.message.author in team_time_check:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=TEAM_COOLDOWN_ERROR_EMBED)

        changed_units = {
            0: [],
            1: [],
            2: [],
            3: []
        }

        async def send_message(last_team_message=None):
            if last_team_message is not None:
                await last_team_message.delete()

            if ctx.message.author not in team_time_check:
                team_time_check.append(ctx.message.author)
            loading_message = await ctx.send(embed=LOADING_EMBED)
            team_message = await ctx.send(file=image_to_discord(compose_rerolled_team(
                team=proposed_team, re_units=changed_units
            ),
                "units.png"),
                content=f"{ctx.message.author.mention} this is your team",
                embed=discord.Embed().set_image(url="attachment://units.png"))
            await loading_message.delete()
            for emoji in TEAM_REROLL_EMOJIS:
                await team_message.add_reaction(emoji)

            def check_reroll(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) in TEAM_REROLL_EMOJIS \
                       and reaction.message == team_message

            try:
                reaction, user = await BOT.wait_for("reaction_add", check=check_reroll, timeout=5)
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
                proposed_team[c_index] = create_random_unit(races=attr["race"], grades=attr["grade"],
                                                            types=attr["type"],
                                                            events=attr["event"], affections=attr["affection"])

                replace_duplicates(attr=attr, team=proposed_team)
                await send_message(last_team_message=team_message)
            except asyncio.TimeoutError:
                if ctx.message.author in team_time_check:
                    team_time_check.remove(ctx.message.author)
                await team_message.clear_reactions()

        await send_message()
    except LookupError:
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=TEAM_LOOKUP_ERROR_EMBED)


# ..multi
@BOT.command()
async def multi(ctx, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author

    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )

    draw = await ctx.send(embed=LOADING_EMBED.set_image(url=LOADING_IMAGE_URL))

    img = compose_multi_draw(banner=banner, user=person) if banner.banner_type == BannerType.ELEVEN \
        else compose_five_multi_draw(banner=banner, user=person)
    await ctx.send(file=image_to_discord(img, "units.png"),
                   content=f"{person.mention} this is your multi" if person is ctx.message.author
                   else f"{person.mention} this is your multi coming from {ctx.message.author.mention}",
                   embed=discord.Embed(title=f"{banner.pretty_name} "
                                             f"({11 if banner.banner_type == BannerType.ELEVEN else 5}x summon)")
                   .set_image(url="attachment://units.png"))
    return await draw.delete()


# ..summon
@BOT.command()
async def summon(ctx):
    draw = await ctx.send(embed=LOADING_EMBED)
    await build_menu(ctx, prev_message=draw)


async def build_menu(ctx, prev_message, page: int = 0):
    summon_menu_emojis = ["⬅️", "1️⃣", "🔟" if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else "5️⃣", "🐋",
                          "➡️"]
    await prev_message.clear_reactions()
    draw = prev_message

    await draw.edit(content=f"{ctx.message.author.mention}",
                    embed=discord.Embed(
                        title=ALL_BANNERS[page].pretty_name
                    ).set_image(url=ALL_BANNERS[page].background))

    if page == 0:
        await asyncio.gather(
            draw.add_reaction(summon_menu_emojis[1]),
            draw.add_reaction(summon_menu_emojis[2]),
            draw.add_reaction(summon_menu_emojis[3]),
            draw.add_reaction(summon_menu_emojis[4]),
        )
    elif page == len(ALL_BANNERS) - 1:
        await asyncio.gather(
            draw.add_reaction(summon_menu_emojis[0]),
            draw.add_reaction(summon_menu_emojis[1]),
            draw.add_reaction(summon_menu_emojis[2]),
            draw.add_reaction(summon_menu_emojis[3]),
        )
    else:
        await asyncio.gather(
            draw.add_reaction(summon_menu_emojis[0]),
            draw.add_reaction(summon_menu_emojis[1]),
            draw.add_reaction(summon_menu_emojis[2]),
            draw.add_reaction(summon_menu_emojis[3]),
            draw.add_reaction(summon_menu_emojis[4])
        )

    try:
        def check_banner(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in summon_menu_emojis

        reaction, user = await BOT.wait_for("reaction_add", check=check_banner)

        if "➡️" in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page + 1)
        elif "⬅️" in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page - 1)
        elif ("🔟" if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else "5️⃣") in str(reaction.emoji):
            await draw.delete()
            await multi(ctx, person=ctx.message.author, banner_name=ALL_BANNERS[page].name[0])
        elif "1️⃣" in str(reaction.emoji):
            await draw.delete()
            await single(ctx, person=ctx.message.author, banner_name=ALL_BANNERS[page].name[0])
        elif "🐋" in str(reaction.emoji):
            await draw.delete()
            await shaft(ctx, person=ctx.message.author, banner_name=ALL_BANNERS[page].name[0])
    except asyncio.TimeoutError:
        pass


# ..single
@BOT.command()
async def single(ctx, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author
    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"))

    return await ctx.send(file=compose_draw(banner, person),
                          content=f"{person.mention} this is your single" if person is ctx.message.author
                          else f"{person.mention} this is your single coming from {ctx.message.author.mention}",
                          embed=discord.Embed(title=f"{banner.pretty_name} (1x summon)").set_image(
                              url="attachment://unit.png"))


# ..shaft
@BOT.command()
async def shaft(ctx, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author

    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"))
    for bN in banner.name:
        if "gssr" in bN:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                      description=f"Can't get shafted on the \"{banner.pretty_name}\" banner"))

    i = 0
    draw = await ctx.send(content=f"{person.mention} this is your shaft" if person is ctx.message.author
    else f"{person.mention} this is your shaft coming from {ctx.message.author.mention}",
                          embed=discord.Embed(title="Shafting...").set_image(
                              url=LOADING_IMAGE_URL))

    rang = 11 if banner.banner_type == BannerType.ELEVEN else 5
    drawn_units = [unit_with_chance(banner, person) for _ in range(rang)]

    def has_ssr(du: List[Unit]) -> bool:
        for u in du:
            if u.grade == Grade.SSR:
                return True
        return False

    while not has_ssr(drawn_units) and i < 100000:
        i += 1
        drawn_units = [unit_with_chance(banner, person) for _ in range(rang)]

    await ctx.send(
        file=image_to_discord(
            compose_unit_multi_draw(units=drawn_units) if banner.banner_type == BannerType.ELEVEN
            else compose_unit_five_multi_draw(units=drawn_units),
            "units.png"),
        content=f"{person.mention}" if person is ctx.message.author
        else f"{person.mention} coming from {ctx.message.author.mention}",
        embed=discord.Embed(
            title=f"{banner.pretty_name} ({rang}x summon)",
            description=f"Shafted {i} times \n This is your final pull").set_image(
            url="attachment://units.png"))
    await draw.delete()
    add_shaft(person, i)


# ..create
@BOT.command()
async def create(ctx, name="", attribute="red", grade="ssr", file_url="", race="", affection=""):
    if file_url == "" or name == "":
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=UNIT_CREATE_COMMAND_USAGE_ERROR_EMBED)
    with BytesIO(requests.get(file_url).content) as url:
        atr = map_attribute(attribute)
        grd = map_grade(grade)
        rac = map_race(race)
        affection = map_affection(affection)
        icon = compose_icon(attribute=atr, grade=grd, background=Image.open(url))
        await ctx.send(
            file=image_to_discord(img=icon, image_name="unit.png"),
            content=f"{ctx.message.author.mention} this is your created unit",
            embed=discord.Embed(
                title=name,
                color=discord.Color.red() if atr == Type.RED
                else discord.Color.blue() if atr == Type.BLUE
                else discord.Color.green()
            ).set_image(url="attachment://unit.png"))
        save_custom_units(icon=icon, attribute=atr, grade=grd, name=name, race=rac, affection=affection)


# ..crop
@BOT.command()
async def crop(ctx, file_url=None, starting_width=0, starting_height=0, ending_width=75, ending_height=75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=CROP_COMMAND_USAGE_ERROR_EMBED)
    with BytesIO(requests.get(file_url).content) as url:
        img = Image.open(url)
        await ctx.send(content=f"{ctx.message.author.mention} this is your cropped image",
                       file=image_to_discord(img.crop((starting_width, starting_height, ending_width, ending_height)),
                                             "cropped.png"),
                       embed=discord.Embed().set_image(url="attachment://cropped.png"))


# ..resize
@BOT.command()
async def resize(ctx, file_url=None, width=75, height=75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=RESIZE_COMMAND_USAGE_ERROR_EMBED)
    with BytesIO(requests.get(file_url).content) as url:
        img = Image.open(url)
        await ctx.send(content=f"{ctx.message.author.mention} this is your resized image",
                       file=image_to_discord(img.resize((width, height)), "resized.png"),
                       embed=discord.Embed().set_image(url="attachment://resized.png"))


def unit_with_chance(banner: Banner, user: discord.Member) -> Unit:
    draw_chance = round(ra.uniform(0, 100), 4)

    if banner.ssr_chance >= draw_chance or len(banner.sr_units) == 0:
        u = banner.ssr_units[ra.randint(0, len(banner.ssr_units) - 1)]
    elif banner.ssr_rate_up_chance >= draw_chance and len(banner.rate_up_units) != 0:
        u = banner.rate_up_units[ra.randint(0, len(banner.rate_up_units) - 1)]
    elif banner.sr_chance >= draw_chance or len(banner.r_units) == 0:
        u = banner.sr_units[ra.randint(0, len(banner.sr_units) - 1)]
    else:
        u = banner.r_units[ra.randint(0, len(banner.r_units) - 1)]

    if user is not None:
        add_user_pull(user, u.grade == Grade.SSR)
    return u


def get_text_dimensions(text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height


def compose_rerolled_team(team: List[Unit], re_units) -> Image:
    if re_units[0] == 0 and re_units[1] == 0 and re_units[2] == 0 and re_units[3] == 0:
        icons = list(map(lambda x: x.resize([IMG_SIZE, IMG_SIZE]), [i for i in list(map(lambda x: x.icon, team))]))
        img = Image.new('RGBA', ((IMG_SIZE * 4) + 6, IMG_SIZE))
        x_offset = 0
        for icon in icons:
            img.paste(icon, (x_offset, 0))
            x_offset += icon.size[0] + 2

        return img

    icons = list(map(lambda x: x.resize([IMG_SIZE, IMG_SIZE]), [i for i in list(map(lambda x: x.icon, team))]))
    font = ImageFont.truetype("pvp.ttf", 12)
    dummy_height = get_text_dimensions("[Dummy] Bot", font)[1]
    all_re_units_len = 0
    for i in re_units:
        all_re_units_len += len(re_units[i])
    img = Image.new('RGBA', ((IMG_SIZE * 4) + 6,
                             IMG_SIZE + ((5 + dummy_height) * all_re_units_len)
                             ))
    img_draw = ImageDraw.Draw(img)
    x_offset = 0
    for icon in icons:
        img.paste(icon, (x_offset, img.size[1] - IMG_SIZE))
        x_offset += icon.size[0] + 2

    pointer = 0
    for re_unit_index in re_units:
        for i in range(len(re_units[re_unit_index])):
            img_draw.text(((IMG_SIZE * re_unit_index) + (re_unit_index * 2),
                           (5 + dummy_height) * pointer
                           ),
                          re_units[re_unit_index][i].name,
                          (255, 255, 255), font=font)
            pointer += 1

    return img


def compose_pvp_with_images(player1: discord.Member, team1_img: Image, player2: discord.Member,
                            team2_img: Image) -> Image:
    font = ImageFont.truetype("pvp.ttf", 30)
    font_dim = get_text_dimensions("vs", font)
    pvp_img = Image.new('RGBA', (team1_img.size[0] + 5 + font_dim[0] + 5 + team2_img.size[0],
                                 IMG_SIZE + font_dim[1] + 5))
    pvp_img_draw = ImageDraw.Draw(pvp_img)

    pvp_img.paste(team1_img, (0, font_dim[1] + 5))

    pvp_img_draw.text((pvp_img.size[0] / 2 - (font_dim[0] / 2), (IMG_SIZE / 2) + 20), "vs", (255, 255, 255),
                      font=font)

    pvp_img.paste(team2_img, (pvp_img.size[0] - team2_img.size[0], font_dim[1] + 5))

    pvp_img_draw.text((0, 0), f"{player1.display_name}", (255, 255, 255), font=font)
    pvp_img_draw.text((pvp_img.size[0] - get_text_dimensions(f"{player2.display_name}", font)[0], 0),
                      f"{player2.display_name}", (255, 255, 255), font=font)

    return pvp_img


def compose_pvp(player1: discord.Member, team1: List[Unit], player2: discord.Member, team2: List[Unit]) -> Image:
    left_icons = list(map(lambda x: x.resize((IMG_SIZE, IMG_SIZE)), [i for i in list(map(lambda x: x.icon, team1))]))
    right_icons = list(map(lambda x: x.resize((IMG_SIZE, IMG_SIZE)), [i for i in list(map(lambda x: x.icon, team2))]))
    right_team_img = Image.new('RGBA', (IMG_SIZE * 4 + 4, IMG_SIZE))
    left_team_img = Image.new('RGBA', (IMG_SIZE * 4 + 4, IMG_SIZE))

    x_offset = 0
    for icon in left_icons:
        left_team_img.paste(icon, (x_offset, 0))
        x_offset += icon.size[0] + 2

    x_offset = 0
    for icon in right_icons:
        right_team_img.paste(icon, (x_offset, 0))
        x_offset += icon.size[0] + 2

    return compose_pvp_with_images(player1=player1, team1_img=left_team_img, player2=player2, team2_img=right_team_img)


def compose_draw(banner: Banner, user: discord.Member) -> discord.File:
    f = unit_with_chance(banner, user).discord_icon()
    return f


def compose_five_multi_draw(banner: Banner, user: discord.Member) -> Image:
    i = compose_unit_five_multi_draw([unit_with_chance(banner, user) for _ in range(5)])
    return i


def compose_multi_draw(banner: Banner, user: discord.Member) -> Image:
    i = compose_unit_multi_draw([unit_with_chance(banner, user) for _ in range(11)])
    return i


def compose_unit_five_multi_draw(units: List[Unit]) -> Image:
    image_row_1 = [units[0].icon, units[1].icon, units[2].icon]
    image_row_2 = [units[3].icon, units[4].icon]

    complete_offset = 5
    i = Image.new('RGBA', ((IMG_SIZE * 3) + 10, (IMG_SIZE * 2) + 5))

    x_offset = 0
    for icon in image_row_1:
        i.paste(icon, (x_offset, 0))
        x_offset += icon.size[0] + complete_offset

    x_offset = int((((IMG_SIZE * 3) + 10) - IMG_SIZE * 2) / 2)
    for icon in image_row_2:
        i.paste(icon, (x_offset, icon.size[1] + complete_offset))
        x_offset += icon.size[0] + complete_offset

    return i


def compose_unit_multi_draw(units: List[Unit]) -> Image:
    image_row_1 = [units[0].icon, units[1].icon, units[2].icon, units[3].icon]
    image_row_2 = [units[4].icon, units[5].icon, units[6].icon, units[7].icon]
    image_row_3 = [units[8].icon, units[9].icon, units[10].icon]

    complete_offset = 5

    i = Image.new('RGBA', ((IMG_SIZE * 4) + (complete_offset * 3), (IMG_SIZE * 3) + (complete_offset * 2)))
    y_offset = 0
    for icons in [image_row_1, image_row_2, image_row_3]:
        x_offset = 0
        for icon in icons:
            i.paste(icon, (x_offset, y_offset))
            x_offset += icon.size[0] + complete_offset
        y_offset += icon.size[1] + complete_offset

    return i


def compose_icon(attribute: Type, grade: Grade, background: Image = None) -> Image:
    background_frame = FRAME_BACKGROUNDS[grade].copy()
    if background is None:
        background = background_frame
    else:
        background = background.resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    frame = FRAMES[attribute][grade]
    background_frame.paste(background, (0, 0), background)
    background_frame.paste(frame, (0, 0), frame)

    return background_frame


def compose_unit_list(cus_units: List[Unit]) -> Image:
    font = ImageFont.truetype("pvp.ttf", 24)
    text_dim = get_text_dimensions(sorted(cus_units, key=lambda k: len(k.name), reverse=True)[0].name, font=font)
    i = Image.new('RGBA', (IMG_SIZE + text_dim[0] + 5, (IMG_SIZE * len(cus_units)) + (5 * len(cus_units))))
    draw = ImageDraw.Draw(i)

    offset = 0
    for cus_unit in cus_units:
        i.paste(cus_unit.icon, (0, offset))
        draw.text((5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)), cus_unit.name, (255, 255, 255),
                  font=font)
        offset += IMG_SIZE + 5

    return i


@BOT.command()
async def unitlist(ctx, *, criteria: str = "event: custom"):
    attr = lookup_possible_units(criteria)
    await ctx.send(file=image_to_discord(compose_unit_list(
        get_matching_units(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"])),
                                         "units.png"),
                   embed=discord.Embed().set_image(url="attachment://units.png"))


@BOT.command()
async def banner(ctx, *, banner_name: str = "banner one"):
    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )

    await ctx.send(file=image_to_discord(compose_unit_list(banner.ssr_units + banner.rate_up_units), "units.png"),
                   embed=discord.Embed(title=f"SSRs in {banner.pretty_name}").set_image(url="attachment://units.png"))


def read_custom_units_from_db():
    CONN.commit()
    for row in CURSOR.execute('SELECT * FROM custom_units'):
        u = Unit(unit_id=row[0],
                 name=row[1],
                 simple_name="custom",
                 type=map_attribute(row[2]),
                 grade=map_grade(row[3]),
                 race=map_race(row[4]),
                 affection=map_affection(row[5]),
                 event=Event.CUS)
        UNITS.append(u)


def add_custom_units_to_banner():
    cus_units = list(filter(lambda x: x.event == Event.CUS, UNITS))
    if banner_by_name("custom") is not None:
        ALL_BANNERS.remove(banner_by_name("custom"))
    ALL_BANNERS.append(
        Banner(name=["customs", "custom"],
               pretty_name="Custom Created Units",
               units=cus_units,
               ssr_unit_rate=(3 / len(cus_units)) if len(cus_units) > 0 else -1,
               sr_unit_rate=1.2414,
               includes_all_r=False,
               includes_all_sr=False,
               bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/A9619A31-B793-4E12-8DF6-D0FCC706DEF2_1_105_c.jpeg")
    )


def save_custom_units(attribute: Type, grade: Grade, icon: Image, name: str,
                      race: Race = Race.UNKNOWN,
                      affection: Affection = Affection.NONE):
    custom_units = list(filter(lambda x: x.event == Event.CUS, UNITS))
    icon.save(f"gc/icons/{-1 * len(custom_units)}.png", "PNG")
    u = Unit(unit_id=-1 * len(custom_units),
             name=name,
             type=attribute,
             grade=grade,
             race=race,
             event=Event.CUS,
             affection=affection,
             simple_name="custom")

    UNITS.append(u)
    add_custom_units_to_banner()

    i = (u.unit_id, u.name, u.type.value, u.grade.value, u.race.value, u.affection.value)
    CURSOR.execute('INSERT INTO custom_units VALUES (?, ?, ?, ?, ?, ?)', i)
    CONN.commit()


if __name__ == '__main__':
    try:
        BOT.run(TOKEN)
    finally:
        CONN.close()
