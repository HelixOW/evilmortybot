import PIL.Image as ImageLib
import discord
import random as ra
import logging

from enum import Enum
from PIL import ImageDraw
from typing import List, Optional, Dict, Any, Tuple
from utilities import sr_unit_list, r_unit_list, all_banner_list, unit_list, logger, flatten, chunks, \
    get_text_dimensions, img_size, x_offset, y_offset, text_with_shadow
from utilities.units import Unit, Grade, Event, unit_by_id, longest_named
from utilities.sql_helper import execute, fetch_row, fetch_item, rows, fetch_items


class BannerType(Enum):
    ELEVEN = 11
    FIVE = 5


def map_bannertype(raw_bannertype: int) -> BannerType:
    if raw_bannertype == 5:
        return BannerType.FIVE
    return BannerType.ELEVEN


class Banner:
    def __init__(self, name: List[str],
                 pretty_name: str,
                 units: List[Unit],
                 ssr_unit_rate: float,
                 sr_unit_rate: float,
                 bg_url: str,
                 r_unit_rate: float = 6.6667,
                 rate_up_units: List[Unit] = None,
                 ssr_unit_rate_up: float = 0.5,
                 includes_all_sr: bool = True,
                 includes_all_r: bool = True,
                 banner_type: BannerType = BannerType.ELEVEN,
                 loyality: int = 900) -> None:

        if rate_up_units is None:
            rate_up_units = []

        self.unique_name = name[0]
        self.name: List[str] = name
        self.pretty_name: str = pretty_name

        self.includes_all_sr: bool = includes_all_sr
        self.includes_all_r: bool = includes_all_r

        if sr_unit_rate != 0 and includes_all_sr:
            units += sr_unit_list
        if r_unit_rate != 0 and includes_all_r:
            units += r_unit_list

        self.units: List[Unit] = units
        self.rate_up_units: List[Unit] = rate_up_units

        self.ssr_unit_rate: float = ssr_unit_rate
        self.ssr_unit_rate_up: float = ssr_unit_rate_up
        self.sr_unit_rate: float = sr_unit_rate
        self.r_unit_rate: float = r_unit_rate

        self.banner_type: BannerType = banner_type

        self.r_units: List[Unit] = [x for x in self.units if x.grade == Grade.R]
        self.sr_units: List[Unit] = [x for x in self.units if x.grade == Grade.SR]
        self.ssr_units: List[Unit] = [x for x in self.units if x.grade == Grade.SSR and x not in self.rate_up_units]
        self.all_ssr_units: List[Unit] = [x for x in self.units if x.grade == Grade.SSR]
        self.all_units: List[Unit] = self.units + self.rate_up_units

        self.ssr_chance: float = (self.ssr_unit_rate_up * len(self.rate_up_units)) + (
                self.ssr_unit_rate * (len(self.ssr_units)))
        self.ssr_rate_up_chance: float = (self.ssr_unit_rate_up * len(self.rate_up_units)) if len(
            self.rate_up_units) != 0 else 0
        self.sr_chance: float = (self.sr_unit_rate * len(self.sr_units))

        self.background: str = bg_url

        self.shaftable: bool = len([x for x in name if "gssr" in x]) == 0

        self.loyality: int = loyality

        self.unit_list_image: Tuple[ImageLib.Image, ...] = self._compose_banner_unit_list()

    def __repr__(self) -> str:
        return "Banner: " + ", ".join([f"{x}: {self.__getattribute__(x)} " for x in dir(self)])

    def __str__(self) -> str:
        return f"Banner: {self.name}"

    def contains_any_unit(self, possible_units: List[Unit]):
        return len([a for a in possible_units if a.unit_id in [b.unit_id for b in self.all_units]]) != 0

    def get_unit_rate(self, unit: Unit) -> float:
        if unit in self.rate_up_units:
            return self.ssr_unit_rate_up
        elif unit in self.ssr_units:
            return self.ssr_unit_rate
        elif unit in self.sr_units:
            return self.sr_unit_rate
        elif unit in self.r_units:
            return self.r_unit_rate
        return -1

    async def load_custom_units(self):
        for unit in self.all_units:
            await unit.set_icon()

        self.unit_list_image: Tuple[ImageLib.Image, ...] = self._compose_banner_unit_list()

    def _compose_banner_unit_list(self) -> Tuple[ImageLib.Image, ...]:
        if len(self.ssr_units + self.rate_up_units) == 0:
            return ImageLib.new('RGBA', (0, 0))

        chunked_units: List[List[Unit]] = list(
            chunks(self.all_units, 5))

        banner_unit_list = []

        for units in chunked_units:
            unit_text: Tuple[int, int] = get_text_dimensions(longest_named(units).name + " - 99.9999%")
            i: ImageLib.Image = ImageLib.new('RGBA', (
                img_size + unit_text[0] + x_offset,
                (img_size * len(units)) + (y_offset * (len(units) - 1))
            ))
            draw: ImageDraw = ImageDraw.Draw(i)

            y: int = 0
            for _unit in units:
                if _unit.icon:
                    i.paste(_unit.icon, (0, y))
                text_with_shadow(draw,
                                 xy=(
                                     x_offset + img_size,
                                     y + int(img_size / 2) - int(unit_text[1] / 2)),
                                 text=f"{_unit.name} - {self.get_unit_rate(_unit)}%")
                y += img_size + 5

            banner_unit_list.append(i)

        return tuple(banner_unit_list)


def find_banner_containing_unit(u: Unit) -> Banner:
    return next((banner for banner in all_banner_list if u in banner.all_units), None)


def find_banner_containing_any_unit(us: List[Unit]):
    for u in us:
        banner_containing = find_banner_containing_unit(u)
        if banner_containing is not None:
            return banner_containing
    raise ValueError


def banner_by_name(name: str) -> Optional[Banner]:
    return next((x for x in all_banner_list if name in x.name), None)


def banners_by_name(names: List[str]) -> List[Banner]:
    found = [x for x in all_banner_list if not set(x.name).isdisjoint(names)]
    if len(found) == 0:
        raise ValueError
    return found


async def create_custom_unit_banner() -> None:
    cus_units: List[Unit] = [x for x in unit_list if x.event == Event.CUS]
    ssrs: List[Unit] = [x for x in cus_units if x.grade == Grade.SSR]
    srs: List[Unit] = [x for x in cus_units if x.grade == Grade.SR]
    rs: List[Unit] = [x for x in cus_units if x.grade == Grade.R]
    if banner_by_name("custom") is not None:
        all_banner_list.remove(banner_by_name("custom"))

    b: Banner = Banner(name=["customs", "custom"],
                       pretty_name="Custom Created Units",
                       units=cus_units,
                       ssr_unit_rate=(3 / len(ssrs)) if len(ssrs) > 0 else -1,
                       sr_unit_rate=((100 - 3 - (6.6667 * len(rs))) / len(srs)) if len(srs) > 0 else -1,
                       includes_all_r=False,
                       includes_all_sr=False,
                       bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/custom.png")

    await b.load_custom_units()

    all_banner_list.append(b)


def create_jp_banner() -> None:
    jp_units: List[Unit] = [x for x in unit_list if x.is_jp]
    ssrs: List[Unit] = [x for x in jp_units if x.grade == Grade.SSR]
    if banner_by_name("jp") is not None:
        all_banner_list.remove(banner_by_name("jp"))
    all_banner_list.append(
        Banner(name=["kr", "jp"],
               loyality=150,
               pretty_name="JP/KR exclusive draw",
               units=jp_units,
               ssr_unit_rate=(4 / len(ssrs)) if len(ssrs) > 0 else -1,
               sr_unit_rate=((100 - 4 - (6.6667 * len(r_unit_list))) / len(sr_unit_list)) if len(
                   sr_unit_list) > 0 else -1,
               includes_all_r=True,
               includes_all_sr=True,
               bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/A9619A31-B793-4E12-8DF6-D0FCC706DEF2_1_105_c.jpeg")
    )


async def add_unit_to_box(user: discord.Member, unit_to_add: Unit) -> None:
    data: Optional[int] = await fetch_item(
        'SELECT amount FROM box_units WHERE user_id=? AND guild=? AND unit_id=?',
        (user.id, user.guild.id, unit_to_add.unit_id))

    if data is None:
        await execute('INSERT INTO box_units VALUES (?, ?, ?, ?)', (user.id, user.guild.id, unit_to_add.unit_id, 1))
    else:
        if data < 1000:
            await execute('UPDATE box_units SET amount=? WHERE user_id=? AND guild=? AND unit_id=?',
                          (data + 1, user.id, user.guild.id, unit_to_add.unit_id))


async def get_user_pull(user: discord.Member) -> Dict[str, int]:
    return await fetch_row(
        'SELECT * FROM user_pulls WHERE user_id=? AND guild=?',
        lambda x: {"ssr_amount": x[1], "pull_amount": x[2], "guild": x[3], "shafts": x[4]},
        (user.id, user.guild.id),
        {})


async def add_user_pull(user: discord.Member, got_ssr: bool) -> None:
    data: Dict[str, Any] = await get_user_pull(user)
    if len(data) == 0:
        await execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                      (user.id, 1 if got_ssr else 0, 1, user.guild.id, 0))
    else:
        if got_ssr:
            await execute('UPDATE user_pulls SET ssr_amount=?, pull_amount=? WHERE user_id=? AND guild=?',
                          (data["ssr_amount"] + 1, data["pull_amount"] + 1, user.id, user.guild.id))
        else:
            await execute('UPDATE user_pulls SET pull_amount=? WHERE user_id=? AND guild=?',
                          (data["pull_amount"] + 1, user.id, user.guild.id))


async def unit_with_chance(from_banner: Banner, user: discord.Member) -> Unit:
    draw_chance: float = round(ra.uniform(0, 100), 4)

    if from_banner.ssr_rate_up_chance >= draw_chance and len(from_banner.rate_up_units) != 0:
        u: Unit = from_banner.rate_up_units[ra.randint(0, len(from_banner.rate_up_units) - 1)]
    elif from_banner.ssr_chance >= draw_chance or len(from_banner.sr_units) == 0:
        u: Unit = from_banner.ssr_units[ra.randint(0, len(from_banner.ssr_units) - 1)]
    elif from_banner.sr_chance >= draw_chance or len(from_banner.r_units) == 0:
        u: Unit = from_banner.sr_units[ra.randint(0, len(from_banner.sr_units) - 1)]
    else:
        u: Unit = from_banner.r_units[ra.randint(0, len(from_banner.r_units) - 1)]

    if user is not None:
        await add_user_pull(user, u.grade == Grade.SSR)
        await add_unit_to_box(user, u)
    await u.set_icon()
    return u


async def add_shaft(user: discord.Member, amount: int) -> None:
    data: Dict[str, Any] = await get_user_pull(user)
    if len(data) != 0:
        await execute('UPDATE user_pulls SET shafts=? WHERE user_id=? AND guild=?',
                      (data["shafts"] + amount, user.id, user.guild.id))
    else:
        await execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                      (user.id, 0, 0, user.guild.id, amount))


async def add_unit_to_banner(banner: str, units: str) -> None:
    for u_id in [int(x) for x in units.replace(" ", "").split(",")]:
        await execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner, u_id))


async def add_rate_up_unit_to_banner(banner: str, units: str) -> None:
    for u_id in [int(x) for x in units.replace(" ", "").split(",")]:
        await execute('INSERT INTO banners_rate_up_units VALUES (?, ?)', (banner, u_id))


async def read_banners_from_db() -> None:
    all_banner_list.clear()
    async for banner_data in rows('SELECT * FROM banners ORDER BY "order"'):
        banner_names: List[str] = await fetch_items(
            'SELECT alternative_name FROM banner_names WHERE name=?', (banner_data[0],)
        )
        _unit_list: List[Unit] = [unit_by_id(x) for x in await fetch_items(
            'SELECT unit_id FROM banners_units WHERE banner_name=?', (banner_data[0],)
        )]
        rate_up_unit_list: List[Unit] = [unit_by_id(x) for x in await fetch_items(
            'SELECT unit_id FROM banners_rate_up_units WHERE banner_name=?', (banner_data[0],)
        )]

        banner_names.append(banner_data[0])

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
            rate_up_units=rate_up_unit_list,
            loyality=banner_data[11]
        )
        all_banner_list.append(b)
        logger.log(logging.INFO, f"Read Banner {banner_names}")


def banner_starting_names() -> List[str]:
    return list(set([y.split(" ")[0] for y in flatten([x.name for x in all_banner_list])]))
