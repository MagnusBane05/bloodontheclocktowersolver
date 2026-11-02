"""Plays benchmark games under cProfile and writes one JSON line per game.

Started by bench.profiler in its own process, like bench.worker, so a game that runs out
of memory or hangs can't take down the whole profiling run. Each game's profile is
written to <out-dir>/<game id>.prof; bench.profiler merges them.
"""
import argparse
import cProfile
import gc
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import tracemalloc
from typing import Any

from grimoire import GrimoireManager
from grimoire.errors import TrueGrimLostError
from grimoire.grimoire_manager import StepRecord

from .scenarios import Scenario, load_scenarios
from .worker import OOM_EXIT_CODE, GameTimeout, _on_alarm  # pyright: ignore[reportPrivateUsage]

# allocation sites kept from the snapshot taken at the game's memory peak
TOP_ALLOCATIONS = 15

def current_rss_kb() -> int | None:
    """Resident memory right now (ru_maxrss only gives the peak so far, which never goes down
    between games in the same worker)."""
    try:
        with open("/proc/self/statm") as f:
            pages = int(f.read().split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return pages * resource.getpagesize() // 1024

def _top_allocations(snapshot: tracemalloc.Snapshot) -> list[list[Any]]:
    snapshot = snapshot.filter_traces([
        tracemalloc.Filter(False, tracemalloc.__file__),
        # the step records this worker keeps
        tracemalloc.Filter(False, __file__),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
    ])
    rows: list[list[Any]] = []
    for stat in snapshot.statistics("lineno")[:TOP_ALLOCATIONS]:
        frame = stat.traceback[0]
        rows.append([f"{frame.filename}:{frame.lineno}", stat.size // 1024, stat.count])
    return rows

def profile_game(
    scenario: Scenario,
    players: int,
    timeout: float,
    prof_path: Path,
    memory: bool = False,
    fault: str | None = None,
) -> dict[str, Any]:
    """Plays one game under cProfile and dumps the profile to prof_path, even if the game
    didn't finish (a partial profile of a game that ran out of memory is still useful).

    Each step is [stage, grims_before, grims_after, seconds, rss_kb, traced_kb, traced_peak_kb];
    the traced values are None unless memory is on."""
    steps: list[list[Any]] = []
    profiler = cProfile.Profile()
    peak_snapshot: tuple[str, tracemalloc.Snapshot] | None = None
    peak_traced = -1

    def on_step(record: StepRecord):
        nonlocal peak_snapshot, peak_traced
        # keep the bookkeeping out of the profile; the manager doesn't time it either
        profiler.disable()
        traced_kb, traced_peak_kb = None, None
        if memory:
            traced, traced_peak = tracemalloc.get_traced_memory()
            tracemalloc.reset_peak()
            traced_kb, traced_peak_kb = traced // 1024, traced_peak // 1024
            if traced > peak_traced:
                peak_traced = traced
                peak_snapshot = (record.stage, tracemalloc.take_snapshot())
        steps.append([record.stage, record.grims_before, record.grims_after, record.seconds, current_rss_kb(), traced_kb, traced_peak_kb])
        profiler.enable()

    manager = GrimoireManager({"players": players}, scenario.true_grim, on_step=on_step)
    status = "ok"
    error = None
    if memory:
        tracemalloc.start()
    _ = signal.setitimer(signal.ITIMER_REAL, timeout)
    start = time.perf_counter()
    profiler.enable()
    try:
        if fault == "oom":
            raise MemoryError()
        if fault == "kill":
            os.kill(os.getpid(), signal.SIGKILL)
        manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)
    except GameTimeout:
        status = "timeout"
    except MemoryError:
        status = "oom"
    except TrueGrimLostError as e:
        status = "true_grim_lost"
        error = str(e)
    except RuntimeError as e:
        status = "too_many" if "too many solutions" in str(e) else "error"
        error = str(e)
    except Exception as e:
        status = "error"
        error = repr(e)
    finally:
        profiler.disable()
        _ = signal.setitimer(signal.ITIMER_REAL, 0)
    seconds = time.perf_counter() - start

    final_grims = len(manager.grims) if status == "ok" else None
    # free the grims before writing anything, in case we're out of memory
    del manager
    _ = gc.collect()

    peak_stage, top_allocations = None, None
    if memory:
        tracemalloc.stop()
        if peak_snapshot is not None:
            peak_stage = peak_snapshot[0]
            top_allocations = _top_allocations(peak_snapshot[1])
        peak_snapshot = None

    profiler.dump_stats(prof_path)

    peak = max(steps, key=lambda s: s[2], default=None)
    return {
        "id": scenario.id,
        "seed": scenario.seed,
        "status": status,
        "error": error,
        "seconds": seconds,
        "final_grims": final_grims,
        "peak_grims": peak[2] if peak else None,
        "peak_stage": peak[0] if peak else None,
        "world_steps": sum(s[2] for s in steps),
        "memory_peak_stage": peak_stage,
        "top_allocations": top_allocations,
        "steps": steps,
    }

def main():
    parser = argparse.ArgumentParser(description="Profile benchmark games for one player count")
    _ = parser.add_argument("--players", type=int, required=True)
    _ = parser.add_argument("--version", default="v1")
    _ = parser.add_argument("--indices", required=True, help="Comma separated scenario indices")
    _ = parser.add_argument("--timeout", type=float, required=True)
    _ = parser.add_argument("--memory-gb", type=float, required=True)
    _ = parser.add_argument("--out-dir", type=Path, required=True, help="Directory for the per-game .prof files")
    _ = parser.add_argument("--memory", action="store_true", help="Also trace allocations with tracemalloc")
    # for tests: "INDEX:oom" or "INDEX:kill" makes the game at scenario INDEX fail that way
    _ = parser.add_argument("--inject-fault", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    # results go to a private copy of stdout; anything the solver prints goes to stderr
    out = os.fdopen(os.dup(sys.stdout.fileno()), "w")
    sys.stdout = sys.stderr

    memory_bytes = int(args.memory_gb * 1024**3)
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    _ = signal.signal(signal.SIGALRM, _on_alarm)

    fault_index, fault_kind = None, None
    if args.inject_fault:
        index, fault_kind = args.inject_fault.split(":")
        fault_index = int(index)

    indices = [int(i) for i in args.indices.split(",")]
    scenarios = load_scenarios(args.players, args.version, limit=max(indices) + 1)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for index in indices:
        scenario = scenarios[index]
        fault = fault_kind if index == fault_index else None
        result = profile_game(scenario, args.players, args.timeout, args.out_dir / f"{scenario.id}.prof", args.memory, fault)
        out.write(json.dumps({"type": "game", **result}) + "\n")
        out.flush()
        if result["status"] == "oom":
            sys.exit(OOM_EXIT_CODE)

if __name__ == "__main__":
    main()
