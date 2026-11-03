from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from .nightOrderPosition import NightOrderPosition
from . import helper

if TYPE_CHECKING:
    from .grimoire import Grimoire
    from .grimoire_page import GrimoirePage

from .role import *

ROLE_BREAKDOWNS: dict[
    int, dict[
        Literal['townsfolk']
        | Literal['outsiders']
        | Literal['minions']
        | Literal['demons'],
        int]
    ] = {
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

ALLOWED_MULTIPLES = {Role.IMP} | ANY_OTHER_ROLES_SET
EVIL_PLAYERS_WITHOUT_SPY = EVIL_ROLES_SET - {Role.SPY}

def can_scarlet_woman_catch(page: GrimoirePage, dead_player: int) -> bool:
    # known non-demon player died
    if not can_player_be_demon(page.characters[dead_player]):
        return False

    # known scarlet woman is dead already
    for i,c in enumerate(page.characters):
        if c == Role.SCARLET_WOMAN and page.dead[i]:
            return False
    
    # all evils are dead already
    dead_evil_count = sum(
        1 for i, c in enumerate(page.characters) 
        if page.dead[i] and c in EVIL_ROLES_SET
    )
    dead = page.dead[dead_player]
    max_evils = get_evil_count(page.num_players)
    if dead_evil_count + (1 if not dead else 0) >= max_evils:
        return False

    # none of the alive players could be a scarlet woman
    if len(page.get_alive_characters_of_type({Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.NON_DEMON, Role.SCARLET_WOMAN})) == 0:
        return False
    
    # scarlet woman cannot be in minion types
    if not is_minion_type_possible(Role.SCARLET_WOMAN, page.minion_types):
        return False
    
    return True

def can_imp_starpass(page: GrimoirePage, dead_player: int, red_herring_spy_catches: bool = False) -> bool:
    if red_herring_spy_catches and (page.find_red_herring_spy() is None or page.find_scarlet_woman() is not None):
        return False

    # known non-demon player killed by demon
    if not can_player_be_demon(page.characters[dead_player]):
        return False
    
    # all evils are dead already (assume dead player is the dead Imp)
    dead_evil_count = sum(
        1 for i, c in enumerate(page.characters) 
        if (
            page.dead[i] 
            and c in EVIL_ROLES_SET
            or i == dead_player)
    )
    max_evils = get_evil_count(page.num_players)
    if dead_evil_count >= max_evils:
        return False
    
    # none of the alive players could be a minion
    alive_potential_minions = page.get_alive_characters_of_type(MINIONS_SET | {Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON})
    if len(alive_potential_minions) == 0:
        return False
    
    return True

def can_minion_become_demon(prev: GrimoirePage, curr: GrimoirePage, minion: int) -> bool:
    minion_type = prev.characters[minion]
    if not minion_type in GENERIC_MINION_SET and curr.characters[minion] == Role.IMP:
        raise AssertionError(
            f"Called function with incompatible characters. "
            f"Prev: {prev.characters[minion].name}, curr: {curr.characters[minion].name}"
        )
    phase = curr.night_order_position
    if phase == NightOrderPosition.AFTER_IMP:
        if not curr.star_passed:
            return False
        if Role.SCARLET_WOMAN not in curr.minion_types:
            return True
        if minion_type == Role.SCARLET_WOMAN:
            return True
        if Role.SCARLET_WOMAN in curr.get_alive_characters_of_type({Role.SCARLET_WOMAN}):
            return False
        return True
    elif phase == NightOrderPosition.AFTER_EXECUTION:
        if curr.executee is None:
            return False
        if curr.characters[curr.executee] != Role.IMP and prev.characters[curr.executee] != Role.IMP:
            return False
        if Role.SCARLET_WOMAN not in curr.minion_types:
            return False
        if minion_type == Role.SCARLET_WOMAN or minion_type == Role.ANY_OTHER_MINION:
            return True
        return False
    elif phase == NightOrderPosition.AFTER_SLAYER:
        if True not in curr.slayer_shot:
            return False
        slayer_shot = curr.slayer_shot.index(True)
        if curr.characters[slayer_shot] != Role.IMP and prev.characters[slayer_shot] != Role.IMP:
            return False
        if Role.SCARLET_WOMAN not in curr.minion_types:
            return False
        if minion_type == Role.SCARLET_WOMAN or minion_type == Role.ANY_OTHER_MINION:
            return True
        return False
    else:
        return False
        
def can_non_demon_become_potential_demon(prev: GrimoirePage, curr: GrimoirePage, player: int) -> bool:
    previous = prev.characters[player]
    if not (
        (previous == Role.NON_DEMON or previous in GENERIC_MINION_SET)
        and (curr.characters[player] == Role.ANY_OTHER or curr.characters[player] == Role.ANY_OTHER_EVIL)
    ):
        raise AssertionError(
            f"Called function with incompatible characters. " +
            f"Prev: {previous.name}, curr: {curr.characters[player].name}"
        )
    could_be_scarlet_woman = previous in (Role.NON_DEMON, Role.ANY_OTHER_MINION, Role.SCARLET_WOMAN)
    phase = curr.night_order_position
    if phase == NightOrderPosition.AFTER_IMP:
        if not curr.star_passed:
            return False
    elif phase == NightOrderPosition.AFTER_EXECUTION:
        if curr.executee is None:
            return False
        if curr.characters[curr.executee] != Role.IMP and prev.characters[curr.executee] != Role.IMP:
            return False
        if not could_be_scarlet_woman:
            return False
    elif phase == NightOrderPosition.AFTER_SLAYER:
        if True not in curr.slayer_shot:
            return False
        slayer_shot = curr.slayer_shot.index(True)
        if curr.characters[slayer_shot] != Role.IMP and prev.characters[slayer_shot] != Role.IMP:
            return False
        if not could_be_scarlet_woman:
            return False
    else:
        return False
    for i, c in enumerate(curr.characters):
        if i == player:
            continue
        if c == Role.IMP and not curr.dead[i]:
            return False
    return True

def get_characters_of_type(characters: list[Role], type: set[Role]):
    return [c for c in characters if c in type]

POSSIBLE_RECLUSE_ROLES = {
    Role.RECLUSE,
    Role.ANY_OTHER_OUTSIDER,
    Role.ANY_OTHER_GOOD,
    Role.NON_DEMON,
    Role.ANY_OTHER
}

def is_first_night_setup_page(page: GrimoirePage) -> bool:
    return (
        page.night == 1
        and page.night_order_position == NightOrderPosition.AFTER_IMP
    )

def is_baron_possible(page: GrimoirePage) -> bool:
    return (
        Role.BARON in page.minion_types
        or Role.ANY_OTHER_MINION in page.minion_types
    )

def is_no_baron_possible(page: GrimoirePage) -> bool:
    return Role.BARON not in page.minion_types

def can_player_be_recluse(player: Role):
    return player in POSSIBLE_RECLUSE_ROLES

def can_player_be_demon(player: Role):
    return player not in {Role.NON_DEMON, Role.ANY_OTHER_MINION} | GOOD_ROLES_SET | MINIONS_SET

def is_minion_type_possible(minion: Role, minion_types: list[Role]):
    return minion in minion_types or Role.ANY_OTHER_MINION in minion_types

def get_valid_red_herrings(characters: list[Role]):
    return [i for i, c in enumerate(characters) if c not in EVIL_CHARACTERS or c == Role.SPY]

def get_evil_count(num_players: int) -> int:
    return ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']

def get_good_count(num_players: int) -> int:
    return ROLE_BREAKDOWNS[num_players]['townsfolk'] + ROLE_BREAKDOWNS[num_players]['outsiders']

def get_townsfolk_count(num_players: int, baron: bool) -> int:
    return ROLE_BREAKDOWNS[num_players]['townsfolk'] - 2 if baron else ROLE_BREAKDOWNS[num_players]['townsfolk']

def get_outsider_count(num_players: int, baron: bool):
    return ROLE_BREAKDOWNS[num_players]['outsiders'] + 2 if baron else ROLE_BREAKDOWNS[num_players]['outsiders']

def get_minion_count(num_players: int):
    return ROLE_BREAKDOWNS[num_players]['minions']
