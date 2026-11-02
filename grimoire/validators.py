from enum import IntEnum, auto
import math
from typing import TYPE_CHECKING, Callable, NamedTuple

from . import helper
from . import gamerules
from .nightOrderPosition import NightOrderPosition
from .role import *
from .character_type import CharacterType, get_possible_types

if TYPE_CHECKING:
    from .grimoire import Grimoire
    from .grimoire_page import GrimoirePage

class ChangeType(IntEnum):
    CHARACTER = auto()
    MINION_TYPE = auto()
    LIBRARIAN_NO = auto()
    DEATH = auto()
    POISONED = auto()
    NIGHT_ORDER = auto()
    EXECUTEE = auto()
    CHEF_NUMBER = auto()
    RED_HERRING = auto()

class Validator(NamedTuple):
    validate: Callable[[GrimoirePage], bool]
    reason: str
    affected_by: frozenset[ChangeType]

def is_outsider_count_valid(first_page: GrimoirePage, num_players: int) -> bool:
    # librarian told no outsiders
    if first_page.no_outsiders and len(gamerules.get_characters_of_type(first_page.characters, NON_RECLUSE_OUTSIDERS)) > 0:
        return False
    # base outsider count or if a Baron is in play, base outsider count plus 2
    base_outsider_count = gamerules.get_outsider_count(num_players, Role.BARON in first_page.minion_types)
    recluse = False
    for c in first_page.characters:
        if gamerules.can_player_be_recluse(c):
            recluse = True
            break
    # Recluse can register as non-outsider to Librarian
    non_recluse_outsiders = base_outsider_count - 1 if recluse else base_outsider_count
    if first_page.no_outsiders and non_recluse_outsiders > 0:
        return False

    valid_counts = [base_outsider_count]
    # we don't know if a baron is in play, valid counts could be base and base plus 2
    if Role.BARON not in first_page.minion_types and Role.ANY_OTHER_MINION in first_page.minion_types:
        valid_counts.append(gamerules.get_outsider_count(num_players, True))
    minimum = len(gamerules.get_characters_of_type(first_page.characters, OUTSIDERS_SET | {Role.ANY_OTHER_OUTSIDER}))
    # more than 1 outsider with Librarian no
    if minimum > 1 and first_page.no_outsiders:
        return False
    maximum = minimum + len(gamerules.get_characters_of_type(first_page.characters, {Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON}))
    # valid if any possible number of outsiders is in one of the valid counts
    return any(c in valid_counts for c in range(minimum, maximum+1))

NONDEMON_OR_ANY = {Role.NON_DEMON, Role.ANY_OTHER}
POTENTIAL_IMPS = {Role.IMP, Role.ANY_OTHER_EVIL, Role.ANY_OTHER}
VALID_DUPLICATES = ANY_OTHER_ROLES_SET | {Role.IMP}
OUTSIDER_MAX_ROLES = {Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON}
OUTSIDERS_OR_UNKNOWN = GENERIC_OUTSIDER_SET | {Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON}

def is_evil_count_valid(page: GrimoirePage, num_players: int):
    # characters = page.characters
    evil_count = gamerules.get_evil_count(num_players)

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
        if character in GENERIC_MINION_SET:
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
    if minion_count > gamerules.get_minion_count(num_players):
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
    return good_count <= gamerules.get_good_count(num_players)

def is_role_breakdown_valid(page: GrimoirePage):
    num_players = page.num_players
    minions = gamerules.get_minion_count(num_players)
    demons  = 1

    if gamerules.is_baron_possible(page):
        if _is_breakdown_possible(
            page,
            townsfolk=gamerules.get_townsfolk_count(num_players, True),
            outsiders=gamerules.get_outsider_count(num_players, True),
            minions=minions,
            demons=demons
        ):
            return True

    if gamerules.is_no_baron_possible(page):
        if _is_breakdown_possible(
            page,
            townsfolk=gamerules.get_townsfolk_count(num_players, False),
            outsiders=gamerules.get_outsider_count(num_players, False),
            minions=minions,
            demons=demons
        ):
            return True
        
    return False
        
CHARACTER_TYPE_INDEX = {
    CharacterType.TOWNSFOLK: 0,
    CharacterType.OUTSIDER: 1,
    CharacterType.MINION: 2,
    CharacterType.DEMON: 3,
}

def _is_breakdown_possible(
    page: GrimoirePage,
    *,
    townsfolk: int,
    outsiders: int,
    minions: int,
    demons: int
) -> bool:
    target = (townsfolk, outsiders, minions, demons)
    possible_counts = {(0, 0, 0, 0)}
    for character in page.characters:
        next_counts: set[tuple[int, int, int, int]] = set()
        for counts in possible_counts:
            for character_type in get_possible_types(character):
                new_counts = list(counts)
                index = CHARACTER_TYPE_INDEX[character_type]
                new_counts[index] += 1
                new_counts_tuple = (
                    new_counts[0],
                    new_counts[1],
                    new_counts[2],
                    new_counts[3],
                )
                if all(
                    count <= maximum
                    for count, maximum in zip(new_counts_tuple, target)
                ):
                    next_counts.add(new_counts_tuple)
        if not next_counts:
            return False
        possible_counts = next_counts
    return target in possible_counts

def is_role_assignment_valid(page: GrimoirePage) -> bool:
    num_players = page.num_players
    minions = gamerules.get_minion_count(num_players)

    if gamerules.is_baron_possible(page):
        if _is_assignment_possible(
            page,
            townsfolk=gamerules.get_townsfolk_count(num_players, True),
            outsiders=gamerules.get_outsider_count(num_players, True),
            minions=minions,
            demons=1,
        ):
            return True

    if gamerules.is_no_baron_possible(page):
        if _is_assignment_possible(
            page,
            townsfolk=gamerules.get_townsfolk_count(num_players, False),
            outsiders=gamerules.get_outsider_count(num_players, False),
            minions=minions,
            demons=1,
        ):
            return True

    return False

class _RoleAssignmentOption(NamedTuple):
    character_type: CharacterType
    registers_evil: bool
    is_spy: bool = False
    is_recluse: bool = False

class _AssignmentState(NamedTuple):
    townsfolk: int = 0
    outsiders: int = 0
    minions: int = 0
    demons: int = 0
    chef_pairs: int = 0
    first_registers_evil: bool | None = None
    previous_registers_evil: bool = False
    spy_count: int = 0
    recluse_count: int = 0
    chef_players: int = 0

SPY_CANDIDATE_ROLES = {
    Role.SPY,
    Role.ANY_OTHER_MINION,
    Role.ANY_OTHER_EVIL,
    Role.NON_DEMON,
    Role.ANY_OTHER,
}

RECLUSE_CANDIDATE_ROLES = {
    Role.RECLUSE,
    Role.ANY_OTHER_OUTSIDER,
    Role.ANY_OTHER_GOOD,
    Role.NON_DEMON,
    Role.ANY_OTHER,
}

def _is_assignment_possible(
    page: GrimoirePage,
    *,
    townsfolk: int,
    outsiders: int,
    minions: int,
    demons: int,
) -> bool:
    target = (
        townsfolk,
        outsiders,
        minions,
        demons,
    )
    states = {_AssignmentState()}

    for player, character in enumerate(page.characters):
        next_states: set[_AssignmentState] = set()

        options = _get_role_assignment_options(
            page,
            player,
            character,
        )

        for state in states:
            for option in options:
                new_state = _apply_assignment_option(
                    state,
                    option,
                    player,
                )

                if _state_can_reach_target(
                    new_state,
                    target,
                    page.chef_number,
                ):
                    next_states.add(new_state)

        if not next_states:
            return False

        states = next_states

    return any(
        _is_final_assignment_valid(
            page,
            state,
            target,
        )
        for state in states
    )

def _get_role_assignment_options(
    page: GrimoirePage,
    player: int,
    character: Role,
) -> tuple[_RoleAssignmentOption, ...]:
    options: set[_RoleAssignmentOption] = set()

    spy_possible = (
        character == Role.SPY
        or (
            Role.SPY not in page.characters
            and (
                Role.SPY in page.minion_types
                or Role.ANY_OTHER_MINION in page.minion_types
            )
        )
    )

    for possible_type in get_possible_types(character):
        if possible_type == CharacterType.TOWNSFOLK:
            options.add(
                _RoleAssignmentOption(
                    CharacterType.TOWNSFOLK,
                    registers_evil=False,
                )
            )

        elif possible_type == CharacterType.OUTSIDER:
            if character != Role.RECLUSE:
                options.add(
                    _RoleAssignmentOption(
                        CharacterType.OUTSIDER,
                        registers_evil=False,
                    )
                )

            if character in RECLUSE_CANDIDATE_ROLES:
                options.add(
                    _RoleAssignmentOption(
                        CharacterType.OUTSIDER,
                        registers_evil=False,
                        is_recluse=True,
                    )
                )
                options.add(
                    _RoleAssignmentOption(
                        CharacterType.OUTSIDER,
                        registers_evil=True,
                        is_recluse=True,
                    )
                )

        elif possible_type == CharacterType.MINION:
            if character != Role.SPY:
                options.add(
                    _RoleAssignmentOption(
                        CharacterType.MINION,
                        registers_evil=True,
                    )
                )

            if (
                spy_possible
                and character in SPY_CANDIDATE_ROLES
            ):
                options.add(
                    _RoleAssignmentOption(
                        CharacterType.MINION,
                        registers_evil=False,
                        is_spy=True,
                    )
                )
                options.add(
                    _RoleAssignmentOption(
                        CharacterType.MINION,
                        registers_evil=True,
                        is_spy=True,
                    )
                )

        elif possible_type == CharacterType.DEMON:
            options.add(
                _RoleAssignmentOption(
                    CharacterType.DEMON,
                    registers_evil=True,
                )
            )

    if page.in_chef_pair & (1 << player):
        options = {
            option
            for option in options
            if option.registers_evil
        }

    return tuple(options)

def _apply_assignment_option(
    state: _AssignmentState,
    option: _RoleAssignmentOption,
    player: int,
) -> _AssignmentState:
    townsfolk = state.townsfolk
    outsiders = state.outsiders
    minions = state.minions
    demons = state.demons

    if option.character_type == CharacterType.TOWNSFOLK:
        townsfolk += 1
    elif option.character_type == CharacterType.OUTSIDER:
        outsiders += 1
    elif option.character_type == CharacterType.MINION:
        minions += 1
    elif option.character_type == CharacterType.DEMON:
        demons += 1

    chef_pairs = state.chef_pairs
    chef_players = state.chef_players

    if (
        player > 0
        and state.previous_registers_evil
        and option.registers_evil
    ):
        chef_pairs += 1
        chef_players |= 1 << (player - 1)
        chef_players |= 1 << player

    first_registers_evil = state.first_registers_evil
    if player == 0:
        first_registers_evil = option.registers_evil

    return _AssignmentState(
        townsfolk=townsfolk,
        outsiders=outsiders,
        minions=minions,
        demons=demons,
        chef_pairs=chef_pairs,
        first_registers_evil=first_registers_evil,
        previous_registers_evil=option.registers_evil,
        spy_count=state.spy_count + option.is_spy,
        recluse_count=state.recluse_count + option.is_recluse,
        chef_players=chef_players,
    )

def _state_can_reach_target(
    state: _AssignmentState,
    target: tuple[int, int, int, int],
    chef_number: int | None,
) -> bool:
    counts = (
        state.townsfolk,
        state.outsiders,
        state.minions,
        state.demons,
    )

    if any(
        count > maximum
        for count, maximum in zip(counts, target)
    ):
        return False

    if state.spy_count > 1:
        return False

    if state.recluse_count > 1:
        return False

    if (
        chef_number is not None
        and state.chef_pairs > chef_number
    ):
        return False

    return True

def _is_final_assignment_valid(
    page: GrimoirePage,
    state: _AssignmentState,
    target: tuple[int, int, int, int],
) -> bool:
    counts = (
        state.townsfolk,
        state.outsiders,
        state.minions,
        state.demons,
    )
    if counts != target:
        return False

    if state.spy_count > 1:
        return False

    if state.recluse_count > 1:
        return False

    if page.recluse_needed and state.recluse_count == 0:
        return False

    chef_pairs = state.chef_pairs
    chef_players = state.chef_players

    if (
        state.first_registers_evil
        and state.previous_registers_evil
    ):
        chef_pairs += 1
        chef_players |= 1
        chef_players |= 1 << (page.num_players - 1)

    if (
        page.chef_number is not None
        and chef_pairs != page.chef_number
    ):
        return False

    if page.in_chef_pair & ~chef_players:
        return False

    if page.not_in_chef_pair & chef_players:
        return False

    return True

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
    if len([c for c in dead_characters if c in EVIL_ROLES]) == gamerules.get_minion_count(num_players):
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

    known_outsiders = 0
    non_outsiders = 0
    known_evil_count = 0
    for i, c in enumerate(characters):
        if c in GENERIC_OUTSIDER_SET:
            known_outsiders += 1
        if c not in OUTSIDERS_OR_UNKNOWN:
            non_outsiders += 1
        if c in EVIL_ROLES_SET:
            known_evil_count += 1

    evil_count = gamerules.get_evil_count(num_players)
    room_for_outsiders = num_players - non_outsiders - (evil_count - known_evil_count)

    baron_possible = Role.BARON in minion_types or Role.ANY_OTHER_MINION in minion_types
    max_outsiders = gamerules.get_outsider_count(num_players, baron_possible)
    if max_outsiders > room_for_outsiders:
        baron_possible = False
        max_outsiders = gamerules.get_outsider_count(num_players, False)
    outsiders_known = known_outsiders == max_outsiders
    recluse_known = Role.RECLUSE in characters

    # Precompute predicates for each character
    definitely_evil: set[int] = set()
    possibly_evil: set[int] = set()
    could_be_recluse: set[int] = set()
    evil_could_be_spy: set[int] = set()

    for i, role in enumerate(characters):
        if role == Role.SPY:
            evil_could_be_spy.add(i)
        elif role in EVIL_CHARACTERS:
            definitely_evil.add(i)
        elif not spy_possible and role in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]:
            definitely_evil.add(i)
        elif role in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]:
            evil_could_be_spy.add(i)
        elif role == Role.RECLUSE:
            could_be_recluse.add(i)
        elif not outsiders_known and not recluse_known and role in [Role.ANY_OTHER, Role.NON_DEMON]:
            possibly_evil.add(i)
            could_be_recluse.add(i)
        elif role in NONDEMON_OR_ANY:
            possibly_evil.add(i)
        elif not recluse_known and role == Role.ANY_OTHER_OUTSIDER:
            could_be_recluse.add(i)
        elif not outsiders_known and not recluse_known and role == Role.ANY_OTHER_GOOD:
            could_be_recluse.add(i)

    possible_spies = set(evil_could_be_spy)

    if spy_possible:
        possible_spies.update(possibly_evil)

    known_evils = definitely_evil | evil_could_be_spy

    minion_only_positions = {
        i
        for i, role in enumerate(characters)
        if (
            role == Role.NON_DEMON
            or role in GENERIC_MINION_SET
        )
    }

    min_pairs = _get_min_pairs_from_positions(
        known_evils,
        possible_spies,
        possibly_evil,
        num_players,
        evil_count
    )

    max_pairs = _get_max_pairs_from_positions(
        possible_evils=possibly_evil,
        known_evils=known_evils,
        recluse_positions=could_be_recluse,
        minion_only_positions=minion_only_positions,
        num_players=num_players,
        max_evils=evil_count,
        max_minions=gamerules.get_minion_count(num_players),
    )

    return min_pairs <= chef_number <= max_pairs

def _get_min_pairs_from_positions(
    known_evils: set[int], 
    possible_spies: set[int], 
    possible_evils: set[int], 
    num_players: int, 
    evil_count: int
):
    """
    known_evils and possible_evils are mutually exclusive
    known evils contains all of possible_spies
    """
    result = helper.minimum_possible_runs_with_one_remove(
            known=known_evils,
            possible=possible_evils,
            remove_nums=possible_spies,
            count=evil_count,
            upper_bound=num_players,
        )
    
    if result is None:
        return math.inf 
    _, total, _, _, _ = result
    return total

def _get_max_pairs_from_positions(
    possible_evils: set[int],
    known_evils: set[int],
    recluse_positions: set[int],
    minion_only_positions: set[int],
    num_players: int,
    max_evils: int,
    max_minions: int,
) -> int:
    try:
        _, total, _, _, _ = helper.maximum_possible_runs(
            known=known_evils,
            possible=possible_evils,
            count=max_evils,
            upper_bound=num_players,
            insert_nums=recluse_positions,
            constrained_positions=minion_only_positions,
            max_constrained=max_minions,
        )
    except ValueError:
        # There is no valid assignment of roles for this page.
        return -1

    return total

EVIL_PLAYERS_WITHOUT_SPY = EVIL_ROLES_SET - {Role.SPY}

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

def _is_outsider_count_valid(page: GrimoirePage) -> bool:
    return is_outsider_count_valid(page, page.num_players)

def _is_evil_count_valid(page: GrimoirePage) -> bool:
    return is_evil_count_valid(page, page.num_players)

def _is_good_count_valid(page: GrimoirePage) -> bool:
    return is_good_count_valid(page, page.num_players)

def _is_poisoning_valid(page: GrimoirePage) -> bool:
    return is_poisoning_valid(page, page.num_players)

OUTSIDER_COUNT_VALIDATOR = Validator(
    _is_outsider_count_valid,
    "invalid outsider count",
    frozenset({
        ChangeType.CHARACTER,
        ChangeType.MINION_TYPE,
        ChangeType.LIBRARIAN_NO
    })
)

EVIL_COUNT_VALIDATOR = Validator(
    _is_evil_count_valid,
    "invalid evil count",
    frozenset({
        ChangeType.CHARACTER,
        ChangeType.DEATH
    })
)

GOOD_COUNT_VALIDATOR = Validator(
    _is_good_count_valid,
    "invalid good count",
    frozenset({
        ChangeType.CHARACTER
    })
)

ROLE_BREAKDOWN_VALIDATOR = Validator(
    is_role_breakdown_valid,
    "invalid ocmbined evil count and outsider count",
    frozenset({
        ChangeType.CHARACTER,
        ChangeType.MINION_TYPE
    })
)

ROLE_ASSIGNMENT_VALIDATOR = Validator(
    is_role_assignment_valid,
    "invalid combined role assigment and chef number",
    frozenset({
        ChangeType.CHARACTER,
        ChangeType.MINION_TYPE,
        ChangeType.CHEF_NUMBER
    })
)

MINION_TYPE_VALIDATOR = Validator(
    are_minion_types_valid,
    "invalid minion types",
    frozenset({
        ChangeType.CHARACTER,
        ChangeType.MINION_TYPE
    })
)

POISONING_VALIDATOR = Validator(
    _is_poisoning_valid,
    "invalid poisoning",
    frozenset({
        ChangeType.POISONED,
        ChangeType.MINION_TYPE,
        ChangeType.CHARACTER,
        ChangeType.DEATH
    })
)

DUPLICATES_VALIDATOR = Validator(
    is_no_invalid_duplicates,
    "invalid duplicates",
    frozenset({
        ChangeType.CHARACTER
    })
)

SAINT_EXECUTION_VALIDATOR = Validator(
    is_no_sober_saint_executed,
    "sober Saint executed",
    frozenset({
      ChangeType.NIGHT_ORDER,
      ChangeType.EXECUTEE,
      ChangeType.CHARACTER,
      ChangeType.POISONED  
    })
)

CHEF_NUMBER_VALIDATOR = Validator(
    is_chef_number_valid,
    "invalid chef number",
    frozenset({
        ChangeType.CHEF_NUMBER,
        ChangeType.CHARACTER,
        ChangeType.MINION_TYPE
    })
)

RED_HERRING_VALIDATOR = Validator(
    is_red_herring_valid,
    "invalid red herring",
    frozenset({
        ChangeType.RED_HERRING,
        ChangeType.CHARACTER
    })
)

ALL_VALIDATORS = (
    OUTSIDER_COUNT_VALIDATOR,
    EVIL_COUNT_VALIDATOR,
    GOOD_COUNT_VALIDATOR,
    MINION_TYPE_VALIDATOR,
    POISONING_VALIDATOR,
    DUPLICATES_VALIDATOR,
    SAINT_EXECUTION_VALIDATOR,
    RED_HERRING_VALIDATOR,
    ROLE_BREAKDOWN_VALIDATOR,
    CHEF_NUMBER_VALIDATOR,
    ROLE_ASSIGNMENT_VALIDATOR,
)

FIRST_NIGHT_VALIDATORS = (
    OUTSIDER_COUNT_VALIDATOR,
    ROLE_BREAKDOWN_VALIDATOR,
    CHEF_NUMBER_VALIDATOR,
    ROLE_ASSIGNMENT_VALIDATOR,
)

FULL_PAGE_VALIDATORS = (
    OUTSIDER_COUNT_VALIDATOR,
    EVIL_COUNT_VALIDATOR,
    GOOD_COUNT_VALIDATOR,
    MINION_TYPE_VALIDATOR,
    POISONING_VALIDATOR,
    DUPLICATES_VALIDATOR,
    SAINT_EXECUTION_VALIDATOR,
    RED_HERRING_VALIDATOR,
    CHEF_NUMBER_VALIDATOR,
)

def get_affected_validators(change_type: ChangeType) -> tuple[Validator, ...]:
    return tuple(
        validator
        for validator in FULL_PAGE_VALIDATORS
        if change_type in validator.affected_by
    )

def run_validators(page: GrimoirePage, validators: tuple[Validator, ...]) -> tuple[bool, str]:
    is_first_night = gamerules.is_first_night_setup_page(page)
    for validator in validators:
        if not is_first_night and validator in FIRST_NIGHT_VALIDATORS:
            continue
        if not validator.validate(page):
            return False, validator.reason
    return True, ""

def is_page_valid(page: GrimoirePage) -> tuple[bool, str]:
    return run_validators(page, FULL_PAGE_VALIDATORS)

def is_grim_valid(grim: Grimoire) -> tuple[bool, str]:
    for page in grim.pages:
        valid, reason = is_page_valid(page)
        if not valid:
            return False, reason
    return True, ""
