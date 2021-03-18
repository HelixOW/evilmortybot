TAROT_UNITS = {
    1: [5, 158, 147, 122, 163, 135, 144, 138, 14, 2, 82, 97, 121, 127, 81, 36, 27, 41, 58, 32, 25, 88, 45, 42, 37],
    2: [8, 156, 170, 63, 62, 66],
    3: [146, 61, 4, 90, 68, 60, 64],
    4: [74, 119, 102, 67, 83, 46],
    5: [106, 16, 163],
    6: [103, 99, 59, 139, 84, 35, 57],
    7: [164, 142, 15, 112, 38, 33, 20],
    8: [131, 100, 91, 17, 6, 117, 18, 87, 155],
    9: [69, 80, 94, 3, 98, 55],
    10: [105, 72, 89, 153, 49, 43, 22, 31, 23, 39, 44, 52, 54],
    11: [124, 70, 159, 95, 75],
    12: [101, 71, 154, 120, 126],
    13: [104, 13, 1, 77, 133, 141],
    14: [140, 86, 12, 110, 78, 129, 123, 65],
    15: [150, 7, 149, 168, 93, 118, 30, 96],
    16: [111, 11, 143, 10, 161, 92, 28, 53, 51],
    17: [85, 73, 125, 115, 130, 21],
    18: [134, 132, 34, 128],
    19: [136, 108],
    20: [160, 79, 19, 109, 114, 113, 9, 47, 76, 107],
    21: [145, 152, 151],
    22: [116, 148, 137, 157, 169, 165]
}
TAROT_FOOD = {
    1: [],
    2: [],
    3: [],
    4: []
}


def tarot_name(num: int):
    if num == 1:
        return "1) The Fool"
    elif num == 2:
        return "2) The Magician"
    elif num == 3:
        return "3) The High Priestess"
    elif num == 4:
        return "4) The Empress"
    elif num == 5:
        return "5) The Emperor"
    elif num == 6:
        return "6) The Hierophant"
    elif num == 7:
        return "7) The Lovers"
    elif num == 8:
        return "8) The Chariot"
    elif num == 9:
        return "9) Strength"
    elif num == 10:
        return "10) The Hermit"
    elif num == 11:
        return "11) Wheel of Fortune"
    elif num == 12:
        return "12) Justice"
    elif num == 13:
        return "13) The Hanged Man"
    elif num == 14:
        return "14) Death"
    elif num == 15:
        return "15) Temperance"
    elif num == 16:
        return "16) The Devil"
    elif num == 17:
        return "17) The Tower"
    elif num == 18:
        return "18) The Star"
    elif num == 19:
        return "19) The Moon"
    elif num == 20:
        return "20) The Sun"
    elif num == 21:
        return "21) Judgement"
    elif num == 22:
        return "22) The World"
