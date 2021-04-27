from typing import Dict, List, Any

tarot_units: Dict[int, List[int]] = {
    1: [5, 158, 147, 122, 163, 135, 144, 138, 14, 2, 82, 97, 121, 127, 81, 36, 27, 41, 58, 32, 25, 88, 45, 42, 37, 174],
    2: [8, 156, 170, 63, 62, 66],
    3: [146, 61, 4, 90, 68, 60, 64],
    4: [74, 119, 102, 67, 83, 46],
    5: [106, 16, 163, 166],
    6: [103, 99, 59, 139, 84, 35, 57, 176],
    7: [142, 15, 112, 38, 33, 20, 180],
    8: [131, 100, 91, 17, 6, 117, 18, 87, 155, 171],
    9: [164, 69, 80, 94, 3, 98, 55],
    10: [105, 72, 89, 153, 49, 43, 22, 31, 23, 39, 44, 52, 54, 173],
    11: [124, 70, 159, 95, 75],
    12: [101, 71, 154, 120, 126, 177],
    13: [104, 13, 1, 77, 133, 141],
    14: [140, 86, 12, 110, 78, 129, 123, 65],
    15: [150, 7, 149, 168, 93, 118, 30, 96],
    16: [111, 11, 143, 10, 161, 92, 28, 53, 51, 162],
    17: [85, 73, 125, 115, 130, 21, 178],
    18: [134, 132, 34, 128],
    19: [136, 108],
    20: [160, 79, 19, 109, 114, 113, 9, 47, 76, 107, 172, 175],
    21: [145, 152, 151],
    22: [116, 148, 137, 157, 169, 165, 179]
}
tarot_food: Dict[int, Any] = {
    1: [],
    2: [],
    3: [],
    4: []
}


def tarot_name(num: int) -> str:
    if num == 1:
        return "1) The Fool"
    if num == 2:
        return "2) The Magician"
    if num == 3:
        return "3) The High Priestess"
    if num == 4:
        return "4) The Empress"
    if num == 5:
        return "5) The Emperor"
    if num == 6:
        return "6) The Hierophant"
    if num == 7:
        return "7) The Lovers"
    if num == 8:
        return "8) The Chariot"
    if num == 9:
        return "9) Strength"
    if num == 10:
        return "10) The Hermit"
    if num == 11:
        return "11) Wheel of Fortune"
    if num == 12:
        return "12) Justice"
    if num == 13:
        return "13) The Hanged Man"
    if num == 14:
        return "14) Death"
    if num == 15:
        return "15) Temperance"
    if num == 16:
        return "16) The Devil"
    if num == 17:
        return "17) The Tower"
    if num == 18:
        return "18) The Star"
    if num == 19:
        return "19) The Moon"
    if num == 20:
        return "20) The Sun"
    if num == 21:
        return "21) Judgement"
    if num == 22:
        return "22) The World"
