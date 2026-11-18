from typing import get_args, get_type_hints
import unittest
from unittest import mock

from bench.scenarios import load_scenarios
from grimoire import GrimoireManager
from grimoire import add_info_to_grims as add_info_module
from grimoire.add_info_to_grims import MAX_FINALIZE_ROUNDS, _finalize, _is_virgin_spent, _try_branch, _try_intermediate_branch, add_death_info_to_grims, add_info_to_grims, find_finalize_problem  # pyright: ignore[reportPrivateUsage]
from grimoire.branch_actions import character_action
from grimoire.errors import FinalizeDidNotSettleError
from grimoire.grimoire import Grimoire, GrimoireKey
from grimoire.grimoire_page import GrimoirePage
from grimoire.info import DemonKillInfo, ExecutionInfo, Info, SlayerKillInfo, FortuneTellerInfo, VirginInfo
from grimoire.nightOrderPosition import NightOrderPosition
from grimoire.role import EVIL_ROLES_SET, Role


def get_required_page(grim: Grimoire, night: int, order: NightOrderPosition):
    page = grim.get_page(night, order)
    assert page is not None
    return page


class TestAddDeathInfoToGrims(unittest.TestCase):
    def test_non_demon_night_death(self):
        base = Grimoire()
        target = 3

        info: DemonKillInfo = {
            "kind": "demon",
            "night": 2,
            "player": target
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                )).dead[target]
                and page.characters[target] == Role.NON_DEMON
                for grim in results
            ),
            "Expected a result where the player is dead and a non-demon role."
        )
        # The input grim should not be mutated.
        self.assertEqual(len(base.pages), 1)
        self.assertFalse(base.get_first_page().dead[target])

        base_page = base.add_page(2, NightOrderPosition.AFTER_IMP)
        base_page.characters[target] = Role.IMP

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertFalse(
            any(
                (page := get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                )).dead[target]
                and page.characters[target] == Role.NON_DEMON
                for grim in results
            ),
            "Expected no result where the player is a non-demon role if that player was the Imp before."
        )

        base_page.characters[target] = Role.ANY_OTHER
        base_page.dead[target] = True

        # a second death for the same player is a bug in the caller, not a world to reject
        with self.assertRaises(AssertionError):
            _ = add_death_info_to_grims(info, [base])

    def test_startpass(self):
        base = Grimoire()
        target = 3

        info: DemonKillInfo = {
            "kind": "demon",
            "night": 2,
            "player": target
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                )).dead[target]
                and page.characters[target] == Role.IMP
                for grim in results
            ),
            "Expected a result where the player is dead and an Imp."
        )
        # The input grim should not be mutated.
        self.assertEqual(len(base.pages), 1)
        self.assertFalse(base.get_first_page().dead[target])

        base = Grimoire()
        base_page = base.add_page(2, NightOrderPosition.AFTER_IMP)
        base_page.characters[target] = Role.NON_DEMON

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertFalse(
            any(
                get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                ).characters[target] == Role.IMP
                for grim in results
            ),
            "Expected no result where the player is an Imp if that player was a non-demon role before."
        )

        base_page.characters[target] = Role.ANY_OTHER
        base_page.dead[target] = True

        # a second death for the same player is a bug in the caller, not a world to reject
        with self.assertRaises(AssertionError):
            _ = add_death_info_to_grims(info, [base])

    def test_starpass_to_minions(self):
        base = Grimoire()
        base_page = base.add_page(2, NightOrderPosition.AFTER_IMP)
        target = 3
        minion = 0
        base_page.characters[minion] = Role.ANY_OTHER_MINION 

        info: DemonKillInfo = {
            "kind": "demon",
            "night": 2,
            "player": target
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                )).dead[target]
                and page.characters[target] == Role.IMP
                and page.characters[minion] == Role.IMP
                for grim in results
            ),
            "Expected a result where the player is dead and was a demon and the minion is now a demon."
        )

        base = Grimoire()
        base_page = base.add_page(2, NightOrderPosition.AFTER_IMP)
        base_page.characters[minion] = Role.ANY_OTHER_MINION
        base_page.dead[minion] = True

        info: DemonKillInfo = {
            "kind": "demon",
            "night": 2,
            "player": target
        }

        results = add_death_info_to_grims(info, [base])
        self.assertFalse(
            any(
                get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                ).characters[target] == Role.IMP
                for grim in results
            ),
            "Expected no result where the player is an Imp if the minion was dead already."
        )

        base = Grimoire(10)
        base_page = base.add_page(2, NightOrderPosition.AFTER_IMP)
        scarlet_woman = 1
        minion = 0
        base_page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        base_page.characters[minion] = Role.ANY_OTHER_MINION

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                )).dead[target]
                and page.characters[target] == Role.IMP
                and page.characters[scarlet_woman] == Role.IMP
                and page.characters[minion] == Role.ANY_OTHER_MINION
                for grim in results
            ),
            "Expected a result where the player is dead and was a demon and the scarlet woman prioritizes catching the pass."
        )

        base = Grimoire(10)
        base_page = base.add_page(2, NightOrderPosition.AFTER_IMP)
        minion1 = 0
        non_demon = 2
        base_page.characters[minion1] = Role.ANY_OTHER_MINION
        base_page.characters[non_demon] = Role.NON_DEMON

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    2,
                    NightOrderPosition.AFTER_IMP,
                )).dead[target]
                and page.characters[target] == Role.IMP
                and page.characters[minion1] == Role.ANY_OTHER_EVIL
                and page.characters[non_demon] == Role.ANY_OTHER
                for grim in results
            ),
            "Expected a result where the player is dead and was a demon and the minions and non-demons are now possible demon candidates."
        )

    def test_non_demon_executed(self):
        base = Grimoire()
        target = 3

        info: ExecutionInfo = {
            "kind": "execution",
            "night": 1,
            "player": target
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_EXECUTION,
                )).dead[target]
                and page.characters[target] == Role.NON_DEMON
                for grim in results
            ),
            "Expected a result where the player is dead and a non-demon role."
        )
        # The input grim should not be mutated.
        self.assertEqual(len(base.pages), 1)
        self.assertFalse(base.get_first_page().dead[target])

        base_page = base.add_page(1, NightOrderPosition.AFTER_EXECUTION)
        base_page.characters[target] = Role.IMP

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertFalse(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_EXECUTION,
                )).dead[target]
                and page.characters[target] == Role.NON_DEMON
                for grim in results
            ),
            "Expected no result where the player is a non-demon role if the executed player was an Imp before."
        )

        base_page.characters[target] = Role.ANY_OTHER
        base_page.dead[target] = True

        # a second death for the same player is a bug in the caller, not a world to reject
        with self.assertRaises(AssertionError):
            _ = add_death_info_to_grims(info, [base])

    def test_demon_executed(self):
        base = Grimoire()
        target = 3

        info: ExecutionInfo = {
            "kind": "execution",
            "night": 1,
            "player": target
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_EXECUTION,
                )).dead[target]
                and page.characters[target] == Role.IMP
                and Role.SCARLET_WOMAN in page.minion_types
                for grim in results
            ),
            "Expected a result where the player is dead and an Imp and Scarlet Woman is a minion type."
        )
        # The input grim should not be mutated.
        self.assertEqual(len(base.pages), 1)
        self.assertFalse(base.get_first_page().dead[target])

        base = Grimoire()
        base_page = base.add_page(1, NightOrderPosition.AFTER_EXECUTION)
        base_page.characters[target] = Role.NON_DEMON

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertFalse(
            any(
                get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_EXECUTION,
                ).characters[target] == Role.IMP
                for grim in results
            ),
            "Expected no result where the player is an Imp if that player was a non-demon role before."
        )

        base_page.characters[target] = Role.ANY_OTHER
        base_page.dead[target] = True

        # a second death for the same player is a bug in the caller, not a world to reject
        with self.assertRaises(AssertionError):
            _ = add_death_info_to_grims(info, [base])

        base = Grimoire()
        scarlet_woman = 0
        base_page = base.add_page(1, NightOrderPosition.AFTER_EXECUTION)
        base_page.characters[scarlet_woman] = Role.SCARLET_WOMAN

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_EXECUTION,
                )).dead[target]
                and page.characters[target] == Role.IMP
                and Role.SCARLET_WOMAN in page.minion_types
                and page.characters[scarlet_woman] == Role.IMP
                for grim in results
            ),
            "Expected a result where the old Scarlet Woman is now the Imp."
        )

        base = Grimoire(10)
        minion1 = 0
        minion2 = 1
        base_page: GrimoirePage = base.add_page(1, NightOrderPosition.AFTER_EXECUTION)
        base_page.characters[minion1] = Role.ANY_OTHER_MINION
        base_page.characters[minion2] = Role.ANY_OTHER_MINION
        base_page.dead[minion1] = True

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_EXECUTION,
                )).dead[target]
                and page.characters[target] == Role.IMP
                and Role.SCARLET_WOMAN in page.minion_types
                and page.characters[minion2] == Role.IMP
                for grim in results
            ),
            "Expected a result where Scarlet Woman is in the minion types and the only alive minion is the new Imp."
        )

    def test_recluse_slayer_shot(self):
        base = Grimoire(6)
        recluse = 3

        info: SlayerKillInfo = {
            "kind": "slayer",
            "night": 1,
            "player": recluse
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_SLAYER,
                )).dead[recluse]
                and page.characters[recluse] == Role.RECLUSE
                for grim in results
            ),
            "Expected a result where the shot player was a Recluse"
        )
        # The input grim should not be mutated.
        self.assertEqual(len(base.pages), 1)
        self.assertFalse(base.get_first_page().dead[recluse])

        base = Grimoire(10)

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_SLAYER,
                )).dead[recluse]
                and page.characters[recluse] == Role.RECLUSE
                and Role.BARON in page.minion_types
                for grim in results
            ),
            "Expected a result where the shot player was a Recluse and Baron was a minion type."
        )

    def test_imp_slayer_shot(self):
        base = Grimoire(10)
        imp = 3

        info: SlayerKillInfo = {
            "kind": "slayer",
            "night": 1,
            "player": imp
        }

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_SLAYER,
                )).dead[imp]
                and page.characters[imp] == Role.IMP
                and Role.SCARLET_WOMAN in page.minion_types
                for grim in results
            ),
            "Expected a result where the shot player was an Imp and Scarlet Woman is a minion type."
        )
        # The input grim should not be mutated.
        self.assertEqual(len(base.pages), 1)
        self.assertFalse(base.get_first_page().dead[imp])

        base = Grimoire(10)
        scarlet_woman = 0
        base_page = base.add_page(1, NightOrderPosition.AFTER_SLAYER)
        base_page.characters[scarlet_woman] = Role.SCARLET_WOMAN

        results = add_death_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (page := get_required_page(
                    grim,
                    1,
                    NightOrderPosition.AFTER_SLAYER,
                )).dead[imp]
                and page.characters[imp] == Role.IMP
                and Role.SCARLET_WOMAN in page.minion_types
                and page.characters[scarlet_woman] == Role.IMP
                for grim in results
            ),
            "Expected a result where the shot player was an Imp and the old Scarlet Woman is an Imp."
        )

class TestStarpassToRedHerringSpy(unittest.TestCase):
    NIGHT = 2
    ORDER = NightOrderPosition.AFTER_IMP
    IMP = 3
    SPY = 0

    def _kill_imp(self, base: Grimoire) -> list[Grimoire]:
        info: DemonKillInfo = {
            "kind": "demon",
            "night": self.NIGHT,
            "player": self.IMP,
        }
        return add_death_info_to_grims(info, [base])

    def _base(self, num_players: int) -> tuple[Grimoire, GrimoirePage]:
        base = Grimoire(num_players)
        page = base.add_page(self.NIGHT, self.ORDER)
        page.add_minion_type(Role.SPY)
        page.characters[self.SPY] = Role.SPY
        page.red_herring[self.SPY] = True
        return base, page

    def _starpass_pages(self, results: list[Grimoire]) -> list[GrimoirePage]:
        pages = [get_required_page(g, self.NIGHT, self.ORDER) for g in results]
        return [p for p in pages if p.dead[self.IMP] and p.characters[self.IMP] == Role.IMP]

    def _spy_became_imp(self, page: GrimoirePage) -> bool:
        return (
            page.characters[self.SPY] == Role.IMP
            and not page.red_herring[self.SPY]
            and page.red_herring_moved
        )

    def _spy_stayed_spy(self, page: GrimoirePage) -> bool:
        return (
            page.characters[self.SPY] == Role.SPY
            and page.red_herring[self.SPY]
            and not page.red_herring_moved
        )

    def test_both_branches_when_other_minion_possible(self):
        base, _ = self._base(10)
        pages = self._starpass_pages(self._kill_imp(base))

        self.assertTrue(
            any(self._spy_became_imp(p) for p in pages),
            "Expected a branch where the red herring Spy caught the starpass and the red herring moved.",
        )
        self.assertTrue(
            any(self._spy_stayed_spy(p) for p in pages),
            "Expected a branch where another minion caught the starpass and the Spy kept the red herring.",
        )
        self.assertFalse(
            any(p.characters[self.SPY] == Role.ANY_OTHER_EVIL for p in pages),
            "The red herring Spy should not be widened to ANY_OTHER_EVIL.",
        )

    def test_spy_is_only_minion(self):
        # 5 players: one minion, so the Spy must catch the starpass
        base, _ = self._base(5)
        pages = self._starpass_pages(self._kill_imp(base))

        self.assertTrue(
            any(self._spy_became_imp(p) for p in pages),
            "Expected the only minion (the red herring Spy) to become the Imp.",
        )
        self.assertFalse(
            any(p.characters[self.SPY] == Role.SPY for p in pages),
            "The Spy cannot stay the Spy when no other minion can catch the starpass.",
        )
        self.assertFalse(
            any(p.characters[self.SPY] == Role.IMP and p.red_herring[self.SPY] for p in pages),
            "The red herring must never stay on the new Imp.",
        )

    def test_scarlet_woman_takes_priority(self):
        for scarlet_woman in (1, 5):  # Spy is seat 0, so the Scarlet Woman is seated after it
            with self.subTest(scarlet_woman=scarlet_woman):
                base, page = self._base(10)
                page.add_minion_type(Role.SCARLET_WOMAN)
                page.characters[scarlet_woman] = Role.SCARLET_WOMAN
                pages = self._starpass_pages(self._kill_imp(base))

                self.assertTrue(
                    any(
                        p.characters[scarlet_woman] == Role.IMP and self._spy_stayed_spy(p)
                        for p in pages
                    ),
                    "Expected the Scarlet Woman to catch the starpass with the Spy keeping the red herring.",
                )
                self.assertFalse(
                    any(p.characters[self.SPY] == Role.IMP for p in pages),
                    "The Spy should not catch the starpass over a living, healthy Scarlet Woman.",
                )

    def test_scarlet_woman_seated_before_spy(self):
        # Spy at a later seat than the Scarlet Woman
        base = Grimoire(10)
        page = base.add_page(self.NIGHT, self.ORDER)
        spy, scarlet_woman = 5, 0
        page.add_minion_type(Role.SPY)
        page.add_minion_type(Role.SCARLET_WOMAN)
        page.characters[spy] = Role.SPY
        page.red_herring[spy] = True
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        pages = self._starpass_pages(self._kill_imp(base))

        self.assertGreater(len(pages), 0)
        self.assertFalse(
            any(p.characters[spy] == Role.IMP for p in pages),
            "The Spy should not catch the starpass over a living, healthy Scarlet Woman.",
        )

    def test_spy_without_red_herring_unchanged(self):
        base = Grimoire(10)
        page = base.add_page(self.NIGHT, self.ORDER)
        page.add_minion_type(Role.SPY)
        page.characters[self.SPY] = Role.SPY
        pages = self._starpass_pages(self._kill_imp(base))

        self.assertGreater(len(pages), 0)
        self.assertFalse(
            any(p.red_herring_moved for p in pages),
            "The red herring Spy branch should not fire when the Spy has no red herring.",
        )
        self.assertTrue(
            any(p.characters[self.SPY] == Role.ANY_OTHER_EVIL for p in pages),
            "A Spy without the red herring is widened like any other minion.",
        )

    def test_dead_red_herring_spy_does_not_catch(self):
        base, page = self._base(10)
        page.dead[self.SPY] = True
        pages = self._starpass_pages(self._kill_imp(base))

        self.assertFalse(
            any(p.characters[self.SPY] == Role.IMP for p in pages),
            "A dead Spy cannot catch the starpass.",
        )


class TestRedHerringAfterMove(unittest.TestCase):
    SPY = 0
    FORTUNE_TELLER = 1
    IMP = 3

    def test_new_red_herring_can_be_marked_after_a_move(self):
        # 5 players: the red herring Spy is the only minion, so it catches the starpass and the red herring moves
        base = Grimoire(5)
        first = base.get_first_page()
        first.add_minion_type(Role.SPY)
        first.characters[self.SPY] = Role.SPY
        first.red_herring[self.SPY] = True
        kill: DemonKillInfo = {"kind": "demon", "night": 2, "player": self.IMP}
        moved = [
            w for w in add_death_info_to_grims(kill, [base])
            if get_required_page(w, 2, NightOrderPosition.AFTER_IMP).red_herring_moved
        ]
        self.assertGreater(len(moved), 0)

        reading: FortuneTellerInfo = {"kind": "fortune teller", "fortune_teller": self.FORTUNE_TELLER, "night": 2, "pings": ((2, 4), True)}
        worlds = add_info_to_grims(reading, moved)
        new_red_herrings = [
            w for w in worlds
            if (page := get_required_page(w, 2, NightOrderPosition.AFTER_IMP)).red_herring[2] or page.red_herring[4]
        ]
        self.assertGreater(len(new_red_herrings), 0, "Expected the new red herring to explain a yes after the old one moved.")
        for world in new_red_herrings:
            self.assertTrue(world.get_first_page().red_herring[self.SPY], "Expected the Spy to stay the red herring before the move.")

class TestAddInfoToGrims(unittest.TestCase):
    def test_fortune_teller_no(self):
        fortune_teller = 0
        a = 1
        b = 2

        base = Grimoire(10)

        info: FortuneTellerInfo = {
            "kind": "fortune teller",
            "fortune_teller": fortune_teller,
            "night": 1,
            "pings": ((a, b), False),
        }

        results = add_info_to_grims(info, [base])
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any(
                (
                    (page := grim.get_first_page()).characters[fortune_teller] == Role.FORTUNE_TELLER
                    and page.characters[a] == Role.NON_DEMON
                    and page.characters[b] == Role.NON_DEMON
                )
                for grim in results
            ),
            "Expected a no-ping Fortune Teller branch where both pinged players are non-demons.",
        )

        # The input grim should not be mutated.
        self.assertEqual(base.get_first_page().characters[fortune_teller], Role.ANY_OTHER)
        self.assertEqual(base.get_first_page().characters[a], Role.ANY_OTHER)
        self.assertEqual(base.get_first_page().characters[b], Role.ANY_OTHER)

        base = Grimoire(10)
        demon = 1
        base.get_first_page().characters[demon] = Role.IMP

        results = add_info_to_grims(info, [base])
        self.assertFalse(
            any(
                (
                    (page := grim.get_first_page()).characters[fortune_teller] == Role.FORTUNE_TELLER
                    and page.characters[a] == Role.NON_DEMON
                    and page.characters[b] == Role.NON_DEMON
                )
                for grim in results
            ),
            "Expected no branches where both pinged players are non-demons if one was an Imp before.",
        )

    def test_fortune_teller_yes(self):
        fortune_teller = 0
        a = 1
        b = 2

        base = Grimoire(10)

        info: FortuneTellerInfo = {
            "kind": "fortune teller",
            "fortune_teller": fortune_teller,
            "night": 1,
            "pings": ((a, b), True),
        }

        results = add_info_to_grims(info, [base])

        self.assertGreater(len(results), 0)

        has_demon_branch = any(
            (
                (page := grim.get_first_page()).characters[fortune_teller] == Role.FORTUNE_TELLER
                and (
                    page.characters[a] == Role.IMP
                    or page.characters[b] == Role.IMP
                )
            )
            for grim in results
        )

        has_red_herring_branch = any(
            (
                (page := grim.get_first_page()).characters[fortune_teller] == Role.FORTUNE_TELLER
                and (
                    page.red_herring[a]
                    or page.red_herring[b]
                )
            )
            for grim in results
        )

        has_recluse_branch = any(
            (
                (page := grim.get_first_page()).characters[fortune_teller] == Role.FORTUNE_TELLER
                and (
                    page.characters[a] == Role.RECLUSE
                    or page.characters[b] == Role.RECLUSE
                )
            )
            for grim in results
        )

        self.assertTrue(
            has_demon_branch and has_red_herring_branch and has_recluse_branch,
            "Expected yes-ping Fortune Teller branches with Imp, red herring and Recluse.",
        )

        # The input grim should not be mutated.
        self.assertEqual(base.get_first_page().characters[fortune_teller], Role.ANY_OTHER)
        self.assertFalse(base.get_first_page().red_herring[a])
        self.assertFalse(base.get_first_page().red_herring[b])


def _page(
    night: int,
    order: NightOrderPosition,
    characters: list[Role],
    minion_types: list[Role],
    dead: list[bool] | None = None,
    poisoned: list[bool] | None = None,
    **fields: object,
) -> GrimoirePage:
    page = GrimoirePage(len(characters), night, order)
    page.characters = list(characters)
    page.minion_types = list(minion_types)
    if dead is not None:
        page.dead = list(dead)
    if poisoned is not None:
        page.poisoned = list(poisoned)
    for field, value in fields.items():
        setattr(page, field, value)
    return page

def _grim(pages: list[GrimoirePage]) -> Grimoire:
    grim = Grimoire(pages[0].num_players)
    grim.pages = pages
    grim.keys = [(p.night, p.night_order_position) for p in pages]
    return grim


class TestFortuneTellerRulesOutRedHerring(unittest.TestCase):
    FORTUNE_TELLER = 0
    PLAYER = 1

    @staticmethod
    def _info(night: int, pair: tuple[int, int], ping: bool) -> FortuneTellerInfo:
        return {"kind": "fortune teller", "fortune_teller": 0, "night": night, "pings": (pair, ping)}

    def _worlds(self, infos: list[FortuneTellerInfo]) -> list[Grimoire]:
        worlds = [Grimoire(5)]
        for info in infos:
            worlds = add_info_to_grims(info, worlds)
        return worlds

    def _red_herring_after_sober_no(self, worlds: list[Grimoire], no_night: int) -> list[Grimoire]:
        out: list[Grimoire] = []
        for world in worlds:
            page = world.get_page(no_night, NightOrderPosition.AFTER_IMP)
            if page is None or page.characters[self.FORTUNE_TELLER] != Role.FORTUNE_TELLER or page.poisoned[self.FORTUNE_TELLER]:
                continue
            if any(p.red_herring[self.PLAYER] for p in world.pages):
                out.append(world)
        return out

    def test_no_then_yes(self):
        worlds = self._worlds([self._info(1, (1, 2), False), self._info(2, (1, 3), True)])
        self.assertEqual(self._red_herring_after_sober_no(worlds, 1), [], "A sober Fortune Teller's no ruled player 1 out.")
        self.assertTrue(
            any(any(p.red_herring[self.PLAYER] for p in w.pages) for w in worlds),
            "Expected player 1 to still be the red herring when the Fortune Teller wasn't sober on night 1.",
        )

    def test_yes_then_no(self):
        worlds = self._worlds([self._info(1, (1, 3), True), self._info(2, (1, 2), False)])
        self.assertEqual(self._red_herring_after_sober_no(worlds, 2), [], "A sober Fortune Teller's no ruled player 1 out.")

    def test_no_after_the_first_night_then_yes(self):
        # marks set on a later page have to survive passing from an earlier page that has none
        worlds = self._worlds([self._info(2, (1, 2), False)])
        self.assertTrue(any(
            (page := w.get_page(2, NightOrderPosition.AFTER_IMP)) is not None
            and page.not_red_herring[1] and page.not_red_herring[2]
            for w in worlds
        ))
        worlds = self._worlds([self._info(2, (1, 2), False), self._info(3, (1, 3), True)])
        self.assertEqual(self._red_herring_after_sober_no(worlds, 2), [], "A sober Fortune Teller's no ruled player 1 out.")

    def test_no_marks_from_an_unreliable_reading(self):
        worlds = self._worlds([self._info(1, (1, 2), False)])
        for world in worlds:
            page = world.get_first_page()
            if page.characters[self.FORTUNE_TELLER] == Role.FORTUNE_TELLER and not page.poisoned[self.FORTUNE_TELLER]:
                self.assertTrue(page.not_red_herring[1] and page.not_red_herring[2])
            else:
                self.assertFalse(any(page.not_red_herring), "Expected only a sober Fortune Teller's reading to rule players out.")

    def test_starpass_page_drops_the_marks(self):
        # the night 2 page is made as a copy of night 1, marks included
        base = Grimoire()
        first = base.get_first_page()
        first.apply_not_red_herring(1)
        first.apply_not_red_herring(2)
        kill: DemonKillInfo = {"kind": "demon", "night": 2, "player": 0}
        results = add_death_info_to_grims(kill, [base])

        starpasses = [grim for grim in results if grim.pages[-1].star_passed]
        others = [grim for grim in results if not grim.pages[-1].star_passed]
        self.assertGreater(len(starpasses), 0)
        self.assertGreater(len(others), 0)
        for grim in starpasses:
            self.assertTrue(grim.pages[0].not_red_herring[1] and grim.pages[0].not_red_herring[2], "Expected the marks to stay on the page before the starpass.")
            self.assertFalse(any(grim.pages[-1].not_red_herring), "Expected the red herring to be able to move to a ruled out player on a starpass.")
        for grim in others:
            self.assertTrue(grim.pages[-1].not_red_herring[1] and grim.pages[-1].not_red_herring[2], "Expected the marks to stay when nobody starpassed.")

    def test_true_grim_with_red_herring_moved_onto_a_ruled_out_player_is_kept(self):
        base = Grimoire()
        base.get_first_page().apply_not_red_herring(1)
        kill: DemonKillInfo = {"kind": "demon", "night": 2, "player": 0}

        true_grim = Grimoire()
        true_first = true_grim.get_first_page()
        true_first.minion_types = [Role.SPY]
        true_first.characters = [Role.IMP, Role.EMPATH, Role.SPY, Role.MONK, Role.CHEF]
        true_first.red_herring[2] = True
        true_night2 = true_grim.add_page(2, NightOrderPosition.AFTER_IMP)
        true_night2.dead[0] = True
        true_night2.characters[2] = Role.IMP
        true_night2.red_herring = [False, True, False, False, False]
        true_night2.star_passed = True
        true_night2.red_herring_moved = True

        results = add_death_info_to_grims(kill, [base])
        self.assertTrue(any(true_grim.loose_equals(grim) for grim in results))

class TestSpentVirgin(unittest.TestCase):
    VIRGIN = 0
    NOMINATOR = 1

    @staticmethod
    def _virgin_info(night: int, executed: bool, virgin: int = 0, nominator: int = 1) -> VirginInfo:
        return {"kind": "virgin", "virgin": virgin, "nominator": nominator, "executed": executed, "night": night}

    def _townsfolk_nominator_base(self) -> Grimoire:
        base = Grimoire(10)
        base.get_first_page().characters[self.NOMINATOR] = Role.WASHERWOMAN
        return base

    def _has_sober_virgin(self, worlds: list[Grimoire]) -> bool:
        return any(
            (page := w.pages[-1]).characters[self.VIRGIN] == Role.VIRGIN
            and not page.poisoned[self.VIRGIN]
            for w in worlds
        )

    def test_earlier_nomination_spends_the_ability(self):
        info = self._virgin_info(2, executed=False)
        for executed in (True, False):
            earlier = self._virgin_info(1, executed=executed, nominator=2)
            self.assertTrue(_is_virgin_spent(info, [earlier, info]), f"earlier executed={executed}")

    def test_other_nominations_do_not_spend_the_ability(self):
        info = self._virgin_info(2, executed=False)
        cases: dict[str, list[Info]] = {
            "only itself": [info],
            "same night": [self._virgin_info(2, executed=False, nominator=2), info],
            "different virgin": [self._virgin_info(1, executed=True, virgin=3), info],
            "later night": [info, self._virgin_info(3, executed=False, nominator=2)],
            "other kind of info": [
                {"kind": "slayer", "slayer": 0, "target": 1, "successful": False, "night": 1},
                info,
            ],
            "no info list": [],
        }
        for name, info_list in cases.items():
            self.assertFalse(_is_virgin_spent(info, info_list), name)

    def test_spent_virgin_nominated_by_townsfolk_is_not_executed(self):
        info = self._virgin_info(2, executed=False)
        earlier = self._virgin_info(1, executed=True, nominator=2)

        unspent = add_info_to_grims(info, [self._townsfolk_nominator_base()])
        self.assertFalse(
            self._has_sober_virgin(unspent),
            "An unspent sober Virgin nominated by a Townsfolk would have executed them.",
        )

        spent = add_info_to_grims(info, [self._townsfolk_nominator_base()], info_list=[earlier, info])
        self.assertTrue(
            self._has_sober_virgin(spent),
            "A sober Virgin whose ability is spent doesn't execute a Townsfolk nominator.",
        )

    def test_spent_virgin_cannot_execute(self):
        info = self._virgin_info(2, executed=True)
        earlier = self._virgin_info(1, executed=False, nominator=2)

        self.assertGreater(len(add_info_to_grims(info, [Grimoire(10)])), 0)
        self.assertEqual(
            add_info_to_grims(info, [Grimoire(10)], info_list=[earlier, info]),
            [],
            "No world explains an execution by a spent Virgin.",
        )


class TestFinalize(unittest.TestCase):
    def test_conflict_found_only_on_second_pass(self):
        # Found in a 10p smoke game. Night 1 Chef 0 with player 0 next to the Scarlet Woman forces
        # player 0 to be the Spy, but that is only deduced after the first pass. The second pass
        # then finds night 1's minion types (SW, Spy) clash with night 2's (Poisoner, SW).
        # players 2-9; player 3 is evil
        rest = [Role.SLAYER, Role.ANY_OTHER_EVIL, Role.CHEF, Role.LIBRARIAN, Role.UNDERTAKER, Role.MAYOR, Role.SOLDIER, Role.MONK]
        grim = _grim([
            _page(1, NightOrderPosition.AFTER_IMP,
                [Role.ANY_OTHER_EVIL, Role.SCARLET_WOMAN] + rest,
                [Role.SCARLET_WOMAN, Role.ANY_OTHER_MINION],
                chef_number=0, no_outsiders=True),
            _page(1, NightOrderPosition.AFTER_EXECUTION,
                [Role.ANY_OTHER_EVIL, Role.SCARLET_WOMAN] + rest,
                [Role.SCARLET_WOMAN, Role.ANY_OTHER_MINION],
                dead=[i == 8 for i in range(10)],
                no_outsiders=True, executee=8),
            _page(2, NightOrderPosition.AFTER_IMP,
                [Role.IMP, Role.SCARLET_WOMAN] + rest,
                [Role.POISONER, Role.SCARLET_WOMAN],
                dead=[i in (0, 8) for i in range(10)],
                poisoned=[i == 2 for i in range(10)],
                no_outsiders=True, star_passed=True),
            _page(3, NightOrderPosition.AFTER_EXECUTION,
                [Role.IMP, Role.IMP, Role.SLAYER, Role.IMP] + rest[2:],
                [Role.POISONER, Role.SCARLET_WOMAN],
                dead=[i in (0, 3, 8) for i in range(10)],
                no_outsiders=True, star_passed=True, executee=3),
        ])
        self.assertIsNone(_finalize(grim), "Expected the minion type conflict found on the second pass to reject the world.")

    def test_reports_why_a_world_is_impossible(self):
        grim = Grimoire()
        grim.get_first_page().minion_types = [Role.BARON]
        night2 = grim.add_page(2, NightOrderPosition.AFTER_IMP)
        night2.minion_types = [Role.POISONER]
        self.assertEqual(find_finalize_problem(grim), "mismatched minion types between pages")

    def test_not_settling_is_an_error_not_an_invalid_world(self):
        # branching drops a world on RuntimeError or ValueError, which would hide this bug
        with mock.patch.object(GrimoirePage, "make_deductions", return_value=True) as make_deductions:
            with self.assertRaises(FinalizeDidNotSettleError):
                _ = _finalize(Grimoire())
            self.assertEqual(make_deductions.call_count, MAX_FINALIZE_ROUNDS)
            with self.assertRaises(FinalizeDidNotSettleError):
                _ = _try_branch(Grimoire())

    def test_settled_world_is_kept_unchanged(self):
        grim = Grimoire()
        grim.get_first_page().characters = [Role.IMP, Role.SCARLET_WOMAN, Role.MONK, Role.EMPATH, Role.SLAYER]
        grim.get_first_page().minion_types = [Role.SCARLET_WOMAN]
        _ = grim.add_page(2, NightOrderPosition.AFTER_IMP)
        expected = grim.clone()
        result = _finalize(grim)
        self.assertIsNotNone(result)
        assert result is not None
        for page, expected_page in zip(result.pages, expected.pages):
            self.assertEqual(vars(expected_page), vars(page))

    def test_result_is_settled(self):
        # finalizing a finalized world again must change nothing
        grim = Grimoire()
        grim.get_first_page().characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        grim.get_first_page().minion_types = [Role.POISONER]
        _ = grim.add_page(2, NightOrderPosition.AFTER_IMP)
        result = _finalize(grim)
        assert result is not None
        again = _finalize(result.clone())
        assert again is not None
        for page, again_page in zip(result.pages, again.pages):
            self.assertEqual(vars(page), vars(again_page))
        self.assertEqual(Role.IMP, result.pages[1].characters[0], "Expected night 1 deductions to reach night 2.")


class TestDirtyPageFinalize(unittest.TestCase):
    def _settled(self, nights: int = 3) -> Grimoire:
        grim = Grimoire()
        for night in range(2, nights + 1):
            _ = grim.add_page(night, NightOrderPosition.AFTER_IMP)
        result = _finalize(grim)
        assert result is not None
        return result

    def test_finalized_world_is_settled(self):
        self.assertEqual(set(), self._settled().unsettled)

    def test_rejected_world_stays_unsettled(self):
        grim = Grimoire()
        grim.get_first_page().minion_types = [Role.BARON]
        night2 = grim.add_page(2, NightOrderPosition.AFTER_IMP)
        night2.minion_types = [Role.POISONER]
        self.assertIsNone(_finalize(grim))
        self.assertIsNone(grim.unsettled)

    def test_default_finalizes_every_page(self):
        grim = Grimoire()
        night2 = grim.add_page(2, NightOrderPosition.AFTER_IMP)
        grim.get_first_page().characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        grim.get_first_page().minion_types = [Role.POISONER]
        self.assertIsNotNone(_finalize(grim))
        self.assertEqual(Role.IMP, night2.characters[0])

    def test_clean_pages_are_not_deduced(self):
        grim = self._settled()
        deducible = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        grim.pages[0].characters = list(deducible)
        grim.pages[0].minion_types = [Role.POISONER]
        self.assertIsNotNone(_finalize(grim, {grim.keys[2]}))
        self.assertEqual(deducible, grim.pages[0].characters, "Expected a page outside dirty_keys to be left alone.")

    def test_only_changed_pages_are_deduced_again(self):
        grim = self._settled(4)
        grim.pages[1].dead[0] = True
        with mock.patch.object(GrimoirePage, "make_deductions", autospec=True, return_value=False) as make_deductions:
            self.assertIsNotNone(_finalize(grim, {grim.keys[1]}))
        deduced = [call.args[0] for call in make_deductions.call_args_list]
        self.assertEqual({id(grim.pages[i]) for i in (1, 2, 3)}, {id(page) for page in deduced}, "Expected the dirty page and the pages it changed.")

    def test_deduction_on_a_dirty_page_reaches_later_pages(self):
        grim = self._settled()
        grim.pages[0].characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        grim.pages[0].minion_types = [Role.POISONER]
        self.assertIsNotNone(_finalize(grim, {grim.keys[0]}))
        self.assertEqual(Role.IMP, grim.pages[2].characters[0])

    def test_conflict_found_after_a_deduction_on_a_dirty_page(self):
        grim = self._settled()
        grim.pages[0].characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        grim.pages[0].minion_types = [Role.POISONER]
        grim.pages[2].characters[0] = Role.SLAYER
        self.assertIsNone(_finalize(grim, {grim.keys[0]}))

    def test_first_page_is_validated_when_dirty(self):
        # nothing passes into the first page, so this is the only check it gets
        too_many_evils = [Role.IMP, Role.BARON, Role.POISONER, Role.MONK, Role.SLAYER]
        grim = self._settled()
        grim.pages[0].characters = list(too_many_evils)
        self.assertIsNotNone(find_finalize_problem(grim, {grim.keys[0]}))

        grim = Grimoire()
        grim.get_first_page().characters = list(too_many_evils)
        self.assertIsNotNone(find_finalize_problem(grim))

    def test_later_pages_are_validated_when_dirty(self):
        grim = self._settled()
        grim.pages[1].characters = [Role.IMP, Role.BARON, Role.POISONER, Role.MONK, Role.SLAYER]
        self.assertIsNotNone(find_finalize_problem(grim, {grim.keys[1]}))

    def test_branch_finalizes_the_page_its_actions_changed(self):
        grim = self._settled()
        def set_monk(candidate: Grimoire) -> bool:
            candidate.pages[0].characters[0] = Role.MONK
            return True
        result = _try_branch(grim, set_monk)
        assert result is not None
        self.assertEqual(Role.MONK, result.pages[2].characters[0])
        self.assertEqual(set(), result.unsettled)
        self.assertEqual(Role.ANY_OTHER, grim.pages[0].characters[0], "Expected the base world not to change.")

    def test_intermediate_branch_records_its_changes(self):
        grim = self._settled()
        def set_monk(candidate: Grimoire) -> bool:
            candidate.pages[0].characters[0] = Role.MONK
            return True
        intermediate = _try_intermediate_branch(grim, set_monk)
        assert intermediate is not None
        self.assertEqual({grim.keys[0]}, intermediate.unsettled)
        self.assertEqual(Role.ANY_OTHER, intermediate.pages[2].characters[0], "Expected an intermediate world not to be finalized yet.")

    def test_changes_from_an_intermediate_branch_get_finalized(self):
        # the change comes from the intermediate world, so comparing with that world alone would miss it
        grim = self._settled()
        def set_monk(candidate: Grimoire) -> bool:
            candidate.pages[0].characters[0] = Role.MONK
            return True
        intermediate = _try_intermediate_branch(grim, set_monk)
        assert intermediate is not None
        result = _try_branch(intermediate)
        assert result is not None
        self.assertEqual(Role.MONK, result.pages[2].characters[0])
        self.assertEqual(set(), result.unsettled)

    def test_intermediate_change_that_conflicts_is_rejected(self):
        grim = self._settled()
        grim.pages[2].characters[0] = Role.SLAYER
        def set_monk(candidate: Grimoire) -> bool:
            candidate.pages[0].characters[0] = Role.MONK
            return True
        intermediate = _try_intermediate_branch(grim, set_monk)
        assert intermediate is not None
        self.assertIsNone(_try_branch(intermediate))

class TestUnpoisonedBranchesRecordTheirInfo(unittest.TestCase):
    """A poisoned world is only dropped for a world in the same state with less poison. That's only
    safe if the unpoisoned world has recorded what its info implies, otherwise later info could
    contradict it with nothing to show for it. This uses blank worlds because a branch can
    correctly record nothing when the world already implies its info."""
    # info kind -> (claimed role, player who gave the info, examples of that info)
    CASES: dict[str, tuple[Role, list[dict[str, object]]]] = {
        "investigator": (Role.INVESTIGATOR, [{"kind": "investigator", "investigator": 0, "first_player": 1, "second_player": 2, "minion": Role.SPY}]),
        "washerwoman": (Role.WASHERWOMAN, [{"kind": "washerwoman", "washerwoman": 0, "first_player": 1, "second_player": 2, "townsfolk": Role.EMPATH}]),
        "librarian": (Role.LIBRARIAN, [
            {"kind": "librarian", "librarian": 0, "first_player": 1, "second_player": 2, "token": Role.SAINT},
            {"kind": "librarian", "librarian": 0, "first_player": None, "second_player": None, "token": None},
        ]),
        "chef": (Role.CHEF, [{"kind": "chef", "chef": 0, "number": number} for number in (0, 1)]),
        "fortune teller": (Role.FORTUNE_TELLER, [
            {"kind": "fortune teller", "fortune_teller": 0, "night": night, "pings": ((1, 2), ping)}
            for night in (1, 2) for ping in (True, False)
        ]),
        "empath": (Role.EMPATH, [
            {"kind": "empath", "empath": 0, "number": number, "night": night, "left_neighbour": 4, "right_neighbour": 1}
            for night in (1, 2) for number in (0, 1, 2)
        ]),
        "undertaker": (Role.UNDERTAKER, [
            {"kind": "undertaker", "undertaker": 0, "body": 1, "token": token, "night": 2} for token in (Role.MONK, Role.IMP)
        ]),
        "ravenkeeper": (Role.RAVENKEEPER, [
            {"kind": "ravenkeeper", "ravenkeeper": 0, "chosen": 1, "token": token, "night": 2} for token in (Role.MONK, Role.IMP)
        ]),
        "virgin": (Role.VIRGIN, [{"kind": "virgin", "virgin": 0, "nominator": 1, "executed": False, "night": 1}]),
        "slayer": (Role.SLAYER, [{"kind": "slayer", "slayer": 0, "target": 1, "successful": False, "night": 1}]),
    }

    @staticmethod
    def _is_poisoned(world: Grimoire, night: int) -> bool:
        page = world.get_page(night, NightOrderPosition.AFTER_IMP)
        return page is not None and page.poisoned[0]

    def _check(self, base: Grimoire, kind: str, role: Role, info: dict[str, object]) -> int:
        night: int = info.get("night", 1)  # pyright: ignore[reportAssignmentType]
        claim_only = _try_intermediate_branch(base, character_action(role, 0, night, NightOrderPosition.AFTER_IMP))
        assert claim_only is not None
        worlds = add_info_to_grims(info, [base])  # pyright: ignore[reportArgumentType]
        poisoned = [w for w in worlds if self._is_poisoned(w, night)]
        unpoisoned = [w for w in worlds if not self._is_poisoned(w, night) and w.pages[-1].characters[0] == role]
        self.assertEqual(1, len(poisoned), "Expected one poisoned branch.")
        for world in unpoisoned:
            self.assertNotEqual(claim_only.state_without_poison(), world.state_without_poison(), f"{kind} recorded nothing.")
            self.assertNotEqual(poisoned[0].state_without_poison(), world.state_without_poison(), f"{kind} matches its poisoned branch.")
        return len(unpoisoned)

    def test_every_info_type_with_a_poisoned_branch_is_covered(self):
        kinds = {get_args(get_type_hints(t)["kind"])[0] for t in get_args(Info.__value__)}
        self.assertEqual(kinds - {"claim"}, set(self.CASES))

    def test_blank_world(self):
        for kind, (role, examples) in self.CASES.items():
            for info in examples:
                with self.subTest(kind=kind, info=info):
                    self.assertGreater(self._check(Grimoire(), kind, role, info), 0, "Expected an unpoisoned branch to check.")

    def test_blank_world_with_a_known_poisoner(self):
        # the poisoned branch has a Poisoner in its minion types, so this is what could actually match it
        for kind, (role, examples) in self.CASES.items():
            for info in examples:
                with self.subTest(kind=kind, info=info):
                    base = Grimoire()
                    base.pages[0].minion_types = [Role.POISONER]
                    _ = self._check(base, kind, role, info)

class TestDirtyPageFinalizeMatchesFullFinalize(unittest.TestCase):
    GAMES = {5: 40, 10: 2}

    def test_every_branch_matches(self):
        original = add_info_module._finalize  # pyright: ignore[reportPrivateUsage]
        compared = {"kept": 0, "rejected": 0}

        def state(grim: Grimoire) -> list[dict[str, object]]:
            return [dict(vars(page)) for page in grim.pages]

        def checked(grim: Grimoire, dirty_keys: set[GrimoireKey] | None = None) -> Grimoire | None:
            full = grim.clone()
            try:
                full_rejects = find_finalize_problem(full) is not None
            except (RuntimeError, ValueError):
                full_rejects = True
            result = original(grim, dirty_keys)
            self.assertEqual(full_rejects, result is None, "Expected both finalizes to agree on whether the world is possible.")
            if result is not None:
                self.assertEqual(state(full), state(result), "Expected both finalizes to settle on the same pages.")
            compared["rejected" if result is None else "kept"] += 1
            return result

        with mock.patch.object(add_info_module, "_finalize", checked):
            for players, games in self.GAMES.items():
                for scenario in load_scenarios(players, limit=games):
                    manager = GrimoireManager({"players": players}, scenario.true_grim)
                    manager.add_full_game(scenario.info, scenario.deaths, scenario.nights)

        self.assertGreater(compared["kept"], 1000)
        self.assertGreater(compared["rejected"], 0)


class TestSoldierKilledAtNight(unittest.TestCase):
    """A sober Soldier can't die to the Imp, so a killed Soldier claimant is the Drunk, evil or poisoned."""
    PLAYERS = 10
    SOLDIER = 2

    def _claimed(self, minion_types: list[Role] | None = None, dead_poisoner: int | None = None) -> list[Grimoire]:
        base = Grimoire(self.PLAYERS)
        first = base.get_first_page()
        if minion_types is not None:
            first.minion_types = list(minion_types)
        if dead_poisoner is not None:
            first.characters[dead_poisoner] = Role.POISONER
            first.dead[dead_poisoner] = True
        claim: Info = {"kind": "claim", "player": self.SOLDIER, "character": Role.SOLDIER}  # pyright: ignore[reportAssignmentType]
        return add_info_to_grims(claim, [base])

    def _kill_pages(self, grims: list[Grimoire]) -> list[GrimoirePage]:
        kill: DemonKillInfo = {"kind": "demon", "night": 2, "player": self.SOLDIER}
        results = add_death_info_to_grims(kill, grims)
        self.assertGreater(len(results), 0, "Expected the claimed Soldier to be killable as the Drunk or an evil player.")
        return [get_required_page(grim, 2, NightOrderPosition.AFTER_IMP) for grim in results]

    def _soldier_pages(self, pages: list[GrimoirePage]) -> list[GrimoirePage]:
        return [p for p in pages if p.characters[self.SOLDIER] == Role.SOLDIER]

    def test_kill_is_recorded(self):
        for page in self._kill_pages(self._claimed()):
            self.assertEqual(page.demon_kill, self.SOLDIER)

    def test_killed_soldier_is_poisoned(self):
        soldiers = self._soldier_pages(self._kill_pages(self._claimed()))
        self.assertGreater(len(soldiers), 0, "Expected a world where the Poisoner poisoned the Soldier.")
        for page in soldiers:
            self.assertTrue(page.poisoned[self.SOLDIER], "Expected no world where the Imp killed a sober Soldier.")

    def test_other_worlds_still_kept(self):
        pages = self._kill_pages(self._claimed())
        self.assertTrue(any(p.characters[self.SOLDIER] == Role.DRUNK for p in pages), "Expected a world where the claimant is the Drunk.")
        self.assertTrue(
            any(p.characters[self.SOLDIER] in EVIL_ROLES_SET | {Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL} for p in pages),
            "Expected a world where the claimant is evil.",
        )

    def test_no_poisoner_in_play(self):
        pages = self._kill_pages(self._claimed(minion_types=[Role.SPY, Role.BARON]))
        self.assertEqual(self._soldier_pages(pages), [], "Expected the Soldier to need a Poisoner to die.")

    def test_poisoner_already_dead(self):
        pages = self._kill_pages(self._claimed(minion_types=[Role.POISONER, Role.SPY], dead_poisoner=0))
        self.assertEqual(self._soldier_pages(pages), [], "Expected a dead Poisoner not to be able to poison the Soldier.")

    def test_full_game_keeps_poisoned_soldier(self):
        # the claim is applied on night 1 before any kill, so the kill sees the Soldier. this breaks if claims ever come after kills
        manager = GrimoireManager({"players": self.PLAYERS})
        claim: Info = {"kind": "claim", "player": self.SOLDIER, "character": Role.SOLDIER}  # pyright: ignore[reportAssignmentType]
        kill: DemonKillInfo = {"kind": "demon", "night": 2, "player": self.SOLDIER}
        manager.add_full_game([claim], [kill], 2)
        pages = [get_required_page(grim, 2, NightOrderPosition.AFTER_IMP) for grim in manager.grims]
        soldiers = self._soldier_pages(pages)
        self.assertGreater(len(soldiers), 0, "Expected the poisoned Soldier world to survive a full game.")
        self.assertTrue(all(p.poisoned[self.SOLDIER] for p in soldiers), "Expected no world where the Imp killed a sober Soldier.")


if __name__ == "__main__":
    unittest.main()