import unittest

from grimoire import gamerules, GrimoirePage, Role, NightOrderPosition



class TestScarletWomanCatch(unittest.TestCase):
    def test_can_scarlet_woman_catch(self):
        imp = 3
        page = GrimoirePage(10)        
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertTrue(result, "Expected blank pagee to be true.")

        scarlet_woman = 0
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        page.characters[imp] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertTrue(result, "Expected page with known Imp and Scarlet Woman to be true.")

        page.characters[imp] = Role.NON_DEMON
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertFalse(result, "Expected executing a non-demon to be false.")

        page.characters[imp] = Role.IMP
        page.dead[scarlet_woman] = True        
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertFalse(result, "Expected a page with a known dead Scalet Woman to be false.")

        page = GrimoirePage(10)
        page.minion_types = [Role.BARON, Role.POISONER]
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertFalse(result, "Expected a page with no room for a Scarlet Woman in the minion types to be false.")

        page = GrimoirePage(10)
        page.characters[0] = Role.ANY_OTHER_MINION
        page.characters[1] = Role.ANY_OTHER_MINION
        page.dead[0] = True
        page.dead[1] = True
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertFalse(result, "Expected a page with all minions dead to be false.")

        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[0] = Role.IMP
        page.characters[1] = Role.IMP
        page.characters[3] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertFalse(result, "Expected a page with no Scarlet Woman candidates to be false.")

        page = GrimoirePage(5)
        page.characters[0] = Role.IMP
        page.characters[2] = Role.ANY_OTHER_TOWNSFOLK
        page.characters[4] = Role.ANY_OTHER_TOWNSFOLK
        page.dead[0] = True
        result = gamerules.can_scarlet_woman_catch(page, imp, [])
        self.assertFalse(result, "Expected an unknown character being executed with all evils dead can't be the Imp.")

    def test_cannot_catch_after_an_earlier_imp_death(self):
        # a living Scarlet Woman takes the first Imp death, so she can't catch a later one
        imp = 3
        page = GrimoirePage(10)
        earlier = GrimoirePage(10)
        result = gamerules.can_scarlet_woman_catch(page, imp, [earlier])
        self.assertTrue(result, "Expected a catch with no earlier Imp death to be true.")

        earlier.star_passed = True
        result = gamerules.can_scarlet_woman_catch(page, imp, [earlier])
        self.assertFalse(result, "Expected a catch after an earlier Imp death to be false.")

        result = gamerules.can_scarlet_woman_catch(page, imp, [GrimoirePage(10), earlier, GrimoirePage(10)])
        self.assertFalse(result, "Expected an Imp death on any earlier page to make the catch false.")

    @staticmethod
    def _page_with_others_dead(imp: int, others_dead: int, imp_marked_dead: bool) -> GrimoirePage:
        page = GrimoirePage(10)
        others = [i for i in range(10) if i != imp]
        for i in others[:others_dead]:
            page.characters[i] = Role.NON_DEMON
            page.dead[i] = True
        page.dead[imp] = imp_marked_dead
        return page

    def test_catch_needs_five_alive_counting_the_dying_imp(self):
        imp = 3
        # the branch marks the Imp dead before asking, so both orders must give the same answer
        for imp_marked_dead in (False, True):
            with self.subTest(imp_marked_dead=imp_marked_dead):
                page = self._page_with_others_dead(imp, 4, imp_marked_dead)
                result = gamerules.can_scarlet_woman_catch(page, imp, [])
                self.assertTrue(result, "Expected a catch with 6 alive before the Imp dies to be true.")

                page = self._page_with_others_dead(imp, 5, imp_marked_dead)
                result = gamerules.can_scarlet_woman_catch(page, imp, [])
                self.assertTrue(result, "Expected a catch with exactly 5 alive before the Imp dies to be true.")

                page = self._page_with_others_dead(imp, 6, imp_marked_dead)
                result = gamerules.can_scarlet_woman_catch(page, imp, [])
                self.assertFalse(result, "Expected a catch with 4 alive before the Imp dies to be false.")

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

    def _pages(self, minion_role: Role, phase: NightOrderPosition) -> tuple[GrimoirePage, GrimoirePage]:
        minion = 0
        imp = 3
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        prev.characters[minion] = minion_role
        prev.characters[imp] = Role.IMP
        prev.dead[imp] = True
        curr.night_order_position = phase
        curr.characters[minion] = Role.ANY_OTHER_EVIL
        if phase == NightOrderPosition.AFTER_IMP:
            curr.star_passed = True
        elif phase == NightOrderPosition.AFTER_EXECUTION:
            curr.executee = imp
        else:
            curr.slayer_shot[imp] = True
        return prev, curr

    def test_known_minion(self):
        for minion_role in (Role.SPY, Role.POISONER, Role.BARON, Role.SCARLET_WOMAN):
            with self.subTest(minion_role=minion_role):
                prev, curr = self._pages(minion_role, NightOrderPosition.AFTER_IMP)
                self.assertTrue(
                    gamerules.can_non_demon_become_potential_demon(prev, curr, 0),
                    "Expected any known minion able to become a potential demon after a starpass.",
                )
        for phase in (NightOrderPosition.AFTER_EXECUTION, NightOrderPosition.AFTER_SLAYER):
            with self.subTest(phase=phase):
                prev, curr = self._pages(Role.POISONER, phase)
                self.assertFalse(
                    gamerules.can_non_demon_become_potential_demon(prev, curr, 0),
                    "Expected only a Scarlet Woman able to become the demon when the Imp is executed or slain.",
                )
                prev, curr = self._pages(Role.SCARLET_WOMAN, phase)
                self.assertTrue(
                    gamerules.can_non_demon_become_potential_demon(prev, curr, 0),
                    "Expected a known Scarlet Woman able to become a potential demon when the Imp is executed or slain.",
                )

class TestScarletWomanTakesTheFirstStarpass(unittest.TestCase):
    """At the first Imp death, a night starpass with 5 or more alive goes to the Scarlet Woman if
    she's in play, so a known Poisoner, Spy or Baron can't take it unless she might already be dead."""
    heir = 0
    imp = 3

    def _pages(
        self,
        heir_role: Role,
        minion_types: list[Role],
        heir_after: Role = Role.IMP,
        dead_before: dict[int, Role] | None = None,
    ) -> tuple[GrimoirePage, GrimoirePage]:
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        for page in (prev, curr):
            page.minion_types = list(minion_types)
            for player, role in (dead_before or {}).items():
                page.characters[player] = role
                page.dead[player] = True
        prev.characters[self.heir] = heir_role
        prev.characters[self.imp] = Role.IMP
        curr.characters[self.heir] = heir_after
        curr.characters[self.imp] = Role.IMP
        curr.dead[self.imp] = True
        curr.star_passed = True
        return prev, curr

    def _can_take_over(self, *args: object, **kwargs: object) -> bool:
        prev, curr = self._pages(*args, **kwargs)  # pyright: ignore[reportArgumentType]
        return gamerules.can_minion_become_demon(prev, curr, self.heir)

    def _can_become_potential_demon(self, heir_role: Role, minion_types: list[Role], **kwargs: object) -> bool:
        prev, curr = self._pages(heir_role, minion_types, Role.ANY_OTHER_EVIL, **kwargs)  # pyright: ignore[reportArgumentType]
        return gamerules.can_non_demon_become_potential_demon(prev, curr, self.heir)

    def test_known_minion_cant_take_it(self):
        for role in (Role.POISONER, Role.SPY, Role.BARON):
            with self.subTest(role=role):
                self.assertFalse(self._can_take_over(role, [role, Role.SCARLET_WOMAN]))
                self.assertFalse(self._can_become_potential_demon(role, [role, Role.SCARLET_WOMAN]))

    def test_without_a_scarlet_woman(self):
        self.assertTrue(self._can_take_over(Role.SPY, [Role.SPY, Role.POISONER]))
        self.assertTrue(self._can_take_over(Role.SPY, [Role.SPY, Role.ANY_OTHER_MINION]))
        self.assertTrue(self._can_become_potential_demon(Role.SPY, [Role.SPY, Role.POISONER]))

    def test_the_scarlet_woman_or_an_unknown_minion_can_take_it(self):
        self.assertTrue(self._can_take_over(Role.SCARLET_WOMAN, [Role.SPY, Role.SCARLET_WOMAN]))
        self.assertTrue(self._can_take_over(Role.ANY_OTHER_MINION, [Role.SPY, Role.SCARLET_WOMAN]))
        for role in (Role.SCARLET_WOMAN, Role.ANY_OTHER_MINION, Role.NON_DEMON):
            with self.subTest(role=role):
                self.assertTrue(self._can_become_potential_demon(role, [Role.SPY, Role.SCARLET_WOMAN]))

    def test_five_alive_before_the_imp_dies(self):
        # dead known good players can't have been the Scarlet Woman, so only the count matters
        five_alive = {p: Role.ANY_OTHER_TOWNSFOLK for p in (4, 5, 6, 7, 8)}
        four_alive = five_alive | {9: Role.ANY_OTHER_TOWNSFOLK}
        types = [Role.SPY, Role.SCARLET_WOMAN]
        self.assertFalse(self._can_take_over(Role.SPY, types, dead_before=five_alive))
        self.assertTrue(self._can_take_over(Role.SPY, types, dead_before=four_alive))
        self.assertTrue(self._can_become_potential_demon(Role.SPY, types, dead_before=four_alive))

    def test_after_an_earlier_imp_death(self):
        types = [Role.SPY, Role.SCARLET_WOMAN]
        self.assertTrue(self._can_take_over(Role.SPY, types, dead_before={5: Role.IMP}))
        self.assertTrue(self._can_become_potential_demon(Role.SPY, types, dead_before={5: Role.IMP}))

    def test_she_might_already_be_dead(self):
        types = [Role.SPY, Role.SCARLET_WOMAN]
        for role in (Role.SCARLET_WOMAN, Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON):
            with self.subTest(role=role):
                self.assertTrue(self._can_take_over(Role.SPY, types, dead_before={5: role}))
                self.assertTrue(self._can_become_potential_demon(Role.SPY, types, dead_before={5: role}))

    def test_dead_good_player_doesnt_matter(self):
        types = [Role.SPY, Role.SCARLET_WOMAN]
        self.assertFalse(self._can_take_over(Role.SPY, types, dead_before={5: Role.ANY_OTHER_TOWNSFOLK}))

    def test_living_named_scarlet_woman(self):
        types = [Role.SPY, Role.SCARLET_WOMAN]
        prev, curr = self._pages(Role.SPY, types, dead_before={6: Role.ANY_OTHER})
        for page in (prev, curr):
            page.characters[5] = Role.SCARLET_WOMAN
        self.assertFalse(
            gamerules.can_minion_become_demon(prev, curr, self.heir),
            "Expected a living named Scarlet Woman to take the starpass even when an unknown player is dead.",
        )

    def test_living_named_scarlet_woman_with_four_alive(self):
        four_alive = {p: Role.ANY_OTHER_TOWNSFOLK for p in (1, 4, 6, 7, 8, 9)}
        types = [Role.SPY, Role.SCARLET_WOMAN]
        prev, curr = self._pages(Role.SPY, types, dead_before=four_alive)
        for page in (prev, curr):
            page.characters[5] = Role.SCARLET_WOMAN
        self.assertTrue(
            gamerules.can_minion_become_demon(prev, curr, self.heir),
            "Expected the Scarlet Woman not to take the starpass with fewer than 5 alive.",
        )

class TestDyingPlayerIsNotTheNewImp(unittest.TestCase):
    """The player who dies on a page was already the Imp, so they aren't the minion who took over."""
    minion = 0
    imp = 3

    def _pages(self, phase: NightOrderPosition, dying: int) -> tuple[GrimoirePage, GrimoirePage]:
        prev = GrimoirePage(10)
        curr = GrimoirePage(10)
        for page in (prev, curr):
            page.minion_types = [Role.SCARLET_WOMAN, Role.ANY_OTHER_MINION]
        prev.characters[self.minion] = Role.SCARLET_WOMAN
        prev.characters[self.imp] = Role.IMP
        curr.night_order_position = phase
        curr.characters[self.minion] = Role.IMP
        curr.characters[self.imp] = Role.IMP
        curr.dead[dying] = True
        if phase == NightOrderPosition.AFTER_IMP:
            curr.star_passed = True
        elif phase == NightOrderPosition.AFTER_EXECUTION:
            curr.executee = dying
        else:
            curr.slayer_shot[dying] = True
        return prev, curr

    def test_dying_minion_cant_become_the_imp(self):
        for phase in (NightOrderPosition.AFTER_IMP, NightOrderPosition.AFTER_EXECUTION, NightOrderPosition.AFTER_SLAYER):
            with self.subTest(phase=phase):
                prev, curr = self._pages(phase, self.minion)
                self.assertFalse(gamerules.can_minion_become_demon(prev, curr, self.minion))

    def test_living_minion_can_take_over_from_the_dying_imp(self):
        for phase in (NightOrderPosition.AFTER_IMP, NightOrderPosition.AFTER_EXECUTION, NightOrderPosition.AFTER_SLAYER):
            with self.subTest(phase=phase):
                prev, curr = self._pages(phase, self.imp)
                self.assertTrue(gamerules.can_minion_become_demon(prev, curr, self.minion))

class TestCanPlayerBeAlivePoisoner(unittest.TestCase):
    @staticmethod
    def _page(character: Role, minion_types: list[Role] | None = None) -> GrimoirePage:
        page = GrimoirePage(10)
        page.minion_types = list(minion_types or [Role.POISONER, Role.ANY_OTHER_MINION])
        page.characters[0] = character
        return page

    def test_roles_that_could_be_the_poisoner(self):
        for role in (Role.POISONER, Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.NON_DEMON, Role.ANY_OTHER):
            with self.subTest(role=role):
                self.assertTrue(gamerules.can_player_be_alive_poisoner(self._page(role), 0))

    def test_roles_that_cant(self):
        for role in (Role.IMP, Role.SPY, Role.SCARLET_WOMAN, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.EMPATH):
            with self.subTest(role=role):
                self.assertFalse(gamerules.can_player_be_alive_poisoner(self._page(role), 0))

    def test_dead(self):
        page = self._page(Role.POISONER)
        page.dead[0] = True
        self.assertFalse(gamerules.can_player_be_alive_poisoner(page, 0))

    def test_poisoner_not_in_minion_types(self):
        page = self._page(Role.ANY_OTHER, [Role.ANY_OTHER_MINION, Role.ANY_OTHER_MINION])
        self.assertFalse(
            gamerules.can_player_be_alive_poisoner(page, 0),
            "Expected the Poisoner to have to be a known minion type.",
        )

    def test_known_poisoner_elsewhere(self):
        # a dead known Poisoner is rejected by the validator before this is asked
        page = self._page(Role.ANY_OTHER)
        page.characters[1] = Role.POISONER
        self.assertTrue(gamerules.can_player_be_alive_poisoner(page, 1))

if __name__ == '__main__':
    _ = unittest.main()
