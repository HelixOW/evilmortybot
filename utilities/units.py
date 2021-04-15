import discord
import PIL.Image as ImageLib
import aiohttp
import random as ra

from PIL.Image import Image as Img
from typing import List, Dict, Optional, Any
from enum import Enum
from utilities import img_size, unit_list, remove_trailing_whitespace, remove_beginning_ignore_case, image_to_discord
from io import BytesIO


class Grade(Enum):
    R: str = "r"
    SR: str = "sr"
    SSR: str = "ssr"

    def to_int(self) -> int:
        if self.value == "ssr":
            return 0
        if self.value == "sr":
            return 1
        return 2


class Type(Enum):
    RED: str = "red"
    GRE: str = "green"
    BLUE: str = "blue"


class Race(Enum):
    DEMON: str = "demon"
    GIANT: str = "giant"
    HUMAN: str = "human"
    FAIRY: str = "fairy"
    GODDESS: str = "goddess"
    UNKNOWN: str = "unknown"


class Event(Enum):
    GC: str = "gc"
    SLI: str = "slime"
    AOT: str = "aot"
    KOF: str = "kof"
    NEY: str = "newyear"
    HAL: str = "halloween"
    FES: str = "festival"
    VAL: str = "valentine"
    REZ: str = "rezero"
    CUS: str = "custom"


class Affection(Enum):
    SIN: str = "sins"
    COMMANDMENTS: str = "commandments"
    KNIGHT: str = "holyknights"
    CATASTROPHE: str = "catastrophes"
    ANGEL: str = "archangels"
    NONE: str = "none"


all_races: List[Race] = [Race.DEMON, Race.GIANT, Race.HUMAN, Race.FAIRY, Race.GODDESS, Race.UNKNOWN]
all_grades: List[Grade] = [Grade.R, Grade.SR, Grade.SSR]
all_types: List[Type] = [Type.RED, Type.GRE, Type.BLUE]
all_events: List[Event] = [Event.GC, Event.SLI, Event.AOT, Event.KOF, Event.FES, Event.NEY, Event.VAL, Event.HAL, Event.REZ]
all_affections: List[str] = [Affection.SIN.value, Affection.COMMANDMENTS.value, Affection.CATASTROPHE.value,
                             Affection.ANGEL.value, Affection.KNIGHT.value, Affection.NONE.value]

frames: Dict[Type, Dict[Grade, Img]] = {
    Type.BLUE: {
        Grade.R: ImageLib.open("gc/frames/blue_r_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.SR: ImageLib.open("gc/frames/blue_sr_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.SSR: ImageLib.open("gc/frames/blue_ssr_frame.png").resize((img_size, img_size)).convert("RGBA")
    },
    Type.RED: {
        Grade.R: ImageLib.open("gc/frames/red_r_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.SR: ImageLib.open("gc/frames/red_sr_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.SSR: ImageLib.open("gc/frames/red_ssr_frame.png").resize((img_size, img_size)).convert("RGBA")
    },
    Type.GRE: {
        Grade.R: ImageLib.open("gc/frames/green_r_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.SR: ImageLib.open("gc/frames/green_sr_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.SSR: ImageLib.open("gc/frames/green_ssr_frame.png").resize((img_size, img_size)).convert("RGBA")
    }
}
frame_backgrounds: Dict[Grade, Img] = {
    Grade.R: ImageLib.open("gc/frames/r_frame_background.png").resize((img_size, img_size)).convert("RGBA"),
    Grade.SR: ImageLib.open("gc/frames/sr_frame_background.png").resize((img_size, img_size)).convert("RGBA"),
    Grade.SSR: ImageLib.open("gc/frames/ssr_frame_background.png").resize((img_size, img_size)).convert("RGBA")
}


def map_attribute(raw_att: str) -> Optional[Type]:
    raw_att: str = raw_att.lower()
    if raw_att in ["blue", "speed", "b"]:
        return Type.BLUE
    if raw_att in ["red", "strength", "r"]:
        return Type.RED
    if raw_att in ["green", "hp", "g"]:
        return Type.GRE
    return None


def map_grade(raw_grade: str) -> Optional[Grade]:
    raw_grade: str = raw_grade.lower()
    if raw_grade == "r":
        return Grade.R
    if raw_grade == "sr":
        return Grade.SR
    if raw_grade == "ssr":
        return Grade.SSR
    return None


def map_race(raw_race: str) -> Optional[Race]:
    raw_race: str = raw_race.lower()
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
    raw_event: str = raw_event.replace(" ", "").lower()
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
    if raw_event in ["rezero", "re", "zero"]:
        return Event.REZ
    if raw_event in ["custom"]:
        return Event.CUS
    return Event.GC


def map_affection(raw_affection: str) -> str:
    raw_affection: str = raw_affection.replace(" ", "").lower()
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
    if raw_affection in all_affections:
        return raw_affection
    return Affection.NONE.value


async def compose_icon(attribute: Type, grade: Grade, background: Optional[Img] = None) -> \
        Img:
    background_frame: Img = frame_backgrounds[grade].copy()
    if background is None:
        background: Img = background_frame
    else:
        background: Img = background.resize((img_size, img_size)).convert("RGBA")
    frame: Img = frames[attribute][grade]
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
                 alt_names: Optional[List[str]] = None,
                 is_jp: bool = False) -> None:

        if alt_names is None:
            alt_names: List[str] = []

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
            img: Img = ImageLib.new('RGBA', (img_size, img_size))
            img.paste(ImageLib.open(icon_path.format(unit_id)).resize((img_size, img_size)), (0, 0))
            self.icon: Img = img
        else:
            self.icon: Optional[Img] = None

    async def info_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{self.name}",
            colour=self.discord_color()
        ).add_field(
            name="Type",
            value=f"```{self.type.value}```"
        ).add_field(
            name="Grade",
            value=f"```{self.grade.value}```"
        ).add_field(
            name="Race",
            value=f"```{self.race.value}```"
        ).add_field(
            name="Event",
            value=f"```{self.event.value}```"
        ).add_field(
            name="Affection",
            value=f"```{self.affection}```"
        ).add_field(
            name="Is a JP Unit?",
            value="```Yes```" if self.is_jp else "```No```"
        ).add_field(
            name="ID",
            value=f"```{self.unit_id}```"
        )
        if len(self.alt_names) != 0:
            embed._fields = [
                {'inline': True, 'name': "Alternative names", 'value': "```" + ",\n".join(self.alt_names) + "```"}
            ] + embed._fields
        return embed

    async def discord_icon(self) -> discord.File:
        return await image_to_discord(self.icon, "unit.png")

    async def set_icon(self) -> Optional[Img]:
        if self.icon is None:
            await self.refresh_icon()
        return self.icon

    async def refresh_icon(self) -> Optional[Img]:
        if self.unit_id <= 0:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.icon_path) as resp:
                    self.icon: Img = await compose_icon(attribute=self.type, grade=self.grade,
                                                        background=ImageLib.open(BytesIO(await resp.read())))
        return self.icon

    def discord_color(self) -> discord.Color:
        if self.type == Type.RED:
            return discord.Color.red()
        if self.type == Type.GRE:
            return discord.Color.green()
        if self.type == Type.BLUE:
            return discord.Color.blue()
        return discord.Color.gold()

    def __str__(self) -> str:
        return f"Unit: {self.name} ({self.unit_id})"

    @classmethod
    async def convert(cls, _, argument: str):
        return find_unit(argument)[0]


def find_unit(name_or_id: str):
    try:
        return [unit_by_id(int(name_or_id))]
    except ValueError:
        return unit_by_vague_name(name_or_id)


def units_by_id(ids: List[int]) -> List[Unit]:
    found = [x for x in unit_list if x.unit_id in ids]
    if len(found) == 0:
        raise LookupError
    return found


def unit_by_id(unit_id: int) -> Optional[Unit]:
    return next((x for x in unit_list if unit_id == x.unit_id), None)


def unit_by_name(name: str) -> Optional[Unit]:
    return next((x for x in unit_list if name == x.name), None)


def unit_by_vague_name(name: str) -> List[Unit]:
    return [x for x in unit_list if (name.lower() in x.name.lower()) or name.lower() in [y.lower() for y in x.alt_names]]


def longest_named(chunk: List[Unit] = None) -> Unit:
    if chunk is None:
        chunk = unit_list.copy()
    if len(chunk) == 0:
        raise LookupError
    return sorted(chunk, key=lambda k: len(k.name), reverse=True)[0]


def get_units_matching(grades: Optional[List[Grade]] = None,
                       types: Optional[List[Type]] = None,
                       races: Optional[List[Race]] = None,
                       events: Optional[List[Event]] = None,
                       affections: Optional[List[str]] = None,
                       names: Optional[List[str]] = None,
                       jp: bool = False) -> List[Unit]:
    if races is None or races == []:
        races = all_races.copy()
    if grades is None or grades == []:
        grades = all_grades.copy()
    if types is None or types == []:
        types = all_types.copy()
    if events is None or events == []:
        events = all_events.copy()
    if affections is None or affections == []:
        affections = [x.lower().replace(" ", "") for x in all_affections]
    if names is None or names == []:
        names = [x.name.lower().replace(" ", "") for x in unit_list]

    def test(x: Unit):
        return x.race in races \
               and x.type in types \
               and x.grade in grades \
               and x.event in events \
               and x.affection.lower().replace(" ", "") in affections \
               and x.name.lower().replace(" ", "") in names

    possible_units: List[Unit] = [x for x in unit_list if test(x)]

    if jp:
        
        possible_units += [x for x in possible_units if x.is_jp]
    else:
        possible_units = [x for x in unit_list if test(x) and not x.is_jp]

    if len(possible_units) == 0:
        raise LookupError

    return possible_units


def get_random_unit_from_dict(criteria: Dict[str, Any]) -> Unit:
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
    possible_units: List[Unit] = get_units_matching(grades=grades,
                                                    types=types,
                                                    races=races,
                                                    events=events,
                                                    affections=affections,
                                                    names=names,
                                                    jp=jp)
    return possible_units[ra.randint(0, len(possible_units) - 1)]


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
                parsed_names = [x.name for x in unit_list if
                                x.name.lower() != remove_beginning_ignore_case(name_str, "!").lower()]
            else:
                parsed_names = [remove_trailing_whitespace(x) for x in name_str.split(",")]
            continue

        if arg.lower().startswith("race:"):
            race_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "race:").lower())

            if race_str.startswith("!"):
                parsed_races = [x for x in all_races if x.value != remove_beginning_ignore_case(race_str, "!")]
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
                parsed_grades = [x for x in all_grades if x.value != remove_beginning_ignore_case(grade_str, "!")]
            else:
                parsed_grades = [map_grade(remove_trailing_whitespace(x)) for x in grade_str.split(",")]
            continue

        if arg.lower().startswith("type:"):
            type_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "type:").lower())

            if type_str.startswith("!"):
                parsed_types = [x for x in all_types if x.value != remove_beginning_ignore_case(type_str, "!")]
            else:
                parsed_types = [map_attribute(remove_trailing_whitespace(x)) for x in type_str.split(",")]
            continue

        if arg.lower().startswith("event:"):
            event_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "event:").lower())

            if event_str.startswith("!"):
                parsed_events = [x for x in all_events if x.value != remove_beginning_ignore_case(event_str, "!")]
            else:
                parsed_events = [map_event(remove_trailing_whitespace(x)) for x in event_str.split(",")]
            continue

        if arg.lower().startswith("affection:"):
            affection_str = remove_trailing_whitespace(remove_beginning_ignore_case(arg, "affection:").lower())

            if affection_str.startswith("!"):
                parsed_affections = [x for x in all_affections if x != remove_beginning_ignore_case(affection_str, "!")]
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


def replace_duplicates_in_team(criteria: Dict[str, Any], team_to_deduplicate: List[Unit]) -> None:
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
