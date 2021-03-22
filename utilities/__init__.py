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
