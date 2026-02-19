import unittest
from warnings import warn
from simulator import simulate_info
from worldCreator import *
from tqdm import tqdm

class TestCreatorWithSimulator(unittest.TestCase):
    def test_sanity_check(self):
        # make sure that the correct world from simulator is in the created worlds
        game: Game = {
            'players': 5
        }
        n = 1000
        seed = 42
        x = simulate_info(n, game['players'], seed)
        for i, ((info_list, death_info), true_world) in tqdm(enumerate(x)):
            
            combined_worlds, conflicting_worlds = create_worlds_from_info(game, info_list, death_info, true_world)

            true_world_found = False
            # print("-----------------------")
            # if death_info['slayer_shot'] is not None:
            #     print(f"Slayer shot player {death_info['slayer_shot'][0]}")
            # if death_info['executed'] is not None:
            #     print(f"Executed player {death_info['executed'][0]}")
            # if death_info['killed_by_demon'] is not None:
            #     print(f"Demon killed player {death_info['killed_by_demon'][0]}")
            for _, world in enumerate(combined_worlds):
            #     print(f"Comparing True World with World {j}")
                if true_world == world:
                    true_world_found = True
                #     print("Equal")
                # else:
                #     print("Not equal")
                # print("")
            if not true_world_found:
                for _, (a,b) in enumerate(conflicting_worlds):
                    if true_world == a or true_world == b:
                        warn("True world found in conflicting worlds.")
            self.assertTrue(true_world_found, f"True world {i} not in created worlds.")

if __name__ == '__main__':
    _ = unittest.main()