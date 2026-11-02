import argparse
import sys

from . import compare, runner, worlds
from .tiers import TIERS

def _parse_timeouts(values: list[str]) -> dict[int, float]:
    timeouts: dict[int, float] = {}
    for value in values:
        players, seconds = value.split("=")
        timeouts[int(players)] = float(seconds)
    return timeouts

def main():
    parser = argparse.ArgumentParser(prog="python -m bench", description="Solver benchmarks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run a benchmark tier")
    _ = run.add_argument("--tier", choices=sorted(TIERS), required=True)
    _ = run.add_argument("--label", required=True, help="Name for this run, e.g. the change being measured")
    _ = run.add_argument("--players", type=int, nargs="+", help="Only run these player counts from the tier")
    _ = run.add_argument("--version", default="v1", help="Scenario version")
    _ = run.add_argument("--repeat", type=int, default=1, help="Run each game this many times and keep the fastest")
    _ = run.add_argument("--timeout", nargs="+", default=[], metavar="PLAYERS=SECONDS", help="Per game timeouts, e.g. 15=3600")
    _ = run.add_argument("--memory-gb", type=float, default=runner.DEFAULT_MEMORY_GB, help="Memory limit per worker process")
    _ = run.add_argument("--asserts", action="store_true", help="Keep asserts on (workers run with -O by default)")
    _ = run.add_argument("--no-csv", action="store_true", help="Don't append this run to results.csv")
    world_options = run.add_mutually_exclusive_group()
    _ = world_options.add_argument("--worlds", type=int, nargs="+", default=list(runner.DEFAULT_WORLDS), metavar="PLAYERS", help="Player counts whose final worlds are saved (default: 5 10)")
    _ = world_options.add_argument("--no-worlds", action="store_true", help="Don't save any final worlds")

    compare_parser = subparsers.add_parser("compare", help="Compare two runs game by game")
    _ = compare_parser.add_argument("a", nargs="?", default="baseline", help="Run to compare against: a path, 'baseline', 'latest' or part of a file name (default: baseline)")
    _ = compare_parser.add_argument("b", nargs="?", default="latest", help="Run to compare (default: latest)")
    _ = compare_parser.add_argument("--game", help="Show step by step detail for one game, e.g. 10p-0003")
    _ = compare_parser.add_argument("--force", action="store_true", help="Compare runs that use different scenario versions")

    worlds_parser = subparsers.add_parser("worlds", help="Compare the final worlds of two runs")
    _ = worlds_parser.add_argument("a", nargs="?", default="baseline", help="Run to compare against (default: baseline)")
    _ = worlds_parser.add_argument("b", nargs="?", default="latest", help="Run to compare (default: latest)")
    _ = worlds_parser.add_argument("--game", help="List every world that differs for one game, e.g. 5p-0074")

    baseline = subparsers.add_parser("baseline", help="Make a run the baseline (copied to bench/baseline.json)")
    _ = baseline.add_argument("run", nargs="?", default="latest", help="A path, 'latest' or part of a file name (default: latest)")

    args = parser.parse_args()
    try:
        _run_command(args)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

def _run_command(args: argparse.Namespace):
    if args.command == "run":
        _ = runner.run(
            tier=args.tier,
            label=args.label,
            players=args.players,
            version=args.version,
            timeouts=_parse_timeouts(args.timeout),
            memory_gb=args.memory_gb,
            repeat=args.repeat,
            asserts=args.asserts,
            write_csv=not args.no_csv,
            worlds=() if args.no_worlds else tuple(args.worlds),
        )
    elif args.command == "compare":
        run_a = compare.load_run(compare.resolve_run(args.a))
        run_b = compare.load_run(compare.resolve_run(args.b))
        if args.game:
            print(compare.format_game_steps(run_a, run_b, args.game))
        else:
            comparison = compare.compare_runs(run_a, run_b, force=args.force)
            print(compare.format_comparison(comparison))
            # only correctness problems fail the command; timings are too noisy for that
            if compare.has_regressions(comparison):
                sys.exit(1)
    elif args.command == "worlds":
        comparison = worlds.compare_worlds(compare.resolve_run(args.a), compare.resolve_run(args.b), args.game)
        print(worlds.format_world_comparison(comparison))
        # worlds that pass every check but were removed may be valid worlds that were lost
        if worlds.has_unexplained(comparison):
            sys.exit(1)
    elif args.command == "baseline":
        path = compare.resolve_run(args.run)
        compare.set_baseline(path)
        print(f"Baseline set to {path.name} (copied to {compare.BASELINE_PATH})")

if __name__ == "__main__":
    main()
