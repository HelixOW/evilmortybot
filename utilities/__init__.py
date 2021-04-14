from typing import List, Pattern, Generator, Any, Dict, Tuple
from discord.ext import commands
from discord.ext.commands import Context
from itertools import islice
from io import BytesIO, StringIO

import discord
import sqlite3 as sqlite
import re
import logging


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

img_size: int = 150
half_img_size: int = 75

unit_list = []
r_unit_list = []
sr_unit_list = []
custom_unit_list = []
all_banner_list = []

ssr_pattern: Pattern[str] = re.compile(r'(ssr[-_:])+')
number_pattern: Pattern[str] = re.compile(r'^([1-4][0-9]\s+)?$|50\s+')

demon_offer_messages = {}

periods: List[Tuple[str, int]] = [
    ('year', 60 * 60 * 24 * 365),
    ('month', 60 * 60 * 24 * 30),
    ('day', 60 * 60 * 24),
    ('hour', 60 * 60),
    ('minute', 60),
    ('second', 1)
]

connection: sqlite.Connection = sqlite.connect("data/data.db")


class MemberMentionConverter(commands.Converter):
    async def convert(self, ctx: Context, argument: str) -> discord.Member:
        return ctx.message.mentions[0]


def get_prefix(_bot, message):
    return commands.when_mentioned_or(*['..', 'k> ', 'd> '])(_bot, message)


async def text_to_discord(text: str) -> discord.File:
    with StringIO(text) as file:
        image_file = discord.File(fp=file, filename="lol.md")
    return image_file


class StatsContext(commands.Context):
    data = None

    def save_stats(self, _data: Dict[str, Any]):
        self.data = _data


class KingBot(commands.Bot):
    async def get_context(self, message, *, cls=StatsContext):
        return await super().get_context(message, cls=cls)


def chunks(lst: List[Any], n: int) -> Generator[None, List[Any], None]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def chunks_dict(data: Dict[Any, Any], chunk_size=10000) -> Generator[None, Dict[Any, Any], None]:
    it = iter(data)
    for _ in range(0, len(data), chunk_size):
        yield {k: data[k] for k in islice(it, chunk_size)}


def flatten(to_flatten: List[List[Any]]) -> List[Any]:
    return [item for sublist in to_flatten for item in sublist]


def remove_trailing_whitespace(to_remove: str) -> str:
    while to_remove.startswith(" "):
        to_remove = to_remove[1:]

    while to_remove.endswith(" "):
        to_remove = to_remove[:-1]
    return to_remove


def remove_beginning_ignore_case(remove_from: str, beginning: str) -> str:
    if remove_from.lower().startswith(beginning.lower()):
        return remove_from[len(beginning):]
    return remove_from


def td_format(td_object):
    seconds = int(td_object.total_seconds())

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)
