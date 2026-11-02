import math

from grimoire.role import DEMONS, EVIL_CHARACTERS, GOOD_CHARACTERS, MINIONS, OUTSIDERS, TOWNSFOLK, Role, get_overlapping
from itertools import combinations


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

def wrapped_consecutive_subsets(nums: set[int], upper_bound: int) -> list[list[int]]:
    if not nums:
        return []
    if any(n < 0 or n >= upper_bound for n in nums):
        raise ValueError(f"All numbers must be in range 0 to {upper_bound - 1}")
    if len(nums) == upper_bound:
        return [list(range(upper_bound))]

    subsets: list[list[int]] = []
    for n in nums:
        prev_n = (n - 1) % upper_bound
        if prev_n not in nums:
            current: list[int] = []
            x = n
            while x in nums:
                current.append(x)
                x = (x + 1) % upper_bound
            subsets.append(current)

    return sorted(subsets, key=len, reverse=True)

def longest_runs_with_one_insert(
    nums: set[int],
    insert_nums: set[int],
    upper_bound: int,
) -> tuple[list[list[int]], int, int | None, set[int]]:
    best_runs: list[list[int]] = []
    best_candidate: int | None = None
    best_total: int = 0
    best_selected: set[int] = set()

    # Try using no inserted number
    candidates: list[int | None] = [None] + list(insert_nums)
    for candidate in candidates:
        if candidate is None:
            combined = nums
        else:
            combined = nums | {candidate}
        runs = wrapped_consecutive_subsets(combined, upper_bound)
        total = 0
        filtered_runs: list[list[int]] = []
        selected: set[int] = set()
        for run in runs:
            if len(run) <= 1:
                continue
            length = len(run) - 1
            total += length
            filtered_runs.append(run)
            selected = selected.union(run)
        if runs and total > best_total:
            best_runs = filtered_runs
            best_candidate = candidate
            best_total = total
            best_selected = selected

    return best_runs, best_total, best_candidate, best_selected

def wrapped_pair_count(nums: set[int], upper_bound: int) -> int:
    return sum(
        (position + 1) % upper_bound in nums
        for position in nums
    )

def maximum_possible_runs(
    known: set[int],
    possible: set[int],
    count: int,
    upper_bound: int,
    *,
    insert_nums: set[int] | None = None,
    constrained_positions: set[int] | None = None,
    max_constrained: int | None = None,
) -> tuple[
    list[list[int]],
    int,
    set[int],
    set[int],
    int | None,
]:
    """
    Select exactly `count` positions from `known | possible` while
    maximizing the number of wrapped adjacent pairs.

    `known` positions are always selected.

    At most one position from `insert_nums` may be added for scoring,
    but it does not count toward `count`. This represents the Recluse.

    At most `max_constrained` selected positions may come from
    `constrained_positions`. This can represent positions that must
    consume a minion slot when selected as evil.
    """
    known = set(known)
    possible = set(possible)
    insert_nums = set() if insert_nums is None else set(insert_nums)
    constrained_positions = (
        set()
        if constrained_positions is None
        else set(constrained_positions)
    )

    if known & possible:
        raise ValueError("known and possible must not overlap")

    all_positions = (
        known
        | possible
        | insert_nums
        | constrained_positions
    )

    if any(
        position < 0 or position >= upper_bound
        for position in all_positions
    ):
        raise ValueError(
            f"All positions must be in range 0 to {upper_bound - 1}"
        )

    needed_from_possible = count - len(known)

    if needed_from_possible < 0:
        raise ValueError("count cannot be smaller than len(known)")

    if needed_from_possible > len(possible):
        raise ValueError(
            "Not enough possible positions to reach count"
        )

    if (
        max_constrained is not None
        and len(known & constrained_positions) > max_constrained
    ):
        raise ValueError(
            "Known positions exceed the constrained-position limit"
        )

    best_total = -1
    best_selected: set[int] | None = None
    best_added: set[int] | None = None
    best_insert: int | None = None
    best_scoring_positions: set[int] | None = None

    for added_tuple in combinations(
        sorted(possible),
        needed_from_possible,
    ):
        added = set(added_tuple)
        selected = known | added

        if (
            max_constrained is not None
            and len(selected & constrained_positions) > max_constrained
        ):
            continue

        # The inserted position represents the Recluse. A player who
        # was selected as an actual evil cannot also be the Recluse.
        insert_candidates: list[int | None] = [
            None,
            *sorted(insert_nums - selected),
        ]

        for inserted in insert_candidates:
            scoring_positions = (
                selected
                if inserted is None
                else selected | {inserted}
            )

            total = wrapped_pair_count(
                scoring_positions,
                upper_bound,
            )

            if total > best_total:
                best_total = total
                best_selected = selected
                best_added = added
                best_insert = inserted
                best_scoring_positions = scoring_positions

    if (
        best_selected is None
        or best_added is None
        or best_scoring_positions is None
    ):
        raise ValueError(
            "No selection satisfies the supplied constraints"
        )

    best_runs = [
        run
        for run in wrapped_consecutive_subsets(
            best_scoring_positions,
            upper_bound,
        )
        if len(run) > 1
    ]

    return (
        best_runs,
        best_total,
        best_selected,
        best_added,
        best_insert,
    )

def longest_wrapped_consecutive(nums: set[int], upper_bound: int) -> list[int]:
    if not nums:
        return []
    if any(n < 0 or n >= upper_bound for n in nums):
        raise ValueError(f"All numbers must be in range 0 to {upper_bound - 1}")
    if len(nums) == upper_bound:
        return list(range(upper_bound))

    longest: list[int] = []
    for n in nums:
        prev_n = (n - 1) % upper_bound
        if prev_n not in nums:
            current: list[int] = []
            x = n
            while x in nums:
                current.append(x)
                x = (x + 1) % upper_bound
            if len(current) > len(longest):
                longest = current

    return longest

def minimum_possible_runs_with_one_remove(
    known: set[int],
    possible: set[int],
    remove_nums: set[int],
    count: int,
    upper_bound: int,
) -> tuple[
    list[list[int]],
    int,
    set[int],
    set[int],
    int | None,
] | None:
    if known & possible:
        raise ValueError("known and possible must not overlap")

    if any(
        n < 0 or n >= upper_bound
        for n in known | possible | remove_nums
    ):
        raise ValueError(
            f"All numbers must be in range 0 to {upper_bound - 1}"
        )

    needed_from_possible = count - len(known)

    if needed_from_possible < 0:
        return None

    if needed_from_possible > len(possible):
        return None

    best_runs: list[list[int]] | None = None
    best_selected: set[int] | None = None
    best_added: set[int] | None = None
    best_removed: int | None = None
    best_total = math.inf

    for added_tuple in combinations(
        sorted(possible),
        needed_from_possible,
    ):
        added = set(added_tuple)
        selected = known | added

        removal_candidates: list[int | None] = [
            None,
            *sorted(remove_nums & selected),
        ]

        for removed in removal_candidates:
            registered_evils = (
                selected
                if removed is None
                else selected - {removed}
            )

            runs = wrapped_consecutive_subsets(
                registered_evils,
                upper_bound,
            )

            total = sum(
                len(run) - 1
                for run in runs
            )

            if best_runs is None or total < best_total:
                best_runs = runs
                best_selected = selected
                best_added = added
                best_removed = removed
                best_total = total

    if (
        best_runs is None
        or best_selected is None
        or best_added is None
        or best_total == math.inf
    ):
        return None

    return (
        best_runs,
        int(best_total),
        best_selected,
        best_added,
        best_removed,
    )

def minimum_possible_runs(
    known: set[int],
    possible: set[int],
    count: int,
    upper_bound: int,
) -> tuple[list[list[int]], int, set[int], set[int]]:
    known = set(known)
    possible = set(possible)

    if known & possible:
        raise ValueError("known and possible must not overlap")
    if any(n < 0 or n >= upper_bound for n in known | possible):
        raise ValueError(f"All numbers must be in range 0 to {upper_bound - 1}")
    needed_from_possible = count - len(known)
    if needed_from_possible < 0:
        raise ValueError("count cannot be smaller than len(known)")
    if needed_from_possible > len(possible):
        raise ValueError("Not enough possible numbers to reach count")

    best_runs = None
    best_selected = None
    best_added = None
    best_total = math.inf
    for added_tuple in combinations(sorted(possible), needed_from_possible):
        added = set(added_tuple)
        selected = known | added

        runs = wrapped_consecutive_subsets(selected, upper_bound)

        total = 0
        for run in runs:
            total += len(run) - 1

        if best_runs is None or total < best_total:
            best_runs = runs
            best_selected = selected
            best_added = added
            best_total = total

    assert best_runs is not None and best_selected is not None and best_added is not None and best_total < math.inf

    return best_runs, int(best_total), best_selected, best_added
