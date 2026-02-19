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
        'minions': 1,
        'demons': 1,
        'townsfolk': 3,
        'outsiders': 0
    },
    6: {
        'minions': 1,
        'demons': 1,
        'townsfolk': 3,
        'outsiders': 1
    },
    13: {
        'minions': 3,
        'demons': 1,
        'townsfolk': 9,
        'outsiders': 0
    }
}

EVIL_CHARACTERS = [Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN, Role.IMP]
GOOD_CHARACTERS = [
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR, Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK
]
MINIONS = [Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN]
TOWNSFOLK = [
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR
]
OUTSIDERS = [Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK]
DEMONS = [Role.IMP]
ALL_CHARACTERS = GOOD_CHARACTERS + EVIL_CHARACTERS
EVIL_ROLES = EVIL_CHARACTERS + [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]
GOOD_ROLES = GOOD_CHARACTERS + [Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_OUTSIDER]
ANY_OTHER_ROLES = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.ANY_OTHER_OUTSIDER, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON]

CHARACTER_STRINGS = {
    Role.ANY_OTHER: "any other character",
    Role.ANY_OTHER_EVIL: "any other Evil character",
    Role.ANY_OTHER_GOOD: "any other Good character",
    Role.ANY_OTHER_MINION: "any other minion",
    Role.NON_DEMON: "any non demon character",
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