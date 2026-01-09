import unittest
from world.world import World
from world.role import Role
from world.phase import Phase

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

    def test_add_phase(self):
        world = World()
        world.add_phase(2)

        self.assertEqual(len(world.phases), 2)
        self.assertEqual(world.phases[0].night, 1)
        self.assertEqual(world.phases[1].night, 2)

        world.add_phase(5)
        world.add_phase(3)

        self.assertEqual(len(world.phases), 4)
        self.assertEqual(world.phases[2].night, 3)
        self.assertEqual(world.phases[3].night, 5)

        world.add_phase(0)
        self.assertEqual(world.phases[0].night, 0)

    def test_execution(self):

        # executed player is dead in both worlds
        world = World()
        no_sw_world, sw_world = world.execute_player(1,2)
        self.assertEqual(len(no_sw_world.phases), 2)
        self.assertTrue(no_sw_world.phases[1].dead[1])
        self.assertNotEqual(sw_world, None)
        self.assertEqual(len(sw_world.phases), 2)
        self.assertTrue(sw_world.phases[1].dead[1])

        # known imp executed -> None
        world = World()
        world.phases[0].characters[0] = Role.IMP
        no_sw_world, sw_world = world.execute_player(0,2)
        self.assertIsNone(no_sw_world)

        # minion type is scarlet woman in sw world
        world = World()
        _, sw_world = world.execute_player(0,2)
        self.assertIn(Role.SCARLET_WOMAN, sw_world.phases[1].minion_types)

        # known scarlet woman becomes imp
        world = World()
        world.phases[0].characters[0] = Role.SCARLET_WOMAN
        _, sw_world = world.execute_player(1,2)
        self.assertNotEqual(sw_world, None)
        self.assertEqual(len(sw_world.phases), 2)
        self.assertEqual(sw_world.phases[1].characters[0], Role.IMP)

        # single alive minion becomes imp
        world = World()
        world.phases[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_MINION, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        _, sw_world = world.execute_player(0,2)
        self.assertNotEqual(sw_world, None)
        self.assertEqual(len(sw_world.phases), 2)
        self.assertEqual(sw_world.phases[1].characters[1], Role.IMP)
        self.assertEqual(sw_world.phases[0].characters[1], Role.SCARLET_WOMAN)
        self.assertIn(Role.SCARLET_WOMAN, sw_world.phases[0].minion_types)
        self.assertIn(Role.SCARLET_WOMAN, sw_world.phases[1].minion_types)

        # non-demons become any role
        world = World()
        world.phases[0].characters[0] = Role.NON_DEMON
        _, sw_world = world.execute_player(1,2)
        self.assertNotEqual(sw_world, None)
        self.assertEqual(len(sw_world.phases), 2)
        self.assertEqual(sw_world.phases[1].characters[0], Role.ANY_OTHER)

        # minions become any evil
        world = World(13)
        world.phases[0].characters[0] = Role.ANY_OTHER_MINION
        world.phases[0].characters[2] = Role.ANY_OTHER_MINION
        _, sw_world = world.execute_player(1,2)
        self.assertNotEqual(sw_world, None)
        self.assertEqual(len(sw_world.phases), 2)
        self.assertEqual(sw_world.phases[1].characters[0], Role.ANY_OTHER_EVIL)

        # no room for scarlet woman in minion types
        world = World()
        world.phases[0].minion_types = [Role.BARON, Role.POISONER]
        _, sw_world = world.execute_player(1,2)
        self.assertIsNone(sw_world)

        # no room for scarlet woman in characters
        world = World()
        world.phases[0].characters = [Role.POISONER, Role.ANY_OTHER_EVIL, Role.WASHERWOMAN, Role.EMPATH, Role.MONK]
        _, sw_world = world.execute_player(2,2)
        self.assertIsNone(sw_world)

        # scarlet woman is dead already -> None
        world = World()
        world.phases[0].characters[0] = Role.SCARLET_WOMAN
        world.phases[0].dead[0] = True
        _, sw_world = world.execute_player(1,2)
        self.assertIsNone(sw_world)

        # non-demon executed
        world = World()
        world.phases[0].characters = [Role.POISONER, Role.ANY_OTHER_EVIL, Role.WASHERWOMAN, Role.EMPATH, Role.MONK]
        _, sw_world = world.execute_player(1,2)
        self.assertIsNone(sw_world)

    def test_night_death(self):
        # player is dead in all worlds
        world = World()
        no_sp_world, sp_world = world.killed_by_demon(1,2)
        self.assertEqual(len(no_sp_world.phases), 2)
        self.assertTrue(no_sp_world.phases[1].dead[1])
        self.assertIsNotNone(sp_world)
        self.assertEqual(len(sp_world.phases), 2)
        self.assertTrue(sp_world.phases[1].dead[1])

        # known imp killed by demon -> None
        world = World()
        world.phases[0].characters[0] = Role.IMP
        no_sp_world, sp_world = world.killed_by_demon(0,2)
        self.assertIsNone(no_sp_world)

        # known scarlet woman becomes imp
        world = World()
        world.phases[0].characters[0] = Role.SCARLET_WOMAN
        _, sp_world = world.killed_by_demon(1,2)
        self.assertIsNotNone(sp_world)
        self.assertEqual(len(sp_world.phases), 2)
        self.assertEqual(sp_world.phases[1].characters[0], Role.IMP)

        # single alive minion becomes demon
        world = World()
        world.phases[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_MINION, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        _, sp_world = world.killed_by_demon(0,2)
        self.assertIsNotNone(sp_world)
        self.assertEqual(len(sp_world.phases), 2)
        self.assertEqual(sp_world.phases[1].characters[1], Role.IMP)

        # non-demons become any role
        world = World()
        world.phases[0].characters[0] = Role.NON_DEMON
        _, sp_world = world.killed_by_demon(1,2)
        self.assertIsNotNone(sp_world)
        self.assertEqual(len(sp_world.phases), 2)
        self.assertEqual(sp_world.phases[1].characters[0], Role.ANY_OTHER)

        # any other minions become any other evil
        world = World(13)
        world.phases[0].characters[0] = Role.ANY_OTHER_MINION
        world.phases[0].characters[2] = Role.ANY_OTHER_MINION
        _, sp_world = world.killed_by_demon(1,2)
        self.assertIsNotNone(sp_world)
        self.assertEqual(len(sp_world.phases), 2)
        self.assertEqual(sp_world.phases[1].characters[0], Role.ANY_OTHER_EVIL)

        # no room in minion types -> None
        world = World()
        world.phases[0].minion_types = [Role.IMP]
        _, sp_world = world.killed_by_demon(1,2)
        self.assertIsNone(sp_world)

        # no alive minions -> None
        world = World()
        world.phases[0].characters = [Role.ANY_OTHER, Role.POISONER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER]
        world.phases[0].dead[1] = True
        _, sp_world = world.killed_by_demon(0,2)
        self.assertIsNone(sp_world)

        # known non-demon killed by demon -> None
        world = World()
        world.phases[0].characters = [Role.NON_DEMON, Role.WASHERWOMAN, Role.LIBRARIAN, Role.EMPATH, Role.MONK]
        _, sp_world = world.killed_by_demon(0,2)
        self.assertIsNone(sp_world)

    def test_pass_through_phases(self):
        # sanity check, same characters should be okay
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.MONK
        night2.characters[0] = Role.MONK
        self.assertTrue(World._pass_through_phases(world))

        # different characters should be invalid
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.MONK
        night2.characters[0] = Role.SLAYER
        self.assertFalse(World._pass_through_phases(world))

        # specific role -> non specific should be okay
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.MONK
        night2.characters[0] = Role.ANY_OTHER_TOWNSFOLK
        self.assertTrue(World._pass_through_phases(world))

        # non-specific role -> specific should be okay
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.ANY_OTHER_EVIL
        night2.characters[0] = Role.SCARLET_WOMAN
        self.assertTrue(World._pass_through_phases(world))

        # if there was a character change, it's okay
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.SCARLET_WOMAN
        night2.characters[0] = Role.IMP
        night2.character_changed[0] = True
        self.assertTrue(World._pass_through_phases(world))

        # any other evil to non-demon becomes any other minion
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.ANY_OTHER_EVIL
        night2.characters[0] = Role.NON_DEMON
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.characters[0], Role.ANY_OTHER_MINION)

        # same in reverse
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters[0] = Role.NON_DEMON
        night2.characters[0] = Role.ANY_OTHER_EVIL
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.characters[0], Role.ANY_OTHER_MINION)

        # combined characters resulting in an invalid world should be invalid
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.characters = [Role.FORTUNE_TELLER, Role.NON_DEMON, Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER]
        night2.characters = [Role.FORTUNE_TELLER, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.NON_DEMON]
        self.assertFalse(World._pass_through_phases(world))

        # if there's a starpass, the scarlet woman should become the imp and other minions stay the same
        world = World(13)
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night2.star_passed = True
        night1.characters[0] = Role.SCARLET_WOMAN
        night1.characters[1] = Role.ANY_OTHER_MINION
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.characters[0], Role.IMP)
        self.assertEqual(night2.characters[1], Role.ANY_OTHER_MINION)

        # if there's a starpass but no scarlet woman, any known minions would have caught it and non-demons stay non demons
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night2.star_passed = True
        night1.characters[0] = Role.ANY_OTHER_MINION
        night1.characters[1] = Role.NON_DEMON
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.characters[0], Role.ANY_OTHER_EVIL)
        self.assertEqual(night2.characters[1], Role.NON_DEMON)

        # if not all minions are known, non-demons become any other role
        world = World(13)
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night2.star_passed = True
        night1.characters[0] = Role.ANY_OTHER_MINION
        night1.characters[1] = Role.NON_DEMON
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.characters[0], Role.ANY_OTHER_EVIL)
        self.assertEqual(night2.characters[1], Role.ANY_OTHER)

        # same minion types should be okay
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.minion_types = [Role.POISONER]
        night2.minion_types = [Role.POISONER]
        self.assertTrue(World._pass_through_phases(world))

        # different minion types should be invalid
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.minion_types = [Role.POISONER]
        night2.minion_types = [Role.SCARLET_WOMAN]
        self.assertFalse(World._pass_through_phases(world))

        # specific minion type -> any other minion should be okay
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.minion_types = [Role.ANY_OTHER_MINION]
        night2.minion_types = [Role.POISONER]
        self.assertTrue(World._pass_through_phases(world))

        # same in reverse
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.minion_types = [Role.POISONER]
        night2.minion_types = [Role.ANY_OTHER_MINION]
        self.assertTrue(World._pass_through_phases(world))

        # red herring should be passed through
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.red_herring[0] = True
        self.assertTrue(World._pass_through_phases(world))
        self.assertTrue(night2.red_herring[0])

        # two red herrings is invalid
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.red_herring[0] = True
        night2.red_herring[1] = True
        self.assertFalse(World._pass_through_phases(world))

        # poisoned should not be passed through
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.poisoned[0] = True
        self.assertTrue(World._pass_through_phases(world))
        self.assertFalse(night2.poisoned[0])

        # drunk token should be passed through
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.drunk_token = Role.UNDERTAKER
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.drunk_token, Role.UNDERTAKER)

        # different drunk token should be invalid
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.drunk_token = Role.UNDERTAKER
        night2.drunk_token = Role.FORTUNE_TELLER
        self.assertFalse(World._pass_through_phases(world))

        # chef number should be passed through
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.chef_number = 1
        self.assertTrue(World._pass_through_phases(world))
        self.assertEqual(night2.chef_number, 1)

        # different chef number should be invalid
        world = World()
        night1 = world.phases[0]
        night2 = world.add_phase(2)
        night1.chef_number = 1
        night2.chef_number = 2
        self.assertFalse(World._pass_through_phases(world))

    def test_comine_poisoned(self):

        # one poisoning should be okay
        phase1 = Phase()
        phase2 = Phase()
        new_phase = Phase()
        phase1.poisoned[0] = True
        result = World._combine_poisoned(new_phase, phase1, phase2, 5)
        self.assertTrue(result)
        self.assertTrue(new_phase.poisoned[0])

        # two poisonings are invalid
        phase1 = Phase()
        phase2 = Phase()
        phase1.poisoned[0] = True
        phase2.poisoned[1] = True
        result = World._combine_poisoned(new_phase, phase1, phase2, 5)
        self.assertFalse(result)

        # other minions with enough room for a poisoner
        phase1 = Phase(num_players=13)
        phase2 = Phase(num_players=13)
        new_phase = Phase(num_players=13)
        phase2.poisoned[0] = True
        new_phase.minion_types[0] = Role.SCARLET_WOMAN
        new_phase.minion_types[1] = Role.SPY
        result = World._combine_poisoned(new_phase, phase1, phase2, 5)
        self.assertTrue(result)
        self.assertTrue(new_phase.poisoned[0])

        # no room for a poisoner
        phase1 = Phase(num_players=13)
        phase2 = Phase(num_players=13)
        new_phase = Phase(num_players=13)
        phase2.poisoned[0] = True
        new_phase.minion_types[0] = Role.SCARLET_WOMAN
        new_phase.minion_types[1] = Role.BARON
        new_phase.minion_types[2] = Role.SPY
        result = World._combine_poisoned(new_phase, phase1, phase2, 5)
        self.assertFalse(result)

        # dead poisoner with active poisoning should return false
        phase1 = Phase()
        phase2 = Phase()
        new_phase = Phase()
        phase1.poisoned[0] = True
        new_phase.characters[0] = Role.POISONER
        new_phase.dead[0] = True
        result = World._combine_poisoned(new_phase, phase1, phase2, 5)
        self.assertFalse(result)

    def test_killed_by_slayer(self):
        pass

if __name__ == '__main__':
    _ = unittest.main()