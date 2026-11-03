import unittest

from grimoire.add_info_to_grims import add_death_info_to_grims, add_info_to_grims
from grimoire.grimoire import Grimoire
from grimoire.grimoire_page import GrimoirePage
from grimoire.info import DemonKillInfo, ExecutionInfo, SlayerKillInfo, FortuneTellerInfo
from grimoire.nightOrderPosition import NightOrderPosition
from grimoire.role import Role


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

        results = add_death_info_to_grims(info, [base])
        self.assertEqual(len(results), 0, "Expected no results if the player was dead already.")

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

        results = add_death_info_to_grims(info, [base])
        self.assertEqual(len(results), 0, "Expected no results if the player was dead already.")

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

        results = add_death_info_to_grims(info, [base])
        self.assertEqual(len(results), 0, "Expected no results if the player was dead already.")

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

        results = add_death_info_to_grims(info, [base])
        self.assertEqual(len(results), 0, "Expected no results if the player was dead already.")

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


if __name__ == "__main__":
    unittest.main()