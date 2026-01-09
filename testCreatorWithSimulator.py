import unittest
from simulator import simulate_info
from worldCreator import *
from world.world import combine_worlds
from typing import get_type_hints

class TestCreatorWithSimulator(unittest.TestCase):
    def test_sanity_check(self):
        # make sure that the correct world from simulator is in the created worlds
        game: Game = {
            'players': 5
        }
        n = 10
        seed = 12
        x = simulate_info(n, game['players'], seed)
        for (info_list, death_info), true_world in x:
            worlds_list = []
            for info in info_list:
                if isinstance(info, WasherwomanInfo):
                    worlds_list.extend(create_worlds_from_washerwoman_info(game, info))
                elif isinstance(info, LibrarianInfo):
                    worlds_list.extend(create_worlds_from_librarian_info(game, info))
                elif isinstance(info, InvestigatorInfo):
                    worlds_list.extend(create_worlds_from_investigator_info(game, info))
                elif isinstance(info, ChefInfo):
                    worlds_list.extend(create_worlds_from_chef_info(game, info))
                elif isinstance(info, FortuneTellerInfo):
                    worlds_list.extend(create_worlds_from_fortune_teller_info(game, info))
                elif isinstance(info, EmpathInfo):
                    worlds_list.extend(create_worlds_from_empath_info(game, info))
                elif isinstance(info, UndertakerInfo):
                    worlds_list.extend(create_worlds_from_undertaker_info(game, info))
                elif isinstance(info, RavenkeeperInfo):
                    worlds_list.extend(create_worlds_from_ravenkeeper_info(game, info))
                elif isinstance(info, VirginInfo):
                    worlds_list.extend(create_worlds_from_virgin_nominated(game, info))
                elif isinstance(info, SlayerInfo):
                    worlds_list.extend(create_worlds_from_slayer_info(game, info))
                elif isinstance(info, Claim):
                    worlds_list.extend(create_worlds_from_claim(game, info))
            combined_worlds = combine_worlds(worlds_list)
            if death_info['slayer_shot'] is not None:
                target = death_info['slayer_shot'][0]
                night = death_info['slayer_shot'][1]
                combined_worlds = create_worlds_from_slayer_kill(combined_worlds, target, night)
            if death_info['executed'] is not None:
                executed = death_info['executed'][0]
                night = death_info['executed'][1]
                combined_worlds = create_worlds_from_execution(combined_worlds, executed, night)
            if death_info['killed_by_demon'] is not None:
                target = death_info['killed_by_demon'][0]
                night = death_info['killed_by_demon'][1]
                combined_worlds = create_worlds_from_night_kill(combined_worlds, target, night)
            self.assertIn(true_world, combined_worlds)

if __name__ == '__main__':
    _ = unittest.main()