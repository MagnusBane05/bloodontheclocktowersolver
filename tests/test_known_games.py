"""Benchmark games that found bugs in full runs, kept as fast regression tests.

The standard benchmark tier only covers the first few 10 and 15 player games, so games that
broke in a full run are added here to make sure they keep working.
"""
import unittest

from bench.scenarios import load_scenarios
from grimoire import GrimoireManager

# game id -> what went wrong
KNOWN_GAMES = {
    "10p-0048": "true grim lost at night 2 demon kill: a known Spy who caught the starpass was narrowed back to Spy",
}

class TestKnownGames(unittest.TestCase):
    def test_known_games_keep_true_grim(self):
        for game_id, problem in KNOWN_GAMES.items():
            with self.subTest(game_id=game_id):
                players, index = game_id.split("p-")
                scenario = load_scenarios(int(players), limit=int(index) + 1)[int(index)]
                manager = GrimoireManager({"players": int(players)}, scenario.true_grim)
                manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)
                self.assertTrue(manager.do_grims_contain_true_grim(), f"{game_id} lost its true grim again ({problem}).")


if __name__ == "__main__":
    _ = unittest.main()
