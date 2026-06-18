from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from grimoire.nightOrderPosition import NightOrderPosition

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

def can_scarlet_woman_catch(page: GrimoirePage, dead_player: int) -> bool:
    # known non-demon player died
    if not can_player_be_demon(page.characters[dead_player]):
        return False

    # known scarlet woman is dead already
    for i,c in enumerate(page.characters):
        if c == Role.SCARLET_WOMAN and page.dead[i]:
            return False
    
    # all minions are dead already
    dead_minions = page.get_dead_characters_of_type(MINIONS_SET | {Role.ANY_OTHER_MINION})
    if len(dead_minions) >= len(page.minion_types):
        return False

    # none of the alive players could be a scarlet woman
    if len(page.get_alive_characters_of_type({Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.NON_DEMON, Role.SCARLET_WOMAN})) == 0:
        return False
    
    # scarlet woman cannot be in minion types
    if not is_minion_type_possible(Role.SCARLET_WOMAN, page.minion_types):
        return False
    
    return True

def can_imp_starpass(page: GrimoirePage, dead_player: int) -> bool:
    # known non-demon player killed by demon
    if not can_player_be_demon(page.characters[dead_player]):
        return False
    
    # all minions are dead already
    dead_minions = page.get_dead_characters_of_type(MINIONS_SET | {Role.ANY_OTHER_MINION})
    if len(dead_minions) >= len(page.minion_types):
        return False
    
    # none of the alive players could be a minion
    alive_potential_minions = page.get_alive_characters_of_type(MINIONS_SET | {Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON})
    if len(alive_potential_minions) == 0:
        return False
    
    return True

def is_grim_valid(grim: Grimoire):
    first_page = grim.pages[0]
    num_players = len(first_page.characters)

    if not is_outsider_count_valid(first_page, num_players):
        return False

    for page in grim.pages:
        valid = (
            is_evil_count_valid(page, num_players) and
            is_good_count_valid(page, num_players) and
            are_minion_types_valid(page) and
            is_poisoning_valid(page, num_players) and
            is_no_invalid_duplicates(page) and
            is_no_sober_saint_executed(page)
        )
        if not valid:
            return False
    return True


def is_outsider_count_valid(first_page: GrimoirePage, num_players: int):
    # librarian told no outsiders
    if first_page.no_outsiders and len(get_characters_of_type(first_page.characters, OUTSIDERS_SET)) > 0:
        return False
    # base outsider count or if a Baron is in play, base outsider count plus 2
    valid_counts = [get_outsider_count(num_players, Role.BARON in first_page.minion_types)]
    # we don't know if a baron is in play, valid counts could be base and base plus 2
    if Role.BARON not in first_page.minion_types and Role.ANY_OTHER_MINION in first_page.minion_types:
        valid_counts.append(ROLE_BREAKDOWNS[num_players]['outsiders']+2)
    minimum = len(get_characters_of_type(first_page.characters, OUTSIDERS_SET | {Role.ANY_OTHER_OUTSIDER}))
    maximum = minimum + len(get_characters_of_type(first_page.characters, {Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON}))
    # valid if any possible number of outsiders is in one of the valid counts
    return any(c in valid_counts for c in range(minimum, maximum+1))

NONDEMON_OR_ANY = {Role.NON_DEMON, Role.ANY_OTHER}
POTENTIAL_IMPS = {Role.IMP, Role.ANY_OTHER_EVIL, Role.ANY_OTHER}
MINIONS_OR_ANY = MINIONS_SET | {Role.ANY_OTHER_MINION}
VALID_DUPLICATES = ANY_OTHER_ROLES_SET | {Role.IMP}
OUTSIDER_MIN_ROLES = OUTSIDERS_SET | {Role.ANY_OTHER_OUTSIDER}
OUTSIDER_MAX_ROLES = {Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON}

def is_evil_count_valid(page: GrimoirePage, num_players: int):
    # characters = page.characters
    role_breakdowns = ROLE_BREAKDOWNS[num_players]
    evil_count = role_breakdowns['demons'] + role_breakdowns['minions']

    # Precompute counts
    evil_roles_count = 0
    nondemon_any_count = 0
    alive_imps = 0
    potential_imps = 0
    dead_evils = 0
    minion_count = 0
    for character, dead in zip(page.characters, page.dead):
        if character in EVIL_ROLES_SET:
            evil_roles_count += 1
            if dead:
                dead_evils += 1
        if character in NONDEMON_OR_ANY:
            nondemon_any_count += 1
        if character == Role.IMP and not dead:
            alive_imps += 1
        if character in POTENTIAL_IMPS and not dead:
            potential_imps += 1
        if character in MINIONS_OR_ANY:
            minion_count += 1
        
    potential_evils = evil_roles_count + nondemon_any_count
    if potential_evils < evil_count:
        return False
    # More than 1 alive imp
    if alive_imps > 1:
        return False
    # No alive player could be the demon
    if potential_imps == 0:
        return False
    # All evil players are dead
    if dead_evils >= evil_count:
        return False
    # Too many minions
    if minion_count > role_breakdowns['minions']:
        return False
    # Too many evil players
    if evil_roles_count > evil_count:
        return False

    return True

def is_good_count_valid(page: GrimoirePage, num_players: int):
    good_count = sum(1 for c in page.characters if c in GOOD_ROLES_SET)
    role_breakdowns = ROLE_BREAKDOWNS[num_players]
    return good_count <= role_breakdowns['townsfolk'] + role_breakdowns['outsiders']

def are_minion_types_valid(page: GrimoirePage) -> bool:
    for c in page.characters:
        if c not in MINIONS or c in page.minion_types:
            continue
        try:
            # If there isn't room to replace ANY_OTHER_MINION with the specific character, it's not a valid world
            page.minion_types.index(Role.ANY_OTHER_MINION)
        except ValueError:
            return False
    return True

def is_poisoning_valid(page: GrimoirePage, num_players: int) -> bool:
    poisoned_count = sum(page.poisoned)
    # we can return true right away if no one is poisoned
    if poisoned_count == 0:
        return True
    # don't allow 2 instances of poisoning
    if poisoned_count > 1:
        return False
    # return false if no room for poisoner
    if Role.POISONER not in page.minion_types and Role.ANY_OTHER_MINION not in page.minion_types:
        return False
    # return false if known poisoner is dead
    dead_characters = [c for i, c in enumerate(page.characters) if page.dead[i]]
    if Role.POISONER in dead_characters:
        return False
    # false if all minions are dead (check evil roles, not just minions, in case of start passes)
    if len([c for c in dead_characters if c in EVIL_ROLES]) == ROLE_BREAKDOWNS[num_players]['minions']:
        return False
    return True

def is_no_invalid_duplicates(page: GrimoirePage) -> bool:
    valid_duplicates = ANY_OTHER_ROLES_SET | {Role.IMP}
    invalid_duplicates = [c for c in page.characters if c not in valid_duplicates]
    return len(invalid_duplicates) == len(set(invalid_duplicates))

def is_no_sober_saint_executed(page: GrimoirePage) -> bool:
    if page.night_order_position != NightOrderPosition.AFTER_EXECUTION:
        return True
    if page.executee is None:
        return True
    if page.characters[page.executee] != Role.SAINT:
        return True
    return page.poisoned[page.executee]

def get_outsider_count(num_players: int, baron: bool):
    return ROLE_BREAKDOWNS[num_players]['outsiders'] + 2 if baron else ROLE_BREAKDOWNS[num_players]['outsiders']

def get_characters_of_type(characters: list[Role], type: set[Role]):
    return [c for c in characters if c in type]

def can_player_be_recluse(player: Role):
    return (player == Role.RECLUSE or player == Role.ANY_OTHER_OUTSIDER or
            player == Role.ANY_OTHER_GOOD or player == Role.ANY_OTHER)

def can_player_be_demon(player: Role):
    return player not in {Role.NON_DEMON, Role.ANY_OTHER_MINION} | GOOD_ROLES_SET | MINIONS_SET

def is_minion_type_possible(minion: Role, minion_types: list[Role]):
    return minion in minion_types or Role.ANY_OTHER_MINION in minion_types

def get_valid_red_herrings(characters: list[Role]):
    return [i for i, c in enumerate(characters) if c not in EVIL_CHARACTERS or c == Role.SPY]