from enum import Enum
from utilities.materials import Material, AdvancedGrade
import PIL.Image as ImageLib


class GearType(Enum):
    ATTACK: str = "Onslaught"
    DEFENSE: str = "Iron Wall"
    HP: str = "Life"
    CRIT_CHANCE: str = "Concentration"
    CRIT_RESISTANCE: str = "Mind's Eye"
    RECOVERY_RATE: str = "Recovery"


class GearPosition(Enum):
    BRACELET: str = "TOP LEFT"
    NECKLACE: str = "MID LEFT"
    BELT: str = "BOTTOM LEFT"
    RING: str = "TOP RIGHT"
    EAR_RINGS: str = "MID RIGHT"
    RUNE: str = "BOTTOM RIGHT"


class Gear(Material):
    def __init__(self, grade: AdvancedGrade, g_type: GearType, g_pos: GearPosition):
        super().__init__(f"{g_type.value} {g_pos.name.lower()}",
                         grade,
                         ImageLib.open(f"../gc/gear/{g_type.value}/{g_type.value}_{g_pos.name.lower()}_{grade.value}.png"))
        self.gear_type: GearType = g_type
        self.g_pos: GearPosition = g_pos
