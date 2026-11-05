import unittest
from grimoire import Grimoire
from grimoire.nightOrderPosition import NightOrderPosition
from grimoire.role import Role
from grimoire import GrimoirePage

class TestAddPage(unittest.TestCase):

    def test_add_phase(self):
        # test phases with different nights
        world = Grimoire()
        _ = world.add_page(2, NightOrderPosition.AFTER_IMP)

        self.assertEqual(len(world.pages), 2)
        self.assertEqual(world.pages[0].night, 1)
        self.assertEqual(world.pages[1].night, 2)

        _ = world.add_page(5, NightOrderPosition.AFTER_IMP)
        _ = world.add_page(3, NightOrderPosition.AFTER_IMP)

        self.assertEqual(len(world.pages), 4)
        self.assertEqual(world.pages[2].night, 3)
        self.assertEqual(world.pages[3].night, 5)

        # test same night with different order

        _ = world.add_page(2, NightOrderPosition.AFTER_EXECUTION)
        _ = world.add_page(2, NightOrderPosition.AFTER_SLAYER)

        self.assertEqual(len(world.pages), 6)
        self.assertEqual(world.pages[1].night_order_position, NightOrderPosition.AFTER_IMP)
        self.assertEqual(world.pages[2].night_order_position, NightOrderPosition.AFTER_SLAYER)
        self.assertEqual(world.pages[3].night_order_position, NightOrderPosition.AFTER_EXECUTION)        

class TestGrimoireEquality(unittest.TestCase):
    @staticmethod
    def _poisoned_on_night(*nights: int) -> Grimoire:
        # poisoning is what creates the page for that night, as poisoned_action does
        world = Grimoire()
        for night in nights:
            world.add_page(night, NightOrderPosition.AFTER_IMP).poisoned[0] = True
        return world

    def test_clone_is_equal_with_same_hash(self):
        world = self._poisoned_on_night(2)
        self.assertEqual(world, world.clone())
        self.assertEqual(hash(world), hash(world.clone()))

    def test_same_poison_on_different_nights_is_unequal(self):
        self.assertNotEqual(self._poisoned_on_night(2), self._poisoned_on_night(3))

    def test_extra_page_is_unequal_both_ways(self):
        world = Grimoire()
        extra = Grimoire()
        _ = extra.add_page(2, NightOrderPosition.AFTER_IMP)
        self.assertNotEqual(world, extra)
        self.assertNotEqual(extra, world)

    def test_same_night_different_order_is_unequal(self):
        world = Grimoire()
        other = Grimoire()
        _ = world.add_page(2, NightOrderPosition.AFTER_IMP)
        _ = other.add_page(2, NightOrderPosition.AFTER_EXECUTION)
        self.assertNotEqual(world, other)

    def test_different_page_contents_are_unequal(self):
        world = Grimoire()
        other = Grimoire()
        other.pages[0].chef_number = 1
        self.assertNotEqual(world, other)

    def test_set_keeps_worlds_with_poison_on_different_nights(self):
        worlds = {self._poisoned_on_night(2), self._poisoned_on_night(3), self._poisoned_on_night(2)}
        self.assertEqual(2, len(worlds))

    def test_unsettled_is_ignored(self):
        world = Grimoire()
        other = world.clone()
        other.unsettled = set()
        self.assertEqual(world, other)
        self.assertEqual(hash(world), hash(other))

    def test_not_equal_to_other_types(self):
        self.assertNotEqual(Grimoire(), None)

class TestGetAllPoisonings(unittest.TestCase):
    def test_no_poison(self):
        self.assertEqual(frozenset(), Grimoire().get_all_poisonings())

    def test_lists_each_poisoning(self):
        world = Grimoire()
        world.pages[0].poisoned[1] = True
        world.add_page(3, NightOrderPosition.AFTER_IMP).poisoned[2] = True
        self.assertEqual(
            {(1, NightOrderPosition.AFTER_IMP, 1), (3, NightOrderPosition.AFTER_IMP, 2)},
            set(world.get_all_poisonings()),
        )

    def test_same_player_on_different_nights_differs(self):
        night2 = Grimoire()
        night2.add_page(2, NightOrderPosition.AFTER_IMP).poisoned[0] = True
        night3 = Grimoire()
        night3.add_page(3, NightOrderPosition.AFTER_IMP).poisoned[0] = True
        self.assertNotEqual(night2.get_all_poisonings(), night3.get_all_poisonings())

class TestStateWithoutPoison(unittest.TestCase):
    @staticmethod
    def _world() -> Grimoire:
        world = Grimoire()
        _ = world.add_page(5, NightOrderPosition.AFTER_IMP)
        return world

    def test_poison_on_an_existing_page_is_ignored(self):
        world = self._world()
        poisoned = world.clone()
        poisoned.pages[1].poisoned[0] = True
        self.assertEqual(world.state_without_poison(), poisoned.state_without_poison())

    def test_page_that_only_holds_poison_is_ignored(self):
        world = self._world()
        poisoned = world.clone()
        poisoned.add_page(3, NightOrderPosition.AFTER_IMP).poisoned[0] = True
        self.assertEqual(world.state_without_poison(), poisoned.state_without_poison())

    def test_first_page_counts(self):
        world = Grimoire()
        other = Grimoire()
        other.pages[0].characters[1] = Role.IMP
        self.assertNotEqual(world.state_without_poison(), other.state_without_poison())

    def test_later_page_counts(self):
        world = self._world()
        other = world.clone()
        other.pages[1].dead[1] = True
        self.assertNotEqual(world.state_without_poison(), other.state_without_poison())

    def test_same_change_on_different_nights_differs(self):
        def died_on(night: int) -> Grimoire:
            world = Grimoire()
            _ = world.add_page(2, NightOrderPosition.AFTER_IMP)
            _ = world.add_page(3, NightOrderPosition.AFTER_IMP)
            for page in world.pages:
                page.dead[0] = page.night >= night
            return world
        self.assertNotEqual(died_on(2).state_without_poison(), died_on(3).state_without_poison())

    def test_is_hashable_and_ignores_unsettled(self):
        world = self._world()
        settled = world.clone()
        settled.unsettled = set()
        self.assertEqual(hash(world.state_without_poison()), hash(settled.state_without_poison()))
        self.assertEqual(world.state_without_poison(), settled.state_without_poison())

class TestLooseEqualsPoison(unittest.TestCase):
    @staticmethod
    def _poisoned(player: int) -> Grimoire:
        world = Grimoire()
        world.pages[0].poisoned[player] = True
        return world

    def test_world_with_less_poison_still_matches_the_true_grim(self):
        self.assertTrue(self._poisoned(0).loose_equals(Grimoire()))

    def test_world_with_a_different_player_poisoned_does_not_match(self):
        self.assertFalse(self._poisoned(0).loose_equals(self._poisoned(1)))

class TestPassBetweenPages(unittest.TestCase):
    def test_pass_characters(self):
        # sanity check, same characters should be okay
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters[0] = Role.MONK
        night2.characters[0] = Role.MONK
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)

        # different characters should be invalid
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters[0] = Role.MONK
        night2.characters[0] = Role.SLAYER
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertFalse(result)

        # specific role -> non specific should be okay
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters[0] = Role.MONK
        night2.characters[0] = Role.ANY_OTHER_TOWNSFOLK
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)

        # non-specific role -> specific should be okay
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters[0] = Role.ANY_OTHER_EVIL
        night2.characters[0] = Role.SCARLET_WOMAN
        night2.minion_types[0] = Role.SCARLET_WOMAN
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)
        
        # 2 minions becoming demon is not okay
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        imp = 3
        minion1 = 0
        minion2 = 1
        prev.characters[minion1] = Role.BARON
        prev.characters[minion2] = Role.POISONER
        prev.characters[imp] = Role.IMP
        curr.characters[minion1] = Role.IMP
        curr.characters[minion2] = Role.IMP
        curr.dead[imp] = True
        curr.star_passed = True
        result, _reason, _ = Grimoire.pass_between_pages(prev, curr)
        self.assertFalse(result, "Expected 2 minions not able to become demon.")

        # any other evil to non-demon becomes any other minion
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters[0] = Role.ANY_OTHER_EVIL
        night2.characters[0] = Role.NON_DEMON
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)
        self.assertEqual(night2.characters[0], Role.ANY_OTHER_MINION)

        # same in reverse
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters[0] = Role.NON_DEMON
        night2.characters[0] = Role.ANY_OTHER_EVIL
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)
        self.assertEqual(night2.characters[0], Role.ANY_OTHER_MINION)

        # combined characters resulting in an invalid world should be invalid
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.characters = [Role.FORTUNE_TELLER, Role.NON_DEMON, Role.NON_DEMON, Role.ANY_OTHER, Role.ANY_OTHER]
        night2.characters = [Role.FORTUNE_TELLER, Role.ANY_OTHER, Role.ANY_OTHER, Role.NON_DEMON, Role.NON_DEMON]
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertFalse(result)

    def _starpass_pages(self, star_passed: bool) -> tuple[GrimoirePage, GrimoirePage]:
        # the Imp starpasses with a known Spy on one side and an unknown minion on the other
        prev = GrimoirePage(10)
        curr = GrimoirePage(10, 2)
        prev.characters[1] = Role.SPY
        prev.add_minion_type(Role.SPY)
        prev.characters[2] = Role.IMP
        prev.characters[3] = Role.ANY_OTHER_MINION
        curr.characters[1] = Role.ANY_OTHER_EVIL
        curr.characters[2] = Role.IMP
        curr.characters[3] = Role.ANY_OTHER_EVIL
        # without a starpass the Imp is still alive
        curr.dead[2] = star_passed
        curr.star_passed = star_passed
        return prev, curr

    def test_pass_known_minion_after_starpass(self):
        prev, curr = self._starpass_pages(star_passed=True)
        result, reason, _ = Grimoire.pass_between_pages(prev, curr)
        self.assertTrue(result, reason)
        self.assertEqual(curr.characters[1], Role.ANY_OTHER_EVIL, "Expected a known Spy to stay a possible new Imp after a starpass.")
        self.assertEqual(curr.characters[3], Role.ANY_OTHER_EVIL)

    def test_pass_known_minion_without_starpass(self):
        prev, curr = self._starpass_pages(star_passed=False)
        result, reason, _ = Grimoire.pass_between_pages(prev, curr)
        self.assertTrue(result, reason)
        self.assertEqual(curr.characters[1], Role.SPY, "Expected a known minion to be narrowed back without a starpass.")

    def test_pass_minion_types(self):
        # same minion types should be okay
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.minion_types = [Role.POISONER]
        night2.minion_types = [Role.POISONER]
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)

        # different minion types should be invalid
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.minion_types = [Role.POISONER]
        night2.minion_types = [Role.SCARLET_WOMAN]
        night1.minion_types[0] = Role.POISONER
        night2.minion_types[0] = Role.SCARLET_WOMAN
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertFalse(result)

        # specific minion type -> any other minion should be okay
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.minion_types = [Role.ANY_OTHER_MINION]
        night2.minion_types = [Role.POISONER]
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)

        # same in reverse
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.minion_types = [Role.POISONER]
        night2.minion_types = [Role.ANY_OTHER_MINION]
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)

    def test_pass_red_herring(self):
        # red herring should be passed through
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.red_herring[0] = True
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)
        self.assertTrue(night2.red_herring[0])

        # two red herrings is invalid
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.red_herring[0] = True
        night2.red_herring[1] = True
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertFalse(result)

    def test_pass_poisoned(self):
        # poisoned should not be passed through
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.poisoned[0] = True
        _result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertFalse(night2.poisoned[0])

    def test_pass_drunk_token(self):
        # drunk token should be passed through
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.drunk_token = Role.UNDERTAKER
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertTrue(result)
        self.assertEqual(night2.drunk_token, Role.UNDERTAKER)

        # different drunk token should be invalid
        world = Grimoire()
        night1 = world.pages[0]
        night2 = world.add_page(2, NightOrderPosition.AFTER_IMP)
        night1.drunk_token = Role.UNDERTAKER
        night2.drunk_token = Role.FORTUNE_TELLER
        result, _reason, _ = Grimoire.pass_between_pages(night1, night2)
        self.assertFalse(result)
        
class TestApply(unittest.TestCase):
    # TODO: add tests for apply starpass
    # TODO: add tests for apply sw catch
    pass

class TestMakeDeductions(unittest.TestCase):
    def test_settled_pages_return_false(self):
        world = Grimoire()
        world.get_first_page().characters = [Role.IMP, Role.SCARLET_WOMAN, Role.MONK, Role.EMPATH, Role.SLAYER]
        world.get_first_page().minion_types = [Role.SCARLET_WOMAN]
        _ = world.add_page(2, NightOrderPosition.AFTER_IMP)
        self.assertFalse(world.make_deductions(), "Expected no deductions when every page is settled.")

    def test_any_page_deducing_returns_true(self):
        world = Grimoire()
        world.get_first_page().characters = [Role.IMP, Role.SCARLET_WOMAN, Role.MONK, Role.EMPATH, Role.SLAYER]
        world.get_first_page().minion_types = [Role.SCARLET_WOMAN]
        page = world.add_page(2, NightOrderPosition.AFTER_IMP)
        page.characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        page.minion_types = [Role.POISONER]
        self.assertTrue(world.make_deductions(), "Expected deductions on the second page to be reported.")
        self.assertEqual(Role.IMP, page.characters[0])
        self.assertFalse(world.make_deductions(), "Expected no deductions once every page has settled.")

if __name__ == '__main__':
    _ = unittest.main()
