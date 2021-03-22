from utilities import *
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/Cellar/tesseract/4.1.1/bin/tesseract'


async def read_base_cc_from_image(image: Image.Image) -> float:
    text = pytesseract.image_to_string(image)

    result = re.search(r'(.*)Team (.?)(.?): ([\d,]{1,7})', text)

    if result is None:
        return -1

    return float(result.group(4).replace(",", "."))


async def read_kh_cc_from_image(image: Image.Image) -> float:
    text = pytesseract.image_to_string(image.resize((830, 1800)))

    if "Registered Combat Class:" not in text:
        return -1

    result = re.search(r'(.*)Registered (.*)(.*): ([\d,]{1,7})', text)

    if result is None:
        return 0

    return float(result.group(4).replace(",", "."))
