from arsenic import get_session
from arsenic.browsers import Chrome
from arsenic.services import Chromedriver
from discord.ext.commands import Bot
from discord import Guild, TextChannel
from utilities import flatten
from sqlite3 import Cursor
from utilities import connection
import discord
import os

service: Chromedriver = Chromedriver(binary="./chromedriver", log_file=os.devnull)
browser: Chrome = Chrome()

browser.capabilities = {"goog:chromeOptions": {"args": ["--headless", "--disable-gpu"]}}


async def find_update_ids():
    async with get_session(service, browser) as session:
        await session.get("https://forum.netmarble.com/kofg_en/list/5/1")

        update_list = await session.wait_for_element(10, '#articleListSubView')
        update_notices = await update_list.get_elements(selector="a")

        for update_notice in [x for x in update_notices if await x.get_attribute("href") is not None]:
            yield await update_notice.get_attribute("href")


async def is_already_noticed(href: str):
    c: Cursor = connection.cursor()
    return c.execute('SELECT * FROM kof_update_notice WHERE href=?', (href,)).fetchone() is not None


async def notice(href: str):
    c: Cursor = connection.cursor()
    c.execute('INSERT OR IGNORE INTO kof_update_notice VALUES (?)', (href,))
    connection.commit()


async def get_latest_update():
    return [x async for x in find_update_ids()][0]


async def add_channel(channel: TextChannel):
    c: Cursor = connection.cursor()
    c.execute('INSERT INTO kof_news_channels VALUES (?, ?)', (channel.guild.id, channel.id))
    connection.commit()


async def find_channel(bot: Bot, guild: Guild):
    c: Cursor = connection.cursor()
    return await bot.fetch_channel(c.execute('SELECT * FROM kof_news_channels WHERE guild=?', (guild.id,)).fetchone()[1])


async def fetch_data(bot: Bot, guild: Guild):
    async with get_session(service, browser) as session:
        link = await get_latest_update()
        await session.get(link)

        if await is_already_noticed(link):
            return

        await notice(link)

        message_div = await session.wait_for_element(10, '.section.bbs_contents .contents_detail')
        div_elements = [await e.get_text() for e in await message_div.get_elements(selector="div") if await e.get_text() != ""]
        elements = [await e.get_text() for e in await message_div.get_elements(selector="p")]
        real = []

        for s in elements:
            if s not in flatten([x.split("\n") for x in div_elements]):
                real.append(s)

        text = " \n".join(real)

        for p in [text[i: i + 1999] for i in range(0, len(text), 1999)]:
            try:
                await (await find_channel(bot, guild)).send(p)
            except discord.errors.HTTPException:
                pass

