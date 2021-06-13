import asyncio
from typing import List, Pattern, Generator, Any, Dict, Tuple, Callable, TypeVar, Union, ValuesView

from discord.ext import commands
from discord.ext.commands import Context
from itertools import islice
from io import StringIO, BytesIO
from PIL import ImageFont, Image, ImageDraw
from PIL.ImageFont import FreeTypeFont

import discord
import re
import logging

import utilities.reactions
import utilities.embeds

T = TypeVar('T')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

img_size: int = 150
half_img_size: int = 75
link_img_size: int = 50
half_link_img_size: int = 30

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

database: str = "data/data.db"

font_12: FreeTypeFont = ImageFont.truetype("pvp.ttf", 12)
font_24: FreeTypeFont = ImageFont.truetype("pvp.ttf", 24)


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


async def image_to_discord(img: Image, image_name: str = "image.png") -> \
        discord.File:
    with BytesIO() as image_bin:
        img.save(image_bin, 'webp', quality=10, optimize=True)
        image_bin.seek(0)
        image_file = discord.File(fp=image_bin, filename=image_name)
    return image_file


def chunks(lst: List[Any], n: int) -> Generator[List[Any], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def chunks_dict(data: Dict[Any, Any], chunk_size=10000) -> Generator[Dict[Any, Any], None, None]:
    it = iter(data)
    for _ in range(0, len(data), chunk_size):
        yield {k: data[k] for k in islice(it, chunk_size)}


def flatten(to_flatten: Union[List[List[Any]], ValuesView[List[Any]]]) -> List[Any]:
    return [item for sublist in to_flatten for item in sublist]


def remove_beginning_ignore_case(remove_from: str, beginning: str) -> str:
    if remove_from.lower().startswith(beginning.lower()):
        return remove_from[len(beginning):]
    return remove_from


def get_text_dimensions(text_string: str, font: FreeTypeFont = font_24) -> Tuple[int, int]:
    _, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height


def text_with_shadow(draw: ImageDraw, text: str, xy: Tuple[int, int], fill: Tuple[int, int, int] = (255, 255, 255),
                     font: FreeTypeFont = font_24) -> None:
    for x, y in [(xy[0] + 1, xy[1]),
                 (xy[0], xy[1] + 1),
                 (xy[0] + 1, xy[1] + 1)]:
        draw.text(
            xy=(x, y),
            text=text,
            fill=(0, 0, 0),
            font=font
        )

    draw.text(
        xy=(xy[0], xy[1]),
        text=text,
        fill=fill,
        font=font
    )


async def send_paged_message(_bot: discord.ext.commands.Bot, ctx: Context,
                             check_func: Callable,
                             timeout: int,
                             pages: List[Dict[str, Any]],
                             buttons: List[Dict[Callable[[], str], Callable[[discord.Message, int], Any]]] = None,
                             after_message: Callable = None):
    if buttons is None:
        buttons = [{} for _, _ in enumerate(pages)]

    async def display_page(page: int, previous_message: discord.Message = None):
        if previous_message is None:
            page_content: discord.Message = await ctx.send(
                file=await image_to_discord(pages[page]["file"]) if pages[page]["file"] is not None else None,
                content=pages[page]["content"],
                embed=pages[page]["embed"]
            )
        else:
            if pages[page]["file"] is None:
                await previous_message.edit(
                    content=pages[page]["content"],
                    embed=pages[page]["embed"]
                )
                page_content: discord.Message = previous_message
                await page_content.clear_reactions()
            else:
                page_content: discord.Message = await ctx.send(
                    file=await image_to_discord(pages[page]["file"]) if pages[page]["file"] is not None else None,
                    content=pages[page]["content"],
                    embed=pages[page]["embed"]
                )
                await previous_message.delete()

        if after_message is not None:
            try:
                await after_message()
            except:
                pass

        if len(pages) == 1:
            return

        if page != 0:
            await page_content.add_reaction(utilities.reactions.LEFT_ARROW)

        for emoji in buttons[page].keys():
            if emoji is not None:
                await page_content.add_reaction(emoji)

        if page != len(pages) - 1:
            await page_content.add_reaction(utilities.reactions.RIGHT_ARROW)

        try:
            reaction, _ = await _bot.wait_for('reaction_add', check=check_func, timeout=timeout)
            clicked: str = str(reaction.emoji)

            if clicked == utilities.reactions.LEFT_ARROW and page != 0:
                return await display_page(page - 1, page_content)

            if clicked == utilities.reactions.RIGHT_ARROW and page != len(pages) - 1:
                return await display_page(page + 1, page_content)

            try:
                if buttons[page][clicked] is not None:
                    await buttons[page][clicked](page_content, page)
            except KeyError:
                pass
        except asyncio.TimeoutError:
            await page_content.clear_reactions()

    await display_page(0, None)


async def ask(ctx: Context,
              question: Union[str, discord.Message],
              convert: Callable[..., T],
              no_input: str = None,
              default_val: T = None,
              convert_failed: str = None,
              timeout: int = 30,
              interrupt_check: Callable[[str], bool] = lambda x: x.lower() in ["stop", "s", "end"],
              delete_question: bool = True,
              delete_answer: bool = True,
              asked_person: discord.Member = None,
              additional_check: Callable[[discord.Message], bool] = lambda _: True) -> T:
    if not asked_person:
        asked_person = ctx.author
    if isinstance(question, str):
        asking_message: discord.Message = await ctx.send(question)
    else:
        asking_message = question

    try:
        answer_message: discord.Message = await ctx.bot.wait_for(
            "message",
            check=lambda x: x.author.id == asked_person.id and x.channel.id == ctx.channel.id and additional_check(x),
            timeout=timeout)

        answer = answer_message.content
        if delete_question:
            await asking_message.delete()
        if delete_answer:
            await answer_message.delete()

        if interrupt_check(answer):
            return default_val

        try:
            return convert(answer)
        except ValueError:
            if convert_failed is not None:
                await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed(convert_failed))
            return await ask(ctx, question, convert, no_input, default_val, convert_failed, timeout, interrupt_check,
                             delete_question, delete_answer, asked_person)
    except asyncio.TimeoutError:
        await asking_message.delete()
        if no_input is not None:
            await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed(no_input))
        return default_val


async def dialogue(ctx: Context,
                   provide_question: str,
                   followed_question: str,
                   convert: Callable[..., T],
                   no_input: str = None,
                   default_val: T = None,
                   convert_failed: str = None,
                   provide_timeout: int = 30,
                   follow_timeout: int = 30) -> T:

    def cont_conv(x: str):
        if x.lower() in ("true", "yes", "y", "ye", "yeah", "1", "yup", "ok"):
            return "continue"
        elif x.lower() in ("stop", "s", "end"):
            return "stop"

    cont: str = await ask(ctx,
                          question=provide_question,
                          convert=cont_conv,
                          default_val="no",
                          timeout=provide_timeout,
                          interrupt_check=lambda x: False)

    if cont == "continue":
        return await ask(ctx,
                         question=followed_question,
                         convert=convert,
                         no_input=no_input,
                         default_val=default_val,
                         convert_failed=convert_failed,
                         timeout=follow_timeout)
    elif cont == "stop":
        raise InterruptedError
