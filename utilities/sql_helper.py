import logging
from sqlite3 import Cursor
from typing import Tuple, Optional, List
from utilities import connection, unit_list, r_unit_list, sr_unit_list, logger
from utilities.units import Unit, map_attribute, map_grade, map_race, map_event, map_affection, Grade, Event,\
    all_affections, unit_by_id
from utilities.banners import all_banner_list, Banner, map_bannertype


def read_units_from_db() -> None:
    cursor: Cursor = connection.cursor()
    unit_list.clear()
    r_unit_list.clear()
    sr_unit_list.clear()

    row: Tuple[int, str, str, str, str, str, str, str, str, int]
    for row in cursor.execute('SELECT * FROM units'):
        cursor2: Cursor = connection.cursor()
        alt_names: List[str] = [x[0] for x in cursor2.execute('SELECT name FROM additional_unit_names WHERE unit_id=?', (row[0], )).fetchall()]

        unit_list.append(Unit(
            unit_id=row[0],
            name=row[1],
            simple_name=row[2],
            alt_names=alt_names,
            type_enum=map_attribute(row[3]),
            grade=map_grade(row[4]),
            race=map_race(row[5]),
            event=map_event(row[6]),
            affection_str=map_affection(row[7]),
            icon_path=row[8] if row[0] < 0 else "gc/icons/{}.png",
            is_jp=row[9] == 1,
        ))
        logger.log(logging.INFO, f"Registering Unit: {row[1]} ({row[0]}) is JP? {row[9] == 1}")

    r_unit_list.extend([x for x in unit_list if x.grade == Grade.R and x.event == Event.GC])
    sr_unit_list.extend([x for x in unit_list if x.grade == Grade.SR and x.event == Event.GC])


def read_affections_from_db() -> None:
    connection.commit()
    cursor: Cursor = connection.cursor()
    row: Tuple[str, int]
    for row in cursor.execute('SELECT * FROM affections'):
        all_affections.append(row[0])
        logger.log(logging.INFO, f"Loaded {row[0]} - affection")


def read_banners_from_db() -> None:
    all_banner_list.clear()
    cursor: Cursor = connection.cursor()
    cursor2: Cursor = connection.cursor()
    banner_data: Tuple[str, str, float, float, str, float, int, int, int, int]
    for banner_data in cursor.execute('SELECT * FROM banners ORDER BY "order"').fetchall():
        banner_name_data: Optional[List[Tuple[str]]] = cursor2.execute(
            'SELECT alternative_name FROM banner_names WHERE name=?',
            (banner_data[0],)).fetchall()
        banner_unit_data: Optional[List[Tuple[int]]] = cursor2.execute(
            'SELECT unit_id FROM banners_units WHERE banner_name=?',
            (banner_data[0],)).fetchall()
        banner_rate_up_unit_data: Optional[List[Tuple[int]]] = cursor2.execute(
            'SELECT unit_id FROM banners_rate_up_units WHERE banner_name=?',
            (banner_data[0],)).fetchall()

        banner_names: List[str] = [banner_data[0]]
        _unit_list: List[Unit] = []
        rate_up_unit_list: List[Unit] = []

        for sql_banner_names in banner_name_data:
            banner_names.append(sql_banner_names[0])
        for sql_unit_id in banner_unit_data:
            _unit_list.append(unit_by_id(sql_unit_id[0]))
        for sql_unit_id in banner_rate_up_unit_data:
            rate_up_unit_list.append(unit_by_id(sql_unit_id[0]))

        if len(unit_list) == 0:
            continue

        b: Banner = Banner(
            name=banner_names,
            pretty_name=banner_data[1],
            ssr_unit_rate=banner_data[2],
            sr_unit_rate=banner_data[3],
            bg_url=banner_data[4],
            r_unit_rate=banner_data[5],
            ssr_unit_rate_up=banner_data[6],
            includes_all_sr=banner_data[7] == 1,
            includes_all_r=banner_data[8] == 1,
            banner_type=map_bannertype(banner_data[9]),
            units=_unit_list,
            rate_up_units=rate_up_unit_list
        )
        all_banner_list.append(b)
        logger.log(logging.INFO, f"Read Banner {banner_names}")


async def add_unit_to_banner(banner: str, units: str) -> None:
    cursor: Cursor = connection.cursor()
    for u_id in [int(x) for x in units.replace(" ", "").split(",")]:
        cursor.execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner, u_id))
    connection.commit()


async def add_rate_up_unit_to_banner(banner: str, units: str) -> None:
    cursor: Cursor = connection.cursor()
    for u_id in [int(x) for x in units.replace(" ", "").split(",")]:
        cursor.execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner, u_id))
    connection.commit()
