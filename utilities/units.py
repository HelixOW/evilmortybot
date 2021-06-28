from __future__ import annotations
import typing

import discord
import PIL.Image as ImageLib
import aiohttp
import random as ra

from PIL.Image import Image as Img
from typing import List, Dict, Optional, Any
from enum import Enum
from utilities import img_size, unit_list, remove_beginning_ignore_case, image_to_discord, \
    embeds
from io import BytesIO


class Grade(Enum):
    r = "r"
    sr = "sr"
    ssr = "ssr"

    def to_int(self) -> int:
        if self.value == "ssr":
            return 0
        if self.value == "sr":
            return 1
        return 2


class Type(Enum):
    red = "red"
    gre = "green"
    blue = "blue"

    def to_discord_color(self) -> discord.Color:
        if self.value == "red":
            return discord.Color.red()
        if self.value == "blue":
            return discord.Color.blue()
        return discord.Color.green()


class Race(Enum):
    demon = "demon"
    giant = "giant"
    human = "human"
    fairy = "fairy"
    goddess = "goddess"
    unknown = "unknown"


class Event(Enum):
    base_game = "gc"
    slime = "slime"
    aot = "aot"
    kof = "kof"
    new_year = "newyear"
    halloween = "halloween"
    festival = "festival"
    valentine = "valentine"
    rezero = "rezero"
    stranger = "stranger"
    ragnarok = "ragnarok"
    custom = "custom"


class Affection(Enum):
    sin = "sins"
    commandments = "commandments"
    knight = "holyknights"
    catastrophe = "catastrophes"
    angel = "archangels"
    none = "none"


all_races: List[Race] = [Race.demon, Race.giant, Race.human, Race.fairy, Race.goddess, Race.unknown]
all_grades: List[Grade] = [Grade.r, Grade.sr, Grade.ssr]
all_types: List[Type] = [Type.red, Type.gre, Type.blue]
all_events: List[Event] = [Event.base_game, Event.slime, Event.aot, Event.kof, Event.festival, Event.new_year,
                           Event.valentine, Event.halloween, Event.rezero, Event.stranger, Event.ragnarok]
all_affections: List[str] = [Affection.sin.value, Affection.commandments.value, Affection.catastrophe.value,
                             Affection.angel.value, Affection.knight.value, Affection.none.value]

frames: Dict[Type, Dict[Grade, Img]] = {
    Type.blue: {
        Grade.r: ImageLib.open("gc/frames/blue_r_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.sr: ImageLib.open("gc/frames/blue_sr_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.ssr: ImageLib.open("gc/frames/blue_ssr_frame.png").resize((img_size, img_size)).convert("RGBA")
    },
    Type.red: {
        Grade.r: ImageLib.open("gc/frames/red_r_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.sr: ImageLib.open("gc/frames/red_sr_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.ssr: ImageLib.open("gc/frames/red_ssr_frame.png").resize((img_size, img_size)).convert("RGBA")
    },
    Type.gre: {
        Grade.r: ImageLib.open("gc/frames/green_r_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.sr: ImageLib.open("gc/frames/green_sr_frame.png").resize((img_size, img_size)).convert("RGBA"),
        Grade.ssr: ImageLib.open("gc/frames/green_ssr_frame.png").resize((img_size, img_size)).convert("RGBA")
    }
}
frame_backgrounds: Dict[Grade, Img] = {
    Grade.r: ImageLib.open("gc/frames/r_frame_background.png").resize((img_size, img_size)).convert("RGBA"),
    Grade.sr: ImageLib.open("gc/frames/sr_frame_background.png").resize((img_size, img_size)).convert("RGBA"),
    Grade.ssr: ImageLib.open("gc/frames/ssr_frame_background.png").resize((img_size, img_size)).convert("RGBA")
}


def map_attribute(raw_att: str) -> Optional[Type]:
    raw_att: str = raw_att.lower()
    if raw_att in ["blue", "speed", "b"]:
        return Type.blue
    if raw_att in ["red", "strength", "r"]:
        return Type.red
    if raw_att in ["green", "hp", "g"]:
        return Type.gre
    return None


def map_grade(raw_grade: str) -> Optional[Grade]:
    raw_grade: str = raw_grade.lower()
    if raw_grade == "r":
        return Grade.r
    if raw_grade == "sr":
        return Grade.sr
    if raw_grade == "ssr":
        return Grade.ssr
    return None


def map_race(raw_race: str) -> Optional[Race]:
    raw_race: str = raw_race.lower()
    if raw_race in ["demon", "demons"]:
        return Race.demon
    if raw_race in ["giant", "giants"]:
        return Race.giant
    if raw_race in ["fairy", "fairies"]:
        return Race.fairy
    if raw_race in ["human", "humans"]:
        return Race.human
    if raw_race in ["goddess", "god", "gods"]:
        return Race.goddess
    if raw_race in ["unknown"]:
        return Race.unknown
    return None


def map_event(raw_event: str) -> Event:
    raw_event: str = raw_event.replace(" ", "").lower()
    if raw_event in ["slime", "tensura"]:
        return Event.slime
    if raw_event in ["aot", "attackontitan", "titan"]:
        return Event.aot
    if raw_event in ["kof", "kingoffighter", "kingoffighters"]:
        return Event.kof
    if raw_event in ["valentine", "val"]:
        return Event.valentine
    if raw_event in ["newyears", "newyear", "ny"]:
        return Event.new_year
    if raw_event in ["halloween", "hal", "hw"]:
        return Event.halloween
    if raw_event in ["festival", "fes", "fest"]:
        return Event.festival
    if raw_event in ["rezero", "re", "zero"]:
        return Event.rezero
    if raw_event in ["custom"]:
        return Event.custom
    if raw_event in ["stranger", "stranger things", "things", "st"]:
        return Event.stranger
    if raw_event in ["ragnarok", "ragna"]:
        return Event.ragnarok
    return Event.base_game


def map_affection(raw_affection: str) -> str:
    raw_affection: str = raw_affection.replace(" ", "").lower()
    if raw_affection in ["sins", "sin"]:
        return Affection.sin.value
    if raw_affection in ["holyknight", "holyknights", "knights", "knight"]:
        return Affection.knight.value
    if raw_affection in ["commandments", "commandment", "command"]:
        return Affection.commandments.value
    if raw_affection in ["catastrophes", "catastrophes"]:
        return Affection.catastrophe.value
    if raw_affection in ["arcangels", "angels", "angel", "arcangel"]:
        return Affection.angel.value
    if raw_affection in ["none", "no"]:
        return Affection.none.value
    if raw_affection in all_affections:
        return raw_affection
    return Affection.none.value


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
                 event: Event = Event.base_game,
                 affection_str: str = Affection.none.value,
                 icon_path: str = "gc/icons/{}.png",
                 alt_names: Optional[List[str]] = None,
                 is_jp: bool = False,
                 emoji_id: str = None) -> None:

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
        self.emoji: str = f"<:{self.unit_id if self.unit_id > 9 else '0' + str(self.unit_id)}:{emoji_id}>"

        if unit_id > 0:
            img: Img = ImageLib.new('RGBA', (img_size, img_size))
            img.paste(ImageLib.open(icon_path.format(unit_id)).resize((img_size, img_size)), (0, 0))
            self.icon: Img = img
        else:
            self.icon: Optional[Img] = None

    async def info_embed(self) -> discord.Embed:
        embed = embeds.DefaultEmbed(
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
        ).add_field(
            name="Emoji",
            value=f"```{self.emoji}```",
        )
        if len(self.alt_names) != 0:
            embed._fields = [
                                {'inline': True, 'name': "Alternative names",
                                 'value': "```" + ",\n".join(self.alt_names) + "```"}
                            ] + embed._fields
        return embed

    def display_alt_names(self) -> str:
        return "```" + ",\n".join(self.alt_names) + "```"

    async def discord_icon(self) -> discord.File:
        return await image_to_discord(self.icon)

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
        if self.type == Type.red:
            return discord.Color.red()
        if self.type == Type.gre:
            return discord.Color.green()
        if self.type == Type.blue:
            return discord.Color.blue()
        return discord.Color.gold()

    def __str__(self) -> str:
        return f"{self.name} ({self.unit_id})"

    def __repr__(self):
        return f"{self.name} ({self.unit_id})"

    def __eq__(self, other: Unit) -> bool:
        if other is not None:
            if isinstance(other, Unit):
                return self.unit_id == other.unit_id
            elif isinstance(other, int):
                return self.unit_id == other
        return False

    # def __lt__(self, other: Unit) -> bool:
    #     if other is not None:
    #         return sorted([self.name, other.name], key=lambda item: (item, len(item)))[0] == self.name
    #     return False

    def __lt__(self, other: Unit) -> bool:
        if other is not None:
            if isinstance(other, Unit):
                return self.unit_id < other.unit_id
            elif isinstance(other, int):
                return self.unit_id < other
        return False

    def __gt__(self, other: Unit) -> bool:
        if other is not None:
            if isinstance(other, Unit):
                return self.unit_id > other.unit_id
            elif isinstance(other, int):
                return self.unit_id > other
        return False

    def __le__(self, other: Unit) -> bool:
        if other is not None:
            if isinstance(other, Unit):
                return self.unit_id <= other.unit_id
            elif isinstance(other, int):
                return self.unit_id <= other
        return False

    def __ge__(self, other: Unit) -> bool:
        if other is not None:
            if isinstance(other, Unit):
                return self.unit_id >= other.unit_id
            elif isinstance(other, int):
                return self.unit_id >= other
        return False

    def __hash__(self):
        return self.unit_id

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


def unit_by_name_no_case(name: str) -> Optional[Unit]:
    return next((x for x in unit_list if name.lower() == x.name.lower()), None)


def unit_by_vague_name(name: str, sample_list: List[Unit] = unit_list) -> List[Unit]:
    return [x for x in sample_list if (name.strip().lower() in [y.lower() for y in
                                                                x.alt_names] or f" {name.strip().lower()}" in x.name.strip().lower())]


def unit_by_name_or_id(name_or_id: typing.Union[str, int]) -> List[Unit]:
    if isinstance(name_or_id, str):
        return unit_by_vague_name(name_or_id)
    elif isinstance(name_or_id, int):
        return [unit_by_id(name_or_id)]
    raise ValueError


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
        Race.human: 0,
        Race.fairy: 0,
        Race.giant: 0,
        Race.unknown: 0,
        Race.demon: 0,
        Race.goddess: 0
    }
    parsed_grades: List[Grade] = []
    parsed_types: List[Type] = []
    parsed_events: List[Event] = []
    parsed_affections: List[str] = []
    parsed_url: str = ""
    parsed_new_name: str = ""
    parsed_owner: int = 0
    jp: bool = False
    unparsed: List[str] = []

    for _, ele in enumerate(args):
        arg: str = ele.strip()

        if arg.lower().startswith("new_name:"):
            parsed_new_name = remove_beginning_ignore_case(arg, "new_name:").strip()
            continue

        if arg.lower().startswith("url:"):
            parsed_url = remove_beginning_ignore_case(arg, "url:").strip()
            continue

        if arg.lower().startswith("jp") or arg.lower().startswith("kr"):
            jp = True
            continue

        if arg.lower().startswith("owner:"):
            parsed_owner = int(remove_beginning_ignore_case(arg, "owner:").strip()[3:-1])
            continue

        if arg.lower().startswith("name:"):
            name_str = remove_beginning_ignore_case(arg, "name:").strip()

            if name_str.startswith("!"):
                parsed_names = [x.name for x in unit_list if
                                x.name.lower() != remove_beginning_ignore_case(name_str, "!").lower()]
            else:
                parsed_names = [x.strip() for x in name_str.split(",")]
            continue

        if arg.lower().startswith("race:"):
            race_str = remove_beginning_ignore_case(arg, "race:").lower().strip()

            if race_str.startswith("!"):
                parsed_races = [x for x in all_races if x.value != remove_beginning_ignore_case(race_str, "!")]
            else:
                races_with_count = [x.strip() for x in race_str.split(",")]
                for _, element in enumerate(races_with_count):
                    apr = element.split("*")

                    if len(apr) == 2:
                        parsed_races.append(map_race(apr[1]))
                        parsed_race_count[map_race(apr[1])] += int(apr[0])
                    else:
                        parsed_races.append(map_race(element))
            continue

        if arg.lower().startswith("grade:"):
            grade_str = remove_beginning_ignore_case(arg, "grade:").lower().strip()

            if grade_str.startswith("!"):
                parsed_grades = [x for x in all_grades if x.value != remove_beginning_ignore_case(grade_str, "!")]
            else:
                parsed_grades = [map_grade(x.strip()) for x in grade_str.split(",")]
            continue

        if arg.lower().startswith("type:"):
            type_str = remove_beginning_ignore_case(arg, "type:").lower().strip()

            if type_str.startswith("!"):
                parsed_types = [x for x in all_types if x.value != remove_beginning_ignore_case(type_str, "!")]
            else:
                parsed_types = [map_attribute(x.strip()) for x in type_str.split(",")]
            continue

        if arg.lower().startswith("event:"):
            event_str = remove_beginning_ignore_case(arg, "event:").lower().strip()

            if event_str.startswith("!"):
                parsed_events = [x for x in all_events if x.value != remove_beginning_ignore_case(event_str, "!")]
            else:
                parsed_events = [map_event(x.strip()) for x in event_str.split(",")]
            continue

        if arg.lower().startswith("affection:"):
            affection_str = remove_beginning_ignore_case(arg, "affection:").lower().strip()

            if affection_str.startswith("!"):
                parsed_affections = [x for x in all_affections if x != remove_beginning_ignore_case(affection_str, "!")]
            else:
                parsed_affections = [map_affection(x.strip()) for x in affection_str.split(",")]
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


def replace_duplicates_in_team(criteria: Dict[str, Any], team_to_deduplicate: List[Unit]) -> None:
    team_simple_names: List[str] = ["", "", "", ""]
    team_races: Dict[Race, int] = {
        Race.human: 0,
        Race.fairy: 0,
        Race.giant: 0,
        Race.unknown: 0,
        Race.demon: 0,
        Race.goddess: 0
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
