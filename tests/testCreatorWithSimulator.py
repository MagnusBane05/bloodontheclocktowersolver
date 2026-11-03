import unittest
from bench.scenarios import load_scenarios
from grimoire.info_to_grim import *
from grimoire import GrimoireManager
from grimoire.info import *

class TestCreatorWithSimulator(unittest.TestCase):
    def test_5_player(self):
        # make sure that the correct world from simulator is in the created worlds
        players = 5
        runs = 1000
        game: Game = {
            'players': players
        }
        scenarios = load_scenarios(players, limit=runs)
        for scenario in scenarios:
            with self.subTest(id=scenario.id):
                grim_manager = GrimoireManager(game, scenario.true_grim)

                nights = len(scenario.true_grim.get_unique_nights())
                grim_manager.add_full_game(scenario.info, scenario.deaths, nights)
                true_world_found = grim_manager.do_grims_contain_true_grim()

                self.assertTrue(true_world_found, f"True world {scenario.id} not in created worlds.")
        
if __name__ == '__main__':
    _ = unittest.main()

