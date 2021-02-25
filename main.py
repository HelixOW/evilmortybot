import asyncio
import random as ra
import sqlite3 as sql
import typing
from enum import Enum
from io import BytesIO
from typing import List

import aiohttp
import discord
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from discord.ext import commands
from discord.ext.commands import HelpCommand

# Version 1.0
# TODO:
#   - maybe web interface for new units?
#   - jp units
#   - daily currency for box pulls
#   - no case sensitive unit lookup


with open("data/bot_token.txt", 'r') as file:
    TOKEN = file.read()
IMG_SIZE = 150
LOADING_IMAGE_URL = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
CONN = sql.connect('data/data.db')
CURSOR = CONN.cursor()


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


class CustomHelp(HelpCommand):
    async def send_bot_help(self, mapping):
        await self.get_destination().send(embed=HELP_EMBED_1)
        await self.get_destination().send(embed=HELP_EMBED_2)


HELP_EMBED_1 = discord.Embed(
    title="Help 1/2",
    description="""
                __*Commands:*__
                    `..unit` -> `Check Info`
                    `..unitlist` -> `Check Info`
                    `..team` -> `Check Info`
                    `..pvp <@Enemy>` -> `Check Info`
                    `..single [@For] [banner=banner 1]` 
                    `..multi [@For] [banner=banner 1]`
                    `..shaft [@For] [unit="Unit name"] [banner=banner 1]`
                    `..summon [banner=banner 1]`
                    `..banner [banner=banner 1]`
                    `..stats <luck, ssrs, units, shafts>`
                    `..top <luck, ssrs, units, shafts>`
                    `..box [@Of]`
                    `..find <unit name>`
                    `..custom` -> `Execute for more Info`

                    __*Info:*__
                    You can use different attributes to narrow down the possibilities:
                     `race:` demons, giants, humans, fairies, goddess, unknown
                     `type:` blue, red, green
                     `grade:` r, sr, ssr
                     `event:` gc, slime, aot, kof, new year, halloween, festival, valentine
                     `affection:` sins, commandments, holy knights, catastrophes, archangels, none
                     `name:` name1, name2, name3, ..., nameN

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
                            `..custom create name:[Demon Slayer] Tanjiro & type: red & grade; sr & url: <URL to image> & race: human` ~ Creates a Red SR Tanjiro
                            """,
    colour=discord.Color.gold(),
).set_footer(text="Ping `Helix Sama#0001` for additional help!")
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

AFFECTION_UNMUTABLE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                description="This Affection can not be added/removed!")
AFFECTION_HELP_EMBED = discord.Embed(title="Help for ..affection", colour=discord.Color.gold(),
                                     description="""
                                     `..affection <action> <name>`

                                     *__actions__*: 
                                     `add <name>`,
                                     `remove <name>`,
                                     `edit <name> name: <new name>`, 
                                     `transfer <name> owner: @<new owner>`,
                                     `list`,
                                     `help`
                                      """)
AFFECTION_ADDED_EMBED = discord.Embed(title="Success", colour=discord.Color.green(), description="Affection added!")
AFFECTION_EDITED_EMBED = discord.Embed(title="Success", colour=discord.Color.green(), description="Affection edited!")
AFFECTION_REMOVED_EMBED = discord.Embed(title="Success", colour=discord.Color.red(), description="Affection removed!")

CUSTOM_HELP_EMBED = discord.Embed(title="Help for ..custom", colour=discord.Color.gold(),
                                  description="""
                                  `..custom <action>`

                                  *__actions__*: `create, remove, edit, help`
                                  """)
CUSTOM_ADD_COMMAND_USAGE_EMBED = discord.Embed(title="Error with ..custom create", colour=discord.Color.dark_red(),
                                               description="""
                                               `..custom create name:<name> & type:<type> & grade:<grade> & url:<file_url> & race:[race] & affection:[affection]`
                                               """)
CUSTOM_EDIT_COMMAND_USAGE_EMBED = discord.Embed(title="Error with ..custom edit", colour=discord.Color.dark_red(),
                                                description="""
                                               `..custom edit name:<name> & criteria:<value1> & criteria2:<value2>`

                                               **__Criteria__**:
                                               `type: <type>`,
                                               `grade: <grade>`,
                                               `url: <image url>`,
                                               `race: <race>`,
                                               `affection: <affection>`
                                               `updated_name: <new name>`
                                               """)
CUSTOM_EDIT_COMMAND_SUCCESS_EMBED = discord.Embed(title="Success", colour=discord.Color.green(),
                                                  description="Unit successfully edited!")
CUSTOM_REMOVE_COMMAND_USAGE_EMBED = discord.Embed(title="Error with ..custom remove", colour=discord.Color.dark_red(),
                                                  description="""
                                                  `..custom remove name:<name>`
                                                  """)
CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED = discord.Embed(title="Success", colour=discord.Color.green(),
                                                    description="Unit successfully removed!")

CROP_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                               description="..crop requires at least a url of a file to crop (..help for more)")

RESIZE_COMMAND_USAGE_ERROR_EMBED = discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                 description="..resize requires at least a url of a file to crop (..help for more)")

LOADING_EMBED = discord.Embed(title="Loading...")
IMAGES_LOADED_EMBED = discord.Embed(title="Images loaded!")

TEAM_REROLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
PVP_REROLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣️"]

RACES = [Race.DEMON, Race.GIANT, Race.HUMAN, Race.FAIRY, Race.GODDESS, Race.UNKNOWN]
GRADES = [Grade.R, Grade.SR, Grade.SSR]
TYPES = [Type.RED, Type.GRE, Type.BLUE]
EVENTS = [Event.GC, Event.SLI, Event.AOT, Event.KOF, Event.FES, Event.NEY, Event.VAL, Event.HAL]
AFFECTIONS = [Affection.SIN.value, Affection.COMMANDMENTS.value, Affection.CATASTROPHE.value,
              Affection.ANGEL.value, Affection.KNIGHT.value, Affection.NONE.value]

UNITS = []
R_UNITS = []
SR_UNITS = []
CUSTOM_UNITS = []
ALL_BANNERS = []

TEAM_TIME_CHECK = []
PVP_TIME_CHECK = []

FRAMES = {
    Type.BLUE: {
        Grade.R: Image.open("gc/frames/blue_r_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SR: Image.open("gc/frames/blue_sr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SSR: Image.open("gc/frames/blue_ssr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    },
    Type.RED: {
        Grade.R: Image.open("gc/frames/red_r_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SR: Image.open("gc/frames/red_sr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SSR: Image.open("gc/frames/red_ssr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    },
    Type.GRE: {
        Grade.R: Image.open("gc/frames/green_r_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SR: Image.open("gc/frames/green_sr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SSR: Image.open("gc/frames/green_ssr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    }
}
FRAME_BACKGROUNDS = {
    Grade.R: Image.open("gc/frames/r_frame_background.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
    Grade.SR: Image.open("gc/frames/sr_frame_background.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
    Grade.SSR: Image.open("gc/frames/ssr_frame_background.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
}

BOT = commands.Bot(command_prefix='..', description='..help for Help', help_command=CustomHelp())


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
    return None


def map_grade(raw_grade: str) -> Grade:
    raw_grade = raw_grade.lower()
    if raw_grade == "r":
        return Grade.R
    elif raw_grade == "sr":
        return Grade.SR
    elif raw_grade == "ssr":
        return Grade.SSR
    return None


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
    elif raw_race in ["unknown"]:
        return Race.UNKNOWN
    return None


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


def map_affection(raw_affection: str) -> str:
    raw_affection = strip_whitespace(raw_affection).lower()
    if raw_affection in ["sins", "sin"]:
        return Affection.SIN.value
    elif raw_affection in ["holyknight", "holyknights", "knights", "knight"]:
        return Affection.KNIGHT.value
    elif raw_affection in ["commandments", "commandment", "command"]:
        return Affection.COMMANDMENTS.value
    elif raw_affection in ["catastrophes", "catastrophes"]:
        return Affection.CATASTROPHE.value
    elif raw_affection in ["arcangels", "angels", "angel", "arcangel"]:
        return Affection.ANGEL.value
    elif raw_affection in ["none", "no"]:
        return Affection.NONE.value
    else:
        if raw_affection in AFFECTIONS:
            return raw_affection
        return Affection.NONE.value


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


async def image_to_discord(img: Image, image_name: str) -> discord.File:
    with BytesIO() as image_bin:
        img.save(image_bin, 'PNG')
        image_bin.seek(0)
        image_file = discord.File(fp=image_bin, filename=image_name)
    return image_file


async def compose_icon(attribute: Type, grade: Grade, background: Image = None) -> Image:
    background_frame = FRAME_BACKGROUNDS[grade].copy()
    if background is None:
        background = background_frame
    else:
        background = background.resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    frame = FRAMES[attribute][grade]
    background_frame.paste(background, (0, 0), background)
    background_frame.paste(frame, (0, 0), frame)

    return background_frame


class Unit:
    def __init__(self, unit_id: int,
                 name: str,
                 simple_name: str,
                 type: Type,
                 grade: Grade,
                 race: Race,
                 event: Event = Event.GC,
                 affection: str = Affection.NONE.value,
                 icon_path: str = "gc/icons/{}.png"):
        self.unit_id: int = unit_id
        self.name: str = name
        self.simple_name: str = simple_name
        self.type: Type = type
        self.grade: Grade = grade
        self.race: Race = race
        self.event: Event = event
        self.affection: str = affection
        self.icon_path: str = icon_path
        if unit_id > 0:
            img = Image.new('RGBA', (IMG_SIZE, IMG_SIZE))
            img.paste(Image.open(icon_path.format(unit_id)).resize((IMG_SIZE, IMG_SIZE)), (0, 0))
            self.icon: Image = img
        else:
            self.icon: Image = None

    async def discord_icon(self) -> discord.File:
        return await image_to_discord(self.icon, "unit.png")

    async def set_icon(self):
        if self.icon is None:
            await self.refresh_icon()

    async def refresh_icon(self):
        if self.unit_id <= 0:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.icon_path) as resp:
                    self.icon: Image = await compose_icon(attribute=self.type, grade=self.grade,
                                                          background=Image.open(BytesIO(await resp.read())))

    def discord_color(self) -> discord.Color:
        if self.type == Type.RED:
            return discord.Color.red()
        elif self.type == Type.GRE:
            return discord.Color.green()
        elif self.type == Type.BLUE:
            return discord.Color.blue()
        else:
            return discord.Color.gold()


def read_units_from_db():
    UNITS.clear()
    R_UNITS.clear()
    SR_UNITS.clear()

    for row in CURSOR.execute('SELECT * FROM units'):
        print(f"Registering Unit with id= {row[0]}")

        UNITS.append(Unit(
            unit_id=row[0],
            name=row[1],
            simple_name=row[2],
            type=map_attribute(row[3]),
            grade=map_grade(row[4]),
            race=map_race(row[5]),
            event=map_event(row[6]),
            affection=map_affection(row[7]),
            icon_path=row[8] if row[0] < 0 else "gc/icons/{}.png"
        ))

    R_UNITS.extend(list(filter(lambda x: x.grade == Grade.R and x.event == Event.GC, UNITS)))
    SR_UNITS.extend(list(filter(lambda x: x.grade == Grade.SR and x.event == Event.GC, UNITS)))


def read_affections_from_db():
    CONN.commit()
    for row in CURSOR.execute('SELECT * FROM affections'):
        print(f"Loaded {row[0]} - affection")
        AFFECTIONS.append(row[0])


# loop.run_until_complete(read_affections_from_db())
# loop.run_until_complete(read_units_from_db())


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


def unit_by_name(name: str) -> Unit:
    return next((x for x in UNITS if name == x.name), None)


def banner_by_name(name: str) -> Banner:
    return next((x for x in ALL_BANNERS if name in x.name), None)


def banners_by_name(names: List[str]) -> List[Banner]:
    found = list(filter(lambda x: not set(x.name).isdisjoint(names), ALL_BANNERS))
    if len(found) == 0:
        raise ValueError
    return found


def read_banners_from_db():
    ALL_BANNERS.clear()
    CONN.commit()
    banner_data = CURSOR.execute('SELECT * FROM banners').fetchall()
    for row in banner_data:
        banner_name_data = CURSOR.execute('SELECT alternative_name FROM banner_names WHERE name=?',
                                          (row[0],)).fetchall()
        banner_unit_data = CURSOR.execute('SELECT unit_id FROM banners_units WHERE banner_name=?', (row[0],)).fetchall()
        banner_rate_up_unit_data = CURSOR.execute('SELECT unit_id FROM banners_rate_up_units WHERE banner_name=?',
                                                  (row[0],)).fetchall()
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


async def get_user_pull(user: discord.Member) -> dict:
    data = CURSOR.execute('SELECT * FROM user_pulls WHERE user_id=? AND guild=?', (user.id, user.guild.id)).fetchone()
    if data is None:
        return {}
    return {"ssr_amount": data[1], "pull_amount": data[2], "guild": data[3], "shafts": data[4]}


async def get_top_users(guild: discord.Guild, action: LeaderboardType = LeaderboardType.LUCK) -> List[dict]:
    ret = []
    if action == LeaderboardType.MOST_SHAFTS:
        data = CURSOR.execute(
            'SELECT * FROM user_pulls WHERE guild=? AND pull_amount > 99 ORDER BY shafts DESC LIMIT 10',
            (guild.id,)).fetchall()
        if data is None:
            return {}
        for i in range(10):
            if i == len(data):
                break
            user = await BOT.fetch_user(data[i][0])
            ret.append({
                "place": i + 1,
                "name": user.display_name,
                "shafts": data[i][4]
            })
    elif action == LeaderboardType.LUCK:
        data = CURSOR.execute(
            'SELECT *, round((CAST(ssr_amount as REAL)/CAST(pull_amount as REAL)), 4) percent FROM user_pulls WHERE guild=? AND pull_amount > 99 ORDER BY percent DESC LIMIT 10',
            (guild.id,)).fetchall()
        if data is None:
            return {}
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
    elif action == LeaderboardType.MOST_SSR:
        data = CURSOR.execute(
            'SELECT * FROM user_pulls WHERE guild=? AND pull_amount > 99 ORDER BY ssr_amount DESC LIMIT 10',
            (guild.id,)).fetchall()
        if data is None:
            return {}
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
    elif action == LeaderboardType.MOST_UNITS:
        data = CURSOR.execute(
            'SELECT * FROM user_pulls WHERE guild=? and pull_amount > 99 ORDER BY pull_amount DESC LIMIT 10',
            (guild.id,)).fetchall()
        if data is None:
            return {}
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


async def add_user_pull(user: discord.Member, got_ssr: bool):
    data = await get_user_pull(user)
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


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def add_unit_to_box(user: discord.Member, unit: Unit):
    data = CURSOR.execute('SELECT amount FROM box_units WHERE user_id=? AND guild=? AND unit_id=?',
                          (user.id, user.guild.id, unit.unit_id)).fetchone()
    if data is None:
        CURSOR.execute('INSERT INTO box_units VALUES (?, ?, ?, ?)', (user.id, user.guild.id, unit.unit_id, 1))
    else:
        if data[0] < 1000:
            CURSOR.execute('UPDATE box_units SET amount=? WHERE user_id=? AND guild=? AND unit_id=?',
                           (data[0] + 1, user.id, user.guild.id, unit.unit_id))
    CONN.commit()


async def read_box(user: discord.Member) -> dict:
    box_d = {}
    for row in CURSOR.execute("""SELECT box_units.unit_id, box_units.amount
                                 FROM box_units INNER JOIN units u ON u.unit_id = box_units.unit_id
                                 WHERE user_id=? AND guild=?
                                 ORDER BY u.grade DESC, box_units.amount DESC;""",
                              (user.id, user.guild.id)):
        box_d[row[0]] = row[1]
    return box_d


async def add_shaft(user: discord.Member, amount: int):
    data = await get_user_pull(user)
    if len(data) != 0:
        CURSOR.execute('UPDATE user_pulls SET shafts=? WHERE user_id=? AND guild=?',
                       (data["shafts"] + amount, user.id, user.guild.id))
    else:
        CURSOR.execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                       (user.id, 0, 0, user.guild.id, amount))


def get_matching_units(grades: List[Grade] = None,
                       types: List[Type] = None,
                       races: List[Race] = None,
                       events: List[Event] = None,
                       affections: List[str] = None,
                       names: List[str] = None) -> List[Unit]:
    if races is None or races == []:
        races = RACES.copy()
    if grades is None or grades == []:
        grades = GRADES.copy()
    if types is None or types == []:
        types = TYPES.copy()
    if events is None or events == []:
        events = EVENTS.copy()
    if affections is None or affections == []:
        affections = list(map(lambda x: strip_whitespace(x.lower()), AFFECTIONS))
    if names is None or names == []:
        names = list(map(lambda x: strip_whitespace(x.name.lower()), UNITS))

    def test(x):
        return x.race in races and x.type in types and x.grade in grades and x.event in events and strip_whitespace(
            x.affection.lower()) in affections and strip_whitespace(x.name.lower()) in names

    possible_units = list(filter(test, UNITS))

    if len(possible_units) == 0:
        raise LookupError

    return possible_units


def create_random_unit(grades: List[Grade] = None,
                       types: List[Type] = None,
                       races: List[Race] = None,
                       events: List[Event] = None,
                       affections: List[str] = None,
                       names: List[str] = None) -> Unit:
    possible_units = get_matching_units(grades=grades,
                                        types=types,
                                        races=races,
                                        events=events,
                                        affections=affections,
                                        names=names)
    return possible_units[ra.randint(0, len(possible_units) - 1)]


def lookup_possible_units(arg: str):
    args = strip_whitespace(arg.lower()).split("&")
    race = []
    name = []
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
        if args[i].startswith("name:"):
            name_str = args[i].replace("name:", "").replace(", ", ",")

            if name_str.startswith(" "):
                name_str = name_str[1:]

            name = name_str.split(",")
        elif args[i].startswith("race:"):
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
        "name": name,
        "race": race,
        "max race count": races,
        "grade": grade,
        "type": attribute,
        "event": event,
        "affection": affection
    }


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
                                            events=attr["event"], affections=attr["affection"],
                                            names=attr["name"])
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
                                            events=attr["event"], affections=attr["affection"],
                                            names=attr["name"])
            return False

    for i in range(len(team)):
        for b in range(500):
            if check_names(i) and check_races(i):
                break

        if team_simple_names[i] == "":
            raise ValueError("Not enough Units available")


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


def lookup_custom_units(arg: str):
    args = arg.split("&")
    name = ""
    updated_name = ""
    owner = 0
    race = ""
    grade = ""
    attribute = ""
    affection = ""
    url = ""

    for i in range(len(args)):
        if args[i].startswith("updated_name:"):
            updated_name = args[i].replace("updated_name:", "")

            while updated_name.endswith(" "):
                updated_name = updated_name[:-1]

            while updated_name.startswith(" "):
                updated_name = updated_name[1:]

        elif args[i].startswith("owner:"):
            owner = strip_whitespace(args[i]).lower().replace("owner:", "")[3:-1]

        elif args[i].startswith("name:"):
            name = args[i].replace("name:", "")

            while name.startswith(" "):
                name = name[1:]

            while name.endswith(" "):
                name = name[:-1]

        elif strip_whitespace(args[i]).startswith("url:"):
            url = strip_whitespace(args[i]).replace("url:", "")

        elif strip_whitespace(args[i]).lower().startswith("race:"):
            race = strip_whitespace(args[i]).lower().replace("race:", "")

        elif strip_whitespace(args[i]).lower().startswith("grade:"):
            grade = strip_whitespace(args[i]).lower().replace("grade:", "")

        elif strip_whitespace(args[i]).lower().startswith("attribute:") or strip_whitespace(args[i]).lower().startswith(
                "type:"):
            attribute = strip_whitespace(args[i]).lower().replace("attribute:", "").replace("type:", "")

        elif strip_whitespace(args[i]).lower().startswith("affection:"):
            affection = strip_whitespace(args[i]).lower().replace("affection:", "")

    race = map_race(race)
    grade = map_grade(grade)
    attribute = map_attribute(attribute)
    affection = map_affection(affection)
    owner = int(owner)

    return {
        "name": name,
        "updated_name": updated_name,
        "owner": owner,
        "url": url,
        "race": race,
        "grade": grade,
        "type": attribute,
        "affection": affection
    }


async def unit_with_chance(banner: Banner, user: discord.Member) -> Unit:
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
        await add_user_pull(user, u.grade == Grade.SSR)
        await add_unit_to_box(user, u)
    await u.set_icon()
    return u


def get_text_dimensions(text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height


async def compose_rerolled_team(team: List[Unit], re_units) -> Image:
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


async def compose_pvp_with_images(player1: discord.Member, team1_img: Image, player2: discord.Member,
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


async def compose_pvp(player1: discord.Member, team1: List[Unit], player2: discord.Member, team2: List[Unit]) -> Image:
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

    return await compose_pvp_with_images(player1=player1, team1_img=left_team_img, player2=player2,
                                         team2_img=right_team_img)


async def compose_draw(banner: Banner, user: discord.Member) -> discord.File:
    f = await (await unit_with_chance(banner, user)).discord_icon()
    CONN.commit()
    return f


async def compose_five_multi_draw(banner: Banner, user: discord.Member) -> Image:
    i = await compose_unit_five_multi_draw([(await unit_with_chance(banner, user)) for _ in range(5)])
    CONN.commit()
    return i


async def compose_multi_draw(banner: Banner, user: discord.Member) -> Image:
    i = await compose_unit_multi_draw([(await unit_with_chance(banner, user)) for _ in range(11)])
    CONN.commit()
    return i


async def compose_unit_five_multi_draw(units: List[Unit]) -> Image:
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


async def compose_unit_multi_draw(units: List[Unit]) -> Image:
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


async def compose_box(units_dict: dict) -> Image:
    # id: amount
    box_rows = list(chunks(list(units_dict.keys()), 5))
    font = ImageFont.truetype("pvp.ttf", 24)

    i = Image.new('RGBA', (
        (IMG_SIZE * 5) + (4 * 5),
        (IMG_SIZE * len(box_rows)) + (5 * (len(box_rows) - 1))
    ))
    draw = ImageDraw.Draw(i)

    y_offset = 0
    for unit_ids in box_rows:
        x_offset = 0
        for unit_id in unit_ids:
            unit = unit_by_id(unit_id)
            await unit.set_icon()
            i.paste(unit.icon, (x_offset, y_offset))
            draw.text((x_offset + 6, y_offset + 10), str(units_dict[unit_id]), (0, 0, 0),
                      font=font)
            draw.text((x_offset + 5, y_offset + 11), str(units_dict[unit_id]), (0, 0, 0),
                      font=font)
            draw.text((x_offset + 6, y_offset + 11), str(units_dict[unit_id]), (0, 0, 0),
                      font=font)
            draw.text((x_offset + 5, y_offset + 10), str(units_dict[unit_id]), (255, 255, 255),
                      font=font)
            x_offset += IMG_SIZE + 5
        y_offset += IMG_SIZE + 5

    return i


async def compose_unit_list(cus_units: List[Unit]) -> Image:
    font = ImageFont.truetype("pvp.ttf", 24)
    text_dim = get_text_dimensions(sorted(cus_units, key=lambda k: len(k.name), reverse=True)[0].name, font=font)
    i = Image.new('RGBA', (IMG_SIZE + text_dim[0] + 5, (IMG_SIZE * len(cus_units)) + (5 * len(cus_units))))
    draw = ImageDraw.Draw(i)

    offset = 0
    for cus_unit in cus_units:
        await cus_unit.set_icon()
        i.paste(cus_unit.icon, (0, offset))
        draw.text((5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)), cus_unit.name, (255, 255, 255),
                  font=font)
        offset += IMG_SIZE + 5

    return i


async def compose_banner_list(b: Banner, include_all: bool = False) -> Image:
    font = ImageFont.truetype("pvp.ttf", 24)
    if len(b.ssr_units + b.rate_up_units) == 0:
        return Image.new('RGBA', (0, 0))
    text_dim = get_text_dimensions(
        sorted(b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else []),
               key=lambda k: len(k.name), reverse=True)[0].name + " - 0.9999%",
        font=font)
    i = Image.new('RGBA', (IMG_SIZE + text_dim[0] + 5,
                           (IMG_SIZE * len(
                               b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else [])))
                           + (5 * len(
                               b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else [])))))
    draw = ImageDraw.Draw(i)

    offset = 0
    for rated_unit in b.rate_up_units:
        await rated_unit.set_icon()
        i.paste(rated_unit.icon, (0, offset))
        draw.text((5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
                  f"{rated_unit.name} - {b.ssr_unit_rate_up}%", (255, 255, 255),
                  font=font)
        offset += IMG_SIZE + 5
    for cus_unit in b.ssr_units:
        await cus_unit.set_icon()
        i.paste(cus_unit.icon, (0, offset))
        draw.text((5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)), f"{cus_unit.name} - {b.ssr_unit_rate}%",
                  (255, 255, 255),
                  font=font)
        offset += IMG_SIZE + 5
    if include_all:
        for cus_unit in b.sr_units:
            await cus_unit.set_icon()
            i.paste(cus_unit.icon, (0, offset))
            draw.text((5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
                      f"{cus_unit.name} - {b.sr_unit_rate}%",
                      (255, 255, 255),
                      font=font)
            offset += IMG_SIZE + 5
        for cus_unit in b.r_units:
            await cus_unit.set_icon()
            i.paste(cus_unit.icon, (0, offset))
            draw.text((5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
                      f"{cus_unit.name} - {b.r_unit_rate}%",
                      (255, 255, 255),
                      font=font)
            offset += IMG_SIZE + 5

    return i


def lookup_unitlist(criteria: str):
    args = strip_whitespace(criteria.lower()).split("&")
    race = []
    name = []
    grade = []
    attribute = []
    event = []
    affection = []

    for i in range(len(args)):
        if args[i].startswith("name:"):
            name_str = args[i].replace("name:", "").replace(", ", ",")

            while name_str.startswith(" "):
                name_str = name_str[1:]

            while name_str.endswith(" "):
                name_str = name_str[:-1]

            name = name_str.split(",")
        elif args[i].startswith("race:"):
            race_str = args[i].replace("race:", "")

            if race_str.startswith("!"):
                inv_race = map_race(race_str.replace("!", "")).value
                race = list(filter(lambda x: x != inv_race, list(map(lambda x: x.value, RACES))))
            else:
                race = race_str.split(",")
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
        "name": name,
        "race": race,
        "grade": grade,
        "type": attribute,
        "event": event,
        "affection": affection
    }


def create_custom_unit_banner():
    cus_units = list(filter(lambda x: x.event == Event.CUS, UNITS))
    ssrs = list(filter(lambda x: x.grade == Grade.SSR, cus_units))
    srs = list(filter(lambda x: x.grade == Grade.SR, cus_units))
    rs = list(filter(lambda x: x.grade == Grade.R, cus_units))
    if banner_by_name("custom") is not None:
        ALL_BANNERS.remove(banner_by_name("custom"))
    ALL_BANNERS.append(
        Banner(name=["customs", "custom"],
               pretty_name="Custom Created Units",
               units=cus_units,
               ssr_unit_rate=(3 / len(ssrs)) if len(ssrs) > 0 else -1,
               sr_unit_rate=((100 - 3 - (6.6667 * len(rs))) / len(srs)) if len(srs) > 0 else -1,
               includes_all_r=False,
               includes_all_sr=False,
               bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/A9619A31-B793-4E12-8DF6-D0FCC706DEF2_1_105_c.jpeg")
    )


async def save_custom_units(name: str, creator: int, type: Type, grade: Grade, url: str, race: Race, affection: str):
    u = Unit(unit_id=-1 * len(list(filter(lambda x: x.event == Event.CUS, UNITS))),
             name=name,
             type=type,
             grade=grade,
             race=race,
             event=Event.CUS,
             affection=affection,
             simple_name=str(creator),
             icon_path=url)

    UNITS.append(u)
    create_custom_unit_banner()

    CURSOR.execute(
        'INSERT INTO units VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (u.unit_id, u.name, str(creator), type.value, grade.value, race.value, u.event.value, affection, url)
    )
    CONN.commit()


async def add_blackjack_game(user: discord.Member, won: bool):
    data = CURSOR.execute(
        'SELECT won, lost, win_streak, highest_streak, last_result FROM blackjack_record WHERE user=? AND guild=?',
        (user.id, user.guild.id)).fetchone()
    if data is None:
        CURSOR.execute('INSERT INTO blackjack_record VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (user.id, user.guild.id, 1 if won else 0, 0 if won else 1, 1 if won else 0, 1 if won else 0,
                        1 if won else 0))
    else:
        if won:
            if data[4] is 1:  # last was won
                CURSOR.execute(
                    'UPDATE blackjack_record SET won=?, win_streak=?, highest_streak=?, last_result=1 WHERE user=? AND guild=?',
                    (data[0] + 1, data[2] + 1, data[2] + 1 if data[2] + 1 > data[3] else data[3], user.id,
                     user.guild.id))
            else:  # last was lost
                CURSOR.execute(
                    'UPDATE blackjack_record SET won=?, win_streak=1, highest_streak=?, last_result=1 WHERE user=? AND guild=?',
                    (data[0] + 1, data[3] + 1 if data[2] + 1 > data[3] else data[3], user.id, user.guild.id))
        else:
            CURSOR.execute('UPDATE blackjack_record SET lost=?, win_streak=0, last_result=0 WHERE user=? AND guild=?',
                           (data[1] + 1, user.id, user.guild.id))
    CONN.commit()


@BOT.event
async def on_ready():
    await BOT.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="..help"))

    create_custom_unit_banner()

    print('Logged in as')
    print(BOT.user.name)
    print(BOT.user.id)
    print('--------')


@BOT.command(no_pm=True)
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


# ..stats
@BOT.command(no_pm=True)
async def stats(ctx, person: typing.Optional[discord.Member], *, action="luck"):
    action = map_leaderboard(action)
    if person is None:
        person = ctx.message.author
    data = await get_user_pull(person)
    ssrs = data["ssr_amount"] if len(data) != 0 else 0
    pulls = data["pull_amount"] if len(data) != 0 else 0
    shafts = data["shafts"] if len(data) != 0 else 0
    percent = round((ssrs / pulls if len(data) != 0 else 0) * 100, 2)

    if action == LeaderboardType.LUCK:
        await ctx.send(
            content=f"{person.mention}'s luck:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s luck:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently got a *{percent}%* SSR droprate in their pulls, with *{ssrs} SSRs* in *{pulls} Units*"
            )
        )
    elif action == LeaderboardType.MOST_SSR:
        await ctx.send(
            content=f"{person.mention}'s SSRs:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s SSRs:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently has *{ssrs} SSRs*"
            )
        )
    elif action == LeaderboardType.MOST_UNITS:
        await ctx.send(
            content=f"{person.mention}'s Units:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s Units:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently has *{pulls} Units*"
            )
        )
    elif action == LeaderboardType.MOST_SHAFTS:
        await ctx.send(
            content=f"{person.mention}'s Shafts:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s Shafts:",
            embed=discord.Embed(
                description=f"**{person.display_name}** currently got shafted {shafts}x"
            )
        )


# ..unit
@BOT.command(no_pm=True)
async def unit(ctx, *, args: str = ""):
    attributes = lookup_possible_units(args)
    try:
        random_unit = create_random_unit(grades=attributes["grade"],
                                         types=attributes["type"],
                                         races=attributes["race"],
                                         events=attributes["event"],
                                         affections=attributes["affection"],
                                         names=attributes["name"])
        await random_unit.set_icon()

        await ctx.send(content=f"{ctx.message.author.mention} this is your unit",
                       embed=discord.Embed(title=random_unit.name, colour=random_unit.discord_color())
                       .set_image(url="attachment://unit.png"),
                       file=random_unit.discord_icon())
    except LookupError:
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=UNIT_LOOKUP_ERROR_EMBED)


# ..pvp
@BOT.command(no_pm=True)
async def pvp(ctx, enemy: discord.Member, attr: str = ""):
    attr = lookup_possible_units(attr)
    proposed_team_p1 = [
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
    ]
    proposed_team_p2 = [
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
        create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"]),
    ]

    try:
        replace_duplicates(attr, proposed_team_p1)
        replace_duplicates(attr, proposed_team_p2)
    except ValueError as e:
        return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                              embed=TEAM_LOOKUP_ERROR_EMBED)

    player1 = ctx.message.author

    if player1 in PVP_TIME_CHECK or enemy in PVP_TIME_CHECK:
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

        if player not in PVP_TIME_CHECK:
            PVP_TIME_CHECK.append(player)

        loading_message = await ctx.send(embed=LOADING_EMBED)
        team_message = await ctx.send(file=await image_to_discord(
            await compose_rerolled_team(team=proposed_team_p1 if player == player1 else proposed_team_p2,
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
                                                               affections=attr["affection"], names=attr["name"])
                replace_duplicates(attr, proposed_team_p1)
            else:
                changed_units[c_index].append(proposed_team_p2[c_index])
                proposed_team_p2[c_index] = create_random_unit(races=attr["race"], grades=attr["grade"],
                                                               types=attr["type"],
                                                               events=attr["event"],
                                                               affections=attr["affection"], names=attr["name"])
                replace_duplicates(attr, proposed_team_p2)

            await send(player=user, last_message=team_message)
        except asyncio.TimeoutError:
            if player in PVP_TIME_CHECK:
                PVP_TIME_CHECK.remove(player)
            await team_message.delete()

    await send(player1)

    changed_units = {0: [], 1: [], 2: [], 3: []}

    await send(enemy)

    await ctx.send(file=await image_to_discord(await compose_pvp(player1=player1, player2=enemy,
                                                                 team1=proposed_team_p1,
                                                                 team2=proposed_team_p2),
                                               "pvp.png"))


# ..team
@BOT.command(no_pm=True)
async def team(ctx, *, args: str = ""):
    attr = lookup_possible_units(args)
    try:
        proposed_team = [
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"], names=attr["name"]),
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"], names=attr["name"]),
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"], names=attr["name"]),
            create_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                               affections=attr["affection"], names=attr["name"]),
        ]

        try:
            replace_duplicates(attr=attr, team=proposed_team)
        except ValueError as e:
            return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                                  embed=TEAM_LOOKUP_ERROR_EMBED)

        if ctx.message.author in TEAM_TIME_CHECK:
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

            if ctx.message.author not in TEAM_TIME_CHECK:
                TEAM_TIME_CHECK.append(ctx.message.author)
            loading_message = await ctx.send(embed=LOADING_EMBED)
            team_message = await ctx.send(file=await image_to_discord(await compose_rerolled_team(
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
                                                            events=attr["event"], affections=attr["affection"],
                                                            names=attr["name"])

                replace_duplicates(attr=attr, team=proposed_team)
                await send_message(last_team_message=team_message)
            except asyncio.TimeoutError:
                if ctx.message.author in TEAM_TIME_CHECK:
                    TEAM_TIME_CHECK.remove(ctx.message.author)
                await team_message.clear_reactions()

        await send_message()
    except LookupError:
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=TEAM_LOOKUP_ERROR_EMBED)


# ..multi
@BOT.command(no_pm=True)
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

    img = await compose_multi_draw(banner=banner, user=person) if banner.banner_type == BannerType.ELEVEN \
        else await compose_five_multi_draw(banner=banner, user=person)
    await ctx.send(file=await image_to_discord(img, "units.png"),
                   content=f"{person.mention} this is your multi" if person is ctx.message.author
                   else f"{person.mention} this is your multi coming from {ctx.message.author.mention}",
                   embed=discord.Embed(title=f"{banner.pretty_name} "
                                             f"({11 if banner.banner_type == BannerType.ELEVEN else 5}x summon)")
                   .set_image(url="attachment://units.png"))
    return await draw.delete()


# ..summon
@BOT.command(no_pm=True)
async def summon(ctx):
    draw = await ctx.send(embed=LOADING_EMBED)
    await build_menu(ctx, prev_message=draw)


# ..single
@BOT.command(no_pm=True)
async def single(ctx, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author
    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"))

    return await ctx.send(file=await compose_draw(banner, person),
                          content=f"{person.mention} this is your single" if person is ctx.message.author
                          else f"{person.mention} this is your single coming from {ctx.message.author.mention}",
                          embed=discord.Embed(title=f"{banner.pretty_name} (1x summon)").set_image(
                              url="attachment://unit.png"))


# ..shaft
@BOT.command(no_pm=True)
async def shaft(ctx, person: typing.Optional[discord.Member], unit_name: typing.Optional[str] = "none", *,
                banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author
    unit_to_draw = None if unit_name == "none" else unit_by_name(unit_name)
    if unit_to_draw is None and unit_name != "none":
        banner_name = unit_name + " " + banner_name
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
    drawn_units = [(await unit_with_chance(banner, person)) for _ in range(rang)]

    def has_ssr(du: List[Unit]) -> bool:
        for u in du:
            if u.grade == Grade.SSR:
                if unit_to_draw is None:
                    return True
                elif unit_to_draw.unit_id == u.unit_id:
                    return True
        return False

    while not has_ssr(drawn_units) and i < 5000:
        i += 1
        drawn_units = [(await unit_with_chance(banner, person)) for _ in range(rang)]

    CONN.commit()

    await ctx.send(
        file=await image_to_discord(
            await compose_unit_multi_draw(units=drawn_units) if banner.banner_type == BannerType.ELEVEN
            else await compose_unit_five_multi_draw(units=drawn_units),
            "units.png"),
        content=f"{person.mention}" if person is ctx.message.author
        else f"{person.mention} coming from {ctx.message.author.mention}",
        embed=discord.Embed(
            title=f"{banner.pretty_name} ({rang}x summon)",
            description=f"Shafted {i} times \n This is your final pull").set_image(
            url="attachment://units.png"))
    await draw.delete()
    await add_shaft(person, i)


# ..custom
@BOT.command(no_pm=True)
async def custom(ctx, action="help", *, name: typing.Optional[str] = ""):
    if action in ["help"]:
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_HELP_EMBED)
    elif action in ["add", "create", "+"]:  # provided with name, type, grade, url, race, affection
        data = lookup_custom_units(name)

        if data["url"] == "" or data["name"] == "" or data["type"] is None or data["grade"] is None:
            return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_ADD_COMMAND_USAGE_EMBED)

        async with aiohttp.ClientSession() as session:
            async with session.get(data["url"]) as resp:
                icon = await compose_icon(attribute=data["type"], grade=data["grade"],
                                          background=Image.open(BytesIO(await resp.read())))

                await ctx.send(
                    file=await image_to_discord(img=icon, image_name="unit.png"),
                    content=f"{ctx.message.author.mention} this is your created unit",
                    embed=discord.Embed(
                        title=data["name"],
                        color=discord.Color.red() if data["type"] == Type.RED
                        else discord.Color.blue() if data["type"] == Type.BLUE
                        else discord.Color.green()
                    ).set_image(url="attachment://unit.png"))

                if data["race"] is None:
                    data["race"] = Race.UNKNOWN

                if data["affection"] is None:
                    data["affection"] = Affection.NONE.value

                await save_custom_units(name=data["name"],
                                        type=data["type"],
                                        grade=data["grade"],
                                        race=data["race"],
                                        affection=data["affection"],
                                        url=data["url"],
                                        creator=ctx.message.author.id)
    elif action in ["remove", "delete", "-"]:
        data = lookup_custom_units(name)
        if data["name"] == "":
            return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_REMOVE_COMMAND_USAGE_EMBED)

        edit_unit = unit_by_name(data["name"])

        if int(edit_unit.simple_name) != ctx.message.author.id:
            return await ctx.send(content=f"{ctx.message.author.mention}", embed=discord.Embed(
                title="Error with ..custom remove", colour=discord.Color.dark_red(),
                description=f"**{edit_unit.name}** wasn't created by you!"))

        CURSOR.execute('DROP FROM custom_units WHERE name=?', (data["name"],))
        UNITS.remove(edit_unit)
        create_custom_unit_banner()
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED)
    elif action in ["list"]:
        data = lookup_custom_units(name)
        if data["owner"] == 0:
            return await unitlist(ctx, criteria="event: custom")

        unit_list = []
        for row in CURSOR.execute('SELECT unit_id FROM units WHERE simple_name=?', (data["owner"],)):
            unit_list.append(unit_by_id(-1 * row[0]))

        loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=LOADING_EMBED)
        await ctx.send(file=await image_to_discord(await compose_unit_list(unit_list), "units.png"),
                       embed=discord.Embed().set_image(url="attachment://units.png"))
        await loading.delete()

    elif action in ["edit"]:
        data = lookup_custom_units(name)
        if data["name"] == "":
            return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_EDIT_COMMAND_USAGE_EMBED)

        edit_unit = unit_by_name(data["name"])

        if int(edit_unit.simple_name) != ctx.message.author.id:
            return await ctx.send(content=f"{ctx.message.author.mention}", embed=discord.Embed(
                title="Error with ..custom remove", colour=discord.Color.dark_red(),
                description=f"**{edit_unit.name}** wasn't created by you!"))

        to_set = []
        values = []
        if data["grade"] is not None:
            edit_unit.grade = data["grade"]
            to_set.append("grade=?")
            values.append(data["grade"].value)
        if data["owner"] != 0:
            to_set.append("creator=?")
            values.append(data["owner"])
        if data["type"] is not None:
            edit_unit.type = data["type"]
            to_set.append("type=?")
            values.append(data["type"].value)
        if data["updated_name"] != "":
            edit_unit.name = data["updated_name"]
            to_set.append("name=?")
            values.append(data["updated_name"])
        if data["url"] != "":
            edit_unit.icon_path = data["url"]
            to_set.append("url=?")
            values.append(data["url"])
        if data["race"] is not None:
            edit_unit.race = data["race"]
            to_set.append("race=?")
            values.append(data["race"].value)
        if data["affection"] is not None:
            edit_unit.affection = data["affection"]
            to_set.append("affection=?")
            values.append(data["affection"])

        if len(to_set) == 0:
            return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)

        to_set = ", ".join(to_set)

        values.append(data["name"])
        CURSOR.execute("UPDATE custom_units SET " + to_set + " WHERE name=?", tuple(values))

        CONN.commit()
        await edit_unit.refresh_icon()
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)


# ..crop
@BOT.command(no_pm=True)
async def crop(ctx, file_url=None, starting_width=0, starting_height=0, ending_width=75, ending_height=75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=CROP_COMMAND_USAGE_ERROR_EMBED)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            await ctx.send(content=f"{ctx.message.author.mention} this is your cropped image",
                           file=await image_to_discord(
                               img.crop((starting_width, starting_height, ending_width, ending_height)),
                               "cropped.png"),
                           embed=discord.Embed().set_image(url="attachment://cropped.png"))


# ..resize
@BOT.command(no_pm=True)
async def resize(ctx, file_url=None, width=75, height=75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=RESIZE_COMMAND_USAGE_ERROR_EMBED)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            await ctx.send(content=f"{ctx.message.author.mention} this is your resized image",
                           file=await image_to_discord(img.resize((width, height)), "resized.png"),
                           embed=discord.Embed().set_image(url="attachment://resized.png"))


@BOT.command(no_pm=True)
async def unitlist(ctx, *, criteria: str = "event: custom"):
    attr = lookup_unitlist(criteria)
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_unit_list(
        get_matching_units(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                           affections=attr["affection"], names=attr["name"])),
                                               "units.png"),
                   embed=discord.Embed(title=f"Units matching {criteria}").set_image(url="attachment://units.png"),
                   content=f"{ctx.message.author.mention}")
    await loading.delete()


@BOT.command(no_pm=True)
async def banner(ctx, *, banner_name: str = "banner one"):
    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Banner", embed=LOADING_EMBED)
    await ctx.send(
        file=await image_to_discord(await compose_banner_list(banner, True if "custom" in banner.name else False),
                                    "banner.png"),
        embed=discord.Embed(title=f"SSRs in {banner.pretty_name} ({banner.ssr_chance}%)").set_image(
            url="attachment://banner.png"),
        content=f"{ctx.message.author.mention}")
    await loading.delete()


@BOT.command(no_pm=True)
async def add_banner_unit(ctx, banner_name: str, *, units: str):
    for u_id in list(int(x) for x in strip_whitespace(units).split(",")):
        CURSOR.execute('INSERT INTO banners_units VALUES (?, ?)', (banner_name, u_id))
    CONN.commit()


@BOT.command(no_pm=True)
async def add_banner_rate_up_unit(ctx, banner_name: str, *, units: str):
    for u_id in list(int(x) for x in strip_whitespace(units).split(",")):
        CURSOR.execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner_name, u_id))
    CONN.commit()


@BOT.command(no_pm=True)
async def update(ctx):
    read_banners_from_db()
    read_units_from_db()
    create_custom_unit_banner()
    await ctx.send(content=f"{ctx.message.author.mention} Updated Units & Banners")


@BOT.command(no_pm=True)
async def affection(ctx, action: str = "help", *, name: typing.Optional[str]):
    if name in [Affection.SIN, Affection.KNIGHT, Affection.NONE, Affection.ANGEL, Affection.CATASTROPHE,
                Affection.COMMANDMENTS]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=AFFECTION_UNMUTABLE_ERROR_EMBED)
    elif action in ["add", "create", "plus", "+"]:
        CURSOR.execute('INSERT OR IGNORE INTO affections VALUES (?, ?)', (name.lower(), ctx.message.author.id))
        AFFECTIONS.append(name.lower())
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=AFFECTION_ADDED_EMBED)
    elif action in ["edit"]:
        new_name = name.lower()
        if "new:" in name.lower():
            new_name = name.split("new:")[1]
            name = name.split("new:")[0]

            while new_name.startswith(" "):
                new_name = new_name[1:]

            while new_name.endswith(" "):
                new_name = new_name[:-1]

            while name.startswith(" "):
                name = name[:1]

            while name.endswith(" "):
                name = name[:-1]

        if name.lower() not in AFFECTIONS:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=AFFECTION_EDITED_EMBED)

        if int(CURSOR.execute('SELECT creator FROM affections where name=?', (name.lower(),)).fetchone()[
                   0]) != ctx.message.author.id:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=discord.Embed(title="Error with ..affections edit",
                                                      colour=discord.Color.dark_red(),
                                                      description=f"**{name.lower()}** is not your affection!"))

        CURSOR.execute('UPDATE affections SET name=? WHERE name=?', (new_name, name.lower()))
        AFFECTIONS.append(name.lower())
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=AFFECTION_EDITED_EMBED)
    elif action in ["move", ">", "transfer"]:
        new_owner = ctx.message.author.id
        if "owner:" in name.lower():
            new_owner = name.split("owner:")[1]
            name = name.split("owner:")[0]

            while name.endswith(" "):
                name = name[:-1]

            while new_owner.startswith(" "):
                new_owner = new_owner[1:]

            while new_owner.endswith(" "):
                new_owner = new_owner[:-1]

            new_owner = int(new_owner[3:-1])
        if name.lower() not in AFFECTIONS:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=AFFECTION_EDITED_EMBED)
        if int(CURSOR.execute('SELECT creator FROM affections where name=?', (name.lower(),)).fetchone()[
                   0]) != ctx.message.author.id:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=discord.Embed(title="Error with ..affections edit",
                                                      colour=discord.Color.dark_red(),
                                                      description=f"**{name.lower()}** is not your affection!"))

        CURSOR.execute('UPDATE affections SET creator=? WHERE name=?', (new_owner, name.lower()))
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=AFFECTION_EDITED_EMBED)
    elif action in ["remove", "delete", "minus", "-"]:
        if name.lower() not in AFFECTIONS:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=AFFECTION_REMOVED_EMBED)

        if int(CURSOR.execute('SELECT creator FROM affections where name=?', (name.lower(),)).fetchone()[
                   0]) != ctx.message.author.id:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=discord.Embed(title="Error with ..affections edit",
                                                      colour=discord.Color.dark_red(),
                                                      description=f"**{name.lower()}** is not your affection!"))
        CURSOR.execute('DELETE FROM affections WHERE name=?', (name.lower(),))
        AFFECTIONS.remove(name.lower())
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=AFFECTION_REMOVED_EMBED)
    elif action in ["list"]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="All Affections", description=",\n".join(AFFECTIONS)))
    elif action in ["help"]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=AFFECTION_HELP_EMBED)
    CONN.commit()


@BOT.command(no_pm=True)
async def box(ctx, user: typing.Optional[discord.Member]):
    if user is None:
        user = ctx.message.author
    box_d = await read_box(user)
    if len(box_d) == 0:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"{user.display_name} has no units!"))
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading {user.display_name}'s box",
                             embed=LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_box(box_d), "box.png"),
                   content=f"{ctx.message.author.mention}",
                   embed=discord.Embed(title=f"{user.display_name}'s box", colour=discord.Color.gold()).set_image(
                       url="attachment://box.png"))
    await loading.delete()


@BOT.command(no_pm=True)
async def find(ctx, *, units=""):
    if strip_whitespace(units) == "":
        return await ctx.send(content=f"{ctx.message.author.mention} -> Please provide at least 1 name `..find name1, "
                                      f"name2, ..., nameN`")
    unit_vague_name_list = units.split(",")
    found = []

    for i in range(len(unit_vague_name_list)):
        while unit_vague_name_list[i].startswith(" "):
            unit_vague_name_list[i] = unit_vague_name_list[i][1:]

        while unit_vague_name_list[i].endswith(" "):
            unit_vague_name_list[i] = unit_vague_name_list[i][:-1]

        found.extend(list(
            x for x in UNITS if strip_whitespace(unit_vague_name_list[i].lower()) in strip_whitespace(x.name.lower())))

    if len(found) == 0:
        return await ctx.send(content=f"{ctx.message.author.mention} -> No units found!")

    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_unit_list(found), "units.png"),
                   embed=discord.Embed().set_image(url="attachment://units.png"))
    await loading.delete()


@BOT.command(no_pm=True, aliases=["bj", "jack", "blackj"])
async def blackjack(ctx, action="", person: typing.Optional[discord.Member] = None):
    if action.lower() in ["top", "leaderboard"]:
        data = CURSOR.execute('SELECT user, highest_streak FROM blackjack_record ORDER BY highest_streak DESC LIMIT 10').fetchall()
        if data is None:
            return await ctx.send(content="Nobody played Blackjack yet!")

        async def map_id(x):
            return (await BOT.fetch_user(x)).display_name

        top_l = []
        i = 0
        for row in data:
            i += 1
            top_l.append(f"**{i}.** *{await map_id(row[0])}* ~ Streak of {row[1]} wins")

        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(
                                  title=f"Blackjack Leaderboard in {ctx.message.guild.name} (Highest Winning Streaks)",
                                  description=",\n".join(top_l)
                              ).set_thumbnail(url=ctx.message.guild.icon_url))
    if action.lower() in ["record", "stats"]:
        if person is None:
            person = ctx.message.author
        data = CURSOR.execute(
            'SELECT won, lost, win_streak, last_result, highest_streak FROM blackjack_record WHERE user=? AND guild=?',
            (person.id, person.guild.id)).fetchone()
        if data is None:
            return await ctx.send(
                content=f"{ctx.message.author.mention} hasn't played Blackjack yet!" if person == ctx.message.author
                else f"{ctx.message.author.mention}: {person.display_name} hasn't played Blackjack yet!")
        return await ctx.send(content=f"{ctx.message.author.mention} Blackjack History:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s Blackjack History:",
                              embed=discord.Embed(
                                  title=f"History of {person.display_name}",
                                  description=f"""
                                  **Wins**: `{data[0]}`
                                  
                                  **Lost**: `{data[1]}`
                                  
                                  **Win Streak**: `{"No" if data[3] is 0 else data[2]}`
                                  
                                  **Highest Winning Streak**: `{data[4]}`
                                  """
                              ))

    # Bot shows 2 cards for player, show 1 bot card
    bot_card_values = [ra.randint(1, 11) for _ in range(2)]
    player_card_values = [ra.randint(1, 11) for _ in range(2)]

    hit = "✅"
    stand = "🟥"

    cards_msg = await ctx.send(content=f"""
            {ctx.message.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
            Bot card is: {bot_card_values[0]}""")

    async def play(last_msg=None):
        await last_msg.clear_reactions()
        if sum(player_card_values) > 21:
            await add_blackjack_game(ctx.message.author, False)
            return await last_msg.edit(
                content=f"{ctx.message.author.mention} you lost! -> Hand of {sum(player_card_values)}")
        elif sum(player_card_values) == 21:
            await add_blackjack_game(ctx.message.author, True)
            if last_msg is None:
                return await ctx.send(content=f"{ctx.message.author.mention} you got a Blackjack and won!")
            return await last_msg.edit(content=f"{ctx.message.author.mention} you got a Blackjack and won!")

        await last_msg.edit(content=f"""
        {ctx.message.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
        Bot card is: {bot_card_values[0]}""")
        await last_msg.add_reaction(hit)
        await last_msg.add_reaction(stand)

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in [hit, stand]

        try:
            reaction, user = await BOT.wait_for('reaction_add', check=check)

            if str(reaction.emoji) == hit:
                player_card_values.append(ra.randint(1, 11))
                return await play(last_msg=cards_msg)
            elif str(reaction.emoji) == stand:
                await cards_msg.clear_reactions()
                await add_blackjack_game(ctx.message.author, 21 - sum(player_card_values) < 21 - sum(bot_card_values))
                return await last_msg.edit(
                    content=f"{ctx.message.author.mention} you won! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})" if 21 - sum(
                        player_card_values) < 21 - sum(bot_card_values)
                    else f"{ctx.message.author.mention} you lost! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})")
        except TimeoutError:
            pass

    await play(cards_msg)


if __name__ == '__main__':
    try:
        read_affections_from_db()
        read_units_from_db()
        read_banners_from_db()

        BOT.run(TOKEN)
    finally:
        CONN.close()
