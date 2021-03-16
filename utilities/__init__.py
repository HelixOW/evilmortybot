from PIL import Image, ImageDraw, ImageFont
from typing import List
from discord.ext import commands
from discord.ext.commands import has_permissions, HelpCommand
from io import BytesIO
from itertools import islice

import asyncio
import aiohttp
import math
import discord
import typing
import random as ra
import sqlite3 as sqlite
import re

IMG_SIZE = 150

UNITS = []
R_UNITS = []
SR_UNITS = []
CUSTOM_UNITS = []
ALL_BANNERS = []

ssr_pattern = re.compile(r'(ssr[-_:])+')


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def chunks_dict(data, chunk_size=10000):
    it = iter(data)
    for _ in range(0, len(data), chunk_size):
        yield {k: data[k] for k in islice(it, chunk_size)}
