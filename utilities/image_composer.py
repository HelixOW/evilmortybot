import discord
import math
from PIL import ImageFont, ImageDraw, Image as ImageLib
from PIL.ImageFont import FreeTypeFont
from PIL.Image import Image
from typing import Tuple, List, Dict
from utilities import img_size, flatten, chunks, chunks_dict, connection, half_img_size
from utilities.units import Unit, longest_named, unit_by_id
from utilities.banners import Banner, unit_with_chance
from utilities.tarot import tarot_units, tarot_food, tarot_name
from utilities.materials import Food


FONT_12: FreeTypeFont = ImageFont.truetype("pvp.ttf", 12)
FONT_24: FreeTypeFont = ImageFont.truetype("pvp.ttf", 24)
X_OFFSET = 5
Y_OFFSET = 9
DRAW_OFFSET = 5


def get_text_dimensions(text_string: str, font: FreeTypeFont = FONT_24) -> Tuple[int, int]:
    _, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height


def _text_with_shadow(draw: ImageDraw, text: str, x: int, y: int, fill: Tuple[int, int, int] = (255, 255, 255),
                      font: FreeTypeFont = FONT_24) -> None:
    text_with_shadow(draw, text, (x, y), fill, font)


def text_with_shadow(draw: ImageDraw, text: str, xy: Tuple[int, int], fill: Tuple[int, int, int] = (255, 255, 255),
                     font: FreeTypeFont = FONT_24) -> None:
    for x, y in [(xy[0] + 1, xy[1]),
                 (xy[0], xy[1] + 1),
                 (xy[0] + 1, xy[1] + 1)]:
        draw.text(
            xy=(x, y),
            text=text,
            fill=(0, 0, 0),
            font=font
        )

    draw.text(
        xy=(xy[0], xy[1]),
        text=text,
        fill=fill,
        font=font
    )


VS_DIM: Tuple[int, int] = get_text_dimensions("vs")
SSR_DIM: Tuple[int, int] = get_text_dimensions("All SSRs you got:")
WHEEL_DIM: Tuple[int, int] = get_text_dimensions("11) Wheel of Fortune")
TEAM_DIM: Tuple[int, int] = get_text_dimensions("Team 15:")
MATERIAL_DIM: Tuple[int, int] = get_text_dimensions("Seal of the [Beard of the Mountain Cat]")
DUMMY_UNIT_HEIGHT: int = get_text_dimensions("[Dummy] Bot")[1]


async def compose_team(rerolled_team: List[Unit],
                       re_units: Dict[int, List[Unit]] = None) -> Image:
    if re_units is None:
        re_units = {0: [], 1: [], 2: [], 3: []}

    icons: list[Image] = [_icon.resize([img_size, img_size]) for _icon in [_unit.icon for _unit in rerolled_team]]
    longest_named_unit = get_text_dimensions(longest_named(re_units[3]).name, FONT_12)[0] if len(
        re_units[3]) != 0 else 0

    if re_units[0] == 0 and re_units[1] == 0 and re_units[2] == 0 and re_units[3] == 0:
        img: Image = ImageLib.new('RGBA', (
            (img_size * 4) + (X_OFFSET * 3),
            img_size
        ))
        x: int = 0
        for icon in icons:
            img.paste(icon, (x, 0))
            x += icon.size[0] + X_OFFSET

        return img

    dummy_height: int = get_text_dimensions("[Dummy] Bot", FONT_12)[1]
    img: Image = ImageLib.new('RGBA', (
        (img_size * 4) + (X_OFFSET * 3) + ((longest_named_unit - img_size) if longest_named_unit > img_size else 0),
        img_size + ((Y_OFFSET + dummy_height) * len(flatten(re_units.values())))
    ))
    draw: ImageDraw = ImageDraw.Draw(img)
    x: int = 0

    icon: Image
    for icon in icons:
        img.paste(icon, (x, img.size[1] - img_size))
        x += icon.size[0] + 2

    pointer: int = 0
    re_unit_index: int
    ele: Unit
    for re_unit_index in re_units:
        for _, ele in enumerate(re_units[re_unit_index]):
            text_with_shadow(draw,
                             xy=(
                                 (img_size * re_unit_index) + (re_unit_index * X_OFFSET),
                                 (Y_OFFSET + dummy_height) * pointer
                             ),
                             text=ele.name,
                             font=FONT_12)
            pointer += 1

    return img


async def compose_pvp(player1: discord.Member, team1: List[Unit], player2: discord.Member, team2: List[Unit]) -> Image:
    left_icons: List[Image] = [_icon.resize([img_size, img_size]) for _icon in [_unit.icon for _unit in team1]]
    right_icons: List[Image] = [_icon.resize([img_size, img_size]) for _icon in [_unit.icon for _unit in team2]]
    name_height: int = get_text_dimensions(player1.display_name)[1] \
        if get_text_dimensions(player1.display_name)[1] > get_text_dimensions(player2.display_name)[1] \
        else get_text_dimensions(player2.display_name)[1]

    pvp_img = ImageLib.new('RGBA', (
        (img_size * 4) + (X_OFFSET * 3) + X_OFFSET + VS_DIM[0] + X_OFFSET + (img_size * 4) + (X_OFFSET * 3),
        name_height + Y_OFFSET + img_size
    ))
    draw = ImageDraw.Draw(pvp_img)

    text_with_shadow(draw,
                     xy=(X_OFFSET, 0),
                     text=player1.display_name)
    text_with_shadow(draw,
                     xy=(pvp_img.size[0] - get_text_dimensions(f"{player2.display_name}")[0] - X_OFFSET,
                         0
                         ),
                     text=player2.display_name)

    text_with_shadow(draw,
                     xy=((img_size * 4) + (X_OFFSET * 3) + X_OFFSET,
                         (img_size / 2) + name_height + Y_OFFSET
                         ),
                     text="vs")

    icons: List[Image]
    icon: Image
    x: int = 0
    for icons in [left_icons, right_icons]:
        for icon in icons:
            pvp_img.paste(icon, (x, name_height + Y_OFFSET))
            x += img_size + X_OFFSET
        x += VS_DIM[0] + X_OFFSET

    return pvp_img


async def compose_draw(from_banner: Banner, user: discord.Member) -> discord.File:
    u: Unit = await unit_with_chance(from_banner, user)
    connection.commit()
    return await u.discord_icon()


async def compose_five_multi_draw(from_banner: Banner, user: discord.Member) -> Image:
    img: Image = await compose_unit_five_multi_draw([(await unit_with_chance(from_banner, user)) for _ in range(5)])
    connection.commit()
    return img


async def compose_multi_draw(from_banner: Banner, user: discord.Member) -> Image:
    img: Image = await compose_unit_multi_draw([(await unit_with_chance(from_banner, user)) for _ in range(11)])
    connection.commit()
    return img


async def compose_unit_five_multi_draw(units: List[Unit]) -> Image:
    i: Image = ImageLib.new('RGBA', (
        (img_size * 3) + (DRAW_OFFSET * 2),
        (img_size * 2) + DRAW_OFFSET
    ))

    x: int = 0
    icon: Image
    for icon in [units[0].icon, units[1].icon, units[2].icon]:
        i.paste(icon, (x, 0))
        x += icon.size[0] + DRAW_OFFSET

    x: int = int((((img_size * 3) + (DRAW_OFFSET * 2)) - (img_size * 2)) / 2)
    for icon in [units[3].icon, units[4].icon]:
        i.paste(icon, (x, icon.size[1] + DRAW_OFFSET))
        x += icon.size[0] + DRAW_OFFSET

    return i


async def compose_banner_rotation(units: Dict[Unit, int]) -> Image:
    pull_rows: List[Dict[Unit, int]] = list(chunks_dict(units, 5))

    i: Image = ImageLib.new('RGBA', (
        (img_size * 4) + (DRAW_OFFSET * 3),  # x
        ((img_size * len(pull_rows)) + (DRAW_OFFSET * (len(pull_rows) - 1)))  # y
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    _units: Dict[Unit, int]
    key: Unit
    for _units in pull_rows:
        x: int = 0
        for key in _units:
            i.paste(await key.set_icon(), (x, y))
            text_with_shadow(draw, str(_units[key]), (x + 10, y + 10))
            x += img_size + 5
        y += img_size + 5

    return i


async def compose_unit_multi_draw(units: List[Unit], ssrs: Dict[Unit, int] = None) -> Image:
    if ssrs is None:
        ssrs = {}

    pull_rows: List[List[Unit]] = list(chunks(units, 4))
    ssr_rows: List[Dict[Unit, int]] = list(chunks_dict(ssrs, 4))

    i: Image = ImageLib.new('RGBA', (
        (img_size * 4) + (DRAW_OFFSET * 3),
        (
                ((img_size * 3) + (DRAW_OFFSET * 2)) +
                ((
                         (Y_OFFSET + SSR_DIM[1] + Y_OFFSET) +
                         (img_size * len(ssr_rows) + (DRAW_OFFSET * (len(ssr_rows) - 1)))
                 ) if len(ssrs) != 0 else 0)
        )
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    _units: List[Unit]
    _unit: Unit
    for _units in pull_rows:
        x: int = 0
        for _unit in _units:
            i.paste(await _unit.set_icon(), (x, y))
            x += img_size + DRAW_OFFSET
        y += img_size + DRAW_OFFSET

    if len(ssrs) == 0:
        return i

    y -= DRAW_OFFSET
    y += Y_OFFSET

    text_with_shadow(draw, xy=(0, y),
                     text="All SSRs you got:")

    y += SSR_DIM[1] + Y_OFFSET

    ssr_dict: Dict[int, int]
    key: Unit
    for ssr_dict in ssr_rows:
        x: int = 0
        for key in ssr_dict:
            i.paste(await key.set_icon(), (x, y))
            text_with_shadow(draw, str(ssr_dict[key]), (x + 10, y + 10))
            x += img_size + DRAW_OFFSET
        y += img_size + DRAW_OFFSET

    return i


async def compose_box(units_dict: Dict[int, int]) -> Image:
    box_rows: List[List[int]] = list(chunks(list(units_dict.keys()), 5))

    i: Image = ImageLib.new('RGBA', (
        (img_size * 5) + (4 * 5),
        (img_size * len(box_rows)) + (5 * (len(box_rows) - 1))
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    unit_ids: List[int]
    unit_id: int
    for unit_ids in box_rows:
        x: int = 0
        for unit_id in unit_ids:
            box_unit: Unit = unit_by_id(unit_id)
            i.paste(await box_unit.set_icon(), (x, y))
            text_with_shadow(draw, str(units_dict[unit_id]), (x + 5, y + 10))
            x += img_size + 5
        y += img_size + 5

    return i


async def compose_paged_unit_list(cus_units: List[Unit], per_page: int) -> List[Image]:
    return [await compose_unit_list(list(chunks(cus_units, per_page))[i])
            for i in range(math.ceil(len(cus_units) / per_page))]


async def compose_unit_list(cus_units: List[Unit]) -> Image:
    name_dim: Tuple[int, int] = get_text_dimensions(longest_named().name + " (Nr. 999)")
    i: Image = ImageLib.new('RGBA', (
        img_size + name_dim[0] + 5,
        (img_size * len(cus_units)) + (5 * len(cus_units))
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    cus_unit: Unit
    for cus_unit in cus_units:
        i.paste(await cus_unit.set_icon(), (0, y))
        text_with_shadow(draw, xy=(5 + img_size, y + (img_size / 2) - (name_dim[1] / 2)),
                         text=cus_unit.name + f" (Nr. {cus_unit.unit_id})")
        y += img_size + 5

    return i


async def compose_tarot_list() -> Image:
    i: Image = ImageLib.new('RGBA', (
        X_OFFSET + WHEEL_DIM[0] + X_OFFSET + (img_size * len(tarot_units[1])) + (X_OFFSET * (len(tarot_units[1]) - 1)),
        (img_size * 22) + (Y_OFFSET * 21)
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    unit_id: List[int]
    _unit: Unit
    for unit_id in tarot_units:
        text_with_shadow(draw, xy=(0, y + (img_size / 2)),
                         text=tarot_name(unit_id))
        x: int = X_OFFSET + WHEEL_DIM[0] + X_OFFSET
        for _unit in [unit_by_id(x) for x in tarot_units[unit_id]]:
            i.paste(await _unit.set_icon(), (x, y))
            x += img_size + X_OFFSET
        y += img_size + Y_OFFSET

    return i


async def compose_paged_tarot_list(page: int) -> Image:
    paged_list: List[List[int]] = list(chunks(tarot_units[page], 5))
    i: Image = ImageLib.new('RGBA', (
        (img_size * 5) + (X_OFFSET * 4),
        (img_size * len(paged_list)) + (5 * (len(paged_list) - 1))
    ))

    y: int = 0
    row: List[int]
    _unit: Unit
    for row in paged_list:
        x: int = 0
        for _unit in [unit_by_id(x) for x in row]:
            i.paste(await _unit.set_icon(), (x, y))
            x += img_size + 5
        y += img_size + 5
    return i


async def compose_banner_list(b: Banner, include_all: bool = False) -> Image:
    if len(b.ssr_units + b.rate_up_units) == 0:
        return ImageLib.new('RGBA', (0, 0))
    _units: List[Unit] = b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else [])
    unit_text: Tuple[int, int] = get_text_dimensions(
        longest_named(_units).name + " - 0.9999%")

    i: Image = ImageLib.new('RGBA', (
        img_size + unit_text[0] + X_OFFSET,
        (img_size * len(_units)) + (Y_OFFSET * len(_units))))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    unit_list: List[Unit]
    unit_rate: float
    _unit: Unit
    for unit_list, unit_rate in [(b.rate_up_units, b.ssr_unit_rate_up),
                                 (b.ssr_units, b.ssr_unit_rate),
                                 (b.sr_units, b.sr_unit_rate),
                                 (b.r_units, b.r_unit_rate)]:
        for _unit in unit_list:
            i.paste(await _unit.set_icon(), (0, y))
            text_with_shadow(draw, xy=(5 + img_size, y + (img_size / 2) - (unit_text[1] / 2)),
                             text=f"{_unit.name} - {unit_rate}%")
            y += img_size + 5

    return i


async def compose_tarot(card1: int, card2: int, card3: int, card4: int, food: int) -> Image:
    food: List[Food] = tarot_food[food]

    longest: List[Unit] = sorted([[unit_by_id(x) for x in tarot_units[card1]],
                                  [unit_by_id(x) for x in tarot_units[card2]],
                                  [unit_by_id(x) for x in tarot_units[card3]],
                                  [unit_by_id(x) for x in tarot_units[card4]]], key=len, reverse=True)[0]
    longest_name: str = sorted([tarot_name(x) for x in [card1, card2, card3, card4]], key=len, reverse=True)[0]

    i: Image = ImageLib.new('RGBA', (
        (len(longest) * img_size) + (X_OFFSET * (len(longest) - 1)) +  # x
        X_OFFSET + get_text_dimensions(longest_name)[0] + X_OFFSET,  # x
        (4 * img_size) + (3 * Y_OFFSET) +  # y
        Y_OFFSET + (len(food) * half_img_size) + (Y_OFFSET * (len(food) - 1))
    ))

    draw: ImageDraw = ImageDraw.Draw(i)
    card: int
    y: int
    unit: Unit
    for card, y in [(card1, 0), (card2, img_size + Y_OFFSET),
                    (card3, (img_size * 2) + (Y_OFFSET * 2)),
                    (card4, (img_size * 3) + (Y_OFFSET * 3))]:
        x: int = X_OFFSET + get_text_dimensions(longest_name)[0] + X_OFFSET
        text_with_shadow(draw, tarot_name(card), (X_OFFSET, y + (img_size / 2)))
        for unit in [unit_by_id(x) for x in tarot_units[card]]:
            i.paste(await unit.set_icon(), (x, y))
            x += img_size + X_OFFSET

    y: int = (4 * img_size) + (4 * Y_OFFSET)
    _food: Food
    food_icon: Image
    for _food in food:
        x = X_OFFSET + get_text_dimensions(_food.name)[0] + X_OFFSET + X_OFFSET
        text_with_shadow(draw, _food.name,
                         (X_OFFSET, y + (half_img_size / 2) - (get_text_dimensions(_food.name)[1] / 2)))
        for food_icon in _food.icons:
            i.paste(food_icon, (x, y))
            x += half_img_size + X_OFFSET + X_OFFSET
        y += half_img_size + Y_OFFSET

    return i


async def compose_random_select_team(possible: List[Unit]) -> Image:
    rows: List[List[Unit]] = list(chunks(possible, 4))

    i: Image = ImageLib.new('RGBA', (
        X_OFFSET + TEAM_DIM[0] + X_OFFSET + (img_size * 4) + (X_OFFSET * 3),
        (img_size * len(rows)) + (Y_OFFSET * (len(rows) - 1))
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    counter: int = 0
    row: List[Unit]
    _unit: Unit
    for row in rows:
        counter += 1
        text_with_shadow(draw,
                         text=f"Team: {counter}",
                         xy=(5, y + (img_size / 2)))
        x: int = X_OFFSET + TEAM_DIM[0] + X_OFFSET
        for _unit in row:
            i.paste(_unit.icon, (x, y))
            x += img_size + 5
        draw.line([(0, y + img_size + 3), (i.size[0], y + img_size + 3)], width=3)
        y += img_size + 9

    return i


async def compose_awakening(materials: dict) -> Image:
    i: Image = ImageLib.new('RGBA', (
        img_size + X_OFFSET + get_text_dimensions("15")[0],
        (img_size * len(materials)) + (Y_OFFSET * (len(materials) - 1))
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    for material in materials:
        _text_with_shadow(draw,
                          x=X_OFFSET,
                          y=y + (img_size / 2),
                          text=str(materials[material]) + "x")
        x: int = X_OFFSET + get_text_dimensions(str(materials[material]) + "x")[0] + X_OFFSET
        i.paste(material.icon, (x, y))
        y += img_size + Y_OFFSET

    return i
