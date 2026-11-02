import argparse

from . import runner
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

    args = parser.parse_args()
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
        )

if __name__ == "__main__":
    main()
