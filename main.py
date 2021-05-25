import random

import aiohttp
from discord.ext.commands import Context

import utilities.reactions as emojis
from utilities import *
from utilities.awaken import *
from utilities.banners import create_jp_banner, create_custom_unit_banner, read_banners_from_db
from utilities.image_composer import compose_unit_list, compose_awakening
from utilities.sql_helper import *
from utilities.tarot import *
from utilities.units import image_to_discord, unit_by_vague_name, compose_icon, unit_by_id, unit_by_name_no_case

token: int = 0
is_beta: bool = False
loading_image_url: str = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
author_id: int = 204150777608929280

intents = discord.Intents.default()
intents.members = True

initial_extensions = ['cogs.custom',
                      'cogs.demon',
                      'cogs.draws',
                      'cogs.list',
                      'cogs.pvp',
                      'cogs.statistics',
                      'cogs.users']

bot: KingBot = KingBot(command_prefix=get_prefix,
                       description='..help for Help',
                       help_command=None,
                       intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="..help"))

    create_custom_unit_banner()
    create_jp_banner()

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('--------')


@bot.group(name="help")
async def bot_help(ctx: Context):
    if ctx.invoked_subcommand is None:
        return await ctx.send(embed=embeds.Help.general_help)


@bot_help.command(name="pvp")
async def pvp_help(ctx: Context):
    await ctx.send(embed=embeds.Help.pvp_help)


@bot_help.command(name="draw")
async def draw_help(ctx: Context):
    await ctx.send(embed=embeds.Help.draw_help)


@bot_help.command(name="stats")
async def stats_help(ctx: Context):
    await ctx.send(embed=embeds.Help.stats_help)


@bot_help.command(name="list")
async def list_help(ctx: Context):
    await ctx.send(embed=embeds.Help.list_help)


@bot_help.command(name="demon")
async def demon_help(ctx: Context):
    await embeds.Help.send_demon_help(ctx, "")


@bot_help.command(name="custom")
async def custom_help(ctx: Context):
    await ctx.send(embed=embeds.Help.custom_help)


@bot_help.command(name="profile")
async def profile_help(ctx: Context):
    await ctx.send(embed=embeds.Help.profile_help)


@bot.command()
async def update(ctx: Context):
    await read_units_from_db()
    await read_banners_from_db()
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
                                              embed=embeds.loading())
    await ctx.send(file=await image_to_discord(await compose_unit_list(found), "units.png"),
                   embed=embeds.DefaultEmbed().set_image(url="attachment://units.png"))
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


@bot.command(name="info")
async def info_cmd(ctx: Context, include_custom: Optional[bool] = False, *, of_name: str):
    ofs: List[Unit] = unit_by_vague_name(of_name)

    if not include_custom:
        ofs = [x for x in ofs if x not in [y for y in unit_list if y.event == Event.CUS]]

    if len(ofs) == 0:
        return await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed(
            f"No Units found who have `{of_name}` in their name!"
        ))

    await send_paged_message(
        bot,
        ctx,
        check_func=lambda x, y: y == ctx.author and str(x.emoji) in [emojis.LEFT_ARROW, emojis.RIGHT_ARROW],
        timeout=15,
        pages=[{
            "file": await x.set_icon(),
            "embed": (await x.info_embed()).set_thumbnail(url="attachment://image.png"),
            "content": None
        } for x in ofs]
    )


@info_cmd.error
async def info_error(ctx: Context, error: discord.ext.commands.CommandError):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        await ctx.send(ctx.author.mention,
                       embed=embeds.ErrorEmbed("No Unit name provided!").set_usage("info <unit name>"))


@bot.command(name="quiz")
async def quiz_cmd(ctx: Context, mode: Optional[str] = "unit"):
    if mode in ["unit", "icon", "character"]:
        unit: Unit = unit_list[random.randint(0, len(unit_list) - 1)]

        while unit.event == Event.CUS:
            unit: Unit = unit_list[random.randint(0, len(unit_list) - 1)]

        question: discord.Message = await ctx.send(ctx.author.mention,
                                                   embed=embeds.DrawEmbed(title="What Unit is this?",
                                                                          description="Enter the **__full name__**."),
                                                   file=await image_to_discord(await unit.set_icon()))

        awnser: str = await ask(ctx,
                                question=question,
                                convert=str,
                                convert_failed="No Unit like this found",
                                delete_question=False,
                                delete_awnser=False)

        if awnser is None or awnser in ["stop", "s", "e", "end", "interrupt", "i"]:
            return await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed("Interrupted game."))

        awnser: Unit = unit_by_name_no_case(awnser)

        if awnser is not None and awnser.unit_id == unit.unit_id:
            return await ctx.send(ctx.author.mention, embed=embeds.SuccessEmbed("Correct!"))

        return await ctx.send(ctx.author.mention, embed=embeds.ErrorEmbed("Wrong!", description=f"""
        Correct awnser was:
        `{unit.name}`
        """))


def start_up_bot(token_path: str = "data/bot_token.txt", _is_beta: bool = False):
    global token, is_beta
    try:
        for extension in initial_extensions:
            bot.load_extension(extension)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(read_affections_from_db())
        loop.run_until_complete(read_units_from_db())
        loop.run_until_complete(read_banners_from_db())
        loop.close()

        with open(token_path, 'r') as token_file:
            token = token_file.read()

        for i, f_types in [(1, ["atk", "crit_ch", "crit_dmg", "pierce"]),
                           (2, ["res", "crit_def", "crit_res", "lifesteal"]),
                           (3, ["cc", "ult", "evade"]),
                           (4, ["def", "hp", "reg", "rec"])]:
            for f_type in f_types:
                food_list: List[Image] = []
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
