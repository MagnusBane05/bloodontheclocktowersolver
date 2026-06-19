from grimoire.role import DEMONS, EVIL_CHARACTERS, GOOD_CHARACTERS, MINIONS, OUTSIDERS, TOWNSFOLK, Role, get_overlapping


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


def role_subsumes(general: Role, specific: Role) -> bool:
    if general == specific:
        return True
    result = get_overlapping(general, specific, False)
    return result == general

def minion_types_subsume(general: list[Role], specific: list[Role]) -> bool:
    general_specific = {
        role for role in general
        if role != Role.ANY_OTHER_MINION
    }

    specific_specific = {
        role for role in specific
        if role != Role.ANY_OTHER_MINION
    }

    # If general requires a concrete minion, specific must also require it.
    return general_specific.issubset(specific_specific)

def singleton_subsumes(general: list[bool], specific: list[bool]) -> bool:
    general_idx = _singleton_index(general)
    specific_idx = _singleton_index(specific)

    if general_idx is None:
        return True

    return general_idx == specific_idx

def _singleton_index(values: list[bool]) -> int | None:
    for i, value in enumerate(values):
        if value:
            return i
    return None