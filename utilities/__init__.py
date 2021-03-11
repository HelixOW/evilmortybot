from PIL import Image, ImageDraw, ImageFont
from typing import List
from discord.ext import commands
from discord.ext.commands import has_permissions, HelpCommand
from io import BytesIO

import asyncio
import aiohttp
import math
import discord
import typing
import random as ra
import sqlite3 as sqlite


IMG_SIZE = 150


UNITS = []
R_UNITS = []
SR_UNITS = []
CUSTOM_UNITS = []
ALL_BANNERS = []


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
