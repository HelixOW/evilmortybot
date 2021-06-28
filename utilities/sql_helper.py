import logging
import aiosqlite
from typing import List, Tuple, Any, AsyncGenerator, Callable, TypeVar
from utilities import database, unit_list, r_unit_list, sr_unit_list, logger
from utilities.units import Unit, map_attribute, map_grade, map_race, map_event, map_affection, Grade, Event, \
    all_affections


T = TypeVar('T')


async def execute(sql: str, args: Tuple[Any, ...] = ()) -> None:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            await cursor.execute(sql, args)
        await db.commit()


async def rows(sql: str, args: Tuple[Any, ...] = ()) -> AsyncGenerator[Tuple[Any], None]:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            for row in await (await cursor.execute(sql, args)).fetchall():
                yield row


async def fetch_row(sql: str, converter: Callable[[Tuple], T], args: Tuple[Any, ...] = (), default: T = None) -> T:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            val = await (await cursor.execute(sql, args)).fetchone()
            if val is None:
                return default
            return converter(val)


async def fetch_rows(sql: str, converter: Callable[[Tuple], T], args: Tuple[Any, ...] = ()) -> List[T]:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            cursor = await cursor.execute(sql, args)
            return [converter(x) for x in await cursor.fetchall()]


async def fetch_item(sql: str, args: Tuple[Any, ...] = ()) -> Any:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            cursor = await cursor.execute(sql, args)
            data = await cursor.fetchone()
            if data is None:
                return None
            return data[0]


async def fetch_items(sql: str, args: Tuple[Any, ...] = ()) -> List[Any]:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            cursor = await cursor.execute(sql, args)
            return [x[0] for x in await cursor.fetchall()]


async def exists(sql: str, args: Tuple[Any, ...] = ()) -> bool:
    async with aiosqlite.connect(database) as db:
        async with db.cursor() as cursor:
            return await (await cursor.execute(sql, args)).fetchone() is not None


async def read_units_from_db() -> None:
    unit_list.clear()
    r_unit_list.clear()
    sr_unit_list.clear()

    async for row in rows('SELECT * FROM units'):
        alt_names: List[str] = await fetch_items(
            'SELECT name FROM additional_unit_names WHERE unit_id=?', (row[0], )
        )

        u: Unit = Unit(
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
            emoji_id=row[10]
        )

        unit_list.append(u)


        logger.log(logging.INFO, f"Registering Unit: {row[1]} ({row[0]}) is JP? {row[9] == 1}")

    r_unit_list.extend([x for x in unit_list if x.grade == Grade.r and x.event == Event.base_game])
    sr_unit_list.extend([x for x in unit_list if x.grade == Grade.sr and x.event == Event.base_game])


async def read_affections_from_db() -> None:
    async for row in rows('SELECT * FROM affections'):
        all_affections.append(row[0])
        logger.log(logging.INFO, f"Loaded {row[0]} - affection")
