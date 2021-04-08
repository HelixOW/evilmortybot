import discord
import aiohttp
import utilities.embeds as embeds
import structlog
from discord.ext import tasks
from utilities import KingBot, get_prefix, remove_trailing_whitespace, td_format, half_img_size
from utilities.banners import create_jp_banner, create_custom_unit_banner
from utilities.sql_helper import *
from utilities.units import image_to_discord, unit_by_vague_name, compose_icon
from utilities.image_composer import compose_unit_list, compose_awakening
from utilities.awaken import *
from utilities.tarot import *
# from utilities.kofas_scrapper import fetch_data, add_channel, fetch_data_manual
from discord.ext.commands import Context, HelpCommand, has_permissions
from datetime import datetime
from io import BytesIO
from PIL.Image import Image

token: int = 0
is_beta: bool = False
loading_image_url: str = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
author_id: int = 204150777608929280

intents = discord.Intents.default()
intents.members = True

initial_extensions = ['cogs.blackjack',
                      'cogs.cc',
                      'cogs.custom',
                      'cogs.demon',
                      'cogs.draws',
                      'cogs.list',
                      'cogs.pvp',
                      'cogs.statistics',
                      'cogs.tournament']


class CustomHelp(HelpCommand):
    async def send_bot_help(self, _):
        await self.get_destination().send(embed=embeds.Help.help)


bot: KingBot = KingBot(command_prefix=get_prefix,
                       description='..help for Help',
                       help_command=CustomHelp(),
                       intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="..help"))

    create_custom_unit_banner()
    create_jp_banner()

    # kof_task.start()

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('--------')


@bot.command()
async def add_banner_unit(ctx: Context, banner_name: str, *, units: str):
    await add_unit_to_banner(banner_name, units)
    await ctx.send(content=f"Units ({units}) added to {banner_name}")


@bot.command()
async def add_banner_rate_up_unit(ctx: Context, banner_name: str, *, units: str):
    await add_rate_up_unit_to_banner(banner_name, units)
    await ctx.send(content=f"Rate up units ({units}) added to {banner_name}")


@bot.command()
async def update(ctx: Context):
    read_units_from_db()
    read_banners_from_db()
    create_custom_unit_banner()
    create_jp_banner()
    await ctx.send(content=f"{ctx.author.mention} Updated Units & Banners")


@bot.command(no_pm=True)
async def find(ctx: Context, *, units: str = ""):
    if units.replace(" ", "") == "":
        return await ctx.send(content=f"{ctx.author.mention} -> Please provide at least 1 name `..find name1, "
                                      f"name2, ..., nameN`")
    unit_vague_name_list: List[str] = units.split(",")
    found: List[Unit] = []

    for _, ele in enumerate(unit_vague_name_list):
        ele = remove_trailing_whitespace(ele)

        try:
            pot_unit: Unit = unit_by_id(int(ele))
            if pot_unit is not None:
                found.append(pot_unit)
        except ValueError:
            found.extend(unit_by_vague_name(ele))

    if len(found) == 0:
        return await ctx.send(content=f"{ctx.author.mention} -> No units found!")

    loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Units",
                                              embed=embeds.LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_unit_list(found), "units.png"),
                   embed=discord.Embed().set_image(url="attachment://units.png"))
    await loading.delete()


@bot.command()
async def icon(ctx: Context, of: Unit):
    if len(ctx.message.attachments) == 0:
        return await ctx.send(file=await image_to_discord(of.icon))
    async with aiohttp.ClientSession() as session:
        async with session.get(ctx.message.attachments[0].url) as resp:
            with BytesIO(await resp.read()) as a:
                img: Image = await compose_icon(attribute=of.type, grade=of.grade, background=ImageLib.open(a))
                await ctx.send(file=await image_to_discord(img))


@bot.command(name="age")
async def age_cmd(ctx: Context):
    await ctx.send(
        f"{ctx.author.mention} you're on {ctx.guild.name} for {td_format((datetime.now() - ctx.author.joined_at))}")


@bot.command(name="awake")
async def awake_cmd(ctx: Context, _unit: Unit, start: Optional[int] = 0, to: Optional[int] = 6):
    data = calc_cost(_unit, min(max(start, 0), 6) + 1, min(max(to, 0), 6) + 1)
    await ctx.send(
        file=await image_to_discord(await compose_awakening(data)),
        content=f"To awaken *{_unit.name}* from **{start}*** to **{to}*** it takes:"
    )


@bot.command(name="code")
async def code_cmd(ctx: Context):
    await ctx.send(f"{ctx.author.mention}: https://github.com/WhoIsAlphaHelix/evilmortybot")


@tasks.loop(seconds=30)
async def kof_task():
    for guild in bot.guilds:
        pass
        # await fetch_data(bot, guild)


@bot.command(name="kof")
@has_permissions(manage_channels=True)
async def kof_cmd(ctx: Context):
    # await add_channel(ctx.channel)
    await ctx.send(ctx.author.mention + " added news channel!")


@bot.command(name="knews")
async def kof_news(ctx: Context):
    # await fetch_data_manual(ctx)
    pass


@bot.command(name="info")
async def info_cmd(ctx: Context, *, of: Unit):
    await ctx.send(
        file=await image_to_discord(await of.set_icon()),
        embed=(await of.info_embed()).set_thumbnail(url="attachment://image.png")
    )


def set_arsenic_log_level(level=logging.WARNING):
    lo = logging.getLogger('arsenic')

    def logger_factory():
        return lo

    structlog.configure(logger_factory=logger_factory)
    lo.setLevel(level)


def start_up_bot(token_path: str = "data/bot_token.txt", _is_beta: bool = False):
    global token, is_beta
    try:
        set_arsenic_log_level(logging.CRITICAL)

        for extension in initial_extensions:
            bot.load_extension(extension)

        read_affections_from_db()
        read_units_from_db()
        read_banners_from_db()

        with open(token_path, 'r') as token_file:
            token = token_file.read()

        for i, f_types in [(1, ["atk", "crit_ch", "crit_dmg", "pierce"]),
                           (2, ["res", "crit_def", "crit_res", "lifesteal"]),
                           (3, ["cc", "ult", "evade"]),
                           (4, ["def", "hp", "reg", "rec"])]:
            for f_type in f_types:
                food_list: List[Food] = []
                name = map_food(f_type)
                for _i in range(1, 4):
                    with ImageLib.open(f"gc/food/{f_type}_{_i}.png") as food_image:
                        food_list.append(food_image.resize((half_img_size, half_img_size)))
                tarot_food[i].append(Food(f_type, name, food_list))
                logger.log(logging.INFO, f"Added food {name}")

        is_beta = _is_beta

        bot.run(token)
    finally:
        connection.close()


if __name__ == '__main__':
    start_up_bot()
