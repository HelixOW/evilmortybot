from utilities import *
from utilities.unit_data import Unit, unit_by_id
from utilities.banner_data import Banner
from utilities.sql_helper import connection, unit_with_chance
from utilities.tarot import *


FONT_24 = ImageFont.truetype("pvp.ttf", 24)


def get_text_dimensions(text_string, font=FONT_24):
    _, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height


def text_with_shadow(draw: ImageDraw, text: str, base_xy):
    font = ImageFont.truetype("pvp.ttf", 24)
    draw.text(
        xy=(base_xy[0] + 1, base_xy[1]),
        text=text,
        fill=(0, 0, 0),
        font=font
    )
    draw.text(
        xy=(base_xy[0], base_xy[1] + 1),
        text=text,
        fill=(0, 0, 0),
        font=font
    )
    draw.text(
        xy=(base_xy[0] + 1, base_xy[1] + 1),
        text=text,
        fill=(0, 0, 0),
        font=font
    )
    draw.text(
        xy=(base_xy[0], base_xy[1]),
        text=text,
        fill=(255, 255, 255),
        font=font
    )


async def compose_team(rerolled_team: List[Unit], re_units=None) -> Image:
    if re_units is None:
        re_units = {0: [], 1: [], 2: [], 3: []}

    icons = [x.resize([IMG_SIZE, IMG_SIZE]) for x in [i.icon for i in rerolled_team]]

    if re_units[0] == 0 and re_units[1] == 0 and re_units[2] == 0 and re_units[3] == 0:
        img = Image.new('RGBA', ((IMG_SIZE * 4) + 6, IMG_SIZE))
        x_offset = 0
        for icon in icons:
            img.paste(icon, (x_offset, 0))
            x_offset += icon.size[0] + 2

        return img

    font = ImageFont.truetype("pvp.ttf", 12)
    dummy_height = get_text_dimensions("[Dummy] Bot", font)[1]
    all_re_units_len = 0
    for i in re_units:
        all_re_units_len += len(re_units[i])
    img = Image.new('RGBA', ((IMG_SIZE * 4) + 6,
                             IMG_SIZE + ((5 + dummy_height) * all_re_units_len)
                             ))
    img_draw = ImageDraw.Draw(img)
    x_offset = 0
    for icon in icons:
        img.paste(icon, (x_offset, img.size[1] - IMG_SIZE))
        x_offset += icon.size[0] + 2

    pointer = 0
    for re_unit_index in re_units:
        for i in range(len(re_units[re_unit_index])):
            img_draw.text(
                xy=((IMG_SIZE * re_unit_index) + (re_unit_index * 2), (5 + dummy_height) * pointer),
                text=re_units[re_unit_index][i].name,
                fill=(255, 255, 255),
                font=font
            )
            pointer += 1

    return img


async def compose_pvp_with_images(player1: discord.Member, team1_img: Image, player2: discord.Member,
                                  team2_img: Image) -> Image:
    font = ImageFont.truetype("pvp.ttf", 30)
    font_dim = get_text_dimensions("vs", font)
    pvp_img = Image.new('RGBA', (team1_img.size[0] + 5 + font_dim[0] + 5 + team2_img.size[0],
                                 IMG_SIZE + font_dim[1] + 5))
    pvp_img_draw = ImageDraw.Draw(pvp_img)

    pvp_img.paste(team1_img, (0, font_dim[1] + 5))

    pvp_img_draw.text(
        xy=(pvp_img.size[0] / 2 - (font_dim[0] / 2), (IMG_SIZE / 2) + 20),
        text="vs",
        fill=(255, 255, 255),
        font=font
    )

    pvp_img.paste(team2_img, (pvp_img.size[0] - team2_img.size[0], font_dim[1] + 5))

    pvp_img_draw.text(
        xy=(0, 0),
        text=f"{player1.display_name}",
        fill=(255, 255, 255),
        font=font
    )
    pvp_img_draw.text(
        xy=(pvp_img.size[0] - get_text_dimensions(f"{player2.display_name}", font)[0], 0),
        text=f"{player2.display_name}",
        fill=(255, 255, 255),
        font=font
    )

    return pvp_img


async def compose_pvp(player1: discord.Member, team1: List[Unit], player2: discord.Member, team2: List[Unit]) -> Image:
    left_icons = [x.resize([IMG_SIZE, IMG_SIZE]) for x in [i.icon for i in team1]]
    right_icons = [x.resize([IMG_SIZE, IMG_SIZE]) for x in [i.icon for i in team2]]
    right_team_img = Image.new('RGBA', (IMG_SIZE * 4 + 4, IMG_SIZE))
    left_team_img = Image.new('RGBA', (IMG_SIZE * 4 + 4, IMG_SIZE))

    x_offset = 0
    for icon in left_icons:
        left_team_img.paste(icon, (x_offset, 0))
        x_offset += icon.size[0] + 2

    x_offset = 0
    for icon in right_icons:
        right_team_img.paste(icon, (x_offset, 0))
        x_offset += icon.size[0] + 2

    return await compose_pvp_with_images(player1=player1, team1_img=left_team_img, player2=player2,
                                         team2_img=right_team_img)


async def compose_draw(from_banner: Banner, user: discord.Member) -> discord.File:
    u = await unit_with_chance(from_banner, user)
    connection.commit()
    return await u.discord_icon()


async def compose_five_multi_draw(from_banner: Banner, user: discord.Member) -> Image:
    u = await compose_unit_five_multi_draw([(await unit_with_chance(from_banner, user)) for _ in range(5)])
    connection.commit()
    return u


async def compose_multi_draw(from_banner: Banner, user: discord.Member) -> Image:
    u = await compose_unit_multi_draw([(await unit_with_chance(from_banner, user)) for _ in range(11)])
    connection.commit()
    return u


async def compose_unit_five_multi_draw(units: List[Unit]) -> Image:
    image_row_1 = [units[0].icon, units[1].icon, units[2].icon]
    image_row_2 = [units[3].icon, units[4].icon]

    complete_offset = 5
    i = Image.new('RGBA', ((IMG_SIZE * 3) + 10, (IMG_SIZE * 2) + 5))

    x_offset = 0
    for icon in image_row_1:
        i.paste(icon, (x_offset, 0))
        x_offset += icon.size[0] + complete_offset

    x_offset = int((((IMG_SIZE * 3) + 10) - IMG_SIZE * 2) / 2)
    for icon in image_row_2:
        i.paste(icon, (x_offset, icon.size[1] + complete_offset))
        x_offset += icon.size[0] + complete_offset

    return i


async def compose_banner_rotation(units) -> Image:
    pull_rows = list(chunks_dict(units, 5))

    i = Image.new('RGBA', (
        (IMG_SIZE * 5) + (5 * 4),  # x
        ((IMG_SIZE * len(pull_rows)) + (5 * (len(pull_rows) - 1)))  # y
    ))
    draw = ImageDraw.Draw(i)

    y_offset = 0
    for _units in pull_rows:
        x_offset = 0
        for key in _units:
            await key.set_icon()
            i.paste(key.icon, (x_offset, y_offset))
            text_with_shadow(draw, str(_units[key]), (x_offset + 10, y_offset + 10))
            x_offset += IMG_SIZE + 5
        y_offset += IMG_SIZE + 5

    return i


async def compose_unit_multi_draw(units: List[Unit], ssrs=None) -> Image:
    if ssrs is None:
        ssrs = {}

    pull_rows = list(chunks(units, 4))
    ssr_rows = list(chunks_dict(ssrs, 4))
    font = ImageFont.truetype("pvp.ttf", 24)
    text_dim = get_text_dimensions("All SSRs you got:", font=font)

    complete_offset = 5

    i = Image.new('RGBA', (
        (IMG_SIZE * 4) + (complete_offset * 3),  # x
        (
                ((IMG_SIZE * 3) + (complete_offset * 2)) +  # y of last pull
                (((IMG_SIZE * len(ssr_rows)) + (complete_offset * (len(ssr_rows) - 1))) if len(ssr_rows) != 0 else 0) +  # y of all ssrs
                ((text_dim[1] + 15) if len(ssrs) != 0 else 0)  # y of text and spacing for top and bottom
        )
    ))
    draw = ImageDraw.Draw(i)

    y_offset = 0
    for _units in pull_rows:
        x_offset = 0
        for _unit in _units:
            await _unit.set_icon()
            i.paste(_unit.icon, (x_offset, y_offset))
            x_offset += IMG_SIZE + complete_offset
        y_offset += IMG_SIZE + complete_offset

    if len(ssrs) == 0:
        return i

    draw.text(
        xy=(0, y_offset + 5),
        text="All SSRs you got:",
        fill=(255, 255, 255),
        font=font
    )
    y_offset += text_dim[1] + 10

    for ssr_dict in ssr_rows:
        x_offset = 0
        for key in ssr_dict:
            await key.set_icon()
            i.paste(key.icon, (x_offset, y_offset))
            text_with_shadow(draw, str(ssr_dict[key]), (x_offset + 10, y_offset + 10))
            x_offset += IMG_SIZE + complete_offset
        y_offset += IMG_SIZE + complete_offset

    return i


async def compose_box(units_dict: dict) -> Image:
    box_rows = list(chunks(list(units_dict.keys()), 5))

    i = Image.new('RGBA', (
        (IMG_SIZE * 5) + (4 * 5),
        (IMG_SIZE * len(box_rows)) + (5 * (len(box_rows) - 1))
    ))
    draw = ImageDraw.Draw(i)

    y_offset = 0
    for unit_ids in box_rows:
        x_offset = 0
        for unit_id in unit_ids:
            box_unit = unit_by_id(unit_id)
            await box_unit.set_icon()
            i.paste(box_unit.icon, (x_offset, y_offset))
            text_with_shadow(draw, str(units_dict[unit_id]), (x_offset + 5, y_offset + 10))
            x_offset += IMG_SIZE + 5
        y_offset += IMG_SIZE + 5

    return i


async def compose_paged_unit_list(cus_units: List[Unit], per_page: int) -> List[typing.Any]:
    return [await compose_unit_list(list(chunks(cus_units, per_page))[i])
            for i in range(math.ceil(len(cus_units) / per_page))]


async def compose_unit_list(cus_units: List[Unit]) -> Image:
    font = ImageFont.truetype("pvp.ttf", 24)
    text_dim = get_text_dimensions(sorted(cus_units, key=lambda k: len(k.name), reverse=True)[0].name + " (Nr. 999)",
                                   font=font)
    i = Image.new('RGBA', (IMG_SIZE + text_dim[0] + 5, (IMG_SIZE * len(cus_units)) + (5 * len(cus_units))))
    draw = ImageDraw.Draw(i)

    offset = 0
    for cus_unit in cus_units:
        await cus_unit.set_icon()
        i.paste(cus_unit.icon, (0, offset))
        draw.text(
            xy=(5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
            text=cus_unit.name + f" (Nr. {cus_unit.unit_id})",
            fill=(255, 255, 255),
            font=font
        )
        offset += IMG_SIZE + 5

    return i


async def compose_banner_list(b: Banner, include_all: bool = False) -> Image:
    font = ImageFont.truetype("pvp.ttf", 24)
    if len(b.ssr_units + b.rate_up_units) == 0:
        return Image.new('RGBA', (0, 0))
    text_dim = get_text_dimensions(
        sorted(b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else []),
               key=lambda k: len(k.name), reverse=True)[0].name + " - 0.9999%",
        font=font)
    i = Image.new('RGBA', (IMG_SIZE + text_dim[0] + 5,
                           (IMG_SIZE * len(
                               b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else [])))
                           + (5 * len(
                               b.ssr_units + b.rate_up_units + ((b.sr_units + b.r_units) if include_all else [])))))
    draw = ImageDraw.Draw(i)

    offset = 0
    for rated_unit in b.rate_up_units:
        await rated_unit.set_icon()
        i.paste(rated_unit.icon, (0, offset))
        draw.text(
            xy=(5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
            text=f"{rated_unit.name} - {b.ssr_unit_rate_up}%",
            fill=(255, 255, 255),
            font=font
        )
        offset += IMG_SIZE + 5
    for cus_unit in b.ssr_units:
        await cus_unit.set_icon()
        i.paste(cus_unit.icon, (0, offset))
        draw.text(
            xy=(5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
            text=f"{cus_unit.name} - {b.ssr_unit_rate}%",
            fill=(255, 255, 255),
            font=font)
        offset += IMG_SIZE + 5
    if include_all:
        for cus_unit in b.sr_units:
            await cus_unit.set_icon()
            i.paste(cus_unit.icon, (0, offset))
            draw.text(
                xy=(5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
                text=f"{cus_unit.name} - {b.sr_unit_rate}%",
                fill=(255, 255, 255),
                font=font)
            offset += IMG_SIZE + 5
        for cus_unit in b.r_units:
            await cus_unit.set_icon()
            i.paste(cus_unit.icon, (0, offset))
            draw.text(
                xy=(5 + IMG_SIZE, offset + (IMG_SIZE / 2) - (text_dim[1] / 2)),
                text=f"{cus_unit.name} - {b.r_unit_rate}%",
                fill=(255, 255, 255),
                font=font)
            offset += IMG_SIZE + 5

    return i


async def compose_tarot(card1: int, card2: int, card3: int, card4: int, food: int):
    food = TAROT_FOOD[food]

    longest = sorted([[unit_by_id(x) for x in TAROT_UNITS[card1]],
                      [unit_by_id(x) for x in TAROT_UNITS[card2]],
                      [unit_by_id(x) for x in TAROT_UNITS[card3]],
                      [unit_by_id(x) for x in TAROT_UNITS[card4]]], key=lambda k: len(k), reverse=True)[0]
    longest_name = sorted([tarot_name(x) for x in [card1, card2, card3, card4]], key=lambda k: len(k), reverse=True)[0]
    standard_x_offset = 5
    standard_y_offset = 9

    i = Image.new('RGBA', (
        (len(longest) * IMG_SIZE) + (standard_x_offset * (len(longest) - 1)) +  # x
        standard_x_offset + get_text_dimensions(longest_name)[0] + standard_x_offset,  # x
        (4 * IMG_SIZE) + (3 * standard_y_offset) +  # y
        standard_y_offset + (len(food) * FOOD_SIZE) + (standard_y_offset * (len(food) - 1))
    ))

    draw = ImageDraw.Draw(i)

    for card, y in [(card1, 0), (card2, IMG_SIZE + standard_y_offset),
                    (card3, (IMG_SIZE * 2) + (standard_y_offset * 2)),
                    (card4, (IMG_SIZE * 3) + (standard_y_offset * 3))]:
        offset = standard_x_offset + get_text_dimensions(longest_name)[0] + standard_x_offset
        text_with_shadow(draw, tarot_name(card), (standard_x_offset, y + (IMG_SIZE / 2)))
        for unit in [unit_by_id(x) for x in TAROT_UNITS[card]]:
            i.paste(await unit.set_icon(), (offset, y))
            offset += IMG_SIZE + standard_x_offset

    y_offset = (4 * IMG_SIZE) + (4 * standard_y_offset)

    for _food in food:
        offset = standard_x_offset + get_text_dimensions(_food.name)[0] + standard_x_offset + standard_x_offset
        text_with_shadow(draw, _food.name, (standard_x_offset, y_offset + (FOOD_SIZE / 2) - (get_text_dimensions(_food.name)[1] / 2)))
        for food_icon in _food.icons:
            i.paste(food_icon, (offset, y_offset))
            offset += FOOD_SIZE + standard_x_offset + standard_x_offset
        y_offset += FOOD_SIZE + standard_y_offset

    return i
