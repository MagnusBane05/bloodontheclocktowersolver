from itertools import combinations
from typing import NamedTuple, TYPE_CHECKING

from . import gamerules
from .character_type import CharacterType
from .role import *
from .chef_pair import ChefPair, is_chef_pair_combination_valid

if TYPE_CHECKING:
    from . import GrimoirePage

DEDUCIBLE_UNKNOWN_ROLES = {
    Role.ANY_OTHER,
    Role.NON_DEMON,
}

class _ChefPossibilities(NamedTuple):
    spy_possible: bool
    recluse_possible: bool
    evils_available: int
    new_outsider_possible: bool
    new_outsider_needs_baron: bool
    spy_and_new_outsider_possible: bool

def _get_chef_possibilities(page: GrimoirePage) -> _ChefPossibilities:
    spy_possible = (
        Role.SPY not in page.characters
        and (
            Role.SPY in page.minion_types
            or Role.ANY_OTHER_MINION in page.minion_types
        )
    )
    baron_possible = (
        Role.BARON in page.minion_types
        or Role.ANY_OTHER_MINION in page.minion_types
    )
    recluse_possible = (
        Role.RECLUSE not in page.characters
        and gamerules.get_outsider_count(page.num_players, baron_possible) > 0
    )
    evil_count = page.get_evil_count()
    evils_available = gamerules.get_evil_count(page.num_players) - evil_count
    outsider_count = sum(1 for c in page.characters if c in GENERIC_OUTSIDER_SET)
    new_outsider_possible = (
        gamerules.get_outsider_count(page.num_players, baron_possible)
        >= outsider_count + 1
    )
    new_outsider_needs_baron = (
        gamerules.get_outsider_count(page.num_players, False) < outsider_count + 1
    )
    spy_and_new_outsider_possible = (
        new_outsider_possible
        and (
            Role.SPY in page.minion_types
            or (
                Role.BARON in page.minion_types
                or not new_outsider_needs_baron
                or page.minion_types.count(Role.ANY_OTHER_MINION) >= 2
            )
        )
    )
    return _ChefPossibilities(
        spy_possible,
        recluse_possible,
        evils_available,
        new_outsider_possible,
        new_outsider_needs_baron,
        spy_and_new_outsider_possible,
    )

def _is_known_non_spy_evil(character: Role, spy_possible: bool) -> bool:
    return (
        character in NON_SPY_EVIL_CHARACTERS
        or (
            not spy_possible
            and character != Role.SPY
            and character in EVIL_ROLES_SET
        )
    )

def _can_be_recluse(
    character: Role,
    recluse_possible: bool,
    new_outsider_possible: bool,
) -> bool:
    return (
        character == Role.RECLUSE
        or (
            recluse_possible
            and (
                character == Role.ANY_OTHER_OUTSIDER
                or (
                    new_outsider_possible
                    and character == Role.ANY_OTHER_GOOD
                )
            )
        )
    )

def _can_be_spy(
    character: Role,
    spy_possible: bool,
    *,
    allow_any_evil_role: bool,
) -> bool:
    if character == Role.SPY:
        return True
    if not spy_possible:
        return False
    if allow_any_evil_role:
        return character in EVIL_ROLES_SET
    return character in (
        Role.ANY_OTHER_MINION,
        Role.ANY_OTHER_EVIL,
    )

def _classify_pair_with_known_evil_partner(
    player: int,
    partner: int,
    character: Role,
    character_unknown: bool,
    possibilities: _ChefPossibilities,
) -> tuple[ChefPair, bool] | None:
    if _is_known_non_spy_evil(character, possibilities.spy_possible):
        return (
            ChefPair(
                player,
                partner,
                a_evil=True,
                b_evil=True,
            ),
            True,
        )
    if _can_be_spy(
        character,
        possibilities.spy_possible,
        allow_any_evil_role=True,
    ):
        return (
            ChefPair(
                player,
                partner,
                a_spy=True,
                b_evil=True,
            ),
            False,
        )
    if _can_be_recluse(
        character,
        possibilities.recluse_possible,
        possibilities.new_outsider_possible,
    ):
        return (
            ChefPair(
                player,
                partner,
                a_recluse=True,
                b_evil=True,
            ),
            False,
        )
    if not character_unknown:
        return None
    if possibilities.evils_available >= 1:
        return (
            ChefPair(
                player,
                partner,
                a_unknown=True,
                b_evil=True,
            ),
            False,
        )
    if (
        possibilities.recluse_possible
        and possibilities.new_outsider_possible
    ):
        return (
            ChefPair(
                player,
                partner,
                a_recluse=True,
                b_evil=True,
            ),
            False,
        )
    return None

def _classify_pair_with_possible_spy_partner(
    player: int,
    partner: int,
    character: Role,
    character_unknown: bool,
    possibilities: _ChefPossibilities,
) -> tuple[ChefPair, bool] | None:
    if _is_known_non_spy_evil(character, possibilities.spy_possible):
        return (
            ChefPair(
                player,
                partner,
                a_evil=True,
                b_spy=True,
            ),
            False,
        )
    if _can_be_spy(
        character,
        possibilities.spy_possible,
        allow_any_evil_role=False,
    ):
        return (
            ChefPair(
                player,
                partner,
                a_spy=True,
                b_spy=True,
            ),
            False,
        )
    if _can_be_recluse(
        character,
        possibilities.recluse_possible,
        possibilities.new_outsider_possible,
    ):
        if possibilities.spy_and_new_outsider_possible:
            return (
                ChefPair(
                    player,
                    partner,
                    a_recluse=True,
                    b_spy=True,
                ),
                False,
            )
        return (
            ChefPair(
                player,
                partner,
                a_recluse=True,
                b_evil=True,
            ),
            False,
        )
    if not character_unknown:
        return None
    if possibilities.evils_available >= 1:
        return (
            ChefPair(
                player,
                partner,
                a_unknown=True,
                b_spy=True,
            ),
            False,
        )
    if (
        possibilities.recluse_possible
        and possibilities.new_outsider_possible
    ):
        return (
            ChefPair(
                player,
                partner,
                a_recluse=True,
                b_spy=True,
            ),
            False,
        )
    return None

def _classify_pair_with_possible_recluse_partner(
    player: int,
    partner: int,
    character: Role,
    character_unknown: bool,
    possibilities: _ChefPossibilities,
) -> tuple[ChefPair, bool] | None:
    if _is_known_non_spy_evil(character, possibilities.spy_possible):
        return (
            ChefPair(
                player,
                partner,
                a_evil=True,
                b_recluse=True,
            ),
            False,
        )
    if _can_be_spy(
        character,
        possibilities.spy_possible,
        allow_any_evil_role=False,
    ):
        return (
            ChefPair(
                player,
                partner,
                a_spy=True,
                b_recluse=True,
            ),
            False,
        )
    if character_unknown and possibilities.evils_available >= 1:
        return (
            ChefPair(
                player,
                partner,
                a_unknown=True,
                b_recluse=True,
            ),
            False,
        )
    return None

def _classify_pair_with_unknown_partner(
    player: int,
    partner: int,
    character: Role,
    character_unknown: bool,
    possibilities: _ChefPossibilities,
) -> tuple[ChefPair, bool] | None:
    if _is_known_non_spy_evil(character, possibilities.spy_possible):
        return (
            ChefPair(
                player,
                partner,
                a_evil=True,
                b_unknown=True,
            ),
            False,
        )
    if _can_be_spy(
        character,
        possibilities.spy_possible,
        allow_any_evil_role=False,
    ):
        return (
            ChefPair(
                player,
                partner,
                a_spy=True,
                b_unknown=True,
            ),
            False,
        )
    if _can_be_recluse(
        character,
        possibilities.recluse_possible,
        possibilities.new_outsider_possible,
    ):
        return (
            ChefPair(
                player,
                partner,
                a_recluse=True,
                b_unknown=True,
            ),
            False,
        )

    # Both players could be evil or Recluse
    if character_unknown:
        evil_and_recluse_possible = (
            possibilities.evils_available == 1
            and possibilities.recluse_possible
            and possibilities.new_outsider_possible
        )
        if possibilities.evils_available >= 2 or evil_and_recluse_possible:
            return (
                ChefPair(
                    player,
                    partner,
                    a_unknown=True,
                    b_unknown=True,
                ),
                False,
            )
    return None

def _classify_chef_pair(
    page: GrimoirePage,
    player: int,
    partner: int,
    possibilities: _ChefPossibilities,
) -> tuple[ChefPair, bool] | None:
    """
    Returns (pair, is_known), or None if this orientation cannot
    produce a Chef pair.
    """
    a = page.characters[player]
    b = page.characters[partner]
    a_unknown = a in DEDUCIBLE_UNKNOWN_ROLES

    # Partner is definitely evil
    if _is_known_non_spy_evil(b, possibilities.spy_possible):
        return _classify_pair_with_known_evil_partner(
            player,
            partner,
            a,
            a_unknown,
            possibilities,
        )

    # Partner is evil and possible Spy.
    if b == Role.SPY or b in EVIL_ROLES_SET:
        return _classify_pair_with_possible_spy_partner(
            player,
            partner,
            a,
            a_unknown,
            possibilities,
        )

    # Partner is possibly Recluse
    if _can_be_recluse(
        b,
        possibilities.recluse_possible,
        possibilities.new_outsider_possible,
    ):
        return _classify_pair_with_possible_recluse_partner(
            player,
            partner,
            a,
            a_unknown,
            possibilities,
        )

    if b in DEDUCIBLE_UNKNOWN_ROLES:
        return _classify_pair_with_unknown_partner(
            player,
            partner,
            a,
            a_unknown,
            possibilities,
        )
    return None

def _get_chef_pairs(
    page: GrimoirePage,
    possibilities: _ChefPossibilities,
) -> tuple[list[ChefPair], list[ChefPair]]:
    known_pairs: list[ChefPair] = []
    possible_pairs: list[ChefPair] = []

    for player in range(page.num_players):
        partner = (player + 1) % page.num_players
        result = _classify_chef_pair(
            page,
            player,
            partner,
            possibilities,
        )
        if result is None:
            continue
        pair, is_known = result
        if is_known:
            known_pairs.append(pair)
        else:
            possible_pairs.append(pair)
    return known_pairs, possible_pairs

def _is_spy_needed(
    page: GrimoirePage,
    pair: ChefPair,
) -> tuple[bool, bool]:
    """
    Returns is_spy_needed, is_spy_found
    """
    # Either player could be the Spy
    if pair.a_spy and pair.b_spy:
        return True, False
    # B has to be the Spy
    if pair.a_evil and pair.b_spy:
        page.characters[pair.b] = Role.SPY
        page.add_minion_type(Role.SPY)
        return False, True
    # A has to be the Spy
    if pair.b_evil and pair.a_spy:
        page.characters[pair.a] = Role.SPY
        page.add_minion_type(Role.SPY)
        return False, True
    return False, False

def _handle_pair_not_in_chef_number(
    page: GrimoirePage,
    pair: ChefPair,
    spy_possible: bool,
) -> bool:
    if spy_possible:
        return False
    # B has to be good
    if pair.a_evil and pair.b_unknown:
        page.characters[pair.b] = Role.ANY_OTHER_GOOD
        return True
    # A has to be good
    if pair.b_evil and pair.a_unknown:
        page.characters[pair.a] = Role.ANY_OTHER_GOOD
        return True
    return False

def _add_baron_if_needed(page: GrimoirePage, player: int) -> None:
    if Role.BARON in page.minion_types:
        return
    if page.characters[player] in GENERIC_OUTSIDER_SET:
        return
    outsider_count = page.get_characters_of_type(CharacterType.OUTSIDER)
    max_outsider_count = gamerules.get_outsider_count(page.num_players, False)
    if outsider_count + 1 > max_outsider_count:
        page.add_minion_type(Role.BARON)

def _handle_unknown_player_in_chef_number(
    page: GrimoirePage,
    player: int
) -> bool:
    if not page.can_be_character(Role.RECLUSE, player):
        return page.apply_character(Role.ANY_OTHER_EVIL, player)

    mask = 1 << player
    if page.in_chef_pair & mask:
        return False

    page.in_chef_pair |= mask
    return True

def _handle_pair_in_chef_number(
    page: GrimoirePage,
    pair: ChefPair,
) -> bool:
    deduced = False
    # B has to be the Recluse
    if pair.b_recluse: # I don't think it's possible for a_recluse and b_recluse to be contributing to a Chef number
        _add_baron_if_needed(page, pair.b)
        page.characters[pair.b] = Role.RECLUSE
        deduced = True
    # A has to be the Recluse
    if pair.a_recluse: # I don't think it's possible for a_recluse and b_recluse to be contributing to a Chef number
        _add_baron_if_needed(page, pair.a)
        page.characters[pair.a] = Role.RECLUSE
        deduced = True
    # A could be the Recluse or evil
    if pair.a_unknown:
        deduced |= _handle_unknown_player_in_chef_number(page, pair.a)
    # B could be the Recluse or evil
    if pair.b_unknown:
        deduced |= _handle_unknown_player_in_chef_number(page, pair.b)
    return deduced

def _handle_player_in_chef_number(
    page: GrimoirePage,
    player: int,
    character: Role,
) -> bool:
    if character in (Role.ANY_OTHER_OUTSIDER, Role.ANY_OTHER_GOOD):
        _add_baron_if_needed(page, player)
        page.characters[player] = Role.RECLUSE
        return True

    if character in DEDUCIBLE_UNKNOWN_ROLES:
        return _handle_unknown_player_in_chef_number(page, player)

    return False

def _is_recluse_needed(
    page: GrimoirePage,
    pair_combinations: list[tuple[ChefPair, ...]],
) -> bool:
    evil_count = gamerules.get_evil_count(page.num_players)
    known_evils = {
        i
        for i, c in enumerate(page.characters)
        if c in EVIL_ROLES_SET
    }
    for pairs in pair_combinations:
        combination_needs_recluse = False
        unknowns: set[int] = set()
        evils = known_evils.copy()
        for pair in pairs:
            if pair.a_recluse or pair.b_recluse:
                combination_needs_recluse = True
                break
            if pair.a_unknown:
                unknowns.add(pair.a)
            if pair.b_unknown:
                unknowns.add(pair.b)
            if pair.a_evil or pair.a_spy:
                evils.add(pair.a)
            if pair.b_evil or pair.b_spy:
                evils.add(pair.b)
        if not (
            combination_needs_recluse
            or len(unknowns) + len(evils) > evil_count
        ):
            return False
    return True

def _deduce_from_fully_explained_chef_number(
    page: GrimoirePage,
    possible_pairs: list[ChefPair],
    spy_possible: bool,
) -> bool:
    deduced = False
    spy_candidates: list[ChefPair] = []
    spy_found = False
    for pair in possible_pairs:
        spy_needed, spy_in_pair = _is_spy_needed(page, pair)
        spy_found |= spy_in_pair
        if spy_needed and not spy_found:
            spy_candidates.append(pair)
        if not spy_needed and not spy_in_pair:
            deduced |= _handle_pair_not_in_chef_number(
                page,
                pair,
                spy_possible,
            )
    deduced |= spy_found
    if len(spy_candidates) > 1:
        candidates = {
            player
            for pair in spy_candidates
            for player in (pair.a, pair.b)
        }
        for spy_candidate in candidates:
            if all(
                spy_candidate in (pair.a, pair.b)
                for pair in spy_candidates
            ):
                page.characters[spy_candidate] = Role.SPY
                page.add_minion_type(Role.SPY)
                deduced = True
    return deduced

def _get_valid_pair_combinations(
    possible_pairs: list[ChefPair],
    effective_chef_number: int,
    num_players: int,
) -> list[tuple[ChefPair, ...]]:
    return [
        combination
        for combination in combinations(possible_pairs, effective_chef_number)
        if is_chef_pair_combination_valid(combination, num_players)
    ]

def _deduce_recluse_needed(
    page: GrimoirePage,
    chef_number: int,
    pair_combinations: list[tuple[ChefPair, ...]],
    new_outsider_needs_baron: bool,
) -> bool:
    recluse_needed = _is_recluse_needed(page, pair_combinations)
    if not (
        (
            recluse_needed
            or chef_number == gamerules.get_evil_count(page.num_players)
        )
        and Role.RECLUSE not in page.characters
    ):
        return False

    page.recluse_needed = True
    if (
        Role.BARON not in page.minion_types
        and Role.ANY_OTHER_OUTSIDER not in page.characters
        and new_outsider_needs_baron
    ):
        page.add_minion_type(Role.BARON)
    return True

def _deduce_pairs_in_all_combinations(
    page: GrimoirePage,
    possible_pairs: list[ChefPair],
    pair_combinations: list[tuple[ChefPair, ...]],
) -> bool:
    deduced = False
    for pair in possible_pairs:
        a, b = pair.a, pair.b
        if all(
            any({p.a, p.b} == {a, b} for p in pairs)
            for pairs in pair_combinations
        ):
            deduced |= _handle_pair_in_chef_number(
                page,
                pair,
            )
    return deduced

def _deduce_players_in_all_combinations(
    page: GrimoirePage,
    pair_combinations: list[tuple[ChefPair, ...]],
) -> bool:
    deduced = False
    for player in range(page.num_players):
        if all(
            player == pair.a or player == pair.b
            for pairs in pair_combinations
            for pair in pairs
        ):
            deduced |= _handle_player_in_chef_number(
                page,
                player,
                page.characters[player],
            )
    return deduced

def _deduce_spy_between_evils(
    page: GrimoirePage,
    possible_pairs: list[ChefPair],
    chef_number: int,
) -> bool:
    deduced = False
    for pair in possible_pairs:
        if not (
            pair.a_evil and pair.b_spy
            or (pair.b_evil and pair.a_spy)
        ):
            continue
        for other in possible_pairs:
            if pair == other:
                continue
            if not (
                other.a_evil and other.b_spy
                or (other.b_evil and other.a_spy)
            ):
                continue
            pair_spy = pair.a if pair.a_spy else pair.b
            other_spy = other.a if other.a_spy else other.b
            if pair_spy != other_spy:
                continue
            # Spy is sitting between two evils
            if chef_number < 2 and page.characters[pair_spy] != Role.SPY:
                page.characters[pair_spy] = Role.SPY
                page.add_minion_type(Role.SPY)
                deduced = True
    return deduced

def _deduce_from_possible_chef_pairs(
    page: GrimoirePage,
    chef_number: int,
    known_pairs: list[ChefPair],
    possible_pairs: list[ChefPair],
    possibilities: _ChefPossibilities,
) -> bool:
    deduced = False
    effective_chef_number = chef_number - len(known_pairs) 
    if effective_chef_number < 0:
        return False
    pair_combinations = _get_valid_pair_combinations(
        possible_pairs,
        effective_chef_number,
        page.num_players,
    )
    # case where recluse is needed and baron is needed for that recluse
    deduced |= _deduce_recluse_needed(
        page,
        chef_number,
        pair_combinations,
        possibilities.new_outsider_needs_baron,
    )
    # any pair that exists in all possible combinations must be in the chef number
    deduced |= _deduce_pairs_in_all_combinations(
        page,
        possible_pairs,
        pair_combinations,
    )
    # any player that is in all pairs in all combinations must be in the chef number
    deduced |= _deduce_players_in_all_combinations(
        page,
        pair_combinations,
    )
    # if an evil is between two non-Spies and the Chef number is less than 2, that player must be the Spy
    deduced |= _deduce_spy_between_evils(
        page,
        possible_pairs,
        chef_number,
    )
    return deduced

def deduce_from_chef_number(page: GrimoirePage) -> bool:
    chef_number = page.chef_number
    if chef_number is None:
        return False

    possibilities = _get_chef_possibilities(page)
    known_pairs, possible_pairs = _get_chef_pairs(page, possibilities)

    # All pairs explained by definite pairs, possible pairs can't be contributing to the number
    if len(known_pairs) == chef_number:
        return _deduce_from_fully_explained_chef_number(
            page,
            possible_pairs,
            possibilities.spy_possible,
        )

    # Not all pairs explained by definite pairs, some possible pairs must contribute to the number
    return _deduce_from_possible_chef_pairs(
        page,
        chef_number,
        known_pairs,
        possible_pairs,
        possibilities,
    )
