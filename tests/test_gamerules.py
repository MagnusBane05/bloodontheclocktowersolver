import unittest

from grimoire import gamerules, GrimoirePage, Role, NightOrderPosition



class TestScarletWomanCatch(unittest.TestCase):
    def test_can_scarlet_woman_catch(self):
        imp = 3
        page = GrimoirePage(10)        
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertTrue(result, "Expected blank pagee to be true.")

        scarlet_woman = 0
        page.characters[scarlet_woman] = Role.SCARLET_WOMAN
        page.characters[imp] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertTrue(result, "Expected page with known Imp and Scarlet Woman to be true.")

        page.characters[imp] = Role.NON_DEMON
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected executing a non-demon to be false.")

        page.characters[imp] = Role.IMP
        page.dead[scarlet_woman] = True        
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with a known dead Scalet Woman to be false.")

        page = GrimoirePage(10)
        page.minion_types = [Role.BARON, Role.POISONER]
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with no room for a Scarlet Woman in the minion types to be false.")

        page = GrimoirePage(10)
        page.characters[0] = Role.ANY_OTHER_MINION
        page.characters[1] = Role.ANY_OTHER_MINION
        page.dead[0] = True
        page.dead[1] = True
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with all minions dead to be false.")

        page.characters = [Role.ANY_OTHER_GOOD] * 10
        page.characters[0] = Role.IMP
        page.characters[1] = Role.IMP
        page.characters[3] = Role.IMP
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected a page with no Scarlet Woman candidates to be false.")

        page = GrimoirePage(5)
        page.characters[0] = Role.IMP
        page.characters[2] = Role.ANY_OTHER_TOWNSFOLK
        page.characters[4] = Role.ANY_OTHER_TOWNSFOLK
        page.dead[0] = True
        result = gamerules.can_scarlet_woman_catch(page, imp)
        self.assertFalse(result, "Expected an unknown character being executed with all evils dead can't be the Imp.")

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

if __name__ == '__main__':
    _ = unittest.main()
