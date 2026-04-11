from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grimoire import Grimoire
    from .grimoire_page import GrimoirePage

from .role import *

def can_scarlet_woman_catch(page: GrimoirePage, dead_player: int) -> bool:
    # known non-demon player died
    if not can_player_be_demon(page.characters[dead_player]):
        return False

    # known scarlet woman is dead already
    if len(get_dead_characters_of_type(page, {Role.SCARLET_WOMAN})) > 0:
        return False
    
    # all minions are dead already
    dead_minions = get_dead_characters_of_type(page, MINIONS_SET | {Role.ANY_OTHER_MINION})
    if len(dead_minions) >= len(page.minion_types):
        return False

    # none of the alive players could be a scarlet woman
    if len(get_alive_characters_of_type(page, {Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.NON_DEMON, Role.SCARLET_WOMAN})) == 0:
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
    dead_minions = get_dead_characters_of_type(page, MINIONS_SET | {Role.ANY_OTHER_MINION})
    if len(dead_minions) >= len(page.minion_types):
        return False
    
    # none of the alive players could be a minion
    alive_potential_minions = get_alive_characters_of_type(page, MINIONS_SET | {Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON})
    if len(alive_potential_minions) == 0:
        return False
    
    return True

def is_grim_valid(grim: Grimoire):
    first_page = grim.pages[0]
    num_players = len(first_page.characters)
    for page in grim.pages:
        valid = (
            is_outsider_count_valid(first_page, num_players) and
            is_evil_count_valid(page, num_players) and
            is_good_count_valid(page, num_players) and
            are_minion_types_valid(page) and
            is_invalid_duplicates(page)
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

def is_evil_count_valid(page: GrimoirePage, num_players: int):
    characters = page.characters
    evil_count = get_evil_count(num_players)

    # Precompute counts
    evil_roles_count = get_characters_of_type_count(characters, EVIL_ROLES_SET)
    nondemon_any_count = get_characters_of_type_count(characters, {Role.NON_DEMON, Role.ANY_OTHER})
    potential_evils = evil_roles_count + nondemon_any_count
    if potential_evils < evil_count:
        return False

    # More than 1 alive imp
    alive_imps = get_alive_characters_of_type_count(page, {Role.IMP})
    if alive_imps > 1:
        return False

    # No alive player could be the demon
    potential_imps = get_alive_characters_of_type_count(page, {Role.IMP, Role.ANY_OTHER_EVIL, Role.ANY_OTHER})
    if potential_imps == 0:
        return False

    # All evil players are dead
    dead_evils = get_dead_characters_of_type_count(page, EVIL_ROLES_SET)
    if dead_evils >= evil_count:
        return False

    # Too many minions
    minion_count = get_characters_of_type_count(characters, MINIONS_SET | {Role.ANY_OTHER_MINION})
    if minion_count > get_minion_count(num_players):
        return False

    # Too many evil players
    if evil_roles_count > evil_count:
        return False

    return True

def is_good_count_valid(page: GrimoirePage, num_players: int):
    good_count = sum(1 for c in page.characters if c in GOOD_ROLES)
    return good_count <= get_good_count(num_players)

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

def is_invalid_duplicates(page: GrimoirePage) -> bool:
    valid_duplicates = ANY_OTHER_ROLES_SET | {Role.IMP}
    no_imps = [c for c in page.characters if c not in valid_duplicates]
    return len(no_imps) == len(set(no_imps))

def get_good_count(num_players: int):
    return get_townsfolk_count(num_players) + get_outsider_count(num_players, False)

def get_evil_count(num_players: int):
    return get_minion_count(num_players) + 1

def get_townsfolk_count(num_players: int):
    return ROLE_BREAKDOWNS[num_players]['townsfolk']

def get_outsider_count(num_players: int, baron: bool):
    return ROLE_BREAKDOWNS[num_players]['outsiders'] + 2 if baron else ROLE_BREAKDOWNS[num_players]['outsiders']

def get_minion_count(num_players: int):
    return ROLE_BREAKDOWNS[num_players]['minions']

def get_characters_of_type(characters: list[Role], type: set[Role]):
    return [c for c in characters if c in type]

def get_alive_characters_of_type(page: GrimoirePage, type: set[Role]):
    return [c for i, c in enumerate(page.characters) if not page.dead[i] and c in type]

def get_alive_players_of_type(page: GrimoirePage, type: set[Role]):
    return [i for i,(c,d) in enumerate(zip(page.characters, page.dead)) if not d and c in type]

def get_dead_characters_of_type(page: GrimoirePage, type: set[Role]):
    return [c for i, c in enumerate(page.characters) if page.dead[i] and c in type]

def get_characters_of_type_count(characters: list[Role], type: set[Role]):
    return sum([1 for c in characters if c in type])

def get_alive_characters_of_type_count(page: GrimoirePage, type: set[Role]):
    return sum([1 for c, d in zip(page.characters, page.dead) if not d and c in type])

def get_dead_characters_of_type_count(page: GrimoirePage, type: set[Role]):
    return sum([1 for c, d in zip(page.characters, page.dead) if d and c in type])

def can_player_be_recluse(player: Role):
    return (player == Role.RECLUSE or player == Role.ANY_OTHER_OUTSIDER or
            player == Role.ANY_OTHER_GOOD or player == Role.ANY_OTHER)

def can_player_be_demon(player: Role):
    return player not in {Role.NON_DEMON} | GOOD_CHARACTERS_SET | MINIONS_SET

def is_minion_type_possible(minion: Role, minion_types: list[Role]):
    return minion in minion_types or Role.ANY_OTHER_MINION in minion_types

def get_valid_red_herrings(characters: list[Role]):
    return [i for i, c in enumerate(characters) if c not in EVIL_CHARACTERS or c == Role.SPY]