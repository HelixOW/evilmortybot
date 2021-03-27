import PIL.Image as ImageLib

from enum import Enum
from PIL.Image import Image
from typing import Optional, List


class Food:
    def __init__(self, f_type: str, true_name: str, images: List[Image]) -> None:
        self.food_type: str = f_type
        self.name: str = true_name
        self.icons: List[Image] = images


class AdvancedGrade(Enum):
    C = "c"
    UC = "uc"
    R = "r"
    SR = "sr"
    SSR = "ssr"
    UR = "ur"


class Material:
    def __init__(self, _id: int,  name: str, grade: AdvancedGrade = AdvancedGrade.R, icon: Optional[Image] = None):
        self.material_id: int = _id
        self.name: str = name
        if icon is None:
            self.icon = ImageLib.open(f"gc/materials/{name.lower().replace(' ', '_')}_{grade.value}.png")
        else:
            self.icon = icon

    def __str__(self):
        return self.name + f" {self.material_id}"

    def __repr__(self):
        return self.name + f" {self.material_id}"


MATERIALS = [
    Material(_id=101, name="Water of Life", grade=AdvancedGrade.C),
    Material(_id=102, name="Water of Life", grade=AdvancedGrade.UC),
    Material(_id=103, name="Water of Life", grade=AdvancedGrade.R),
    Material(_id=104, name="Water of Life", grade=AdvancedGrade.SR),
    Material(_id=105, name="Water of Life", grade=AdvancedGrade.SSR),
    Material(_id=106, name="Water of Life", grade=AdvancedGrade.UR),

    Material(_id=201, name="Demon Blood", grade=AdvancedGrade.C),
    Material(_id=202, name="Demon Blood", grade=AdvancedGrade.UC),
    Material(_id=203, name="Demon Blood", grade=AdvancedGrade.R),
    Material(_id=204, name="Demon Blood", grade=AdvancedGrade.SR),
    Material(_id=205, name="Demon Blood", grade=AdvancedGrade.SSR),
    Material(_id=206, name="Demon Blood", grade=AdvancedGrade.UR),

    Material(3, "Identifying Nametag"),
    Material(4, "Usable Armor Fragment"),
    Material(5, "Seal of the [Beard of the Mountain Cat]"),
    Material(6, "Mustache Comb"),
    Material(7, "Wolf Fang"),
    Material(8, "Friendship Bracelet"),

    Material(9, "Patrol Log"),
    Material(10, "Insect's Poison Stinger"),
    Material(11, "Ancient Warrior Armor Fragment"),
    Material(12, "Soul Crystal"),
    Material(13, "Chess Piece Fragment"),
    Material(14, "Sharp Spike"),

    Material(15, "Broken Horn"),
    Material(16, "Weathered Knighthood Insignia"),
    Material(17, "Non-stick Spider Silk"),
    Material(18, "Pungent Piece of Cloth"),
    Material(19, "Cuspid Fragment"),
    Material(20, "Mysterious Magic Potion"),

    Material(21, "Ominous Dark Orb"),
    Material(22, "Sharp Horn"),
    Material(23, "Warrior's Emblem"),
    Material(24, "Token of Immortality"),
    Material(25, "Wind Feather"),
    Material(26, "Ominous Spellcasting Fluid"),

    Material(27, "Old Armor Fragment"),
    Material(28, "Murky Soul Crystal"),
    Material(29, "Hard Bone Fragment"),
    Material(30, "Totem"),
    Material(31, "Spellcasting Ivory Charm"),
    Material(32, "Blood-stained Battle Helm"),

    Material(33, "High-rank Mage's Mask"),
    Material(34, "Royal Gift"),
    Material(35, "Magical Robe"),
    Material(36, "Double-edged Sword Fragment"),
    Material(37, "Emblem of the Knighthood of Liones"),
    Material(38, "Token of Courage")
]


def find_material(_id: int):
    return next((x for x in MATERIALS if _id == x.material_id), None)


def longest_material_icons(materials: dict):
    return sorted(materials.keys(), key=lambda k: len(k.icons), reverse=True)[0]


def map_food(raw_type: str) -> str:
    if raw_type == "atk":
        return "Attack"
    if raw_type == "crit_ch":
        return "Crit Chance"
    if raw_type == "crit_dmg":
        return "Crit damage"
    if raw_type == "pierce":
        return "Pierce"
    if raw_type == "res":
        return "Resistance"
    if raw_type == "crit_def":
        return "Crit Defense"
    if raw_type == "crit_res":
        return "Crit Resistance"
    if raw_type == "lifesteal":
        return "Lifesteal"
    if raw_type == "cc":
        return "CC"
    if raw_type == "ult":
        return "Ult Gauge"
    if raw_type == "evade":
        return "Evasion"
    if raw_type == "def":
        return "Defense"
    if raw_type == "hp":
        return "HP"
    if raw_type == "reg":
        return "Regeneration Rate"
    if raw_type == "rec":
        return "Recovery Rate"
