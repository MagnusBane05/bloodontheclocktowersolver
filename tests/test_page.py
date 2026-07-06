import unittest

from grimoire.grimoire_page import GrimoirePage
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

    def deduce_from_outsider_count(self):
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

    def deduce_from_chef_number(self):
        # unknown player has to be evil
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        page.minion_types = [Role.SCARLET_WOMAN]
        page.chef_number = 1
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_EVIL, page.characters[3])

        # unknown player has to be Recluse
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        page.chef_number = 2
        page.make_deductions()
        self.assertEqual(Role.RECLUSE, page.characters[3])

        # unknown player has to be good when Spy is not possible
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.ANY_OTHER]
        page.minion_types = [Role.BARON]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, page.characters[3])

        # unknown player has to be Spy
        page = GrimoirePage(5)
        page.characters = [Role.ANY_OTHER_TOWNSFOLK, Role.IMP, Role.ANY_OTHER_MINION, Role.ANY_OTHER, Role.ANY_OTHER]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.SPY, page.characters[2])

        # unknown player has to be good when Spy is elsewhere
        page = GrimoirePage(10)
        page.characters = [
            Role.ANY_OTHER, Role.SPY, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER,
            Role.ANY_OTHER_GOOD, Role.IMP, Role.ANY_OTHER, Role.ANY_OTHER, Role.ANY_OTHER,
        ]
        page.chef_number = 0
        page.make_deductions()
        self.assertEqual(Role.ANY_OTHER_GOOD, page.characters[7])

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


if __name__ == "__main__":
    _ = unittest.main()