from selenium import webdriver
from selenium.webdriver.opera.options import Options
from discord.ext.commands import Bot, Context
from discord import Guild, TextChannel
from utilities import flatten
from sqlite3 import Cursor
from utilities import connection
import discord

from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))
display.start()

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
driver: webdriver.Chrome = webdriver.Opera(options=options, executable_path="./operadriver")


async def find_update_ids():
    driver.get("https://forum.netmarble.com/kofg_en/list/4/1")

    driver.implicitly_wait(10)

    announcement_list_div = driver.find_element_by_css_selector("#articleListSubView")
    announcements = announcement_list_div.find_elements_by_css_selector("a")

    print(announcements)

    for update_notice in [x for x in announcements if x.get_attribute("href") is not None]:
        yield update_notice.get_attribute("href")


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
    link = await get_latest_update()
    driver.get(link)

    if await is_already_noticed(link):
        return

    await notice(link)

    driver.implicitly_wait(10)

    message_div = driver.find_elements_by_css_selector('.section.bbs_contents .contents_detail')
    div_elements = [e.get_text() for e in message_div.get_elements(selector="div") if e.get_text() != ""]
    elements = [e.get_text() for e in message_div.get_elements(selector="p")]
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


async def fetch_data_manual(ctx: Context):
    link = await get_latest_update()
    driver.get(link)

    driver.implicitly_wait(10)

    message_div = driver.find_element_by_css_selector('.section.bbs_contents .contents_detail')
    div_elements = [e.text for e in message_div.find_elements_by_css_selector("div") if e.text != ""]
    elements = [e.text for e in message_div.find_elements_by_css_selector("p")]
    real = []

    for s in elements:
        if s not in flatten([x.split("\n") for x in div_elements]):
            real.append(s)

    text = " \n".join(real)

    for p in [text[i: i + 1999] for i in range(0, len(text), 1999)]:
        try:
            await ctx.send(p)
        except discord.errors.HTTPException:
            pass
