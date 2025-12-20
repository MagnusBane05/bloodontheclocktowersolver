import unittest
from solver import Role, World, combine_worlds
from worldCreator import create_worlds_from_fortune_teller_info, Game, FortuneTellerInfo

class TestSolver(unittest.TestCase):
    def test_chef_worlds(self):

        chef_world = World()
        chef_world.phases[0].chef_number = 0

        ## Valid worlds
        # Chef 0 with Imp and SW not adjacent
        w1 = World()
        w1.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SCARLET_WOMAN
        ]
        w1, valid = World.combine(w1, chef_world)
        self.assertTrue(valid)

        # Chef 0 with evil and Recluse pair
        w2 = World()
        w2.phases[0].characters = [
            Role.CHEF, Role.RECLUSE, Role.IMP, Role.DRUNK, Role.BARON
        ]
        w2, valid = World.combine(w2, chef_world)
        self.assertTrue(valid)
        
        # Chef 0 wih Imp Spy pair
        w3 = World()
        w3.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SPY, Role.LIBRARIAN
        ]
        w3, valid = World.combine(w3, chef_world)
        self.assertTrue(valid)

        chef_world.phases[0].chef_number = 1
        # Chef 1 with 2 evils together
        w4 = World()
        w4.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SCARLET_WOMAN, Role.LIBRARIAN
        ]
        w4, valid = World.combine(w4, chef_world)
        self.assertTrue(valid)

        # Chef 1 with evil and Recluse pair
        w5 = World()
        w5.phases[0].characters = [
            Role.CHEF, Role.RECLUSE, Role.IMP, Role.DRUNK, Role.BARON
        ]
        w5, valid = World.combine(w5, chef_world)
        self.assertTrue(valid)

        # Chef 1 with evil and Spy
        w6 = World()
        w6.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SPY, Role.LIBRARIAN
        ]
        w6, valid = World.combine(w6, chef_world)
        self.assertTrue(valid)
        
        # Chef 1 with evil, Recluse, evil
        chef_world = World(num_players=6)
        chef_world.phases[0].chef_number = 1
        w7 = World(num_players=6)
        w7.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.RECLUSE, Role.SCARLET_WOMAN, Role.LIBRARIAN
        ]
        w7, valid = World.combine(w7, chef_world)
        self.assertTrue(valid)

        chef_world.phases[0].chef_number = 2
        # Chef 2 with evil, Recluse, Spy
        w8 = World(num_players=6)
        w8.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.RECLUSE, Role.SPY, Role.LIBRARIAN
        ]
        w8, valid = World.combine(w8, chef_world)
        self.assertTrue(valid)

        # Chef two with two seperate groups of evils
        chef_world = World(num_players=13)
        w9 = World(num_players=13)
        chef_world.phases[0].chef_number = 2
        w9.phases[0].characters = [
            Role.CHEF, Role.IMP, Role.POISONER, Role.WASHERWOMAN, Role.LIBRARIAN,
            Role.SCARLET_WOMAN, Role.BARON, Role.SOLDIER, Role.SLAYER, Role.MAYOR,
            Role.BUTLER, Role.SAINT, Role.UNDERTAKER
        ]
        w9, valid = World.combine(w9, chef_world)
        self.assertTrue(valid)

        ## Invalid worlds
        chef_world = World(num_players=5)
        chef_world.phases[0].chef_number = 0
        # Chef 0 with 2 non-Spy evils together (should be Chef 1)
        w_invalid1 = World()
        w_invalid1.phases[0].characters = [
            Role.CHEF, Role.IMP, Role.SCARLET_WOMAN, Role.WASHERWOMAN, Role.LIBRARIAN
        ]
        w_invalid1, valid = World.combine(w_invalid1, chef_world)
        self.assertFalse(valid)

        chef_world.phases[0].chef_number = 1
        # Chef 1 with no adjacent evils and no Recluse (should be Chef 0)
        w_invalid2 = World()
        w_invalid2.phases[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SCARLET_WOMAN
        ]
        w_invalid2, valid = World.combine(w_invalid2, chef_world)
        self.assertFalse(valid)

        chef_world.phases[0].chef_number = 3
        # Chef 3 with evil, Recluse, evil, Baron and another outsider (impossible in 5 players)
        w_invalid3 = World()
        w_invalid3.phases[0].characters = [
            Role.CHEF, Role.IMP, Role.RECLUSE, Role.BARON, Role.DRUNK
        ]
        w_invalid3.phases[0].add_minion_type(Role.BARON)
        w_invalid3, valid = World.combine(w_invalid3, chef_world)
        self.assertFalse(valid)

    def test_combine_characters(self):
        ## Valid cases

        # Specific role with any other
        world1a = World()
        world1b = World()
        world1b.phases[0].characters[0] = Role.LIBRARIAN
        world1, valid1 = World.combine(world1a, world1b)
        self.assertEqual(world1.phases[0].characters[0], Role.LIBRARIAN)
        self.assertTrue(valid1)

        # Specific non-demon role with non-demon
        world2a = World()
        world2a.phases[0].characters[0] = Role.SPY
        world2b = World()
        world2b.phases[0].characters[0] = Role.NON_DEMON
        world2, valid2 = World.combine(world2a, world2b)
        self.assertEqual(world2.phases[0].characters[0], Role.SPY)
        self.assertTrue(valid2)

        # Specific good role with any other good
        world3a = World()
        world3a.phases[0].characters[0] = Role.MAYOR
        world3b = World()
        world3b.phases[0].characters[0] = Role.ANY_OTHER_GOOD
        world3, valid3 = World.combine(world3a, world3b)
        self.assertEqual(world3.phases[0].characters[0], Role.MAYOR)
        self.assertTrue(valid3)

        # Specific evil role with any other evil
        world4a = World()
        world4a.phases[0].characters[0] = Role.POISONER
        world4b = World()
        world4b.phases[0].characters[0] = Role.ANY_OTHER_EVIL
        world4, valid4 = World.combine(world4a, world4b)
        self.assertEqual(world4.phases[0].characters[0], Role.POISONER)
        self.assertTrue(valid4)

        # Specific outsider with any other outsider
        world5a = World()
        world5a.phases[0].characters[0] = Role.DRUNK
        world5b = World()
        world5b.phases[0].characters[0] = Role.ANY_OTHER_OUTSIDER
        world5, valid5 = World.combine(world5a, world5b)
        self.assertEqual(world5.phases[0].characters[0], Role.DRUNK)
        self.assertTrue(valid5)

        # Specific townsfolk with any other townsfolk
        world6a = World()
        world6a.phases[0].characters[0] = Role.MONK
        world6b = World()
        world6b.phases[0].characters[0] = Role.ANY_OTHER_TOWNSFOLK
        world6, valid6 = World.combine(world6a, world6b)
        self.assertEqual(world6.phases[0].characters[0], Role.MONK)
        self.assertTrue(valid6)

        # Specific minion with any other minion
        world7a = World()
        world7a.phases[0].characters[0] = Role.SPY
        world7b = World()
        world7b.phases[0].characters[0] = Role.ANY_OTHER_MINION
        world7, valid7 = World.combine(world7a, world7b)
        self.assertEqual(world7.phases[0].characters[0], Role.SPY)
        self.assertTrue(valid7)

        # Any other evil with any other
        world8a = World()
        world8a.phases[0].characters[0] = Role.ANY_OTHER_EVIL
        world8b = World()
        world8, valid8 = World.combine(world8a, world8b)
        self.assertEqual(world8.phases[0].characters[0], Role.ANY_OTHER_EVIL)
        self.assertTrue(valid8)

        # Any other evil with non-demon becomes any other minion
        world9a = World()
        world9a.phases[0].characters[0] = Role.ANY_OTHER_EVIL
        world9b = World()
        world9b.phases[0].characters[0] = Role.NON_DEMON
        world9, valid9 = World.combine(world9a, world9b)
        self.assertEqual(world9.phases[0].characters[0], Role.ANY_OTHER_MINION)
        self.assertTrue(valid9)

        # Any other townsfolk with any other good
        world10a = World()
        world10a.phases[0].characters[0] = Role.ANY_OTHER_TOWNSFOLK
        world10b = World()
        world10b.phases[0].characters[0] = Role.ANY_OTHER_GOOD
        world10, valid10 = World.combine(world10a, world10b)
        self.assertEqual(world10.phases[0].characters[0], Role.ANY_OTHER_TOWNSFOLK)
        self.assertTrue(valid10)

        ## Invalid cases

        # Two different specific roles
        world11a = World()
        world11a.phases[0].characters[0] = Role.MONK
        world11b = World()
        world11b.phases[0].characters[0] = Role.MAYOR
        _, valid11 = World.combine(world11a, world11b)
        self.assertFalse(valid11)

        # Specific evil role with any other good
        world12a = World()
        world12a.phases[0].characters[0] = Role.POISONER
        world12b = World()
        world12b.phases[0].characters[0] = Role.ANY_OTHER_GOOD
        _, valid12 = World.combine(world12a, world12b)
        self.assertFalse(valid12)

        # Specific good role with any other evil
        world13a = World()
        world13a.phases[0].characters[0] = Role.MAYOR
        world13b = World()
        world13b.phases[0].characters[0] = Role.ANY_OTHER_EVIL
        _, valid13 = World.combine(world13a, world13b)
        self.assertFalse(valid13)

        # Imp with non-demon
        world14a = World()
        world14a.phases[0].characters[0] = Role.IMP
        world14b = World()
        world14b.phases[0].characters[0] = Role.NON_DEMON
        _, valid14 = World.combine(world14a, world14b)
        self.assertFalse(valid14)

        # Specific outsider with any other townsfolk
        world15a = World()
        world15a.phases[0].characters[0] = Role.DRUNK
        world15b = World()
        world15b.phases[0].characters[0] = Role.ANY_OTHER_TOWNSFOLK
        _, valid15 = World.combine(world15a, world15b)
        self.assertFalse(valid15)

        # Specific townsfolk with any other outsider
        world16a = World()
        world16a.phases[0].characters[0] = Role.MONK
        world16b = World()
        world16b.phases[0].characters[0] = Role.ANY_OTHER_OUTSIDER
        _, valid16 = World.combine(world16a, world16b)
        self.assertFalse(valid16)

        # Specific townsfolk with any other minion
        world17a = World()
        world17a.phases[0].characters[0] = Role.MONK
        world17b = World()
        world17b.phases[0].characters[0] = Role.ANY_OTHER_MINION
        _, valid17 = World.combine(world17a, world17b)
        self.assertFalse(valid17)

    def testStarpass(self):
        game: Game = {
            "players": 5
        }

        n1_fortune_teller_info: FortuneTellerInfo = {
            "player": 0,
            "night": 1,
            "pings": ((1,2),False)
        }

        n2_fortune_teller_info: FortuneTellerInfo = {
            "player": 0,
            "night": 2,
            "pings": ((1,2),True)
        }

        n1_fortune_teller_worlds = create_worlds_from_fortune_teller_info(game, n1_fortune_teller_info)
        n2_fortune_teller_worlds = create_worlds_from_fortune_teller_info(game, n2_fortune_teller_info)
        combined_worlds, invalid_worlds = combine_worlds([n1_fortune_teller_worlds, n2_fortune_teller_worlds])

        filtered_worlds = [x for x in combined_worlds if x.phases[0].characters[0] == Role.FORTUNE_TELLER and not any([y for ys in x.phases[0].poisoned for y in ys]) and not any([z == Role.RECLUSE for z in x.phases[0].characters])]

        self.assertEqual(1,2)


if __name__ == '__main__':
    _ = unittest.main()