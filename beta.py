import utilities.embeds as embeds
import utilities.sql_helper as sql
from utilities.banner_data import *
from utilities.image_composer import *
from utilities.sql_helper import *
from utilities.unit_data import *

TOKEN = 0
IS_BETA = False
IMG_SIZE = 150
LOADING_IMAGE_URL = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
AUTHOR_HELIX_ID = 204150777608929280

intents = discord.Intents.default()
intents.members = True


class LeaderboardType(Enum):
    LUCK = "luck"
    MOST_SSR = "ssrs"
    MOST_UNITS = "units"
    MOST_SHAFTS = "shafts"


class CustomHelp(HelpCommand):
    async def send_bot_help(self, mapping):
        await self.get_destination().send(embed=embeds.HELP_EMBED_1)
        await self.get_destination().send(embed=embeds.HELP_EMBED_2)


class UnitConverter(commands.Converter):
    async def convert(self, ctx, argument):
        return unit_by_vague_name(argument)[0]


class MemberMentionConverter(commands.Converter):
    async def convert(self, ctx, argument):
        return ctx.message.mentions[0]


TEAM_REROLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
PVP_REROLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣️"]

TEAM_TIME_CHECK = []
PVP_TIME_CHECK = []

DEMON_ROLES = {}
DEMON_MESSAGES = {}
DEMON_CONTRACTS = {}
DEMON_OFFER_MESSAGES = {}

BOT = commands.Bot(command_prefix='..', description='..help for Help', help_command=CustomHelp(), intents=intents)


def map_leaderboard(raw_leaderboard: str) -> LeaderboardType:
    raw_leaderboard = raw_leaderboard.replace(" ", "").lower()
    if raw_leaderboard in ["ssr", "ssrs", "mostssr", "mostssrs"]:
        return LeaderboardType.MOST_SSR
    if raw_leaderboard in ["units", "unit", "mostunits", "mostunit"]:
        return LeaderboardType.MOST_UNITS
    if raw_leaderboard in ["shaft", "shafts", "mostshafts", "mostshaft"]:
        return LeaderboardType.MOST_SHAFTS
    return LeaderboardType.LUCK


async def get_top_users(guild: discord.Guild, action: LeaderboardType = LeaderboardType.LUCK) -> List[dict]:
    if action == LeaderboardType.MOST_SHAFTS:
        return get_top_shafts(BOT, guild)
    elif action == LeaderboardType.LUCK:
        return get_top_lucky(BOT, guild)
    elif action == LeaderboardType.MOST_SSR:
        return get_top_ssrs(BOT, guild)
    elif action == LeaderboardType.MOST_UNITS:
        return get_top_units(BOT, guild)


def get_matching_units(grades: List[Grade] = None,
                       types: List[Type] = None,
                       races: List[Race] = None,
                       events: List[Event] = None,
                       affections: List[str] = None,
                       names: List[str] = None,
                       jp: bool = False) -> List[Unit]:
    if races is None or races == []:
        races = RACES.copy()
    if grades is None or grades == []:
        grades = GRADES.copy()
    if types is None or types == []:
        types = TYPES.copy()
    if events is None or events == []:
        events = EVENTS.copy()
    if affections is None or affections == []:
        affections = [x.lower().replace(" ", "") for x in AFFECTIONS]
    if names is None or names == []:
        names = [x.name.lower().replace(" ", "") for x in UNITS]

    def test(x):
        return x.race in races and x.type in types and x.grade in grades and x.event in events and x.affection.lower().replace(
            " ", "") in affections \
               and x.name.lower().replace(" ", "") in names and (x.is_jp if jp else True)

    possible_units = [x for x in UNITS if test(x)]

    if len(possible_units) == 0:
        raise LookupError

    return possible_units


def get_random_unit(grades: List[Grade] = None,
                    types: List[Type] = None,
                    races: List[Race] = None,
                    events: List[Event] = None,
                    affections: List[str] = None,
                    names: List[str] = None,
                    jp: bool = False) -> Unit:
    possible_units = get_matching_units(grades=grades,
                                        types=types,
                                        races=races,
                                        events=events,
                                        affections=affections,
                                        names=names,
                                        jp=jp)
    return possible_units[ra.randint(0, len(possible_units) - 1)]


def remove_trailing_whitespace(to_remove: str):
    while to_remove.startswith(" "):
        to_remove = to_remove[1:]

    while to_remove.endswith(" "):
        to_remove = to_remove[:-1]
    return to_remove


def remove_beginning_ignore_case(remove_from: str, beginning: str):
    if remove_from.lower().startswith(beginning.lower()):
        return remove_from[len(beginning):]
    return remove_from


def parse_arguments(given_args: str, list_seperator: str = "&") -> dict:
    args = given_args.split(list_seperator)
    parsed_races = []
    parsed_names = []
    parsed_race_count = {
        Race.HUMAN: 0,
        Race.FAIRY: 0,
        Race.GIANT: 0,
        Race.UNKNOWN: 0,
        Race.DEMON: 0,
        Race.GODDESS: 0
    }
    parsed_grades = []
    parsed_types = []
    parsed_events = []
    parsed_affections = []
    parsed_url = ""
    parsed_new_name = ""
    parsed_owner = 0
    jp = False
    unparsed = []

    for _, ele in enumerate(args):
        arg = remove_trailing_whitespace(ele)

        if arg.lower().startswith("new_name:"):
            parsed_new_name = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "new_name:"))
            continue

        if arg.lower().startswith("url:"):
            parsed_url = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "url:"))
            continue

        if arg.lower().startswith("jp") or arg.lower().startswith("kr"):
            jp = True
            continue

        if arg.lower().startswith("owner:"):
            parsed_owner = int(remove_trailing_whitespace(remove_beginning_ignore_case(arg, "owner:"))[3:-1])
            continue

        if arg.lower().startswith("name:"):
            name_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "name:"))

            if name_str.startswith("!"):
                parsed_names = [x.name for x in UNITS if
                                x.name.lower() != remove_beginning_ignore_case(name_str, "!").lower()]
            else:
                parsed_names = [remove_trailing_whitespace(x) for x in name_str.split(",")]
            continue

        if arg.lower().startswith("race:"):
            race_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "race:").lower())

            if race_str.startswith("!"):
                parsed_races = [x for x in RACES if x.value != remove_beginning_ignore_case(race_str, "!")]
            else:
                races_with_count = [remove_trailing_whitespace(x) for x in race_str.split(",")]
                for _, element in enumerate(races_with_count):
                    apr = element.split("*")

                    if len(apr) == 2:
                        parsed_races.append(map_race(apr[1]))
                        parsed_race_count[map_race(apr[1])] += int(apr[0])
                    else:
                        parsed_races.append(map_race(element))
            continue

        if arg.lower().startswith("grade:"):
            grade_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "grade:").lower())

            if grade_str.startswith("!"):
                parsed_grades = [x for x in GRADES if x.value != remove_beginning_ignore_case(grade_str, "!")]
            else:
                parsed_grades = [map_grade(remove_trailing_whitespace(x)) for x in grade_str.split(",")]
            continue

        if arg.lower().startswith("type:"):
            type_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "type:").lower())

            if type_str.startswith("!"):
                parsed_types = [x for x in TYPES if x.value != remove_beginning_ignore_case(type_str, "!")]
            else:
                parsed_types = [map_attribute(remove_trailing_whitespace(x)) for x in type_str.split(",")]
            continue

        if arg.lower().startswith("event:"):
            event_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "event:").lower())

            if event_str.startswith("!"):
                parsed_events = [x for x in EVENTS if x.value != remove_beginning_ignore_case(event_str, "!")]
            else:
                parsed_events = [map_event(remove_trailing_whitespace(x)) for x in event_str.split(",")]
            continue

        if arg.lower().startswith("affection:"):
            affection_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "affection:").lower())

            if affection_str.startswith("!"):
                parsed_affections = [x for x in AFFECTIONS if x != remove_beginning_ignore_case(affection_str, "!")]
            else:
                parsed_affections = [map_affection(remove_trailing_whitespace(x)) for x in affection_str.split(",")]
            continue

        unparsed.append(arg.lower())

    return {
        "name": parsed_names,
        "race": parsed_races,
        "max race count": parsed_race_count,
        "grade": parsed_grades,
        "type": parsed_types,
        "event": parsed_events,
        "affection": parsed_affections,
        "updated_name": parsed_new_name,
        "url": parsed_url,
        "owner": parsed_owner,
        "jp": jp,
        "unparsed": unparsed
    }


def replace_duplicates(criteria: dict, team_to_deduplicate: List[Unit]):
    team_simple_names = ["", "", "", ""]
    team_races = {
        Race.HUMAN: 0,
        Race.FAIRY: 0,
        Race.GIANT: 0,
        Race.UNKNOWN: 0,
        Race.DEMON: 0,
        Race.GODDESS: 0
    }
    max_races = criteria["max race count"]

    checker = 0
    for i in max_races:
        checker += max_races[i]

    if checker not in (4, 0):
        raise ValueError("Too many Races")

    def check_races(abba):
        if checker == 0:
            return True
        if team_races[team_to_deduplicate[abba].race] >= max_races[team_to_deduplicate[abba].race]:
            if team_to_deduplicate[abba].race in criteria["race"]:
                criteria["race"].remove(team_to_deduplicate[abba].race)
            team_to_deduplicate[abba] = get_random_unit(races=criteria["race"], grades=criteria["grade"],
                                                        types=criteria["type"],
                                                        events=criteria["event"], affections=criteria["affection"],
                                                        names=criteria["name"], jp=criteria["jp"])
            return False
        team_races[team_to_deduplicate[abba].race] += 1
        return True

    def check_names(abba):
        if team_to_deduplicate[abba].simple_name not in team_simple_names:
            team_simple_names[abba] = team_to_deduplicate[abba].simple_name
            return True
        team_to_deduplicate[abba] = get_random_unit(races=criteria["race"], grades=criteria["grade"],
                                                    types=criteria["type"],
                                                    events=criteria["event"], affections=criteria["affection"],
                                                    names=criteria["name"], jp=criteria["jp"])
        return False

    for i, _ in enumerate(team_to_deduplicate):
        for _ in range(500):
            if check_names(i) and check_races(i):
                break

        if team_simple_names[i] == "":
            raise ValueError("Not enough Units available")


async def build_menu(ctx, prev_message, page: int = 0):
    summon_menu_emojis = ["⬅️", "1️⃣", "🔟" if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else "5️⃣", "🐋",
                          "ℹ️", "➡️"]
    await prev_message.clear_reactions()
    draw = prev_message

    await draw.edit(content=f"{ctx.message.author.mention}",
                    embed=discord.Embed(
                        title=ALL_BANNERS[page].pretty_name
                    ).set_image(url=ALL_BANNERS[page].background))

    if page == 0:
        await asyncio.gather(
            draw.add_reaction(summon_menu_emojis[1]),
            draw.add_reaction(summon_menu_emojis[2]),
            draw.add_reaction(summon_menu_emojis[3]),
            draw.add_reaction(summon_menu_emojis[4]),
            draw.add_reaction(summon_menu_emojis[5]),
        )
    elif page == len(ALL_BANNERS) - 1:
        await asyncio.gather(
            draw.add_reaction(summon_menu_emojis[0]),
            draw.add_reaction(summon_menu_emojis[1]),
            draw.add_reaction(summon_menu_emojis[2]),
            draw.add_reaction(summon_menu_emojis[3]),
            draw.add_reaction(summon_menu_emojis[4]),
        )
    else:
        await asyncio.gather(
            draw.add_reaction(summon_menu_emojis[0]),
            draw.add_reaction(summon_menu_emojis[1]),
            draw.add_reaction(summon_menu_emojis[2]),
            draw.add_reaction(summon_menu_emojis[3]),
            draw.add_reaction(summon_menu_emojis[4]),
            draw.add_reaction(summon_menu_emojis[5]),
        )

    try:
        def check_banner(added_reaction, user):
            return user == ctx.message.author and str(added_reaction.emoji) in summon_menu_emojis

        reaction, _ = await BOT.wait_for("reaction_add", check=check_banner)

        if "➡️" in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page + 1)
        elif "⬅️" in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page - 1)
        elif ("🔟" if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else "5️⃣") in str(reaction.emoji):
            await draw.delete()
            await multi(ctx, person=ctx.message.author, banner_name=ALL_BANNERS[page].name[0])
        elif "1️⃣" in str(reaction.emoji):
            await draw.delete()
            await single(ctx, person=ctx.message.author, banner_name=ALL_BANNERS[page].name[0])
        elif "🐋" in str(reaction.emoji):
            await draw.delete()
            await shaft(ctx, person=ctx.message.author, banner_name=ALL_BANNERS[page].name[0])
        elif "ℹ️" in str(reaction.emoji):
            await draw.delete()
            await banner(ctx, banner_name=ALL_BANNERS[page].name[0])
    except asyncio.TimeoutError:
        pass


def parse_custom_unit_args(arg: str):
    all_parsed = parse_arguments(arg)

    return {
        "name": all_parsed["name"][0] if len(all_parsed["name"]) > 0 else "",
        "updated_name": all_parsed["updated_name"],
        "owner": all_parsed["owner"],
        "url": all_parsed["url"],
        "race": all_parsed["race"][0] if len(all_parsed["race"]) > 0 else Race.UNKNOWN,
        "grade": all_parsed["grade"][0] if len(all_parsed["grade"]) > 0 else Grade.SSR,
        "type": all_parsed["type"][0] if len(all_parsed["type"]) > 0 else Type.RED,
        "affection": all_parsed["affection"][0] if len(all_parsed["affection"]) > 0 else "none"
    }


def get_demon_role(guild_id: int, demon_type: str = "red") -> discord.Role:
    guild_roles = DEMON_ROLES[guild_id]
    if guild_roles is not None and len(guild_roles[demon_type]) != 0:
        return guild_roles[demon_type][0]
    return None


def parse_demon_roles():
    DEMON_ROLES.clear()
    for guild in BOT.guilds:
        red_demons = [x for x in guild.roles if "red" in x.name.lower() and "demon" in x.name.lower()]
        grey_demons = [x for x in guild.roles if "grey" in x.name.lower() and "demon" in x.name.lower()]
        crimson_demons = [x for x in guild.roles if
                          ("crimson" in x.name.lower() or "howlex" in x.name.lower()) and "demon" in x.name.lower()]

        DEMON_ROLES[guild.id] = {
            "red": red_demons,
            "grey": grey_demons,
            "crimson": crimson_demons
        }


def mutual_guilds(person: discord.User):
    return [g for g in BOT.guilds if g.get_member(person.id) is not None]


def shared_guilds(person1: discord.User, person2: discord.User):
    return [x for x in mutual_guilds(person1) if x in mutual_guilds(person2)]


class Dict2Obj(object):
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])


@BOT.event
async def on_ready():
    await BOT.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="..help"))

    create_custom_unit_banner()
    parse_demon_roles()

    print('Logged in as')
    print(BOT.user.name)
    print(BOT.user.id)
    print('--------')


@BOT.event
async def on_guild_join(guild):
    parse_demon_roles()


@BOT.group()
async def top(ctx):
    if ctx.invoked_subcommand is None:
        return await top_luck(ctx)


@top.command(name="luck", aliases=["lucky", "luckiness"])
async def top_luck(ctx):
    top_users = await get_top_users(ctx.message.guild, LeaderboardType.LUCK)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )

    await ctx.send(
        embed=discord.Embed(
            title=f"Luckiest Members in {ctx.message.guild.name}",
            description='\n'.join([
                "**{}.** {} with a *{}%* SSR drop rate in their pulls. (Total: *{}*)".format(top_user["place"],
                                                                                             top_user["name"],
                                                                                             top_user["luck"],
                                                                                             top_user["pull-amount"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.message.guild.icon_url)
    )


@top.command(name="ssrs", aliases=["ssr"])
async def top_ssrs(ctx):
    top_users = await get_top_users(ctx.message.guild, LeaderboardType.MOST_SSR)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )
    await ctx.send(
        embed=discord.Embed(
            title=f"Members with most drawn SSRs in {ctx.message.guild.name}",
            description='\n'.join([
                "**{}.** {} with *{} SSRs*. (Total: *{}*)".format(top_user["place"], top_user["name"],
                                                                  top_user["ssrs"], top_user["pull-amount"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.message.guild.icon_url)
    )


@top.command(name="units", aliases=["unit"])
async def top_units(ctx):
    top_users = await get_top_users(ctx.message.guild, LeaderboardType.MOST_UNITS)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )
    await ctx.send(
        embed=discord.Embed(
            title=f"Members with most drawn Units in {ctx.message.guild.name}",
            description='\n'.join([
                "**{}.** {} with *{} Units*".format(
                    top_user["place"], top_user["name"], top_user["pull-amount"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.message.guild.icon_url)
    )


@top.command(name="shafts", aliases=["shaft"])
async def top_shafts(ctx):
    top_users = await get_top_users(ctx.message.guild, LeaderboardType.MOST_SHAFTS)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )
    return await ctx.send(
        embed=discord.Embed(
            title=f"Members with most Shafts in {ctx.message.guild.name}",
            description='\n'.join([
                "**{}.** {} with *{} Shafts*".format(
                    top_user["place"], top_user["name"], top_user["shafts"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.message.guild.icon_url)
    )


STAT_HELPER = {}


@BOT.group()
async def stats(ctx, person: typing.Optional[discord.Member]):
    if person is None:
        person = ctx.message.author

    data = await get_user_pull(person)
    ssrs = data["ssr_amount"] if len(data) != 0 else 0
    pulls = data["pull_amount"] if len(data) != 0 else 0
    shafts = data["shafts"] if len(data) != 0 else 0
    percent = round((ssrs / pulls if len(data) != 0 else 0) * 100, 2)

    STAT_HELPER[ctx] = {
        "data": data,
        "ssrs": ssrs,
        "pulls": pulls,
        "shafts": shafts,
        "percent": percent,
        "person": person
    }


@stats.command(name="luck", aliases=["lucky", "luckiness"])
async def stats_luck(ctx):
    person = STAT_HELPER[ctx]["person"]
    percent = STAT_HELPER[ctx]["percent"]
    ssrs = STAT_HELPER[ctx]["ssrs"]
    pulls = STAT_HELPER[ctx]["pulls"]
    await ctx.send(
        content=f"{person.mention}'s luck:" if person == ctx.message.author
        else f"{ctx.message.author.mention}: {person.display_name}'s luck:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently got a *{percent}%* SSR droprate in their pulls, with *{ssrs} SSRs* in *{pulls} Units*"
        )
    )


@stats.command(name="ssrs", aliases=["ssr"])
async def stats_ssrs(ctx):
    person = STAT_HELPER[ctx]["person"]
    ssrs = STAT_HELPER[ctx]["ssrs"]
    await ctx.send(
        content=f"{person.mention}'s SSRs:" if person == ctx.message.author
        else f"{ctx.message.author.mention}: {person.display_name}'s SSRs:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently has *{ssrs} SSRs*"
        )
    )


@stats.command(name="units", aliases=["unit"])
async def stats_units(ctx):
    person = STAT_HELPER[ctx]["person"]
    pulls = STAT_HELPER[ctx]["pulls"]
    await ctx.send(
        content=f"{person.mention}'s Units:" if person == ctx.message.author
        else f"{ctx.message.author.mention}: {person.display_name}'s Units:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently has *{pulls} Units*"
        )
    )


@stats.command(name="shafts", aliases=["shaft"])
async def stats_shafts(ctx):
    person = STAT_HELPER[ctx]["person"]
    shafts = STAT_HELPER[ctx]["shafts"]
    await ctx.send(
        content=f"{person.mention}'s Shafts:" if person == ctx.message.author
        else f"{ctx.message.author.mention}: {person.display_name}'s Shafts:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently got shafted {shafts}x"
        )
    )


# ..unit
@BOT.command(no_pm=True)
async def unit(ctx, *, args: str = ""):
    attributes = parse_arguments(args)
    try:
        random_unit = get_random_unit(grades=attributes["grade"],
                                      types=attributes["type"],
                                      races=attributes["race"],
                                      events=attributes["event"],
                                      affections=attributes["affection"],
                                      names=attributes["name"],
                                      jp=attributes["jp"])

        await random_unit.set_icon()

        await ctx.send(content=f"{ctx.message.author.mention} this is your unit",
                       embed=discord.Embed(title=random_unit.name, colour=random_unit.discord_color())
                       .set_image(url="attachment://unit.png"),
                       file=await random_unit.discord_icon())
    except LookupError:
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=embeds.UNIT_LOOKUP_ERROR_EMBED)


# ..pvp
@BOT.command(no_pm=True)
async def pvp(ctx, enemy: discord.Member, attr: str = ""):
    attr = parse_arguments(attr)
    proposed_team_p1 = [
        get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                        affections=attr["affection"], names=attr["name"], jp=attr["jp"])
        for _ in range(4)]
    proposed_team_p2 = [
        get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                        affections=attr["affection"], names=attr["name"], jp=attr["jp"])
        for _ in range(4)]

    try:
        replace_duplicates(attr, proposed_team_p1)
        replace_duplicates(attr, proposed_team_p2)
    except ValueError as e:
        return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                              embed=embeds.TEAM_LOOKUP_ERROR_EMBED)

    player1 = ctx.message.author

    if player1 in PVP_TIME_CHECK or enemy in PVP_TIME_CHECK:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.PVP_COOLDOWN_ERROR_EMBED)

    changed_units = {
        0: [],
        1: [],
        2: [],
        3: []
    }

    async def send(player: discord.Member, last_message=None):
        if last_message is not None:
            await last_message.delete()

        if player not in PVP_TIME_CHECK:
            PVP_TIME_CHECK.append(player)

        loading_message = await ctx.send(embed=embeds.LOADING_EMBED)
        team_message = await ctx.send(file=await image_to_discord(
            await compose_team(rerolled_team=proposed_team_p1 if player == player1 else proposed_team_p2,
                               re_units=changed_units),
            "team.png"),
                                      content=f"{player.mention} please check if you have those units",
                                      embed=discord.Embed().set_image(url="attachment://team.png"))
        await loading_message.delete()

        for emoji in TEAM_REROLL_EMOJIS:
            await team_message.add_reaction(emoji)

        def check_reroll(added_reaction, from_user):
            return str(added_reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"] and added_reaction.message == team_message \
                   and from_user == player

        try:
            reaction, user = await BOT.wait_for("reaction_add", check=check_reroll, timeout=5)
            reaction = str(reaction.emoji)

            c_index = -1
            if "1️⃣" in reaction:
                c_index = 0
            elif "2️⃣" in reaction:
                c_index = 1
            elif "3️⃣" in reaction:
                c_index = 2
            elif "4️⃣" in reaction:
                c_index = 3

            if user == player1:
                changed_units[c_index].append(proposed_team_p1[c_index])
                proposed_team_p1[c_index] = get_random_unit(races=attr["race"], grades=attr["grade"],
                                                            types=attr["type"],
                                                            events=attr["event"],
                                                            affections=attr["affection"], names=attr["name"],
                                                            jp=attr["jp"])
                replace_duplicates(attr, proposed_team_p1)
            else:
                changed_units[c_index].append(proposed_team_p2[c_index])
                proposed_team_p2[c_index] = get_random_unit(races=attr["race"], grades=attr["grade"],
                                                            types=attr["type"],
                                                            events=attr["event"],
                                                            affections=attr["affection"], names=attr["name"],
                                                            jp=attr["jp"])
                replace_duplicates(attr, proposed_team_p2)

            await send(player=user, last_message=team_message)
        except asyncio.TimeoutError:
            if player in PVP_TIME_CHECK:
                PVP_TIME_CHECK.remove(player)
            await team_message.delete()

    await send(player1)

    changed_units = {0: [], 1: [], 2: [], 3: []}

    await send(enemy)

    await ctx.send(file=await image_to_discord(await compose_pvp(player1=player1, player2=enemy,
                                                                 team1=proposed_team_p1,
                                                                 team2=proposed_team_p2),
                                               "pvp.png"))


# ..team
@BOT.command(no_pm=True)
async def team(ctx, *, args: str = ""):
    attr = parse_arguments(args)

    try:
        proposed_team = [
            get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                            affections=attr["affection"], names=attr["name"], jp=attr["jp"])
            for _ in range(4)]

        try:
            replace_duplicates(criteria=attr, team_to_deduplicate=proposed_team)
        except ValueError as e:
            return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                                  embed=embeds.TEAM_LOOKUP_ERROR_EMBED)

        if ctx.message.author in TEAM_TIME_CHECK:
            return await ctx.send(content=f"{ctx.message.author.mention}",
                                  embed=embeds.TEAM_COOLDOWN_ERROR_EMBED)

        changed_units = {
            0: [],
            1: [],
            2: [],
            3: []
        }

        async def send_message(last_team_message=None):
            if last_team_message is not None:
                await last_team_message.delete()

            if ctx.message.author not in TEAM_TIME_CHECK:
                TEAM_TIME_CHECK.append(ctx.message.author)
            loading_message = await ctx.send(embed=embeds.LOADING_EMBED)
            team_message = await ctx.send(file=await image_to_discord(await compose_team(
                rerolled_team=proposed_team, re_units=changed_units
            ),
                                                                      "units.png"),
                                          content=f"{ctx.message.author.mention} this is your team",
                                          embed=discord.Embed().set_image(url="attachment://units.png"))
            await loading_message.delete()
            for emoji in TEAM_REROLL_EMOJIS:
                await team_message.add_reaction(emoji)

            def check_reroll(added_reaction, user):
                return user == ctx.message.author and str(added_reaction.emoji) in TEAM_REROLL_EMOJIS \
                       and added_reaction.message == team_message

            try:
                reaction, _ = await BOT.wait_for("reaction_add", check=check_reroll, timeout=5)
                reaction = str(reaction.emoji)

                c_index = -1
                if "1️⃣" in reaction:
                    c_index = 0
                elif "2️⃣" in reaction:
                    c_index = 1
                elif "3️⃣" in reaction:
                    c_index = 2
                elif "4️⃣" in reaction:
                    c_index = 3

                changed_units[c_index].append(proposed_team[c_index])
                proposed_team[c_index] = get_random_unit(races=attr["race"], grades=attr["grade"],
                                                         types=attr["type"],
                                                         events=attr["event"], affections=attr["affection"],
                                                         names=attr["name"],
                                                         jp=attr["jp"])

                replace_duplicates(criteria=attr, team_to_deduplicate=proposed_team)
                await send_message(last_team_message=team_message)
            except asyncio.TimeoutError:
                if ctx.message.author in TEAM_TIME_CHECK:
                    TEAM_TIME_CHECK.remove(ctx.message.author)
                await team_message.clear_reactions()

        await send_message()
    except LookupError:
        await ctx.send(content=f"{ctx.message.author.mention}",
                       embed=embeds.TEAM_LOOKUP_ERROR_EMBED)


# ..multi
@BOT.command(no_pm=True)
async def multi(ctx, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author

    from_banner = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )

    draw = await ctx.send(embed=embeds.LOADING_EMBED.set_image(url=LOADING_IMAGE_URL))

    img = await compose_multi_draw(from_banner=from_banner, user=person) if from_banner.banner_type == BannerType.ELEVEN \
        else await compose_five_multi_draw(from_banner=from_banner, user=person)
    await ctx.send(file=await image_to_discord(img, "units.png"),
                   content=f"{person.mention} this is your multi" if person is ctx.message.author
                   else f"{person.mention} this is your multi coming from {ctx.message.author.mention}",
                   embed=discord.Embed(title=f"{from_banner.pretty_name} "
                                             f"({11 if from_banner.banner_type == BannerType.ELEVEN else 5}x summon)")
                   .set_image(url="attachment://units.png"))
    return await draw.delete()


# ..summon
@BOT.command(no_pm=True)
async def summon(ctx):
    draw = await ctx.send(embed=embeds.LOADING_EMBED)
    await build_menu(ctx, prev_message=draw)


# ..single
@BOT.command(no_pm=True)
async def single(ctx, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author
    from_banner = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"))

    return await ctx.send(file=await compose_draw(from_banner, person),
                          content=f"{person.mention} this is your single" if person is ctx.message.author
                          else f"{person.mention} this is your single coming from {ctx.message.author.mention}",
                          embed=discord.Embed(title=f"{from_banner.pretty_name} (1x summon)").set_image(
                              url="attachment://unit.png"))


# ..shaft
@BOT.command(no_pm=True)
async def shaft(ctx, person: typing.Optional[MemberMentionConverter],
                unit_name: typing.Optional[str] = "Helix is awesome", *, banner_name: str = "banner 1"):
    if person is None:
        person = ctx.message.author

    from_banner = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(
                                  title="Error",
                                  colour=discord.Color.dark_red(),
                                  description=f"Can't find the \"{banner_name}\" banner"
                              ))

    unit_ssr = False
    if unit_name.startswith("ssr:"):
        unit_ssr = True
        unit_name = unit_name.replace("ssr:", "")

    possible_units = [a.unit_id for a in unit_by_vague_name(unit_name)]

    if len(possible_units) != 0 and len(
            [a for a in possible_units if a in [b.unit_id for b in from_banner.all_units]]) == 0:
        possible_other_banner = None
        for b1 in ALL_BANNERS:
            matching_units = [x for x in b1.all_units if x.unit_id in possible_units]
            if len(matching_units) > 0:
                possible_other_banner = b1
                break
        from_banner = possible_other_banner

    if from_banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(
                                  title="Error",
                                  colour=discord.Color.dark_red(),
                                  description=f"Can't find any banner with {unit_name} in it"
                              ))

    if not from_banner.shaftable:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(
                                  title="Error",
                                  colour=discord.Color.dark_red(),
                                  description=f"Can't get shafted on the \"{from_banner.pretty_name}\" banner"
                              ))

    unit_to_draw = [a.unit_id for a in unit_by_vague_name(unit_name)
                    if a.unit_id in [b.unit_id for b in from_banner.all_units]]

    draw = await ctx.send(
        content=f"{person.mention} this is your shaft" if person is ctx.message.author
        else f"{person.mention} this is your shaft coming from {ctx.message.author.mention}",
        embed=discord.Embed(
            title="Shafting..."
        ).set_image(url=LOADING_IMAGE_URL))

    rang = 11 if from_banner.banner_type == BannerType.ELEVEN else 5

    async def has_ssr(du: List[Unit]) -> bool:
        for u in du:
            if u.grade == Grade.SSR and len(unit_to_draw) == 0:
                return True

            if u.unit_id in unit_to_draw:
                if unit_ssr:
                    if u.grade == Grade.SSR:
                        return True
                else:
                    return True
        return False

    async def loop():
        i = 0
        drawn_units = [(await unit_with_chance(from_banner, person)) for _ in range(rang)]
        drawn_ssrs = [x for x in drawn_units if x.grade == Grade.SSR]

        while not await has_ssr(drawn_units) and i < 1000:
            i += 1
            drawn_units = [(await unit_with_chance(from_banner, person)) for _ in range(rang)]
            drawn_ssrs.extend([x for x in drawn_units if x.grade == Grade.SSR])

        return i, drawn_units, drawn_ssrs

    shafts_and_units = await loop()

    await ctx.send(
        file=await image_to_discord(
            await compose_unit_multi_draw(units=shafts_and_units[1],
                                          ssrs=shafts_and_units[2]) if from_banner.banner_type == BannerType.ELEVEN
            else await compose_unit_five_multi_draw(units=shafts_and_units[1]),
            "units.png"),
        content=f"{person.mention}" if person is ctx.message.author
        else f"{person.mention} coming from {ctx.message.author.mention}",
        embed=discord.Embed(
            title=f"{from_banner.pretty_name} ({rang}x summon)",
            description=f"Shafted {shafts_and_units[0]} times \n This is your final pull").set_image(
            url="attachment://units.png"))
    await draw.delete()
    await add_shaft(person, shafts_and_units[0])


@BOT.group(no_pm=True)
async def custom(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"{ctx.message.author.mention}:", embed=embeds.CUSTOM_HELP_EMBED)


@custom.command(name="add", aliases=["create", "+"])
async def custom_create(ctx, *, args: typing.Optional[str] = ""):
    data = parse_custom_unit_args(args)

    if data["url"] == "" or data["name"] == "" or data["type"] is None or data["grade"] is None:
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=embeds.CUSTOM_ADD_COMMAND_USAGE_EMBED)

    async with aiohttp.ClientSession() as session:
        async with session.get(data["url"]) as resp:
            with BytesIO(await resp.read()) as image_bytes:
                icon = await compose_icon(attribute=data["type"], grade=data["grade"],
                                          background=Image.open(image_bytes))

                await ctx.send(
                    file=await image_to_discord(img=icon, image_name="unit.png"),
                    content=f"{ctx.message.author.mention} this is your created unit",
                    embed=discord.Embed(
                        title=data["name"],
                        color=discord.Color.red() if data["type"] == Type.RED
                        else discord.Color.blue() if data["type"] == Type.BLUE
                        else discord.Color.green()
                    ).set_image(url="attachment://unit.png"))

                if data["race"] is None:
                    data["race"] = Race.UNKNOWN

                if data["affection"] is None:
                    data["affection"] = Affection.NONE.value

                await add_custom_unit(name=data["name"],
                                      type_enum=data["type"],
                                      grade=data["grade"],
                                      race=data["race"],
                                      affection_str=data["affection"],
                                      url=data["url"],
                                      creator=ctx.message.author.id)


@custom.command(name="remove", aliases=["delete", "-"])
async def custom_remove(ctx, *, args: typing.Optional[str] = ""):
    data = parse_custom_unit_args(args)
    if data["name"] == "":
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=embeds.CUSTOM_REMOVE_COMMAND_USAGE_EMBED)

    edit_unit = unit_by_name(data["name"])

    if int(edit_unit.simple_name) != ctx.message.author.id:
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=discord.Embed(
            title="Error with ..custom remove", colour=discord.Color.dark_red(),
            description=f"**{edit_unit.name}** wasn't created by you!"))

    await remove_custom_unit(data["name"])
    UNITS.remove(edit_unit)
    create_custom_unit_banner()
    return await ctx.send(content=f"{ctx.message.author.mention}", embed=embeds.CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED)


@custom.command(name="list")
async def custom_list(ctx, *, args: typing.Optional[str] = ""):
    data = parse_custom_unit_args(args)
    if data["owner"] == 0:
        return await list_units(ctx, criteria="event: custom")

    unit_list = []
    async for row in parse_custom_unit_list(data["owner"]):
        unit_list.append(unit_by_id(-1 * row[0]))

    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=embeds.LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_unit_list(unit_list), "units.png"),
                   embed=discord.Embed().set_image(url="attachment://units.png"))
    await loading.delete()


@custom.command(name="edit")
async def custom_edit(ctx, *, args: typing.Optional[str] = ""):
    data = parse_custom_unit_args(args)
    if data["name"] == "":
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_USAGE_EMBED)

    edit_unit = unit_by_name(data["name"])

    if int(edit_unit.simple_name) != ctx.message.author.id:
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=discord.Embed(
            title="Error with ..custom remove", colour=discord.Color.dark_red(),
            description=f"**{edit_unit.name}** wasn't created by you!"))

    to_set = []
    values = []
    if data["grade"] is not None:
        edit_unit.grade = data["grade"]
        to_set.append("grade=?")
        values.append(data["grade"].value)
    if data["owner"] != 0:
        to_set.append("creator=?")
        values.append(data["owner"])
    if data["type"] is not None:
        edit_unit.type = data["type"]
        to_set.append("type=?")
        values.append(data["type"].value)
    if data["updated_name"] != "":
        edit_unit.name = data["updated_name"]
        to_set.append("name=?")
        values.append(data["updated_name"])
    if data["url"] != "":
        edit_unit.icon_path = data["url"]
        to_set.append("url=?")
        values.append(data["url"])
    if data["race"] is not None:
        edit_unit.race = data["race"]
        to_set.append("race=?")
        values.append(data["race"].value)
    if data["affection"] is not None:
        edit_unit.affection = data["affection"]
        to_set.append("affection=?")
        values.append(data["affection"])

    if len(to_set) == 0:
        return await ctx.send(content=f"{ctx.message.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)

    to_set = ", ".join(to_set)

    values.append(data["name"])
    await edit_custom_unit(to_set, values)

    await edit_unit.refresh_icon()
    return await ctx.send(content=f"{ctx.message.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)


# ..crop
@BOT.command(no_pm=True)
async def crop(ctx, file_url=None, starting_width=0, starting_height=0, ending_width=75, ending_height=75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.CROP_COMMAND_USAGE_ERROR_EMBED)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            await ctx.send(content=f"{ctx.message.author.mention} this is your cropped image",
                           file=await image_to_discord(
                               img.crop((starting_width, starting_height, ending_width, ending_height)),
                               "cropped.png"),
                           embed=discord.Embed().set_image(url="attachment://cropped.png"))


# ..resize
@BOT.command(no_pm=True)
async def resize(ctx, file_url=None, width=75, height=75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.RESIZE_COMMAND_USAGE_ERROR_EMBED)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            await ctx.send(content=f"{ctx.message.author.mention} this is your resized image",
                           file=await image_to_discord(img.resize((width, height)), "resized.png"),
                           embed=discord.Embed().set_image(url="attachment://resized.png"))


@BOT.group(name="list", no_pm=True)
async def cmd_list(ctx):
    if ctx.invoked_subcommand is None:
        return await list_units(ctx)


@cmd_list.command(name="unit", aliases=["units"])
async def list_units(ctx, units_per_page: int = 5, *, criteria: str = "event: custom"):
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=embeds.LOADING_EMBED)
    attr = parse_arguments(criteria)
    matching_units = get_matching_units(races=attr["race"],
                                        grades=attr["grade"],
                                        types=attr["type"],
                                        events=attr["event"],
                                        affections=attr["affection"],
                                        names=attr["name"],
                                        jp=attr["jp"])
    paged_unit_list = await compose_paged_unit_list(matching_units, units_per_page)
    max_pages = math.ceil(len(matching_units) / units_per_page) - 1
    await loading.delete()

    async def display(page: int):
        _loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=embeds.LOADING_EMBED)
        message = await ctx.send(file=await image_to_discord(paged_unit_list[page], "units.png"),
                                 embed=discord.Embed(
                                     title=f"Units matching {criteria} ({page + 1}/{max_pages + 1})"
                                 ).set_image(url="attachment://units.png"),
                                 content=f"{ctx.message.author.mention}")
        await _loading.delete()

        if page != 0:
            await message.add_reaction("⬅️")

        if page != max_pages:
            await message.add_reaction("➡️")

        try:
            def check_page(added_reaction, user):
                return user == ctx.message.author and str(added_reaction.emoji) in ["⬅️", "➡️"]

            reaction, _ = await BOT.wait_for("reaction_add", check=check_page, timeout=20)

            if "➡️" in str(reaction.emoji):
                await message.delete()
                await display(page + 1)
            elif "⬅️" in str(reaction.emoji):
                await message.delete()
                await display(page - 1)
        except asyncio.TimeoutError:
            await message.clear_reactions()

    await display(0)


@cmd_list.command(name="banner", aliases=["banners"])
async def list_banners(ctx):
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Banners", embed=embeds.LOADING_EMBED)
    await ctx.send(content=f"{ctx.message.author.mention}",
                   embed=discord.Embed(title="All Banners",
                                       description="\n\n".join(
                                           [f"**{x.name[0]}**: `{x.pretty_name}`" for x in ALL_BANNERS])))
    await loading.delete()


@BOT.command(no_pm=True)
async def banner(ctx, *, banner_name: str = "banner one"):
    from_banner = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Banner", embed=embeds.LOADING_EMBED)
    await ctx.send(
        file=await image_to_discord(await compose_banner_list(from_banner, "custom" in from_banner.name),
                                    "banner.png"),
        embed=discord.Embed(title=f"SSRs in {from_banner.pretty_name} ({from_banner.ssr_chance}%)").set_image(
            url="attachment://banner.png"),
        content=f"{ctx.message.author.mention}")
    await loading.delete()


@BOT.command(no_pm=True)
async def add_banner_unit(ctx, banner_name: str, *, units: str):
    await add_unit_to_banner(banner_name, units)
    ctx.send(content=f"Units ({units}) added to {banner_name}")


@BOT.command(no_pm=True)
async def add_banner_rate_up_unit(ctx, banner_name: str, *, units: str):
    await add_rate_up_unit_to_banner(banner_name, units)
    ctx.send(content=f"Rate up units ({units}) added to {banner_name}")


@BOT.command(no_pm=True)
async def update(ctx):
    read_units_from_db()
    read_banners_from_db()
    create_custom_unit_banner()
    parse_demon_roles()
    await ctx.send(content=f"{ctx.message.author.mention} Updated Units & Banners")


@BOT.group(no_pm=True)
async def affection(ctx):
    if ctx.invoked_subcommand is None:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.AFFECTION_HELP_EMBED)


@affection.command(name="add", aliases=["create", "plus", "+"])
async def affection_add(ctx, *, name: typing.Optional[str]):
    if name.lower in [Affection.SIN.value, Affection.KNIGHT.value, Affection.NONE.value, Affection.ANGEL.value,
                      Affection.CATASTROPHE.value,
                      Affection.COMMANDMENTS.value]:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.AFFECTION_UNMUTABLE_ERROR_EMBED)

    await add_affection(name, ctx.message.author.id)
    AFFECTIONS.append(name.lower())
    await ctx.send(content=f"{ctx.message.author.mention}",
                   embed=embeds.AFFECTION_ADDED_EMBED)


@affection.command(name="edit")
async def affection_edit(ctx, old_name: str, *, new_name: str):
    if old_name.lower() not in AFFECTIONS:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.AFFECTION_EDITED_EMBED)

    if get_affection_creator(old_name.lower()) != ctx.message.author.id:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error with ..affections edit",
                                                  colour=discord.Color.dark_red(),
                                                  description=f"**{old_name.lower()}** is not your affection!"))

    await update_affection_name(old_name, new_name)
    AFFECTIONS.append(new_name.lower())
    await ctx.send(content=f"{ctx.message.author.mention}",
                   embed=embeds.AFFECTION_EDITED_EMBED)


@affection.command(name="transfer", aliases=["move", ">"])
async def affection_transfer(ctx, name: str, owner: discord.Member):
    if name.lower() not in AFFECTIONS:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.AFFECTION_EDITED_EMBED)

    if get_affection_creator(name.lower()) != ctx.message.author.id:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error with ..affections edit",
                                                  colour=discord.Color.dark_red(),
                                                  description=f"**{name.lower()}** is not your affection!"))

    await update_affection_owner(name, owner)
    await ctx.send(content=f"{ctx.message.author.mention}",
                   embed=embeds.AFFECTION_EDITED_EMBED)


@affection.command(name="remove", aliases=["delete", "minus", "-"])
async def affection_remove(ctx, *, name: str):
    if name.lower() not in AFFECTIONS:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=embeds.AFFECTION_REMOVED_EMBED)

    if get_affection_creator(name.lower()) != ctx.message.author.id:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error with ..affections edit",
                                                  colour=discord.Color.dark_red(),
                                                  description=f"**{name.lower()}** is not your affection!"))
    await remove_affection(name)
    AFFECTIONS.remove(name.lower())
    await ctx.send(content=f"{ctx.message.author.mention}",
                   embed=embeds.AFFECTION_REMOVED_EMBED)


@affection.command(name="list")
async def affection_list(ctx):
    return await ctx.send(content=f"{ctx.message.author.mention}",
                          embed=discord.Embed(title="All Affections", description=",\n".join(AFFECTIONS)))


@BOT.command(no_pm=True)
async def box(ctx, user: typing.Optional[discord.Member]):
    if user is None:
        user = ctx.message.author
    box_d = await read_box(user)
    if len(box_d) == 0:
        return await ctx.send(content=f"{ctx.message.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"{user.display_name} has no units!"))
    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading {user.display_name}'s box",
                             embed=embeds.LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_box(box_d), "box.png"),
                   content=f"{ctx.message.author.mention}",
                   embed=discord.Embed(title=f"{user.display_name}'s box", colour=discord.Color.gold()).set_image(
                       url="attachment://box.png"))
    await loading.delete()


@BOT.command(no_pm=True)
async def find(ctx, *, units=""):
    if units.replace(" ", "") == "":
        return await ctx.send(content=f"{ctx.message.author.mention} -> Please provide at least 1 name `..find name1, "
                                      f"name2, ..., nameN`")
    unit_vague_name_list = units.split(",")
    found = []

    for _, ele in enumerate(unit_vague_name_list):
        while ele.startswith(" "):
            ele = ele[1:]

        while ele.endswith(" "):
            ele = ele[:-1]

        found.extend(unit_by_vague_name(ele))

    if len(found) == 0:
        return await ctx.send(content=f"{ctx.message.author.mention} -> No units found!")

    loading = await ctx.send(content=f"{ctx.message.author.mention} -> Loading Units", embed=embeds.LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_unit_list(found), "units.png"),
                   embed=discord.Embed().set_image(url="attachment://units.png"))
    await loading.delete()


@BOT.group(no_pm=True, aliases=["bj", "jack", "blackj"])
async def blackjack(ctx):
    if ctx.invoked_subcommand is None:
        bot_card_values = [ra.randint(1, 11) for _ in range(2)]
        player_card_values = [ra.randint(1, 11) for _ in range(2)]

        hit = "✅"
        stand = "🟥"

        cards_msg = await ctx.send(content=f"""
                    {ctx.message.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
                    Bot card is: {bot_card_values[0]}""")

        async def play(last_msg=None):
            await last_msg.clear_reactions()
            if sum(player_card_values) > 21:
                await add_blackjack_game(ctx.message.author, False)
                return await last_msg.edit(
                    content=f"{ctx.message.author.mention} you lost! -> Hand of {sum(player_card_values)}")
            if sum(player_card_values) == 21:
                await add_blackjack_game(ctx.message.author, True)
                if last_msg is None:
                    return await ctx.send(content=f"{ctx.message.author.mention} you got a Blackjack and won!")
                return await last_msg.edit(content=f"{ctx.message.author.mention} you got a Blackjack and won!")

            await last_msg.edit(content=f"""
                {ctx.message.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
                Bot card is: {bot_card_values[0]}""")
            await last_msg.add_reaction(hit)
            await last_msg.add_reaction(stand)

            def check(added_reaction, user):
                return user == ctx.message.author and str(added_reaction.emoji) in [hit, stand]

            try:
                reaction, _ = await BOT.wait_for('reaction_add', check=check)

                if str(reaction.emoji) == hit:
                    player_card_values.append(ra.randint(1, 11))
                    return await play(last_msg=cards_msg)
                if str(reaction.emoji) == stand:
                    await cards_msg.clear_reactions()
                    await add_blackjack_game(ctx.message.author,
                                             21 - sum(player_card_values) < 21 - sum(bot_card_values))
                    return await last_msg.edit(
                        content=f"{ctx.message.author.mention} you won! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})" if 21 - sum(
                            player_card_values) < 21 - sum(bot_card_values)
                        else f"{ctx.message.author.mention} you lost! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})")
            except TimeoutError:
                pass

        await play(cards_msg)


@blackjack.command(name="top", aliases=["leaderboard", "lead", "leader", "leading"])
async def blackjack_top(ctx):
    data = await get_blackjack_top(ctx.message.guild)
    if data is None:
        return await ctx.send(content="Nobody played Blackjack yet!")

    top_l = []
    i = 0
    for row in data:
        i += 1
        top_l.append(f"**{i}.** *{(await BOT.fetch_user(row[0])).display_name}* ~ Streak of {row[1]} wins")

    return await ctx.send(content=f"{ctx.message.author.mention}",
                          embed=discord.Embed(
                              title=f"Blackjack Leaderboard in {ctx.message.guild.name} (Highest Winning Streaks)",
                              description=",\n".join(top_l)
                          ).set_thumbnail(url=ctx.message.guild.icon_url))


@blackjack.command(name="record", aliases=["stats"])
async def blackjack_record(ctx, person: typing.Optional[discord.Member] = None):
    if person is None:
        person = ctx.message.author
    data = await get_blackjack_stats(person)

    if data is None:
        return await ctx.send(
            content=f"{ctx.message.author.mention} hasn't played Blackjack yet!" if person == ctx.message.author
            else f"{ctx.message.author.mention}: {person.display_name} hasn't played Blackjack yet!")

    return await ctx.send(
        content=f"{ctx.message.author.mention} Blackjack History:" if person == ctx.message.author else f"{ctx.message.author.mention}: {person.display_name}'s Blackjack History:",
        embed=discord.Embed(
            title=f"History of {person.display_name}",
            description=f"""
                              **Wins**: `{data[0]}`

                              **Lost**: `{data[1]}`

                              **Win Streak**: `{"No" if data[3] == 0 else data[2]}`

                              **Highest Winning Streak**: `{data[4]}`
                              """
        ))


@BOT.group(no_pm=True)
async def demon(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"{ctx.message.author.mention}:", embed=embeds.DEMON_HELP_EMBED)


@demon.command(name="friend", aliases=["friendcode", "code"])
async def demon_friend(ctx, of: typing.Optional[discord.Member]):
    if of == None:
        of = ctx.message.author

    friendcode = await get_friendcode(ctx.message.author)

    if friendcode is None:
        if of == ctx.message.author:
            ctx.send(f"{ctx.message.author.mention}: You are not registered in the bot yet! `..demon tag <grandcross friendcode> <profile name>` to create one")
        else:
            ctx.send(f"{ctx.message.author.mention}: {of.display_name} is not registered in the bot yet!")
    else:
        ctx.send(f"{ctx.message.author.mention}: {friendcode[0]}")


@demon.command(name="offer")
async def demon_offer(ctx, reds: int = 0, greys: int = 0, crimsons: int = 0, *, additional_message: str = ""):
    if reds == 0 and greys == 0 and crimsons == 0:
        return await ctx.send(
            content=f"{ctx.message.author.mention}",
            embed=discord.Embed(
                title="Error",
                description="Please provide at least one demon",
                color=discord.Color.dark_red()
            )
        )
    author = ctx.message.author
    guild_created_in = ctx.message.guild

    if author.id in DEMON_CONTRACTS.keys():
        del DEMON_CONTRACTS[author.id]

    if author.id not in DEMON_CONTRACTS:
        DEMON_CONTRACTS[author.id] = {
            "guild": ctx.message.guild.id
        }

    for channel_list_item in get_raid_channels():
        channel = await BOT.fetch_channel(channel_list_item[1])
        guild = await BOT.fetch_guild(channel_list_item[0])

        mentions = []
        if reds != 0 and get_demon_role(guild.id, "red") is not None:
            mentions.append(get_demon_role(guild.id, "red").mention)
        if greys != 0 and get_demon_role(guild.id, "grey") is not None:
            mentions.append(get_demon_role(guild.id, "grey").mention)
        if crimsons != 0 and get_demon_role(guild.id, "crimson") is not None:
            mentions.append(get_demon_role(guild.id, "crimson").mention)
        mention_str = ", ".join(mentions)

        to_claim = await channel.send(
            content=mention_str,
            embed=discord.Embed(
                title=f"{author.display_name} offers:",
                description="\n" +
                            (f"Reds: `{reds}` \n" if reds != 0 else "") +
                            (f"Greys: `{greys}` \n" if greys != 0 else "") +
                            (f"Crimsons: `{crimsons}` \n" if crimsons != 0 else "") +
                            (f"\n {additional_message} \n" if additional_message != "" else "") +
                            "\nClick 🆗 to claim them." +
                            "\nMake sure to have a empty spot in your friends list!",
                color=discord.Color.green()
            )
        )

        await to_claim.add_reaction("🆗")

        DEMON_OFFER_MESSAGES[to_claim.id] = {
            "created_in": guild_created_in,
            "guild": guild,
            "channel": channel,
            "creator": author
        }

    if len(DEMON_OFFER_MESSAGES) == 0:
        return await ctx.send(f"{author.mention} no channel to broadcast in found")

    def check(added_reaction, user):
        return user != BOT.user and str(added_reaction.emoji) in "🆗"

    try:
        added_reaction, user = await BOT.wait_for('reaction_add', check=check, timeout=60 * 60 * 4)

        if user == author:
            await ctx.send(f"{author.mention} deleted your demon offer.")
        else:
            author_friendcode = await get_friendcode(author)
            claim_friendcode = await get_friendcode(user)

            if author_friendcode is None and claim_friendcode is None:
                await ctx.send(f"{author.mention}: {user.mention} has claimed your demons!")
            elif author_friendcode is None and claim_friendcode is not None:
                await ctx.send(
                    f"{author.mention}: {user.mention} (Friendcode: {claim_friendcode[0]}) has claimed your demons!")
            elif author_friendcode is not None and claim_friendcode is None:
                await ctx.send(
                    f"{author.mention} (Friendcode: {author_friendcode[0]}): {user.mention} has claimed your demons!")
            else:
                await ctx.send(
                    f"{author.mention} (Friendcode: {author_friendcode[0]}): {user.mention} (Friendcode: {claim_friendcode[0]}) has claimed your demons!")

            if len(shared_guilds(author, user)) != 0 and added_reaction.message.guild.id != \
                    DEMON_OFFER_MESSAGES[added_reaction.message.id]["created_in"].id:
                await author.send(
                    content=f"Please contact {user.mention} (from {shared_guilds(author, user)[0]}) for your demons")

        offer_messages = [message_id for message_id in DEMON_OFFER_MESSAGES if
                          DEMON_OFFER_MESSAGES[message_id]["creator"].id == author.id]

        for offer_id in offer_messages:
            try:
                DEMON_OFFER_MESSAGES[offer_id]["claimed_by"] = user
                offer_message = await DEMON_OFFER_MESSAGES[offer_id]["channel"].fetch_message(offer_id)
                new_embed = discord.Embed(
                    title=f"~~{offer_message.embeds[0].title}~~ Claimed",
                    description=f"~~{offer_message.embeds[0].description}~~"
                ).set_footer(text=f"Claimed by {user.display_name}")
                await offer_message.edit(embed=new_embed)
                await offer_message.clear_reactions()
            except discord.errors.NotFound:
                pass

    except asyncio.TimeoutError:
        offer_messages = [message_id for message_id in DEMON_OFFER_MESSAGES if
                          DEMON_OFFER_MESSAGES[message_id]["creator"].id == author.id]
        for offer_id in offer_messages:
            try:
                msg = await DEMON_OFFER_MESSAGES[offer_id]["channel"].fetch_message(offer_id)
                new_embed = discord.Embed(
                    title=f"~~{msg.embeds[0].title}~~ Timed out",
                    description=f"~~{msg.embeds[0].description}~~"
                ).set_footer(text="Time ran out.")
                await msg.edit(embed=new_embed)
                await msg.clear_reactions()
            except discord.errors.NotFound:
                pass

    if author.id in DEMON_MESSAGES:
        del DEMON_MESSAGES[author.id]


@BOT.event
async def on_message(message):  # if people dont share a server. reply to the offer message
    if message.reference is None:
        return await BOT.process_commands(message)

    demon_msg_id = message.reference.message_id

    if demon_msg_id not in DEMON_OFFER_MESSAGES:
        return await BOT.process_commands(message)

    offer_data = Dict2Obj(DEMON_OFFER_MESSAGES[demon_msg_id])

    if "claimed_by" not in DEMON_OFFER_MESSAGES[demon_msg_id]:
        return await BOT.process_commands(message)

    if len(shared_guilds(offer_data.creator, offer_data.claimed_by)) == 0:
        if message.author.id == offer_data.creator.id:
            await offer_data.claimed_by.send(
                content=f"Message from {offer_data.creator.mention} regarding your demon offer:",
                embed=discord.Embed(description=message.content))
        else:
            await offer_data.creator.send(
                content=f"Message from {offer_data.claimed_by.mention} regarding your demon offer:",
                embed=discord.Embed(description=message.content))


@demon.command(name="profile", aliases=["create", "tag"])
async def demon_profile(ctx, gc_id: int = 0, name: str = "main"):
    if gc_id == 0:
        return await ctx.send(
            content=f"{ctx.message.author.mention}",
            embed=discord.Embed(
                title=f"Info about {ctx.message.author.display_name}",
                description="Names: \n" + "\n".join([
                    "{}: {}".format(x[0], x[1])
                    for x in await get_profile_name_and_friendcode(ctx.message.author)
                ])
            ))

    if get_demon_profile(ctx.message.author, name) is None:
        await create_demon_profile(ctx.message.author, gc_id, name)
        await ctx.send(f"{ctx.message.author.mention}: Added profile {name}  with friendcode {gc_id}")
    else:
        if gc_id == -1:
            await delete_demon_profile(ctx.message.author, name)
            await ctx.send(f"{ctx.message.author.mention}: Deleted profile {name}")
        else:
            await update_demon_profile(ctx.message.author, gc_id, name)
            await ctx.send(f"{ctx.message.author.mention}: Edited profile {name} to friendcode {gc_id}")


@demon.command(name="info", aliases=["me"])
async def demon_info(ctx, of: typing.Optional[discord.Member]):
    if of is None:
        of = ctx.message.author
    await ctx.send(
        content=f"{ctx.message.author.mention}",
        embed=discord.Embed(
            title=f"Info about {of.display_name}",
            description="Names: \n" + "\n".join([
                "{}: {}".format(x[0], x[1])
                for x in await get_profile_name_and_friendcode(of)
            ])
        ))


@demon.command(name="channel")
@has_permissions(manage_channels=True)
async def demon_channel(ctx, action="none"):
    if action == "none":
        await add_raid_channel(ctx.message)
        return await ctx.send(f"{ctx.message.author.mention} added demon channel!")

    channels = [(await BOT.fetch_channel(x[1])).name + " in " + (await BOT.fetch_guild(x[0])).name for x in
                await get_raid_channels()]
    await ctx.message.author.send("\n".join(channels))


def start_up_bot(token_path: str = "data/bot_token.txt", db_path: str = "data/data.db", is_beta: bool = False):
    global TOKEN, IS_BETA
    try:
        read_affections_from_db()
        read_units_from_db()
        read_banners_from_db()

        with open(token_path, 'r') as token_file:
            TOKEN = token_file.read()

        sql.connection.close()
        sql.connection = sql.sqlite.connect(db_path)

        IS_BETA = is_beta

        BOT.run(TOKEN)
    finally:
        sql.connection.close()


if __name__ == '__main__':
    start_up_bot()
