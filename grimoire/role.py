from enum import IntEnum, auto

class Role(IntEnum):
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
ROLE_CATEGORIES = [Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_OUTSIDER, Role.ANY_OTHER_MINION, Role.IMP]

def get_overlapping(c1: Role, c2: Role, specific: bool) -> Role | None:
    if c1 == c2:
        return c1
    if c1 not in ANY_OTHER_ROLES:
        return _get_overlapping_character(c1, c2, specific)
    if c1 == Role.ANY_OTHER_EVIL:
        return _get_overlapping_evil(c2, specific)
    if c1 == Role.ANY_OTHER_GOOD:
        return _get_overlapping_good(c2, specific)
    if c1 == Role.ANY_OTHER_MINION:
        return _get_overlapping_minion(c2, specific)
    if c1 == Role.ANY_OTHER_TOWNSFOLK:
        return _get_overlapping_townsfolk(c2, specific)
    if c1 == Role.ANY_OTHER_OUTSIDER:
        return _get_overlapping_outsider(c2, specific)
    if c1 == Role.NON_DEMON:
        return _get_overlapping_non_demon(c2, specific)
    if c1 == Role.ANY_OTHER:
        return _get_overlapping_other(c2, specific)
    return None

def _get_overlapping_character(character: Role, c2: Role, specific: bool) -> Role | None:
    if c2 not in ANY_OTHER_ROLES and c2 != character:
        return None
    if c2 == Role.ANY_OTHER_EVIL and character in EVIL_CHARACTERS:
        return character if specific else c2
    if c2 == Role.ANY_OTHER_GOOD and character in GOOD_CHARACTERS:
        return character if specific else c2
    if c2 == Role.ANY_OTHER_MINION and character in MINIONS:
        return character if specific else c2
    if c2 == Role.ANY_OTHER_OUTSIDER and character in OUTSIDERS:
        return character if specific else c2
    if c2 == Role.ANY_OTHER_TOWNSFOLK and character in TOWNSFOLK:
        return character if specific else c2
    if c2 == Role.NON_DEMON and character != Role.IMP:
        return character if specific else c2
    if c2 == Role.ANY_OTHER:
        return character if specific else c2
    return None

def _get_overlapping_evil(c2: Role, specific: bool) -> Role | None:
    if c2 == Role.ANY_OTHER:
        return Role.ANY_OTHER_EVIL if specific else c2
    if c2 == Role.ANY_OTHER_GOOD:
        return None
    if c2 == Role.ANY_OTHER_MINION:
        return c2 if specific else Role.ANY_OTHER_EVIL
    if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
        return None
    if c2 == Role.NON_DEMON:
        return Role.ANY_OTHER_MINION if specific else Role.ANY_OTHER_EVIL
    if c2 not in EVIL_CHARACTERS:
        return None
    if c2 == Role.IMP:
        return c2 if specific else Role.ANY_OTHER_EVIL
    return c2 if specific else Role.ANY_OTHER_EVIL

def _get_overlapping_good(c2: Role, specific: bool) -> Role | None:
    if c2 == Role.ANY_OTHER:
        return Role.ANY_OTHER_GOOD if specific else c2
    if c2 == Role.ANY_OTHER_EVIL:
        return None
    if c2 == Role.ANY_OTHER_MINION:
        return None
    if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
        return c2 if specific else Role.ANY_OTHER_GOOD
    if c2 == Role.NON_DEMON:
        return Role.ANY_OTHER_GOOD if specific else c2
    if c2 not in GOOD_CHARACTERS:
        return None
    return c2 if specific else Role.ANY_OTHER_GOOD

def _get_overlapping_minion(c2: Role, specific: bool) -> Role | None:
    if c2 == Role.ANY_OTHER:
        return Role.ANY_OTHER_MINION if specific else c2
    if c2 == Role.ANY_OTHER_GOOD:
        return None
    if c2 == Role.ANY_OTHER_EVIL:
        return Role.ANY_OTHER_MINION if specific else c2
    if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
        return None
    if c2 == Role.NON_DEMON:
        return Role.ANY_OTHER_MINION if specific else c2
    if c2 not in MINIONS:
        return None
    return c2 if specific else Role.ANY_OTHER_MINION

def _get_overlapping_townsfolk(c2: Role, specific: bool) -> Role | None:
    if c2 == Role.ANY_OTHER:
        return Role.ANY_OTHER_TOWNSFOLK if specific else c2
    if c2 == Role.ANY_OTHER_GOOD:
        return Role.ANY_OTHER_TOWNSFOLK if specific else c2
    if c2 == Role.ANY_OTHER_EVIL:
        return None
    if c2 == Role.ANY_OTHER_OUTSIDER:
        return None
    if c2 == Role.ANY_OTHER_MINION:
        return None
    if c2 == Role.NON_DEMON:
        return Role.ANY_OTHER_TOWNSFOLK if specific else c2
    if c2 not in TOWNSFOLK:
        return None
    return c2 if specific else Role.ANY_OTHER_TOWNSFOLK

def _get_overlapping_outsider(c2: Role, specific: bool) -> Role | None:
    if c2 == Role.ANY_OTHER:
        return Role.ANY_OTHER_OUTSIDER if specific else c2
    if c2 == Role.ANY_OTHER_GOOD:
        return Role.ANY_OTHER_OUTSIDER if specific else c2
    if c2 == Role.ANY_OTHER_EVIL:
        return None
    if c2 == Role.ANY_OTHER_TOWNSFOLK:
        return None
    if c2 == Role.ANY_OTHER_MINION:
        return None
    if c2 == Role.NON_DEMON:
        return Role.ANY_OTHER_OUTSIDER if specific else c2
    if c2 not in OUTSIDERS:
        return None
    return c2 if specific else Role.ANY_OTHER_OUTSIDER

def _get_overlapping_non_demon(c2: Role, specific: bool) -> Role | None:
    if c2 == Role.ANY_OTHER:
        return Role.NON_DEMON if specific else c2
    if c2 == Role.ANY_OTHER_EVIL:
        return Role.ANY_OTHER_MINION if specific else c2
    if c2 == Role.ANY_OTHER_GOOD:
        return c2 if specific else Role.NON_DEMON
    if c2 == Role.ANY_OTHER_MINION:
        return c2 if specific else Role.NON_DEMON
    if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
        return c2 if specific else Role.NON_DEMON
    if c2 == Role.IMP:
        return None
    return c2 if specific else Role.NON_DEMON

def _get_overlapping_other(c2: Role, specific: bool) -> Role | None:
    if c2 in ANY_OTHER_ROLES:
        return c2 if specific else Role.ANY_OTHER
    if c2 == Role.IMP:
        return c2 if specific else Role.ANY_OTHER
    return c2 if specific else Role.ANY_OTHER

