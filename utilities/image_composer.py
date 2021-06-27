import discord
import math
from PIL import ImageDraw, Image as ImageLib
from PIL.ImageFont import FreeTypeFont
from PIL.Image import Image
from typing import Tuple, List, Dict
from utilities import img_size, flatten, chunks, chunks_dict, half_img_size, get_text_dimensions, \
    font_24, font_12, text_with_shadow, x_offset, y_offset
from utilities.units import Unit, longest_named, unit_by_id
from utilities.banners import Banner, unit_with_chance
from utilities.tarot import tarot_units, tarot_food, tarot_name
from utilities.materials import Food

draw_offset = 5


def _text_with_shadow(draw: ImageDraw, text: str, x: int, y: int, fill: Tuple[int, int, int] = (255, 255, 255),
                      font: FreeTypeFont = font_24) -> None:
    text_with_shadow(draw, text, (x, y), fill, font)


VS_DIM: Tuple[int, int] = get_text_dimensions("vs")
SSR_DIM: Tuple[int, int] = get_text_dimensions("All SSRs you got:")
WHEEL_DIM: Tuple[int, int] = get_text_dimensions("11) Wheel of Fortune")
TEAM_DIM: Tuple[int, int] = get_text_dimensions("Team 15:")
MATERIAL_DIM: Tuple[int, int] = get_text_dimensions("Seal of the [Beard of the Mountain Cat]")
DUMMY_UNIT_HEIGHT: int = get_text_dimensions("[Dummy] Bot")[1]
trade_dim: Tuple[int, int] = get_text_dimensions(">")


async def compose_team(rerolled_team: List[Unit],
                       re_units: Dict[int, List[Unit]] = None) -> Image:
    if re_units is None:
        re_units = {0: [], 1: [], 2: [], 3: []}

    icons: list[Image] = [_icon.resize([img_size, img_size]) for _icon in [_unit.icon for _unit in rerolled_team] if
                          _icon is not None]
    longest_named_unit = get_text_dimensions(longest_named(re_units[3]).name, font_12)[0] if len(
        re_units[3]) != 0 else 0

    if re_units[0] == 0 and re_units[1] == 0 and re_units[2] == 0 and re_units[3] == 0:
        img: Image = ImageLib.new('RGBA', (
            (img_size * 4) + (x_offset * 3),
            img_size
        ))
        x: int = 0
        for icon in icons:
            img.paste(icon, (x, 0))
            x += icon.size[0] + x_offset

        return img

    dummy_height: int = get_text_dimensions("[Dummy] Bot", font_12)[1]
    img: Image = ImageLib.new('RGBA', (
        (img_size * 4) + (x_offset * 3) + ((longest_named_unit - img_size) if longest_named_unit > img_size else 0),
        img_size + ((y_offset + dummy_height) * len(flatten(re_units.values())))
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
                                 (img_size * re_unit_index) + (re_unit_index * x_offset),
                                 (y_offset + dummy_height) * pointer
                             ),
                             text=ele.name,
                             font=font_12)
            pointer += 1

    return img


async def compose_pvp(player1: discord.Member, team1: List[Unit], player2: discord.Member, team2: List[Unit]) -> Image:
    left_icons: List[Image] = [_icon.resize([img_size, img_size]) for _icon in [_unit.icon for _unit in team1]]
    right_icons: List[Image] = [_icon.resize([img_size, img_size]) for _icon in [_unit.icon for _unit in team2]]
    name_height: int = get_text_dimensions(player1.display_name)[1] \
        if get_text_dimensions(player1.display_name)[1] > get_text_dimensions(player2.display_name)[1] \
        else get_text_dimensions(player2.display_name)[1]

    pvp_img = ImageLib.new('RGBA', (
        (img_size * 4) + (x_offset * 3) + x_offset + VS_DIM[0] + x_offset + (img_size * 4) + (x_offset * 3),
        name_height + y_offset + img_size
    ))
    draw = ImageDraw.Draw(pvp_img)

    text_with_shadow(draw,
                     xy=(x_offset, 0),
                     text=player1.display_name)
    text_with_shadow(draw,
                     xy=(pvp_img.size[0] - get_text_dimensions(f"{player2.display_name}")[0] - x_offset,
                         0
                         ),
                     text=player2.display_name)

    text_with_shadow(draw,
                     xy=((img_size * 4) + (x_offset * 3) + x_offset,
                         int(img_size / 2) + name_height + y_offset
                         ),
                     text="vs")

    icons: List[Image]
    icon: Image
    x: int = 0
    for icons in [left_icons, right_icons]:
        for icon in icons:
            pvp_img.paste(icon, (x, name_height + y_offset))
            x += img_size + x_offset
        x += VS_DIM[0] + x_offset

    return pvp_img


async def compose_draw(from_banner: Banner, user: discord.Member) -> discord.File:
    u: Unit = await unit_with_chance(from_banner, user)
    return await u.discord_icon()


async def compose_five_multi_draw(from_banner: Banner, user: discord.Member) -> Image:
    img: Image = await compose_unit_five_multi_draw([(await unit_with_chance(from_banner, user)) for _ in range(5)])
    return img


async def compose_multi_draw(from_banner: Banner, user: discord.Member) -> Image:
    img: Image = await compose_unit_multi_draw([(await unit_with_chance(from_banner, user)) for _ in range(11)])
    return img


async def compose_unit_five_multi_draw(units: List[Unit]) -> Image:
    i: Image = ImageLib.new('RGBA', (
        (img_size * 3) + (draw_offset * 2),
        (img_size * 2) + draw_offset
    ))

    x: int = 0
    icon: Image
    for icon in [units[0].icon, units[1].icon, units[2].icon]:
        i.paste(icon, (x, 0))
        x += icon.size[0] + draw_offset

    x: int = int((((img_size * 3) + (draw_offset * 2)) - (img_size * 2)) / 2)
    for icon in [units[3].icon, units[4].icon]:
        i.paste(icon, (x, icon.size[1] + draw_offset))
        x += icon.size[0] + draw_offset

    return i


async def compose_banner_rotation(rotation_units: Dict[Unit, int]) -> Image:
    pull_rows: List[Dict[Unit, int]] = list(chunks_dict(rotation_units, 5))

    i: Image = ImageLib.new('RGBA', (
        (img_size * 4) + (draw_offset * 3),  # x
        ((img_size * len(pull_rows)) + (draw_offset * (len(pull_rows) - 1)))  # y
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
        (img_size * 4) + (draw_offset * 3),
        (
                ((img_size * 3) + (draw_offset * 2)) +
                ((
                         (y_offset + SSR_DIM[1] + y_offset) +
                         (img_size * len(ssr_rows) + (draw_offset * (len(ssr_rows) - 1)))
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
            x += img_size + draw_offset
        y += img_size + draw_offset

    if len(ssrs) == 0:
        return i

    y -= draw_offset
    y += y_offset

    text_with_shadow(draw, xy=(0, y),
                     text="All SSRs you got:")

    y += SSR_DIM[1] + y_offset

    ssr_dict: Dict[Unit, int]
    key: Unit
    for ssr_dict in ssr_rows:
        x: int = 0
        for key in ssr_dict:
            i.paste(await key.set_icon(), (x, y))
            text_with_shadow(draw, str(ssr_dict[key]), (x + 10, y + 10))
            x += img_size + draw_offset
        y += img_size + draw_offset

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
        text_with_shadow(draw,
                         xy=(
                             5 + img_size,
                             y + int(img_size / 2) - int(name_dim[1] / 2)),
                         text=cus_unit.name + f" (Nr. {cus_unit.unit_id})")
        y += img_size + 5

    return i


async def compose_tarot_list() -> Image:
    i: Image = ImageLib.new('RGBA', (
        x_offset + WHEEL_DIM[0] + x_offset + (img_size * len(tarot_units[1])) + (x_offset * (len(tarot_units[1]) - 1)),
        (img_size * 22) + (y_offset * 21)
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    unit_id: int
    _unit: Unit
    for unit_id in tarot_units:
        text_with_shadow(draw,
                         xy=(0,
                             y + int(img_size / 2)),
                         text=tarot_name(unit_id))
        x: int = x_offset + WHEEL_DIM[0] + x_offset
        for _unit in [unit_by_id(x) for x in tarot_units[unit_id]]:
            i.paste(await _unit.set_icon(), (x, y))
            x += img_size + x_offset
        y += img_size + y_offset

    return i


async def compose_paged_tarot_list(page: int) -> Image:
    paged_list: List[List[int]] = list(chunks(tarot_units[page], 5))
    i: Image = ImageLib.new('RGBA', (
        (img_size * 5) + (x_offset * 4),
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


async def compose_tarot(card1: int, card2: int, card3: int, card4: int, food: int) -> Image:
    food: List[Food] = tarot_food[food]

    longest: List[Unit] = sorted([[unit_by_id(x) for x in tarot_units[card1]],
                                  [unit_by_id(x) for x in tarot_units[card2]],
                                  [unit_by_id(x) for x in tarot_units[card3]],
                                  [unit_by_id(x) for x in tarot_units[card4]]], key=len, reverse=True)[0]
    longest_name: str = sorted([tarot_name(x) for x in [card1, card2, card3, card4]], key=len, reverse=True)[0]

    i: Image = ImageLib.new('RGBA', (
        (len(longest) * img_size) + (x_offset * (len(longest) - 1)) +  # x
        x_offset + get_text_dimensions(longest_name)[0] + x_offset,  # x
        (4 * img_size) + (3 * y_offset) +  # y
        y_offset + (len(food) * half_img_size) + (y_offset * (len(food) - 1))
    ))

    draw: ImageDraw = ImageDraw.Draw(i)
    card: int
    y: int
    unit: Unit
    for card, y in [(card1, 0), (card2, img_size + y_offset),
                    (card3, (img_size * 2) + (y_offset * 2)),
                    (card4, (img_size * 3) + (y_offset * 3))]:
        x: int = x_offset + get_text_dimensions(longest_name)[0] + x_offset
        text_with_shadow(draw, tarot_name(card), (x_offset, y + int(img_size / 2)))
        for unit in [unit_by_id(x) for x in tarot_units[card]]:
            i.paste(await unit.set_icon(), (x, y))
            x += img_size + x_offset

    y: int = (4 * img_size) + (4 * y_offset)
    _food: Food
    food_icon: Image
    for _food in food:
        x = x_offset + get_text_dimensions(_food.name)[0] + x_offset + x_offset
        text_with_shadow(draw, _food.name,
                         (x_offset, y + int(half_img_size / 2) - int(get_text_dimensions(_food.name)[1] / 2)))
        for food_icon in _food.icons:
            i.paste(food_icon, (x, y))
            x += half_img_size + x_offset + x_offset
        y += half_img_size + y_offset

    return i


async def compose_draftable_units(draft_units: List[Unit], size: int = 10) -> Image:
    rows: List[List[Unit]] = list(chunks(draft_units, size))

    i: Image = ImageLib.new('RGBA', (
        (img_size * size) + (x_offset * (size - 1)),
        (img_size * len(rows)) + (y_offset * len(rows))
    ))

    y: int = 0
    for row in rows:
        x = 0
        for unit in row:
            i.paste(await unit.set_icon(), (x, y))
            x += x_offset + img_size
        y += y_offset + img_size

    return i


async def compose_drafted_units(drafted_units: Dict[discord.Member, List[Unit]], row_len: int = 12) -> Image:
    dim: Tuple[int, int] = get_text_dimensions("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    i: Image = ImageLib.new('RGBA', (
        (img_size * row_len) + (x_offset * row_len - 1) + x_offset + dim[0],
        (img_size * len(drafted_units) + (y_offset * (len(drafted_units) - 1)))
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    for row in drafted_units:
        x = get_text_dimensions(row.display_name)
        for unit in drafted_units[row]:
            text_with_shadow(draw, row.display_name, (0, y))
            i.paste(await unit.set_icon(), (x, y))
            x += x_offset + img_size
        y += y_offset + img_size

    return i


async def compose_draft_trade(wanted: Unit, give: Unit) -> Image:
    i: Image = ImageLib.new('RGBA', (
        (img_size * 2) + x_offset + trade_dim[0] + x_offset,
        img_size
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    i.paste(await give.set_icon(), (0, 0))
    text_with_shadow(draw, ">", (img_size + x_offset, int(img_size / 2)))
    i.paste(await wanted.set_icon(), (img_size + x_offset + trade_dim[0] + x_offset, 0))

    return i


async def compose_random_select_team(possible: List[Unit]) -> Image:
    rows: List[List[Unit]] = list(chunks(possible, 4))

    i: Image = ImageLib.new('RGBA', (
        x_offset + TEAM_DIM[0] + x_offset + (img_size * 4) + (x_offset * 3),
        (img_size * len(rows)) + (y_offset * (len(rows) - 1))
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
                         xy=(5, y + int(img_size / 2)))
        x: int = x_offset + TEAM_DIM[0] + x_offset
        for _unit in row:
            i.paste(_unit.icon, (x, y))
            x += img_size + 5
        draw.line([(0, y + img_size + 3), (i.size[0], y + img_size + 3)], width=3)
        y += img_size + 9

    return i


async def compose_awakening(materials: dict) -> Image:
    i: Image = ImageLib.new('RGBA', (
        img_size + x_offset + get_text_dimensions("15")[0],
        (img_size * len(materials)) + (y_offset * (len(materials) - 1))
    ))
    draw: ImageDraw = ImageDraw.Draw(i)

    y: int = 0
    for material in materials:
        _text_with_shadow(draw,
                          x=x_offset,
                          y=y + int(img_size / 2),
                          text=str(materials[material]) + "x")
        x: int = x_offset + get_text_dimensions(str(materials[material]) + "x")[0] + x_offset
        i.paste(material.icon, (x, y))
        y += img_size + y_offset

    return i
