from enum import IntEnum, auto

from .role import Role, TOWNSFOLK_SET, OUTSIDERS_SET, MINIONS_SET


class CharacterType(IntEnum):
    TOWNSFOLK = auto()
    OUTSIDER = auto()
    MINION = auto()
    DEMON = auto()

def get_type(character: Role) -> CharacterType | None:
    if character == Role.ANY_OTHER_TOWNSFOLK or character in TOWNSFOLK_SET:
        return CharacterType.TOWNSFOLK
    elif character == Role.ANY_OTHER_OUTSIDER or character in OUTSIDERS_SET:
        return CharacterType.OUTSIDER
    elif character == Role.ANY_OTHER_MINION or character in MINIONS_SET:
        return CharacterType.MINION
    elif character == Role.IMP:
        return CharacterType.DEMON
    else:
        return None
