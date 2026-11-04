
import time
import unittest
from unittest import mock

from analyze.simulator import simulate_info
from bench.scenarios import load_scenarios
from grimoire import Grimoire
from grimoire import GrimoireManager
from grimoire.add_info_to_grims import add_death_info_to_grims, add_info_to_grims
from grimoire.nightOrderPosition import NightOrderPosition
from grimoire.errors import TrueGrimLostError
from grimoire.grimoire_manager import StepRecord
from grimoire.role import Role


class TestGrimoire(unittest.TestCase):
    def test_get_player_perspective(self):
        manager = GrimoireManager({"players": 5})
        true_grim = Grimoire()
        true_grim.pages[0].characters = [Role.IMP, Role.SCARLET_WOMAN, Role.FORTUNE_TELLER, Role.SOLDIER, Role.CHEF]
        manager.true_grim = true_grim

        test_grim = Grimoire()

        # test that an unknown grim will get filled in with the player's role        
        test_grim.pages[0].characters = [Role.ANY_OTHER]*5
        manager.grims = [test_grim]

        subjective_manager = manager.get_player_perspective(2)
        # self.assertEqual(subjective_manager.grims[0].pages[0].characters[2], Role.FORTUNE_TELLER)

        # drunk player has seen role and drunk as valid grims
        true_grim.pages[0].characters = [Role.IMP, Role.BARON, Role.DRUNK, Role.RECLUSE, Role.CHEF]
        true_grim.pages[0].drunk_token = Role.FORTUNE_TELLER
        test_grim.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER, Role.DRUNK, Role.ANY_OTHER, Role.ANY_OTHER]
        test_grim2 = Grimoire()
        test_grim2.pages[0].characters = [Role.ANY_OTHER, Role.ANY_OTHER, Role.FORTUNE_TELLER, Role.ANY_OTHER, Role.ANY_OTHER]
        manager.grims = [test_grim, test_grim2]
        subjective_manager = manager.get_player_perspective(2)
        self.assertEqual(len(subjective_manager.grims), 2)
        self.assertEqual(subjective_manager.grims[0].pages[0].characters[2], Role.DRUNK)
        self.assertEqual(subjective_manager.grims[1].pages[0].characters[2], Role.FORTUNE_TELLER)

class TestStepObserver(unittest.TestCase):
    GAME = {"players": 5}
    # 5 player game where the final remove_subsumed_grims step removes grims (131 -> 127)
    SEED = 201

    def test_records_every_step(self):
        (info_list, death_info), true_grim = simulate_info(1, self.GAME, self.SEED)[0]
        records: list[StepRecord] = []
        manager = GrimoireManager(self.GAME, true_grim, on_step=records.append)

        start = time.perf_counter()
        manager.add_full_game(info_list, death_info, len(true_grim.get_unique_nights()))
        total = time.perf_counter() - start

        self.assertGreater(len(records), 1, "Expected a record for each info step.")
        self.assertEqual(records[-1].stage, "final remove_subsumed_grims", "Expected the last record to be the final cleanup step.")
        self.assertLess(records[-1].grims_after, records[-1].grims_before, "Expected the final step to report the grims removed by subsumption.")
        for previous, current in zip(records, records[1:]):
            self.assertEqual(current.grims_before, previous.grims_after, f"Expected no unreported steps between '{previous.stage}' and '{current.stage}'.")
        self.assertEqual(records[-1].grims_after, len(manager.grims), "Expected the last record to match the final grim count.")
        self.assertTrue(all(r.seconds >= 0 for r in records), "Expected step times to be non-negative.")
        self.assertLessEqual(sum(r.seconds for r in records), total, "Expected step times to add up to no more than the game's total time.")

    def test_records_failing_step_before_raising(self):
        (info_list, death_info), true_grim = simulate_info(1, self.GAME, self.SEED)[0]
        _, other_true_grim = simulate_info(1, self.GAME, self.SEED + 1)[0]
        records: list[StepRecord] = []
        manager = GrimoireManager(self.GAME, other_true_grim, on_step=records.append)

        with self.assertRaises(TrueGrimLostError) as context:
            manager.add_full_game(info_list, death_info, len(true_grim.get_unique_nights()))

        self.assertGreater(len(records), 0, "Expected the failing step to be recorded.")
        self.assertIn(records[-1].stage, str(context.exception), "Expected the last record to be the step that lost the true grim.")

    def test_no_observer(self):
        (info_list, death_info), true_grim = simulate_info(1, self.GAME, self.SEED)[0]
        manager = GrimoireManager(self.GAME, true_grim)
        manager.add_full_game(info_list, death_info, len(true_grim.get_unique_nights()))
        self.assertTrue(manager.do_grims_contain_true_grim(), "Expected the game to solve normally without an observer.")




def _poisoned(*night_and_player: tuple[int, int]) -> Grimoire:
    world = Grimoire()
    world.pages[0].minion_types = [Role.POISONER]
    for night, player in night_and_player:
        page = world.get_page(night, NightOrderPosition.AFTER_IMP) or world.add_page(night, NightOrderPosition.AFTER_IMP)
        page.poisoned[player] = True
    return world

class TestRemoveUnneededPoison(unittest.TestCase):
    def _kept(self, *worlds: Grimoire) -> list[Grimoire]:
        return GrimoireManager.remove_unneeded_poison(list(worlds))

    def test_drops_world_with_extra_poison(self):
        healthy, poisoned = _poisoned(), _poisoned((1, 0))
        self.assertEqual([healthy], self._kept(poisoned, healthy))
        self.assertEqual([healthy], self._kept(healthy, poisoned))

    def test_drops_every_world_above_the_least_poison_in_a_chain(self):
        least = _poisoned((1, 0))
        self.assertEqual([least], self._kept(_poisoned((1, 0), (2, 1), (3, 1)), least, _poisoned((1, 0), (2, 1))))

    def test_keeps_worlds_that_each_have_poison_the_other_lacks(self):
        first, second = _poisoned((1, 0)), _poisoned((1, 1))
        self.assertCountEqual([first, second], self._kept(first, second))

    def test_drops_a_world_covered_by_either_of_two_others(self):
        first, second = _poisoned((1, 0)), _poisoned((2, 1))
        self.assertCountEqual([first, second], self._kept(first, second, _poisoned((1, 0), (2, 1))))

    def test_keeps_same_player_poisoned_on_different_nights(self):
        night2, night3 = _poisoned((2, 0)), _poisoned((3, 0))
        self.assertCountEqual([night2, night3], self._kept(night2, night3))

    def test_keeps_world_with_different_roles(self):
        poisoned = _poisoned((1, 0))
        poisoned.pages[0].characters[1] = Role.MONK
        healthy = _poisoned()
        self.assertCountEqual([poisoned, healthy], self._kept(poisoned, healthy))

    def test_drops_world_whose_page_only_holds_poison(self):
        healthy = _poisoned()
        self.assertEqual([healthy], self._kept(healthy, _poisoned((3, 0))))

    def test_keeps_worlds_with_equal_poison(self):
        # only strictly less poison makes a world unneeded
        world = _poisoned((1, 0))
        empty_page = world.clone()
        _ = empty_page.add_page(3, NightOrderPosition.AFTER_IMP)
        self.assertCountEqual([world, empty_page], self._kept(world, empty_page))

    def test_empty_and_single(self):
        world = _poisoned((1, 0))
        self.assertEqual([], self._kept())
        self.assertEqual([world], self._kept(world))

    def test_leaves_the_input_list_alone(self):
        worlds = [_poisoned((1, 0)), _poisoned()]
        _ = GrimoireManager.remove_unneeded_poison(worlds)
        self.assertEqual(2, len(worlds))

    def test_kept_world_still_matches_a_true_grim_with_the_dropped_poison(self):
        true_grim = _poisoned((1, 0))
        kept = self._kept(true_grim.clone(), _poisoned())
        self.assertTrue(any(true_grim.loose_equals(world) for world in kept))

class TestManagerRemovesUnneededPoison(unittest.TestCase):
    GAME = {"players": 5}

    def test_applied_to_each_step_and_reported(self):
        records: list[StepRecord] = []
        manager = GrimoireManager(self.GAME, on_step=records.append)
        healthy = _poisoned()
        manager._set_grims_checked([healthy, _poisoned((1, 0))], "stage")  # pyright: ignore[reportPrivateUsage]
        self.assertEqual([healthy], manager.grims)
        self.assertEqual(1, records[0].grims_after)

    def test_world_limit_applies_after_removing(self):
        manager = GrimoireManager(self.GAME)
        world = _poisoned()
        too_many = [world] * 250001
        with mock.patch.object(GrimoireManager, "remove_unneeded_poison", return_value=[world]):
            manager._set_grims_checked(too_many, "stage")  # pyright: ignore[reportPrivateUsage]
        self.assertEqual([world], manager.grims)

    def test_true_grim_check_sees_the_remaining_worlds(self):
        manager = GrimoireManager(self.GAME, Grimoire())
        with mock.patch.object(GrimoireManager, "remove_unneeded_poison", return_value=[]):
            with self.assertRaises(TrueGrimLostError):
                manager._set_grims_checked([Grimoire()], "stage")  # pyright: ignore[reportPrivateUsage]

class TestRemovingPoisonFromRealBranches(unittest.TestCase):
    NIGHT = 1
    ORDER = NightOrderPosition.AFTER_IMP

    def _base(self) -> Grimoire:
        # the realistic version of a poisoned and a healthy Washerwoman being the same otherwise:
        # the Washerwoman's target is already the Empath and there's already a Poisoner
        base = Grimoire()
        base.pages[0].minion_types = [Role.POISONER]
        base.pages[0].characters[1] = Role.EMPATH
        return base

    def _is_poisoned(self, world: Grimoire, player: int) -> bool:
        return world.pages[0].poisoned[player]

    def _washerwoman(self) -> list[Grimoire]:
        return add_info_to_grims(
            {"kind": "washerwoman", "washerwoman": 0, "first_player": 1, "second_player": 2, "townsfolk": Role.EMPATH},
            [self._base()],
        )

    def test_poison_is_dropped_when_the_info_is_already_true(self):
        worlds = self._washerwoman()
        self.assertTrue(any(self._is_poisoned(w, 0) for w in worlds), "Expected a poisoned branch before removing.")
        kept = GrimoireManager.remove_unneeded_poison(worlds)
        self.assertFalse(any(self._is_poisoned(w, 0) for w in kept))
        self.assertTrue(any(w.pages[0].characters[0] == Role.WASHERWOMAN for w in kept))

    def test_kept_world_can_still_poison_someone_else_that_night(self):
        # the poisoned Washerwoman couldn't do this, but dropping it adds nothing new: the healthy one always could
        info = {"kind": "investigator", "investigator": 3, "first_player": 4, "second_player": 2, "minion": Role.POISONER}
        def poisoned_investigators(worlds: list[Grimoire]) -> list[Grimoire]:
            return [w for w in add_info_to_grims(info, worlds) if self._is_poisoned(w, 3)]  # pyright: ignore[reportArgumentType]

        worlds = self._washerwoman()
        kept = GrimoireManager.remove_unneeded_poison(worlds)
        from_kept = poisoned_investigators(kept)
        self.assertGreater(len(from_kept), 0)
        self.assertEqual(set(poisoned_investigators(worlds)), set(from_kept))
        self.assertEqual([], poisoned_investigators([w for w in worlds if self._is_poisoned(w, 0)]))

    def test_keeps_poison_when_the_info_is_false(self):
        # the only way the Washerwoman's info can be false here is being poisoned, drunk or evil
        base = self._base()
        base.pages[0].characters[1] = Role.MONK
        base.pages[0].characters[2] = Role.CHEF
        worlds = add_info_to_grims(
            {"kind": "washerwoman", "washerwoman": 0, "first_player": 1, "second_player": 2, "townsfolk": Role.EMPATH},
            [base],
        )
        kept = GrimoireManager.remove_unneeded_poison(worlds)
        self.assertEqual(1, sum(self._is_poisoned(w, 0) for w in kept))
        self.assertEqual(0, sum(w.pages[0].characters[0] == Role.WASHERWOMAN and not self._is_poisoned(w, 0) for w in kept))

    def test_keeps_poison_on_an_executed_saint(self):
        # 6 players have an outsider without needing a Baron, so the single minion can be the Poisoner
        base = Grimoire(6)
        base.pages[0].minion_types = [Role.POISONER]
        base.pages[0].characters[0] = Role.SAINT
        worlds = add_death_info_to_grims({"kind": "execution", "player": 0, "night": 1}, [base])
        self.assertGreater(len(worlds), 0, "Expected a poisoned Saint to be executable.")
        kept = GrimoireManager.remove_unneeded_poison(worlds)
        self.assertEqual(len(worlds), len(kept))
        for world in kept:
            page = world.get_page(1, NightOrderPosition.AFTER_EXECUTION)
            assert page is not None
            self.assertTrue(page.poisoned[0], "Expected every executed Saint to be poisoned.")

class TestRemovingPoisonFromFullGames(unittest.TestCase):
    def test_info_that_only_later_proves_false_keeps_its_poison(self):
        # 5p-0004: the Washerwoman's info looks correct when it arrives, but in the true world neither
        # target registers as the Virgin, which is only revealed by claims and info later in the game
        scenario = load_scenarios(5, limit=5)[4]
        poisoning = (1, NightOrderPosition.AFTER_IMP, 1)
        self.assertIn(poisoning, scenario.true_grim.get_all_poisonings())
        manager = GrimoireManager({"players": 5}, scenario.true_grim)
        manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)
        self.assertTrue(any(
            poisoning in world.get_all_poisonings() and scenario.true_grim.loose_equals(world)
            for world in manager.grims
        ))

    def test_only_worlds_with_unneeded_poison_are_removed(self):
        removed_any = False
        for scenario in load_scenarios(5, limit=100):
            with self.subTest(scenario.id):
                with mock.patch.object(GrimoireManager, "remove_unneeded_poison", side_effect=lambda grims: grims):  # pyright: ignore[reportUnknownLambdaType]
                    everything = GrimoireManager({"players": 5}, scenario.true_grim)
                    everything.add_full_game(scenario.info, scenario.deaths, scenario.nights)
                manager = GrimoireManager({"players": 5}, scenario.true_grim)
                manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)

                self.assertTrue(manager.do_grims_contain_true_grim())
                kept = set(manager.grims)
                poisonings_by_state: dict[object, list[frozenset[object]]] = {}
                for world in manager.grims:
                    poisonings_by_state.setdefault(world.state_without_poison(), []).append(world.get_all_poisonings())
                for world in everything.grims:
                    if world in kept:
                        continue
                    removed_any = True
                    self.assertTrue(
                        any(p <= world.get_all_poisonings() for p in poisonings_by_state.get(world.state_without_poison(), [])),
                        f"Expected a kept world that's the same with no extra poison: {world}",
                    )
                self.assertEqual({w.state_without_poison() for w in everything.grims}, set(poisonings_by_state))
        self.assertTrue(removed_any, "Expected at least one of these games to have unneeded poison.")

if __name__ == '__main__':
    _ = unittest.main()