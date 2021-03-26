from PIL import Image, ImageDraw, ImageFont
from typing import List, Pattern, Generator, Any, Dict, Tuple, Callable, Awaitable, AsyncGenerator, Optional, Union, Coroutine as Coro
from discord.ext import commands
from discord.ext.commands import has_permissions, HelpCommand
from io import BytesIO
from itertools import islice
from enum import Enum

import asyncio
import aiohttp
import math
import discord
import typing
import random as ra
import sqlite3 as sqlite
import re
import PIL.Image as ImageLib
import os
import logging


LOGGER = logging.getLogger('discord')
LOGGER.setLevel(logging.DEBUG)
HANDLER = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
HANDLER.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
LOGGER.addHandler(HANDLER)

IMG_SIZE: int = 150
FOOD_SIZE: int = 75

UNITS = []
R_UNITS = []
SR_UNITS = []
CUSTOM_UNITS = []
ALL_BANNERS = []

ssr_pattern: Pattern[str] = re.compile(r'(ssr[-_:])+')
number_pattern: Pattern[str] = re.compile(r'^([1-4][0-9]\s+)?$|50\s+')

TEAM_TIME_CHECK: List[discord.Member] = []
PVP_TIME_CHECK: List[discord.Member] = []

DEMON_ROLES: Dict[int, Dict[str, List[discord.Role]]] = {}
DEMON_OFFER_MESSAGES = {}

STAT_HELPER: Dict[discord.ext.commands.Context, Dict[str, Any]] = {}

PERIODS: Dict[str, int] = [
    ('year', 60 * 60 * 24 * 365),
    ('month', 60 * 60 * 24 * 30),
    ('day', 60 * 60 * 24),
    ('hour', 60 * 60),
    ('minute', 60),
    ('second', 1)
]


def chunks(lst: List[Any], n: int) -> Generator[None, List[Any], None]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def chunks_dict(data: Dict[Any, Any], chunk_size=10000) -> Generator[None, Dict[Any, Any], None]:
    it = iter(data)
    for _ in range(0, len(data), chunk_size):
        yield {k: data[k] for k in islice(it, chunk_size)}


def flatten(to_flatten: List[List[Any]]) -> List[Any]:
    return [item for sublist in to_flatten for item in sublist]


class LeaderboardType(Enum):
    LUCK: str = "luck"
    MOST_SSR: str = "ssrs"
    MOST_UNITS: str = "units"
    MOST_SHAFTS: str = "shafts"


class AdvancedGrade(Enum):
    C = "c"
    UC = "uc"
    R = "r"
    SR = "sr"
    SSR = "ssr"
    UR = "ur"


class Material:
    def __init__(self, _id: int,  name: str, grade: AdvancedGrade = AdvancedGrade.R, icon: Optional[ImageLib.Image] = None):
        self.material_id: int = _id
        self.name: str = name
        if icon is None:
            self.icon = ImageLib.open(f"gc/materials/{name.lower().replace(' ', '_')}_{grade.value}.png")
        else:
            self.icon = icon

    def __str__(self):
        return self.name + f" {self.material_id}"

    def __repr__(self):
        return self.name + f" {self.material_id}"


MATERIALS = [
    Material(_id=101, name="Water of Life", grade=AdvancedGrade.C),
    Material(_id=102, name="Water of Life", grade=AdvancedGrade.UC),
    Material(_id=103, name="Water of Life", grade=AdvancedGrade.R),
    Material(_id=104, name="Water of Life", grade=AdvancedGrade.SR),
    Material(_id=105, name="Water of Life", grade=AdvancedGrade.SSR),
    Material(_id=106, name="Water of Life", grade=AdvancedGrade.UR),

    Material(_id=201, name="Demon Blood", grade=AdvancedGrade.C),
    Material(_id=202, name="Demon Blood", grade=AdvancedGrade.UC),
    Material(_id=203, name="Demon Blood", grade=AdvancedGrade.R),
    Material(_id=204, name="Demon Blood", grade=AdvancedGrade.SR),
    Material(_id=205, name="Demon Blood", grade=AdvancedGrade.SSR),
    Material(_id=206, name="Demon Blood", grade=AdvancedGrade.UR),

    Material(3, "Identifying Nametag"),
    Material(4, "Usable Armor Fragment"),
    Material(5, "Seal of the [Beard of the Mountain Cat]"),
    Material(6, "Mustache Comb"),
    Material(7, "Wolf Fang"),
    Material(8, "Friendship Bracelet"),

    Material(9, "Patrol Log"),
    Material(10, "Insect's Poison Stinger"),
    Material(11, "Ancient Warrior Armor Fragment"),
    Material(12, "Soul Crystal"),
    Material(13, "Chess Piece Fragment"),
    Material(14, "Sharp Spike"),

    Material(15, "Broken Horn"),
    Material(16, "Weathered Knighthood Insignia"),
    Material(17, "Non-stick Spider Silk"),
    Material(18, "Pungent Piece of Cloth"),
    Material(19, "Cuspid Fragment"),
    Material(20, "Mysterious Magic Potion"),

    Material(21, "Ominous Dark Orb"),
    Material(22, "Sharp Horn"),
    Material(23, "Warrior's Emblem"),
    Material(24, "Token of Immortality"),
    Material(25, "Wind Feather"),
    Material(26, "Ominous Spellcasting Fluid"),

    Material(27, "Old Armor Fragment"),
    Material(28, "Murky Soul Crystal"),
    Material(29, "Hard Bone Fragment"),
    Material(30, "Totem"),
    Material(31, "Spellcasting Ivory Charm"),
    Material(32, "Blood-stained Battle Helm"),

    Material(33, "High-rank Mage's Mask"),
    Material(34, "Royal Gift"),
    Material(35, "Magical Robe"),
    Material(36, "Double-edged Sword Fragment"),
    Material(37, "Emblem of the Knighthood of Liones"),
    Material(38, "Token of Courage")
]


def find_material(_id: int):
    return next((x for x in MATERIALS if _id == x.material_id), None)


def map_leaderboard(raw_leaderboard: str) -> LeaderboardType:
    raw_leaderboard = raw_leaderboard.replace(" ", "").lower()
    if raw_leaderboard in ["ssr", "ssrs", "mostssr", "mostssrs"]:
        return LeaderboardType.MOST_SSR
    if raw_leaderboard in ["units", "unit", "mostunits", "mostunit"]:
        return LeaderboardType.MOST_UNITS
    if raw_leaderboard in ["shaft", "shafts", "mostshafts", "mostshaft"]:
        return LeaderboardType.MOST_SHAFTS
    return LeaderboardType.LUCK


def td_format(td_object):
    seconds = int(td_object.total_seconds())

    strings = []
    for period_name, period_seconds in PERIODS:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)


def longest_material_icons(materials: dict):
    return sorted(materials.keys(), key=lambda k: len(k.icons), reverse=True)[0]


def grade_to_int(grade: AdvancedGrade):
    if grade == AdvancedGrade.C:
        return 1
    if grade == AdvancedGrade.UC:
        return 2
    if grade == AdvancedGrade.R:
        return 3
    if grade == AdvancedGrade.SR:
        return 4
    if grade == AdvancedGrade.SSR:
        return 5
    if grade == AdvancedGrade.UR:
        return 6
