import unittest
from unittest.mock import patch

from grimoire.deduced_page import deduce_from_chef_number
from grimoire.grimoire_page import GrimoirePage, _FIELDS_NOT_VALIDATED, _FIELD_CHANGE_TYPES  # pyright: ignore[reportPrivateUsage]
from grimoire.role import *


class TestDeducePage(unittest.TestCase):
    def test_sanity_check(self):
        # saninty check, a fully deduced world should have no changes made
        phase = GrimoirePage()
        phase.make_deductions()
        for i,c in enumerate(phase.characters):
            self.assertEqual(c,Role.ANY_OTHER, f"Player {i} has a non ANY_OTHER role ({c})")
        # saninty check, a fully unknown world should have no changes made
        phase = GrimoirePage()
        characters = [Role.IMP, Role.SCARLET_WOMAN, Role.MONK, Role.EMPATH, Role.SLAYER]
        phase.characters = characters
        phase.make_deductions()
        self.assertListEqual(phase.characters, characters)

    def test_deduce_minion_from_minion_type(self):
        # if there is one unknown minion and minion types are known, assign the type to the minion
        # case with 1 minion
        phase = GrimoirePage()
        phase.characters[0] = Role.ANY_OTHER_MINION
        phase.minion_types = [Role.SCARLET_WOMAN]
        phase.make_deductions()
        self.assertEqual(Role.SCARLET_WOMAN, phase.characters[0])
        # case with known minions + 1 unknown minion
        phase = GrimoirePage(13)
        phase.characters[0] = Role.SCARLET_WOMAN
        phase.characters[1] = Role.SPY
        phase.characters[2] = Role.ANY_OTHER_MINION
        phase.minion_types = [Role.SCARLET_WOMAN, Role.SPY, Role.BARON]
        phase.make_deductions()
        self.assertEqual(Role.BARON, phase.characters[2])

    def test_deduce_alignment(self):
        # if all good players are accounted for, assign evil roles to the unknown players
        phase = GrimoirePage()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER]
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_EVIL, phase.characters[3])
        self.assertEqual(Role.ANY_OTHER_EVIL, phase.characters[4])

        # if all good players are accounted for, non-demons should become any minion
        phase = GrimoirePage()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON, Role.ANY_OTHER]
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[3])

        # if all minions are known and some players have NON_DEMON role, assign ANY_OTHER_GOOD to those players
        phase = GrimoirePage()
        phase.characters[0] = Role.ANY_OTHER_MINION
        phase.characters[1] = Role.NON_DEMON
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[1])

        # if all evils are known, assign ANY_OTHER_GOOD to NON_DEMON roles
        phase = GrimoirePage()
        phase.characters[0] = Role.ANY_OTHER_EVIL
        phase.characters[1] = Role.ANY_OTHER_EVIL
        phase.characters[2] = Role.NON_DEMON
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[2])

        # if all evils are accounted for, assign good roles to any unknowns
        phase = GrimoirePage()
        phase.characters = [Role.IMP, Role.ANY_OTHER_MINION, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER]
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[3])
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[4])

    def test_deduce_from_known_imp(self):
        # if there is only 1 spot left for an alive demon, assign Imp to that player
        # case with no dead players
        phase = GrimoirePage()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.NON_DEMON, Role.ANY_OTHER_MINION, Role.ANY_OTHER]
        phase.make_deductions()
        self.assertEqual(Role.IMP, phase.characters[4])
        # case with dead Imp
        phase = GrimoirePage()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.NON_DEMON, Role.ANY_OTHER, Role.IMP]
        phase.dead[4] = True
        phase.make_deductions()
        self.assertEqual(Role.IMP, phase.characters[3])

        # if the alive demon is known, assign minions to the other evil players
        # case with alive Imp
        phase = GrimoirePage()
        phase.characters[0] = Role.IMP
        phase.characters[1] = Role.ANY_OTHER_EVIL
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[1])
        # case with dead Imp and alive Imp
        phase = GrimoirePage()
        phase.characters[0] = Role.IMP
        phase.characters[1] = Role.IMP
        phase.dead[0] = True
        phase.characters[2] = Role.ANY_OTHER_EVIL
        phase.characters[3] = Role.ANY_OTHER_EVIL
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[2])
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[3])

    def test_deduce_from_outsider_count(self):
        # if outsider count is known, assign leftover outsiders to unknown good players
        # case with Baron
        phase = GrimoirePage()
        phase.characters = [Role.BARON, Role.IMP, Role.MONK, Role.SAINT, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.BARON]
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_OUTSIDER, phase.characters[4])
        # case without Baron
        phase = GrimoirePage(6)
        phase.characters = [Role.SCARLET_WOMAN, Role.IMP, Role.ANY_OTHER_TOWNSFOLK, Role.MAYOR, Role.MONK, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.SCARLET_WOMAN]
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_OUTSIDER, phase.characters[5])
        # if outsider count is known, assign leftover townsfolk to unknown good players
        phase = GrimoirePage()
        phase.characters = [Role.POISONER, Role.IMP, Role.MONK, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.POISONER]
        phase.make_deductions()
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, phase.characters[3])
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, phase.characters[4])
        # if Baron is not possible, assign townsfolk 
        page = GrimoirePage(5)
        page.characters = [Role.IMP, Role.RAVENKEEPER, Role.ANY_OTHER_GOOD, Role.SOLDIER, Role.ANY_OTHER_MINION]
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, page.characters[2])

    def test_deduce_from_chef_number(self):
        # sanity check -> all unknowns don't change anything
        page = GrimoirePage(10)
        page.chef_number = 1
        page.make_deductions()
        self.assertTrue(all(character == Role.ANY_OTHER for character in page.characters))
        self.assertEqual(page.in_chef_pair, 0)

        # unknown player has to be evil
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        page.minion_types = [Role.SCARLET_WOMAN]
        page.chef_number = 1
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_EVIL, page.characters[3])

        # unknown player with known recluse and minion has to be Imp
        page = GrimoirePage(8)
        page.characters = [
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.RECLUSE, Role.ANY_OTHER_OUTSIDER, 
            Role.BARON, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_OUTSIDER, Role.ANY_OTHER
        ]
        page.minion_types[0] = Role.BARON
        page.chef_number = 1
        page.make_deductions()
        self.assertEqual(Role.IMP, page.characters[1])

        # unknown player has to be Recluse
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        page.chef_number = 2
        page.make_deductions()
        self.assertEqual(Role.RECLUSE, page.characters[3])

        # unknown player has to be Recluse when player is in any possible Chef number
        page = GrimoirePage(10)
        page.characters = [
            Role.ANY_OTHER_TOWNSFOLK, Role.SCARLET_WOMAN, Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_EVIL
        ]
        page.chef_number = 1
        page.minion_types[0] = Role.SCARLET_WOMAN
        page.make_deductions()
        self.assertEqual(Role.RECLUSE, page.characters[2])
        self.assertEqual(Role.BARON, page.minion_types[1])

        # unknown player has to be good when Spy is not possible
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        page.minion_types = [Role.BARON]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, page.characters[3])

        # if evils are accounted for from in_chef_pair, assign good roles to unknowns
        page = GrimoirePage(10)
        page.characters = [
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_MINION,
            Role.IMP, Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK
        ]
        page.chef_number = 3
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_OUTSIDER, page.characters[2])

        # unknown player has to be Spy
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER_TOWNSFOLK, Role.IMP, Role.ANY_OTHER_MINION, Role.ANY_OTHER, Role.ANY_OTHER]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.SPY, page.characters[2])

        # If more than 1 Spy candidate, can't determine Spy
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_EVIL, page.characters[0])
        self.assertEqual(Role.ANY_OTHER_EVIL, page.characters[1])

        # evil player between two evils must by Spy when Chef 0
        page = GrimoirePage(10)
        page.characters = [
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD,
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD

        ]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.SPY, page.characters[7])

        # evil player between two evils must by Spy when Chef 1
        page = GrimoirePage(10)
        page.characters = [
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD,
            Role.ANY_OTHER_GOOD, Role.IMP, Role.ANY_OTHER_EVIL, Role.BARON, Role.ANY_OTHER_GOOD

        ]
        page.chef_number = 1
        page.minion_types[0] = Role.BARON
        page.make_deductions()
        self.assertEqual(Role.SPY, page.characters[7])

        # unknown player has to be good when Spy is elsewhere
        page = GrimoirePage(10)
        page.characters = [
            Role.ANY_OTHER, Role.SPY, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER,
            Role.ANY_OTHER_GOOD, Role.IMP, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER,
        ]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, page.characters[7])

        # chef number only possible with recluse means Baron in play
        page = GrimoirePage(5)
        page.characters = [Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.CHEF]
        page.chef_number = 2
        page.make_deductions()
        self.assertIn(Role.BARON, page.minion_types)

        # chef number only possible with Recluse, but outsider count covers it
        page = GrimoirePage(6)
        page.characters = [Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.CHEF, Role.ANY_OTHER]
        page.chef_number = 2
        page.minion_types = [Role.SCARLET_WOMAN]
        page.make_deductions()
        self.assertEqual(Role.SCARLET_WOMAN, page.minion_types[0])

        # chef number only possible with Recluse, outsider count covers it, but it's the wrong outsider
        page = GrimoirePage(6)
        page.characters = [Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER, Role.SAINT, Role.CHEF, Role.ANY_OTHER]
        page.chef_number = 2
        page.minion_types = [Role.ANY_OTHER_MINION]
        page.make_deductions()
        self.assertEqual(Role.BARON, page.minion_types[0])

        # Chef number only possible with Recluse when evil configuration isn't enough
        page = GrimoirePage(13)
        page.characters = [
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON, Role.ANY_OTHER_MINION, Role.IMP,
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON, Role.SPY
        ]
        page.chef_number = 3
        page.minion_types[0] = Role.SPY
        page.make_deductions()
        self.assertIn(Role.BARON, page.minion_types)

        # 2 seperate pairs is too many evils/Recluse, the only option is 1 continuous pair
        page = GrimoirePage(8)
        page.characters = [
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.BARON, Role.ANY_OTHER_TOWNSFOLK, 
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_OUTSIDER, Role.BUTLER
        ]
        page.chef_number = 2
        page.minion_types = [Role.BARON]
        page.make_deductions()
        self.assertEqual(Role.RECLUSE, page.characters[0])
        self.assertEqual(Role.IMP, page.characters[1])

        # unknown player has to be in chef number, but not sure whether Recluse or evil
        page = GrimoirePage(8)
        page.characters = [
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.NON_DEMON
        ]
        page.chef_number = 1
        page.make_deductions()
        self.assertTrue(page.in_chef_pair & (1 << 6))
        self.assertTrue(page.in_chef_pair & (1 << 7))

        # unknown pair is in chef number, but either could be Recluse or evil
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER, Role.ANY_OTHER, Role.CHEF, Role.ANY_OTHER, Role.DRUNK]
        page.chef_number = 1
        page.make_deductions()
        self.assertTrue(page.in_chef_pair & (1 << 0))
        self.assertTrue(page.in_chef_pair & (1 << 1))
        self.assertEqual(Role.ANY_OTHER, page.characters[0])
        self.assertEqual(Role.ANY_OTHER, page.characters[1])

        # edges of chef line are unknown but middle is always in a pair
        page = GrimoirePage(8)
        page.characters = [
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON, Role.MONK, # players 6 and 7 are always in the chef number
            Role.CHEF, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON
        ]
        page.chef_number = 2
        page.make_deductions()
        self.assertTrue(page.in_chef_pair & (1 << 6))
        self.assertTrue(page.in_chef_pair & (1 << 7))    

        # player who is in all possible chef pairs, but not sure which one or evil/Recluse
        page = GrimoirePage(8)
        page.characters = [
            Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER
        ]
        page.chef_number = 1
        page.make_deductions()
        self.assertTrue(page.in_chef_pair & (1 << 7))

    def test_multi_stage_deductions(self):
        # multi-stage deductions
        phase = GrimoirePage()
        phase.characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.POISONER]
        phase.make_deductions()
        self.assertEqual(Role.IMP, phase.characters[0])
        self.assertEqual(Role.POISONER, phase.characters[1])
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, phase.characters[4])

class TestPage(unittest.TestCase):

    def test_apply_starpass(self):
        imp = 3
        page = GrimoirePage()
        page.dead[imp] = True

        new_imp = page.apply_starpass(imp)
        self.assertIsNone(new_imp)


        page = GrimoirePage(10)
        scarlet_woman = 0
        page.dead[imp] = True
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN

        new_imp = page.apply_starpass(imp)
        self.assertIsNotNone(new_imp)
        self.assertEqual(page.characters[imp], Role.IMP, "Expected old Imp to still be an Imp.")
        self.assertEqual(new_imp, scarlet_woman, "Expected new imp to be the old Scarlet Woman.")
        self.assertEqual(page.characters[scarlet_woman], Role.IMP, "Expected Scarlet Woman to become the Imp.")

        page = GrimoirePage(10)
        page.dead[imp] = True
        minion1 = 0
        minion2 = 1
        page.characters[minion1] = Role.ANY_OTHER_MINION
        page.characters[minion2] = Role.ANY_OTHER_MINION
        page.dead[minion1] = True

        new_imp = page.apply_starpass(imp)
        self.assertIsNotNone(new_imp)
        self.assertEqual(page.characters[imp], Role.IMP, "Expected old Imp to still be an Imp.")
        self.assertEqual(new_imp, minion2, "Expected new imp to be the last alive minion.")
        self.assertEqual(page.characters[minion2], Role.IMP, "Expected last alive minion to become the Imp.")

        page = GrimoirePage(10)
        minion_candidate_1 = 0
        minion_candidate_2 = 1
        minion_candidate_3 = 2
        page.dead[imp] = True
        page.dead[minion_candidate_1] = True
        page.dead[minion_candidate_2] = True
        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[imp] = Role.IMP
        page.characters[minion_candidate_1] = Role.ANY_OTHER
        page.characters[minion_candidate_2] = Role.ANY_OTHER
        page.characters[minion_candidate_3] = Role.ANY_OTHER

        new_imp = page.apply_starpass(imp)
        self.assertIsNotNone(new_imp)
        self.assertEqual(page.characters[imp], Role.IMP, "Expected old Imp to still be an Imp.")
        self.assertEqual(new_imp, minion_candidate_3, "Expected new imp to be the last minion candidate.")
        self.assertEqual(page.characters[minion_candidate_3], Role.IMP, "Expected last alive minion candidate to become the Imp.")

    def test_apply_scarlet_woman_catch(self):
        imp = 3
        page = GrimoirePage()
        page.dead[imp] = True

        new_imp = page.apply_sw_catch(imp)
        self.assertIsNone(new_imp)
        self.assertEqual(page.characters[imp], Role.IMP, "Expected old Imp to still be an Imp.")
        self.assertIn(Role.SCARLET_WOMAN, page.minion_types, "Expected Scarlet Woman to be in the minion types.")

        page = GrimoirePage()
        scarlet_woman = 0
        page.dead[imp] = True
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN

        new_imp = page.apply_sw_catch(imp)
        self.assertIsNotNone(new_imp)
        self.assertEqual(new_imp, scarlet_woman, "Expected the new Imp to be the Scarlet Woman.")
        self.assertEqual(page.characters[scarlet_woman], Role.IMP, "Expected Scarlet Woman to have become the new Imp.")
        self.assertIn(Role.SCARLET_WOMAN, page.minion_types, "Expected Scarlet Woman to be in the minion types.")

        page = GrimoirePage(10)
        page.dead[imp] = True
        minion1 = 0
        minion2 = 1
        page.characters[minion1] = Role.ANY_OTHER_MINION
        page.characters[minion2] = Role.ANY_OTHER_MINION
        page.dead[minion1] = True

        new_imp = page.apply_sw_catch(imp)
        self.assertIsNotNone(new_imp)
        self.assertIn(Role.SCARLET_WOMAN, page.minion_types, "Expected Scarlet Woman to be in the minion types.")
        self.assertEqual(page.characters[imp], Role.IMP, "Expected old Imp to still be an Imp.")
        self.assertEqual(new_imp, minion2, "Expected new imp to be the last alive minion.")
        self.assertEqual(page.characters[minion2], Role.IMP, "Expected last alive minion to become the Imp.")

        page = GrimoirePage(10)
        minion_candidate_1 = 0
        minion_candidate_2 = 1
        minion_candidate_3 = 2
        page.dead[imp] = True
        page.dead[minion_candidate_1] = True
        page.dead[minion_candidate_2] = True
        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[imp] = Role.IMP
        page.characters[minion_candidate_1] = Role.ANY_OTHER
        page.characters[minion_candidate_2] = Role.ANY_OTHER
        page.characters[minion_candidate_3] = Role.ANY_OTHER

        new_imp = page.apply_sw_catch(imp)
        self.assertIsNotNone(new_imp)
        self.assertIn(Role.SCARLET_WOMAN, page.minion_types, "Expected Scarlet Woman to be in the minion types.")
        self.assertEqual(page.characters[imp], Role.IMP, "Expected old Imp to still be an Imp.")
        self.assertEqual(new_imp, minion_candidate_3, "Expected new imp to be the last minion candidate.")
        self.assertEqual(page.characters[minion_candidate_3], Role.IMP, "Expected last alive minion candidate to become the Imp.")

class TestCanBeCharacter(unittest.TestCase):
    def test_unknown_character(self):
        page = GrimoirePage()
        character = Role.ANY_OTHER
        player = 0
        result = page.can_be_character(character, player)
        self.assertTrue(result, "Expected unknown character to be valid.")

    def test_outsider(self):
        page = GrimoirePage(10)
        character = Role.ANY_OTHER_OUTSIDER
        player = 0
        result = page.can_be_character(character, player)
        self.assertTrue(result, "Expected player able to be outsider when Baron could still be a minion type.")

        page.minion_types = [Role.POISONER, Role.SCARLET_WOMAN]
        result = page.can_be_character(character, player)
        self.assertFalse(result, "Expected player not able to be outsider when Baron is not a minion type.")

        page = GrimoirePage(10)
        page.characters[1] = Role.RECLUSE
        page.characters[2] = Role.DRUNK
        result = page.can_be_character(character, player)
        self.assertFalse(result, "Expected player not able to be outsider when 2 other players already outsiders.")

        page = GrimoirePage(10)
        page.no_outsiders = True
        result = page.can_be_character(Role.SAINT, player)
        self.assertFalse(result, "Expected player not able to be outsider when librarian shown no outsiders.")

        page = GrimoirePage(8)
        page.no_outsiders = True
        result = page.can_be_character(Role.RECLUSE, player)
        self.assertTrue(result, "Expected Recluse able to register as non-outsider to Librarian.")

        page = GrimoirePage(8)
        page.characters[1] = Role.ANY_OTHER_OUTSIDER
        page.no_outsiders = True
        result = page.can_be_character(Role.ANY_OTHER_OUTSIDER, player)
        self.assertFalse(result, "Expected 2 outsiders not able to register as non-outsider to Librarian.")

    def test_baron(self):
        page = GrimoirePage(5)
        page.no_outsiders = True
        player = 0
        result = page.can_be_character(Role.BARON, player)
        self.assertFalse(result)

class TestCanHaveNoOutsiders(unittest.TestCase):
    def test_all(self):
        page = GrimoirePage(5)
        result = page.can_have_no_outsiders()
        self.assertTrue(result, "Expected no-outsiders to be valid for a 5-player game.")

        page = GrimoirePage(6)
        result = page.can_have_no_outsiders()
        self.assertTrue(result, "Expected no-outsiders to be valid on 6 players when an unknown player could be Recluse.")

        page = GrimoirePage(9)
        result = page.can_have_no_outsiders()
        self.assertFalse(result, "Expected no-outsiders to be invalid on 9 players (base 2 outsiders).")

        page = GrimoirePage(6)
        page.characters[0] = Role.RECLUSE
        result = page.can_have_no_outsiders()
        self.assertTrue(result, "Expected no-outsiders to be valid when the only outsider is a Recluse.")

        page = GrimoirePage(6)
        page.characters[0] = Role.SAINT
        result = page.can_have_no_outsiders()
        self.assertFalse(result, "Expected no-outsiders to be invalid when a known outsider is already present.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.BARON
        result = page.can_have_no_outsiders()
        self.assertFalse(result, "Expected no-outsiders to be invalid when a Baron is in the game.")

class TestCanHaveChefNumber(unittest.TestCase):
    def test_all(self):
        page = GrimoirePage(5)
        self.assertTrue(page.can_have_chef_number(2), "Expected a chef number of 2 to be valid for a 5-player game.")
        self.assertFalse(page.can_have_chef_number(3), "Expected a chef number of 3 to be invalid for a 5-player game.")

        page = GrimoirePage(5)
        page.characters = [Role.IMP, Role.ANY_OTHER_MINION, Role.MONK, Role.EMPATH, Role.SLAYER]
        self.assertTrue(page.can_have_chef_number(1), "Expected a chef number of 1 to be valid for the provided role setup.")
        self.assertFalse(page.can_have_chef_number(2), "Expected a chef number of 2 to be invalid for the provided role setup.")

        page = GrimoirePage(5)
        page.characters = [Role.RECLUSE, Role.SPY, Role.MONK, Role.MONK, Role.MONK]
        self.assertFalse(page.can_have_chef_number(0), "Expected no chef number to be valid when there aren't enough possible evil players.")

        page = GrimoirePage(6)
        page.add_minion_type(Role.SPY)
        page.characters = [Role.RECLUSE, Role.SPY, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SLAYER]
        self.assertTrue(page.can_have_chef_number(0), "Expected chef number 0 to be valid when a known Recluse is adjacent to a known Spy.")
        self.assertTrue(page.can_have_chef_number(1), "Expected chef number 1 to be valid when a known Recluse and Spy can still form one evil adjacency pair.")
        self.assertFalse(page.can_have_chef_number(2), "Expected chef number 2 to be invalid for the provided Recluse/Spy layout.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.SCARLET_WOMAN
        page.characters = [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        self.assertFalse(page.can_have_chef_number(0), "Expected a chef number of 0 to be invalid when 2 non-Spy evils next to each other")
        self.assertTrue(page.can_have_chef_number(1), "Expected a chef 1 to be valid with 2 non-Spy evils next to each other.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.SPY
        page.characters = [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        self.assertTrue(page.can_have_chef_number(0), "Expected a chef number of 0 to be valid when 2 possible spies next to each other")
        self.assertTrue(page.can_have_chef_number(1), "Expected a chef 1 to be valid with 2 possible spies next to each other.")
        self.assertFalse(page.can_have_chef_number(2), "Expected a chef 2 to be invalid with 2 evils next to non-reclus.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.BARON
        page.characters = [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        self.assertTrue(page.can_have_chef_number(2), "Expected a chef 2 to be valid with 2 evils next to a possible recluse.")

class TestCanBePoisoned(unittest.TestCase):
    def test_all(self):
        page = GrimoirePage(5)
        result = page.can_be_poisoned(0)
        self.assertTrue(result, "Expected poisoning to be valid when the Poisoner can still be added as a minion type.")
        self.assertEqual(page.minion_types, [Role.ANY_OTHER_MINION], "Expected can_be_poisoned not to modify the page's minion types.")
        self.assertEqual(page.poisoned, [False]*5, "Expected can_be_poisoned not to modify the page's poisoned players.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.POISONER
        result = page.can_be_poisoned(0)
        self.assertTrue(result, "Expected poisoning to be valid when the Poisoner is a known minion type.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.BARON
        result = page.can_be_poisoned(0)
        self.assertFalse(result, "Expected poisoning to be invalid when all minion types are known and none is the Poisoner.")
        self.assertEqual(page.minion_types, [Role.BARON], "Expected can_be_poisoned not to modify the page's minion types.")

        page = GrimoirePage(5)
        page.apply_poisoned(1)
        result = page.can_be_poisoned(0)
        self.assertFalse(result, "Expected poisoning to be invalid when another player is already poisoned.")

        page = GrimoirePage(5)
        page.minion_types[0] = Role.POISONER
        page.characters[1] = Role.POISONER
        page.dead[1] = True
        result = page.can_be_poisoned(0)
        self.assertFalse(result, "Expected poisoning to be invalid when the known Poisoner is dead.")

def _page_state(page: GrimoirePage) -> dict[str, object]:
    return {k: (list(v) if isinstance(v, list) else v) for k, v in vars(page).items()}

def _chef_page(characters: list[Role], chef_number: int, minion_types: list[Role] | None = None) -> GrimoirePage:
    page = GrimoirePage(len(characters))
    page.characters = list(characters)
    if minion_types is not None:
        page.minion_types = list(minion_types)
    page.chef_number = chef_number
    return page

def _settle(page: GrimoirePage) -> None:
    # run deductions until the page stops changing, without trusting the deduced flag
    for _ in range(20):
        before = _page_state(page)
        page.make_deductions()
        if _page_state(page) == before:
            return
    raise AssertionError("page did not settle")

# (description, characters, chef number, minion types)
_CHEF_CASES: list[tuple[str, list[Role], int, list[Role] | None]] = [
    ("known Spy in a pair with a known evil",
        [Role.ANY_OTHER_TOWNSFOLK, Role.IMP, Role.ANY_OTHER_MINION, Role.ANY_OTHER, Role.ANY_OTHER], 0, None),
    ("Spy between two evils",
        [Role.ANY_OTHER_GOOD]*6 + [Role.ANY_OTHER_EVIL]*3 + [Role.ANY_OTHER_GOOD], 0, None),
    ("Spy between two evils, Chef 1",
        [Role.ANY_OTHER_GOOD]*6 + [Role.IMP, Role.ANY_OTHER_EVIL, Role.BARON, Role.ANY_OTHER_GOOD], 1,
        [Role.BARON, Role.ANY_OTHER_MINION]),
    ("known Recluse in the chef pair",
        [Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER], 2, None),
    ("Recluse and Baron needed for the chef number",
        [Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.CHEF], 2, None),
    ("Recluse needed, outsider count covers it",
        [Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.CHEF, Role.ANY_OTHER], 2,
        [Role.SCARLET_WOMAN]),
    ("Recluse in any possible chef number",
        [
            Role.ANY_OTHER_TOWNSFOLK, Role.SCARLET_WOMAN, Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_EVIL
        ], 1, [Role.SCARLET_WOMAN, Role.ANY_OTHER_MINION]),
    ("unknown player good when Spy is not possible",
        [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER], 0, [Role.BARON]),
    ("unknown player good when Spy is elsewhere",
        [
            Role.ANY_OTHER, Role.SPY, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER,
            Role.ANY_OTHER_GOOD, Role.IMP, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER,
        ], 0, None),
    ("unknown pair in chef number, Recluse or evil",
        [Role.ANY_OTHER, Role.ANY_OTHER, Role.CHEF, Role.ANY_OTHER, Role.DRUNK], 1, None),
    ("one continuous pair",
        [
            Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.BARON, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_OUTSIDER, Role.BUTLER
        ], 2, [Role.BARON]),
    ("player in all possible chef pairs",
        [
            Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK,
            Role.ANY_OTHER, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER
        ], 1, None),
]

class TestChefDeductionsReportChanges(unittest.TestCase):
    """deduce_from_chef_number must only return True when it changed the page,
    otherwise make_deductions keeps running deduction steps that do nothing."""

    def test_settled_page_reports_no_change(self):
        for description, characters, chef_number, minion_types in _CHEF_CASES:
            with self.subTest(description):
                page = _chef_page(characters, chef_number, minion_types)
                _settle(page)
                before = _page_state(page)
                deduced = deduce_from_chef_number(page)
                self.assertEqual(before, _page_state(page), "Expected a settled page not to change.")
                self.assertFalse(deduced, "Expected no deduction to be reported on a settled page.")

    def test_reported_change_is_real(self):
        for description, characters, chef_number, minion_types in _CHEF_CASES:
            with self.subTest(description):
                page = _chef_page(characters, chef_number, minion_types)
                for _ in range(20):
                    before = _page_state(page)
                    deduced = deduce_from_chef_number(page)
                    changed = _page_state(page) != before
                    self.assertEqual(changed, deduced, "Expected the deduced flag to match whether the page changed.")
                    if not changed:
                        break

    def test_settled_page_runs_one_deduction_step(self):
        for description, characters, chef_number, minion_types in _CHEF_CASES:
            with self.subTest(description):
                page = _chef_page(characters, chef_number, minion_types)
                _settle(page)
                with patch.object(GrimoirePage, "_deduction_step", autospec=True, side_effect=GrimoirePage._deduction_step) as step:  # pyright: ignore[reportPrivateUsage]
                    page.make_deductions()
                self.assertEqual(1, step.call_count, "Expected one deduction step on a settled page.")

class TestFields(unittest.TestCase):
    def test_all_fields_validated(self):
        page = GrimoirePage()
        for field in vars(page):
            with self.subTest(field):
                validated = field in _FIELD_CHANGE_TYPES.keys()
                explicitly_not_validated = field in _FIELDS_NOT_VALIDATED
                self.assertTrue(validated or explicitly_not_validated, f"Expected {field} to be mapped to a ChangeType or explicitly not validated.")

    def test_not_validated_no_overlaps(self):
        for field in _FIELDS_NOT_VALIDATED:
            with self.subTest(field):
                self.assertNotIn(field, _FIELD_CHANGE_TYPES.keys(), f"Expected {field} not to be both mapped to a ChangeType and explicitly not validated.")

if __name__ == "__main__":
    _ = unittest.main()
