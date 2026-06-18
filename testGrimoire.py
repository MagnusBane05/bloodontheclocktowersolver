import unittest
from grimoire import Grimoire
from grimoire.nightOrderPosition import NightOrderPosition
from grimoire.role import Role
from grimoire import GrimoirePage

class TestGrimoire(unittest.TestCase):
    def test_chef_worlds(self):

        chef_world = Grimoire()
        chef_world.pages[0].chef_number = 0

        ## Valid worlds
        # Chef 0 with Imp and SW not adjacent
        w1 = Grimoire()
        w1.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SCARLET_WOMAN
        ]
        w1, valid, _ = Grimoire.combine(w1, chef_world)
        self.assertTrue(valid)

        # Chef 0 with evil and Recluse pair
        w2 = Grimoire()
        w2.pages[0].characters = [
            Role.CHEF, Role.RECLUSE, Role.IMP, Role.DRUNK, Role.BARON
        ]
        w2, valid, _ = Grimoire.combine(w2, chef_world)
        self.assertTrue(valid)
        
        # Chef 0 wih Imp Spy pair
        w3 = Grimoire()
        w3.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SPY, Role.LIBRARIAN
        ]
        w3, valid, _ = Grimoire.combine(w3, chef_world)
        self.assertTrue(valid)

        chef_world.pages[0].chef_number = 1
        # Chef 1 with 2 evils together
        w4 = Grimoire()
        w4.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SCARLET_WOMAN, Role.LIBRARIAN
        ]
        w4, valid, _ = Grimoire.combine(w4, chef_world)
        self.assertTrue(valid)

        # Chef 1 with evil and Recluse pair
        w5 = Grimoire()
        w5.pages[0].characters = [
            Role.CHEF, Role.RECLUSE, Role.IMP, Role.DRUNK, Role.BARON
        ]
        w5, valid, _ = Grimoire.combine(w5, chef_world)
        self.assertTrue(valid)

        # Chef 1 with evil and Spy
        w6 = Grimoire()
        w6.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SPY, Role.LIBRARIAN
        ]
        w6, valid, _ = Grimoire.combine(w6, chef_world)
        self.assertTrue(valid)
        
        # Chef 1 with evil, Recluse, evil
        chef_world = Grimoire(num_players=6)
        chef_world.pages[0].chef_number = 1
        w7 = Grimoire(num_players=6)
        w7.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.RECLUSE, Role.SCARLET_WOMAN, Role.LIBRARIAN
        ]
        w7, valid, _ = Grimoire.combine(w7, chef_world)
        self.assertTrue(valid)

        chef_world.pages[0].chef_number = 2
        # Chef 2 with evil, Recluse, Spy
        w8 = Grimoire(num_players=6)
        w8.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.RECLUSE, Role.SPY, Role.LIBRARIAN
        ]
        w8, valid, _ = Grimoire.combine(w8, chef_world)
        self.assertTrue(valid)

        # Chef two with two seperate groups of evils
        chef_world = Grimoire(num_players=13)
        w9 = Grimoire(num_players=13)
        chef_world.pages[0].chef_number = 2
        w9.pages[0].characters = [
            Role.CHEF, Role.IMP, Role.POISONER, Role.WASHERWOMAN, Role.LIBRARIAN,
            Role.SCARLET_WOMAN, Role.BARON, Role.SOLDIER, Role.SLAYER, Role.MAYOR,
            Role.BUTLER, Role.SAINT, Role.UNDERTAKER
        ]
        w9, valid, _ = Grimoire.combine(w9, chef_world)
        self.assertTrue(valid)

        ## Invalid worlds
        chef_world = Grimoire(num_players=5)
        chef_world.pages[0].chef_number = 0
        # Chef 0 with 2 non-Spy evils together (should be Chef 1)
        w_invalid1 = Grimoire()
        w_invalid1.pages[0].characters = [
            Role.CHEF, Role.IMP, Role.SCARLET_WOMAN, Role.WASHERWOMAN, Role.LIBRARIAN
        ]
        w_invalid1, valid, _ = Grimoire.combine(w_invalid1, chef_world)
        self.assertFalse(valid)

        chef_world.pages[0].chef_number = 1
        # Chef 1 with no adjacent evils and no Recluse (should be Chef 0)
        w_invalid2 = Grimoire()
        w_invalid2.pages[0].characters = [
            Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SCARLET_WOMAN
        ]
        w_invalid2, valid, _ = Grimoire.combine(w_invalid2, chef_world)
        self.assertFalse(valid)

        chef_world.pages[0].chef_number = 3
        # Chef 3 impossible in 5 players
        w_invalid3 = Grimoire()
        w_invalid3, valid, _ = Grimoire.combine(w_invalid3, chef_world)
        self.assertFalse(valid)

        # In an unknown world, Chef number can be up to maximum possible
        chef_world.pages[0].chef_number = 2
        world = Grimoire()
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertTrue(valid)

        # If an unknown evil could be a Spy, a chef could get a 0
        chef_world.pages[0].chef_number = 0
        world = Grimoire()
        world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertTrue(valid)
        # self.assertIn(Role.SPY, world.phases[0].minion_types)

        # 0 is not possible if no Spy
        chef_world.pages[0].chef_number = 0
        world = Grimoire()
        world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        world.pages[0].minion_types = [Role.SCARLET_WOMAN]
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertFalse(valid)

        # if Spy is elsewhere, 0 is not possible
        chef_world = Grimoire(13)
        chef_world.pages[0].chef_number = 0
        world = Grimoire(13)
        world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER, Role.SPY, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER]
        world.pages[0].minion_types = [Role.SPY, Role.ANY_OTHER_MINION, Role.ANY_OTHER_MINION]
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertFalse(valid)

        # only 1 possible evil pair can include a spy
        chef_world.pages[0].chef_number = 0
        world = Grimoire(13)
        world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER]
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertFalse(valid)

        # an unknown good could be the Recluse, making 2 the max Chef number
        chef_world = Grimoire()
        chef_world.pages[0].chef_number = 2
        world = Grimoire()
        world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertTrue(valid)

        # if the unknown good is not the Recluse, they can't contribute to the Chef number
        chef_world.pages[0].chef_number = 2
        world = Grimoire()
        world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        world.pages[0].minion_types = [Role.SCARLET_WOMAN]
        world, valid, _ = Grimoire.combine(world, chef_world)
        self.assertFalse(valid)

    def test_add_phase(self):
        # test phases with different nights
        world = Grimoire()
        _ = world.add_page(2, NightOrderPosition.AFTER_IMP)

        self.assertEqual(len(world.pages), 2)
        self.assertEqual(world.pages[0].night, 1)
        self.assertEqual(world.pages[1].night, 2)

        _ = world.add_page(5, NightOrderPosition.AFTER_IMP)
        _ = world.add_page(3, NightOrderPosition.AFTER_IMP)

        self.assertEqual(len(world.pages), 4)
        self.assertEqual(world.pages[2].night, 3)
        self.assertEqual(world.pages[3].night, 5)

        # test same night with different order

        _ = world.add_page(2, NightOrderPosition.AFTER_EXECUTION)
        _ = world.add_page(2, NightOrderPosition.AFTER_SLAYER)

        self.assertEqual(len(world.pages), 6)
        self.assertEqual(world.pages[1].night_order_position, NightOrderPosition.AFTER_IMP)
        self.assertEqual(world.pages[2].night_order_position, NightOrderPosition.AFTER_SLAYER)
        self.assertEqual(world.pages[3].night_order_position, NightOrderPosition.AFTER_EXECUTION)

    # def test_execution(self):
    #     # executed player is dead in both worlds
    #     world = Grimoire()
    #     no_sw_world, sw_world = world.execute_player(1,2)
    #     self.assertEqual(len(no_sw_world.pages), 2)
    #     self.assertTrue(no_sw_world.pages[1].dead[1])
    #     self.assertNotEqual(sw_world, None)
    #     self.assertEqual(len(sw_world.pages), 2)
    #     self.assertTrue(sw_world.pages[1].dead[1])

    #     # known imp executed -> None
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.IMP
    #     no_sw_world, sw_world = world.execute_player(0,2)
    #     self.assertIsNone(no_sw_world)

    #     # minion type is scarlet woman in sw world
    #     world = Grimoire()
    #     _, sw_world = world.execute_player(0,2)
    #     self.assertIn(Role.SCARLET_WOMAN, sw_world.pages[1].minion_types)

    #     # known scarlet woman becomes imp
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.SCARLET_WOMAN
    #     _, sw_world = world.execute_player(1,2)
    #     self.assertNotEqual(sw_world, None)
    #     self.assertEqual(len(sw_world.pages), 2)
    #     self.assertEqual(sw_world.pages[1].characters[0], Role.IMP)

    #     # single alive minion becomes imp
    #     world = Grimoire()
    #     world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_MINION, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
    #     _, sw_world = world.execute_player(0,2)
    #     self.assertNotEqual(sw_world, None)
    #     self.assertEqual(len(sw_world.pages), 2)
    #     self.assertEqual(sw_world.pages[1].characters[1], Role.IMP)
    #     self.assertEqual(sw_world.pages[0].characters[1], Role.SCARLET_WOMAN)
    #     self.assertIn(Role.SCARLET_WOMAN, sw_world.pages[0].minion_types)
    #     self.assertIn(Role.SCARLET_WOMAN, sw_world.pages[1].minion_types)

    #     # non-demons become any role
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.NON_DEMON
    #     _, sw_world = world.execute_player(1,2)
    #     self.assertNotEqual(sw_world, None)
    #     self.assertEqual(len(sw_world.pages), 2)
    #     self.assertEqual(sw_world.pages[1].characters[0], Role.ANY_OTHER)

    #     # minions become any evil
    #     world = Grimoire(13)
    #     world.pages[0].characters[0] = Role.ANY_OTHER_MINION
    #     world.pages[0].characters[2] = Role.ANY_OTHER_MINION
    #     _, sw_world = world.execute_player(1,2)
    #     self.assertNotEqual(sw_world, None)
    #     self.assertEqual(len(sw_world.pages), 2)
    #     self.assertEqual(sw_world.pages[1].characters[0], Role.ANY_OTHER_EVIL)

    #     # no room for scarlet woman in minion types
    #     world = Grimoire()
    #     world.pages[0].minion_types = [Role.BARON, Role.POISONER]
    #     _, sw_world = world.execute_player(1,2)
    #     self.assertIsNone(sw_world)

    #     # no room for scarlet woman in characters
    #     world = Grimoire()
    #     world.pages[0].characters = [Role.POISONER, Role.ANY_OTHER_EVIL, Role.WASHERWOMAN, Role.EMPATH, Role.MONK]
    #     _, sw_world = world.execute_player(2,2)
    #     self.assertIsNone(sw_world)

    #     # scarlet woman is dead already -> None
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.SCARLET_WOMAN
    #     world.pages[0].dead[0] = True
    #     _, sw_world = world.execute_player(1,2)
    #     self.assertIsNone(sw_world)

    #     # non-demon executed
    #     world = Grimoire()
    #     world.pages[0].characters = [Role.POISONER, Role.ANY_OTHER_EVIL, Role.WASHERWOMAN, Role.EMPATH, Role.MONK]
    #     _, sw_world = world.execute_player(1,2)
    #     self.assertIsNone(sw_world)

    # def test_night_death(self):
    #     # player is dead in all worlds
    #     world = Grimoire()
    #     no_sp_world, sp_world = world.killed_by_demon(1,2)
    #     self.assertEqual(len(no_sp_world.pages), 2)
    #     self.assertTrue(no_sp_world.pages[1].dead[1])
    #     self.assertIsNotNone(sp_world)
    #     self.assertEqual(len(sp_world.pages), 2)
    #     self.assertTrue(sp_world.pages[1].dead[1])

    #     # known imp killed by demon -> None
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.IMP
    #     no_sp_world, sp_world = world.killed_by_demon(0,2)
    #     self.assertIsNone(no_sp_world)

    #     # known scarlet woman becomes imp
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.SCARLET_WOMAN
    #     _, sp_world = world.killed_by_demon(1,2)
    #     self.assertIsNotNone(sp_world)
    #     self.assertEqual(len(sp_world.pages), 2)
    #     self.assertEqual(sp_world.pages[1].characters[0], Role.IMP)

    #     # single alive minion becomes demon
    #     world = Grimoire()
    #     world.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER_MINION, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
    #     _, sp_world = world.killed_by_demon(0,2)
    #     self.assertIsNotNone(sp_world)
    #     self.assertEqual(len(sp_world.pages), 2)
    #     self.assertEqual(sp_world.pages[1].characters[1], Role.IMP)

    #     # non-demons become any role
    #     world = Grimoire()
    #     world.pages[0].characters[0] = Role.NON_DEMON
    #     _, sp_world = world.killed_by_demon(1,2)
    #     self.assertIsNotNone(sp_world)
    #     self.assertEqual(len(sp_world.pages), 2)
    #     self.assertEqual(sp_world.pages[1].characters[0], Role.ANY_OTHER)

    #     # any other minions become any other evil
    #     world = Grimoire(13)
    #     world.pages[0].characters[0] = Role.ANY_OTHER_MINION
    #     world.pages[0].characters[2] = Role.ANY_OTHER_MINION
    #     _, sp_world = world.killed_by_demon(1,2)
    #     self.assertIsNotNone(sp_world)
    #     self.assertEqual(len(sp_world.pages), 2)
    #     self.assertEqual(sp_world.pages[1].characters[0], Role.ANY_OTHER_EVIL)

    #     # no room in minion types -> None
    #     world = Grimoire()
    #     world.pages[0].minion_types = [Role.IMP]
    #     _, sp_world = world.killed_by_demon(1,2)
    #     self.assertIsNone(sp_world)

    #     # no alive minions -> None
    #     world = Grimoire()
    #     world.pages[0].characters = [Role.ANY_OTHER, Role.POISONER, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER]
    #     world.pages[0].dead[1] = True
    #     _, sp_world = world.killed_by_demon(0,2)
    #     self.assertIsNone(sp_world)

    #     # known non-demon killed by demon -> None
    #     world = Grimoire()
    #     world.pages[0].characters = [Role.NON_DEMON, Role.WASHERWOMAN, Role.LIBRARIAN, Role.EMPATH, Role.MONK]
    #     _, sp_world = world.killed_by_demon(0,2)
    #     self.assertIsNone(sp_world)

    #     # simple world sanity check
    #     world = Grimoire()
    #     test_characters = [Role.IMP, Role.SCARLET_WOMAN, Role.FORTUNE_TELLER, Role.MONK, Role.CHEF]
    #     world.pages[0].characters = test_characters
    #     _, sp_world = world.killed_by_demon(0,2)
    #     self.assertIsNotNone(sp_world)
    #     self.assertEqual(len(sp_world.pages), 2)
    #     self.assertListEqual(sp_world.pages[0].characters, test_characters)
    #     self.assertListEqual(sp_world.pages[1].characters, [Role.IMP, Role.IMP, Role.FORTUNE_TELLER, Role.MONK, Role.CHEF])
        

    # def test_pass_through_phases(self):
    #     # sanity check, same characters should be okay
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.MONK
    #     night2.characters[0] = Role.MONK
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # different characters should be invalid
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.MONK
    #     night2.characters[0] = Role.SLAYER
    #     self.assertFalse(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # specific role -> non specific should be okay
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.MONK
    #     night2.characters[0] = Role.ANY_OTHER_TOWNSFOLK
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # non-specific role -> specific should be okay
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.ANY_OTHER_EVIL
    #     night2.characters[0] = Role.SCARLET_WOMAN
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # if there was a character change, it's okay
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.SCARLET_WOMAN
    #     night2.characters[0] = Role.IMP
    #     night2.character_changed[0] = True
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # any other evil to non-demon becomes any other minion
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.ANY_OTHER_EVIL
    #     night2.characters[0] = Role.NON_DEMON
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.characters[0], Role.ANY_OTHER_MINION)

    #     # same in reverse
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters[0] = Role.NON_DEMON
    #     night2.characters[0] = Role.ANY_OTHER_EVIL
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.characters[0], Role.ANY_OTHER_MINION)

    #     # combined characters resulting in an invalid world should be invalid
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.characters = [Role.FORTUNE_TELLER, Role.NON_DEMON, Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER]
    #     night2.characters = [Role.FORTUNE_TELLER, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.NON_DEMON]
    #     self.assertFalse(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # if there's a starpass, the scarlet woman should become the imp and other minions stay the same
    #     world = Grimoire(13)
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night2.star_passed = True
    #     night1.characters[0] = Role.SCARLET_WOMAN
    #     night1.characters[1] = Role.ANY_OTHER_MINION
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.characters[0], Role.IMP)
    #     self.assertEqual(night2.characters[1], Role.ANY_OTHER_MINION)

    #     # if there's a starpass but no scarlet woman, any known minions would have caught it and non-demons stay non demons
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night2.star_passed = True
    #     night1.characters[0] = Role.ANY_OTHER_MINION
    #     night1.characters[1] = Role.NON_DEMON
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.characters[0], Role.ANY_OTHER_EVIL)
    #     self.assertEqual(night2.characters[1], Role.NON_DEMON)

    #     # if not all minions are known, non-demons become any other role
    #     world = Grimoire(13)
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night2.star_passed = True
    #     night1.characters[0] = Role.ANY_OTHER_MINION
    #     night1.characters[1] = Role.NON_DEMON
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.characters[0], Role.ANY_OTHER_EVIL)
    #     self.assertEqual(night2.characters[1], Role.ANY_OTHER)

    #     # same minion types should be okay
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.minion_types = [Role.POISONER]
    #     night2.minion_types = [Role.POISONER]
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # different minion types should be invalid
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.minion_types = [Role.POISONER]
    #     night2.minion_types = [Role.SCARLET_WOMAN]
    #     self.assertFalse(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # specific minion type -> any other minion should be okay
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.minion_types = [Role.ANY_OTHER_MINION]
    #     night2.minion_types = [Role.POISONER]
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # same in reverse
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.minion_types = [Role.POISONER]
    #     night2.minion_types = [Role.ANY_OTHER_MINION]
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # red herring should be passed through
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.red_herring[0] = True
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertTrue(night2.red_herring[0])

    #     # two red herrings is invalid
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.red_herring[0] = True
    #     night2.red_herring[1] = True
    #     self.assertFalse(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # poisoned should not be passed through
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.poisoned[0] = True
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertFalse(night2.poisoned[0])

    #     # drunk token should be passed through
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.drunk_token = Role.UNDERTAKER
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.drunk_token, Role.UNDERTAKER)

    #     # different drunk token should be invalid
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.drunk_token = Role.UNDERTAKER
    #     night2.drunk_token = Role.FORTUNE_TELLER
    #     self.assertFalse(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    #     # chef number should be passed through
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.chef_number = 1
    #     self.assertTrue(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]
    #     self.assertEqual(night2.chef_number, 1)

    #     # different chef number should be invalid
    #     world = Grimoire()
    #     night1 = world.pages[0]
    #     night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
    #     night1.chef_number = 1
    #     night2.chef_number = 2
    #     self.assertFalse(Grimoire.pass_through_pages(world)) # pyright: ignore[reportPrivateUsage]

    def test_combine_poisoned(self):

        # one poisoning should be okay
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        new_phase = GrimoirePage()
        phase1.poisoned[0] = True
        result = Grimoire._combine_poisoned(new_phase, phase1, phase2, 5) # pyright: ignore[reportPrivateUsage]
        self.assertTrue(result)
        self.assertTrue(new_phase.poisoned[0])

        # two poisonings are invalid
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        phase1.poisoned[0] = True
        phase2.poisoned[1] = True
        result = Grimoire._combine_poisoned(new_phase, phase1, phase2, 5) # pyright: ignore[reportPrivateUsage]
        self.assertFalse(result)

        # other minions with enough room for a poisoner
        phase1 = GrimoirePage(num_players=13)
        phase2 = GrimoirePage(num_players=13)
        new_phase = GrimoirePage(num_players=13)
        phase2.poisoned[0] = True
        new_phase.minion_types[0] = Role.SCARLET_WOMAN
        new_phase.minion_types[1] = Role.SPY
        result = Grimoire._combine_poisoned(new_phase, phase1, phase2, 5) # pyright: ignore[reportPrivateUsage]
        self.assertTrue(result)
        self.assertTrue(new_phase.poisoned[0])

        # no room for a poisoner
        phase1 = GrimoirePage(num_players=13)
        phase2 = GrimoirePage(num_players=13)
        new_phase = GrimoirePage(num_players=13)
        phase2.poisoned[0] = True
        new_phase.minion_types[0] = Role.SCARLET_WOMAN
        new_phase.minion_types[1] = Role.BARON
        new_phase.minion_types[2] = Role.SPY
        result = Grimoire._combine_poisoned(new_phase, phase1, phase2, 5) # pyright: ignore[reportPrivateUsage]
        self.assertFalse(result)

        # dead poisoner with active poisoning should return false
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        new_phase = GrimoirePage()
        phase1.poisoned[0] = True
        new_phase.characters[0] = Role.POISONER
        new_phase.dead[0] = True
        result = Grimoire._combine_poisoned(new_phase, phase1, phase2, 5) # pyright: ignore[reportPrivateUsage]
        self.assertFalse(result)

    def test_combine_no_outsiders(self):
        # default scenario - neither phase has no outsiders
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        new_phase = GrimoirePage()
        result = Grimoire._combine_no_outsiders(new_phase, phase1, phase2) # pyright: ignore[reportPrivateUsage]
        self.assertTrue(result)
        self.assertFalse(new_phase.no_outsiders)

        # one phase has no outsiders
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        new_phase = GrimoirePage()
        phase1.no_outsiders = True
        result = Grimoire._combine_no_outsiders(new_phase, phase1, phase2) # pyright: ignore[reportPrivateUsage]
        self.assertTrue(result)
        self.assertTrue(new_phase.no_outsiders)

        # neither phase has no outsiders and there is a baron
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        new_phase = GrimoirePage()
        new_phase.add_minion_type(Role.BARON)
        result = Grimoire._combine_no_outsiders(new_phase, phase1, phase2) # pyright: ignore[reportPrivateUsage]
        self.assertTrue(result)
        self.assertFalse(new_phase.no_outsiders)

        # one phase has no outsiders and there is a baron
        phase1 = GrimoirePage()
        phase2 = GrimoirePage()
        new_phase = GrimoirePage()
        phase1.no_outsiders = True
        new_phase.add_minion_type(Role.BARON)
        result = Grimoire._combine_no_outsiders(new_phase, phase1, phase2) # pyright: ignore[reportPrivateUsage]
        self.assertFalse(result)

if __name__ == '__main__':
    _ = unittest.main()