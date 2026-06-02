from enum import Enum, auto

class Role(Enum):
    WASHERWOMAN = auto()
    LIBRARIAN = auto()
    INVESTIGATOR = auto()
    CHEF = auto()
    EMPATH = auto()
    FORTUNE_TELLER = auto()
    UNDERTAKER = auto()
    MONK = auto()
    RAVENKEEPER = auto()
    VIRGIN = auto()
    SLAYER = auto()
    SOLDIER = auto()
    MAYOR = auto()
    BUTLER = auto()
    SAINT = auto()
    RECLUSE = auto()
    DRUNK = auto()
    POISONER = auto()
    SPY = auto()
    BARON = auto()
    SCARLET_WOMAN = auto()
    IMP = auto()
    ANY_OTHER_TOWNSFOLK = auto()
    ANY_OTHER_OUTSIDER = auto()
    ANY_OTHER_MINION = auto()
    ANY_OTHER_GOOD = auto()
    ANY_OTHER_EVIL = auto()
    NON_DEMON = auto()
    ANY_OTHER = auto()

ROLE_BREAKDOWNS = {
    5: {
        'townsfolk': 3,
        'outsiders': 0,
        'minions': 1,
        'demons': 1,
    },
    6: {
        'townsfolk': 3,
        'outsiders': 1,
        'minions': 1,
        'demons': 1,
    },
    7: {
        'townsfolk': 5,
        'outsiders': 0,
        'minions': 1,
        'demons': 1,
    },
    8: {
        'townsfolk': 5,
        'outsiders': 1,
        'minions': 1,
        'demons': 1,
    },
    9: {
        'townsfolk': 5,
        'outsiders': 2,
        'minions': 1,
        'demons': 1,
    },
    10: {
        'townsfolk': 7,
        'outsiders': 0,
        'minions': 2,
        'demons': 1,
    },
    11: {
        'townsfolk': 7,
        'outsiders': 1,
        'minions': 2,
        'demons': 1,
    },
    12: {
        'townsfolk': 7,
        'outsiders': 2,
        'minions': 2,
        'demons': 1,
    },
    13: {
        'townsfolk': 9,
        'outsiders': 0,
        'minions': 3,
        'demons': 1,
    },
    14: {
        'townsfolk': 9,
        'outsiders': 1,
        'minions': 3,
        'demons': 1,
    },
    15: {
        'townsfolk': 9,
        'outsiders': 2,
        'minions': 3,
        'demons': 1,
    },
}

EVIL_CHARACTERS = [Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN, Role.IMP]
EVIL_CHARACTERS_SET = set(EVIL_CHARACTERS)
GOOD_CHARACTERS = [
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR, Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK
]
GOOD_CHARACTERS_SET = set(GOOD_CHARACTERS)
MINIONS = [Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN]
MINIONS_SET = set(MINIONS)
TOWNSFOLK = [
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR
]
TOWNSFOLK_SET = set(TOWNSFOLK)
OUTSIDERS = [Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK]
OUTSIDERS_SET = set(OUTSIDERS)
DEMONS = [Role.IMP]
ALL_CHARACTERS = GOOD_CHARACTERS + EVIL_CHARACTERS
EVIL_ROLES = EVIL_CHARACTERS + [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]
EVIL_ROLES_SET = set(EVIL_ROLES)
GOOD_ROLES = GOOD_CHARACTERS + [Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_OUTSIDER]
GOOD_ROLES_SET = set(GOOD_ROLES)
ANY_OTHER_ROLES = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.ANY_OTHER_OUTSIDER, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON]
ANY_OTHER_ROLES_SET = set(ANY_OTHER_ROLES)

CHARACTER_STRINGS = {
    Role.ANY_OTHER: "Unknown",
    Role.ANY_OTHER_EVIL: "Unknown Evil",
    Role.ANY_OTHER_GOOD: "Unknown Good",
    Role.ANY_OTHER_MINION: "Unknown Minion",
    Role.ANY_OTHER_TOWNSFOLK: "Unknown Townsfolk",
    Role.ANY_OTHER_OUTSIDER: "Unknown Outsider",
    Role.NON_DEMON: "Non Demon",
    Role.WASHERWOMAN: "Washerwoman", 
    Role.LIBRARIAN: "Librarian", 
    Role.INVESTIGATOR: "Investigator", 
    Role.CHEF: "Chef", 
    Role.EMPATH: "Empath", 
    Role.FORTUNE_TELLER: "Fortune Teller", 
    Role.UNDERTAKER: "Undertaker", 
    Role.MONK: "Monk", 
    Role.RAVENKEEPER: "Ravenkeeper", 
    Role.VIRGIN: "Virgin", 
    Role.SLAYER: "Slayer", 
    Role.SOLDIER: "Soldier", 
    Role.MAYOR: "Mayor", 
    Role.BUTLER: "Butler", 
    Role.SAINT: "Saint", 
    Role.RECLUSE: "Recluse", 
    Role.DRUNK: "Drunk", 
    Role.POISONER: "Poisoner", 
    Role.SPY: "Spy", 
    Role.BARON: "Baron", 
    Role.SCARLET_WOMAN: "Scarlet Woman", 
    Role.IMP: "Imp"
}