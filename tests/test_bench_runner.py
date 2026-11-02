import csv
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from bench import report, runner
from bench.scenarios import load_scenarios
from bench.worker import run_game


def _game(game_id: str, status: str = "ok", seconds: float = 1.0, final: int = 10, peak: int = 20, world_steps: int = 50):
    return {
        "id": game_id,
        "seed": 0,
        "status": status,
        "error": None,
        "seconds": seconds if status == "ok" else None,
        "final_grims": final if status == "ok" else None,
        "peak_grims": peak,
        "peak_stage": "night 1 chef",
        "world_steps": world_steps,
        "steps": [],
    }

class TestWorker(unittest.TestCase):
    def test_run_game_records_steps(self):
        scenario = load_scenarios(5, limit=1)[0]
        result = run_game(scenario, 5, timeout=60)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["id"], "5p-0000")
        self.assertGreaterEqual(result["peak_grims"], result["final_grims"])
        self.assertEqual(result["world_steps"], sum(step[2] for step in result["steps"]))
        self.assertEqual(result["steps"][-1][0], "final remove_subsumed_grims")

    def test_repeat_keeps_fastest(self):
        scenario = load_scenarios(5, limit=1)[0]
        result = run_game(scenario, 5, timeout=60, repeat=3)
        self.assertEqual(result["status"], "ok", "Expected repeated runs to give identical world counts.")

class TestRunPlayerCount(unittest.TestCase):
    def test_ok_games(self):
        games, peak_rss_kb = runner.run_player_count(5, 3, progress=False)
        self.assertEqual([g["id"] for g in games], ["5p-0000", "5p-0001", "5p-0002"])
        self.assertTrue(all(g["status"] == "ok" for g in games))
        self.assertGreater(peak_rss_kb, 0)

    def test_memory_error_restarts_worker(self):
        games, _ = runner.run_player_count(5, 3, inject_fault="1:oom", progress=False)
        self.assertEqual([g["status"] for g in games], ["ok", "oom", "ok"])

    def test_killed_worker_restarts(self):
        games, _ = runner.run_player_count(5, 3, inject_fault="1:kill", progress=False)
        self.assertEqual([g["status"] for g in games], ["ok", "oom", "ok"])
        self.assertEqual(games[1]["id"], "5p-0001", "Expected the killed game to be the one reported.")

    def test_game_timeout(self):
        games, _ = runner.run_player_count(10, 2, timeout=0.01, progress=False)
        self.assertEqual([g["status"] for g in games], ["timeout", "timeout"], "Expected the run to continue after a timeout.")

    def test_watchdog_kills_silent_worker(self):
        with mock.patch.object(runner, "WATCHDOG_GRACE", 1.0):
            games, _ = runner.run_player_count(5, 3, timeout=0.5, inject_fault="1:hang", progress=False)
        self.assertEqual([g["status"] for g in games], ["ok", "timeout", "ok"])
        self.assertIn("killed", games[1]["error"])

class TestReport(unittest.TestCase):
    def test_summarize(self):
        games = [_game(f"5p-{i:04d}", seconds=float(i + 1), final=i, peak=10 * i) for i in range(20)]
        games.append(_game("5p-0020", status="timeout", peak=1000))
        summary = report.summarize(games, peak_rss_kb=2048)
        self.assertEqual(summary["games"], 21)
        self.assertEqual(summary["ok"], 20)
        self.assertEqual(summary["failures"], "timeout:1")
        self.assertEqual(summary["total_s"], sum(range(1, 21)), "Expected failed games to be left out of time totals.")
        self.assertEqual(summary["p95_s"], 19.0)
        self.assertEqual(summary["max_s"], 20.0)
        self.assertEqual(summary["peak_max"], 190, "Expected peaks to only count finished games.")
        self.assertEqual(summary["peak_max_game"], "5p-0019")
        self.assertEqual(summary["peak_rss_mb"], 2)

    def test_summarize_no_ok_games(self):
        summary = report.summarize([_game("15p-0006", status="oom")], peak_rss_kb=0)
        self.assertEqual(summary["ok"], 0)
        self.assertEqual(summary["failures"], "oom:1")
        self.assertNotIn("total_s", summary)

    def test_failure_location(self):
        steps = [["info {'kind': 'chef'}", 1, 50, 0.1], ["night 2 demon kill {'kind': 'demon'}", 50, 40, 0.1]]
        lost = _game("10p-0000", status="true_grim_lost") | {"steps": steps, "peak_stage": "info {'kind': 'chef'}"}
        self.assertEqual(report.failure_location(lost), " at night 2 demon kill", "Expected the failing step, not the peak step.")
        timed_out = _game("15p-0006", status="timeout") | {"steps": steps}
        self.assertEqual(report.failure_location(timed_out), " after night 2 demon kill")
        self.assertEqual(report.failure_location(_game("15p-0006", status="oom")), "", "Expected nothing when no steps were recorded.")

    def test_short_stage(self):
        self.assertEqual(report.short_stage("info {'kind': 'washerwoman', 'washerwoman': 1}"), "night 1 washerwoman")
        self.assertEqual(report.short_stage("night 3 fortune teller info."), "night 3 fortune teller info")
        self.assertEqual(report.short_stage("night 2 demon kill {'kind': 'demon', 'player': 1}"), "night 2 demon kill")

    def _result(self):
        meta = {c: "x" for c in report.META_COLUMNS}
        games = [_game("5p-0000")]
        return {"meta": meta, "players": {"5": {"summary": report.summarize(games, 1024), "games": games}}}

    def test_csv_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.csv"
            row = report.csv_row(self._result())
            report.append_csv(path, row)
            report.append_csv(path, row)
            with open(path, newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], report.COLUMNS, "Expected the header to be written once.")
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[1][report.COLUMNS.index("10p_games")], "", "Expected player counts that weren't run to be blank.")

    def test_csv_header_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.csv"
            _ = path.write_text("timestamp,label\n")
            with self.assertRaises(ValueError):
                report.append_csv(path, report.csv_row(self._result()))

    def test_tsv_matches_columns(self):
        line = report.tsv_line(report.csv_row(self._result()))
        self.assertEqual(len(line.split("\t")), len(report.COLUMNS))

class TestRun(unittest.TestCase):
    def test_run_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            results_dir = Path(tmp) / "results"
            csv_path = Path(tmp) / "results.csv"
            with mock.patch("sys.stdout"):
                result = runner.run("smoke", "Test run", players=[5], results_dir=results_dir, csv_path=csv_path)
            self.assertEqual(list(result["players"]), ["5"])
            self.assertEqual(result["players"]["5"]["summary"]["games"], 100)
            self.assertEqual(len(list(results_dir.glob("*_test-run.json"))), 1)
            with open(csv_path, newline="") as f:
                self.assertEqual(len(list(csv.reader(f))), 2)


if __name__ == "__main__":
    _ = unittest.main()
