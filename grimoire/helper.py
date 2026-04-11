from grimoire.role import DEMONS, EVIL_CHARACTERS, GOOD_CHARACTERS, MINIONS, OUTSIDERS, TOWNSFOLK, Role


def roleLooseEquals(r1: Role, r2: Role) -> bool:
    if r1 == r2:
        return True
    if r1 == Role.ANY_OTHER or r2 == Role.ANY_OTHER:
        return True
    if r1 == Role.NON_DEMON:
        return r2 != Role.IMP
    if r2 == Role.NON_DEMON:
        return r1 != Role.IMP
    if r1 == Role.ANY_OTHER_TOWNSFOLK:
        return r2 in TOWNSFOLK or r2 == Role.ANY_OTHER_GOOD
    if r1 == Role.ANY_OTHER_OUTSIDER:
        return r2 in OUTSIDERS or r2 == Role.ANY_OTHER_GOOD
    if r1 == Role.ANY_OTHER_MINION:
        return r2 in MINIONS or r2 == Role.ANY_OTHER_EVIL
    if r1 == Role.ANY_OTHER_GOOD:
        return r2 in GOOD_CHARACTERS or r2 == Role.ANY_OTHER_OUTSIDER or r2 == Role.ANY_OTHER_TOWNSFOLK
    if r1 == Role.ANY_OTHER_EVIL:
        return r2 in EVIL_CHARACTERS or r2 == Role.ANY_OTHER_MINION
    if r1 in TOWNSFOLK:
        return r2 == Role.ANY_OTHER_TOWNSFOLK or r2 == Role.ANY_OTHER_GOOD
    if r1 in OUTSIDERS:
        return r2 == Role.ANY_OTHER_OUTSIDER or r2 == Role.ANY_OTHER_GOOD
    if r1 in MINIONS:
        return r2 == Role.ANY_OTHER_MINION or r2 == Role.ANY_OTHER_EVIL
    if r1 in DEMONS:
        return r2 == Role.ANY_OTHER_EVIL
    raise Exception("Something has gone terribly wrong")

def minion_types_loose_equals(mt1: list[Role], mt2: list[Role]):
    unique_minions = set(mt1 + mt2)
    unique_minions.discard(Role.ANY_OTHER_MINION)
    return len(unique_minions) <= len(mt1)

            