import unittest

from grimoire import Grimoire, gamerules, GrimoirePage, Role, NightOrderPosition


class TestValidation(unittest.TestCase):
    
    def test_validate_world(self):
        # Sanity test, simple world works
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.SCARLET_WOMAN, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        phase.minion_types[0] = Role.SCARLET_WOMAN
        valid = gamerules.is_grim_valid(world)
        self.assertTrue(valid)

        # Only 1 alive imp is okay
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        valid = gamerules.is_grim_valid(world)
        self.assertFalse(valid)

        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        phase.dead[1] = True
        valid = gamerules.is_grim_valid(world)
        self.assertTrue(valid)

        # More than 2 evils is not
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.IMP, Role.SLAYER, Role.CHEF]
        phase.dead = [True, True, False, False, False]
        valid = gamerules.is_grim_valid(world)
        self.assertFalse(valid)

    def test_is_ousider_count_valid(self):
        num_players = 9
        page = GrimoirePage(num_players)
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertTrue(result, "Expected page with all unknown roles to be valid.")

        page.characters[0] = Role.ANY_OTHER_OUTSIDER
        page.characters[1] = Role.ANY_OTHER_OUTSIDER
        page.characters[2:] = [Role.ANY_OTHER_TOWNSFOLK]*7
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertTrue(result, "Expected 9 player game with 2 outsiders to be valid.")

        page.characters[0:3] = [Role.ANY_OTHER_OUTSIDER]*4
        page.characters[4:] = [Role.ANY_OTHER_TOWNSFOLK]*5
        page.minion_types[0] = Role.BARON
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertTrue(result, "Expected 9 player game with 4 outsiders and a Baron to be valid.")

        page.characters[0:3] = [Role.ANY_OTHER_OUTSIDER]*4
        page.characters[4:] = [Role.ANY_OTHER_TOWNSFOLK]*5
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertTrue(result, "Expected 9 player game with 4 outsiders and an unknown minion to be valid.")

        page.characters[0:2] = [Role.ANY_OTHER_OUTSIDER]*3
        page.characters[3:] = [Role.ANY_OTHER_TOWNSFOLK]*6
        page.minion_types[0] = Role.BARON
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertFalse(result, "Expected 9 player game with 3 outsiders and a Baron to be invalid.")

        page.characters[0:3] = [Role.ANY_OTHER_OUTSIDER]*4
        page.characters[4:] = [Role.ANY_OTHER_TOWNSFOLK]*5
        page.minion_types = [Role.POISONER, Role.SCARLET_WOMAN]
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertFalse(result, "Expected 9 player game with 4 outsiders and no Baron to be invalid.")

        page.characters[0:2] = [Role.ANY_OTHER_OUTSIDER]*3
        page.characters[3] = Role.ANY_OTHER
        page.characters[4:] = [Role.ANY_OTHER_TOWNSFOLK]*5
        page.minion_types[0] = Role.BARON
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertTrue(result, "Expected 9 player game with 3 outsiders and an unknown role and a Baron to be valid.")

        page = GrimoirePage(num_players)
        page.no_outsiders = True
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertFalse(result, "Expected a 9 player game with a Librarian 0 to be invalid.")

        num_players = 8
        page = GrimoirePage(num_players)
        page.no_outsiders = True
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertTrue(result, "Expected an 8 player game with a Librarian 0 to be valid (Recluse could register as not an outsider).")

        page.characters[0] = Role.SAINT
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertFalse(result, "Expected an 8 player game with a Saint and Librarian 0 to be invalid.")

        num_players = 10
        page = GrimoirePage(num_players)
        page.no_outsiders = True
        page.minion_types[0] = Role.BARON
        result = gamerules.is_outsider_count_valid(page, num_players)
        self.assertFalse(result, "Expected a page with no outsiders and a Baron to be invalid.")


    def test_is_evil_count_valid(self):
        num_players = 10
        page = GrimoirePage(num_players)
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertTrue(result, "Expected page with all unknown roles to be valid.")

        page.characters[0] = Role.IMP
        page.characters[1] = Role.ANY_OTHER_MINION
        page.characters[2] = Role.ANY_OTHER_MINION
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertTrue(result, "Expected a 10 player game with an Imp and 2 minions to be valid.")

        page.characters[:3] = [Role.ANY_OTHER_EVIL] * 4
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertFalse(result, "Expected a 10 player game with 4 evils to be invalid.")

        page = GrimoirePage(num_players)
        page.characters[0] = Role.IMP
        page.dead[0] = True
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertTrue(result, "Expected a page with a dead Imp and some unknown characters to be valid.")

        page.characters[1] = Role.ANY_OTHER_MINION
        page.characters[2] = Role.ANY_OTHER_MINION
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertFalse(result, "Expected a page with a dead Imp and all known minions to be invalid.")

        page.characters[1] = Role.IMP
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertTrue(result, "Expected a 10 player game with 1 dead Imp, 1 alive Imp and a minion to be valid.")

        page.characters[2] = Role.IMP
        result = gamerules.is_evil_count_valid(page, num_players)
        self.assertFalse(result, "Expected a game with 2 alive Imps to be invalid.")

    def test_is_good_count_valid(self):
        num_players = 10
        page = GrimoirePage(num_players)
        result = gamerules.is_good_count_valid(page, num_players)
        self.assertTrue(result, "Expected page with all unknown roles to be valid.")

        page.characters[0:2] = [Role.ANY_OTHER_EVIL] * 3
        page.characters[3:9] = [Role.ANY_OTHER_GOOD] * 7
        result = gamerules.is_good_count_valid(page, num_players)
        self.assertTrue(result, "Expected a 10 player game with 3 evils and 7 goods to be valid.")

        page.characters[0:2] = [Role.ANY_OTHER_EVIL] * 2
        page.characters[3:9] = [Role.ANY_OTHER_GOOD] * 8
        result = gamerules.is_good_count_valid(page, num_players)
        self.assertFalse(result, "Expected a 10 player game with 2 evils and 8 goods to be invalid.")


    def test_are_minion_types_valid(self):
        page = GrimoirePage(10)
        result = gamerules.are_minion_types_valid(page)
        self.assertTrue(result, "Expected page with all unknown roles and unknown minion types to be valid.")

        page.minion_types = [Role.SCARLET_WOMAN, Role.POISONER]
        result = gamerules.are_minion_types_valid(page)
        self.assertTrue(result, "Expected a page with known minion types and unknown roles to be valid.")

        page = GrimoirePage(10)
        page.characters[0] = Role.SCARLET_WOMAN
        page.characters[1] = Role.POISONER
        result = gamerules.are_minion_types_valid(page)
        self.assertFalse(result, "Expected a page with known minions and unknown minion types to be invalid.")

        page.minion_types = [Role.SCARLET_WOMAN, Role.POISONER]
        result = gamerules.are_minion_types_valid(page)
        self.assertTrue(result, "Expected a page with known minions and matching minion types to be valid.")

        page.minion_types = [Role.SCARLET_WOMAN, Role.BARON]
        result = gamerules.are_minion_types_valid(page)
        self.assertFalse(result, "Expected a page with known minions and mismatching minion types to be invalid.")

    def test_is_poisoning_valid(self):
        num_players = 10
        page = GrimoirePage(num_players)
        result = gamerules.is_poisoning_valid(page, num_players)
        self.assertTrue(result, "Expected a page with no poisoning to be valid.")

        page.poisoned[0] = True
        result = gamerules.is_poisoning_valid(page, num_players)
        self.assertFalse(result, "Expected a page with poisoning but no Poisoner to be invalid.")

        page.minion_types[0] = Role.POISONER
        result = gamerules.is_poisoning_valid(page, num_players)
        self.assertTrue(result, "Expected a page with poisoning and a Poisoner minion type to be valid.")

        page.poisoned[1] = True
        result = gamerules.is_poisoning_valid(page, num_players)
        self.assertFalse(result, "Expected a page with 2 instances of poisoning to be invalid.")

        page = GrimoirePage(num_players)
        page.poisoned[3] = True
        page.minion_types[0] = Role.POISONER
        page.characters[0] = Role.POISONER
        page.dead[0] = True
        result = gamerules.is_poisoning_valid(page, num_players)
        self.assertFalse(result, "Expected a page with poisoning and a dead Poisoner to be invalid.")

        page.characters[0] = Role.ANY_OTHER_MINION
        page.characters[1] = Role.ANY_OTHER_MINION
        page.dead[1] = True
        result = gamerules.is_poisoning_valid(page, num_players)
        self.assertFalse(result, "Expected a page with poisoning and all minions dead to be invalid.")

    def test_is_no_invalid_deuplicates(self):
        page = GrimoirePage(10)
        result = gamerules.is_no_invalid_duplicates(page)
        self.assertTrue(result, "Expected a page with all unknown roles to be valid.")

        page.characters[0] = Role.NON_DEMON
        page.characters[1] = Role.NON_DEMON
        result = gamerules.is_no_invalid_duplicates(page)
        self.assertTrue(result, "Expected a page with allowed duplicate roles to be valid.")

        page.characters[0] = Role.IMP
        page.characters[1] = Role.IMP
        page.dead[0] = True
        result = gamerules.is_no_invalid_duplicates(page)
        self.assertTrue(result, "Expected a page with an alive and dead Imp to be valid.")

        page.characters[0] = Role.INVESTIGATOR
        page.characters[1] = Role.INVESTIGATOR
        result = gamerules.is_no_invalid_duplicates(page)
        self.assertFalse(result, "Expected a page with disallowed duplicate roles to be invalid.")

    def test_is_no_sober_saint_executed(self):
        page = GrimoirePage(10)
        page.night_order_position = NightOrderPosition.AFTER_EXECUTION
        page.characters[0] = Role.SAINT
        page.dead[0] = True
        page.executee = 0
        result = gamerules.is_no_sober_saint_executed(page)
        self.assertFalse(result, "Expected a page with an executed sober Saint to be invalid.")

        page.poisoned[0] = True
        result = gamerules.is_no_sober_saint_executed(page)
        self.assertTrue(result, "Expected a page with a poisoned executed Saint to be valid.")

        page.poisoned[0] = False
        page.night_order_position = NightOrderPosition.AFTER_IMP
        result = gamerules.is_no_sober_saint_executed(page)
        self.assertTrue(result, "Expected non-execution page to be valid.")

class TestScarletWomanCatch(unittest.TestCase):
    def test_can_scarlet_woman_catch(self):
        imp = 3
        page = GrimoirePage(10)        
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertTrue(result, "Expected blank pagee to be true.")

        scarlet_woman = 0
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        page.characters[imp] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertTrue(result, "Expected page with known Imp and Scarlet Woman to be true.")

        page.characters[imp] = Role.NON_DEMON
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected executing a non-demon to be false.")

        page.characters[imp] = Role.IMP
        page.dead[scarlet_woman] = True        
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with a known dead Scalet Woman to be false.")

        page = GrimoirePage(10)
        page.minion_types = [Role.BARON, Role.POISONER]
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with no room for a Scarlet Woman in the minion types to be false.")

        page = GrimoirePage(10)
        page.characters[0] = Role.ANY_OTHER_MINION
        page.characters[1] = Role.ANY_OTHER_MINION
        page.dead[0] = True
        page.dead[1] = True
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with all minions dead to be false.")

        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[0] = Role.IMP
        page.characters[1] = Role.IMP
        page.characters[3] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with no Scarlet Woman candidates to be false.")

    def test_can_imp_starpass(self):
        imp = 3
        page = GrimoirePage(10)
        result = gamerules.can_imp_starpass(page, imp)
        self.assertTrue(result, "Expected blank pagee to be true.")

        scarlet_woman = 0
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        page.characters[imp] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertTrue(result, "Expected page with known Imp and Scarlet Woman to be true.")

        page.characters[imp] = Role.NON_DEMON
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected executing a non-demon to be false.")

        page = GrimoirePage(10)
        page.characters[0] = Role.ANY_OTHER_MINION
        page.characters[1] = Role.ANY_OTHER_MINION
        page.dead[0] = True
        page.dead[1] = True
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with all minions dead to be false.")

        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[0] = Role.IMP
        page.characters[1] = Role.IMP
        page.characters[3] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with no minion candidates to be false.")
        
if __name__ == '__main__':
    _ = unittest.main()