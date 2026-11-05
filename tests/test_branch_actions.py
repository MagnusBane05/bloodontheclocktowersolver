import random
from typing import NamedTuple
import unittest

from tqdm import tqdm

from grimoire import Grimoire, NightOrderPosition, Role, gamerules, validators
from grimoire import branch_actions
from grimoire.role import MINIONS, OUTSIDERS, TOWNSFOLK
from grimoire.add_info_to_grims import _try_branch  # pyright: ignore[reportPrivateUsage]

def _expected_character_result(
    grim: Grimoire,
    role: Role,
    player: int,
    night: int,
    order: NightOrderPosition
) -> tuple[bool, Grimoire]:
    candidate = grim.clone()
    try:
        _ = candidate.apply_character(role, player, night, order)
        candidate.make_deductions()
    except (RuntimeError, ValueError):
        return False, candidate
    return validators.is_grim_valid(candidate)[0], candidate

def _build_random_valid_grim(num_players: int, rng: random.Random) -> Grimoire:
    grim = Grimoire(num_players)
    page = grim.get_first_page()

    characters: list[Role] = []
    # pick demon
    possible_demons = [Role.IMP, Role.ANY_OTHER_EVIL, Role.ANY_OTHER]
    characters.append(rng.choice(possible_demons))
    # pick minions
    possible_minions = MINIONS + [Role.ANY_OTHER_MINION, Role.NON_DEMON, Role.ANY_OTHER_EVIL, Role.ANY_OTHER]
    minions = rng.sample(possible_minions, gamerules.ROLE_BREAKDOWNS[num_players]['minions'])
    characters.extend(minions)
    for minion in minions:
        if minion in MINIONS:
            page.add_minion_type(minion)
    # pick outsiders
    num_outsiders = gamerules.get_outsider_count(num_players, Role.BARON in characters)
    possible_outsiders = OUTSIDERS + [Role.ANY_OTHER_OUTSIDER, Role.NON_DEMON, Role.ANY_OTHER_GOOD, Role.ANY_OTHER]
    characters.extend(rng.sample(possible_outsiders, num_outsiders))
    # pick townsfolk
    possible_townsfolk = TOWNSFOLK + [Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON, Role.ANY_OTHER_GOOD, Role.ANY_OTHER]
    characters.extend(rng.sample(possible_townsfolk, num_players - len(characters)))
    assert len(characters) == num_players

    page.characters = rng.sample(characters, num_players)  # shuffle characters
    grim.make_deductions()

    if Role.CHEF in characters:
        options: list[Grimoire] = []
        for chef_number in range(0, 4):
            candidate = _try_branch(grim, branch_actions.chef_number_action(chef_number))
            if candidate is not None:
                options.append(candidate)
        grim = rng.choice(options)
        page = grim.get_first_page()

    if Role.LIBRARIAN in characters:
        options = [grim]
        candidate = _try_branch(grim, branch_actions.no_outsiders_action())
        if candidate is not None:
            options.append(candidate)
        grim = rng.choice(options)
        page = grim.get_first_page()
            
    valid, reason = validators.is_grim_valid(grim)
    assert valid, f"Randomly generated grim is not valid: {reason}\n{grim}"
    return grim

class Scenario(NamedTuple):
    grim: Grimoire
    role: Role
    player: int

def print_rejects(rejects: list[Scenario], num_to_print: int, rng: random.Random):
    rejects_to_print = rng.sample(rejects, min(num_to_print, len(rejects)))
    for reject in rejects_to_print:
        print("Failed scenario:")
        print(reject.grim)
        print(f"Chef number: {reject.grim.pages[0].chef_number}")
        print(f"No outsiders? {reject.grim.pages[0].no_outsiders}")
        print(f"Role: {reject.role.name}")
        print(f"Player: {reject.player}")

class TestCharacterActionParityWithValidation(unittest.TestCase):
    def assert_character_action_matches_validation(
        self,
        grim: Grimoire,
        role: Role,
        player: int,
        night: int = 1,
        order: NightOrderPosition = NightOrderPosition.AFTER_IMP,
    ):
        expected_result, expected_grim = _expected_character_result(grim, role, player, night, order)
        actual_grim = grim.clone()
        action = branch_actions.character_action(role, player, night, order)
        actual_result = action(actual_grim)

        self.assertEqual(
            actual_result,
            expected_result,
            msg=(
                f"character_action returned {actual_result} but validation says {expected_result} "
                f"for role={role.name}, player={player}, num_players={grim.num_players}"
            ),
        )
        if actual_result:
            self.assertEqual(
                actual_grim,
                expected_grim,
                msg=(
                    f"character_action grim doesn't match expected grim "
                    f"for role={role.name}, player={player}, num_players={grim.num_players}"
                )
            )

    @staticmethod
    def setup_scenario(num_players: int, rng: random.Random) -> Scenario:
        grim = _build_random_valid_grim(num_players, rng)
        role = rng.choice([r for r in Role])
        player = rng.randrange(num_players)
        return Scenario(grim, role, player)


    def test_character_action_matches_validation_for_seeded_random_setups(self):
        rng = random.Random(2412341)
        n = 10000

        for num_players in (5, 8, 9, 10, 13):
            for case_idx in tqdm(range(n)):
                with self.subTest(num_players=num_players, case=case_idx):
                    grim, role, player = self.setup_scenario(num_players, rng)
                    self.assert_character_action_matches_validation(grim, role, player)

    def role_assignment_matches_validation(
        self, 
        grim: Grimoire, 
        role: Role, 
        player: int,
        night: int = 1,
        order: NightOrderPosition = NightOrderPosition.AFTER_IMP
    ) -> bool | None:
        expected_result, expected_grim = _expected_character_result(grim, role, player, night, order) 
        if expected_result:
            page = expected_grim.get_page(night, order)
            assert page
            actual_result = validators.ROLE_ASSIGNMENT_VALIDATOR.validate(page)
            return expected_result == actual_result
        return None

    @staticmethod
    def apply_match(total: int, matches: int, rejects: list[Scenario], match: bool | None, scenario: Scenario) -> tuple[int, int, list[Scenario]]:
        new_rejects = rejects[:]
        if not match:
            new_rejects.append(scenario)
        return total + 1, matches + (1 if match else 0), new_rejects

    def test_role_assignment_gap(self):
        rng = random.Random(2342)
        n = 1000
        total = 0
        matches = 0
        rejects: list[Scenario] = []
        for num_players in (5, 8, 9, 10, 13):
            player_count_total = 0
            player_count_matches = 0
            for case_idx in tqdm(range(n)):
                with self.subTest(num_players=num_players, case=case_idx):
                    scenario = self.setup_scenario(num_players, rng)
                    match = self.role_assignment_matches_validation(scenario.grim, scenario.role, scenario.player)
                    if match is not None:
                        player_count_total, player_count_matches, rejects = self.apply_match(player_count_total, player_count_matches, rejects, match, scenario)
            print(f"Player count: {num_players}, total compared: {player_count_total}, matches: {player_count_matches}")
            total += player_count_total
            matches += player_count_matches
        num_rejects_to_print = 3
        print_rejects(rejects, num_rejects_to_print, rng)
        self.assertLess(total - matches, 0.01 * total)


def _unknown_with_evils_at(num_players: int, evils: list[int]) -> list[Role]:
    return [Role.ANY_OTHER_EVIL if i in evils else Role.ANY_OTHER for i in range(num_players)]

class TestChefNumberAction(unittest.TestCase):
    def assertChefAction(
        self,
        expected: bool,
        number: int,
        characters: list[Role] | None = None,
        minion_types: list[Role] | None = None,
        num_players: int = 5,
    ) -> None:
        grim = Grimoire(num_players)
        page = grim.get_first_page()
        if characters is not None:
            page.characters = characters
        if minion_types is not None:
            page.minion_types = minion_types
        self.assertEqual(expected, branch_actions.chef_number_action(number)(grim))

    def test_chef_0(self):
        with self.subTest("Imp and Scarlet Woman not adjacent"):
            self.assertChefAction(True, 0, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SCARLET_WOMAN], [Role.SCARLET_WOMAN])
        with self.subTest("evil and Recluse pair"):
            self.assertChefAction(True, 0, [Role.CHEF, Role.RECLUSE, Role.IMP, Role.DRUNK, Role.BARON], [Role.BARON])
        with self.subTest("Imp and Spy pair"):
            self.assertChefAction(True, 0, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SPY, Role.LIBRARIAN], [Role.SPY])
        with self.subTest("2 non-Spy evils together should be Chef 1"):
            self.assertChefAction(False, 0, [Role.CHEF, Role.IMP, Role.SCARLET_WOMAN, Role.WASHERWOMAN, Role.LIBRARIAN], [Role.SCARLET_WOMAN])

    def test_chef_0_with_unknown_evils(self):
        adjacent_evils = _unknown_with_evils_at(5, [1, 2])
        with self.subTest("an unknown evil could be a Spy"):
            self.assertChefAction(True, 0, adjacent_evils)
        with self.subTest("not possible if no Spy"):
            self.assertChefAction(False, 0, adjacent_evils, [Role.SCARLET_WOMAN])
        with self.subTest("not possible if the Spy is elsewhere"):
            characters = _unknown_with_evils_at(13, [1, 2])
            characters[5] = Role.SPY
            self.assertChefAction(False, 0, characters, [Role.SPY, Role.ANY_OTHER_MINION, Role.ANY_OTHER_MINION], 13)
        with self.subTest("only 1 possible evil pair can include a Spy"):
            self.assertChefAction(False, 0, _unknown_with_evils_at(13, [1, 2, 5, 6]), num_players=13)

    def test_chef_1(self):
        with self.subTest("2 evils together"):
            self.assertChefAction(True, 1, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SCARLET_WOMAN, Role.LIBRARIAN], [Role.SCARLET_WOMAN])
        with self.subTest("evil and Recluse pair"):
            self.assertChefAction(True, 1, [Role.CHEF, Role.RECLUSE, Role.IMP, Role.DRUNK, Role.BARON], [Role.BARON])
        with self.subTest("evil and Spy"):
            self.assertChefAction(True, 1, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.SPY, Role.LIBRARIAN], [Role.SPY])
        with self.subTest("evil, Recluse, evil"):
            self.assertChefAction(True, 1, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.RECLUSE, Role.SCARLET_WOMAN, Role.LIBRARIAN], [Role.SCARLET_WOMAN], 6)
        with self.subTest("no adjacent evils and no Recluse should be Chef 0"):
            self.assertChefAction(False, 1, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SCARLET_WOMAN], [Role.SCARLET_WOMAN])

    def test_chef_2_and_up(self):
        with self.subTest("evil, Recluse, Spy"):
            self.assertChefAction(True, 2, [Role.CHEF, Role.WASHERWOMAN, Role.IMP, Role.RECLUSE, Role.SPY, Role.LIBRARIAN], [Role.SPY], 6)
        with self.subTest("two separate groups of evils"):
            self.assertChefAction(
                True,
                2,
                [
                    Role.CHEF, Role.IMP, Role.POISONER, Role.WASHERWOMAN, Role.LIBRARIAN,
                    Role.SCARLET_WOMAN, Role.BARON, Role.SOLDIER, Role.SLAYER, Role.MAYOR,
                    Role.BUTLER, Role.SAINT, Role.UNDERTAKER,
                ],
                [Role.POISONER, Role.SCARLET_WOMAN, Role.BARON],
                13,
            )
        with self.subTest("an unknown world can be up to the maximum"):
            self.assertChefAction(True, 2)
        with self.subTest("3 is impossible in 5 players"):
            self.assertChefAction(False, 3)
        unknown_goods = [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        with self.subTest("an unknown good could be the Recluse, making 2 the max"):
            self.assertChefAction(True, 2, unknown_goods)
        with self.subTest("an unknown good that can't be the Recluse can't add to the number"):
            self.assertChefAction(False, 2, unknown_goods, [Role.SCARLET_WOMAN])

class TestNoOutsidersAction(unittest.TestCase):
    def test_without_the_info_the_flag_stays_off(self):
        grim = Grimoire()
        self.assertTrue(validators.is_grim_valid(grim)[0])
        self.assertFalse(grim.get_first_page().no_outsiders)

    def test_sets_the_flag(self):
        grim = Grimoire()
        self.assertTrue(branch_actions.no_outsiders_action()(grim))
        self.assertTrue(grim.get_first_page().no_outsiders)

    def test_baron_without_the_info_is_valid(self):
        grim = Grimoire()
        self.assertTrue(grim.get_first_page().add_minion_type(Role.BARON))
        self.assertTrue(validators.is_grim_valid(grim)[0])
        self.assertFalse(grim.get_first_page().no_outsiders)

    def test_baron_rules_out_the_info(self):
        grim = Grimoire()
        self.assertTrue(grim.get_first_page().add_minion_type(Role.BARON))
        self.assertFalse(branch_actions.no_outsiders_action()(grim))
