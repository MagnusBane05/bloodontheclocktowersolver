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
