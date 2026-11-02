
import time
import unittest

from analyze.simulator import simulate_info
from grimoire import Grimoire
from grimoire import GrimoireManager
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




if __name__ == '__main__':
    _ = unittest.main()