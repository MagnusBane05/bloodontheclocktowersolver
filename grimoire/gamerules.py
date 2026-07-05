from __future__ import annotations
from collections import Counter
from typing import TYPE_CHECKING, Literal

from .role import NON_RECLUSE_OUTSIDERS
from .nightOrderPosition import NightOrderPosition

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

def can_imp_starpass(page: GrimoirePage, dead_player: int) -> bool:
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
    if not (
        (prev.characters[player] == Role.NON_DEMON or prev.characters[player] == Role.ANY_OTHER_MINION)
        and (curr.characters[player] == Role.ANY_OTHER or curr.characters[player] == Role.ANY_OTHER_EVIL)
    ):
        raise AssertionError(
            f"Called function with incompatible characters. "
            f"Prev: {prev.characters[player].name}, curr: {curr.characters[player].name}"
        )
    phase = curr.night_order_position
    if phase == NightOrderPosition.AFTER_IMP:
        if not curr.star_passed:
            return False
    elif phase == NightOrderPosition.AFTER_EXECUTION:
        if curr.executee is None:
            return False
        if curr.characters[curr.executee] != Role.IMP and prev.characters[curr.executee] != Role.IMP:
            return False
    elif phase == NightOrderPosition.AFTER_SLAYER:
        if True not in curr.slayer_shot:
            return False
        slayer_shot = curr.slayer_shot.index(True)
        if curr.characters[slayer_shot] != Role.IMP and prev.characters[slayer_shot] != Role.IMP:
            return False
    else:
        return False
    for i, c in enumerate(curr.characters):
        if i == player:
            continue
        if c == Role.IMP and not curr.dead[i]:
            return False
    return True

def is_grim_valid(grim: Grimoire):
    for page in grim.pages:
        valid, _reason = is_page_valid(page)
        if not valid:
            return False
    return True

def is_page_valid(page: GrimoirePage) -> tuple[bool, str]:
    num_players = page.num_players
    # Check outsider count on first night only
    if page.night == 1 and page.night_order_position == NightOrderPosition.AFTER_IMP:
        if not is_outsider_count_valid(page, num_players):
            return False, "invalid outsider count"
        elif not is_chef_number_valid(page):
            return False, "invalid chef number"
    if not is_evil_count_valid(page, num_players):
        return False, "invalid evil count"
    elif not is_good_count_valid(page, num_players):
        return False, "invalid good count"
    elif not are_minion_types_valid(page):
        return False, "invalid minion types"
    elif not is_poisoning_valid(page, num_players):
        return False, "invalid poisoning"
    elif not is_no_invalid_duplicates(page):
        return False, "invalid duplicates"
    elif not is_no_sober_saint_executed(page):
        return False, "sober Saint executed"
    elif not is_red_herring_valid(page):
        return False, "invalid red herring"
    return True, ""

def is_outsider_count_valid(first_page: GrimoirePage, num_players: int):
    # librarian told no outsiders
    if first_page.no_outsiders and len(get_characters_of_type(first_page.characters, NON_RECLUSE_OUTSIDERS)) > 0:
        return False
    # base outsider count or if a Baron is in play, base outsider count plus 2
    base_outsider_count = get_outsider_count(num_players, Role.BARON in first_page.minion_types)
    recluse = False
    for c in first_page.characters:
        if can_player_be_recluse(c):
            recluse = True
            break
    # Recluse can register as non-outsider to Librarian
    non_recluse_outsiders = base_outsider_count - 1 if recluse else base_outsider_count
    if first_page.no_outsiders and non_recluse_outsiders > 0:
        return False

    valid_counts = [base_outsider_count]
    # we don't know if a baron is in play, valid counts could be base and base plus 2
    if Role.BARON not in first_page.minion_types and Role.ANY_OTHER_MINION in first_page.minion_types:
        valid_counts.append(get_outsider_count(num_players, True))
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
    dead_imps = 0
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
        if character == Role.IMP:
            if not dead:
                alive_imps += 1
            else:
                dead_imps += 1
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
    # Dead imp and all minions known
    if dead_imps + minion_count == evil_count:
        return False

    return True

def is_good_count_valid(page: GrimoirePage, num_players: int):
    good_count = sum(1 for c in page.characters if c in GOOD_ROLES_SET)
    role_breakdowns = ROLE_BREAKDOWNS[num_players]
    return good_count <= role_breakdowns['townsfolk'] + role_breakdowns['outsiders']

def are_minion_types_valid(page: GrimoirePage) -> bool:
    for c in page.characters:
        if c in MINIONS and c not in page.minion_types:
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
    # return false if no poisoner (must be explicit)
    if Role.POISONER not in page.minion_types:
        return False
    # return false if known poisoner is dead
    dead_characters = [c for i, c in enumerate(page.characters) if page.dead[i]]
    if Role.POISONER in dead_characters:
        return False
    # false if all minions are dead (check evil roles, not just minions, in case of star passes)
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

def is_chef_number_valid(page: GrimoirePage) -> bool:
    chef_number = page.chef_number
    if chef_number is None:
        return True
    characters = page.characters
    minion_types = page.minion_types
    num_players = page.num_players

    # Could an unknown player be the spy
    spy_possible = (
        Role.SPY not in characters 
        and (
            Role.SPY in minion_types 
            or Role.ANY_OTHER_MINION in minion_types)
    )

    # Could an unknown player be the recluse
    known_outsiders = sum(1 for c in characters if c in OUTSIDERS)
    baron_possible = Role.BARON in minion_types or Role.ANY_OTHER_MINION in minion_types
    max_outsiders = get_outsider_count(num_players, baron_possible)
    recluse_possible = Role.RECLUSE not in characters and known_outsiders < max_outsiders

    # Precompute predicates for each character
    definitely_evil = [False] * num_players
    possibly_evil = [False] * num_players
    could_be_recluse = [False] * num_players
    evil_could_be_spy = [False] * num_players

    for i in range(num_players):
        role = characters[i]
        if role == Role.SPY:
            definitely_evil[i] = False
            possibly_evil[i] = True
            could_be_recluse[i] = False
            evil_could_be_spy[i] = False
        elif role in EVIL_CHARACTERS:
            definitely_evil[i] = True
            possibly_evil[i] = True
            could_be_recluse[i] = False
            evil_could_be_spy[i] = False
        elif not spy_possible and role in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]:
            definitely_evil[i] = True
            possibly_evil[i] = True
            could_be_recluse[i] = False
            evil_could_be_spy[i] = False
        elif role in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]:
            definitely_evil[i] = False
            possibly_evil[i] = True
            could_be_recluse[i] = False
            evil_could_be_spy[i] = True
        elif role in [Role.ANY_OTHER, Role.NON_DEMON]:
            definitely_evil[i] = False
            possibly_evil[i] = True
            could_be_recluse[i] = True
            evil_could_be_spy[i] = False
        elif role == Role.RECLUSE:
            definitely_evil[i] = False
            possibly_evil[i] = True
            could_be_recluse[i] = False
            evil_could_be_spy[i] = False
        else:
            definitely_evil[i] = False
            possibly_evil[i] = False
            could_be_recluse[i] = role in [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_OUTSIDER]
            evil_could_be_spy[i] = False

    pairs = [(i, (i + 1) % num_players) for i in range(num_players)]

    min_pairs = 0
    max_pairs = 0

    recluse_needed: list[int] = []
    possible_spies: list[int] = []
    spies_needed = 0

    for i, j in pairs:
        if definitely_evil[i] and definitely_evil[j]:
            min_pairs += 1
        elif definitely_evil[i] and evil_could_be_spy[j]:
            possible_spies.append(j)
            spies_needed += 1
        elif evil_could_be_spy[i] and definitely_evil[j]:
            possible_spies.append(i)
            spies_needed += 1
        elif evil_could_be_spy[i] and evil_could_be_spy[j]:
            possible_spies.extend([i, j])
            spies_needed += 1

        if possibly_evil[i] and possibly_evil[j]:
            max_pairs += 1
        elif possibly_evil[i] and could_be_recluse[j]:
            recluse_needed.append(j)
        elif could_be_recluse[i] and possibly_evil[j]:
            recluse_needed.append(i)

    recluse_counter = Counter(recluse_needed)
    recluse_impact = max(recluse_counter.values()) if recluse_counter else 0
    max_pairs += recluse_impact if recluse_possible else 0

    spy_counter = Counter(possible_spies)
    spy_impact = max(spy_counter.values()) if spy_counter else 0
    min_pairs += spies_needed - spy_impact if spy_possible else 0

    # Global evil count constraint
    max_evils = ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']
    max_pairs = min(max_pairs, max_evils)

    return min_pairs <= chef_number <= max_pairs

def is_red_herring_valid(page: GrimoirePage) -> bool:
    red_herring = page.red_herring
    num_rh = sum(1 for rh in red_herring if rh)
    if num_rh == 0:
        return True
    # No more than 1 red herring
    if num_rh > 1:
        return False
    # Red herring isn't on an evil character
    rh_player = red_herring.index(True)
    character = page.characters[rh_player]
    if character in EVIL_PLAYERS_WITHOUT_SPY:
        return False
    return True

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