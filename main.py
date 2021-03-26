from datetime import datetime

from discord.ext.commands import Context

import utilities.embeds as embeds
import utilities.reactions as emojis
import utilities.sql_helper as sql
from utilities.awaken import *
from utilities.banner_data import *
from utilities.cc_register import *
from utilities.image_composer import *
from utilities.sql_helper import *
from utilities.unit_data import *

TOKEN: int = 0
IS_BETA: bool = False
LOADING_IMAGE_URL: str = \
    "https://raw.githubusercontent.com/dokkanart/SDSGC/master/Loading%20Screens/Gacha/loading_gacha_start_01.png"
AUTHOR_HELIX_ID: int = 204150777608929280

intents = discord.Intents.default()
intents.members = True

TEAM_REROLL_EMOJIS = [emojis.NO_1, emojis.NO_2, emojis.NO_3, emojis.NO_4]


class CustomHelp(HelpCommand):
    async def send_bot_help(self, _):
        await self.get_destination().send(embed=embeds.Help.General.HELP_1)
        await self.get_destination().send(embed=embeds.Help.General.HELP_2)


class MemberMentionConverter(commands.Converter):
    async def convert(self, ctx: Context, argument: str) -> discord.Member:
        return ctx.message.mentions[0]


BOT: Bot = commands.Bot(command_prefix='..', description='..help for Help', help_command=CustomHelp(), intents=intents)


async def get_top_users(guild: discord.Guild, action: LeaderboardType = LeaderboardType.LUCK) -> List[Dict[str, Any]]:
    if action == LeaderboardType.MOST_SHAFTS:
        return [x async for x in get_top_shafts(BOT, guild)]
    if action == LeaderboardType.LUCK:
        return [x async for x in get_top_lucky(BOT, guild)]
    if action == LeaderboardType.MOST_SSR:
        return [x async for x in get_top_ssrs(BOT, guild)]
    if action == LeaderboardType.MOST_UNITS:
        return [x async for x in get_top_units(BOT, guild)]


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

    def test(x: Unit):
        return x.race in races \
               and x.type in types \
               and x.grade in grades \
               and x.event in events \
               and x.affection.lower().replace(" ", "") in affections \
               and x.name.lower().replace(" ", "") in names \
               and (x.is_jp if jp else True)

    possible_units: List[Unit] = [x for x in UNITS if test(x)]

    if len(possible_units) == 0:
        raise LookupError

    return possible_units


def _get_random_unit(criteria: Dict[str, Any]) -> Unit:
    return get_random_unit(
        grades=criteria["grade"],
        types=criteria["type"],
        races=criteria["race"],
        events=criteria["event"],
        affections=criteria["affection"],
        names=criteria["name"],
        jp=criteria["jp"]
    )


def get_random_unit(grades: Optional[List[Grade]] = None,
                    types: Optional[List[Type]] = None,
                    races: Optional[List[Race]] = None,
                    events: Optional[List[Event]] = None,
                    affections: Optional[List[str]] = None,
                    names: Optional[List[str]] = None,
                    jp: bool = False) -> Unit:
    possible_units: List[Unit] = get_matching_units(grades=grades,
                                                    types=types,
                                                    races=races,
                                                    events=events,
                                                    affections=affections,
                                                    names=names,
                                                    jp=jp)
    return possible_units[ra.randint(0, len(possible_units) - 1)]


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


def parse_arguments(given_args: str, list_seperator: str = "&") -> Dict[str, Any]:
    args: List[str] = given_args.split(list_seperator)
    parsed_races: List[Race] = []
    parsed_names: List[str] = []
    parsed_race_count: Dict[Race, int] = {
        Race.HUMAN: 0,
        Race.FAIRY: 0,
        Race.GIANT: 0,
        Race.UNKNOWN: 0,
        Race.DEMON: 0,
        Race.GODDESS: 0
    }
    parsed_grades: List[Grade] = []
    parsed_types: List[Type] = []
    parsed_events: List[Event] = []
    parsed_affections: List[Affection] = []
    parsed_url: str = ""
    parsed_new_name: str = ""
    parsed_owner: int = 0
    jp: bool = False
    unparsed: List[str] = []

    for _, ele in enumerate(args):
        arg: str = remove_trailing_whitespace(ele)

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


def replace_duplicates(criteria: Dict[str, Any], team_to_deduplicate: List[Unit]) -> None:
    team_simple_names: List[str] = ["", "", "", ""]
    team_races: Dict[Race, int] = {
        Race.HUMAN: 0,
        Race.FAIRY: 0,
        Race.GIANT: 0,
        Race.UNKNOWN: 0,
        Race.DEMON: 0,
        Race.GODDESS: 0
    }
    max_races: Dict[Race, int] = criteria["max race count"]

    checker: int = 0
    for i in max_races:
        checker += max_races[i]

    if checker not in (4, 0):
        raise ValueError("Too many Races")

    def check_races(_i: int) -> bool:
        if checker == 0:
            return True
        if team_races[team_to_deduplicate[_i].race] >= max_races[team_to_deduplicate[_i].race]:
            if team_to_deduplicate[_i].race in criteria["race"]:
                criteria["race"].remove(team_to_deduplicate[_i].race)
            team_to_deduplicate[_i] = get_random_unit(races=criteria["race"], grades=criteria["grade"],
                                                      types=criteria["type"],
                                                      events=criteria["event"], affections=criteria["affection"],
                                                      names=criteria["name"], jp=criteria["jp"])
            return False
        team_races[team_to_deduplicate[_i].race] += 1
        return True

    def check_names(_i: int) -> bool:
        if team_to_deduplicate[_i].simple_name not in team_simple_names:
            team_simple_names[_i] = team_to_deduplicate[_i].simple_name
            return True
        team_to_deduplicate[_i] = get_random_unit(races=criteria["race"], grades=criteria["grade"],
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


async def build_menu(ctx: Context, prev_message: discord.Message, page: int = 0) -> None:
    of_banner: Banner = ALL_BANNERS[page]
    summon_menu_emojis: List[str] = [emojis.LEFT_ARROW, emojis.NO_1,
                                     emojis.NO_10 if of_banner.banner_type == BannerType.ELEVEN else emojis.NO_5,
                                     emojis.WHALE, emojis.INFO, emojis.RIGHT_ARROW]
    await prev_message.clear_reactions()
    draw: discord.Message = prev_message

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

        if emojis.RIGHT_ARROW in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page + 1)
        elif emojis.LEFT_ARROW in str(reaction.emoji):
            await build_menu(ctx, prev_message=draw, page=page - 1)
        elif (emojis.NO_10 if ALL_BANNERS[page].banner_type == BannerType.ELEVEN else emojis.NO_5) in str(
                reaction.emoji):
            await draw.delete()
            await multi(ctx, person=ctx.author, banner_name=ALL_BANNERS[page].name[0])
        elif emojis.NO_1 in str(reaction.emoji):
            await draw.delete()
            await single(ctx, person=ctx.author, banner_name=ALL_BANNERS[page].name[0])
        elif emojis.WHALE in str(reaction.emoji):
            await draw.delete()
            await shaft(ctx, person=ctx.author, banner_name=ALL_BANNERS[page].name[0])
        elif emojis.INFO in str(reaction.emoji):
            await draw.delete()
            await banner(ctx, banner_name=ALL_BANNERS[page].name[0])
    except asyncio.TimeoutError:
        pass


def parse_custom_unit_args(arg: str) -> Dict[str, Any]:
    all_parsed: Dict[str, Any] = parse_arguments(arg)

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


def mutual_guilds(person: discord.User) -> List[discord.Guild]:
    return [g for g in BOT.guilds if g.get_member(person.id) is not None]


def shared_guilds(person1: discord.User, person2: discord.User) -> List[discord.Guild]:
    return [x for x in mutual_guilds(person1) if x in mutual_guilds(person2)]


@BOT.event
async def on_ready():
    await BOT.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="..help"))

    create_custom_unit_banner()
    create_jp_banner()

    print('Logged in as')
    print(BOT.user.name)
    print(BOT.user.id)
    print('--------')


@BOT.group()
async def top(ctx: Context):
    if ctx.invoked_subcommand is None:
        return await top_luck(ctx)


@top.command(name="luck", aliases=["lucky", "luckiness"])
async def top_luck(ctx: Context):
    top_users: List[Dict[str, Any]] = await get_top_users(ctx.guild, LeaderboardType.LUCK)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )

    await ctx.send(
        embed=discord.Embed(
            title=f"Luckiest Members in {ctx.guild.name}",
            description='\n'.join([
                "**{}.** {} with a *{}%* SSR drop rate in their pulls. (Total: *{}*)".format(top_user["place"],
                                                                                             top_user["name"],
                                                                                             top_user["luck"],
                                                                                             top_user["pull-amount"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.guild.icon_url)
    )


@top.command(name="ssrs", aliases=["ssr"])
async def top_ssrs(ctx: Context):
    top_users: List[Dict[str, Any]] = await get_top_users(ctx.guild, LeaderboardType.MOST_SSR)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )
    await ctx.send(
        embed=discord.Embed(
            title=f"Members with most drawn SSRs in {ctx.guild.name}",
            description='\n'.join([
                "**{}.** {} with *{} SSRs*. (Total: *{}*)".format(top_user["place"],
                                                                  top_user["name"],
                                                                  top_user["ssrs"],
                                                                  top_user["pull-amount"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.guild.icon_url)
    )


@top.command(name="units", aliases=["unit"])
async def top_units(ctx: Context):
    top_users: List[Dict[str, Any]] = await get_top_users(ctx.guild, LeaderboardType.MOST_UNITS)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )
    await ctx.send(
        embed=discord.Embed(
            title=f"Members with most drawn Units in {ctx.guild.name}",
            description='\n'.join([
                "**{}.** {} with *{} Units*".format(top_user["place"],
                                                    top_user["name"],
                                                    top_user["pull-amount"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.guild.icon_url)
    )


@top.command(name="shafts", aliases=["shaft"])
async def top_shafts(ctx: Context):
    top_users: List[Dict[str, Any]] = await get_top_users(ctx.message.guild, LeaderboardType.MOST_SHAFTS)
    if len(top_users) == 0:
        return await ctx.send(
            embed=discord.Embed(
                title="Nobody summoned yet",
                description="Use `..multi`, `..single` or `..shaft`"
            )
        )
    return await ctx.send(
        embed=discord.Embed(
            title=f"Members with most Shafts in {ctx.guild.name}",
            description='\n'.join([
                "**{}.** {} with *{} Shafts*".format(top_user["place"],
                                                     top_user["name"],
                                                     top_user["shafts"])
                for top_user in top_users]),
            colour=discord.Colour.gold()
        ).set_thumbnail(url=ctx.guild.icon_url)
    )


@BOT.group()
async def stats(ctx: Context, person: typing.Optional[discord.Member]):
    if person is None:
        person: discord.Member = ctx.author

    data: Dict[str, int] = await get_user_pull(person)
    ssrs: int = data["ssr_amount"] if len(data) != 0 else 0
    pulls: int = data["pull_amount"] if len(data) != 0 else 0
    shafts: int = data["shafts"] if len(data) != 0 else 0
    percent: float = round((ssrs / pulls if len(data) != 0 else 0) * 100, 2)

    STAT_HELPER[ctx] = {
        "data": data,
        "ssrs": ssrs,
        "pulls": pulls,
        "shafts": shafts,
        "percent": percent,
        "person": person
    }

    if ctx.invoked_subcommand is None:
        return await stats_luck(ctx)


@stats.command(name="luck", aliases=["lucky", "luckiness"])
async def stats_luck(ctx):
    person: discord.Member = STAT_HELPER[ctx]["person"]
    percent: float = STAT_HELPER[ctx]["percent"]
    ssrs: int = STAT_HELPER[ctx]["ssrs"]
    pulls: int = STAT_HELPER[ctx]["pulls"]
    await ctx.send(
        content=f"{person.mention}'s luck:" if person == ctx.author
        else f"{ctx.author.mention}: {person.display_name}'s luck:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently got a *{percent}%* SSR droprate in their pulls, with *{ssrs} SSRs* in *{pulls} Units*"
        )
    )
    STAT_HELPER[ctx] = None


@stats.command(name="ssrs", aliases=["ssr"])
async def stats_ssrs(ctx: Context):
    person: discord.Member = STAT_HELPER[ctx]["person"]
    ssrs: int = STAT_HELPER[ctx]["ssrs"]
    await ctx.send(
        content=f"{person.mention}'s SSRs:" if person == ctx.author
        else f"{ctx.author.mention}: {person.display_name}'s SSRs:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently has *{ssrs} SSRs*"
        )
    )
    STAT_HELPER[ctx] = None


@stats.command(name="units", aliases=["unit"])
async def stats_units(ctx: Context):
    person: discord.Member = STAT_HELPER[ctx]["person"]
    pulls: int = STAT_HELPER[ctx]["pulls"]
    await ctx.send(
        content=f"{person.mention}'s Units:" if person == ctx.author
        else f"{ctx.author.mention}: {person.display_name}'s Units:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently has *{pulls} Units*"
        )
    )
    STAT_HELPER[ctx] = None


@stats.command(name="shafts", aliases=["shaft"])
async def stats_shafts(ctx: Context):
    person: discord.Member = STAT_HELPER[ctx]["person"]
    shafts: int = STAT_HELPER[ctx]["shafts"]
    await ctx.send(
        content=f"{person.mention}'s Shafts:" if person == ctx.author
        else f"{ctx.author.mention}: {person.display_name}'s Shafts:",
        embed=discord.Embed(
            description=f"**{person.display_name}** currently got shafted {shafts}x"
        )
    )


@BOT.command(no_pm=True)
async def unit(ctx: Context, *, args: str = ""):
    attributes: Dict[str, Any] = parse_arguments(args)
    try:
        random_unit: Unit = get_random_unit(grades=attributes["grade"],
                                            types=attributes["type"],
                                            races=attributes["race"],
                                            events=attributes["event"],
                                            affections=attributes["affection"],
                                            names=attributes["name"],
                                            jp=attributes["jp"])

        await random_unit.set_icon()

        await ctx.send(content=f"{ctx.author.mention} this is your unit",
                       embed=discord.Embed(title=random_unit.name, colour=random_unit.discord_color())
                       .set_image(url="attachment://unit.png"),
                       file=await random_unit.discord_icon())
    except LookupError:
        await ctx.send(content=f"{ctx.author.mention}",
                       embed=embeds.UNIT_LOOKUP_ERROR_EMBED)


@BOT.command(no_pm=True)
async def pvp(ctx: Context, enemy: discord.Member, attr: str = ""):
    attr: Dict[str, Any] = parse_arguments(attr)
    proposed_team_p1: List[Unit] = [
        get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                        affections=attr["affection"], names=attr["name"], jp=attr["jp"])
        for _ in range(4)]
    proposed_team_p2: List[Unit] = [
        get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                        affections=attr["affection"], names=attr["name"], jp=attr["jp"])
        for _ in range(4)]

    try:
        replace_duplicates(attr, proposed_team_p1)
        replace_duplicates(attr, proposed_team_p2)
    except ValueError as e:
        return await ctx.send(content=f"{ctx.message.author.mention} -> {e}",
                              embed=embeds.TEAM_LOOKUP_ERROR_EMBED)

    player1 = ctx.author

    if player1 in PVP_TIME_CHECK or enemy in PVP_TIME_CHECK:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=embeds.PVP_COOLDOWN_ERROR_EMBED)

    changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

    async def send(player: discord.Member, last_message: Optional[discord.Message] = None) -> None:
        if last_message is not None:
            await last_message.delete()

        if player not in PVP_TIME_CHECK:
            PVP_TIME_CHECK.append(player)

        loading_message: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED)
        team_message: discord.Message = await ctx.send(
            file=await image_to_discord(await compose_team(
                rerolled_team=proposed_team_p1 if player == player1 else proposed_team_p2,
                re_units=changed_units), "team.png"),
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

    changed_units: Dict[int, List[Unit]] = {0: [], 1: [], 2: [], 3: []}

    await send(enemy)

    await ctx.send(file=await image_to_discord(await compose_pvp(player1=player1,
                                                                 player2=enemy,
                                                                 team1=proposed_team_p1,
                                                                 team2=proposed_team_p2),
                                               "pvp.png"))


# ..team
@BOT.command(no_pm=True)
async def team(ctx: Context, *, args: str = ""):
    attr: Dict[str, Any] = parse_arguments(args)
    amount: int = 1

    if len(attr["unparsed"]) != 0:
        try:
            amount: int = int(attr["unparsed"][0])
        except ValueError:
            pass

    if amount > 1:
        amount: int = min(amount, 15)

        loading: discord.Message = await ctx.send(content=ctx.author.mention, embed=embeds.LOADING_EMBED)
        possible: List[Unit] = [_get_random_unit(attr) for _ in range(amount * 4)]
        teams: List[Unit] = [[possible[i + 0], possible[i + 1], possible[i + 2], possible[i + 3]] for i in
                             range(0, amount * 4, 4)]
        for i, ele in enumerate(teams):
            replace_duplicates(attr, ele)
        possible: List[Unit] = [item for sublist in teams for item in sublist]
        await ctx.send(ctx.author.mention,
                       file=await image_to_discord(await compose_random_select_team(possible),
                                                   "random_select_team.png"))
        return await loading.delete()

    try:
        proposed_team: List[Unit] = [
            get_random_unit(races=attr["race"], grades=attr["grade"], types=attr["type"], events=attr["event"],
                            affections=attr["affection"], names=attr["name"], jp=attr["jp"])
            for _ in range(4)]

        try:
            replace_duplicates(criteria=attr, team_to_deduplicate=proposed_team)
        except ValueError as e:
            return await ctx.send(content=f"{ctx.author.mention} -> {e}",
                                  embed=embeds.TEAM_LOOKUP_ERROR_EMBED)

        if ctx.message.author in TEAM_TIME_CHECK:
            return await ctx.send(content=f"{ctx.author.mention}",
                                  embed=embeds.TEAM_COOLDOWN_ERROR_EMBED)

        changed_units: Dict[int, List[Unit]] = {
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

            loading_message: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED)
            team_message: discord.Message = await ctx.send(
                file=await image_to_discord(await compose_team(
                    rerolled_team=proposed_team, re_units=changed_units), "units.png"),
                content=f"{ctx.author.mention} this is your team",
                embed=discord.Embed().set_image(url="attachment://units.png"))
            await loading_message.delete()

            for emoji in TEAM_REROLL_EMOJIS:
                await team_message.add_reaction(emoji)

            def check_reroll(added_reaction, user):
                return user == ctx.author and str(added_reaction.emoji) in TEAM_REROLL_EMOJIS \
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
                    TEAM_TIME_CHECK.remove(ctx.author)
                await team_message.clear_reactions()

        await send_message()
    except LookupError:
        await ctx.send(content=f"{ctx.author.mention}",
                       embed=embeds.TEAM_LOOKUP_ERROR_EMBED)


@BOT.command(no_pm=True)
async def multi(ctx: Context, person: typing.Optional[discord.Member], *, banner_name: str = "1 banner 1"):
    if person is None:
        person: discord.Member = ctx.author

    amount_str: str = ""
    amount: int = 1
    rot: bool = False

    if banner_name.startswith("rot") or banner_name.startswith("rotation"):
        rot: bool = True
        banner_name: str = remove_trailing_whitespace(banner_name.replace("rotation", "").replace("rot", ""))
        if banner_name.replace(" ", "") == "":
            banner_name: str = "banner 1"
    else:
        while banner_name.startswith(tuple(str(i) for i in range(50))):
            amount_str += remove_trailing_whitespace(banner_name[0])
            banner_name: str = remove_trailing_whitespace(banner_name[1:])
            amount: int = int(amount_str)

        if banner_name.replace(" ", "") == "":
            banner_name: str = "banner 1"

    from_banner: Optional[Banner] = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )

    draw: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED.set_image(url=LOADING_IMAGE_URL))

    if rot:
        units: Dict[Unit, int] = {}
        for _ in range(30 * 11):
            _unit: Unit = await unit_with_chance(from_banner, person)
            if _unit in units:
                units[_unit] += 1
            else:
                units[_unit]: int = 1
        connection.commit()
        await ctx.send(
            file=await image_to_discord(await compose_banner_rotation(
                dict(sorted(units.items(), key=lambda x: x[0].grade.to_int()))
            ), "rotation.png"),
            content=f"{person.display_name} those are the units you pulled in 1 rotation" if person is ctx.author
            else f"{person.display_name} those are the units you pulled in 1 rotation coming from {ctx.author.display_name}",
            embed=discord.Embed(
                title=f"{from_banner.pretty_name} ~ 1 Rotation (900 Gems)",
            ).set_image(url="attachment://rotation.png"))
        return await draw.delete()

    images: List[Img] = [await compose_multi_draw(from_banner=from_banner, user=person)
                         if from_banner.banner_type == BannerType.ELEVEN else
                         await compose_five_multi_draw(from_banner=from_banner, user=person) for _ in range(amount)]

    await display_draw_menu(ctx, draw, person, from_banner, 0, images)


async def display_draw_menu(ctx: Context, last_message: discord.Message, person: discord.Member, from_banner: Banner,
                            page: int, images: List[Img]):
    img: discord.File = await image_to_discord(images[page], "units.png")
    msg: discord.Message = await ctx.send(file=img,
                                          content=
                                          f"{person.display_name} this is your {page + 1}. multi"
                                          if person is ctx.author else
                                          f"{person.display_name} this is your {page + 1}. multi coming from {ctx.author.display_name}",
                                          embed=discord.Embed(
                                              title=f"{from_banner.pretty_name}"
                                                    f"({11 if from_banner.banner_type == BannerType.ELEVEN else 5}x summon)")
                                          .set_image(url="attachment://units.png"))
    if last_message is not None:
        await last_message.delete()
    if page != 0:
        await msg.add_reaction(emojis.LEFT_ARROW)

    if page != len(images) - 1:
        await msg.add_reaction(emojis.RIGHT_ARROW)

    if page == 0 and len(images) == 1:
        return

    def check(added_reaction, user):
        return user == ctx.message.author or user == person and str(added_reaction.emoji) in [emojis.LEFT_ARROW,
                                                                                              emojis.RIGHT_ARROW]

    try:
        add_react, _ = await BOT.wait_for('reaction_add', check=check, timeout=30)

        if str(add_react.emoji) == emojis.LEFT_ARROW:
            return await display_draw_menu(ctx, msg, person, from_banner, page - 1, images)
        if str(add_react.emoji) == emojis.RIGHT_ARROW:
            return await display_draw_menu(ctx, msg, person, from_banner, page + 1, images)
    except asyncio.TimeoutError:
        await msg.clear_reactions()


@BOT.command(no_pm=True)
async def summon(ctx: Context):
    draw: discord.Message = await ctx.send(embed=embeds.LOADING_EMBED)
    await build_menu(ctx, prev_message=draw)


@BOT.command(no_pm=True)
async def single(ctx: Context, person: typing.Optional[discord.Member], *, banner_name: str = "banner 1"):
    if person is None:
        person: discord.Member = ctx.author
    from_banner: Optional[Banner] = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"))

    return await ctx.send(file=await compose_draw(from_banner, person),
                          content=f"{person.mention} this is your single"
                          if person is ctx.message.author else
                          f"{person.mention} this is your single coming from {ctx.author.mention}",
                          embed=discord.Embed(title=f"{from_banner.pretty_name} (1x summon)").set_image(
                              url="attachment://unit.png"))


@BOT.command(no_pm=True)
async def shaft(ctx: Context, person: typing.Optional[MemberMentionConverter],
                unit_name: typing.Optional[str] = "Helix is awesome", *, banner_name: str = "banner 1"):
    if person is None:
        person: discord.Member = ctx.author

    if unit_name in ["banner", "part", "gssr", "race", "humans", "soluna", "commandments", "jp", "custom"]:
        banner_name: str = unit_name + " " + banner_name
        unit_name: str = "none"

    from_banner: Banner = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(
                                  title="Error",
                                  colour=discord.Color.dark_red(),
                                  description=f"Can't find the \"{banner_name}\" banner"
                              ))

    unit_ssr: bool = False
    if ssr_pattern.match(unit_name, 0):
        unit_ssr: bool = True
        unit_name: str = ssr_pattern.sub("", unit_name)

    possible_units: List[int] = [a.unit_id for a in unit_by_vague_name(unit_name)]

    if len(possible_units) != 0 and len(
            [a for a in possible_units if a in [b.unit_id for b in from_banner.all_units]]) == 0:
        possible_other_banner: Optional[Banner] = None
        for b1 in ALL_BANNERS:
            matching_units: List[Unit] = [x for x in b1.all_units if x.unit_id in possible_units]
            if len(matching_units) > 0:
                possible_other_banner: Banner = b1
                break
        from_banner: Banner = possible_other_banner

    if from_banner is None:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(
                                  title="Error",
                                  colour=discord.Color.dark_red(),
                                  description=f"Can't find any banner with {unit_name} in it"
                              ))

    if not from_banner.shaftable:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(
                                  title="Error",
                                  colour=discord.Color.dark_red(),
                                  description=f"Can't get shafted on the \"{from_banner.pretty_name}\" banner"
                              ))

    unit_to_draw: List[int] = [a.unit_id for a in unit_by_vague_name(unit_name)
                               if a.unit_id in [b.unit_id for b in from_banner.all_units]]

    draw = await ctx.send(
        content=f"{person.mention} you are getting shafted" if person is ctx.author
        else f"{person.mention} you are getting shafted from {ctx.author.mention}",
        embed=discord.Embed(
            title="Shafting..."
        ).set_image(url=LOADING_IMAGE_URL))

    rang: int = 11 if from_banner.banner_type == BannerType.ELEVEN else 5

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

    i: int = 0
    drawn_units: List[Unit] = [(await unit_with_chance(from_banner, person)) for _ in range(rang)]
    drawn_ssrs: Dict[Unit, int] = {}
    for x in drawn_units:
        if x.grade == Grade.SSR:
            if x not in drawn_ssrs:
                drawn_ssrs[x] = 1
            else:
                drawn_ssrs[x] += 1

    while not await has_ssr(drawn_units) and i < 1000:
        i += 1
        drawn_units: List[Unit] = [(await unit_with_chance(from_banner, person)) for _ in range(rang)]
        for x in drawn_units:
            if x.grade == Grade.SSR:
                if x not in drawn_ssrs:
                    drawn_ssrs[x] = 1
                else:
                    drawn_ssrs[x] += 1

    connection.commit()
    multi_msg: str = "Multi" if i == 0 else "Multis"

    await ctx.send(
        file=await image_to_discord(
            await compose_unit_multi_draw(units=drawn_units,
                                          ssrs=drawn_ssrs) if from_banner.banner_type == BannerType.ELEVEN
            else await compose_unit_five_multi_draw(units=drawn_units),
            "units.png"),
        content=f"{person.mention}: Your shaft" if person is ctx.author
        else f"{person.mention}: Your shaft coming from {ctx.author.mention}",
        embed=discord.Embed(
            title=f"{from_banner.pretty_name} ({rang}x summon)",
            description=f"You did {i + 1}x {multi_msg}. \n With this being your final pull:").set_image(
            url="attachment://units.png"))
    await draw.delete()
    await add_shaft(person, i)


@BOT.group(no_pm=True)
async def custom(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"{ctx.author.mention}:", embed=embeds.CUSTOM_HELP_EMBED)


@custom.command(name="add", aliases=["create", "+"])
async def custom_create(ctx: Context, *, args: typing.Optional[str] = ""):
    data: Dict[str, Any] = parse_custom_unit_args(args)

    if data["url"] == "" or data["name"] == "" or data["type"] is None or data["grade"] is None:
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_ADD_COMMAND_USAGE_EMBED)

    async with aiohttp.ClientSession() as session:
        async with session.get(data["url"]) as resp:
            with BytesIO(await resp.read()) as image_bytes:
                _icon: Img = await compose_icon(attribute=data["type"], grade=data["grade"],
                                                background=Image.open(image_bytes))

                await ctx.send(
                    file=await image_to_discord(img=_icon, image_name="unit.png"),
                    content=f"{ctx.author.mention} this is your created unit",
                    embed=discord.Embed(
                        title=data["name"],
                        color=discord.Color.red() if data["type"] == Type.RED
                        else discord.Color.blue() if data["type"] == Type.BLUE
                        else discord.Color.green()
                    ).set_image(url="attachment://unit.png"))

                if data["race"] is None:
                    data["race"]: Race = Race.UNKNOWN

                if data["affection"] is None:
                    data["affection"]: str = Affection.NONE.value

                await add_custom_unit(name=data["name"],
                                      type_enum=data["type"],
                                      grade=data["grade"],
                                      race=data["race"],
                                      affection_str=data["affection"],
                                      url=data["url"],
                                      creator=ctx.author.id)


@custom.command(name="remove", aliases=["delete", "-"])
async def custom_remove(ctx: Context, *, args: typing.Optional[str] = ""):
    data: Dict[str, Any] = parse_custom_unit_args(args)
    if data["name"] == "":
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_REMOVE_COMMAND_USAGE_EMBED)

    edit_unit: Unit = unit_by_name(data["name"])

    if int(edit_unit.simple_name) != ctx.author.id:
        return await ctx.send(content=f"{ctx.author.mention}", embed=discord.Embed(
            title="Error with ..custom remove", colour=discord.Color.dark_red(),
            description=f"**{edit_unit.name}** wasn't created by you!"))

    await remove_custom_unit(data["name"])
    UNITS.remove(edit_unit)
    create_custom_unit_banner()
    return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_REMOVE_COMMAND_SUCCESS_EMBED)


@custom.command(name="list")
async def custom_list(ctx: Context, *, args: typing.Optional[str] = ""):
    data: Dict[str, Any] = parse_custom_unit_args(args)
    if data["owner"] == 0:
        return await list_units(ctx, criteria="event: custom")

    unit_list: List[Unit] = []
    async for unit_id in parse_custom_unit_ids(data["owner"]):
        unit_list.append(unit_by_id(-1 * unit_id))

    loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Units",
                                              embed=embeds.LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_unit_list(unit_list), "units.png"),
                   embed=discord.Embed().set_image(url="attachment://units.png"))
    await loading.delete()


@custom.command(name="edit")
async def custom_edit(ctx: Context, *, args: typing.Optional[str] = ""):
    data: Dict[str, Any] = parse_custom_unit_args(args)
    if data["name"] == "":
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_USAGE_EMBED)

    edit_unit: Unit = unit_by_name(data["name"])

    if int(edit_unit.simple_name) != ctx.author.id:
        return await ctx.send(content=f"{ctx.author.mention}", embed=discord.Embed(
            title="Error with ..custom remove", colour=discord.Color.dark_red(),
            description=f"**{edit_unit.name}** wasn't created by you!"))

    to_set: List[str] = []
    values: List[str] = []
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
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)

    to_set: str = ", ".join(to_set)

    values.append(data["name"])
    await edit_custom_unit(to_set, values)

    await edit_unit.refresh_icon()
    return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CUSTOM_EDIT_COMMAND_SUCCESS_EMBED)


@BOT.command(no_pm=True)
async def crop(ctx: Context, file_url: Optional[str] = "",
               starting_width: Optional[int] = 0, starting_height: Optional[int] = 0,
               ending_width: Optional[int] = 75, ending_height: Optional[int] = 75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.CROP_COMMAND_USAGE_ERROR_EMBED)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            await ctx.send(content=f"{ctx.author.mention} this is your cropped image",
                           file=await image_to_discord(
                               img.crop((starting_width, starting_height, ending_width, ending_height)),
                               "cropped.png"),
                           embed=discord.Embed().set_image(url="attachment://cropped.png"))


@BOT.command(no_pm=True)
async def resize(ctx: Context, file_url: Optional[str] = "", width: int = 75, height: int = 75):
    if file_url in [None, ""]:
        return await ctx.send(content=f"{ctx.author.mention}", embed=embeds.RESIZE_COMMAND_USAGE_ERROR_EMBED)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            await ctx.send(content=f"{ctx.author.mention} this is your resized image",
                           file=await image_to_discord(img.resize((width, height)), "resized.png"),
                           embed=discord.Embed().set_image(url="attachment://resized.png"))


@BOT.group(name="list", no_pm=True)
async def cmd_list(ctx: Context):
    if ctx.invoked_subcommand is None:
        return await list_units(ctx)


@cmd_list.command(name="unit", aliases=["units"])
async def list_units(ctx: Context, units_per_page: Optional[int] = 5, *, criteria: str = "event: custom"):
    loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Units",
                                              embed=embeds.LOADING_EMBED)
    attr: Dict[str, Any] = parse_arguments(criteria)
    matching_units: List[Unit] = get_matching_units(races=attr["race"],
                                                    grades=attr["grade"],
                                                    types=attr["type"],
                                                    events=attr["event"],
                                                    affections=attr["affection"],
                                                    names=attr["name"],
                                                    jp=attr["jp"])
    paged_unit_list: List[Img] = await compose_paged_unit_list(matching_units, units_per_page)
    max_pages: float = math.ceil(len(matching_units) / units_per_page) - 1
    await loading.delete()

    async def display(page: int):
        _loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Units",
                                                   embed=embeds.LOADING_EMBED)
        message: discord.Message = await ctx.send(file=await image_to_discord(paged_unit_list[page], "units.png"),
                                                  embed=discord.Embed(
                                                      title=f"Units matching {criteria} ({page + 1}/{max_pages + 1})"
                                                  ).set_image(url="attachment://units.png"),
                                                  content=f"{ctx.author.mention}")
        await _loading.delete()

        if page != 0:
            await message.add_reaction(emojis.LEFT_ARROW)

        if page != max_pages:
            await message.add_reaction(emojis.RIGHT_ARROW)

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
async def list_banners(ctx: Context):
    loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Banners",
                                              embed=embeds.LOADING_EMBED)
    await ctx.send(content=f"{ctx.author.mention}",
                   embed=discord.Embed(title="All Banners",
                                       description="\n\n".join(
                                           [f"**{x.name[0]}**: `{x.pretty_name}`" for x in ALL_BANNERS])))
    await loading.delete()


@cmd_list.command(name="tarot")
async def list_tarot(ctx: Context, paged: str = "paged"):
    loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Tarot Cards",
                                              embed=embeds.LOADING_EMBED)
    if paged != "paged":
        await ctx.send(content=ctx.author.mention,
                       file=await image_to_discord(await compose_tarot_list(), "tarot_list.png"),
                       embed=discord.Embed().set_image(url="attachment://tarot_list.png")
                       )
        return await loading.delete()

    async def display(page: int, last_message):
        msg = await ctx.send(content=ctx.author.mention,
                             file=await image_to_discord(await compose_paged_tarot_list(page), "tarot_list.png"),
                             embed=discord.Embed(title=tarot_name(page)).set_image(url="attachment://tarot_list.png")
                             )
        await last_message.delete()

        if page != 1:
            await msg.add_reaction(emojis.LEFT_ARROW)

        if page != 22:
            await msg.add_reaction(emojis.RIGHT_ARROW)

        def check(added_reaction, user):
            return user == ctx.author and str(added_reaction.emoji) in [emojis.LEFT_ARROW, emojis.RIGHT_ARROW]

        try:
            reaction, _ = await BOT.wait_for('reaction_add', check=check, timeout=15)

            if str(reaction.emoji) == emojis.LEFT_ARROW and page != 1:
                return await display(page - 1, msg)

            if str(reaction.emoji) == emojis.RIGHT_ARROW and page != 22:
                return await display(page + 1, msg)
        except asyncio.TimeoutError:
            await msg.clear_reactions()

    await display(1, loading)


@BOT.command(no_pm=True)
async def banner(ctx: Context, *, banner_name: str = "banner one"):
    from_banner: Banner = banner_by_name(banner_name)
    if from_banner is None:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"Can't find the \"{banner_name}\" banner"
                                                  )
                              )
    loading: discord.Message = await ctx.send(content=f"{ctx.author.mention} -> Loading Banner",
                                              embed=embeds.LOADING_EMBED)
    await ctx.send(
        file=await image_to_discord(await compose_banner_list(from_banner, "custom" in from_banner.name),
                                    "banner.png"),
        embed=discord.Embed(title=f"SSRs in {from_banner.pretty_name} ({from_banner.ssr_chance}%)").set_image(
            url="attachment://banner.png"),
        content=f"{ctx.author.mention}")
    await loading.delete()


@BOT.command(no_pm=True)
async def add_banner_unit(ctx: Context, banner_name: str, *, units: str):
    await add_unit_to_banner(banner_name, units)
    await ctx.send(content=f"Units ({units}) added to {banner_name}")


@BOT.command(no_pm=True)
async def add_banner_rate_up_unit(ctx: Context, banner_name: str, *, units: str):
    await add_rate_up_unit_to_banner(banner_name, units)
    await ctx.send(content=f"Rate up units ({units}) added to {banner_name}")


@BOT.command(no_pm=True)
async def update(ctx: Context):
    read_units_from_db()
    read_banners_from_db()
    create_custom_unit_banner()
    create_jp_banner()
    await ctx.send(content=f"{ctx.author.mention} Updated Units & Banners")


@BOT.group(no_pm=True)
async def affection(ctx: Context):
    if ctx.invoked_subcommand is None:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=embeds.AFFECTION_HELP_EMBED)


@affection.command(name="add", aliases=["create", "plus", "+"])
async def affection_add(ctx: Context, *, name: typing.Optional[str]):
    if name.lower in [Affection.SIN.value, Affection.KNIGHT.value, Affection.NONE.value, Affection.ANGEL.value,
                      Affection.CATASTROPHE.value,
                      Affection.COMMANDMENTS.value]:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=embeds.AFFECTION_UNMUTABLE_ERROR_EMBED)

    await add_affection(name, ctx.author.id)
    AFFECTIONS.append(name.lower())
    await ctx.send(content=f"{ctx.author.mention}", embed=embeds.AFFECTION_ADDED_EMBED)


@affection.command(name="edit")
async def affection_edit(ctx: Context, old_name: str, *, new_name: str):
    if old_name.lower() not in AFFECTIONS:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=embeds.AFFECTION_EDITED_EMBED)

    if get_affection_creator(old_name.lower()) != ctx.author.id:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error with ..affections edit",
                                                  colour=discord.Color.dark_red(),
                                                  description=f"**{old_name.lower()}** is not your affection!"))

    await update_affection_name(old_name, new_name)
    AFFECTIONS.append(new_name.lower())
    await ctx.send(content=f"{ctx.author.mention}", embed=embeds.AFFECTION_EDITED_EMBED)


@affection.command(name="transfer", aliases=["move", ">"])
async def affection_transfer(ctx: Context, name: str, owner: discord.Member):
    if name.lower() not in AFFECTIONS:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=embeds.AFFECTION_EDITED_EMBED)

    if get_affection_creator(name.lower()) != ctx.author.id:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error with ..affections edit",
                                                  colour=discord.Color.dark_red(),
                                                  description=f"**{name.lower()}** is not your affection!"))

    await update_affection_owner(name, owner)
    await ctx.send(content=f"{ctx.author.mention}", embed=embeds.AFFECTION_EDITED_EMBED)


@affection.command(name="remove", aliases=["delete", "minus", "-"])
async def affection_remove(ctx: Context, *, name: str):
    if name.lower() not in AFFECTIONS:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=embeds.AFFECTION_REMOVED_EMBED)

    if get_affection_creator(name.lower()) != ctx.author.id:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error with ..affections edit",
                                                  colour=discord.Color.dark_red(),
                                                  description=f"**{name.lower()}** is not your affection!"))
    await remove_affection(name)
    AFFECTIONS.remove(name.lower())
    await ctx.send(content=f"{ctx.author.mention}", embed=embeds.AFFECTION_REMOVED_EMBED)


@affection.command(name="list")
async def affection_list(ctx: Context):
    return await ctx.send(content=f"{ctx.author.mention}",
                          embed=discord.Embed(title="All Affections", description=",\n".join(AFFECTIONS)))


@BOT.command(no_pm=True)
async def box(ctx: Context, user: typing.Optional[discord.Member]):
    if user is None:
        user: discord.Member = ctx.author
    box_d: Dict[int, int] = await read_box(user)
    if len(box_d) == 0:
        return await ctx.send(content=f"{ctx.author.mention}",
                              embed=discord.Embed(title="Error", colour=discord.Color.dark_red(),
                                                  description=f"{user.display_name} has no units!"))
    loading: discord.Member = await ctx.send(content=f"{ctx.author.mention} -> Loading {user.display_name}'s box",
                                             embed=embeds.LOADING_EMBED)
    await ctx.send(file=await image_to_discord(await compose_box(box_d), "box.png"),
                   content=f"{ctx.author.mention}",
                   embed=discord.Embed(title=f"{user.display_name}'s box", colour=discord.Color.gold()).set_image(
                       url="attachment://box.png"))
    await loading.delete()


@BOT.command(no_pm=True)
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


@BOT.group(no_pm=True, aliases=["bj", "jack", "blackj"])
async def blackjack(ctx: Context):
    if ctx.invoked_subcommand is None:
        bot_card_values: List[int] = [ra.randint(1, 11) for _ in range(2)]
        player_card_values: List[int] = [ra.randint(1, 11) for _ in range(2)]

        cards_msg: discord.Message = await ctx.send(content=f"""
                    {ctx.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
                    Bot card is: {bot_card_values[0]}""")

        async def play(last_msg: discord.Message = None):
            await last_msg.clear_reactions()
            if sum(player_card_values) > 21:
                await add_blackjack_game(ctx.author, False)
                return await last_msg.edit(
                    content=f"{ctx.author.mention} you lost! -> Hand of {sum(player_card_values)}")
            if sum(player_card_values) == 21:
                await add_blackjack_game(ctx.author, True)
                if last_msg is None:
                    return await ctx.send(content=f"{ctx.author.mention} you got a Blackjack and won!")
                return await last_msg.edit(content=f"{ctx.author.mention} you got a Blackjack and won!")

            await last_msg.edit(content=f"""
                {ctx.author.mention}'s cards are: {player_card_values}. Total = {sum(player_card_values)}
                Bot card is: {bot_card_values[0]}""")

            await last_msg.add_reaction(emojis.HIT)
            await last_msg.add_reaction(emojis.STAND)

            def check(added_reaction, user):
                return user == ctx.author and str(added_reaction.emoji) in [emojis.HIT, emojis.STAND]

            try:
                reaction, _ = await BOT.wait_for('reaction_add', check=check)

                if str(reaction.emoji) == emojis.HIT:
                    player_card_values.append(ra.randint(1, 11))
                    return await play(last_msg=cards_msg)
                if str(reaction.emoji) == emojis.STAND:
                    await cards_msg.clear_reactions()
                    await add_blackjack_game(ctx.message.author,
                                             21 - sum(player_card_values) < 21 - sum(bot_card_values))
                    return await last_msg.edit(
                        content=f"{ctx.author.mention} you won! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})" if 21 - sum(
                            player_card_values) < 21 - sum(bot_card_values)
                        else f"{ctx.author.mention} you lost! -> Your hand ({sum(player_card_values)}) & Bot hand ({sum(bot_card_values)})")
            except TimeoutError:
                pass

        await play(cards_msg)


@blackjack.command(name="top", aliases=["leaderboard", "lead", "leader", "leading"])
async def blackjack_top(ctx: Context):
    if len([x async for x in get_blackjack_top(ctx.message.guild)]) is None:
        return await ctx.send(content="Nobody played Blackjack yet!")

    return await ctx.send(content=f"{ctx.author.mention}",
                          embed=discord.Embed(
                              title=f"Blackjack Leaderboard in {ctx.guild.name} (Highest Winning Streaks)",
                              description=",\n".join(["**{}.** *{}* ~ Streak of {} wins".format(
                                  data["place"],
                                  await BOT.fetch_user(data["user"]),
                                  data["highest_streak"]
                              ) async for data in get_blackjack_top(ctx.guild)])
                          ).set_thumbnail(url=ctx.guild.icon_url))


@blackjack.command(name="record", aliases=["stats"])
async def blackjack_record(ctx: Context, person: typing.Optional[discord.Member] = None):
    if person is None:
        person: discord.Member = ctx.author
    data: Optional[Tuple[int, int, int, int, int]] = await get_blackjack_stats(person)

    if data is None:
        return await ctx.send(
            content=f"{ctx.author.mention}: You haven't played Blackjack yet!" if person == ctx.author
            else f"{ctx.author.mention}: {person.display_name} hasn't played Blackjack yet!")

    return await ctx.send(
        content=f"{ctx.author.mention} Blackjack History:" if person == ctx.author else f"{ctx.author.mention}: {person.display_name}'s Blackjack History:",
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
async def demon(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"{ctx.author.mention}:", embed=embeds.DEMON_HELP_EMBED)


@demon.command(name="friend", aliases=["friendcode", "code"])
async def demon_friend(ctx: Context, of: typing.Optional[discord.Member]):
    if of is None:
        of = ctx.author

    friendcode: Optional[Tuple[int]] = await get_friendcode(of)

    if friendcode is None:
        if of == ctx.author:
            await ctx.send(
                f"{ctx.author.mention}: You are not registered in the bot yet! `..demon tag <grandcross friendcode> <profile name>` to create one")
        else:
            await ctx.send(f"{ctx.author.mention}: {of.display_name} is not registered in the bot yet!")
    else:
        await ctx.send(f"{ctx.author.mention}: {friendcode[0]}")


@demon.command(name="offer")
async def demon_offer(ctx: Context, reds: int = 0, greys: int = 0, crimsons: int = 0, *, additional_message: str = ""):
    if reds == 0 and greys == 0 and crimsons == 0:
        return await ctx.send(
            content=f"{ctx.author.mention}",
            embed=discord.Embed(
                title="Error",
                description="Please provide at least one demon",
                color=discord.Color.dark_red()
            )
        )
    author: discord.Member = ctx.author
    guild_created_in: discord.Guild = ctx.guild

    async for channel_list_item in get_raid_channels():
        try:
            channel: discord.TextChannel = await BOT.fetch_channel(channel_list_item["channel_id"])
        except discord.Forbidden:
            continue
        guild: discord.Guild = await BOT.fetch_guild(channel_list_item["guild"])

        mentions: List[str] = []

        red_role = await get_demon_role(guild, "red")
        grey_role = await get_demon_role(guild, "grey")
        crimson_role = await get_demon_role(guild, "red")
        all_role = await get_demon_role(guild, "all")

        if reds != 0 and red_role is not None:
            mentions.append(guild.get_role(red_role[0]).mention)
        if greys != 0 and grey_role is not None:
            mentions.append(guild.get_role(grey_role[0]).mention)
        if crimsons != 0 and crimson_role is not None:
            mentions.append(guild.get_role(crimson_role[0]).mention)

        if all_role is not None and red_role is None and grey_role is None and crimson_role is None:
            mentions.append(guild.get_role(all_role[0]).mention)

        to_claim: discord.Message = await channel.send(
            content=", ".join(mentions),
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

        await to_claim.add_reaction(emojis.OK)

        DEMON_OFFER_MESSAGES[to_claim.id]: Dict[str, Any] = {
            "created_in": guild_created_in,
            "guild": guild,
            "channel": channel,
            "creator": author
        }

    if len(DEMON_OFFER_MESSAGES) == 0:
        return await ctx.send(f"{author.mention} no channel to broadcast in found")

    def check(added_reaction, user):
        return user != BOT.user and str(added_reaction.emoji) in emojis.OK

    try:
        added_reaction, user = await BOT.wait_for('reaction_add', check=check, timeout=60 * 60 * 4)

        if user == author:
            await ctx.send(f"{author.mention} deleted your demon offer.")
        else:
            author_friendcode: Optional[Tuple[int]] = await get_friendcode(author)
            claim_friendcode: Optional[Tuple[int]] = await get_friendcode(user)

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

        for offer_id in [message_id for message_id in DEMON_OFFER_MESSAGES if
                         DEMON_OFFER_MESSAGES[message_id]["creator"].id == author.id]:
            try:
                DEMON_OFFER_MESSAGES[offer_id]["claimed_by"] = user
                offer_message: discord.Message = await DEMON_OFFER_MESSAGES[offer_id]["channel"].fetch_message(offer_id)
                new_embed: discord.Embed = discord.Embed(
                    title=f"~~{offer_message.embeds[0].title}~~ Claimed",
                    description=f"~~{offer_message.embeds[0].description}~~"
                ).set_footer(text=f"Claimed by {user.display_name}")
                await offer_message.edit(embed=new_embed)
                await offer_message.clear_reactions()
            except discord.errors.NotFound:
                pass

    except asyncio.TimeoutError:
        offer_messages: List[int] = [message_id for message_id in DEMON_OFFER_MESSAGES if
                                     DEMON_OFFER_MESSAGES[message_id]["creator"].id == author.id]
        for offer_id in offer_messages:
            try:
                msg: discord.Message = await DEMON_OFFER_MESSAGES[offer_id]["channel"].fetch_message(offer_id)
                new_embed: discord.Embed = discord.Embed(
                    title=f"~~{msg.embeds[0].title}~~ Timed out",
                    description=f"~~{msg.embeds[0].description}~~"
                ).set_footer(text="Time ran out.")
                await msg.edit(embed=new_embed)
                await msg.clear_reactions()
            except discord.errors.NotFound:
                pass


@BOT.event
async def on_message(message: discord.Message):  # if people dont share a server. reply to the offer message
    if message.reference is None:
        return await BOT.process_commands(message)

    demon_msg_id: int = message.reference.message_id

    if demon_msg_id not in DEMON_OFFER_MESSAGES:
        return await BOT.process_commands(message)

    offer_data: Dict[str, Any] = DEMON_OFFER_MESSAGES[demon_msg_id]

    if "claimed_by" not in offer_data:
        return await BOT.process_commands(message)

    if len(shared_guilds(offer_data['creator'], offer_data['claimed_by'])) == 0:
        if message.author.id == offer_data['creator'].id:
            await offer_data['claimed_by'].send(
                content=f"Message from {offer_data['creator'].mention} regarding your demon offer:",
                embed=discord.Embed(description=message.content))
        else:
            await offer_data['creator'].send(
                content=f"Message from {offer_data['claimed_by'].mention} regarding your demon offer:",
                embed=discord.Embed(description=message.content))


@demon.command(name="profile", aliases=["create", "tag"])
async def demon_profile(ctx: Context, gc_id: int = 0, name: str = "main"):
    if gc_id == 0:
        return demon_info(ctx)

    if await get_demon_profile(ctx.author, name) is None:
        await create_demon_profile(ctx.author, gc_id, name)
        await ctx.send(f"{ctx.author.mention}: Added profile {name}  with friendcode {gc_id}")
    else:
        if gc_id == -1:
            await delete_demon_profile(ctx.author, name)
            await ctx.send(f"{ctx.author.mention}: Deleted profile {name}")
        else:
            await update_demon_profile(ctx.author, gc_id, name)
            await ctx.send(f"{ctx.author.mention}: Edited profile {name} to friendcode {gc_id}")


@demon.command(name="info", aliases=["me"])
async def demon_info(ctx: Context, of: typing.Optional[discord.Member]):
    if of is None:
        of: discord.Member = ctx.message.author
    await ctx.send(
        content=f"{ctx.author.mention}",
        embed=discord.Embed(
            title=f"Info about {of.display_name}",
            description="Names: \n" + "\n".join([
                "{}: {}".format(x["name"], x["code"])
                async for x in get_profile_name_and_friendcode(of)
            ])
        ))


@demon.command(name="channel")
@has_permissions(manage_channels=True)
async def demon_channel(ctx: Context, action: str = "none"):
    if action == "none":
        await add_raid_channel(ctx.message)
        return await ctx.send(f"{ctx.author.mention} added demon channel!")

    channels: List[discord.TextChannel] = [
        (await BOT.fetch_channel(x["channel_id"])).name + " in " + (await BOT.fetch_guild(x["guild"])).name
        async for x in get_raid_channels()]
    await ctx.author.send("\n".join(channels))


@demon.command(name="role")
@has_permissions(manage_roles=True)
async def demon_role(ctx: Context, role: discord.Role, demon_type: str):
    await add_demon_role(role, demon_type)
    await ctx.send(f"{ctx.author.mention}: Added Demon role!")


@BOT.group(no_pm=True, aliases=["tourney"])
async def tournament(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)


@tournament.command(name="signup")
async def tournament_signup(ctx: Context, gc_code: int = 0, team_cc: float = 0,
                            unit1: int = 0, unit2: int = 0, unit3: int = 0, unit4: int = 0):
    if 0 in [gc_code, team_cc, unit1, unit2, unit3, unit4]:
        return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

    _team: List[Unit] = []

    for unit_id in [unit1, unit2, unit3, unit4]:
        u: Unit = unit_by_id(unit_id)
        if u is None:
            return await ctx.send(f"{ctx.author.mention}: No Unit with ID: {unit_id} found!")

        _team.append(u)

    if await create_tourney_profile(ctx.author, gc_code, team_cc, [unit1, unit2, unit3, unit4]):
        await ctx.send(f"{ctx.author.mention}:",
                       file=await image_to_discord(await compose_team(_team), "team.png"),
                       embed=discord.Embed(
                           title="Registered Profile!",
                           colour=discord.Color.green(),
                           description=f"""
            CC: `{team_cc}`

            To edit your Team CC: 
                `..tourney cc <new cc>`

            Friend code: `{gc_code}`

            To edit your Friend code:
                `..tourney code <new friend code>`

            Registered Team:
            """
                       ).set_image(url="attachment://team.png"))
    else:
        await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Profile already exist",
            colour=discord.Color.red(),
            description="""
            To edit your team cc: `..tourney cc <new cc>`

            To edit your friend code: `..tourney code <new friend code>`
            """
        ))


@tournament.command(name="code")
async def tournament_code(ctx: Context, gc_code: int = 0):
    if gc_code == 0:
        return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

    if await edit_tourney_friendcode(ctx.author, gc_code):
        await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Updated Profile!",
            colour=discord.Color.green(),
            description=f"Your new friend code is: {gc_code}"
        ))
    else:
        await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Profile doesn't exist",
            colour=discord.Color.red(),
            description="To create one: `..tourney signup <friend code> <team cc>`"
        ))


@tournament.command(name="cc")
async def tournament_cc(ctx: Context, cc: float = 0):
    if cc == 0:
        return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

    if await edit_tourney_cc(ctx.author, cc):
        await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Updated Profile!",
            colour=discord.Color.green(),
            description=f"Your new cc is: {cc}"
        ))
    else:
        await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Profile doesn't exist",
            colour=discord.Color.red(),
            description="To create one: `..tourney signup <friend code> <team cc>`"
        ))


@tournament.command(name="team")
async def tournament_team(ctx: Context, unit1: int = 0, unit2: int = 0, unit3: int = 0, unit4: int = 0):
    if 0 in [unit1, unit2, unit3, unit4]:
        return await ctx.send(content=ctx.author.mention, embed=embeds.TourneyEmbeds.HELP)

    _team: List[Unit] = []

    for unit_id in [unit1, unit2, unit3, unit4]:
        u: Unit = unit_by_id(unit_id)
        if u is None:
            return await ctx.send(f"{ctx.author.mention}: No Unit with ID: {unit_id} found!")

        _team.append(u)

    if await edit_tourney_team(ctx.author, [unit1, unit2, unit3, unit4]):
        await ctx.send(f"{ctx.author.mention}:",
                       file=await image_to_discord(await compose_team(_team), "team.png"),
                       embed=discord.Embed(
                           title="Updated Profile!",
                           colour=discord.Color.green(),
                           description="Your new team is:"
                       ).set_image(url="attachment://team.png"))
    else:
        await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Profile doesn't exist",
            colour=discord.Color.red(),
            description="To create one: `..tourney signup <friend code> <team cc>`"
        ))


@tournament.command(name="stats", aliases=["profile"])
async def tournament_stats(ctx: Context, of: typing.Optional[discord.Member]):
    if of is None:
        of: discord.Member = ctx.author

    data: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(of)
    if data is None:
        return await ctx.send(content=ctx.author.mention, embed=discord.Embed(
            title="Error",
            colour=discord.Color.red(),
            description=f"{of.display_name} has no registered profile"
        ))

    _team: List[Unit] = [unit_by_id(x) for x in data["team"]]

    return await ctx.send(content=ctx.author.mention,
                          file=await image_to_discord(await compose_team(_team), "team.png"),
                          embed=discord.Embed(
                              title=f"Profile of: {of.display_name}",
                              description=f"""
        Friend code: `{data["gc_code"]}` 

        Team CC: `{data["team_cc"]}`

        Won: `{data["won"]}`

        Lost: `{data["lost"]}`

        Registered Team:
        """
                          ).set_image(url="attachment://team.png"))


@tournament.command(name="challenge", aliases=["fight"])
async def tournament_challenge(ctx: Context, enemy: typing.Optional[discord.Member]):
    if enemy is None or enemy == ctx.author:
        return await ctx.send(f"{ctx.author.mention}: Please provide a enemy you want to challenge")

    author_data: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(ctx.author)
    enemy_data: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(enemy)

    if author_data is None or enemy_data is None:
        return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Profile doesn't exist",
            colour=discord.Color.red(),
            description="To create one: `..tourney signup <friend code> <team cc>`"
        ))

    if author_data["team_cc"] > enemy_data["team_cc"]:
        return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Too high CC",
            colour=discord.Color.red(),
            description="You can't challenge someone who has __less__ CC then you."
        ))

    await add_tourney_challenge(ctx.author, enemy)
    await ctx.send(f"{enemy.mention}: {ctx.author.mention} has challenged you!")


@tournament.command(name="accept")
async def tournament_accept(ctx: Context, enemy: typing.Optional[discord.Member]):
    if enemy is None or enemy == ctx.author:
        return await ctx.send(f"{ctx.author.mention}: Please provide a challenger you want to accept")

    if await tourney_in_game(enemy):
        return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Enemy still in a game",
            colour=discord.Color.red(),
            description=f"{enemy.display_name} is still in a game!"
        ))
    if await tourney_in_game(ctx.author):
        return await ctx.send(f"{ctx.author.mention}:", embed=discord.Embed(
            title="Error: Enemy still in a game",
            colour=discord.Color.red(),
            description="You are still in a game! \n\n `..tourney report <@Winner> <@Looser>` to finish the game"
        ))
    if enemy.id not in [x async for x in get_tourney_challengers(ctx.author)]:
        return await ctx.send(f"{ctx.author.mention}: {enemy.display_name} didn't challenge you!")

    p1_profile: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(ctx.author)
    p2_profile: Optional[Dict[str, Union[int, float, List[int]]]] = await get_tourney_profile(enemy)

    p1_team: List[Unit] = [unit_by_id(x) for x in p1_profile["team"]]
    p2_team: List[Unit] = [unit_by_id(x) for x in p2_profile["team"]]

    await accept_challenge(ctx.author, enemy)
    await ctx.send(f"{ctx.author.mention} ({p1_profile['gc_code']}) vs {enemy.mention} ({p2_profile['gc_code']})",
                   file=await image_to_discord(await compose_pvp(ctx.author, p1_team, enemy, p2_team), "match.png"),
                   embed=discord.Embed(
                       title=f"{ctx.author.display_name} vs {enemy.display_name}",
                       description=f"{p1_profile['team_cc']}CC vs {p2_profile['team_cc']}CC \n\n Please do `..tourney report <@Winner> <@Looser>` to end the game!"
                   ).set_image(url="attachment://match.png"))


@tournament.command(name="decline")
async def tournament_decline(ctx: Context, enemy: typing.Optional[discord.Member]):
    if enemy is None or enemy == ctx.author:
        return await ctx.send(f"{ctx.author.mention}: Please provide a challenger you want to accept")

    if enemy.id not in [x async for x in get_tourney_challengers(ctx.author)]:
        return await ctx.send(f"{ctx.author.mention}: {enemy.display_name} didn't challenge you!")

    await decline_challenge(ctx.author, enemy)
    await ctx.send(f"{enemy.mention} {ctx.author.mention} has declined your challenge.")


@tournament.command(name="challengers")
async def tournament_challengers(ctx: Context):
    if len([x async for x in get_tourney_challengers(ctx.author)]) == 0:
        return await ctx.send(f"{ctx.author.mention}: No challengers.")
    await ctx.send(ctx.author.mention, embed=discord.Embed(
        title=f"{ctx.author.display_name}'s challengers",
        description="\n".join(
            [(await BOT.fetch_user(x)).display_name async for x in get_tourney_challengers(ctx.author)])
    ))


@tournament.command(name="report")
async def tournament_report(ctx: Context, winner: typing.Optional[discord.Member],
                            looser: typing.Optional[discord.Member]):
    if winner == looser:
        return await ctx.send(f"{ctx.author.mention} Winner and looser can't be the same person!")

    if ctx.author not in (winner, looser):
        return await ctx.send(f"{ctx.author.mention}: You can't report the game of someone else.")

    if not tourney_in_game_with(winner, looser):
        return await ctx.send(f"{winner.display_name} & {looser.display_name} were not in a game!")

    await report_tourney_game(winner, looser)

    unit_to_build = get_random_unit()

    await ctx.send(f"{winner.mention} won against {looser.mention}",
                   file=await image_to_discord(unit_to_build.icon, "unit.png"),
                   embed=discord.Embed(
                       title=f"{looser.display_name} you now have to build out:",
                       description=unit_to_build.name
                   ).set_image(url="attachment://unit.png"))


@tournament.command(name="top")
async def tournament_top(ctx: Context):
    await ctx.send(ctx.author.mention, embed=discord.Embed(
        title="Tournament Participants with most wins",
        description="\n".join(
            [f"**{x['place']}.** {(await BOT.fetch_user(x['member_id'])).mention} with {x['won']} wins"
             async for x in get_tourney_top_profiles()])
    ))


@BOT.command(no_pm=True)
async def tarot(ctx: Context):
    __units: List[int] = [ra.randint(1, 22) for _ in range(4)]
    __food: List[int] = ra.randint(1, 4)

    async def send_msg(_units, _food) -> None:
        while any(_units.count(element) > 1 for element in _units):
            _units: List[int] = [ra.randint(1, 22) for _ in range(4)]

        loading: discord.Message = await ctx.send(content=ctx.author.mention, embed=embeds.LOADING_EMBED)
        msg: discord.Message = await ctx.send(
            file=await image_to_discord(await compose_tarot(_units[0], _units[1], _units[2], _units[3], _food),
                                        "tarot.png"),
            content=ctx.author.mention)
        await loading.delete()

        for emoji in [emojis.NO_1, emojis.NO_2, emojis.NO_3, emojis.NO_4]:
            await msg.add_reaction(emoji)

        def check(added_reaction, user):
            return user == ctx.author and str(added_reaction.emoji) in [emojis.NO_1, emojis.NO_2, emojis.NO_3,
                                                                        emojis.NO_4]

        try:
            added_reaction, _ = await BOT.wait_for('reaction_add', check=check, timeout=15)

            await msg.delete()

            if str(added_reaction.emoji) == emojis.NO_1:
                _units[0] = ra.randint(1, 22)
            elif str(added_reaction.emoji) == emojis.NO_2:
                _units[1] = ra.randint(1, 22)
            elif str(added_reaction.emoji) == emojis.NO_3:
                _units[2] = ra.randint(1, 22)
            elif str(added_reaction.emoji) == emojis.NO_4:
                _units[3] = ra.randint(1, 22)

            await send_msg(_units, _food)
        except asyncio.TimeoutError:
            await msg.clear_reactions()

    await send_msg(__units, __food)


@BOT.command()
async def icon(ctx: Context, of: Unit):
    async with aiohttp.ClientSession() as session:
        async with session.get(ctx.message.attachments[0].url) as resp:
            with BytesIO(await resp.read()) as a:
                img: Img = await compose_icon(attribute=of.type, grade=of.grade, background=Image.open(a))
                await ctx.send(file=await image_to_discord(img))


@BOT.group(name="cc", no_pm=True)
async def cc_cmd(ctx: Context):
    if ctx.invoked_subcommand is not None:
        return

    if len(ctx.message.attachments) == 0:
        return ctx.send(f"{ctx.author.mention}: no image attached!")

    loading: discord.Message = await ctx.send(f"{ctx.author.mention}: Reading your CC...")
    async with aiohttp.ClientSession() as session:
        async with session.get(ctx.message.attachments[0].url) as resp:
            with BytesIO(await resp.read()) as a:
                if await is_cc_knighthood(ctx.guild):
                    read_cc = await read_kh_cc_from_image(Image.open(a))

                    if read_cc == -1:
                        return await loading.edit(
                            content=f"{ctx.author.mention} Can't read CC from Image. Please make sure to provide a full screenshot")
                else:
                    read_cc: float = await read_base_cc_from_image(Image.open(a))

                    if read_cc == -1:
                        return await loading.edit(
                            content=f"{ctx.author.mention} Can't read CC from Image. Please make sure to provide a full screenshot")
                role_id: Optional[Tuple[int]] = await get_cc_role(ctx.guild, read_cc)

                if role_id is None:
                    return await loading.edit(content=f"{ctx.author.mention} no CC roles registered for {read_cc} CC!")

                role: discord.Role = ctx.guild.get_role(role_id[0])

                for cc_role in [ctx.guild.get_role(x) async for x in get_cc_roles(ctx.guild)]:
                    if cc_role in ctx.author.roles:
                        await ctx.author.remove_roles(cc_role)

                await ctx.author.add_roles(role)
                await loading.edit(content=f"Gave {role.name} to {ctx.author.mention}")


@cc_cmd.command(name="role")
@has_permissions(manage_roles=True)
async def cc_role_register(ctx: Context, role: discord.Role, min_cc: float, is_knighthood_only: bool):
    await add_cc_role(role, min_cc, is_knighthood_only)
    await ctx.send(f"Role: {role.name} added!")


@BOT.command(name="age")
async def age_cmd(ctx: Context):
    await ctx.send(
        f"{ctx.author.mention} you're on {ctx.guild.name} for {td_format((datetime.now() - ctx.author.joined_at))}")


@BOT.command(name="awake")
async def awake_cmd(ctx: Context, _unit: Unit, start: Optional[int] = 0, to: Optional[int] = 6):
    data = calc_cost(_unit, min(max(start, 0), 6) + 1, min(max(to, 0), 6) + 1)
    await ctx.send(
        file=await image_to_discord(await compose_awakening(data, start, to)),
        content=f"To awaken *{_unit.name}* from **{start}*** to **{to}*** it takes:"
    )


@BOT.command(name="code")
async def code_cmd(ctx: Context):
    await ctx.send(f"{ctx.author.mention}: https://github.com/WhoIsAlphaHelix/evilmortybot")


def start_up_bot(token_path: str = "data/bot_token.txt", is_beta: bool = False):
    global TOKEN, IS_BETA
    try:
        read_affections_from_db()
        read_units_from_db()
        read_banners_from_db()

        with open(token_path, 'r') as token_file:
            TOKEN = token_file.read()

        for f_type in ["atk", "crit_ch", "crit_dmg", "pierce"]:
            if f_type == "atk":
                name: str = "Attack"
            elif f_type == "crit_ch":
                name: str = "Crit Chance"
            elif f_type == "crit_dmg":
                name: str = "Crit damage"
            else:
                name: str = "Pierce"
            food_list: List[Food] = []
            for i in range(1, 4):
                with Image.open(f"gc/food/{f_type}_{i}.png") as food_image:
                    food_list.append(food_image.resize((FOOD_SIZE, FOOD_SIZE)))
            TAROT_FOOD[1].append(Food(f_type, name, food_list))
            LOGGER.log(logging.INFO, f"Added food {name}")

        for f_type in ["res", "crit_def", "crit_res", "lifesteal"]:
            if f_type == "res":
                name: str = "Resistance"
            elif f_type == "crit_def":
                name: str = "Crit Defense"
            elif f_type == "crit_res":
                name: str = "Crit Resistance"
            else:
                name: str = "Lifesteal"
            food_list: List[Food] = []
            for i in range(1, 4):
                with Image.open(f"gc/food/{f_type}_{i}.png") as food_image:
                    food_list.append(food_image.resize((FOOD_SIZE, FOOD_SIZE)))
            TAROT_FOOD[2].append(Food(f_type, name, food_list))
            LOGGER.log(logging.INFO, f"Added food {name}")

        for f_type in ["cc", "ult", "evade"]:
            if f_type == "cc":
                name: str = "CC"
            elif f_type == "ult":
                name: str = "Ult Gauge"
            else:
                name: str = "Evasion"
            food_list: List[Food] = []
            for i in range(1, 4):
                with Image.open(f"gc/food/{f_type}_{i}.png") as food_image:
                    food_list.append(food_image.resize((FOOD_SIZE, FOOD_SIZE)))
            TAROT_FOOD[3].append(Food(f_type, name, food_list))
            LOGGER.log(logging.INFO, f"Added food {name}")

        for f_type in ["def", "hp", "reg", "rec"]:
            if f_type == "def":
                name: str = "Defense"
            elif f_type == "hp":
                name: str = "HP"
            elif f_type == "reg":
                name: str = "Regeneration Rate"
            else:
                name: str = "Recovery Rate"
            food_list: List[Food] = []
            for i in range(1, 4):
                with Image.open(f"gc/food/{f_type}_{i}.png") as food_image:
                    food_list.append(food_image.resize((FOOD_SIZE, FOOD_SIZE)))
            TAROT_FOOD[4].append(Food(f_type, name, food_list))
            LOGGER.log(logging.INFO, f"Added food {name}")

        IS_BETA = is_beta

        BOT.run(TOKEN)
    finally:
        sql.connection.close()


if __name__ == '__main__':
    start_up_bot()
