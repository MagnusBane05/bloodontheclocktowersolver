import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from analyze.simulator import simulate_single_game
from bench import scenarios
from bench.scenarios import (  # pyright: ignore[reportPrivateUsage]
    SEED_START,
    decode_grim,
    _decode_hook,
    _encode,
    encode_grim,
    _pages_equal,
    load_scenarios,
)
from bench.tiers import TIERS
from grimoire import GrimoireManager, NightOrderPosition, Role


def _round_trip(value):  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
    return json.loads(json.dumps(_encode(value)), object_hook=_decode_hook)  # pyright: ignore[reportAny]

class TestEncoding(unittest.TestCase):
    def test_enums_stored_by_name(self):
        encoded = json.dumps(_encode({"role": Role.IMP, "order": NightOrderPosition.AFTER_SLAYER}))
        self.assertIn("Role.IMP", encoded, "Expected roles to be stored by name, not as ints.")
        self.assertIn("NightOrderPosition.AFTER_SLAYER", encoded, "Expected night order positions to be stored by name.")

    def test_round_trip_values(self):
        value = {
            "role": Role.IMP,
            "pings": ((1, 2), True),
            "list": [Role.SPY, None, 3],
            "nested": {"token": None, "flag": False},
        }
        self.assertEqual(_round_trip(value), value, "Expected enums, tuples and nested values to survive a round trip.")

    def test_round_trip_simulated_games(self):
        for players in (5, 10, 15):
            for seed in (SEED_START, SEED_START + 1):
                with self.subTest(players=players, seed=seed):
                    (info, deaths), true_grim = simulate_single_game(players, None, seed)
                    self.assertEqual(_round_trip(info), info, "Expected info to survive a round trip.")
                    self.assertEqual(_round_trip(deaths), deaths, "Expected deaths to survive a round trip.")
                    grim_data = json.loads(json.dumps(encode_grim(true_grim)), object_hook=_decode_hook)  # pyright: ignore[reportAny]
                    decoded = decode_grim(grim_data)  # pyright: ignore[reportAny]
                    self.assertTrue(_pages_equal(decoded, true_grim), "Expected every page field to survive a round trip.")

    def test_unknown_page_field_rejected(self):
        (_, _), true_grim = simulate_single_game(5, None, SEED_START)
        grim_data = json.loads(json.dumps(encode_grim(true_grim)), object_hook=_decode_hook)  # pyright: ignore[reportAny]
        grim_data["pages"][0]["removed_field"] = True
        with self.assertRaises(ValueError):
            _ = decode_grim(grim_data)  # pyright: ignore[reportAny]

class TestScenarioFiles(unittest.TestCase):
    def test_files_match_simulator(self):
        for players in (5, 10, 15):
            for scenario in load_scenarios(players, limit=2):
                with self.subTest(id=scenario.id):
                    (info, deaths), true_grim = simulate_single_game(players, None, scenario.seed)
                    self.assertEqual(
                        scenario.info, info,
                        "Saved v1 scenarios no longer match the simulator. If the simulator changed on purpose, generate a new scenario version.",
                    )
                    self.assertEqual(scenario.deaths, deaths, "Saved deaths no longer match the simulator.")
                    self.assertTrue(_pages_equal(scenario.true_grim, true_grim), "Saved true grim no longer matches the simulator.")

    def test_ids_and_seeds(self):
        loaded = load_scenarios(15, limit=7)
        self.assertEqual(loaded[6].id, "15p-0006")
        self.assertEqual(loaded[6].seed, SEED_START + 6)

    def test_tiers_fit_files(self):
        for tier, sizes in TIERS.items():
            for players, count in sizes.items():
                with self.subTest(tier=tier, players=players):
                    self.assertEqual(len(load_scenarios(players, limit=count)), count)

    def test_limit_larger_than_file_raises(self):
        with self.assertRaises(ValueError):
            _ = load_scenarios(15, limit=10_000)

    def test_missing_version_raises(self):
        with self.assertRaises(FileNotFoundError):
            _ = load_scenarios(5, version="does-not-exist")

    def test_loaded_scenario_solves(self):
        scenario = load_scenarios(5, limit=1)[0]
        manager = GrimoireManager({"players": 5}, scenario.true_grim)
        manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)
        self.assertTrue(manager.do_grims_contain_true_grim(), "Expected a loaded scenario to keep its true grim.")

    def test_generate_refuses_to_overwrite(self):
        with self.assertRaises(FileExistsError):
            _ = scenarios.generate(5, "v1")

    def test_generate_uses_git_state_from_before_writing(self):
        # writing the first file used to make the tree look dirty for the next one
        states = iter([("abc1234", False), ("abc1234", True)])
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(scenarios, "SCENARIOS_DIR", Path(tmp)), \
                mock.patch.object(scenarios, "_scenario_count", return_value=1), \
                mock.patch.object(scenarios, "_git_state", side_effect=lambda: next(states)), \
                mock.patch("sys.argv", ["bench.scenarios", "generate", "--version", "test", "--players", "5", "10"]), \
                mock.patch("sys.stdout"):
            scenarios.main()
            for players in (5, 10):
                with open(Path(tmp) / "test" / f"{players}p.json") as f:
                    header = json.load(f)
                self.assertEqual(header["commit"], "abc1234")
                self.assertFalse(header["dirty"], f"Expected the {players} player file to record the tree as it was before generating.")


if __name__ == "__main__":
    _ = unittest.main()
