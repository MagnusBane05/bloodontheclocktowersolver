from enum import IntEnum, auto

from .role import Role, TOWNSFOLK_SET, OUTSIDERS_SET, MINIONS_SET


class CharacterType(IntEnum):
    TOWNSFOLK = auto()
    OUTSIDER = auto()
    MINION = auto()
    DEMON = auto()
    ANY_GOOD = auto()
    ANY_EVIL = auto()
    NON_DEMON = auto()
    ANY = auto()

    def loose_equals(self, other: CharacterType) -> bool:
        if self == other:
            return True
        elif self == CharacterType.ANY or other == CharacterType.ANY:
            return True
        elif self == CharacterType.NON_DEMON:
            return other != CharacterType.DEMON
        elif other == CharacterType.NON_DEMON:
            return self != CharacterType.DEMON
        elif self == CharacterType.ANY_GOOD:
            return other == CharacterType.TOWNSFOLK or other == CharacterType.OUTSIDER
        elif self == CharacterType.ANY_EVIL:
            return other == CharacterType.MINION or other == CharacterType.DEMON
        elif self == CharacterType.TOWNSFOLK or self == CharacterType.OUTSIDER:
            return other == CharacterType.ANY_GOOD
        elif self == CharacterType.MINION or self == CharacterType.DEMON:
            return other == CharacterType.ANY_EVIL
        else:
            raise RuntimeError(f"Cannot determine equality between {self} and {other}")

def get_type(character: Role) -> CharacterType:
    if character == Role.ANY_OTHER:
        return CharacterType.ANY
    elif character == Role.NON_DEMON:
        return CharacterType.NON_DEMON
    elif character == Role.ANY_OTHER_GOOD:
        return CharacterType.ANY_GOOD
    elif character == Role.ANY_OTHER_EVIL:
        return CharacterType.ANY_EVIL
    elif character == Role.ANY_OTHER_TOWNSFOLK or character in TOWNSFOLK_SET:
        return CharacterType.TOWNSFOLK
    elif character == Role.ANY_OTHER_OUTSIDER or character in OUTSIDERS_SET:
        return CharacterType.OUTSIDER
    elif character == Role.ANY_OTHER_MINION or character in MINIONS_SET:
        return CharacterType.MINION
    elif character == Role.IMP:
        return CharacterType.DEMON
    else:
        raise RuntimeError(f"Character {character.name} has unknown type")
