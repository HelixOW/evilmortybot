import discord
import random as ra

from enum import Enum
from typing import List, Optional, Dict, Tuple, Any
from sqlite3 import Cursor
from utilities import sr_unit_list, r_unit_list, all_banner_list, unit_list, connection
from utilities.units import Unit, Grade, Event


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
                 banner_type: BannerType = BannerType.ELEVEN) -> None:

        if rate_up_units is None:
            rate_up_units = []

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
        self.all_units: List[Unit] = self.units + self.rate_up_units

        self.ssr_chance: float = (self.ssr_unit_rate_up * len(self.rate_up_units)) + (
                self.ssr_unit_rate * (len(self.ssr_units)))
        self.ssr_rate_up_chance: float = (self.ssr_unit_rate_up * len(self.rate_up_units)) if len(
            self.rate_up_units) != 0 else 0
        self.sr_chance: float = (self.sr_unit_rate * len(self.sr_units))

        self.background: str = bg_url

        self.shaftable: bool = len([x for x in name if "gssr" in x]) == 0

    def __repr__(self) -> str:
        return "Banner: " + ", ".join([f"{x}: {self.__getattribute__(x)} " for x in dir(self)])

    def __str__(self) -> str:
        return f"Banner: {self.name}"

    def contains_any_unit(self, possible_units: List[Unit]):
        return len([a for a in possible_units if a.unit_id in [b.unit_id for b in self.all_units]]) != 0


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


def create_custom_unit_banner() -> None:
    cus_units: List[Unit] = [x for x in unit_list if x.event == Event.CUS]
    ssrs: List[Unit] = [x for x in cus_units if x.grade == Grade.SSR]
    srs: List[Unit] = [x for x in cus_units if x.grade == Grade.SR]
    rs: List[Unit] = [x for x in cus_units if x.grade == Grade.R]
    if banner_by_name("custom") is not None:
        all_banner_list.remove(banner_by_name("custom"))
    all_banner_list.append(
        Banner(name=["customs", "custom"],
               pretty_name="Custom Created Units",
               units=cus_units,
               ssr_unit_rate=(3 / len(ssrs)) if len(ssrs) > 0 else -1,
               sr_unit_rate=((100 - 3 - (6.6667 * len(rs))) / len(srs)) if len(srs) > 0 else -1,
               includes_all_r=False,
               includes_all_sr=False,
               bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/A9619A31-B793-4E12-8DF6-D0FCC706DEF2_1_105_c.jpeg")
    )


def create_jp_banner() -> None:
    jp_units: List[Unit] = [x for x in unit_list if x.is_jp]
    ssrs: List[Unit] = [x for x in jp_units if x.grade == Grade.SSR]
    if banner_by_name("jp") is not None:
        all_banner_list.remove(banner_by_name("jp"))
    all_banner_list.append(
        Banner(name=["kr", "jp"],
               pretty_name="JP/KR exclusive draw",
               units=jp_units,
               ssr_unit_rate=(4 / len(ssrs)) if len(ssrs) > 0 else -1,
               sr_unit_rate=((100 - 4 - (6.6667 * len(r_unit_list))) / len(sr_unit_list)) if len(sr_unit_list) > 0 else -1,
               includes_all_r=True,
               includes_all_sr=True,
               bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/A9619A31-B793-4E12-8DF6-D0FCC706DEF2_1_105_c.jpeg")
    )


async def add_unit_to_box(user: discord.Member, unit_to_add: Unit) -> None:
    cursor: Cursor = connection.cursor()
    data: Optional[Tuple[int]] = cursor.execute(
        'SELECT amount FROM box_units WHERE user_id=? AND guild=? AND unit_id=?',
        (user.id, user.guild.id, unit_to_add.unit_id)).fetchone()
    if data is None:
        cursor.execute('INSERT INTO box_units VALUES (?, ?, ?, ?)', (user.id, user.guild.id, unit_to_add.unit_id, 1))
    else:
        if data[0] < 1000:
            cursor.execute('UPDATE box_units SET amount=? WHERE user_id=? AND guild=? AND unit_id=?',
                           (data[0] + 1, user.id, user.guild.id, unit_to_add.unit_id))


async def get_user_pull(user: discord.Member) -> Dict[str, int]:
    cursor: Cursor = connection.cursor()
    data: Optional[Tuple[int, int, int, int, int]] = cursor.execute(
        'SELECT * FROM user_pulls WHERE user_id=? AND guild=?',
        (user.id, user.guild.id)).fetchone()
    if data is None:
        return {}
    return {"ssr_amount": data[1], "pull_amount": data[2], "guild": data[3], "shafts": data[4]}


async def add_user_pull(user: discord.Member, got_ssr: bool) -> None:
    data: Dict[str, Any] = await get_user_pull(user)
    cursor: Cursor = connection.cursor()
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
    cursor: Cursor = connection.cursor()
    if len(data) != 0:
        cursor.execute('UPDATE user_pulls SET shafts=? WHERE user_id=? AND guild=?',
                       (data["shafts"] + amount, user.id, user.guild.id))
    else:
        cursor.execute('INSERT INTO user_pulls VALUES (?, ?, ?, ?, ?)',
                       (user.id, 0, 0, user.guild.id, amount))
    connection.commit()
