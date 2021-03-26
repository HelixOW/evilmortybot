from utilities import *
from utilities.unit_data import Type, Unit, Affection, Grade

COSTS = {
    "gold": {
        1: 100,
        2: 120,
        3: 160,
        4: 220,
        5: 300,
        6: 400
    },
    Type.BLUE: {
        1: {
            find_material(3): 2,
            find_material(4): 3,
            find_material(5): 5
        },
        2: {
            find_material(9): 2,
            find_material(10): 3,
            find_material(11): 5
        },
        3: {
            find_material(15): 4,
            find_material(16): 6,
            find_material(17): 10
        },
        4: {
            find_material(21): 4,
            find_material(22): 6,
            find_material(23): 10
        },
        5: {
            find_material(27): 6,
            find_material(28): 9,
            find_material(29): 15
        },
        6: {
            find_material(33): 6,
            find_material(34): 9,
            find_material(35): 15
        }
    },
    Type.RED: {
        1: {
            find_material(6): 2,
            find_material(5): 3,
            find_material(7): 5
        },
        2: {
            find_material(12): 2,
            find_material(11): 3,
            find_material(13): 5
        },
        3: {
            find_material(18): 4,
            find_material(17): 6,
            find_material(19): 10
        },
        4: {
            find_material(24): 4,
            find_material(23): 6,
            find_material(25): 10
        },
        5: {
            find_material(30): 6,
            find_material(29): 9,
            find_material(31): 15
        },
        6: {
            find_material(36): 6,
            find_material(35): 9,
            find_material(37): 15
        }
    },
    Type.GRE: {
        1: {
            find_material(8): 2,
            find_material(7): 3,
            find_material(4): 5
        },
        2: {
            find_material(14): 2,
            find_material(13): 3,
            find_material(10): 5
        },
        3: {
            find_material(20): 4,
            find_material(19): 6,
            find_material(16): 10
        },
        4: {
            find_material(26): 4,
            find_material(25): 6,
            find_material(22): 10
        },
        5: {
            find_material(32): 6,
            find_material(31): 9,
            find_material(28): 15
        },
        6: {
            find_material(38): 6,
            find_material(37): 9,
            find_material(34): 15
        }
    }
}


def calc_cost(u: Unit, start: int, end: int):
    blood_amount: int = (3 if u.grade == Grade.SSR else 2 if u.grade == Grade.SR else 1)

    if u.affection == Affection.SIN:
        total_costs = {
            find_material(100 + i): blood_amount for i in range(start, end)
        }
    else:
        total_costs = {
            find_material(200 + i): blood_amount for i in range(start, end)
        }
    for between in range(start, end):
        for mats in COSTS[u.type][between]:
            if mats in total_costs:
                total_costs[mats] += COSTS[u.type][between][mats]
            else:
                total_costs[mats] = COSTS[u.type][between][mats]

    return total_costs
