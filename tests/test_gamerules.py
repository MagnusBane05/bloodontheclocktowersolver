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

        # 2 alive Imps is not valid
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        valid = gamerules.is_grim_valid(world)
        self.assertFalse(valid)

        # Only 1 alive imp is okay
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

class TestIsChefNumberValid(unittest.TestCase):
    def make_page(
        self,
        characters: list[Role],
        chef_number: int | None,
        minion_types: list[Role] | None = None,
    ) -> GrimoirePage:
        page = GrimoirePage(len(characters))
        page.characters = characters
        page.chef_number = chef_number

        if minion_types is not None:
            page.minion_types = minion_types

        return page

    def assertChefValid(
        self,
        characters: list[Role],
        chef_number: int | None,
        expected: bool,
        minion_types: list[Role] | None = None,
    ) -> None:
        page = self.make_page(characters, chef_number, minion_types)
        self.assertEqual(
            expected,
            gamerules.is_chef_number_valid(page),
            msg=(
                f"Expected Chef {chef_number} validity to be {expected}, "
                f"but got {not expected}. Characters: {[c.name for c in characters]}, "
                f"minion_types: {[m.name for m in page.minion_types]}"
            ),
        )

    def assertChefOutcomes(
        self,
        characters: list[Role],
        expected_by_number: dict[int | None, bool],
        minion_types: list[Role] | None = None,
    ) -> None:
        for chef_number, expected in expected_by_number.items():
            with self.subTest(chef_number=chef_number):
                self.assertChefValid(
                    characters=characters,
                    chef_number=chef_number,
                    expected=expected,
                    minion_types=minion_types,
                )

    def test_no_chef_number_is_always_valid(self):
        self.assertChefValid(
            characters=[
                Role.IMP,
                Role.POISONER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.POISONER],
            chef_number=None,
            expected=True,
        )

    def test_negative_chef_number_is_invalid(self):
        self.assertChefValid(
            characters=[
                Role.IMP,
                Role.POISONER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.POISONER],
            chef_number=-1,
            expected=False,
        )

    def test_known_adjacent_evil_pair_requires_at_least_one(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.POISONER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.POISONER],
            expected_by_number={
                0: False,
                1: True,
                2: False,
            },
        )

    def test_known_evil_pair_wraps_around_table(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.POISONER,
            ],
            minion_types=[Role.POISONER],
            expected_by_number={
                0: False,
                1: True,
                2: False,
            },
        )

    def test_known_evil_players_not_adjacent_can_have_chef_zero(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_GOOD,
                Role.POISONER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.POISONER],
            expected_by_number={
                0: True,
                1: False,
            },
        )

    def test_known_spy_next_to_demon_can_make_zero_or_one_possible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.SPY,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.SPY],
            expected_by_number={
                0: True,
                1: True,
                2: False,
            },
        )

    def test_unknown_minion_next_to_demon_can_be_spy_when_spy_possible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_MINION,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.ANY_OTHER_MINION],
            expected_by_number={
                0: True,
                1: True,
                2: True,
            },
        )

    def test_unknown_minion_next_to_demon_is_definitely_chef_evil_when_spy_impossible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_MINION,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.BARON],
            expected_by_number={
                0: False,
                1: True,
                2: True,
            },
        )

    def test_unknown_evil_next_to_demon_can_be_spy_when_spy_possible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.ANY_OTHER_MINION],
            expected_by_number={
                0: True,
                1: True,
                2: True,
            },
        )

    def test_unknown_evil_next_to_demon_is_definitely_chef_evil_when_spy_impossible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.BARON],
            expected_by_number={
                0: False,
                1: True,
                2: True,
            },
        )

    def test_unknown_minion_cannot_be_spy_when_spy_is_already_elsewhere(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_MINION,
                Role.SPY,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.SPY, Role.ANY_OTHER_MINION],
            expected_by_number={
                0: False,
                1: True,
                2: True,
            },
        )

    def test_good_unknown_can_be_recluse_when_baron_is_possible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.ANY_OTHER_MINION],
            expected_by_number={
                0: True,
                1: True,
                2: False,
            },
        )

    def test_good_unknown_cannot_be_recluse_when_no_outsider_slots_available(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_GOOD,
                Role.DRUNK,
                Role.ANY_OTHER,
                Role.SAINT,
            ],
            minion_types=[Role.BARON],
            expected_by_number={
                0: True,
                1: False,
            },
        )

    def test_known_recluse_next_to_evil_can_make_zero_or_one_possible(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.RECLUSE,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.BARON],
            expected_by_number={
                0: True,
                1: True,
                2: False,
            },
        )

    def test_only_one_unknown_recluse_can_exist(self):
        self.assertChefOutcomes(
            characters=[
                Role.IMP,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.POISONER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.BARON, Role.POISONER],
            expected_by_number={
                0: True,
                1: True,
                2: False,
            },
        )

    def test_all_unknowns_are_limited_by_global_evil_count(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
            ],
            minion_types=[Role.ANY_OTHER_MINION],
            expected_by_number={
                0: True,
                1: True,
                2: True,
                3: False,
            },
        )

    def test_all_good_players_cannot_make_chef_pair_without_recluse(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.POISONER],
            expected_by_number={
                0: True,
                1: False,
            },
        )

    def test_evil_count_limits_evil_contributions_to_chef_number(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER,
                Role.NON_DEMON,
                Role.ANY_OTHER,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.SPY,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
            ],
            minion_types=[Role.SPY, Role.ANY_OTHER_MINION],
            expected_by_number={
                3: False
            }
        )

    def test_all_unknown_evils_next_to_evil_increases_minimum_number(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.SCARLET_WOMAN],
            expected_by_number={
                0: False,
                1: True
            }
        )

    def test_all_unknown_evils_make_line_with_known_evil_increases_minimum_number(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
                Role.ANY_OTHER_GOOD,
            ],
            minion_types=[Role.SCARLET_WOMAN, Role.POISONER, Role.BARON],
            expected_by_number={
                0: False,
                1: False,
                2: True
            }
        )

    def test_evil_outside_run_still_counts_towards_max(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER_TOWNSFOLK,
                Role.IMP,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
            ],
            minion_types=[Role.ANY_OTHER_MINION],
            expected_by_number={
                0: True,
                1: True,
                2: False
            }
        )

    def test_any_other_not_recluse_when_outsider_count_elsewhere(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER_TOWNSFOLK,
                Role.POISONER,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER,
                Role.ANY_OTHER,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_OUTSIDER,
            ],
            minion_types=[Role.POISONER],
            expected_by_number={
                0: True,
                1: False,
            }
        )

    def test_two_seperate_runs_of_evils(self):
        self.assertChefOutcomes(
            characters=[
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.SAINT,
                Role.BUTLER,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_EVIL,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
                Role.ANY_OTHER_TOWNSFOLK,
            ],
            minion_types=[Role.POISONER, Role.BARON, Role.SCARLET_WOMAN],
            expected_by_number={
                0: False,
                1: False,
                2: True,
                3: False
            }
        )


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

        page = GrimoirePage(5)
        page.characters[0] = Role.IMP
        page.characters[2] = Role.ANY_OTHER_TOWNSFOLK
        page.characters[4] = Role.ANY_OTHER_TOWNSFOLK
        page.dead[0] = True
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected an unknown character being executed with all evils dead can't be the Imp.")

    def test_can_imp_starpass(self):
        imp = 3
        page = GrimoirePage(10)
        result = gamerules.can_imp_starpass(page, imp)
        self.assertTrue(result, "Expected blank page to be true.")

        scarlet_woman = 0
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        page.characters[imp] = Role.IMP
        result = gamerules.can_imp_starpass(page, imp)
        self.assertTrue(result, "Expected page with known Imp and Scarlet Woman to be true.")

        page.characters[imp] = Role.NON_DEMON
        result = gamerules.can_imp_starpass(page, imp)
        self.assertFalse(result, "Expected executing a non-demon to be false.")

        page = GrimoirePage(10)
        page.characters[0] = Role.ANY_OTHER_MINION
        page.characters[1] = Role.ANY_OTHER_MINION
        page.dead[0] = True
        page.dead[1] = True
        result = gamerules.can_imp_starpass(page, imp)
        self.assertFalse(result, "Expected a page with all minions dead to be false.")

        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[0] = Role.IMP
        page.characters[1] = Role.IMP
        page.characters[3] = Role.IMP
        result = gamerules.can_imp_starpass(page, imp)
        self.assertFalse(result, "Expected a page with no minion candidates to be false.")

        page = GrimoirePage(5)
        page.characters[0] = Role.IMP
        page.characters[2] = Role.ANY_OTHER_TOWNSFOLK
        page.characters[4] = Role.ANY_OTHER_TOWNSFOLK
        page.dead[0] = True
        result = gamerules.can_imp_starpass(page, imp)
        self.assertFalse(result, "Expected an unknown character with all evils dead can't be the Imp who starpassed.")

class TestCanMinionBecomeDemon(unittest.TestCase):
    def test_starpass(self):
        minion = 0
        imp = 3
        # 1 minion becoming demon when there was a starpass is okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.BARON
        prev.characters[imp] = Role.IMP
        curr.characters[minion] = Role.IMP
        curr.dead[imp] = True
        curr.star_passed = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertTrue(result, "Expected minion able to become demon when there was a starpass.")

        # Minion becoming demon not in "after imp" phase is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.BARON
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.dead[imp] = True
        curr.star_passed = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected minion not able to become demon when not in after imp phase.")

        # Minion becomes demon without demon dying is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.BARON
        curr.night_order_position = NightOrderPosition.AFTER_IMP
        curr.characters[minion] = Role.IMP
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected minion not able to become demon when Imp did not starpass.")

    def test_execution(self):
        minion = 0
        imp = 3
        # Scarlet Woman becoming demon after execution
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.SCARLET_WOMAN
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.executee = imp
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertTrue(result, "Expected Scarlet Woman able to become demon after imp is executed.")

        # Unknown minion becoming demon after execution
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.ANY_OTHER_MINION
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.executee = imp
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertTrue(result, "Expected unknown minion able to become demon after imp is executed.")

        # Unknown minion becoming demon if Scarlet Woman is not in minion type is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[minion] = Role.IMP
        curr.dead[imp] = True
        curr.executee = imp
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected unknown minion not able to become Imp if Scarlet Woman is not a minion type.")

        # non-Scarlet Woman minion becomes demon after execution
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.BARON
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.executee = imp
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected minion not able to become demon after imp executed.")

        # non-Scarlet Woman minion becomes demon after execution if Scarlet Woman alive is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        scarlet_woman = 1
        prev.characters[minion] = Role.BARON
        prev.characters[scarlet_woman] = Role.SCARLET_WOMAN
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.executee = imp
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected minion not able to become demon if Scarlet Woman is alive after imp executed.")

    def test_slayer_shot(self):
        minion = 0
        imp = 3

        # Scarlet Woman becoming demon after slayer shot
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.SCARLET_WOMAN
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.slayer_shot[imp] = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertTrue(result, "Expected Scarlet Woman able to become demon after Imp is slayer shot.")

        # Scarlet Woman becoming demon after slayer shot someone else is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.SCARLET_WOMAN
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.slayer_shot[4] = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected not able to become demon after non-demon is slayer shot.")

        # Unknown minion becoming demon after slayer shot
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.ANY_OTHER_MINION
        prev.minion_types[0] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.slayer_shot[imp] = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertTrue(result, "Expected unknown minion able to become demon after imp is slayer shot.")

        # Unknown minion becoming demon if Scarlet Woman is not in minion type is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.dead[imp] = True
        curr.slayer_shot[imp] = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected unknown minion not able to become Imp if Scarlet Woman is not a minion type.")

        # non-Scarlet Woman minion becomes demon after slayer shot
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = Role.BARON
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.slayer_shot[imp] = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected non-Scarlet Woman minion not able to become demon after imp slayer shot.")

        # non-Scarlet Woman minion becomes demon after slayer shot if Scarlet Woman alive is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        scarlet_woman = 1
        prev.characters[minion] = Role.BARON
        prev.characters[scarlet_woman] = Role.SCARLET_WOMAN
        prev.characters[imp] = Role.IMP
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[minion] = Role.IMP
        curr.minion_types[0] = Role.SCARLET_WOMAN
        curr.dead[imp] = True
        curr.slayer_shot[imp] = True
        result = gamerules.can_minion_become_demon(prev, curr, minion)
        self.assertFalse(result, "Expected minion not able to become demon if Scarlet Woman is alive after imp slayer shot.")

class TestCanNonDemonBecomePotentialDemon(unittest.TestCase):
    def test_starpass(self):
        non_demon = 0
        imp = 3
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_IMP
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.star_passed = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertTrue(result, "Expected non demon able to become any other role after starpass.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_IMP
        curr.characters[non_demon] = Role.ANY_OTHER_EVIL
        curr.star_passed = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertTrue(result, "Expected minion able to become any other evil role after starpass.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_IMP
        curr.characters[non_demon] = Role.ANY_OTHER
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected non demon not able to become any other role if no starpass.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_IMP
        curr.characters[non_demon] = Role.ANY_OTHER_EVIL
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected minion not able to become any other evil role if no starpass.")
        
        minion = 1
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.characters[minion] = Role.ANY_OTHER_MINION
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_IMP
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.characters[minion] = Role.IMP
        curr.star_passed = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected non demon not able to become potential demon if a minion caught the pass.")
        
    def test_execution(self):
        non_demon = 0
        imp = 3
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.executee = imp
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertTrue(result, "Expected non demon able to become any other role after executed Imp.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[non_demon] = Role.ANY_OTHER_EVIL
        curr.executee = imp
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertTrue(result, "Expected minion able to become any other evil role after executed Imp.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.executee = 5
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected non demon not able to become any other role if executed different player.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[non_demon] = Role.ANY_OTHER_EVIL
        curr.executee = 5
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected minion not able to become any other evil role if executed different player.")
        
        minion = 1
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.characters[minion] = Role.SCARLET_WOMAN
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_EXECUTION
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.characters[minion] = Role.IMP
        curr.executee = imp
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected non demon not able to become potential demon if a Scarlet Woman caught the pass.")
        
    def test_slayer_shot(self):
        non_demon = 0
        imp = 3
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.slayer_shot[imp] = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertTrue(result, "Expected non demon able to become any other role after Slayer shot Imp.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[non_demon] = Role.ANY_OTHER_EVIL
        curr.slayer_shot[imp] = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertTrue(result, "Expected minion able to become any other evil role after Slayer shot Imp.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.slayer_shot[5] = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected non demon not able to become any other role if Slayer shot different player.")
        
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.ANY_OTHER_MINION
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[non_demon] = Role.ANY_OTHER_EVIL
        curr.slayer_shot[5] = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected minion not able to become any other evil role if Slayer shot different player.")
        
        minion = 1
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[non_demon] = Role.NON_DEMON
        prev.characters[imp] = Role.IMP
        prev.characters[minion] = Role.ANY_OTHER_MINION
        prev.dead[imp] = True
        curr.night_order_position = NightOrderPosition.AFTER_SLAYER
        curr.characters[non_demon] = Role.ANY_OTHER
        curr.characters[minion] = Role.IMP
        curr.slayer_shot[imp] = True
        result = gamerules.can_non_demon_become_potential_demon(prev, curr, non_demon)
        self.assertFalse(result, "Expected non demon not able to become potential demon if a Scarlet Woman caught the pass.")
        
if __name__ == '__main__':
    _ = unittest.main()