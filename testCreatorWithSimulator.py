import time
import unittest
from simulator import simulate_info
from grimoire.info_to_grim import *
from grimoire import GrimoireManager
from tqdm import tqdm
from grimoire.info import *

class TestCreatorWithSimulator(unittest.TestCase):
    def test_5_player(self):
        self._test_x_player(self, 5, 1000)

    # def test_10_player(self):
    #     self._test_x_player(self, 10, 1000)

    def test_15_player(self):
        self._test_x_player(self, 15, 10)

    @staticmethod
    def _test_x_player(clazz: TestCreatorWithSimulator, x: int, n: int):
        # make sure that the correct world from simulator is in the created worlds
        game: Game = {
            'players': x
        }
        seed = 193
        result = simulate_info(n, game, seed)
        times: list[float] = []
        grims: list[int] = []
        for i, ((info_list, death_info), true_world) in tqdm(enumerate(result)):
        # (info_list, death_info), true_world = result[385]
            grim_manager = GrimoireManager(game, true_world)

            nights = len(true_world.get_unique_nights())
            start = time.time()
            grim_manager.add_full_game(info_list, death_info, nights)
            end = time.time()
            times.append(end - start)
            grims.append(len(grim_manager.grims))
            true_world_found = grim_manager.do_grims_contain_true_grim()

            clazz.assertTrue(true_world_found, f"True world {i} not in created worlds.")
        print(f"{x} Players")
        print(f"Least grims: {min(grims)}")
        print(f"Most grims: {max(grims)}")
        print(f"Average grims: {round(sum(grims) / n)}")
        print(f"Fastest: {min(times)}")
        print(f"Slowest: {max(times)}")
        print(f"Average: {sum(times) / n}")
        print(f"Total: {sum(times)}")
        print()
        

if __name__ == '__main__':
    unittest.main()
