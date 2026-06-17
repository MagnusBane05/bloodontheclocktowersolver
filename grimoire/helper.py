from typing import TYPE_CHECKING

from grimoire.role import DEMONS, EVIL_CHARACTERS, GOOD_CHARACTERS, MINIONS, OUTSIDERS, TOWNSFOLK, Role

if TYPE_CHECKING:
    from grimoire.grimoire import Grimoire

def quick_reject(g1: Grimoire, g2: Grimoire) -> bool:
    p2 = g2.pages[-1]
    p1 = g1.get_page(p2.night, p2.night_order_position)
    if p1 == None:
        return False
    
    for i,c in enumerate(p2.characters):
        if not roleLooseEquals(c, p1.characters[i]):
            return True
        
    return False


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

            