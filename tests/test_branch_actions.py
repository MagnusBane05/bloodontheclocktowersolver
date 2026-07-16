import random
import unittest

from grimoire import Grimoire, NightOrderPosition, Role, gamerules
from grimoire import branch_actions
from grimoire.role import MINIONS, OUTSIDERS, TOWNSFOLK

class TestCharacterActionParityWithValidation(unittest.TestCase):
    def assert_character_action_matches_validation(
        self,
        grim: Grimoire,
        role: Role,
        player: int,
        night: int = 1,
        order: NightOrderPosition = NightOrderPosition.AFTER_IMP,
    ):
        before = grim.clone()
        expected = before.clone()
        expected_result = False

        if expected.can_be_character(role, player, night, order):
            expected.apply_character(role, player, night, order)
            expected.make_deductions()
            expected_result = gamerules.is_grim_valid(expected)
            if not expected_result:
                expected = before.clone()

        actual = before.clone()
        action = branch_actions.character_action(role, player, night, order)
        actual_result = action(actual)

        self.assertEqual(
            actual_result,
            expected_result,
            msg=(
                f"character_action returned {actual_result} but validation says {expected_result} "
                f"for role={role.name}, player={player}, num_players={grim.num_players}"
            ),
        )

    def character_action_matches_validation_for_seeded_random_setups(self):
        rng = random.Random(2412341)
        n = 1000

        for num_players in (5, 8, 9, 10, 13):
            for case_idx in range(n):
                with self.subTest(num_players=num_players, case=case_idx):
                    grim = self._build_random_valid_grim(num_players, rng)
                    role = rng.choice([r for r in Role])
                    player = rng.randrange(num_players)
                    self.assert_character_action_matches_validation(grim, role, player)

    def _build_random_valid_grim(self, num_players: int, rng: random.Random) -> Grimoire:
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
            possible_chef_numbers: list[int] = []
            for chef_number in range(0, 4):
                page.chef_number = chef_number
                if gamerules.is_chef_number_valid(page):
                    possible_chef_numbers.append(chef_number)
            page.chef_number = rng.choice(possible_chef_numbers)
            page.make_deductions()

        if Role.LIBRARIAN in characters:
            page.no_outsiders = True
            if gamerules.is_outsider_count_valid(page, num_players):
                page.no_outsiders = rng.choice([True, False])
            else:
                page.no_outsiders = False
            page.make_deductions()
                
        assert gamerules.is_grim_valid(grim), "Randomly generated grim is not valid"
        return grim
