from utilities import *
from utilities.unit_data import Unit, R_UNITS, SR_UNITS, Grade, Event


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
            units += SR_UNITS
        if r_unit_rate != 0 and includes_all_r:
            units += R_UNITS

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

        self.shaftable: bool = len([x for x in name if "gssr" in name]) == 0

    def __repr__(self) -> str:
        return "Banner: " + ", ".join([f"{x}: {self.__getattribute__(x)} " for x in dir(self)])

    def __str__(self) -> str:
        return f"Banner: {self.name}"


def banner_by_name(name: str) -> Optional[Banner]:
    return next((x for x in ALL_BANNERS if name in x.name), None)


def banners_by_name(names: List[str]) -> List[Banner]:
    found = [x for x in ALL_BANNERS if not set(x.name).isdisjoint(names)]
    if len(found) == 0:
        raise ValueError
    return found


def create_custom_unit_banner() -> None:
    cus_units: List[Unit] = [x for x in UNITS if x.event == Event.CUS]
    ssrs: List[Unit] = [x for x in cus_units if x.grade == Grade.SSR]
    srs: List[Unit] = [x for x in cus_units if x.grade == Grade.SR]
    rs: List[Unit] = [x for x in cus_units if x.grade == Grade.R]
    if banner_by_name("custom") is not None:
        ALL_BANNERS.remove(banner_by_name("custom"))
    ALL_BANNERS.append(
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
    jp_units: List[Unit] = [x for x in UNITS if x.is_jp]
    ssrs: List[Unit] = [x for x in jp_units if x.grade == Grade.SSR]
    if banner_by_name("jp") is not None:
        ALL_BANNERS.remove(banner_by_name("jp"))
    ALL_BANNERS.append(
        Banner(name=["kr", "jp"],
               pretty_name="JP/KR exclusive draw",
               units=jp_units,
               ssr_unit_rate=(4 / len(ssrs)) if len(ssrs) > 0 else -1,
               sr_unit_rate=((100 - 4 - (6.6667 * len(R_UNITS))) / len(SR_UNITS)) if len(SR_UNITS) > 0 else -1,
               includes_all_r=True,
               includes_all_sr=True,
               bg_url="https://raw.githubusercontent.com/WhoIsAlphaHelix/evilmortybot/master/gc/banners/A9619A31-B793-4E12-8DF6-D0FCC706DEF2_1_105_c.jpeg")
    )
