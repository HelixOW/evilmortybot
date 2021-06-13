from PIL import Image
import pytesseract
import re

# pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/4.1.1/bin/tesseract'


async def read_base_cc_from_image(ctx, image: Image.Image) -> float:
    text = pytesseract.image_to_string(image.resize((1242, 2688), resample=Image.BOX), config="-psm 1")

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
    text = pytesseract.image_to_string(im, config='')

    if "Knighthood" not in text:
        return -1

    result = re.search(r'(.*)([ce]?)([ce]?):\s?([\d,]{1,8})', text)

    if result is None:
        return 0

    return float(result.group(4).replace(",", ".").replace(" ", ""))