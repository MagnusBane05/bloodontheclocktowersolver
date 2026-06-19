
import unittest

from grimoire import Grimoire
from grimoire import GrimoireManager
from grimoire.role import Role


class TestGrimoire(unittest.TestCase):
    def test_get_player_perspective(self):
        manager = GrimoireManager({"players": 5})
        true_grim = Grimoire()
        true_grim.pages[0].characters = [Role.IMP, Role.SCARLET_WOMAN, Role.FORTUNE_TELLER, Role.SOLDIER, Role.CHEF]
        manager.true_grim = true_grim

        test_grim = Grimoire()

        # test that an unknown grim will get filled in with the player's role        
        test_grim.pages[0].characters = [Role.ANY_OTHER]*5
        manager.grims = [test_grim]

        subjective_manager = manager.get_player_perspective(2)
        # self.assertEqual(subjective_manager.grims[0].pages[0].characters[2], Role.FORTUNE_TELLER)

        # drunk player has seen role and drunk as valid grims
        true_grim.pages[0].characters = [Role.IMP, Role.BARON, Role.DRUNK, Role.RECLUSE, Role.CHEF]
        true_grim.pages[0].drunk_token = Role.FORTUNE_TELLER
        test_grim.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER, Role.DRUNK, Role.ANY_OTHER, Role.ANY_OTHER]
        test_grim2 = Grimoire()
        test_grim2.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER, Role.FORTUNE_TELLER, Role.ANY_OTHER, Role.ANY_OTHER]
        manager.grims = [test_grim, test_grim2]
        subjective_manager = manager.get_player_perspective(2)
        self.assertEqual(len(subjective_manager.grims), 2)
        self.assertEqual(subjective_manager.grims[0].pages[0].characters[2], Role.DRUNK)
        self.assertEqual(subjective_manager.grims[1].pages[0].characters[2], Role.FORTUNE_TELLER)




if __name__ == '__main__':
    _ = unittest.main()