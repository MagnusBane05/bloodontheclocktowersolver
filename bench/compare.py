"""Compares two benchmark runs game by game."""
from difflib import SequenceMatcher
import json
from pathlib import Path
import shutil
from typing import Any

from . import report
from .runner import RESULTS_DIR
from .worlds import worlds_dir

BASELINE_PATH = Path(__file__).parent / "baseline.json"
# games faster than this in both runs are left out of the slowdown list, since a few
# milliseconds of noise looks like a big percentage change
MIN_SECONDS_FOR_RATIO = 0.02
SLOWDOWNS_SHOWN = 5
SPEEDUPS_SHOWN = 3
PEAK_INCREASES_SHOWN = 5
FINAL_CHANGES_SHOWN = 5
# settings that make timings less comparable when they differ between runs
COMPARABILITY_KEYS = ("repeat", "asserts", "host")

PERFORMANCE_METRICS = [
    ("total s", "total_s"),
    ("median s", "median_s"),
    ("p95 s", "p95_s"),
    ("slowest s", "max_s"),
    ("peak max", "peak_max"),
    ("peak avg", "peak_avg"),
    ("world-steps", "world_steps"),
    ("known invalid", "known_invalid"),
    ("memory MB", "peak_rss_mb"),
]

def resolve_run(name: str, results_dir: Path = RESULTS_DIR, baseline_path: Path = BASELINE_PATH) -> Path:
    """Finds a run by path, "baseline", "latest", or part of its file name."""
    if name == "baseline":
        if not baseline_path.exists():
            raise FileNotFoundError("No baseline yet. Set one with `python -m bench baseline <run>`.")
        return baseline_path
    path = Path(name)
    if path.exists():
        return path
    # file names start with a timestamp, so sorting by name is chronological
    runs = sorted(results_dir.glob("*.json"))
    if name == "latest":
        if not runs:
            raise FileNotFoundError(f"No runs in {results_dir}.")
        return runs[-1]
    matches = [run for run in runs if name in run.name]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"No run in {results_dir} matches '{name}'.")
    raise ValueError(f"'{name}' matches more than one run: " + ", ".join(m.name for m in matches))

def load_run(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)

def set_baseline(run_path: Path, baseline_path: Path = BASELINE_PATH):
    _ = shutil.copyfile(run_path, baseline_path)
    # replace the baseline's worlds too, so they never come from a different run
    baseline_worlds = worlds_dir(baseline_path)
    if baseline_worlds.exists():
        shutil.rmtree(baseline_worlds)
    run_worlds = worlds_dir(run_path)
    if run_worlds.exists():
        _ = shutil.copytree(run_worlds, baseline_worlds)

def percent_change(a: Any, b: Any) -> str:
    if a in (None, "") or b in (None, ""):
        return ""
    if a == 0:
        return "" if b == 0 else "new"
    return f"{(b - a) / a * 100:+.1f}%"

def _games_by_id(run: dict[str, Any], players: str) -> dict[str, dict[str, Any]]:
    return {g["id"]: g for g in run["players"][players]["games"]}

def compare_runs(a: dict[str, Any], b: dict[str, Any], force: bool = False) -> dict[str, Any]:
    if a["meta"]["scenario_version"] != b["meta"]["scenario_version"] and not force:
        raise ValueError(
            f"The runs use different scenario versions ({a['meta']['scenario_version']} and " +
            f"{b['meta']['scenario_version']}), so their games differ. Use --force to compare anyway."
        )

    warnings: list[str] = []
    for key in COMPARABILITY_KEYS:
        if a["meta"][key] != b["meta"][key]:
            warnings.append(f"{key} differs: {a['meta'][key]} vs {b['meta'][key]}")
    for name, run in (("A", a), ("B", b)):
        if run["meta"]["dirty"]:
            warnings.append(f"{name} was run with uncommitted changes")

    by_players: dict[str, Any] = {}
    for players in sorted(set(a["players"]) & set(b["players"]), key=int):
        games_a = _games_by_id(a, players)
        games_b = _games_by_id(b, players)
        common = sorted(set(games_a) & set(games_b))
        both_ok = [i for i in common if games_a[i]["status"] == "ok" and games_b[i]["status"] == "ok"]

        worse = [
            {"id": i, "before": games_a[i]["status"], "after": games_b[i]["status"], "error": games_b[i]["error"]}
            for i in common
            if games_a[i]["status"] == "ok" and games_b[i]["status"] != "ok"
        ]
        fixed = [
            {"id": i, "before": games_a[i]["status"], "after": games_b[i]["status"]}
            for i in common
            if games_a[i]["status"] != "ok" and games_b[i]["status"] == "ok"
        ]
        final_changes = sorted(
            (
                {"id": i, "before": games_a[i]["final_grims"], "after": games_b[i]["final_grims"]}
                for i in both_ok
                if games_a[i]["final_grims"] != games_b[i]["final_grims"]
            ),
            key=lambda c: -abs(c["after"] - c["before"]),
        )

        timed = [
            {
                "id": i,
                "before": games_a[i]["seconds"],
                "after": games_b[i]["seconds"],
                "ratio": games_b[i]["seconds"] / games_a[i]["seconds"],
                "stage": games_b[i]["peak_stage"],
            }
            for i in both_ok
            if max(games_a[i]["seconds"], games_b[i]["seconds"]) >= MIN_SECONDS_FOR_RATIO
            and games_a[i]["seconds"] > 0
        ]
        slowdowns = sorted((t for t in timed if t["ratio"] > 1), key=lambda t: -t["ratio"])[:SLOWDOWNS_SHOWN]
        speedups = sorted((t for t in timed if t["ratio"] < 1), key=lambda t: t["ratio"])[:SPEEDUPS_SHOWN]
        peak_increases = sorted(
            (
                {
                    "id": i,
                    "before": games_a[i]["peak_grims"],
                    "after": games_b[i]["peak_grims"],
                    "stage": games_b[i]["peak_stage"],
                }
                for i in both_ok
                if (games_b[i]["peak_grims"] or 0) > (games_a[i]["peak_grims"] or 0)
            ),
            key=lambda p: -(p["after"] - (p["before"] or 0)),
        )[:PEAK_INCREASES_SHOWN]

        # memory can't be split per game, so it comes from the whole run
        summary_a = report.summarize([games_a[i] for i in both_ok], 0)
        summary_b = report.summarize([games_b[i] for i in both_ok], 0)
        summary_a["peak_rss_mb"] = a["players"][players]["summary"]["peak_rss_mb"]
        summary_b["peak_rss_mb"] = b["players"][players]["summary"]["peak_rss_mb"]

        by_players[players] = {
            "compared": len(common),
            "only_a": len(games_a) - len(common),
            "only_b": len(games_b) - len(common),
            "both_ok": len(both_ok),
            "worse": worse,
            "fixed": fixed,
            "final_changes": final_changes,
            "summary_a": summary_a,
            "summary_b": summary_b,
            "slowdowns": slowdowns,
            "speedups": speedups,
            "peak_increases": peak_increases,
        }

    return {"a": a["meta"], "b": b["meta"], "warnings": warnings, "players": by_players}

def has_regressions(comparison: dict[str, Any]) -> bool:
    return any(data["worse"] for data in comparison["players"].values())

def _describe(meta: dict[str, Any]) -> str:
    dirty = " + uncommitted changes" if meta["dirty"] else ""
    return f"{meta['label']}  (tier {meta['tier']}, commit {meta['commit']}{dirty}, {meta['timestamp']})"

def _stage(stage: str | None) -> str:
    return report.short_stage(stage) if stage else ""

def format_comparison(comparison: dict[str, Any]) -> str:
    lines = [
        "",
        f"A: {_describe(comparison['a'])}",
        f"B: {_describe(comparison['b'])}",
    ]
    for warning in comparison["warnings"]:
        lines.append(f"Warning: {warning}")

    for players, data in comparison["players"].items():
        lines.append("")
        lines.append(f"=== {players} players: {data['compared']} games compared ===")
        if data["only_a"] or data["only_b"]:
            lines.append(f"(skipped {data['only_a']} games only in A and {data['only_b']} only in B)")

        lines.append("")
        lines.append("Correctness")
        if data["worse"]:
            lines.append(f"  GOT WORSE ({len(data['worse'])}):")
            for w in data["worse"]:
                detail = f": {w['error']}" if w["error"] else ""
                lines.append(f"    {w['id']} {w['before']} -> {w['after']}{detail}")
        else:
            lines.append("  Got worse: none")
        if data["fixed"]:
            lines.append(f"  Got fixed ({len(data['fixed'])}):")
            for f in data["fixed"]:
                lines.append(f"    {f['id']} {f['before']} -> {f['after']}")
        changes = data["final_changes"]
        if changes:
            down = sum(1 for c in changes if c["after"] < c["before"])
            lines.append(f"  Final world counts changed in {len(changes)} games ({down} down, {len(changes) - down} up). Biggest:")
            for c in changes[:FINAL_CHANGES_SHOWN]:
                lines.append(f"    {c['id']} {c['before']} -> {c['after']}")
            lines.append("  Run `python -m bench worlds` to see which worlds changed and whether any valid ones were lost.")
        else:
            lines.append("  Final world counts: unchanged")

        lines.append("")
        lines.append(f"Performance ({data['both_ok']} games that finished in both runs)")
        lines.append(f"  {'':<12} {'A':>12} {'B':>12} {'change':>9}")
        for label, key in PERFORMANCE_METRICS:
            a_value = data["summary_a"].get(key, "")
            b_value = data["summary_b"].get(key, "")
            lines.append(f"  {label:<12} {a_value!s:>12} {b_value!s:>12} {percent_change(a_value, b_value):>9}")

        if data["slowdowns"]:
            lines.append("")
            lines.append("Biggest slowdowns")
            for t in data["slowdowns"]:
                lines.append(f"  {t['id']} {t['before']:.3f}s -> {t['after']:.3f}s ({t['ratio']:.2f}x)  peak at {_stage(t['stage'])}")
        if data["speedups"]:
            lines.append("")
            lines.append("Biggest speed-ups")
            for t in data["speedups"]:
                lines.append(f"  {t['id']} {t['before']:.3f}s -> {t['after']:.3f}s ({t['ratio']:.2f}x)")
        if data["peak_increases"]:
            lines.append("")
            lines.append("Biggest peak increases")
            for p in data["peak_increases"]:
                lines.append(f"  {p['id']} {p['before']} -> {p['after']} at {_stage(p['stage'])}")

    lines.append("")
    return "\n".join(lines)

def format_game_steps(a: dict[str, Any], b: dict[str, Any], game_id: str) -> str:
    players = game_id.split("p-")[0]
    games = []
    for name, run in (("A", a), ("B", b)):
        if players not in run["players"]:
            raise ValueError(f"Run {name} has no {players} player games.")
        game = _games_by_id(run, players).get(game_id)
        if game is None:
            raise ValueError(f"Run {name} doesn't include {game_id}.")
        games.append(game)
    game_a, game_b = games

    lines = [
        "",
        f"{game_id}: A {game_a['status']}, B {game_b['status']}",
        f"{'stage':<40} {'worlds A':>9} {'worlds B':>9} {'time A':>9} {'time B':>9}",
    ]

    def row(stage: str, step_a: list[Any] | None, step_b: list[Any] | None):
        worlds_a = step_a[2] if step_a else ""
        worlds_b = step_b[2] if step_b else ""
        time_a = f"{step_a[3]:.4f}" if step_a else ""
        time_b = f"{step_b[3]:.4f}" if step_b else ""
        lines.append(f"{_stage(stage)[:40]:<40} {worlds_a!s:>9} {worlds_b!s:>9} {time_a:>9} {time_b:>9}")

    steps_a, steps_b = game_a["steps"], game_b["steps"]
    # the scenarios are fixed so the steps normally line up, but a failed game stops early
    matcher = SequenceMatcher(a=[s[0] for s in steps_a], b=[s[0] for s in steps_b], autojunk=False)
    for tag, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if tag == "equal":
            for step_a, step_b in zip(steps_a[a_start:a_end], steps_b[b_start:b_end]):
                row(step_a[0], step_a, step_b)
        else:
            for step_a in steps_a[a_start:a_end]:
                row(step_a[0], step_a, None)
            for step_b in steps_b[b_start:b_end]:
                row(step_b[0], None, step_b)

    lines.append("")
    return "\n".join(lines)
