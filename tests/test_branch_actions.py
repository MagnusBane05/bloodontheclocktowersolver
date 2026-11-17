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
        action = branch_actions.character_action(role, player, night, order)
        actual_grim = _try_branch(grim, action)
        actual_result = actual_grim is not None

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
        # the action only records the number; _finalize is what rejects an impossible one
        result = _try_branch(grim, branch_actions.chef_number_action(number))
        self.assertEqual(expected, result is not None)

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

    def test_known_evil_pair(self):
        characters = [Role.IMP, Role.ANY_OTHER_MINION, Role.MONK, Role.EMPATH, Role.SLAYER]
        with self.subTest("the pair counts once"):
            self.assertChefAction(True, 1, characters)
        with self.subTest("nobody else can add to the number"):
            self.assertChefAction(False, 2, characters)

    def test_recluse_next_to_spy(self):
        with self.subTest("0 needs a non-Spy evil somewhere"):
            self.assertChefAction(False, 0, [Role.RECLUSE, Role.SPY, Role.MONK, Role.MONK, Role.MONK])
        characters = [Role.RECLUSE, Role.SPY, Role.WASHERWOMAN, Role.IMP, Role.LIBRARIAN, Role.SLAYER]
        with self.subTest("neither registers as evil"):
            self.assertChefAction(True, 0, characters, [Role.SPY], 6)
        with self.subTest("both register as evil"):
            self.assertChefAction(True, 1, characters, [Role.SPY], 6)
        with self.subTest("one pair can't count twice"):
            self.assertChefAction(False, 2, characters, [Role.SPY], 6)

    def test_adjacent_unknown_evils_by_minion_type(self):
        adjacent_evils = _unknown_with_evils_at(5, [0, 1])
        adjacent_evils = [Role.ANY_OTHER_GOOD if c == Role.ANY_OTHER else c for c in adjacent_evils]
        with self.subTest("Scarlet Woman: the pair must count"):
            self.assertChefAction(False, 0, adjacent_evils, [Role.SCARLET_WOMAN])
            self.assertChefAction(True, 1, adjacent_evils, [Role.SCARLET_WOMAN])
        with self.subTest("Spy: the pair may count or not, but no Recluse can add a second"):
            self.assertChefAction(True, 0, adjacent_evils, [Role.SPY])
            self.assertChefAction(True, 1, adjacent_evils, [Role.SPY])
            self.assertChefAction(False, 2, adjacent_evils, [Role.SPY])
        with self.subTest("Baron: a neighbour could be the Recluse"):
            self.assertChefAction(True, 2, adjacent_evils, [Role.BARON])

class TestNoOutsidersAction(unittest.TestCase):
    def test_without_the_info_the_flag_stays_off(self):
        grim = Grimoire()
        self.assertTrue(validators.is_grim_valid(grim)[0])
        self.assertFalse(grim.get_first_page().no_outsiders)

    # the action only sets the flag; _finalize is what rejects an impossible one
    def assertNoOutsidersAction(self, expected: bool, grim: Grimoire, msg: str | None = None) -> None:
        result = _try_branch(grim, branch_actions.no_outsiders_action())
        self.assertEqual(expected, result is not None, msg)

    def test_sets_the_flag(self):
        result = _try_branch(Grimoire(), branch_actions.no_outsiders_action())
        assert result is not None
        self.assertTrue(result.get_first_page().no_outsiders)

    def test_baron_without_the_info_is_valid(self):
        grim = Grimoire()
        self.assertTrue(grim.get_first_page().add_minion_type(Role.BARON))
        self.assertTrue(validators.is_grim_valid(grim)[0])
        self.assertFalse(grim.get_first_page().no_outsiders)

    def test_baron_rules_out_the_info(self):
        grim = Grimoire()
        self.assertTrue(grim.get_first_page().add_minion_type(Role.BARON))
        self.assertNoOutsidersAction(False, grim)

    def test_player_count(self):
        self.assertNoOutsidersAction(True, Grimoire(5), "5 players have no outsiders")
        self.assertNoOutsidersAction(True, Grimoire(6), "an unknown player could be the Recluse")
        self.assertNoOutsidersAction(False, Grimoire(9), "9 players have 2 outsiders")

    def test_known_outsiders(self):
        grim = Grimoire(6)
        grim.get_first_page().characters[0] = Role.RECLUSE
        self.assertNoOutsidersAction(True, grim, "the only outsider is a Recluse")

        grim = Grimoire(6)
        grim.get_first_page().characters[0] = Role.SAINT
        self.assertNoOutsidersAction(False, grim, "a known outsider that isn't the Recluse")

class TestPoisonedAction(unittest.TestCase):
    # the action only marks the player; _finalize is what rejects an impossible poisoning
    def assertPoisonedAction(self, expected: bool, grim: Grimoire, msg: str | None = None) -> None:
        action = branch_actions.poisoned_action(0, 1, NightOrderPosition.AFTER_IMP)
        result = _try_branch(grim, action)
        self.assertEqual(expected, result is not None, msg)

    def test_poisoner_can_be_added(self):
        self.assertPoisonedAction(True, Grimoire(5))

    def test_known_poisoner(self):
        grim = Grimoire(5)
        grim.get_first_page().minion_types[0] = Role.POISONER
        self.assertPoisonedAction(True, grim)

    def test_no_room_for_a_poisoner(self):
        grim = Grimoire(5)
        grim.get_first_page().minion_types[0] = Role.BARON
        self.assertPoisonedAction(False, grim)

    def test_another_player_is_already_poisoned(self):
        grim = Grimoire(5)
        grim.get_first_page().apply_poisoned(1)
        self.assertPoisonedAction(False, grim)

    def test_known_poisoner_is_dead(self):
        grim = Grimoire(5)
        page = grim.get_first_page()
        page.minion_types[0] = Role.POISONER
        page.characters[1] = Role.POISONER
        page.dead[1] = True
        self.assertPoisonedAction(False, grim)
