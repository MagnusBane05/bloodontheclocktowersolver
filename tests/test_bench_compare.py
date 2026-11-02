import json
from pathlib import Path
import tempfile
import unittest
from typing import Any

from bench import compare, report


def _game(game_id: str, status: str = "ok", seconds: float = 1.0, final: int = 10, peak: int = 20, steps: list[list[Any]] | None = None) -> dict[str, Any]:
    return {
        "id": game_id,
        "seed": 0,
        "status": status,
        "error": "boom" if status != "ok" else None,
        "seconds": seconds if status == "ok" else None,
        "final_grims": final if status == "ok" else None,
        "peak_grims": peak,
        "peak_stage": "night 2 demon kill {'kind': 'demon'}",
        "world_steps": 50,
        "steps": steps if steps is not None else [],
    }

def _run(games: dict[str, list[dict[str, Any]]], **meta: Any) -> dict[str, Any]:
    run_meta = {
        "timestamp": "2026-11-02T12:00:00", "label": "run", "tier": "smoke", "scenario_version": "v1",
        "commit": "abc1234", "dirty": False, "repeat": 1, "asserts": False, "python": "3.14.3", "host": "host",
    }
    run_meta.update(meta)
    return {
        "meta": run_meta,
        "players": {p: {"summary": report.summarize(g, 1024), "games": g} for p, g in games.items()},
    }

class TestCompareRuns(unittest.TestCase):
    def test_only_shared_games_compared(self):
        a = _run({"5": [_game("5p-0000"), _game("5p-0001"), _game("5p-0002")]})
        b = _run({"5": [_game("5p-0000")], "10": [_game("10p-0000")]})
        result = compare.compare_runs(a, b)
        self.assertEqual(list(result["players"]), ["5"], "Expected only player counts in both runs.")
        self.assertEqual(result["players"]["5"]["compared"], 1)
        self.assertEqual(result["players"]["5"]["only_a"], 2)

    def test_scenario_version_mismatch(self):
        a = _run({"5": [_game("5p-0000")]})
        b = _run({"5": [_game("5p-0000")]}, scenario_version="v2")
        with self.assertRaises(ValueError):
            _ = compare.compare_runs(a, b)
        _ = compare.compare_runs(a, b, force=True)

    def test_warnings(self):
        a = _run({"5": [_game("5p-0000")]})
        b = _run({"5": [_game("5p-0000")]}, repeat=3, dirty=True)
        warnings = compare.compare_runs(a, b)["warnings"]
        self.assertTrue(any("repeat" in w for w in warnings))
        self.assertTrue(any("B was run with uncommitted changes" in w for w in warnings))

    def test_worse_and_fixed(self):
        a = _run({"5": [_game("5p-0000"), _game("5p-0001", status="timeout")]})
        b = _run({"5": [_game("5p-0000", status="true_grim_lost"), _game("5p-0001")]})
        result = compare.compare_runs(a, b)
        data = result["players"]["5"]
        self.assertEqual([(w["id"], w["after"]) for w in data["worse"]], [("5p-0000", "true_grim_lost")])
        self.assertEqual([f["id"] for f in data["fixed"]], ["5p-0001"])
        self.assertTrue(compare.has_regressions(result))
        self.assertIn("GOT WORSE", compare.format_comparison(result))

    def test_no_regressions(self):
        a = _run({"5": [_game("5p-0000")]})
        self.assertFalse(compare.has_regressions(compare.compare_runs(a, a)))

    def test_final_changes(self):
        a = _run({"5": [_game("5p-0000", final=10), _game("5p-0001", final=10), _game("5p-0002", final=10)]})
        b = _run({"5": [_game("5p-0000", final=4), _game("5p-0001", final=12), _game("5p-0002", final=10)]})
        changes = compare.compare_runs(a, b)["players"]["5"]["final_changes"]
        self.assertEqual([c["id"] for c in changes], ["5p-0000", "5p-0001"], "Expected changes ordered by size.")

    def test_slowdowns_skip_fast_games(self):
        a = _run({"5": [_game("5p-0000", seconds=0.001), _game("5p-0001", seconds=1.0), _game("5p-0002", seconds=1.0)]})
        b = _run({"5": [_game("5p-0000", seconds=0.005), _game("5p-0001", seconds=3.0), _game("5p-0002", seconds=0.5)]})
        data = compare.compare_runs(a, b)["players"]["5"]
        self.assertEqual([s["id"] for s in data["slowdowns"]], ["5p-0001"], "Expected games under the cut-off to be skipped.")
        self.assertAlmostEqual(data["slowdowns"][0]["ratio"], 3.0)
        self.assertEqual([s["id"] for s in data["speedups"]], ["5p-0002"])

    def test_peak_increases(self):
        a = _run({"5": [_game("5p-0000", peak=10), _game("5p-0001", peak=10)]})
        b = _run({"5": [_game("5p-0000", peak=50), _game("5p-0001", peak=5)]})
        increases = compare.compare_runs(a, b)["players"]["5"]["peak_increases"]
        self.assertEqual([(p["id"], p["before"], p["after"]) for p in increases], [("5p-0000", 10, 50)])

class TestPercentChange(unittest.TestCase):
    def test_percent_change(self):
        self.assertEqual(compare.percent_change(10, 12), "+20.0%")
        self.assertEqual(compare.percent_change(10, 5), "-50.0%")
        self.assertEqual(compare.percent_change(0, 0), "")
        self.assertEqual(compare.percent_change(0, 3), "new")
        self.assertEqual(compare.percent_change("", 3), "")

class TestResolveRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.results_dir = Path(self.tmp.name) / "results"
        self.results_dir.mkdir()
        for name in ("20261101-100000_baseline.json", "20261102-100000_cache-clones.json", "20261102-110000_cache-sets.json"):
            _ = (self.results_dir / name).write_text("{}")
        self.baseline_path = Path(self.tmp.name) / "baseline.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _resolve(self, name: str) -> Path:
        return compare.resolve_run(name, self.results_dir, self.baseline_path)

    def test_latest(self):
        self.assertEqual(self._resolve("latest").name, "20261102-110000_cache-sets.json")

    def test_partial_name(self):
        self.assertEqual(self._resolve("clones").name, "20261102-100000_cache-clones.json")

    def test_ambiguous_partial_name(self):
        with self.assertRaises(ValueError):
            _ = self._resolve("cache")

    def test_no_match(self):
        with self.assertRaises(FileNotFoundError):
            _ = self._resolve("nothing")

    def test_baseline(self):
        with self.assertRaises(FileNotFoundError):
            _ = self._resolve("baseline")
        compare.set_baseline(self.results_dir / "20261102-100000_cache-clones.json", self.baseline_path)
        self.assertEqual(self._resolve("baseline"), self.baseline_path)
        self.assertEqual(json.loads(self.baseline_path.read_text()), {})

class TestGameSteps(unittest.TestCase):
    def test_steps_line_up(self):
        steps_a = [["info {'kind': 'chef'}", 1, 5, 0.1], ["night 2 demon kill {'kind': 'demon'}", 5, 9, 0.2]]
        steps_b = [["info {'kind': 'chef'}", 1, 5, 0.1], ["night 2 demon kill {'kind': 'demon'}", 5, 7, 0.3]]
        a = _run({"5": [_game("5p-0000", steps=steps_a)]})
        b = _run({"5": [_game("5p-0000", steps=steps_b)]})
        lines = compare.format_game_steps(a, b, "5p-0000").splitlines()
        demon_kill = next(line for line in lines if line.startswith("night 2 demon kill"))
        self.assertEqual(demon_kill.split()[4:6], ["9", "7"], "Expected matching steps on the same row.")

    def test_failed_game_stops_early(self):
        steps_a = [["info {'kind': 'chef'}", 1, 5, 0.1], ["night 2 demon kill {'kind': 'demon'}", 5, 9, 0.2]]
        steps_b = [["info {'kind': 'chef'}", 1, 5, 0.1]]
        a = _run({"5": [_game("5p-0000", steps=steps_a)]})
        b = _run({"5": [_game("5p-0000", status="oom", steps=steps_b)]})
        output = compare.format_game_steps(a, b, "5p-0000")
        self.assertIn("A ok, B oom", output)
        self.assertIn("night 2 demon kill", output, "Expected steps only in A to still be shown.")

    def test_missing_game(self):
        a = _run({"5": [_game("5p-0000")]})
        with self.assertRaises(ValueError):
            _ = compare.format_game_steps(a, a, "5p-0001")


if __name__ == "__main__":
    _ = unittest.main()
