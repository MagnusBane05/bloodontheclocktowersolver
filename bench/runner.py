"""Runs a benchmark tier, one worker process per player count, and collects the results."""
from datetime import datetime
import json
import os
from pathlib import Path
import platform
import select
import signal
import subprocess
import sys
import time
from typing import Any

from . import report
from .scenarios import _git_state, load_scenarios  # pyright: ignore[reportPrivateUsage]
from .tiers import TIERS
from .worker import OOM_EXIT_CODE
from .worlds import worlds_file

REPO_ROOT = Path(__file__).parent.parent
RESULTS_DIR = Path(__file__).parent / "results"
CSV_PATH = Path(__file__).parent / "results.csv"

DEFAULT_TIMEOUTS = {5: 60.0, 10: 300.0, 15: 1800.0}
DEFAULT_MEMORY_GB = 12.0
# player counts whose final worlds are saved; 15 player games can end with tens of thousands
DEFAULT_WORLDS = (5, 10)
# extra time the runner waits on a silent worker before killing it
WATCHDOG_GRACE = 30.0

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
        "known_invalid": None,
        "steps": [],
    }

def _start_worker(
    players: int,
    version: str,
    start: int,
    count: int,
    timeout: float,
    memory_gb: float,
    repeat: int,
    asserts: bool,
    inject_fault: str | None,
    worlds_path: Path | None,
) -> subprocess.Popen[str]:
    command = [sys.executable]
    if not asserts:
        command.append("-O")
    command += [
        "-m", "bench.worker",
        "--players", str(players),
        "--version", version,
        "--start", str(start),
        "--count", str(count),
        "--timeout", str(timeout),
        "--memory-gb", str(memory_gb),
        "--repeat", str(repeat),
    ]
    if worlds_path is not None:
        command += ["--worlds-out", str(worlds_path)]
    if inject_fault:
        command += ["--inject-fault", inject_fault]
    return subprocess.Popen(command, cwd=REPO_ROOT, stdout=subprocess.PIPE, text=True, bufsize=1)

def run_player_count(
    players: int,
    count: int,
    version: str = "v1",
    timeout: float | None = None,
    memory_gb: float = DEFAULT_MEMORY_GB,
    repeat: int = 1,
    asserts: bool = False,
    inject_fault: str | None = None,
    progress: bool = True,
    worlds_path: Path | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Returns the per-game results and the peak memory (KB) of the workers.
    If worlds_path is given, each finished game's final worlds are appended to it."""
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUTS[players]
    scenarios = load_scenarios(players, version, limit=count)
    results: list[dict[str, Any]] = []
    peak_rss_kb = 0
    progress_every = max(1, count // 10)

    while len(results) < count:
        start = len(results)
        worker = _start_worker(players, version, start, count - start, timeout, memory_gb, repeat, asserts, inject_fault, worlds_path)
        assert worker.stdout is not None
        killed_by_watchdog = False
        last_output = time.monotonic()

        while True:
            remaining = timeout + WATCHDOG_GRACE - (time.monotonic() - last_output)
            ready, _, _ = select.select([worker.stdout], [], [], max(remaining, 0))
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
            if progress and (len(results) % progress_every == 0 or len(results) == count):
                print(f"  {players}p: {len(results)}/{count}", file=sys.stderr, flush=True)

        worker.stdout.close()
        # wait4 gives the worker's own peak memory, even if it was killed
        _, wait_status, rusage = os.wait4(worker.pid, 0)
        worker.returncode = os.waitstatus_to_exitcode(wait_status)
        peak_rss_kb = max(peak_rss_kb, rusage.ru_maxrss)

        exit_code = worker.returncode
        if exit_code == 0 or len(results) >= count:
            continue
        if exit_code == OOM_EXIT_CODE:
            # the worker already reported the game as oom; start a new one for the rest
            continue

        # the worker died partway through a game without reporting it
        scenario = scenarios[len(results)]
        if killed_by_watchdog:
            status, error = "timeout", f"worker silent for {timeout + WATCHDOG_GRACE:.0f}s and was killed"
        elif exit_code == -signal.SIGKILL:
            status, error = "oom", "worker was killed (likely by the system's out-of-memory killer)"
        else:
            status, error = "crashed", f"worker exited with code {exit_code}"
        results.append(_failed_game(scenario.id, scenario.seed, status, error))

    return results, peak_rss_kb

def run(
    tier: str,
    label: str,
    players: list[int] | None = None,
    version: str = "v1",
    timeouts: dict[int, float] | None = None,
    memory_gb: float = DEFAULT_MEMORY_GB,
    repeat: int = 1,
    asserts: bool = False,
    write_csv: bool = True,
    results_dir: Path = RESULTS_DIR,
    csv_path: Path = CSV_PATH,
    worlds: tuple[int, ...] = DEFAULT_WORLDS,
) -> dict[str, Any]:
    sizes = TIERS[tier]
    player_counts = [p for p in sorted(sizes) if sizes[p] > 0 and (players is None or p in players)]
    timeouts = {**DEFAULT_TIMEOUTS, **(timeouts or {})}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_path = results_dir / f"{stamp}_{report.slugify(label)}.json"
    if write_csv:
        report.check_csv(csv_path)

    commit, dirty = _git_state()
    if sys.gettrace() is not None:
        print("Warning: running under a debugger, timings will be much slower than normal.", file=sys.stderr)
    if dirty:
        print("Warning: the working tree has uncommitted changes.", file=sys.stderr)

    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "label": label,
        "tier": tier,
        "scenario_version": version,
        "commit": commit,
        "dirty": dirty,
        "repeat": repeat,
        "asserts": asserts,
        "python": platform.python_version(),
        "host": platform.node(),
        "memory_gb": memory_gb,
        "timeouts": {str(p): timeouts[p] for p in player_counts},
        "worlds": [p for p in player_counts if p in worlds],
    }

    by_players: dict[str, Any] = {}
    for p in player_counts:
        print(f"Running {sizes[p]} {p} player games...", file=sys.stderr, flush=True)
        worlds_path = worlds_file(run_path, p) if p in worlds else None
        games, peak_rss_kb = run_player_count(
            p, sizes[p], version, timeouts[p], memory_gb, repeat, asserts, worlds_path=worlds_path
        )
        by_players[str(p)] = {
            "summary": report.summarize(games, peak_rss_kb),
            "games": games,
        }

    result = {"meta": meta, "players": by_players}

    results_dir.mkdir(parents=True, exist_ok=True)
    with open(run_path, "w") as f:
        json.dump(result, f, separators=(",", ":"))

    row = report.csv_row(result)
    if write_csv:
        report.append_csv(csv_path, row)

    print(report.format_summary(result))
    print(f"Full results: {run_path}")
    print("Paste line:")
    print(report.tsv_line(row))
    return result
