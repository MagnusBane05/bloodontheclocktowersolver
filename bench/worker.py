"""Runs benchmark games for one player count and writes one JSON line per game.

Started by bench.runner in its own process so that a game that runs out of memory
or hangs can't take down the whole benchmark run.
"""
import argparse
import gc
import json
import os
import resource
import signal
import sys
import time
from types import FrameType
from typing import Any, TextIO

from pathlib import Path

from grimoire import Grimoire, GrimoireManager
from grimoire.errors import TrueGrimLostError
from grimoire.grimoire_manager import StepRecord

from .scenarios import Scenario, load_scenarios
from .worlds import append_worlds, count_known_invalid

# exit code used after a game raises MemoryError, so the runner starts a fresh worker
OOM_EXIT_CODE = 3

class GameTimeout(Exception):
    pass

def _on_alarm(_signum: int, _frame: FrameType | None):
    raise GameTimeout()

def _play(scenario: Scenario, players: int, timeout: float, fault: str | None, keep_worlds: bool = False) -> dict[str, Any]:
    steps: list[StepRecord] = []
    manager = GrimoireManager({"players": players}, scenario.true_grim, on_step=steps.append)
    status = "ok"
    error = None
    _ = signal.setitimer(signal.ITIMER_REAL, timeout)
    start = time.perf_counter()
    try:
        if fault == "oom":
            raise MemoryError()
        if fault == "kill":
            os.kill(os.getpid(), signal.SIGKILL)
        if fault == "hang":
            # ignore the game timeout so only the runner's watchdog can stop it
            _ = signal.signal(signal.SIGALRM, signal.SIG_IGN)
            time.sleep(3600)
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
        _ = signal.setitimer(signal.ITIMER_REAL, 0)
    seconds = time.perf_counter() - start

    final_grims = len(manager.grims) if status == "ok" else None
    # done after timing, so neither counts towards the game's time
    worlds: list[Grimoire] | None = manager.grims if status == "ok" and keep_worlds else None
    known_invalid = count_known_invalid(worlds) if worlds is not None else None
    # free the grims before building the result, in case we're out of memory
    del manager
    _ = gc.collect()

    peak = max(steps, key=lambda s: s.grims_after, default=None)
    return {
        "worlds": worlds,
        "known_invalid": known_invalid,
        "id": scenario.id,
        "seed": scenario.seed,
        "status": status,
        "error": error,
        "seconds": seconds,
        "final_grims": final_grims,
        "peak_grims": peak.grims_after if peak else None,
        "peak_stage": peak.stage if peak else None,
        "world_steps": sum(s.grims_after for s in steps),
        "steps": [[s.stage, s.grims_before, s.grims_after, s.seconds] for s in steps],
    }

def run_game(scenario: Scenario, players: int, timeout: float, repeat: int = 1, fault: str | None = None, keep_worlds: bool = False) -> dict[str, Any]:
    """The result includes "worlds" (the final grims, or None) for the caller to save; it isn't
    part of the JSON line. Repeats don't keep worlds, since their world counts must match the first run's."""
    first = _play(scenario, players, timeout, fault, keep_worlds)
    best = first
    for _ in range(repeat - 1):
        if best["status"] != "ok":
            break
        result = _play(scenario, players, timeout, fault)
        if result["status"] != "ok":
            return result
        # world counts must be identical every time, otherwise the numbers can't be trusted
        if [s[2] for s in result["steps"]] != [s[2] for s in best["steps"]]:
            best["status"] = "nondeterministic"
            best["error"] = "world counts differed between repeats"
            break
        if result["seconds"] < best["seconds"]:
            best = result
    if best is not first:
        best["worlds"] = first["worlds"]
        best["known_invalid"] = first["known_invalid"]
    return best

def _emit(out: TextIO, record: dict[str, Any]):
    out.write(json.dumps(record) + "\n")
    out.flush()

def main():
    parser = argparse.ArgumentParser(description="Run benchmark games for one player count")
    _ = parser.add_argument("--players", type=int, required=True)
    _ = parser.add_argument("--version", default="v1")
    _ = parser.add_argument("--start", type=int, required=True)
    _ = parser.add_argument("--count", type=int, required=True)
    _ = parser.add_argument("--timeout", type=float, required=True)
    _ = parser.add_argument("--memory-gb", type=float, required=True)
    _ = parser.add_argument("--repeat", type=int, default=1)
    _ = parser.add_argument("--worlds-out", type=Path, default=None, help="Append each finished game's final worlds to this .jsonl.gz file")
    # for tests: "INDEX:oom", "INDEX:kill" or "INDEX:hang" makes the game at INDEX fail that way
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

    scenarios = load_scenarios(args.players, args.version, limit=args.start + args.count)[args.start:]
    for index, scenario in enumerate(scenarios, start=args.start):
        fault = fault_kind if index == fault_index else None
        result = run_game(scenario, args.players, args.timeout, args.repeat, fault, keep_worlds=args.worlds_out is not None)
        worlds = result.pop("worlds")
        if worlds is not None:
            append_worlds(args.worlds_out, scenario.id, worlds)
        _emit(out, {"type": "game", **result})
        if result["status"] == "oom":
            sys.exit(OOM_EXIT_CODE)

if __name__ == "__main__":
    main()
