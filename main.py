import asyncio
import json
import random as ra
import sqlite3 as sql
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
#   - saving unit pull data in json file -> later DB

with open("data/bot_token.txt", 'r') as file:
    TOKEN = file.read()
IMG_SIZE = 150
STORAGE_FILE_PATH = "data/custom_units.json"
LOADING_IMAGE_URL = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
CONN = sql.connect('data/data.db')
CURSOR = CONN.cursor()

HELP_EMBED_1 = discord.Embed(
    title="Help 1/2",
    description="""
                __*Commands:*__
                    `..unit`
                    `..team`
                    `..pvp <@Enemy>`
                    `..single [banner="banner one"] [times=1] [@For]`
                    `..multi [banner="banner one"] [times=1] [@For]`
                    `..shaft [banner="banner one"] [times=1] [@For]`
                    `..summon [banner="banner one"]`
                    `..create "<name>" "<simple_name>" <attribute> <grade> "<image url>" [race=unknown] [affection=none]`

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

                    __Available banners:__ banner 1, part 1, part 2, gssr part 1, gssr part 2, race 1, race 2, humans
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
                            `..single 1 "part two"` ~ does a single summon on the Part 2 banner
                            `..single 2 "part two"` ~ does a single summon on the Part 2 banner 2x
                            `..multi 1 "race two"` ~ does a 5x summon on the Demon/Fairy/Goddess banner
                            `..multi 2 "race two"` ~ does a 5x summon on the Demon/Fairy/Goddess banner 2x
                            `..multi 1 banner two` ~ does a 11x summon on the most recent banner 1x
                            `..multi 3 "banner two"` ~ does a 11x summon on the most recent banner 3x 
                            `..create "[Demon Slayer] Tanjiro" "tanjiro" red sr "URL to image" human` ~ Creates a Red SR Tanjiro
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
                                                      `..create <name> <simple_name> <attribute> <grade> <file_url>`

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


UNITS = [
    Unit(unit_id=1, name="[The Dragon Sin of Wrath] Demon Meliodas", type=Type.RED, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=2, name="[Explosion] Guila", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="guila"),
    Unit(unit_id=3, name="[Iron-wall Knight] Griamore", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="griamore"),
    Unit(unit_id=4, name="[Liones's Hero] Gowther", type=Type.BLUE, grade=Grade.SSR, race=Race.UNKNOWN,
         affection=Affection.SIN, simple_name="gowther"),
    Unit(unit_id=5, name="[Snatch] Brawler Ban", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.SIN, simple_name="ban"),
    Unit(unit_id=6, name="[Tempest] Holy Knight Howzer", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="howzer"),
    Unit(unit_id=7, name="[Godspeed Knight] Guardian Jericho", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="jericho"),
    Unit(unit_id=8, name="[The Grizzly Sin of Sloth] King the Fairy King", type=Type.BLUE, grade=Grade.SSR,
         race=Race.FAIRY,
         affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=9, name="[The Seven Deadly Sins] Captain Meliodas", type=Type.GRE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=10, name="[Matrona] Fighter Diane", type=Type.BLUE, grade=Grade.SSR, race=Race.GIANT,
         simple_name="diane"),
    Unit(unit_id=11, name="[Outlaw] Brawler Ban", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.SIN, simple_name="ban"),
    Unit(unit_id=12, name="[Protector of Dolls] Old Fart King", type=Type.GRE, grade=Grade.SSR, race=Race.FAIRY,
         affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=13, name="[Forest Guardian] Fairy Helbram", type=Type.GRE, grade=Grade.SSR, race=Race.FAIRY,
         simple_name="helbram"),
    Unit(unit_id=14, name="[Melt] Grandmaster Hendrickson", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="hendrickson"),
    Unit(unit_id=15, name="[Thunderbolt] Guardian Gilthunder", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="gilthunder"),
    Unit(unit_id=16, name="[Overpower] Hunter Slater", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="slater"),
    Unit(unit_id=17, name="[The Serpent Sin of Envy] Holy Knight Diane", type=Type.BLUE, grade=Grade.SSR,
         race=Race.GIANT,
         affection=Affection.SIN, simple_name="diane"),
    Unit(unit_id=18, name="[The Fox Sin of Greed] Adventurer Ban", type=Type.GRE, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.SIN, simple_name="ban"),
    Unit(unit_id=19, name="[Forest Guardian] King the Fairy King", type=Type.GRE, grade=Grade.SSR,
         race=Race.FAIRY, affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=20, name="[Beard of the Mountain Cat] Member Alioni", type=Type.GRE, grade=Grade.R,
         race=Race.HUMAN, simple_name="alioni"),
    Unit(unit_id=21, name="[Undead] Prisoner Ban", type=Type.RED, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.SIN, simple_name="ban"),
    Unit(unit_id=22, name="[Burning Ember] Knight of Danafor Cain", type=Type.GRE, grade=Grade.SR,
         race=Race.HUMAN, simple_name="cain"),
    Unit(unit_id=23, name="[Wanted Man] Young Villager Gowther", type=Type.GRE, grade=Grade.SR, race=Race.UNKNOWN,
         affection=Affection.SIN, simple_name="gowther"),
    Unit(unit_id=25, name="[Omen of Chaos] Grandmaster Dreyfus", type=Type.RED, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="dreyfus"),
    Unit(unit_id=27, name="[Mascot] Hawk & Elizabeth", type=Type.GRE, grade=Grade.SR, race=Race.GODDESS,
         affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=28, name="[Mobile Tavern] Hawk & Elizabeth", type=Type.RED, grade=Grade.SR, race=Race.GODDESS,
         affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=30, name="[Weird Fangs] Holy Knight Freesia", type=Type.BLUE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="freesia"),
    Unit(unit_id=31, name="[Chivalrous] Holy Knight Gilthunder", type=Type.GRE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="gilthunder"),
    Unit(unit_id=32, name="[Star of the Kingdom] Holy Knight Gilthunder", type=Type.BLUE, grade=Grade.SR,
         race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="gilthunder"),
    Unit(unit_id=33, name="[Adventurer] Ranger Griamore", type=Type.BLUE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="griamore"),
    Unit(unit_id=34, name="[The Goat Sin of Lust] Holy Knight Gowther", type=Type.RED, grade=Grade.SSR,
         race=Race.UNKNOWN, affection=Affection.SIN, simple_name="gowther"),
    Unit(unit_id=35, name="[Champion] Ranger Griamore", type=Type.RED, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="griamore"),
    Unit(unit_id=36, name="[Rapier] Holy Knight Guila", type=Type.BLUE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="guila"),
    Unit(unit_id=37, name="[Weird Fangs] Holy Knight Golgius", type=Type.BLUE, grade=Grade.R, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="golgius"),
    Unit(unit_id=38, name="[The Seven Deadly Sins] Old Fart King", type=Type.BLUE, grade=Grade.SSR,
         race=Race.FAIRY, affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=39, name="[Adventurer] Holy Knight Jericho", type=Type.RED, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="jericho"),
    Unit(unit_id=40, name="[Star of the Kingdom] Ranger Howzer", type=Type.BLUE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="howzer"),
    Unit(unit_id=41, name="[Liones Royalty] Ranger Howzer", type=Type.GRE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="howzer"),
    Unit(unit_id=42, name="[Roars of Dawn] Holy Knight Hugo", type=Type.GRE, grade=Grade.R, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="hugo"),
    Unit(unit_id=43, name="[New Generation] Holy Knight Jericho", type=Type.BLUE, grade=Grade.SR,
         race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="jericho"),
    Unit(unit_id=44, name="[Roars of Dawn] Holy Knight Jillian", type=Type.GRE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="jillian"),
    Unit(unit_id=45, name="[Weird Fangs] Holy Knight Jude", type=Type.RED, grade=Grade.R, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="jude"),
    Unit(unit_id=46, name="[Boom Boom Pow] Holy Knight Marmas", type=Type.BLUE, grade=Grade.R, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="marmas"),
    Unit(unit_id=47, name="[Boar Hat Tavern] Master Meliodas", type=Type.BLUE, grade=Grade.SR, race=Race.DEMON,
         affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=49, name="[The Boar Sin of Gluttony] Great Mage Merlin", type=Type.GRE, grade=Grade.SSR,
         race=Race.UNKNOWN, affection=Affection.SIN, simple_name="merlin"),
    Unit(unit_id=51, name="[Weird Fangs] Holy Knight Ruin", type=Type.GRE, grade=Grade.R, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="ruin"),
    Unit(unit_id=52, name="[Roars of Dawn] Holy Knight Simon", type=Type.RED, grade=Grade.R, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="simon"),
    Unit(unit_id=53, name="[Roars of Dawn] Captain Slater", type=Type.RED, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="slater"),
    Unit(unit_id=54, name="[Confirmation] Apprentice Holy Knight Twigo", type=Type.RED, grade=Grade.R,
         race=Race.HUMAN, simple_name="twigo"),
    Unit(unit_id=55, name="[Vaizel Fight Festival] Champion Taizoo", type=Type.RED, grade=Grade.R,
         race=Race.HUMAN, simple_name="taizoo"),
    Unit(unit_id=57, name="[Roars of Dawn] Holy Knight Weinheidt", type=Type.BLUE, grade=Grade.SR,
         race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="weinheidt"),
    Unit(unit_id=58, name="[Heart of the Land] Mercenary Diane", type=Type.RED, grade=Grade.SR, race=Race.GIANT,
         affection=Affection.SIN, simple_name="diane"),
    Unit(unit_id=59, name="[Kungfu Master] Fighter Diane", type=Type.RED, grade=Grade.SSR, race=Race.GIANT,
         affection=Affection.SIN, simple_name="diane"),
    Unit(unit_id=60, name="[Boar Hat Tavern] Hostess Elizabeth", type=Type.RED, grade=Grade.SR, race=Race.GODDESS,
         affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=61, name="[Liones] Princess Elizabeth", type=Type.GRE, grade=Grade.SSR, race=Race.GODDESS,
         affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=62, name="[Collector] Great Mage Merlin", type=Type.RED, grade=Grade.SSR, race=Race.UNKNOWN,
         affection=Affection.SIN, simple_name="merlin"),
    Unit(unit_id=63, name="[Reincarnation of Revenge] Fairy Helbram", type=Type.RED, grade=Grade.SSR,
         race=Race.FAIRY, simple_name="helbram"),
    Unit(unit_id=64, name="[Omen of Chaos] Druid Hendrickson", type=Type.GRE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="hendrickson"),
    Unit(unit_id=65, name="[Break] Grandmaster Dreyfus", type=Type.GRE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="dreyfus"),
    Unit(unit_id=66, name="[Knight of Ice] Holy Knight Gustav", type=Type.GRE, grade=Grade.SR, race=Race.HUMAN,
         affection=Affection.KNIGHT, simple_name="gustav"),
    Unit(unit_id=67, name="[Reverse] Guardian Hawk & Elizabeth", type=Type.BLUE, grade=Grade.SSR,
         race=Race.GODDESS, affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=68, name="[Slime] Rimuru Tempest", type=Type.GRE, grade=Grade.SR, race=Race.UNKNOWN,
         event=Event.SLI, simple_name="rimuru"),
    Unit(unit_id=69, name="[Ruler of Monsters] Rimuru Tempest", type=Type.BLUE, grade=Grade.SSR, race=Race.UNKNOWN,
         event=Event.SLI, simple_name="rimuru"),
    Unit(unit_id=70, name="[Kijin] Benimaru", type=Type.RED, grade=Grade.SSR, race=Race.UNKNOWN, event=Event.SLI,
         simple_name="benimaru"),
    Unit(unit_id=71, name="[Tyrant of Destruction] Milim Nava", type=Type.BLUE, grade=Grade.SSR, race=Race.UNKNOWN,
         event=Event.SLI, simple_name="milim"),
    Unit(unit_id=72, name="[Doombringer] Mage Lillia", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.CATASTROPHE, simple_name="lillia"),
    Unit(unit_id=73, name="[Fairy King's Forest] Guardian Elaine", type=Type.GRE, grade=Grade.SSR,
         race=Race.FAIRY, simple_name="elaine"),
    Unit(unit_id=74, name="[Camelot's Sword] New King Arthur", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         simple_name="arthur"),
    Unit(unit_id=75, name="[The Ten Commandments] Galland of Truth", type=Type.BLUE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="galland"),
    Unit(unit_id=76, name="[King of Prophecies] Adventurer Arthur", type=Type.BLUE, grade=Grade.SR,
         race=Race.HUMAN, simple_name="arthur"),
    Unit(unit_id=77, name="[A New Adventure] Princess Elizabeth", type=Type.BLUE, grade=Grade.SSR,
         race=Race.GODDESS, affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=78, name="[Nunchaku] Adventurer Ban", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.SIN, simple_name="ban"),
    Unit(unit_id=79, name="[Sunshine] Holy Knight Escanor", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.SIN, simple_name="escanor"),
    Unit(unit_id=80, name="[Creation] Fighter Diane", type=Type.GRE, grade=Grade.SSR, race=Race.GIANT,
         affection=Affection.SIN, simple_name="diane"),
    Unit(unit_id=81, name="[Reincarnation of Obsession] Mage Vivian", type=Type.RED, grade=Grade.SR,
         race=Race.HUMAN, simple_name="vivian"),
    Unit(unit_id=82, name="[Halloween] Captain Meliodas", type=Type.RED, grade=Grade.SSR, race=Race.DEMON,
         event=Event.HAL, affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=83, name="[Halloween] Guardian Elaine", type=Type.BLUE, grade=Grade.SSR, race=Race.FAIRY,
         event=Event.HAL, simple_name="elaine"),
    Unit(unit_id=84, name="[Halloween] Guardian Guila", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.HAL, affection=Affection.KNIGHT, simple_name="guila"),
    Unit(unit_id=85, name="[Mastermind] Mage Lillia", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.CATASTROPHE, simple_name="lillia"),
    Unit(unit_id=86, name="[The Ten Commandments] Monspeet of Reticence", type=Type.RED, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="monspeet"),
    Unit(unit_id=87, name="[Knight of Wrath] Demon Meliodas", type=Type.BLUE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=88, name="[The Pleiades of the Azure Sky] Holy Knight Dogedo", type=Type.RED, grade=Grade.SR,
         race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="dogedo"),
    Unit(unit_id=89, name="[The Pleiades of the Azure Sky] Holy Knight Deathpierce", type=Type.GRE,
         grade=Grade.SSR, race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="deathpierce"),
    Unit(unit_id=90, name="[Disaster] Old Fart King", type=Type.RED, grade=Grade.SSR, race=Race.FAIRY,
         affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=91, name="[The Ten Commandments] Melascula of Faith", type=Type.BLUE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="melascula"),
    Unit(unit_id=92, name="[Infinity] Great Mage Merlin", type=Type.BLUE, grade=Grade.SSR, race=Race.UNKNOWN,
         affection=Affection.SIN, simple_name="merlin"),
    Unit(unit_id=93, name="[The Ten Commandments] Gloxinia of Repose", type=Type.GRE, grade=Grade.SSR,
         race=Race.FAIRY, affection=Affection.COMMANDMENTS, simple_name="gloxinia"),
    Unit(unit_id=94, name="[Earthshaker] Weapon Researcher Valenti", type=Type.GRE, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.CATASTROPHE, simple_name="valenti"),
    Unit(unit_id=95, name="[The Pleiades of the Azure Sky] Holy Knight Deldry", type=Type.RED,
         grade=Grade.SSR, race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="deldry"),
    Unit(unit_id=96, name="[The Pleiades of the Azure Sky] Holy Knight Arden", type=Type.BLUE, grade=Grade.SR,
         race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="arden"),
    Unit(unit_id=97, name="[The Seven Deadly Sins] Holy Knight Diane", type=Type.GRE, grade=Grade.SSR,
         race=Race.GIANT, affection=Affection.SIN, simple_name="diane"),
    Unit(unit_id=98, name="[Ale Collector] Adventurer Ban", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.SIN, simple_name="ban"),
    Unit(unit_id=99, name="[Wings of the Sky] Celestial Ellatte", type=Type.RED, grade=Grade.SSR,
         race=Race.GODDESS, simple_name="ellatte"),
    Unit(unit_id=100, name="[The Lion Sin of Pride] Holy Knight Escanor", type=Type.RED, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.SIN, simple_name="escanor"),
    Unit(unit_id=101, name="[New Legend] Demon Meliodas", type=Type.GRE, grade=Grade.SSR,
         race=Race.DEMON, event=Event.NEY, affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=102, name="[New Legend] Princess Elizabeth", type=Type.RED, grade=Grade.SSR, race=Race.GODDESS,
         event=Event.NEY, affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=103, name="[New Legend] Guardian Jericho", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.NEY, affection=Affection.KNIGHT, simple_name="jericho"),
    Unit(unit_id=104, name="[Elite Demon] Melascula of Faith", type=Type.RED, grade=Grade.SSR, race=Race.DEMON,
         affection=Affection.COMMANDMENTS, simple_name="melascula"),
    Unit(unit_id=105, name="[Harlequin] King the Fairy King", type=Type.RED, grade=Grade.SSR, race=Race.FAIRY,
         affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=106, name="[Elite Demon] Galland of Truth", type=Type.RED, grade=Grade.SSR, race=Race.DEMON,
         affection=Affection.COMMANDMENTS, simple_name="galland"),
    Unit(unit_id=107, name="[Cadet Corps] Eren Jaeger", type=Type.BLUE, grade=Grade.SR, race=Race.HUMAN,
         event=Event.AOT, simple_name="eren"),
    Unit(unit_id=108, name="[Titan Form] Eren Jaeger", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.AOT, simple_name="eren"),
    Unit(unit_id=109, name="[Greatest Soldier] Levi", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.AOT, simple_name="levi"),
    Unit(unit_id=110, name="[Greatest Soldier] Mikasa Ackermann", type=Type.BLUE, grade=Grade.SSR,
         race=Race.HUMAN, event=Event.AOT, simple_name="mikasa"),
    Unit(unit_id=111, name="[The Ten Commandments] Estarossa of Love", type=Type.RED, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="estarossa"),
    Unit(unit_id=112, name="[Elite Demon] Estarossa of Love", type=Type.GRE, grade=Grade.SSR, race=Race.DEMON,
         affection=Affection.COMMANDMENTS, simple_name="estarossa"),
    Unit(unit_id=113, name="[Elite Demon] Monspeet of Reticence", type=Type.GRE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="monspeet"),
    Unit(unit_id=114, name="[The Ten Commandments] Derieri of Purity", type=Type.RED, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="derieri"),
    Unit(unit_id=115, name="[Elite Demon] Derieri of Purity", type=Type.GRE, grade=Grade.SSR, race=Race.DEMON,
         affection=Affection.COMMANDMENTS, simple_name="derieri"),
    Unit(unit_id=116, name="[Virtual Body Doubles] Lostvayne Meliodas", type=Type.RED, grade=Grade.SSR,
         race=Race.DEMON, event=Event.FES, affection=Affection.SIN, simple_name="meliodas"),
    Unit(unit_id=117, name="[Destined Heir] New King Arthur", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         simple_name="arthur"),
    Unit(unit_id=118, name="[Shepherd of Death] Human Weapon Mono", type=Type.RED, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.CATASTROPHE, simple_name="mono"),
    Unit(unit_id=119, name="[Ruler of Stormy Seas] Noblesse Eastin", type=Type.BLUE, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.CATASTROPHE, simple_name="eastin"),
    Unit(unit_id=120, name="[The Ten Commandments] Fraudrin of Selflessness", type=Type.GRE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="dreyfus"),
    Unit(unit_id=121, name="[Sweet Temptation] Guardian Elaine", type=Type.RED, grade=Grade.SSR,
         race=Race.FAIRY, event=Event.VAL, simple_name="elaine"),
    Unit(unit_id=122, name="[Sweet Temptation] Druid Jenna", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.VAL, simple_name="jenna"),
    Unit(unit_id=123, name="[Sweet Temptation] Druid Zaneri", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.VAL, simple_name="zaneri"),
    Unit(unit_id=124, name="[The Ten Commandments] Zeldris of Piety", type=Type.BLUE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="zeldris"),
    Unit(unit_id=125, name="[Elite Demon] Zeldris of Piety", type=Type.RED, grade=Grade.SSR, race=Race.DEMON,
         affection=Affection.COMMANDMENTS, simple_name="zeldris"),
    Unit(unit_id=126, name="[Elite Demon] Gloxinia of Repose", type=Type.RED, grade=Grade.SSR, race=Race.FAIRY,
         affection=Affection.COMMANDMENTS, simple_name="gloxinia"),
    Unit(unit_id=127, name="[Reincarnation of Conviction] Grandmaster Zaratras", type=Type.GRE,
         grade=Grade.SSR, race=Race.HUMAN, affection=Affection.KNIGHT, simple_name="zaratras"),
    Unit(unit_id=128, name="[Dungeon Raider] Gamer Shin", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         affection=Affection.CATASTROPHE, simple_name="shin"),
    Unit(unit_id=129, name="[Mad Destroyer] Queen of Explosions Roxy", type=Type.RED, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.CATASTROPHE, simple_name="roxy"),
    Unit(unit_id=130, name="[KOF' 98] Athena Asamiya", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.KOF, simple_name="athena"),
    Unit(unit_id=131, name="[KOF' 98] Kyo Kusanagi", type=Type.RED, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.KOF, simple_name="kyo"),
    Unit(unit_id=132, name="[KOF' 98] Mei Shiranui", type=Type.BLUE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.KOF, simple_name="mei"),
    Unit(unit_id=133, name="[KOF' 98] Omega Rugal", type=Type.GRE, grade=Grade.SSR, race=Race.HUMAN,
         event=Event.KOF, simple_name="rugal"),
    Unit(unit_id=134, name="[Halloween] Holy Knight Gowther", type=Type.GRE, grade=Grade.SSR, race=Race.UNKNOWN,
         event=Event.HAL, affection=Affection.SIN, simple_name="gowther"),
    Unit(unit_id=135, name="[Fang of the Land] Mercenary Matrona", type=Type.BLUE, grade=Grade.SSR,
         race=Race.GIANT, simple_name="matrona"),
    Unit(unit_id=136, name="[Executor of Darkness] Guardian Deity Camila", type=Type.RED, grade=Grade.SSR,
         race=Race.UNKNOWN, affection=Affection.CATASTROPHE, simple_name="camilla"),
    Unit(unit_id=137, name="[Holy Warrior] Goddess Elizabeth", type=Type.BLUE, grade=Grade.SSR, race=Race.GODDESS,
         event=Event.FES, affection=Affection.SIN, simple_name="liz"),
    Unit(unit_id=138, name="[Knighthood of Scraps Disposal] Captain Hawk", type=Type.GRE, grade=Grade.SSR,
         race=Race.UNKNOWN, event=Event.FES, affection=Affection.SIN, simple_name="hawk"),
    Unit(unit_id=139, name="[Eternal Promise] Holy Knight Diane", type=Type.RED, grade=Grade.SSR,
         race=Race.GIANT, affection=Affection.SIN, simple_name="diane"),
    Unit(unit_id=140, name="[Knight of Scraps Disposal] Oslo & Hawk", type=Type.RED, grade=Grade.SSR,
         race=Race.UNKNOWN, affection=Affection.SIN, simple_name="hawk"),
    Unit(unit_id=141, name="[Elite Demon] Fraudrin of Selflessness", type=Type.BLUE, grade=Grade.SSR,
         race=Race.DEMON, affection=Affection.COMMANDMENTS, simple_name="dreyfus"),
    Unit(unit_id=142, name="[Elite Demon] Drole of Patience", type=Type.BLUE, grade=Grade.SSR, race=Race.GIANT,
         affection=Affection.COMMANDMENTS, simple_name="drole"),
    Unit(unit_id=143, name="[The Ten Commandments] Drole of Patience", type=Type.GRE, grade=Grade.SSR,
         race=Race.GIANT, affection=Affection.COMMANDMENTS, simple_name="drole"),
    Unit(unit_id=144, name="[The Six Knights of Black] Captain Bellion", type=Type.BLUE, grade=Grade.SSR,
         race=Race.DEMON, simple_name="bellion"),
    Unit(unit_id=145, name="[The Four Archangels] Ludociel of Flash", type=Type.BLUE, grade=Grade.SSR,
         race=Race.GODDESS, affection=Affection.ANGEL, simple_name="ludociel"),
    Unit(unit_id=146, name="[Three Millennia of Memories] Aide Gerharde", type=Type.GRE, grade=Grade.SSR,
         race=Race.FAIRY, simple_name="gerharde"),
    Unit(unit_id=147, name="[Royalty] Fairy Helbram", type=Type.BLUE, grade=Grade.SSR, race=Race.FAIRY,
         simple_name="helbram"),
    Unit(unit_id=148, name="[Signs of Maturity] New Wings King", type=Type.BLUE, grade=Grade.SSR,
         race=Race.FAIRY, event=Event.FES, affection=Affection.SIN, simple_name="king"),
    Unit(unit_id=149, name="[Ashen Desire] Demon Hendrickson", type=Type.GRE, grade=Grade.SSR, race=Race.DEMON,
         affection=Affection.KNIGHT, simple_name="hendrickson"),
    Unit(unit_id=150, name="[Advent of Destruction] Lillia of Desire", type=Type.RED, grade=Grade.SSR,
         race=Race.HUMAN, affection=Affection.CATASTROPHE, simple_name="lillia"),
    Unit(unit_id=151, name="[The Four Archangels] Sariel of Tornado", type=Type.RED, grade=Grade.SSR,
         race=Race.GODDESS, affection=Affection.ANGEL, simple_name="sariel"),
    Unit(unit_id=152, name="[The Four Archangels] Tarmiel of Ocean", type=Type.BLUE, grade=Grade.SSR,
         race=Race.GODDESS, affection=Affection.ANGEL, simple_name="tarmiel"),
    Unit(unit_id=153, name="[Fairy of Blessings] Golden Wings Elaine", type=Type.RED, grade=Grade.SSR,
         race=Race.FAIRY, simple_name="elaine"),
    Unit(unit_id=154, name="[Halloween] Gamer Shin", type=Type.RED, grade=Grade.SSR,
         race=Race.HUMAN, simple_name="shin", affection=Affection.CATASTROPHE, event=Event.HAL),
    Unit(unit_id=155, name="[Halloween] Queen of Explosions Roxy", type=Type.GRE, grade=Grade.SSR,
         race=Race.HUMAN, simple_name="roxy", affection=Affection.CATASTROPHE, event=Event.HAL),
    Unit(unit_id=156, name="[Knight of Frost] Guardian Jericho", type=Type.RED, grade=Grade.SSR,
         race=Race.HUMAN, simple_name="jericho", affection=Affection.KNIGHT),
    Unit(unit_id=157, name="[Invincible Avatar] \"The One\" Escanor", type=Type.BLUE, grade=Grade.SSR,
         race=Race.HUMAN, simple_name="escanor", affection=Affection.SIN),
    Unit(unit_id=158, name="[Light of Hope] New King Arthur", type=Type.GRE, grade=Grade.SSR,
         race=Race.HUMAN, simple_name="arthur")
]
R_UNITS = list(filter(lambda x: x.grade == Grade.R, UNITS))
SR_UNITS = list(filter(lambda x: x.grade == Grade.SR and x.event == Event.GC, UNITS))
RACE_COUNTER = {
    Race.HUMAN: len(list(filter(lambda x: x.race == Race.HUMAN, UNITS))),
    Race.FAIRY: len(list(filter(lambda x: x.race == Race.FAIRY, UNITS))),
    Race.DEMON: len(list(filter(lambda x: x.race == Race.DEMON, UNITS))),
    Race.UNKNOWN: len(list(filter(lambda x: x.race == Race.UNKNOWN, UNITS))),
    Race.GODDESS: len(list(filter(lambda x: x.race == Race.GODDESS, UNITS))),
    Race.GIANT: len(list(filter(lambda x: x.race == Race.GIANT, UNITS))),
}
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
        if sr_unit_rate != 0 and includes_all_sr:
            units += SR_UNITS
        if r_unit_rate != 0 and includes_all_r:
            units += R_UNITS
        self.units: List[Unit] = units
        self.rate_up_unit: List[Unit] = rate_up_units
        self.ssr_unit_rate: float = ssr_unit_rate
        self.ssr_unit_rate_up: float = ssr_unit_rate_up
        self.sr_unit_rate: float = sr_unit_rate
        self.r_unit_rate: float = r_unit_rate
        self.banner_type: BannerType = banner_type
        self.r_units: List[Unit] = list(filter(lambda x: x.grade == Grade.R, self.units))
        self.sr_units: List[Unit] = list(filter(lambda x: x.grade == Grade.SR, self.units))
        self.ssr_units: List[Unit] = list(
            filter(lambda x: x.grade == Grade.SSR and x not in self.rate_up_unit, self.units))
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


def strip_whitespace(arg: str) -> str:
    return arg.replace(" ", "")


def file_exists(file) -> bool:
    try:
        with open(file):
            return True
    except FileNotFoundError:
        return False


ALL_BANNERS = [
    Banner(name=["banner 1", "banner one", "t1", "the one", "escanor"],
           pretty_name="1st 7DS Anniversary The One Festival Draw",
           units=units_by_id([
               157, 158, 116, 137, 148, 149, 1, 49, 100, 112, 125, 142, 129, 136, 118, 128
           ]),
           ssr_unit_rate=0.25,
           sr_unit_rate=1.2414,
           bg_url="https://i.imgur.com/txERVKP.jpg"),
    Banner(name=["banner 2", "banner two", "homecoming"],
           pretty_name="7DS Homecoming Special",
           units=units_by_id([
               94, 73, 72, 74, 16, 13, 14, 3, 6, 15, 7, 2
           ]),
           ssr_unit_rate=0.25,
           sr_unit_rate=1.2759,
           bg_url="https://i.imgur.com/7ktNtcm.jpg"),
    Banner(name=["part 1", "part one"],
           pretty_name="Part. 1",
           units=units_by_id([
               73, 74, 16, 13, 63, 14, 3, 6, 15, 7, 2, 62, 4, 12, 38, 19, 11, 5, 10, 59, 97, 61, 9]),
           ssr_unit_rate=0.0991,
           ssr_unit_rate_up=0.35,
           sr_unit_rate=1.3704,
           bg_url="https://i.imgur.com/s1083TM.png"),

    Banner(name=["part 2", "part two"],
           pretty_name="Part. 2",
           units=units_by_id([
               143, 135, 127, 124, 120, 117, 114, 111, 144, 99, 95, 93, 89, 86, 91, 79, 75, 92, 105, 98, 78, 80, 77, 67,
               87]),
           ssr_unit_rate=0.09,
           ssr_unit_rate_up=0.35,
           sr_unit_rate=1.3704,
           bg_url="https://i.imgur.com/cTzcHfg.png"),

    Banner(name=["gssr part 1", "gssr part one", "gssr part I"],
           pretty_name="Guaranteed SSR Part. 1",
           units=units_by_id([
               73, 74, 16, 13, 63, 14, 3, 6, 15, 7, 2, 62, 4, 12, 38, 19, 11, 5, 10, 59, 97, 61, 9, 149]),
           ssr_unit_rate=4.3478,
           sr_unit_rate=0,
           r_unit_rate=0,
           banner_type=BannerType.FIVE,
           bg_url="https://i.imgur.com/YEZD0mx.png"),

    Banner(name=["gssr part 2", "gssr part two", "gssr part II"],
           pretty_name="Guaranteed SSR Part 2.",
           units=units_by_id([
               143, 135, 127, 124, 120, 117, 114, 111, 144, 99, 95, 93, 89, 86, 91, 79, 75, 92, 105, 98, 78, 80, 77, 67,
               87, 147]),
           ssr_unit_rate=4,
           sr_unit_rate=0,
           r_unit_rate=0,
           banner_type=BannerType.FIVE,
           bg_url="https://i.imgur.com/QXcBm3K.png"),

    Banner(name=["race 1", "race one", "race I"],
           pretty_name="[Race Draw I] Human/Giant/Unknown",
           units=units_by_id([
               143, 135, 127, 117, 95, 89, 79, 74, 16, 14, 3, 15, 7, 2, 62, 4, 92, 98, 78, 80, 11, 5, 10, 59, 97,
               96, 88, 76, 81, 57, 22, 30, 53, 25, 65, 64, 33, 35, 40, 41, 31, 32, 39, 43, 36, 23, 21, 58]),
           includes_all_sr=False,
           ssr_unit_rate=0.2308,
           sr_unit_rate=3.9167,
           r_unit_rate=0,
           banner_type=BannerType.FIVE,
           bg_url="https://i.imgur.com/0YobFo4.png"),

    Banner(name=["race 2", "race two", "race II"],
           pretty_name="[Race Draw II] Demon/Fairy/Goddess",
           units=units_by_id([
               124, 120, 114, 111, 99, 144, 93, 86, 91, 75, 73, 13, 63, 12, 38, 19, 77, 67, 87, 9, 145, 146, 147, 149,
               151, 152,
               60, 27, 28, 47, ]),
           includes_all_sr=False,
           ssr_unit_rate=0.25,
           sr_unit_rate=23.5,
           r_unit_rate=0,
           banner_type=BannerType.FIVE,
           bg_url="https://i.imgur.com/WVEIzFP.png"),

    Banner(name=["humans", "human"],
           pretty_name="Grade R-SSR Human Heroes",
           units=list(filter(lambda x: x.race == Race.HUMAN and x.event == Event.GC, UNITS)),
           includes_all_sr=False,
           includes_all_r=False,
           ssr_unit_rate=0.0625,
           sr_unit_rate=0.8636,
           r_unit_rate=8.8889,
           banner_type=BannerType.FIVE,
           bg_url="https://i.imgur.com/P67MIY6.png")
]


@BOT.event
async def on_ready():
    CURSOR.execute("""
    CREATE TABLE IF NOT EXISTS "units" (
        unit_id INTEGER PRIMARY KEY,
        name Text,
        simple_name Text,
        type Text,
        grade Text,
        race Text,
        affection Text
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
    read_units_from_json()
    print('Logged in as')
    print(BOT.user.name)
    print(BOT.user.id)
    print('--------')


RACES = [Race.DEMON, Race.GIANT, Race.HUMAN, Race.FAIRY, Race.GODDESS, Race.UNKNOWN]
GRADES = [Grade.R, Grade.SR, Grade.SSR]
TYPES = [Type.RED, Type.GRE, Type.BLUE]
EVENTS = [Event.GC, Event.SLI, Event.AOT, Event.KOF, Event.FES, Event.NEY, Event.VAL, Event.HAL]
AFFECTIONS = [Affection.SIN, Affection.COMMANDMENTS, Affection.CATASTROPHE, Affection.ANGEL, Affection.KNIGHT,
              Affection.NONE]


def create_random_unit(grades: List[Grade] = None,
                       types: List[Type] = None,
                       races: List[Race] = None,
                       events: List[Event] = None,
                       affections: List[Affection] = None) -> Unit:
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

    return possible_units[ra.randint(0, len(possible_units) - 1)]


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
    elif raw_event in "custom":
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
async def multi(ctx, banner_name: str = "banner 1", amount: int = 1, person: discord.Member = None):
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

    if amount > 5:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=SUMMON_THROTTLE_ERROR_EMBED)
    elif amount < 2:
        img = compose_multi_draw(banner=banner) if banner.banner_type == BannerType.ELEVEN \
            else compose_five_multi_draw(banner=banner)
        await ctx.send(file=image_to_discord(img, "units.png"),
                       content=f"{person.mention} this is your multi" if person is ctx.message.author
                       else f"{person.mention} this is your multi coming from {ctx.message.author.mention}",
                       embed=discord.Embed(title=f"{banner.pretty_name} "
                                                 f"({11 if banner.banner_type == BannerType.ELEVEN else 5}x summon)")
                       .set_image(url="attachment://units.png"))
        return await draw.delete()

    pending = []
    for a in range(amount):
        img = compose_multi_draw(banner=banner) if banner.banner_type == BannerType.ELEVEN else compose_five_multi_draw(
            banner=banner)
        pending.append(
            {
                "file": image_to_discord(img, "units.png"),
                "content": f"{person.mention} this is your {a+1}. multi" if person is ctx.message.author
                else f"{person.mention} this is your {a+1}. multi coming from {ctx.message.author.mention}",
                "embed-title": f"{banner.pretty_name} ({11 if banner.banner_type == BannerType.ELEVEN else 5}x summon)"
            }
        )
    await draw.edit(embed=IMAGES_LOADED_EMBED)

    for pend in pending:
        await ctx.send(file=pend["file"],
                       content=pend["content"],
                       embed=discord.Embed(title=pend["embed-title"]).set_image(url="attachment://units.png"))
    await draw.delete()


# ..summon
@BOT.command()
async def summon(ctx):
    draw = await ctx.send(embed=LOADING_EMBED)
    await build_menu(ctx, prev_message=draw)


async def build_menu(ctx, prev_message, page: int = 0, action: str = ""):
    if action == "single":
        return await ctx.send(content=f"{ctx.message.author.mention} this is your single",
                              file=compose_draw(ALL_BANNERS[page]),
                              embed=discord.Embed(
                                  title=f"{ALL_BANNERS[page].pretty_name} (1x summon)")
                              .set_image(url="attachment://unit.png"))
    elif action == "multi":
        await prev_message.edit(embed=LOADING_EMBED.set_image(url=LOADING_IMAGE_URL))

        await ctx.send(file=image_to_discord(
            compose_multi_draw(banner=ALL_BANNERS[page]) if ALL_BANNERS[page].banner_type == BannerType.ELEVEN
            else compose_five_multi_draw(
                banner=ALL_BANNERS[page]), "units.png"),
            content=f"{ctx.message.author.mention} this is your multi",
            embed=discord.Embed(
                title=f"{ALL_BANNERS[page].pretty_name} "
                      f"({11 if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else 5}x summon)"
            ).set_image(url="attachment://units.png"))
        return await prev_message.delete()
    elif action == "shaft":
        for bN in ALL_BANNERS[page].name:
            if "gssr" in bN:
                return await prev_message.edit(content=f"{ctx.message.author.mention}",
                                               embed=discord.Embed(
                                                   title="Error",
                                                   colour=discord.Color.dark_red(),
                                                   description=f"Can't get shafted on the \"{ALL_BANNERS[page].pretty_name}\" banner "
                                               )
                                               )
        i = 0
        draw = await ctx.send(content=f"{ctx.message.author.mention} this is your multi",
                              embed=discord.Embed(title="Shafting...").set_image(
                                  url=LOADING_IMAGE_URL))

        rang = 11 if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else 5
        drawn_units = [unit_with_chance(ALL_BANNERS[page]) for _ in range(rang)]

        def has_ssr(du: List[Unit]) -> bool:
            for u in du:
                if u.grade == Grade.SSR:
                    return True
            return False

        while not has_ssr(drawn_units):
            i += 1
            drawn_units = [unit_with_chance(ALL_BANNERS[page]) for _ in range(rang)]

        await ctx.send(file=image_to_discord(
            compose_unit_multi_draw(units=drawn_units) if ALL_BANNERS[page].banner_type == BannerType.ELEVEN
            else compose_unit_five_multi_draw(units=drawn_units), "units.png"),
            content=f"{ctx.message.author.mention}",
            embed=discord.Embed(
                title=f"{ALL_BANNERS[page].pretty_name} ({rang}x summon)",
                description=f"Shafted {i} times \n This is your final pull"
            ).set_image(url="attachment://units.png")
        )
        await prev_message.delete()
        return await draw.delete()

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
            await build_menu(ctx, prev_message=draw, page=page, action="multi")
        elif "1️⃣" in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page, action="single")
        elif "🐋" in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page, action="shaft")
    except asyncio.TimeoutError:
        pass


# ..single
@BOT.command()
async def single(ctx, banner_name: str = "banner 1", amount: int = 1, person: discord.Member = None):
    if person is None:
        person = ctx.message.author
    banner = banner_by_name(banner_name)
    if banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"))

    if amount > 5:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=SUMMON_THROTTLE_ERROR_EMBED)
    elif amount < 2:
        return await ctx.send(file=compose_draw(banner),
                              content=f"{person.mention} this is your single" if person is ctx.message.author
                              else f"{person.mention} this is your single coming from {ctx.message.author.mention}",
                              embed=discord.Embed(title=f"{banner.pretty_name} (1x summon)").set_image(
                                  url="attachment://unit.png"))

    draw = await ctx.send(embed=LOADING_EMBED.set_image(url=LOADING_IMAGE_URL))

    pending = []
    for a in range(amount):
        img = unit_with_chance(banner).icon
        pending.append(
            {
                "file": image_to_discord(img, "unit.png"),
                "content": f"{person.mention} this is your {a+1}. single" if person is ctx.message.author
                else f"{person.mention} this is your {a+1}. single from {ctx.message.author}",
                "embed-title": f"{banner.pretty_name} (1x summon)"
            }
        )
    await draw.edit(embed=IMAGES_LOADED_EMBED)

    for pend in pending:
        await ctx.send(file=pend["file"],
                       content=pend["content"],
                       embed=discord.Embed(title=pend["embed-title"]).set_image(url="attachment://unit.png"))
    await draw.delete()


# ..shaft
@BOT.command()
async def shaft(ctx, banner_name: str = "banner 1", amount: int = 1, person: discord.Member = None):
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

    async def do_shaft():
        i = 0
        draw = await ctx.send(content=f"{person.mention} this is your shaft" if person is ctx.message.author
                              else f"{person.mention} this is your shaft coming from {ctx.message.author.mention}",
                              embed=discord.Embed(title="Shafting...").set_image(
                                  url=LOADING_IMAGE_URL))

        rang = 11 if banner.banner_type == BannerType.ELEVEN else 5
        drawn_units = [unit_with_chance(banner) for _ in range(rang)]

        def has_ssr(du: List[Unit]) -> bool:
            for u in du:
                if u.grade == Grade.SSR:
                    return True
            return False

        while not has_ssr(drawn_units):
            i += 1
            drawn_units = [unit_with_chance(banner) for _ in range(rang)]

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

    if amount > 5:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=SUMMON_THROTTLE_ERROR_EMBED)
    elif amount < 2:
        return await do_shaft()

    for a in range(amount):
        await do_shaft()


# ..create
@BOT.command()
async def create(ctx, name="", simple_name="", attribute="red", grade="ssr", file_url="", race="", affection=""):
    if file_url == "" or name == "" or simple_name == "":
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
        save_unit_to_json(icon=icon, attribute=atr, grade=grd, name=name, race=rac, affection=affection,
                          simple_name=simple_name)


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


def unit_with_chance(banner: Banner) -> Unit:
    u = banner.units[ra.randint(0, len(banner.units) - 1)]
    draw_chance = round(ra.uniform(0, 100), 4)

    if len(banner.r_units) == 0 and len(banner.sr_units) == 0:
        if banner.ssr_unit_rate < draw_chance < banner.ssr_unit_rate_up and u not in banner.rate_up_unit:
            u = banner.rate_up_unit[ra.randint(0, len(banner.rate_up_unit) - 1)]
        return u

    chance = ra.randint(0, 100)
    if chance > (banner.ssr_unit_rate_up * len(banner.rate_up_unit)) + (
            banner.ssr_unit_rate * (len(banner.ssr_units))):
        if chance > (banner.sr_unit_rate * len(banner.sr_units)):
            u = banner.r_units[ra.randint(0, len(banner.r_units) - 1)]
        else:
            u = banner.sr_units[ra.randint(0, len(banner.sr_units) - 1)]
    elif banner.ssr_unit_rate < draw_chance < banner.ssr_unit_rate_up and u not in banner.rate_up_unit:
        u = banner.rate_up_unit[ra.randint(0, len(banner.rate_up_unit) - 1)]

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


def compose_draw(banner: Banner) -> discord.File:
    return unit_with_chance(banner).discord_icon()


def compose_five_multi_draw(banner: Banner) -> Image:
    return compose_unit_five_multi_draw([unit_with_chance(banner) for _ in range(5)])


def compose_multi_draw(banner: Banner) -> Image:
    return compose_unit_multi_draw([unit_with_chance(banner) for _ in range(11)])


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
    background_frame = FRAME_BACKGROUNDS[grade]
    if background is None:
        background = background_frame
    else:
        background = background.resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    frame = FRAMES[attribute][grade]
    background_frame.paste(background, (0, 0), background)
    background_frame.paste(frame, (0, 0), frame)

    return background_frame


def read_units_from_json():
    for row in CURSOR.execute('SELECT * FROM units'):
        UNITS.append(Unit(unit_id=row[0],
                          name=row[1],
                          simple_name=row[2],
                          type=map_attribute(row[3]),
                          grade=map_grade(row[4]),
                          race=map_race(row[5]),
                          affection=map_affection(row[6]),
                          event=Event.CUS))


def save_unit_to_json(attribute: Type, grade: Grade, icon: Image, name: str, simple_name: str,
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
             simple_name=simple_name)

    i = (u.unit_id, u.name, u.simple_name, u.type.value, u.grade.value, u.race.value, u.affection.value)
    CURSOR.execute('INSERT INTO units VALUES (?, ?, ?, ?, ?, ?, ?)', i)
    CONN.commit()


if __name__ == '__main__':
    try:
        BOT.run(TOKEN)
    finally:
        CONN.close()
