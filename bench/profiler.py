"""Profiles benchmark games with cProfile, one worker process per player count.

Writes a merged .prof per player count (open with snakeviz), a summary of the slowest
functions, and a per-stage breakdown of where the time and worlds go.
"""
from collections import defaultdict
from datetime import datetime
import json
import os
from pathlib import Path
import pstats
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from typing import Any

from . import report
from .scenarios import _git_state, load_scenarios  # pyright: ignore[reportPrivateUsage]
from .tiers import TIERS
from .worker import OOM_EXIT_CODE

REPO_ROOT = Path(__file__).parent.parent
PROFILES_DIR = Path(__file__).parent / "profiles"
BASELINE_PATH = Path(__file__).parent / "baseline.json"

# games profiled for a player count when only --players is given
DEFAULT_GAMES = {5: 100, 10: 3, 15: 1}
# cProfile roughly doubles the solver's run time, so these are twice the benchmark's
DEFAULT_TIMEOUTS = {5: 120.0, 10: 600.0, 15: 3600.0}
DEFAULT_MEMORY_GB = 12.0
DEFAULT_TOP = 30
WATCHDOG_GRACE = 30.0
SORTS = ("tottime", "cumtime")

_GAME_ID = re.compile(r"^(\d+)p-(\d+)$")

def parse_game_id(game_id: str) -> tuple[int, int]:
    """'10p-0003' -> (10, 3)"""
    match = _GAME_ID.match(game_id)
    if not match:
        raise ValueError(f"Bad game id {game_id!r}, expected something like 10p-0003.")
    return int(match.group(1)), int(match.group(2))

def parse_indices(spec: str) -> list[int]:
    """'3-7' -> [3, 4, 5, 6, 7]; '1,4,9' -> [1, 4, 9]; ranges and single indices can be mixed."""
    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                first, last = (int(x) for x in part.split("-"))
                if last < first:
                    raise ValueError()
                indices.update(range(first, last + 1))
            else:
                indices.add(int(part))
        except ValueError:
            raise ValueError(f"Bad game indices {spec!r}, expected e.g. 3-7 or 1,4,9.") from None
    if not indices:
        raise ValueError(f"No game indices in {spec!r}.")
    return sorted(indices)

def select_games(
    players: list[int] | None = None,
    game_ids: list[str] | None = None,
    count: int | None = None,
    indices: str | None = None,
    tier: str | None = None,
) -> dict[int, list[int]]:
    """Scenario indices to profile for each player count. Only one of game_ids, count,
    indices and tier may be given; players narrows any of them."""
    if sum(x is not None for x in (game_ids, count, indices, tier)) > 1:
        raise ValueError("Use only one of game ids, count, indices or tier.")

    selected: dict[int, list[int]] = {}
    if game_ids is not None:
        by_players: dict[int, set[int]] = defaultdict(set)
        for game_id in game_ids:
            p, index = parse_game_id(game_id)
            by_players[p].add(index)
        selected = {p: sorted(i) for p, i in by_players.items()}
    elif tier is not None:
        selected = {p: list(range(n)) for p, n in TIERS[tier].items() if n > 0}
    else:
        player_counts = players or sorted(DEFAULT_GAMES)
        if indices is not None:
            chosen = parse_indices(indices)
            selected = {p: chosen for p in player_counts}
        else:
            if count is not None and count < 1:
                raise ValueError("Count must be at least 1.")
            selected = {p: list(range(count if count is not None else DEFAULT_GAMES.get(p, 1))) for p in player_counts}

    if players is not None:
        selected = {p: i for p, i in selected.items() if p in players}
    if not selected:
        raise ValueError("No games selected.")
    return dict(sorted(selected.items()))

def stage_kind(stage: str) -> str:
    """Groups a step's stage by what it does, e.g. 'night 3 demon kill {...}' -> 'demon kill'."""
    return re.sub(r"^night \d+ ", "", report.short_stage(stage)).removesuffix(" info").strip()

def _failed_game(scenario_id: str, seed: int, status: str, error: str) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "seed": seed,
        "status": status,
        "error": error,
        "seconds": None,
        "final_grims": None,
        "peak_grims": None,
        "peak_stage": None,
        "world_steps": None,
        "memory_peak_stage": None,
        "top_allocations": None,
        "steps": [],
    }

def _start_worker(
    players: int,
    indices: list[int],
    version: str,
    timeout: float,
    memory_gb: float,
    asserts: bool,
    games_dir: Path,
    memory: bool,
    inject_fault: str | None,
) -> subprocess.Popen[str]:
    command = [sys.executable]
    if not asserts:
        command.append("-O")
    command += [
        "-m", "bench.profiler_worker",
        "--players", str(players),
        "--version", version,
        "--indices", ",".join(map(str, indices)),
        "--timeout", str(timeout),
        "--memory-gb", str(memory_gb),
        "--out-dir", str(games_dir),
    ]
    if memory:
        command.append("--memory")
    if inject_fault:
        command += ["--inject-fault", inject_fault]
    return subprocess.Popen(command, cwd=REPO_ROOT, stdout=subprocess.PIPE, text=True, bufsize=1)

def profile_player_count(
    players: int,
    indices: list[int],
    games_dir: Path,
    version: str = "v1",
    timeout: float | None = None,
    memory_gb: float = DEFAULT_MEMORY_GB,
    asserts: bool = False,
    memory: bool = False,
    inject_fault: str | None = None,
    progress: bool = True,
) -> list[dict[str, Any]]:
    """Profiles the games at these scenario indices, writing <game id>.prof files to games_dir.
    Returns the per-game results in the same order as indices."""
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUTS.get(players, 3600.0)
    # loads the scenarios here too, so a bad index fails before any worker starts
    scenarios = load_scenarios(players, version, limit=max(indices) + 1)
    results: list[dict[str, Any]] = []
    progress_every = max(1, len(indices) // 10)

    while len(results) < len(indices):
        remaining = indices[len(results):]
        worker = _start_worker(players, remaining, version, timeout, memory_gb, asserts, games_dir, memory, inject_fault)
        assert worker.stdout is not None
        killed_by_watchdog = False
        last_output = time.monotonic()

        while True:
            wait = timeout + WATCHDOG_GRACE - (time.monotonic() - last_output)
            ready, _, _ = select.select([worker.stdout], [], [], max(wait, 0))
            if not ready:
                worker.kill()
                killed_by_watchdog = True
                break
            line = worker.stdout.readline()
            if line == "":
                break
            last_output = time.monotonic()
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "game":
                continue
            del record["type"]
            results.append(record)
            if progress and (len(results) % progress_every == 0 or len(results) == len(indices)):
                print(f"  {players}p: {len(results)}/{len(indices)}", file=sys.stderr, flush=True)

        worker.stdout.close()
        exit_code = worker.wait()
        if exit_code == 0 or len(results) >= len(indices) or exit_code == OOM_EXIT_CODE:
            continue

        # the worker died partway through a game without reporting it
        scenario = scenarios[indices[len(results)]]
        if killed_by_watchdog:
            status, error = "timeout", f"worker silent for {timeout + WATCHDOG_GRACE:.0f}s and was killed"
        elif exit_code == -signal.SIGKILL:
            status, error = "oom", "worker was killed (likely by the system's out-of-memory killer)"
        else:
            status, error = "crashed", f"worker exited with code {exit_code}"
        results.append(_failed_game(scenario.id, scenario.seed, status, error))

    return results

def merge_profiles(paths: list[Path], out_path: Path) -> bool:
    """Merges .prof files into one. Returns False if there was nothing to merge."""
    existing = [str(p) for p in paths if p.exists()]
    if not existing:
        return False
    stats = pstats.Stats(*existing)
    stats.dump_stats(out_path)
    return True

def stage_breakdown(games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Time and worlds per kind of step, summed over the games, slowest first."""
    rows: dict[str, dict[str, Any]] = {}
    for game in games:
        for step in game["steps"]:
            kind = stage_kind(step[0])
            row = rows.setdefault(kind, {"kind": kind, "steps": 0, "seconds": 0.0, "world_steps": 0, "max_worlds": 0})
            row["steps"] += 1
            row["seconds"] += step[3]
            row["world_steps"] += step[2]
            row["max_worlds"] = max(row["max_worlds"], step[2])
    return sorted(rows.values(), key=lambda r: r["seconds"], reverse=True)

def _function_name(key: tuple[str, int, str]) -> str:
    filename, line, name = key
    if filename == "~":
        # built-ins, e.g. "<built-in method builtins.sorted>"
        return name
    return f"{_relative(filename)}:{line}({name})"

def format_functions(prof_path: Path, sort: str, top: int, restrict: str | None = None) -> str:
    """The top functions as a table, with paths relative to the repo so restrict can match on
    them, e.g. 'grimoire/' for only the solver's own code."""
    stats: dict[Any, Any] = pstats.Stats(str(prof_path)).stats  # pyright: ignore[reportAttributeAccessIssue]
    total = sum(tt for _, _, tt, _, _ in stats.values()) or 1.0
    rows = [
        (_function_name(key), primitive, calls, tottime, cumtime)
        for key, (primitive, calls, tottime, cumtime, _) in stats.items()
    ]
    if restrict:
        pattern = re.compile(restrict)
        rows = [r for r in rows if pattern.search(r[0])]
    rows.sort(key=lambda r: r[3] if sort == "tottime" else r[4], reverse=True)
    lines = [f"  {'calls':>11} {'tottime':>9} {'share':>6} {'cumtime':>9} {'share':>6} {'us/call':>8}  function"]
    for name, primitive, calls, tottime, cumtime in rows[:top]:
        # recursive functions show total/primitive calls, like pstats
        call_text = str(calls) if calls == primitive else f"{calls}/{primitive}"
        lines.append(
            f"  {call_text:>11} {tottime:>9.3f} {tottime / total:>6.1%} {cumtime:>9.3f} {cumtime / total:>6.1%} " +
            f"{tottime / calls * 1e6 if calls else 0:>8.1f}  {name}"
        )
    return "\n".join(lines)

def _baseline_seconds(path: Path = BASELINE_PATH) -> dict[str, float]:
    try:
        with open(path) as f:
            baseline = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        g["id"]: g["seconds"]
        for data in baseline.get("players", {}).values()
        for g in data["games"]
        if g.get("seconds") is not None
    }

def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)

def _format_games(games: list[dict[str, Any]], baseline: dict[str, float]) -> list[str]:
    lines = [f"  {'game':<10} {'status':<15} {'profiled s':>10} {'baseline s':>10} {'final':>7} {'peak':>8}  peak stage"]
    shown = sorted(games, key=lambda g: g["seconds"] or 0, reverse=True)
    for g in shown[:15]:
        lines.append(
            f"  {g['id']:<10} {g['status']:<15} {_fmt(g['seconds']):>10} {_fmt(baseline.get(g['id'])):>10} " +
            f"{_fmt(g['final_grims']):>7} {_fmt(g['peak_grims']):>8}  {report.short_stage(g['peak_stage']) if g['peak_stage'] else ''}"
        )
    if len(shown) > 15:
        lines.append(f"  ... {len(shown) - 15} more (slowest shown first)")
    total = sum(g["seconds"] or 0 for g in games)
    total_baseline = sum(baseline.get(g["id"], 0) for g in games)
    lines.append(f"  total {total:.2f}s profiled" + (f", {total_baseline:.2f}s in the baseline" if total_baseline else ""))
    return lines

def _format_stages(games: list[dict[str, Any]]) -> list[str]:
    rows = stage_breakdown(games)
    total = sum(r["seconds"] for r in rows) or 1.0
    lines = [f"  {'stage':<28} {'steps':>7} {'seconds':>9} {'share':>6} {'world-steps':>12} {'max worlds':>11}"]
    for r in rows:
        lines.append(
            f"  {r['kind'][:28]:<28} {r['steps']:>7} {r['seconds']:>9.2f} {r['seconds'] / total:>6.0%} " +
            f"{r['world_steps']:>12} {r['max_worlds']:>11}"
        )
    return lines

def _format_memory(games: list[dict[str, Any]]) -> list[str]:
    lines = [f"  {'game':<10} {'peak rss MB':>11} {'peak traced MB':>14}  most memory held after"]
    for g in games:
        rss = max((s[4] for s in g["steps"] if s[4] is not None), default=None)
        traced = max((s[6] for s in g["steps"] if s[6] is not None), default=None)
        lines.append(
            f"  {g['id']:<10} {_fmt(rss / 1024 if rss is not None else None, 1):>11} " +
            f"{_fmt(traced / 1024 if traced is not None else None, 1):>14}  " +
            f"{report.short_stage(g['memory_peak_stage']) if g.get('memory_peak_stage') else ''}"
        )
    biggest = max(
        (g for g in games if g.get("top_allocations")),
        key=lambda g: max((s[5] or 0 for s in g["steps"]), default=0),
        default=None,
    )
    if biggest is not None:
        lines.append("")
        lines.append(f"  Largest allocation sites when {biggest['id']} held the most memory ({report.short_stage(biggest['memory_peak_stage'])}):")
        lines.append(f"    {'KB':>10} {'blocks':>10}  line")
        for location, size_kb, blocks in biggest["top_allocations"]:
            lines.append(f"    {size_kb:>10} {blocks:>10}  {_relative(location)}")
    return lines

def _relative(location: str) -> str:
    try:
        return str(Path(location).relative_to(REPO_ROOT))
    except ValueError:
        return location

def format_summary(result: dict[str, Any], out_dir: Path, sorts: tuple[str, ...] = SORTS, top: int = DEFAULT_TOP, restrict: str | None = None) -> str:
    meta = result["meta"]
    baseline = _baseline_seconds()
    lines = [
        f"{meta['label']}  (commit {meta['commit']}{' + uncommitted changes' if meta['dirty'] else ''}" +
        f"{', tracemalloc on' if meta['memory'] else ''})",
        "Times are under cProfile and tracemalloc, so expect them to be roughly 5 times the benchmark's."
        if meta["memory"] else
        "Times are under cProfile, so expect them to be roughly twice the benchmark's.",
    ]
    for p, data in result["players"].items():
        games = data["games"]
        lines += ["", "=" * 100, f"{p} players: {len(games)} game{'s' if len(games) != 1 else ''}", ""]
        problems = [g for g in games if g["status"] != "ok"]
        if problems:
            lines.append("  Games that didn't finish (their profiles cover the part that ran):")
            for g in problems:
                detail = f": {g['error']}" if g["error"] else ""
                lines.append(f"    {g['id']} {g['status']}{report.failure_location(g)}{detail}")
            lines.append("")
        lines += _format_games(games, baseline)
        lines += ["", "  Time by stage:"] + _format_stages(games)
        if meta["memory"]:
            lines += ["", "  Memory:"] + _format_memory(games)
        prof_path = out_dir / data["profile"] if data["profile"] else None
        if prof_path is not None:
            for sort in sorts:
                lines += ["", f"  Top {top} functions by {sort}, share of all profiled time{f' matching {restrict!r}' if restrict else ''}:", ""]
                lines.append(format_functions(prof_path, sort, top, restrict))
    lines += ["", f"Profiles: {out_dir}", f"View one with: snakeviz {out_dir / '<players>p.prof'}"]
    return "\n".join(lines)

def run(
    selection: dict[int, list[int]],
    label: str = "profile",
    version: str = "v1",
    timeouts: dict[int, float] | None = None,
    memory_gb: float = DEFAULT_MEMORY_GB,
    asserts: bool = False,
    memory: bool = False,
    per_game: bool = False,
    sorts: tuple[str, ...] = SORTS,
    top: int = DEFAULT_TOP,
    restrict: str | None = None,
    profiles_dir: Path = PROFILES_DIR,
    inject_fault: str | None = None,
    progress: bool = True,
) -> tuple[dict[str, Any], Path]:
    """Profiles the selected games. Returns the results and the directory they were written to."""
    timeouts = {**DEFAULT_TIMEOUTS, **(timeouts or {})}
    # fail on a missing scenario file or a game that doesn't exist before writing anything
    for p, indices in selection.items():
        _ = load_scenarios(p, version, limit=max(indices) + 1)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = profiles_dir / f"{stamp}_{report.slugify(label)}"
    out_dir.mkdir(parents=True, exist_ok=False)

    commit, dirty = _git_state()
    if dirty:
        print("Warning: the working tree has uncommitted changes.", file=sys.stderr)
    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "label": label,
        "scenario_version": version,
        "commit": commit,
        "dirty": dirty,
        "asserts": asserts,
        "memory": memory,
        "memory_gb": memory_gb,
        "games": {str(p): [f"{p}p-{i:04d}" for i in indices] for p, indices in selection.items()},
    }

    by_players: dict[str, Any] = {}
    for p, indices in selection.items():
        print(f"Profiling {len(indices)} {p} player game{'s' if len(indices) != 1 else ''}...", file=sys.stderr, flush=True)
        games_dir = out_dir / f"{p}p_games"
        games = profile_player_count(
            p, indices, games_dir, version, timeouts.get(p), memory_gb, asserts, memory, inject_fault, progress
        )
        prof_name = f"{p}p.prof"
        merged = merge_profiles([games_dir / f"{g['id']}.prof" for g in games], out_dir / prof_name)
        if not per_game:
            shutil.rmtree(games_dir, ignore_errors=True)
        by_players[str(p)] = {"profile": prof_name if merged else None, "games": games}

    result = {"meta": meta, "players": by_players}
    with open(out_dir / "meta.json", "w") as f:
        json.dump(result, f, separators=(",", ":"))

    summary = format_summary(result, out_dir, sorts, top, restrict)
    (out_dir / "summary.txt").write_text(summary + "\n")
    print(summary)
    return result, out_dir

def open_snakeviz(prof_path: Path):
    snakeviz = shutil.which("snakeviz") or str(Path(sys.executable).parent / "snakeviz")
    if not os.path.exists(snakeviz):
        print("snakeviz isn't installed (pip install snakeviz).", file=sys.stderr)
        return
    _ = subprocess.Popen([snakeviz, str(prof_path)])
