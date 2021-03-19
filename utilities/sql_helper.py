from discord.ext.commands import Bot

from utilities.banner_data import Banner, map_bannertype, create_custom_unit_banner
from utilities.unit_data import *

connection: sqlite.Connection = sqlite.connect("data/data.db")


def read_units_from_db():
    cursor = connection.cursor()
    UNITS.clear()
    R_UNITS.clear()
    SR_UNITS.clear()

    for row in cursor.execute('SELECT * FROM units'):
        UNITS.append(Unit(
            unit_id=row[0],
            name=row[1],
            simple_name=row[2],
            alt_names=None,
            type_enum=map_attribute(row[3]),
            grade=map_grade(row[4]),
            race=map_race(row[5]),
            event=map_event(row[6]),
            affection_str=map_affection(row[7]),
            icon_path=row[8] if row[0] < 0 else "gc/icons/{}.png",
            is_jp=row[9] == 1,
        ))
        print(f"Registering Unit: {row[1]} ({row[0]}) is JP? {row[9] == 1}")

    R_UNITS.extend([x for x in UNITS if x.grade == Grade.R and x.event == Event.GC])
    SR_UNITS.extend([x for x in UNITS if x.grade == Grade.SR and x.event == Event.GC])


def read_affections_from_db():
    connection.commit()
    cursor = connection.cursor()
    for row in cursor.execute('SELECT * FROM affections'):
        AFFECTIONS.append(row[0])
        print(f"Loaded {row[0]} - affection")


def read_banners_from_db():
    ALL_BANNERS.clear()
    connection.commit()
    cursor = connection.cursor()
    cursor2 = connection.cursor()
    for row in cursor.execute('SELECT * FROM banners ORDER BY "order"'):
        banner_name_data = cursor2.execute('SELECT alternative_name FROM banner_names WHERE name=?',
                                           (row[0],)).fetchall()
        banner_unit_data = cursor2.execute('SELECT unit_id FROM banners_units WHERE banner_name=?', (row[0],)).fetchall()
        banner_rate_up_unit_data = cursor2.execute('SELECT unit_id FROM banners_rate_up_units WHERE banner_name=?',
                                                   (row[0],)).fetchall()
        banner_names = [row[0]]
        unit_list = []
        rate_up_unit_list = []

        for sql_banner_names in banner_name_data:
            banner_names.append(sql_banner_names[0])
        for sql_unit_id in banner_unit_data:
            unit_list.append(unit_by_id(sql_unit_id[0]))
        for sql_unit_id in banner_rate_up_unit_data:
            rate_up_unit_list.append(unit_by_id(sql_unit_id[0]))

        if len(unit_list) == 0:
            continue

        b = Banner(
            name=banner_names,
            pretty_name=row[1],
            ssr_unit_rate=row[2],
            sr_unit_rate=row[3],
            bg_url=row[4],
            r_unit_rate=row[5],
            ssr_unit_rate_up=row[6],
            includes_all_sr=row[7] == 1,
            includes_all_r=row[8] == 1,
            banner_type=map_bannertype(row[9]),
            units=unit_list,
            rate_up_units=rate_up_unit_list
        )
        ALL_BANNERS.append(b)


async def unit_with_chance(from_banner: Banner, user: discord.Member) -> Unit:
    draw_chance = round(ra.uniform(0, 100), 4)

    if from_banner.ssr_chance >= draw_chance or len(from_banner.sr_units) == 0:
        u = from_banner.ssr_units[ra.randint(0, len(from_banner.ssr_units) - 1)]
    elif from_banner.ssr_rate_up_chance >= draw_chance and len(from_banner.rate_up_units) != 0:
        u = from_banner.rate_up_units[ra.randint(0, len(from_banner.rate_up_units) - 1)]
    elif from_banner.sr_chance >= draw_chance or len(from_banner.r_units) == 0:
        u = from_banner.sr_units[ra.randint(0, len(from_banner.sr_units) - 1)]
    else:
        u = from_banner.r_units[ra.randint(0, len(from_banner.r_units) - 1)]

    if user is not None:
        await add_user_pull(user, u.grade == Grade.SSR)
        await add_unit_to_box(user, u)
    await u.set_icon()
    return u


async def get_top_shafts(bot: Bot, guild: discord.Guild):
    cursor = connection.cursor()
    for i, row in enumerate(cursor.execute(
            'SELECT user_id,'
            ' shafts'
            ' FROM user_pulls'
            ' WHERE guild=? AND pull_amount > 99'
            ' ORDER BY shafts'
            ' DESC LIMIT 10',
            (guild.id,))):
        try:
            yield {
                "place": i+1,
                "name": (await bot.fetch_user(row[0])).mention,
                "shafts": row[1]
            }
        except discord.NotFound:
            connection.cursor().execute('DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                                        (guild.id, row[0]))
            yield {
                "place": i + 1,
                "name": "User",
                "shafts": row[1]
            }


async def get_top_lucky(bot: Bot, guild: discord.Guild):
    cursor = connection.cursor()
    for i, row in enumerate(cursor.execute(
            'SELECT user_id,'
            ' pull_amount,'
            ' round((CAST(ssr_amount as REAL)/CAST(pull_amount as REAL)), 4) * 100 percent '
            'FROM user_pulls'
            ' WHERE guild=? AND pull_amount > 99'
            ' ORDER BY percent'
            ' DESC LIMIT 10',
            (guild.id,))):
        try:
            yield {
                "place": i+1,
                "name": (await bot.fetch_user(row[0])).mention,
                "luck": round(row[2], 2),
                "pull-amount": row[1]
            }
        except discord.NotFound:
            connection.cursor().execute(
                'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                (guild.id, row[0]))
            yield {
                "place": i + 1,
                "name": "User",
                "luck": round(row[2], 2),
                "pull-amount": row[1]
            }


async def get_top_ssrs(bot: Bot, guild: discord.Guild):
    cursor = connection.cursor()
    for i, row in enumerate(cursor.execute(
            'SELECT user_id,'
            ' ssr_amount,'
            ' pull_amount'
            ' FROM user_pulls WHERE guild=? AND pull_amount > 99'
            ' ORDER BY ssr_amount'
            ' DESC LIMIT 10',
            (guild.id,))):
        try:
            yield {
                "place": i+1,
                "name": (await bot.fetch_user(row[0])).mention,
                "ssrs": row[1],
                "pull-amount": row[2]
            }
        except discord.NotFound:
            connection.cursor().execute(
                'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                (guild.id, row[0]))
            yield {
                "place": i + 1,
                "name": "User",
                "ssrs": row[1],
                "pull-amount": row[2]
            }


async def get_top_units(bot: Bot, guild: discord.Guild):
    cursor = connection.cursor()
    for i, row in enumerate(cursor.execute(
            'SELECT user_id,'
            ' pull_amount'
            ' FROM user_pulls'
            ' WHERE guild=? AND pull_amount > 99'
            ' ORDER BY pull_amount'
            ' DESC LIMIT 10',
            (guild.id,))):
        try:
            yield {
                "place": i+1,
                "name": (await bot.fetch_user(row[0])).mention,
                "pull-amount": row[2]
            }
        except discord.NotFound:
            connection.cursor().execute(
                'DELETE FROM "user_pulls" WHERE main.user_pulls.guild=? AND user_pulls.user_id=?',
                (guild.id, row[0]))
            yield {
                "place": i + 1,
                "name": "User",
                "pull-amount": row[2]
            }


async def get_user_pull(user: discord.Member) -> dict:
    cursor = connection.cursor()
    data = cursor.execute('SELECT * FROM user_pulls WHERE user_id=? AND guild=?', (user.id, user.guild.id)).fetchone()
    if data is None:
        return {}
    return {"ssr_amount": data[1], "pull_amount": data[2], "guild": data[3], "shafts": data[4]}


async def add_user_pull(user: discord.Member, got_ssr: bool):
    data = await get_user_pull(user)
    cursor = connection.cursor()
    if len(data) == 0:
        cursor.execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                       (user.id, 1 if got_ssr else 0, 1, user.guild.id, 0))
    else:
        if got_ssr:
            cursor.execute('UPDATE user_pulls SET ssr_amount=?, pull_amount=? WHERE user_id=? AND guild=?',
                           (data["ssr_amount"] + 1, data["pull_amount"] + 1, user.id, user.guild.id))
        else:
            cursor.execute('UPDATE user_pulls SET pull_amount=? WHERE user_id=? AND guild=?',
                           (data["pull_amount"] + 1, user.id, user.guild.id))


async def read_box(user: discord.Member) -> dict:
    box_d = {}
    cursor = connection.cursor()
    for row in cursor.execute("""SELECT box_units.unit_id, box_units.amount
                                 FROM box_units INNER JOIN units u ON u.unit_id = box_units.unit_id
                                 WHERE user_id=? AND guild=?
                                 ORDER BY u.grade DESC, box_units.amount DESC;""",
                              (user.id, user.guild.id)):
        box_d[row[0]] = row[1]
    return box_d


async def add_unit_to_box(user: discord.Member, unit_to_add: Unit):
    cursor = connection.cursor()
    data = cursor.execute('SELECT amount FROM box_units WHERE user_id=? AND guild=? AND unit_id=?',
                          (user.id, user.guild.id, unit_to_add.unit_id)).fetchone()
    if data is None:
        cursor.execute('INSERT INTO box_units VALUES (?, ?, ?, ?)', (user.id, user.guild.id, unit_to_add.unit_id, 1))
    else:
        if data[0] < 1000:
            cursor.execute('UPDATE box_units SET amount=? WHERE user_id=? AND guild=? AND unit_id=?',
                           (data[0] + 1, user.id, user.guild.id, unit_to_add.unit_id))


async def add_shaft(user: discord.Member, amount: int):
    data = await get_user_pull(user)
    cursor = connection.cursor()
    if len(data) != 0:
        cursor.execute('UPDATE user_pulls SET shafts=? WHERE user_id=? AND guild=?',
                       (data["shafts"] + amount, user.id, user.guild.id))
    else:
        cursor.execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                       (user.id, 0, 0, user.guild.id, amount))
    connection.commit()


async def add_custom_unit(name: str, creator: int, type_enum: Type, grade: Grade, url: str, race: Race,
                          affection_str: str):
    cursor = connection.cursor()
    u = Unit(unit_id=(-1 * len([x for x in UNITS if x.event == Event.CUS]) - 1),
             name=name,
             type_enum=type_enum,
             grade=grade,
             race=race,
             event=Event.CUS,
             affection_str=affection_str,
             simple_name=str(creator),
             icon_path=url)

    UNITS.append(u)
    create_custom_unit_banner()

    cursor.execute(
        'INSERT INTO units (unit_id, name, simple_name, type, grade, race, event, affection, icon_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (u.unit_id, u.name, str(creator), type_enum.value, grade.value, race.value, u.event.value, affection_str, url)
    )
    connection.commit()


async def remove_custom_unit(unit_name: str):
    cursor = connection.cursor()
    cursor.execute('DROP FROM custom_units WHERE name=?', (unit_name,))
    connection.commit()


async def parse_custom_unit_ids(owner: int):
    cursor = connection.cursor()
    for row in cursor.execute('SELECT unit_id FROM units WHERE simple_name=?', (owner,)).fetchall():
        yield row[0]


async def edit_custom_unit(to_set: str, values: List):
    cursor = connection.cursor()
    cursor.execute("UPDATE custom_units SET " + to_set + " WHERE name=?", tuple(values))
    connection.commit()


async def add_unit_to_banner(banner: str, units: str):
    cursor = connection.cursor()
    for u_id in [int(x) for x in units.replace(" ", "").split(",")]:
        cursor.execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner, u_id))
    connection.commit()


async def add_rate_up_unit_to_banner(banner: str, units: str):
    cursor = connection.cursor()
    for u_id in [int(x) for x in units.replace(" ", "").split(",")]:
        cursor.execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner, u_id))
    connection.commit()


async def add_affection(name: str, owner: int):
    cursor = connection.cursor()
    cursor.execute('INSERT OR IGNORE INTO affections VALUES (?, ?)', (name.lower(), owner))
    connection.commit()


async def get_affection_creator(name: str):
    cursor = connection.cursor()
    return cursor.execute('SELECT creator FROM affections where name=?', (name.lower(),)).fetchone()[0]


async def update_affection_name(old_name: str, new_name: str):
    cursor = connection.cursor()
    cursor.execute('UPDATE affections SET name=? WHERE name=?', (new_name.lower(), old_name.lower()))
    connection.commit()


async def update_affection_owner(name: str, owner: int):
    cursor = connection.cursor()
    cursor.execute('UPDATE affections SET creator=? WHERE name=?', (owner, name.lower()))
    connection.commit()


async def remove_affection(name: str):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM affections WHERE name=?', (name.lower(),))
    connection.commit()


async def add_blackjack_game(user: discord.Member, won: bool):
    cursor = connection.cursor()
    data = cursor.execute(
        'SELECT won, lost, win_streak, highest_streak, last_result FROM blackjack_record WHERE user=? AND guild=?',
        (user.id, user.guild.id)).fetchone()
    if data is None:
        cursor.execute('INSERT INTO blackjack_record VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (user.id, user.guild.id, 1 if won else 0, 0 if won else 1, 1 if won else 0, 1 if won else 0,
                        1 if won else 0))
    else:
        if won:
            if data[4] == 1:  # last was won
                cursor.execute(
                    'UPDATE blackjack_record SET won=?, win_streak=?, highest_streak=?, last_result=1 WHERE user=? AND guild=?',
                    (data[0] + 1, data[2] + 1, data[2] + 1 if data[2] + 1 > data[3] else data[3], user.id,
                     user.guild.id))
            else:  # last was lost
                cursor.execute(
                    'UPDATE blackjack_record SET won=?, win_streak=1, highest_streak=?, last_result=1 WHERE user=? AND guild=?',
                    (data[0] + 1, data[3] + 1 if data[2] + 1 > data[3] else data[3], user.id, user.guild.id))
        else:
            cursor.execute('UPDATE blackjack_record SET lost=?, win_streak=0, last_result=0 WHERE user=? AND guild=?',
                           (data[1] + 1, user.id, user.guild.id))
    connection.commit()


async def get_blackjack_top(guild: discord.Guild):
    cursor = connection.cursor()
    for row in cursor.execute(
            'SELECT row_number() over (ORDER BY highest_streak), user, highest_streak FROM blackjack_record WHERE guild=? ORDER BY highest_streak DESC LIMIT 10',
            (guild.id,)):
        yield {"place": row[0], "user": row[1], "highest_streak": row[2]}


async def get_blackjack_stats(of: discord.Member):
    cursor = connection.cursor()
    return cursor.execute(
        'SELECT won, lost, win_streak, last_result, highest_streak FROM blackjack_record WHERE user=? AND guild=?',
        (of.id, of.guild.id)).fetchone()


async def get_raid_channels():
    cursor = connection.cursor()
    for row in cursor.execute('SELECT * FROM "raid_channels"'):
        yield {"guild": row[0], "channel_id": row[1]}


async def add_raid_channel(by: discord.Message):
    cursor = connection.cursor()
    cursor.execute('INSERT INTO "raid_channels" VALUES (?, ?)', (by.guild.id, by.channel.id))
    connection.commit()


async def get_friendcode(of: discord.Member):
    cursor = connection.cursor()
    return cursor.execute('SELECT gc_id FROM "users" WHERE discord_id=?', (of.id,)).fetchone()


async def get_profile_name_and_friendcode(of: discord.Member):
    cursor = connection.cursor()
    for row in cursor.execute('SELECT name, gc_id FROM "users" WHERE discord_id=?', (of.id,)):
        yield {"name": row[0], "code": row[1]}


async def get_demon_profile(of: discord.Member, name: str):
    cursor = connection.cursor()
    return cursor.execute('SELECT * FROM "users" WHERE discord_id=? AND name=?', (of.id, name.lower())).fetchone()


async def create_demon_profile(of: discord.Member, gc_id: int, name: str):
    cursor = connection.cursor()
    cursor.execute('INSERT OR IGNORE INTO "users" VALUES (?, ?, ?)', (of.id, gc_id, name.lower()))
    connection.commit()


async def delete_demon_profile(of: discord.Member, name: str):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM "users" WHERE name=? AND discord_id=?', (name.lower(), of.id))
    connection.commit()


async def update_demon_profile(of: discord.Member, gc_id: int, name: str):
    cursor = connection.cursor()
    cursor.execute('UPDATE "users" SET gc_id=?, name=? WHERE discord_id=? AND name=?',
                   (gc_id, name.lower(), of.id, name.lower()))
    connection.commit()


async def create_tourney_profile(of: discord.Member, gc_id: int, cc: float, team: List[int]):
    cursor = connection.cursor()
    try:
        cursor.execute('INSERT INTO "tourney_profiles" VALUES (?, ?, ?, ?, ?, ?)', (of.id, gc_id, cc, 0, 0, ",".join([str(x) for x in team])))
        connection.commit()
        return True
    except sqlite.IntegrityError:
        return False


async def edit_tourney_friendcode(of: discord.Member, gc_id: int):
    cursor = connection.cursor()

    if cursor.execute('SELECT * FROM "tourney_profiles" WHERE discord_id=?', (of.id, )).fetchone() is None:
        return False

    cursor.execute('UPDATE "tourney_profiles" SET gc_code=? WHERE discord_id=?', (gc_id, of.id))
    connection.commit()
    return True


async def edit_tourney_cc(of: discord.Member, cc: float):
    cursor = connection.cursor()

    if cursor.execute('SELECT * FROM "tourney_profiles" WHERE discord_id=?', (of.id, )).fetchone() is None:
        return False

    cursor.execute('UPDATE "tourney_profiles" SET team_cc=? WHERE discord_id=?', (cc, of.id))
    connection.commit()
    return True


async def edit_tourney_team(of: discord.Member, team: List[int]):
    cursor = connection.cursor()

    if cursor.execute('SELECT * FROM "tourney_profiles" WHERE discord_id=?', (of.id,)).fetchone() is None:
        return False

    cursor.execute('UPDATE "tourney_profiles" SET team_unit_ids=? WHERE discord_id=?', (",".join([str(x) for x in team]), of.id))
    connection.commit()
    return True


async def get_tourney_profile(of: discord.Member):
    cursor = connection.cursor()
    data = cursor.execute('SELECT gc_code, team_cc, won, lost, team_unit_ids FROM "tourney_profiles" WHERE discord_id=?', (of.id, )).fetchone()
    if data is None:
        return None
    return {
        "gc_code": data[0],
        "team_cc": data[1],
        "won": data[2],
        "lost": data[3],
        "team": [int(x) for x in data[4].split(",")]
    }


async def get_tourney_top_profiles():
    cursor = connection.cursor()
    for i, row in enumerate(cursor.execute('SELECT won, discord_id'
                                           ' FROM "tourney_profiles"'
                                           ' ORDER BY won DESC'
                                           ' LIMIT 10').fetchall()):
        yield {
            "place": i + 1,
            "won": row[0],
            "member_id": row[1]
        }


async def add_tourney_challenge(author: discord.Member, to_fight: discord.Member):
    cursor = connection.cursor()

    try:
        cursor.execute('INSERT INTO "tourney_challenges" VALUES (?, ?)', (to_fight.id, author.id))
        connection.commit()
        return True
    except sqlite.IntegrityError:
        return False


async def get_tourney_challengers(of: discord.Member):
    cursor = connection.cursor()

    for row in cursor.execute('SELECT challenger_discord_id FROM "tourney_challenges" WHERE challenged_discord_id=?',
                              (of.id, )):
        yield row[0]


async def accept_challenge(challenged: discord.Member, challenger: discord.Member):
    return await start_tourney_game(challenged, challenger)


async def decline_challenge(challenged: discord.Member, challenger: discord.Member):
    cursor = connection.cursor()

    cursor.execute('DELETE FROM "tourney_challenges" WHERE challenged_discord_id=? AND challenger_discord_id=?',
                   (challenged.id, challenger.id))

    connection.commit()


async def start_tourney_game(challenged: discord.Member, challenger: discord.Member):
    cursor = connection.cursor()

    cursor.execute('DELETE FROM "tourney_challenges" WHERE challenged_discord_id=? AND challenger_discord_id=?',
                   (challenged.id, challenger.id))

    cursor.execute('INSERT INTO "tourney_games" VALUES (?, ?)', (challenged.id, challenger.id))
    connection.commit()


async def report_tourney_game(winner: discord.Member, looser: discord.Member):
    cursor = connection.cursor()

    if not await tourney_in_game_with(winner, looser):
        return False

    cursor.execute('DELETE FROM "tourney_games" WHERE (person1=? AND person2=?) OR (person1=? AND person2=?)',
                   (winner.id, looser.id, looser.id, winner.id))

    cursor.execute('UPDATE "tourney_profiles" SET won = won + 1 WHERE discord_id=?', (winner.id,))
    cursor.execute('UPDATE "tourney_profiles" SET lost = lost + 1 WHERE discord_id=?', (looser.id,))

    return True


async def tourney_in_game(player: discord.Member):
    cursor = connection.cursor()

    return len(
        cursor.execute('SELECT * FROM "tourney_games" WHERE person1=? OR person2=?', (player.id, player.id)).fetchall()) != 0


async def tourney_in_game_with(p1: discord.Member, p2: discord.Member):
    cursor = connection.cursor()

    return len(
        cursor.execute('SELECT * FROM "tourney_games" WHERE (person1=? AND person2=?) OR (person1=? AND person2=?)',
                       (p1.id, p2.id, p2.id, p1.id)).fetchall()) != 0
