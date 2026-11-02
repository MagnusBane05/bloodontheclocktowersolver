from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import pstats
import signal
import tempfile
import unittest

from bench import profiler
from bench.profiler_worker import profile_game
from bench.worker import _on_alarm  # pyright: ignore[reportPrivateUsage]
from bench.scenarios import load_scenarios


class TestSelection(unittest.TestCase):
    def test_parse_game_id(self):
        self.assertEqual(profiler.parse_game_id("10p-0003"), (10, 3))
        with self.assertRaises(ValueError):
            _ = profiler.parse_game_id("10-3")

    def test_parse_indices(self):
        self.assertEqual(profiler.parse_indices("3-5"), [3, 4, 5])
        self.assertEqual(profiler.parse_indices("9,1,4,1"), [1, 4, 9])
        self.assertEqual(profiler.parse_indices("0-1,7"), [0, 1, 7])
        for bad in ("5-3", "a", ",", "1-"):
            with self.assertRaises(ValueError, msg=bad):
                _ = profiler.parse_indices(bad)

    def test_defaults(self):
        self.assertEqual(
            profiler.select_games(),
            {p: list(range(n)) for p, n in profiler.DEFAULT_GAMES.items()},
        )
        self.assertEqual(profiler.select_games(players=[15]), {15: [0]})

    def test_game_ids_grouped_by_player_count(self):
        selection = profiler.select_games(game_ids=["15p-0000", "5p-0007", "5p-0002"])
        self.assertEqual(selection, {5: [2, 7], 15: [0]})
        self.assertEqual(list(selection), [5, 15], "Expected player counts in order.")

    def test_players_narrows_selection(self):
        self.assertEqual(profiler.select_games(players=[5], game_ids=["5p-0001", "10p-0001"]), {5: [1]})
        self.assertEqual(profiler.select_games(players=[10], tier="smoke"), {10: [0, 1, 2]})
        self.assertEqual(profiler.select_games(players=[5, 10], count=2), {5: [0, 1], 10: [0, 1]})
        self.assertEqual(profiler.select_games(players=[10], indices="2-3"), {10: [2, 3]})

    def test_tier_skips_empty_player_counts(self):
        self.assertNotIn(15, profiler.select_games(tier="smoke"))

    def test_invalid_selection(self):
        with self.assertRaises(ValueError):
            _ = profiler.select_games(count=2, tier="smoke")
        with self.assertRaises(ValueError):
            _ = profiler.select_games(count=0)
        with self.assertRaises(ValueError):
            _ = profiler.select_games(players=[15], tier="smoke")

class TestStages(unittest.TestCase):
    def test_stage_kind(self):
        self.assertEqual(profiler.stage_kind("night 2 empath info."), "empath")
        self.assertEqual(profiler.stage_kind("night 3 demon kill {'player': 4, 'night': 3, 'kind': 'demon'}"), "demon kill")
        self.assertEqual(profiler.stage_kind("night 1 death {'player': 6, 'night': 1, 'kind': 'execution'}"), "death")
        self.assertEqual(profiler.stage_kind("info {'kind': 'claim', 'player': 6, 'character': <Role.MAYOR: 13>}"), "claim")
        self.assertEqual(profiler.stage_kind("final remove_subsumed_grims"), "final remove_subsumed_grims")

    def test_stage_breakdown(self):
        games = [
            {"steps": [["night 1 chef info.", 1, 10, 0.5], ["night 2 chef info.", 10, 4, 0.25]]},
            {"steps": [["night 1 death {'player': 1}", 5, 20, 1.0]]},
        ]
        rows = profiler.stage_breakdown(games)
        self.assertEqual([r["kind"] for r in rows], ["death", "chef"], "Expected the slowest stage first.")
        self.assertEqual(rows[1], {"kind": "chef", "steps": 2, "seconds": 0.75, "world_steps": 14, "max_worlds": 10})

class TestProfileGame(unittest.TestCase):
    def test_profile_written(self):
        scenario = load_scenarios(5, limit=1)[0]
        with tempfile.TemporaryDirectory() as tmp:
            prof_path = Path(tmp) / "game.prof"
            result = profile_game(scenario, 5, timeout=60, prof_path=prof_path)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["world_steps"], sum(s[2] for s in result["steps"]))
            stats: dict[tuple[str, int, str], tuple[int, int, float, float, object]] = pstats.Stats(str(prof_path)).stats  # pyright: ignore[reportAttributeAccessIssue]
            self.assertTrue(any(key[0].endswith("add_info_to_grims.py") for key in stats), "Expected solver functions in the profile.")
            # on_step's call is recorded before it turns the profiler off, but none of its work is
            total = sum(v[2] for v in stats.values())
            bookkeeping = sum(v[3] for key, v in stats.items() if key[0].endswith("profiler_worker.py"))
            self.assertLess(bookkeeping, total * 0.05, "Expected the step bookkeeping to be left out of the profile.")

    def test_memory(self):
        scenario = load_scenarios(5, limit=1)[0]
        with tempfile.TemporaryDirectory() as tmp:
            result = profile_game(scenario, 5, timeout=60, prof_path=Path(tmp) / "game.prof", memory=True)
            self.assertTrue(all(s[5] is not None and s[6] is not None for s in result["steps"]))
            self.assertIsNotNone(result["memory_peak_stage"])
            self.assertTrue(result["top_allocations"])
            self.assertFalse(any("profiler_worker" in a[0] for a in result["top_allocations"]))

    def test_failed_game_still_profiled(self):
        scenario = load_scenarios(10, limit=1)[0]
        with tempfile.TemporaryDirectory() as tmp:
            prof_path = Path(tmp) / "game.prof"
            previous = signal.signal(signal.SIGALRM, _on_alarm)
            try:
                result = profile_game(scenario, 10, timeout=0.05, prof_path=prof_path)
            finally:
                _ = signal.signal(signal.SIGALRM, previous)
            self.assertEqual(result["status"], "timeout")
            self.assertTrue(prof_path.exists(), "Expected a partial profile for a game that didn't finish.")

class TestProfilePlayerCount(unittest.TestCase):
    def test_games_in_selection_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            games = profiler.profile_player_count(5, [3, 0], Path(tmp), progress=False)
            self.assertEqual([g["id"] for g in games], ["5p-0003", "5p-0000"])
            self.assertTrue((Path(tmp) / "5p-0003.prof").exists())

    def test_oom_restarts_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            games = profiler.profile_player_count(5, [0, 1, 2], Path(tmp), inject_fault="1:oom", progress=False)
            self.assertEqual([g["status"] for g in games], ["ok", "oom", "ok"])

    def test_killed_worker_restarts(self):
        with tempfile.TemporaryDirectory() as tmp:
            games = profiler.profile_player_count(5, [0, 1, 2], Path(tmp), inject_fault="1:kill", progress=False)
            self.assertEqual([g["status"] for g in games], ["ok", "oom", "ok"])
            self.assertEqual(games[1]["id"], "5p-0001", "Expected the killed game to be the one reported.")
            self.assertFalse((Path(tmp) / "5p-0001.prof").exists())

    def test_bad_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                _ = profiler.profile_player_count(15, [99999], Path(tmp), progress=False)

class TestRun(unittest.TestCase):
    def _run(self, tmp: str, **kwargs: object):
        with redirect_stdout(io.StringIO()) as out:
            result, out_dir = profiler.run({5: [0, 1]}, label="test run", profiles_dir=Path(tmp), progress=False, **kwargs)  # pyright: ignore[reportArgumentType]
        return result, out_dir, out.getvalue()

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, out_dir, printed = self._run(tmp, top=5)
            self.assertTrue(out_dir.name.endswith("_test-run"))
            self.assertEqual(result["players"]["5"]["profile"], "5p.prof")
            self.assertFalse((out_dir / "5p_games").exists(), "Expected per-game profiles to be removed by default.")

            merged = pstats.Stats(str(out_dir / "5p.prof"))
            self.assertGreater(merged.total_calls, 0)  # pyright: ignore[reportAttributeAccessIssue]

            with open(out_dir / "meta.json") as f:
                saved = json.load(f)
            self.assertEqual([g["id"] for g in saved["players"]["5"]["games"]], ["5p-0000", "5p-0001"])
            self.assertEqual(saved["meta"]["games"], {"5": ["5p-0000", "5p-0001"]})

            summary = (out_dir / "summary.txt").read_text()
            self.assertEqual(summary.rstrip(), printed.rstrip())
            self.assertIn("Time by stage", summary)
            self.assertIn("Top 5 functions by tottime", summary)
            self.assertIn("Top 5 functions by cumtime", summary)

    def test_merged_profile_adds_games(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out_dir, _ = self._run(tmp, per_game=True)
            games_dir = out_dir / "5p_games"
            per_game = [pstats.Stats(str(games_dir / f"5p-000{i}.prof")) for i in range(2)]
            merged = pstats.Stats(str(out_dir / "5p.prof"))
            self.assertEqual(
                merged.total_calls,  # pyright: ignore[reportAttributeAccessIssue]
                sum(s.total_calls for s in per_game),  # pyright: ignore[reportAttributeAccessIssue]
            )

    def test_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out_dir, _ = self._run(tmp, restrict="validators")
            table = profiler.format_functions(out_dir / "5p.prof", "tottime", 10, "validators")
            rows = table.splitlines()[1:]
            self.assertTrue(rows)
            self.assertTrue(all("grimoire/validators.py" in r for r in rows))

if __name__ == "__main__":
    _ = unittest.main()
