"""Saves the final worlds of benchmark games and compares them between runs.

Worlds that one run removed are sorted into dropped poison (a kept world is the same apart from
having no extra poison), merged (covered by a more general world), invalid (fails a validator),
rejected (finalizing it again finds it impossible), refined (finalizing it again gives a world
that was kept), or unexplained (none of these, so possibly a valid world that was wrongly removed).
Unexplained worlds are re-run as the true grim of their game to find the step that drops them.

Refined and rejected use the solver's own finalize, with the code currently checked out. A bug
in it could explain away a valid world, so rejected worlds are always listed with their reason.
"""
import gzip
import json
from pathlib import Path
import re
from typing import Any, NamedTuple

from grimoire import Grimoire, GrimoireManager, validators
from grimoire.add_info_to_grims import find_finalize_problem
from grimoire.errors import TrueGrimLostError
from grimoire.grimoire import Poisoning

from . import report
from .scenarios import _decode_hook, _git_state, decode_grim, encode_grim, load_scenarios  # pyright: ignore[reportPrivateUsage]

WORLD_CATEGORIES_REMOVED = ("dropped_poison", "merged", "refined", "rejected", "invalid", "unexplained")
WORLD_CATEGORIES_ADDED = ("generalized", "refined", "known_invalid", "other")
# categories where no world was lost or gained, so they're only listed for one game
QUIET_CATEGORIES = ("dropped_poison", "merged", "refined", "generalized")
# a world that was still matched after the last step. It only has to loosely match each step's
# worlds, so this doesn't mean the exact world is in the final list.
NOT_DROPPED = "not dropped"
# worlds of each kind listed in the summary; --game lists all of them for one game
SHOWN_PER_CATEGORY = 10

def worlds_dir(run_path: Path) -> Path:
    """The directory holding a run's worlds, next to its JSON: <run>.worlds/"""
    return run_path.with_suffix(".worlds")

def worlds_file(run_path: Path, players: int | str) -> Path:
    return worlds_dir(run_path) / f"{players}p.jsonl.gz"

def append_worlds(path: Path, game_id: str, grims: list[Grimoire]):
    # appending makes a multi-member gzip file, which gzip.open reads as one stream
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "at") as f:
        _ = f.write(json.dumps({"id": game_id, "worlds": [encode_grim(g) for g in grims]}, separators=(",", ":")) + "\n")

def load_worlds(path: Path) -> dict[str, list[Grimoire]]:
    worlds: dict[str, list[Grimoire]] = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            record = json.loads(line, object_hook=_decode_hook)
            worlds[record["id"]] = [decode_grim(g) for g in record["worlds"]]
    return worlds

def count_known_invalid(grims: list[Grimoire]) -> int:
    """Worlds the joint role assignment check rejects. It isn't run during solving because
    it's too slow there, so these are worlds the solver keeps that are known to be impossible."""
    return sum(1 for g in grims if not validators.ROLE_ASSIGNMENT_VALIDATOR.validate(g.pages[0]))

def validity_problem(grim: Grimoire) -> str | None:
    valid, reason = validators.is_grim_valid(grim)
    if not valid:
        return reason
    if not validators.ROLE_ASSIGNMENT_VALIDATOR.validate(grim.pages[0]):
        return validators.ROLE_ASSIGNMENT_VALIDATOR.reason
    return None

def poisonings_by_state(grims: list[Grimoire]) -> dict[tuple[Any, ...], list[frozenset[Poisoning]]]:
    index: dict[tuple[Any, ...], list[frozenset[Poisoning]]] = {}
    for grim in grims:
        index.setdefault(grim.state_without_poison(), []).append(grim.get_all_poisonings())
    return index

def is_dropped_poison(world: Grimoire, kept_poisonings: dict[tuple[Any, ...], list[frozenset[Poisoning]]]) -> bool:
    """A kept world is the same apart from having no extra poison. Equal poison counts because a
    world only gets here when it isn't in the kept list, so it can only differ by an empty page."""
    poisonings = world.get_all_poisonings()
    return any(kept <= poisonings for kept in kept_poisonings.get(world.state_without_poison(), []))

def classify_removed(world: Grimoire, kept: list[Grimoire]) -> tuple[str, str | None]:
    if any(other.subsumes(world) for other in kept):
        return "merged", None
    problem = validity_problem(world)
    if problem is not None:
        return "invalid", problem
    settled = world.clone()
    try:
        problem = find_finalize_problem(settled)
    except (RuntimeError, ValueError) as e:
        # branching treats these as an impossible world too
        problem = str(e)
    if problem is not None:
        return "rejected", problem
    if any(other.subsumes(settled) for other in kept):
        return "refined", None
    return "unexplained", None

def classify_added(world: Grimoire, previous: list[Grimoire]) -> tuple[str, str | None]:
    if any(world.subsumes(other) for other in previous):
        return "generalized", None
    problem = validity_problem(world)
    if problem is not None:
        return "known_invalid", problem
    if any(other.subsumes(world) for other in previous):
        return "refined", None
    return "other", None

_LOST_STAGE = re.compile(r"True grim lost at (.*)\. before=")

def find_drop_step(players: int, scenario_info: Any, scenario_deaths: Any, nights: int, world: Grimoire) -> str:
    """Re-runs a game with the current code, tracking `world` as if it were the true grim."""
    manager = GrimoireManager({"players": players}, world)
    try:
        manager.add_full_game(scenario_info, scenario_deaths, nights)
    except TrueGrimLostError as e:
        match = _LOST_STAGE.search(str(e))
        return report.short_stage(match.group(1)) if match else str(e)
    except Exception as e:
        return f"error while re-running: {e!r}"
    return NOT_DROPPED

def describe_world(grim: Grimoire) -> str:
    """Characters per page, only listing pages whose characters changed."""
    parts: list[str] = []
    previous = None
    for page in grim.pages:
        characters = [c.name for c in page.characters]
        if characters == previous:
            continue
        marks = [
            name + ("(p)" if page.poisoned[i] else "") + ("(rh)" if page.red_herring[i] else "")
            for i, name in enumerate(characters)
        ]
        parts.append(f"N{page.night}: " + " ".join(marks))
        previous = characters
    minions = " ".join(m.name for m in grim.pages[0].minion_types)
    return " | ".join(parts) + f" | minions: {minions}"

class WorldDiff(NamedTuple):
    game_id: str
    world: Grimoire
    category: str
    reason: str | None
    drop_step: str | None

def compare_worlds(a_path: Path, b_path: Path, game_id: str | None = None) -> dict[str, Any]:
    with open(a_path) as f:
        a = json.load(f)
    with open(b_path) as f:
        b = json.load(f)

    warnings: list[str] = []
    commit, dirty = _git_state()
    if commit != b["meta"]["commit"] or dirty:
        warnings.append(
            f"Removed worlds are re-finalized and unexplained ones re-run with the code currently checked out ({commit}" +
            f"{' + uncommitted changes' if dirty else ''}), not B's commit ({b['meta']['commit']}), " +
            "so their categories and steps reflect the current code."
        )

    by_players: dict[str, Any] = {}
    for players in sorted(set(a["players"]) & set(b["players"]), key=int):
        if game_id is not None and not game_id.startswith(f"{players}p-"):
            continue
        file_a, file_b = worlds_file(a_path, players), worlds_file(b_path, players)
        if not file_a.exists() or not file_b.exists():
            missing = "A" if not file_a.exists() else "B"
            warnings.append(f"No saved {players} player worlds for {missing}, so they weren't compared.")
            continue

        worlds_a, worlds_b = load_worlds(file_a), load_worlds(file_b)
        ids = sorted(set(worlds_a) & set(worlds_b))
        if game_id is not None:
            if game_id not in ids:
                raise ValueError(f"{game_id} doesn't have saved worlds in both runs (it may not have finished in one).")
            ids = [game_id]
        scenarios = {s.id: s for s in load_scenarios(int(players), a["meta"]["scenario_version"], limit=len(a["players"][players]["games"]))}

        removed: list[WorldDiff] = []
        added: list[WorldDiff] = []
        changed_games = 0
        for i in ids:
            set_a, set_b = set(worlds_a[i]), set(worlds_b[i])
            only_a = [w for w in worlds_a[i] if w not in set_b]
            only_b = [w for w in worlds_b[i] if w not in set_a]
            if only_a or only_b:
                changed_games += 1
            kept_poisonings = poisonings_by_state(worlds_b[i]) if only_a else {}
            for world in only_a:
                if is_dropped_poison(world, kept_poisonings):
                    removed.append(WorldDiff(i, world, "dropped_poison", None, None))
                    continue
                category, reason = classify_removed(world, worlds_b[i])
                drop_step = None
                if category == "unexplained":
                    s = scenarios[i]
                    drop_step = find_drop_step(int(players), s.info, s.deaths, s.nights, world)
                removed.append(WorldDiff(i, world, category, reason, drop_step))
            for world in only_b:
                category, reason = classify_added(world, worlds_a[i])
                added.append(WorldDiff(i, world, category, reason, None))

        by_players[players] = {
            "games": len(ids),
            "changed_games": changed_games,
            "removed": removed,
            "added": added,
        }

    return {"a": a["meta"], "b": b["meta"], "warnings": warnings, "players": by_players, "game": game_id}

def has_unexplained(comparison: dict[str, Any]) -> bool:
    return any(
        d.category == "unexplained"
        for data in comparison["players"].values()
        for d in data["removed"]
    )

def _world_line(d: WorldDiff) -> str:
    detail = d.drop_step if d.category == "unexplained" else d.reason
    detail = f" [{detail}]" if detail else ""
    return f"    {d.game_id}{detail}: {describe_world(d.world)}"

def format_world_comparison(comparison: dict[str, Any]) -> str:
    show_all = comparison["game"] is not None
    lines = [
        "",
        f"A: {comparison['a']['label']}  (commit {comparison['a']['commit']}, {comparison['a']['timestamp']})",
        f"B: {comparison['b']['label']}  (commit {comparison['b']['commit']}, {comparison['b']['timestamp']})",
    ]
    for warning in comparison["warnings"]:
        lines.append(f"Warning: {warning}")

    for players, data in comparison["players"].items():
        lines.append("")
        lines.append(f"=== {players} players: {data['games']} games compared, worlds changed in {data['changed_games']} ===")
        for title, diffs, categories in (
            ("Removed (in A, not in B)", data["removed"], WORLD_CATEGORIES_REMOVED),
            ("Added (in B, not in A)", data["added"], WORLD_CATEGORIES_ADDED),
        ):
            counts = ", ".join(f"{c.replace('_', ' ')} {sum(1 for d in diffs if d.category == c)}" for c in categories)
            lines.append(f"{title}: {len(diffs)} ({counts})")
            for category in categories:
                in_category = [d for d in diffs if d.category == category]
                if not in_category or (category in QUIET_CATEGORIES and not show_all):
                    continue
                if category == "unexplained":
                    lines.append("  UNEXPLAINED - possibly valid worlds that were removed [step that drops them now]:")
                else:
                    lines.append(f"  {category.replace('_', ' ')}:")
                shown = in_category if show_all or category == "unexplained" else in_category[:SHOWN_PER_CATEGORY]
                lines.extend(_world_line(d) for d in shown)
                if len(shown) < len(in_category):
                    lines.append(f"    ... and {len(in_category) - len(shown)} more")

    lines.append("")
    return "\n".join(lines)
