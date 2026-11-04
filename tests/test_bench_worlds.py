import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from bench import compare, report, runner, worlds
from bench.scenarios import _pages_equal, load_scenarios  # pyright: ignore[reportPrivateUsage]
from bench.worker import run_game
from grimoire import Grimoire, GrimoireManager, GrimoirePage, NightOrderPosition, Role
from grimoire.add_info_to_grims import find_finalize_problem
from grimoire.errors import FinalizeDidNotSettleError


def _world(characters: list[Role], minion_types: list[Role]) -> Grimoire:
    grim = Grimoire(5)
    grim.pages[0].characters = list(characters)
    grim.pages[0].minion_types = list(minion_types)
    return grim

# 5 players with a Baron: 1 townsfolk, 2 outsiders, 1 minion, 1 demon
VALID = [Role.IMP, Role.BARON, Role.SAINT, Role.RECLUSE, Role.CHEF]
TWO_IMPS = [Role.IMP, Role.IMP, Role.SAINT, Role.RECLUSE, Role.CHEF]

def _uncovered_index(grims: list[Grimoire]) -> int:
    """A world that no other world in the list covers, so removing it can't count as merged."""
    return next(
        i for i, g in enumerate(grims)
        if not any(j != i and other.subsumes(g) for j, other in enumerate(grims))
    )

class TestWorldFiles(unittest.TestCase):
    def test_append_and_load(self):
        scenario = load_scenarios(5, limit=1)[0]
        manager = GrimoireManager({"players": 5}, scenario.true_grim)
        manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "5p.jsonl.gz"
            # two separate appends, like a worker being restarted
            worlds.append_worlds(path, "5p-0000", manager.grims)
            worlds.append_worlds(path, "5p-0001", manager.grims[:1])
            loaded = worlds.load_worlds(path)
        self.assertEqual(list(loaded), ["5p-0000", "5p-0001"])
        self.assertEqual(len(loaded["5p-0000"]), len(manager.grims))
        for saved, original in zip(loaded["5p-0000"], manager.grims):
            self.assertTrue(_pages_equal(saved, original), "Expected every page field to survive saving.")

class TestKnownInvalid(unittest.TestCase):
    def test_counted_when_worlds_kept(self):
        # 5p-0030 ends with at least one world that role assignment rejects
        scenario = load_scenarios(5, limit=31)[30]
        result = run_game(scenario, 5, timeout=60, keep_worlds=True)
        self.assertGreaterEqual(result["known_invalid"], 1)
        self.assertEqual(result["known_invalid"], worlds.count_known_invalid(result["worlds"]))

    def test_not_counted_without_worlds(self):
        scenario = load_scenarios(5, limit=1)[0]
        result = run_game(scenario, 5, timeout=60)
        self.assertIsNone(result["known_invalid"])
        self.assertIsNone(result["worlds"])
        self.assertNotIn("known_invalid", report.summarize([result], 0))

    def test_summary_total(self):
        games = [
            {"id": f"5p-{i:04d}", "status": "ok", "seconds": 1.0, "final_grims": 1, "peak_grims": 1, "world_steps": 1, "known_invalid": i}
            for i in range(4)
        ]
        self.assertEqual(report.summarize(games, 0)["known_invalid"], 6)

class TestClassify(unittest.TestCase):
    def test_fixtures(self):
        self.assertIsNone(worlds.validity_problem(_world(VALID, [Role.BARON])), "Expected the valid fixture to pass every check.")
        self.assertIsNotNone(worlds.validity_problem(_world(TWO_IMPS, [Role.BARON])))

    def test_removed(self):
        valid = _world(VALID, [Role.BARON])
        general = Grimoire(5)
        self.assertEqual(worlds.classify_removed(valid, [general]), ("merged", None))
        category, reason = worlds.classify_removed(_world(TWO_IMPS, [Role.BARON]), [])
        self.assertEqual(category, "invalid")
        self.assertIsNotNone(reason)
        self.assertEqual(worlds.classify_removed(valid, []), ("unexplained", None))

    def test_added(self):
        valid = _world(VALID, [Role.BARON])
        self.assertEqual(worlds.classify_added(Grimoire(5), [valid]), ("generalized", None))
        self.assertEqual(worlds.classify_added(_world(TWO_IMPS, [Role.BARON]), [])[0], "known_invalid")
        self.assertEqual(worlds.classify_added(valid, []), ("other", None))

    def _unsettled_world(self) -> Grimoire:
        # night 1 knows player 0 is the Imp, but that hasn't been passed to night 2 yet
        grim = _world(VALID, [Role.BARON])
        night2 = grim.add_page(2, NightOrderPosition.AFTER_IMP)
        night2.characters = [Role.ANY_OTHER] + VALID[1:]
        night2.minion_types = [Role.BARON]
        return grim

    def test_removed_refined(self):
        world = self._unsettled_world()
        settled = world.clone()
        self.assertIsNone(find_finalize_problem(settled))
        self.assertEqual(settled.pages[1].characters[0], Role.IMP)
        self.assertFalse(settled.subsumes(world), "Expected the fixture not to count as merged.")
        self.assertEqual(worlds.classify_removed(world, [settled]), ("refined", None))
        self.assertEqual(worlds.classify_added(settled, [world]), ("refined", None))

    def test_refining_into_a_world_that_was_not_kept_is_unexplained(self):
        other = _world([Role.IMP, Role.BARON, Role.SAINT, Role.CHEF, Role.RECLUSE], [Role.BARON])
        self.assertEqual(worlds.classify_removed(self._unsettled_world(), [other]), ("unexplained", None))

    def test_removed_rejected(self):
        # one minion slot, but the pages disagree on its type
        world = _world(VALID, [Role.BARON])
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night2.characters = [Role.IMP, Role.ANY_OTHER_MINION, Role.ANY_OTHER, Role.ANY_OTHER, Role.CHEF]
        night2.minion_types = [Role.POISONER]
        self.assertIsNone(worlds.validity_problem(world), "Expected only a pass between pages to catch this.")
        self.assertEqual(
            worlds.classify_removed(world, []),
            ("rejected", "mismatched minion types between pages"),
        )

    def test_finalize_bug_is_not_explained_away(self):
        with mock.patch.object(GrimoirePage, "make_deductions", return_value=True):
            with self.assertRaises(FinalizeDidNotSettleError):
                _ = worlds.classify_removed(_world(VALID, [Role.BARON]), [])

    def test_only_unexplained_fails_the_comparison(self):
        for category in ("merged", "refined", "rejected", "invalid"):
            diff = worlds.WorldDiff("5p-0000", Grimoire(5), category, "reason", None)
            self.assertFalse(worlds.has_unexplained({"players": {"5": {"removed": [diff], "added": []}}}), category)

    def test_format_lists_rejected_but_not_refined(self):
        def diff(category: str, reason: str | None = None):
            return worlds.WorldDiff("5p-0000", _world(VALID, [Role.BARON]), category, reason, None)
        comparison = {
            "a": {"label": "A", "commit": "a", "timestamp": "t"},
            "b": {"label": "B", "commit": "b", "timestamp": "t"},
            "warnings": [],
            "game": None,
            "players": {"5": {"games": 1, "changed_games": 1, "added": [], "removed": [
                diff("refined"), diff("rejected", "mismatched minion types between pages"),
            ]}},
        }
        output = worlds.format_world_comparison(comparison)
        self.assertIn("refined 1", output)
        self.assertIn("rejected 1", output)
        self.assertIn("  rejected:", output)
        self.assertIn("[mismatched minion types between pages]", output)
        self.assertNotIn("  refined:", output)
        comparison["game"] = "5p-0000"
        self.assertIn("  refined:", worlds.format_world_comparison(comparison))

class TestDropStep(unittest.TestCase):
    def test_kept_world(self):
        scenario = load_scenarios(5, limit=1)[0]
        manager = GrimoireManager({"players": 5}, scenario.true_grim)
        manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)
        step = worlds.find_drop_step(5, scenario.info, scenario.deaths, scenario.nights, manager.grims[0])
        self.assertEqual(step, worlds.NOT_DROPPED)

    def test_dropped_world(self):
        first, second = load_scenarios(5, limit=2)
        # the first game's true grim doesn't fit the second game's info
        step = worlds.find_drop_step(5, second.info, second.deaths, second.nights, first.true_grim)
        self.assertNotEqual(step, worlds.NOT_DROPPED)
        self.assertFalse(step.startswith("error"), step)
        self.assertNotIn("{", step, "Expected a shortened stage label.")

class TestCompareWorlds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        results_dir = Path(cls.tmp.name) / "results"
        with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            _ = runner.run("smoke", "A", players=[5], results_dir=results_dir, csv_path=Path(cls.tmp.name) / "results.csv")
        cls.run_a = next(results_dir.glob("*_a.json"))

        # B is a copy of A with one valid, uncovered world removed from 5p-0000
        cls.run_b = results_dir / "copy_b.json"
        _ = shutil.copyfile(cls.run_a, cls.run_b)
        saved = worlds.load_worlds(worlds.worlds_file(cls.run_a, 5))
        cls.removed = saved["5p-0000"].pop(_uncovered_index(saved["5p-0000"]))
        for game_id, grims in saved.items():
            worlds.append_worlds(worlds.worlds_file(cls.run_b, 5), game_id, grims)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_identical_runs(self):
        comparison = worlds.compare_worlds(self.run_a, self.run_a)
        self.assertEqual(comparison["players"]["5"]["changed_games"], 0)
        self.assertFalse(worlds.has_unexplained(comparison))

    def test_unexplained_removal(self):
        comparison = worlds.compare_worlds(self.run_a, self.run_b)
        removed = comparison["players"]["5"]["removed"]
        self.assertEqual([(d.game_id, d.category) for d in removed], [("5p-0000", "unexplained")])
        self.assertEqual(removed[0].world, self.removed)
        # the current code still produces this world; it was only deleted from B's file
        self.assertEqual(removed[0].drop_step, worlds.NOT_DROPPED)
        self.assertTrue(worlds.has_unexplained(comparison))
        self.assertIn("UNEXPLAINED", worlds.format_world_comparison(comparison))

    def test_single_game(self):
        comparison = worlds.compare_worlds(self.run_a, self.run_b, game_id="5p-0000")
        self.assertEqual(comparison["players"]["5"]["games"], 1)
        with self.assertRaises(ValueError):
            _ = worlds.compare_worlds(self.run_a, self.run_b, game_id="5p-9999")

    def test_warns_when_checkout_differs(self):
        run_b = Path(self.tmp.name) / "results" / "other_commit.json"
        data = json.loads(self.run_a.read_text())
        data["meta"]["commit"] = "deadbee"
        _ = run_b.write_text(json.dumps(data))
        _ = shutil.copytree(worlds.worlds_dir(self.run_a), worlds.worlds_dir(run_b), dirs_exist_ok=True)
        comparison = worlds.compare_worlds(self.run_a, run_b)
        self.assertTrue(any("deadbee" in w for w in comparison["warnings"]))

    def test_missing_worlds(self):
        run_b = Path(self.tmp.name) / "results" / "no_worlds.json"
        _ = shutil.copyfile(self.run_a, run_b)
        comparison = worlds.compare_worlds(self.run_a, run_b)
        self.assertNotIn("5", comparison["players"])
        self.assertTrue(any("No saved 5 player worlds for B" in w for w in comparison["warnings"]))

    def test_baseline_copies_worlds(self):
        baseline = Path(self.tmp.name) / "baseline.json"
        compare.set_baseline(self.run_a, baseline)
        self.assertTrue(worlds.worlds_file(baseline, 5).exists())
        # a baseline without worlds mustn't keep the previous baseline's
        no_worlds = Path(self.tmp.name) / "results" / "no_worlds_baseline.json"
        _ = shutil.copyfile(self.run_a, no_worlds)
        compare.set_baseline(no_worlds, baseline)
        self.assertFalse(worlds.worlds_dir(baseline).exists())


if __name__ == "__main__":
    _ = unittest.main()
