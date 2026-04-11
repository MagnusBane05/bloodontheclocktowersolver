import unittest
from simulator import simulate_info
from grimoire.info_to_grim import *
from grimoire import GrimoireManager
from tqdm import tqdm
from grimoire.info import *

class TestCreatorWithSimulator(unittest.TestCase):
    def test_5_player(self):
        # make sure that the correct world from simulator is in the created worlds
        game: Game = {
            'players': 5
        }
        n = 1000
        seed = 42
        x = simulate_info(n, game, seed)
        for i, ((info_list, death_info), true_world) in tqdm(enumerate(x)):
            grim_manager = GrimoireManager(game, true_world)

            grim_manager.add_full_game(info_list, death_info, 2)

            true_world_found = grim_manager.do_grims_contain_true_grim()

            self.assertTrue(true_world_found, f"True world {i} not in created worlds.")

    def test_10_player(self):
        # make sure that the correct world from simulator is in the created worlds
        game: Game = {
            'players': 10
        }
        n = 100
        seed = 193
        x = simulate_info(n, game, seed)
        for i, ((info_list, death_info), true_world) in tqdm(enumerate(x)):
            grim_manager = GrimoireManager(game, true_world)

            nights = len(true_world.get_unique_nights())
            grim_manager.add_full_game(info_list, death_info, nights)

            true_world_found = grim_manager.do_grims_contain_true_grim()

            self.assertTrue(true_world_found, f"True world {i} not in created worlds.")


def profile_10_player():
        # make sure that the correct world from simulator is in the created worlds
        game: Game = {
            'players': 10
        }
        n = 10
        seed = 193
        x = simulate_info(n, game, seed)
        for _, ((info_list, death_info), true_world) in tqdm(enumerate(x)):
            grim_manager = GrimoireManager(game, true_world)

            nights = len(true_world.get_unique_nights())
            grim_manager.add_full_game(info_list, death_info, nights)

            grim_manager.do_grims_contain_true_grim()

if __name__ == '__main__':
    profile_10_player()
    # unittest.main()
    # cProfile.run("profile_10_player()", "restats")
    # p = pstats.Stats("restats")
    # p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()
