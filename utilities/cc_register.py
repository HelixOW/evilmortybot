from PIL import Image, ImageFilter
import pytesseract
import re
from utilities.units import image_to_discord

# pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/4.1.1/bin/tesseract'


async def read_base_cc_from_image(ctx, image: Image.Image) -> float:
    # await ctx.send(file=await image_to_discord(image.resize((1242, 2688), resample=Image.BOX)))
    text = pytesseract.image_to_string(image.resize((1242, 2688), resample=Image.BOX), config="-psm 1")

    # await ctx.send("```{text}```")

    result = re.search(r'(.*)Team (.?)(.?): ([\d,]{1,7})', text)

    if result is None:
        return -1

    return float(result.group(4).replace(",", "."))


async def read_kh_cc_from_image(ctx, image: Image.Image) -> float:
    if image.size[0] > image.size[1]:
        im = image
        thresh = 175
    else:
        im = image
        thresh = 180
    im = im.convert('L').point(
        lambda x: 255 if x > thresh else 0, mode='1')
    # await ctx.send(file=await image_to_discord(im))
    text = pytesseract.image_to_string(im, config='')

    # await ctx.send("```{text}```")

    if "Knighthood" not in text:
        return -1

    result = re.search(r'(.*)([ce]?)([ce]?):\s?([\d,]{1,8})', text)

    if result is None:
        return 0

    return float(result.group(4).replace(",", ".").replace(" ", ""))