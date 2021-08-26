from discord.ext import commands
from discord.ext.commands import Cog, Context
from random import random
from utilities.embeds import DefaultEmbed


def raw_calc_dmg(modifier: float, atk: float, crit_damage: float, crit_chance: float, defense: float,
                 crit_defense: float, crit_resistance: float, type_advantage: float, variance: bool = False):
    crit_mod = crit_damage - crit_defense if (crit_chance - crit_resistance) > random() else 1
    type_advantage = 1.3 if type_advantage > 0 else 0.8 if type_advantage < 0 else 1
    variance_mod = 0.85 + (1.05 - 0.85) if variance else 1

    return variance_mod * (modifier * atk * crit_mod - defense) * type_advantage


def calc_damage(modifier: float, atk: float, atk_buff: float, atk_related_buff: tuple, crit_damage: float,
                defense: float, defense_related_debuff: tuple, crit_defense: float, type_advantage: float = 0,
                is_spike: bool = False, amplify_stacks: int = 0, freeze: int = 0, is_crit: int = 1):
    buffed_atk: float = atk * atk_buff
    additional_damage: float = 1 + 0.3 * amplify_stacks
    if freeze:
        defense_related_debuff = ()
        if freeze >= 2:
            additional_damage += (freeze - 1) + (freeze - 3) * 0.2
    for atk_b, pierce_b, crit_d_b in atk_related_buff:
        buffed_atk *= 1 + atk_b
        crit_damage += crit_d_b
    for debuff in defense_related_debuff:
        crit_defense = max(crit_defense + debuff, 0)
    if is_spike:
        crit_damage *= 2

    return raw_calc_dmg(modifier=modifier * additional_damage,
                        atk=buffed_atk,
                        crit_damage=crit_damage,
                        crit_chance=is_crit,
                        defense=defense,
                        crit_defense=crit_defense,
                        crit_resistance=0,
                        type_advantage=type_advantage)


def calc_kelak(boss: str = "kelak", atk: float = 0, crit_damage: float = 100, difficulty: str = "ex",
               ult: int = 6, ggowther: int = 5, stacks: int = 5, deri_buff: int = 3,
               deri_evade: bool = True, sariel_sub: bool = True, ellatte_stacks: int = 0, ellatte_debuff: int = 0,
               ellatte_ult: bool = False, helbram_buff: int = 3, freeze: int = 0,
               is_crit: bool = True):
    crit_damage = crit_damage / 100
    defense, resistance = 0, 0.2
    crit_defense = {
        'kelak': {'ex': 0.75, 'h': 0.47, 'n': 0.35},
        'einek': {'ex': 0, 'h': 0, 'n': 0},
        'akumu': {'ex': 0.5, 'h': 0.47, 'n': 0}
    }[boss][difficulty]

    atk_buff, pierce = 1, 0.3
    atk_related_buff = []
    defense_related_debuff = []

    advantage = 0
    is_spike = False
    amplify_stacks = 0

    ult_modifier = (6.3 + (ult - 1) * 0.63)
    amplify_stacks += stacks
    atk_buff *= (1 + 0.1 * stacks)
    amplify_stacks += 3
    if deri_buff == 1:
        atk_buff *= 1.2
    elif deri_buff == 2:
        atk_buff *= 1.3
    else:
        atk_buff *= 1.5
    amplify_stacks += 1 if deri_evade else 0

    if ellatte_stacks != 0:
        atk_related_buff.append((0, 0, 0.05 * ellatte_stacks))

    if ellatte_debuff != 0:
        defense_related_debuff.append((-0.2 - ellatte_debuff * 0.1))

    if ellatte_ult:
        amplify_stacks += 2

    if helbram_buff:
        buff = 0.15 if helbram_buff == 1 else 0.2 if helbram_buff == 2 else 0.3 if helbram_buff == 3 else 0
        if amplify_stacks:
            amplify_stacks += 1
        atk_related_buff.append((buff,) * 3)

    if ggowther != 0:
        atk_related_buff.append((0.07 * ggowther,) * 3)

    if sariel_sub:
        defense_related_debuff.append(-0.5)

    return calc_damage(ult_modifier,
                       atk, atk_buff, atk_related_buff, crit_damage, defense, defense_related_debuff, crit_defense,
                       advantage, is_spike=is_spike, amplify_stacks=amplify_stacks, freeze=freeze, is_crit=is_crit)


class CalculationsCog(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def calc(self, ctx: Context, *, args: str = None):
        stats = {
            "boss": "kelak",
            "atk": 0,
            "crit_damage": 100,
            "difficulty": "ex",
            "ult_level": 6,
            "ggowther_stacks": 5,
            "deri_stacks": 10,
            "deri_buff": 3,
            "deri_evade": True,
            "sariel_sub": True,
            "ellatte_stacks": 0,
            "ellatte_debuff": 0,
            "ellatte_ult": False,
            "helbram_buff": 3,
            "freeze": 0,
            "is_crit": True
        }

        if args:
            for specific_arg in args.split(","):
                specific_arg = specific_arg.strip().lower()
                if "=" not in specific_arg:
                    continue
                specific_args = specific_arg.split("=")

                for arg, inputs, conv, kelak_exclusive in (
                        ("boss", ("boss", "type"), str, False),
                        ("atk", ("atk", "attack"), int, False),
                        ("crit_damage", ("cd", "critdamage", "crit-damage"), float, False),
                        ("difficulty", ("diff", "difficulty"), str, False),
                        ("ult_level", ("ult", "ultlevel", "ult-level"), int, False),
                        ("ggowther_stacks", ("ggowther",), int, False),
                        ("deri_stacks", ("stacks", "deristacks", "deri-stacks"), int, False),
                        ("deri_buff", ("deribuff", "deribuff", "deri-buff"), int, False),
                        ("deri_evade", ("evade", "derievade", "deri-evade"), bool, False),
                        ("sariel_sub", ("sariel", "sarielsub", "sariel-sub"), bool, False),
                        ("ellatte_stacks", ("ellatte", "ellattestacks", "ellatte-stacks"), int, True),
                        ("ellatte_debuff", ("debuff", "ellattedebuff", "ellatte-debuff"), int, True),
                        ("ellatte_ult", ("ellateult", "ellatte-ult"), bool, True),
                        ("helbram_buff", ("helbram", "helbrambuff", "helbram-buff"), int, False),
                        ("freeze", ("freeze", "freezelevel", "freeze-level"), int, True),
                        ("is_crit", ("crit", "crits", "is-crit"), bool, False)
                ):
                    if specific_args[0] in inputs:
                        if arg in "boss" and specific_args[0] not in "kelak" and kelak_exclusive:
                            continue
                        stats[arg] = conv(specific_args[1])

        points = calc_kelak(boss=stats["boss"], atk=stats["atk"], crit_damage=stats["crit_damage"],
                            difficulty=stats["difficulty"], ult=stats["ult_level"], ggowther=stats["ggowther_stacks"],
                            stacks=stats["deri_stacks"], deri_buff=stats["deri_buff"], deri_evade=stats["deri_evade"],
                            sariel_sub=stats["sariel_sub"], ellatte_stacks=stats["ellatte_stacks"],
                            ellatte_debuff=stats["ellatte_debuff"], ellatte_ult=stats["ellatte_ult"],
                            helbram_buff=stats["helbram_buff"], freeze=stats["freeze"], is_crit=stats["is_crit"])

        await ctx.send(embed=DefaultEmbed(title=f"Points for {stats['boss'].capitalize()}").add_field(
            name=":dagger: Attack", value=f"{stats['atk']:,}"
        ).add_field(
            name=":dart: Crit damage", value=f"{stats['crit_damage']}%"
        ).add_field(
            name=":beginner: Difficulty",
            value="Extreme" if stats["difficulty"] == 'ex' else "Hard" if stats["difficulty"] == 'h' else "Normal"
        ).add_field(
            name="<:deri_ult:872129958808535111> Ult level", value=stats["ult_level"], inline=False
        ).add_blank_field().add_field(
            name="<:deri_passive:872130404545609788> Derieri passive stacks",
            value=stats["deri_stacks"]
        ).add_field(
            name="<:134:844176979674267658> Gowther stacks",
            value=stats["ggowther_stacks"]
        ).add_field(
            name="<:ellatte_passive:872135166565425212> Ellatte stacks", value=stats["ellatte_stacks"]
        ).add_field(
            name="<:deri_buff:872130729297993769> Derieri buff level",
            value=stats["deri_buff"]
        ).add_field(
            name="<:151:844176979356155934> Sariel link?", value="Yes" if stats["sariel_sub"] else "No"
        ).add_field(
            name="<:ellatte_debuff:872134086666358825> Ellatte debuff", value=stats["ellatte_debuff"]
        ).add_field(
            name=":ninja: Derieri evade?", value="Yes" if stats["deri_evade"] else "No"
        ).add_field(
            name=":fairy: Helbram buff", value=stats["helbram_buff"]
        ).add_field(
            name="<:ellatte_ult:872134085714251846> Ellatte ult?", value="Yes" if stats["ellatte_ult"] else "No"
        ).add_field(
            name=":ice_cube: Freeze", value=stats["freeze"]
        ).add_field(
            name=":zap: Crit?", value="Yes" if stats["is_crit"] else "No"
        ).add_blank_field().add_field(
            name=":trophy: Hits for", value=f"{int(points):,}"
        ))


def setup(_bot):
    _bot.add_cog(CalculationsCog(_bot))
