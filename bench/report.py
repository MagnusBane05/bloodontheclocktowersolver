"""Summaries, results.csv rows, and printed output for benchmark runs."""
from collections import Counter
import csv
import math
from pathlib import Path
import re
import statistics
from typing import Any

PLAYER_COUNTS = (5, 10, 15)

META_COLUMNS = [
    "timestamp", "label", "tier", "scenario_version", "commit", "dirty",
    "repeat", "asserts", "python", "host",
]
SUMMARY_COLUMNS = [
    "games", "ok", "failures",
    "total_s", "median_s", "p95_s", "min_s", "max_s",
    "final_min", "final_avg", "final_max",
    "peak_max", "peak_max_game", "peak_avg", "world_steps",
    "peak_rss_mb",
]
COLUMNS = META_COLUMNS + [f"{p}p_{c}" for p in PLAYER_COUNTS for c in SUMMARY_COLUMNS]

def slugify(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:50] or "run"

def short_stage(stage: str) -> str:
    """Shortens stage labels that embed a whole info dict, e.g. "info {...'kind': 'chef'...}"."""
    if stage.startswith("info {"):
        kind = re.search(r"'kind': '([^']+)'", stage)
        return f"night 1 {kind.group(1)}" if kind else "night 1 info"
    return stage.split(" {")[0].rstrip(".")

def _percentile(sorted_values: list[float], fraction: float) -> float:
    # nearest-rank percentile
    return sorted_values[max(0, math.ceil(fraction * len(sorted_values)) - 1)]

def summarize(games: list[dict[str, Any]], peak_rss_kb: int) -> dict[str, Any]:
    # times and world counts only cover games that finished, so a timeout doesn't skew them
    ok = [g for g in games if g["status"] == "ok"]
    failures = Counter(g["status"] for g in games if g["status"] != "ok")
    summary: dict[str, Any] = {
        "games": len(games),
        "ok": len(ok),
        "failures": ";".join(f"{status}:{n}" for status, n in sorted(failures.items())),
        "peak_rss_mb": round(peak_rss_kb / 1024),
    }
    if ok:
        times = sorted(g["seconds"] for g in ok)
        finals = [g["final_grims"] for g in ok]
        peak_game = max(ok, key=lambda g: g["peak_grims"] or 0)
        summary.update({
            "total_s": round(sum(times), 3),
            "median_s": round(statistics.median(times), 4),
            "p95_s": round(_percentile(times, 0.95), 4),
            "min_s": round(times[0], 4),
            "max_s": round(times[-1], 4),
            "final_min": min(finals),
            "final_avg": round(statistics.mean(finals), 1),
            "final_max": max(finals),
            "peak_max": peak_game["peak_grims"],
            "peak_max_game": peak_game["id"],
            "peak_avg": round(statistics.mean(g["peak_grims"] or 0 for g in ok), 1),
            "world_steps": sum(g["world_steps"] for g in ok),
        })
    return summary

def csv_row(result: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {c: result["meta"][c] for c in META_COLUMNS}
    for p in PLAYER_COUNTS:
        summary = result["players"].get(str(p), {}).get("summary", {})
        for c in SUMMARY_COLUMNS:
            row[f"{p}p_{c}"] = summary.get(c, "")
    return row

def append_csv(path: Path, row: dict[str, Any]):
    if path.exists():
        with open(path, newline="") as f:
            header = next(csv.reader(f), None)
        if header != COLUMNS:
            raise ValueError(
                f"{path} has different columns than this version of the benchmark. " +
                "Start a new CSV file instead of appending misaligned rows."
            )
        with open(path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=COLUMNS).writerow(row)
    else:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerow(row)

def tsv_line(row: dict[str, Any]) -> str:
    return "\t".join(str(row[c]) for c in COLUMNS)

def format_summary(result: dict[str, Any]) -> str:
    meta = result["meta"]
    lines = [
        "",
        f"{meta['label']}  (tier {meta['tier']}, commit {meta['commit']}{' + uncommitted changes' if meta['dirty'] else ''})",
    ]

    problems = [
        (p, g)
        for p, data in result["players"].items()
        for g in data["games"]
        if g["status"] != "ok"
    ]
    if problems:
        lines.append("")
        lines.append("Games that didn't finish:")
        for _, g in problems:
            where = f" at {short_stage(g['peak_stage'])}" if g["peak_stage"] else ""
            detail = f": {g['error']}" if g["error"] else ""
            lines.append(f"  {g['id']} {g['status']}{where}{detail}")

    lines.append("")
    lines.append(f"{'players':>7} {'ok':>9} {'total s':>10} {'median s':>9} {'p95 s':>8} {'max s':>8} {'final avg':>9} {'peak max':>9} {'peak game':>10} {'rss MB':>7}")
    for p, data in result["players"].items():
        s = data["summary"]
        lines.append(
            f"{p:>7} {str(s['ok']) + '/' + str(s['games']):>9} {s.get('total_s', ''):>10} {s.get('median_s', ''):>9} " +
            f"{s.get('p95_s', ''):>8} {s.get('max_s', ''):>8} {s.get('final_avg', ''):>9} {s.get('peak_max', ''):>9} " +
            f"{s.get('peak_max_game', ''):>10} {s['peak_rss_mb']:>7}"
        )
    lines.append("")
    return "\n".join(lines)
