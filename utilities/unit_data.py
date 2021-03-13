from enum import Enum
from utilities import *


class Grade(Enum):
    R = "r"
    SR = "sr"
    SSR = "ssr"


class Type(Enum):
    RED = "red"
    GRE = "green"
    BLUE = "blue"


class Race(Enum):
    DEMON = "demon"
    GIANT = "giant"
    HUMAN = "human"
    FAIRY = "fairy"
    GODDESS = "goddess"
    UNKNOWN = "unknown"


class Event(Enum):
    GC = "gc"
    SLI = "slime"
    AOT = "aot"
    KOF = "kof"
    NEY = "newyear"
    HAL = "halloween"
    FES = "festival"
    VAL = "valentine"
    CUS = "custom"


class Affection(Enum):
    SIN = "sins"
    COMMANDMENTS = "commandments"
    KNIGHT = "holyknights"
    CATASTROPHE = "catastrophes"
    ANGEL = "archangels"
    NONE = "none"


RACES = [Race.DEMON, Race.GIANT, Race.HUMAN, Race.FAIRY, Race.GODDESS, Race.UNKNOWN]
GRADES = [Grade.R, Grade.SR, Grade.SSR]
TYPES = [Type.RED, Type.GRE, Type.BLUE]
EVENTS = [Event.GC, Event.SLI, Event.AOT, Event.KOF, Event.FES, Event.NEY, Event.VAL, Event.HAL]
AFFECTIONS = [Affection.SIN.value, Affection.COMMANDMENTS.value, Affection.CATASTROPHE.value,
              Affection.ANGEL.value, Affection.KNIGHT.value, Affection.NONE.value]

FRAMES = {
    Type.BLUE: {
        Grade.R: Image.open("gc/frames/blue_r_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SR: Image.open("gc/frames/blue_sr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SSR: Image.open("gc/frames/blue_ssr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    },
    Type.RED: {
        Grade.R: Image.open("gc/frames/red_r_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SR: Image.open("gc/frames/red_sr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SSR: Image.open("gc/frames/red_ssr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    },
    Type.GRE: {
        Grade.R: Image.open("gc/frames/green_r_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SR: Image.open("gc/frames/green_sr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
        Grade.SSR: Image.open("gc/frames/green_ssr_frame.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    }
}
FRAME_BACKGROUNDS = {
    Grade.R: Image.open("gc/frames/r_frame_background.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
    Grade.SR: Image.open("gc/frames/sr_frame_background.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA"),
    Grade.SSR: Image.open("gc/frames/ssr_frame_background.png").resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
}


def map_attribute(raw_att: str) -> Type:
    raw_att = raw_att.lower()
    if raw_att in ["blue", "speed", "b"]:
        return Type.BLUE
    if raw_att in ["red", "strength", "r"]:
        return Type.RED
    if raw_att in ["green", "hp", "g"]:
        return Type.GRE
    return None


def map_grade(raw_grade: str) -> Grade:
    raw_grade = raw_grade.lower()
    if raw_grade == "r":
        return Grade.R
    if raw_grade == "sr":
        return Grade.SR
    if raw_grade == "ssr":
        return Grade.SSR
    return None


def map_race(raw_race: str) -> Race:
    raw_race = raw_race.lower()
    if raw_race in ["demon", "demons"]:
        return Race.DEMON
    if raw_race in ["giant", "giants"]:
        return Race.GIANT
    if raw_race in ["fairy", "fairies"]:
        return Race.FAIRY
    if raw_race in ["human", "humans"]:
        return Race.HUMAN
    if raw_race in ["goddess", "god", "gods"]:
        return Race.GODDESS
    if raw_race in ["unknown"]:
        return Race.UNKNOWN
    return None


def map_event(raw_event: str) -> Event:
    raw_event = raw_event.replace(" ", "").lower()
    if raw_event in ["slime", "tensura"]:
        return Event.SLI
    if raw_event in ["aot", "attackontitan", "titan"]:
        return Event.AOT
    if raw_event in ["kof", "kingoffighter", "kingoffighters"]:
        return Event.KOF
    if raw_event in ["valentine", "val"]:
        return Event.VAL
    if raw_event in ["newyears", "newyear", "ny"]:
        return Event.NEY
    if raw_event in ["halloween", "hal", "hw"]:
        return Event.HAL
    if raw_event in ["festival", "fes", "fest"]:
        return Event.FES
    if raw_event in ["custom"]:
        return Event.CUS
    return Event.GC


def map_affection(raw_affection: str) -> str:
    raw_affection = raw_affection.replace(" ", "").lower()
    if raw_affection in ["sins", "sin"]:
        return Affection.SIN.value
    if raw_affection in ["holyknight", "holyknights", "knights", "knight"]:
        return Affection.KNIGHT.value
    if raw_affection in ["commandments", "commandment", "command"]:
        return Affection.COMMANDMENTS.value
    if raw_affection in ["catastrophes", "catastrophes"]:
        return Affection.CATASTROPHE.value
    if raw_affection in ["arcangels", "angels", "angel", "arcangel"]:
        return Affection.ANGEL.value
    if raw_affection in ["none", "no"]:
        return Affection.NONE.value
    if raw_affection in AFFECTIONS:
        return raw_affection
    return Affection.NONE.value


async def image_to_discord(img: Image, image_name: str) -> discord.File:
    with BytesIO() as image_bin:
        img.save(image_bin, 'PNG')
        image_bin.seek(0)
        image_file = discord.File(fp=image_bin, filename=image_name)
    return image_file


async def compose_icon(attribute: Type, grade: Grade, background: Image = None) -> Image:
    background_frame = FRAME_BACKGROUNDS[grade].copy()
    if background is None:
        background = background_frame
    else:
        background = background.resize((IMG_SIZE, IMG_SIZE)).convert("RGBA")
    frame = FRAMES[attribute][grade]
    background_frame.paste(background, (0, 0), background)
    background_frame.paste(frame, (0, 0), frame)

    return background_frame


class Unit:
    def __init__(self, unit_id: int,
                 name: str,
                 simple_name: str,
                 type_enum: Type,
                 grade: Grade,
                 race: Race,
                 event: Event = Event.GC,
                 affection_str: str = Affection.NONE.value,
                 icon_path: str = "gc/icons/{}.png",
                 alt_names: List[str] = None,
                 is_jp: bool = False):

        if alt_names is None:
            alt_names = []

        self.unit_id: int = unit_id
        self.name: str = name
        self.simple_name: str = simple_name
        self.alt_names: List[str] = alt_names.copy()
        self.type: Type = type_enum
        self.grade: Grade = grade
        self.race: Race = race
        self.event: Event = event
        self.affection: str = affection_str
        self.icon_path: str = icon_path
        self.is_jp: bool = is_jp

        if unit_id > 0:
            img = Image.new('RGBA', (IMG_SIZE, IMG_SIZE))
            img.paste(Image.open(icon_path.format(unit_id)).resize((IMG_SIZE, IMG_SIZE)), (0, 0))
            self.icon: Image = img
        else:
            self.icon: Image = None

    async def discord_icon(self) -> discord.File:
        return await image_to_discord(self.icon, "unit.png")

    async def set_icon(self):
        if self.icon is None:
            await self.refresh_icon()

    async def refresh_icon(self):
        if self.unit_id <= 0:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.icon_path) as resp:
                    self.icon: Image = await compose_icon(attribute=self.type, grade=self.grade,
                                                          background=Image.open(BytesIO(await resp.read())))

    def discord_color(self) -> discord.Color:
        if self.type == Type.RED:
            return discord.Color.red()
        if self.type == Type.GRE:
            return discord.Color.green()
        if self.type == Type.BLUE:
            return discord.Color.blue()
        return discord.Color.gold()

    def __str__(self):
        return f"Unit: {self.name} ({self.unit_id})"


def units_by_id(ids: List[int]) -> List[Unit]:
    found = [x for x in UNITS if x.unit_id in ids]
    if len(found) == 0:
        raise LookupError
    return found


def unit_by_id(unit_id: int) -> Unit:
    return next((x for x in UNITS if unit_id == x.unit_id), None)


def unit_by_name(name: str) -> Unit:
    return next((x for x in UNITS if name == x.name), None)


def unit_by_vague_name(name: str) -> List[Unit]:
    return [x for x in UNITS if (name.lower() in x.name.lower()) or name.lower() in [y.lower() for y in x.alt_names]]
