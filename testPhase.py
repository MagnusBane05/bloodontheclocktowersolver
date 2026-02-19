import unittest

from world.phase import Phase
from world.role import *


class TestPhase(unittest.TestCase):
    def test_deduce_phase(self):
        # saninty check, a fully deduced world should have no changes made
        phase = Phase()
        phase.make_deductions(5)
        for i,c in enumerate(phase.characters):
            self.assertEqual(c,Role.ANY_OTHER, f"Player {i} has a non ANY_OTHER role ({c})")
        # saninty check, a fully unknown world should have no changes made
        phase = Phase()
        characters = [Role.IMP, Role.SCARLET_WOMAN, Role.MONK, Role.EMPATH, Role.SLAYER]
        phase.characters = characters
        phase.make_deductions(5)
        self.assertListEqual(phase.characters, characters)

        # if there is one unknown minion and minion types are known, assign the type to the minion
        # case with 1 minion
        phase = Phase()
        phase.characters[0] = Role.ANY_OTHER_MINION
        phase.minion_types = [Role.SCARLET_WOMAN]
        phase.make_deductions(5)
        self.assertEqual(Role.SCARLET_WOMAN, phase.characters[0])
        # case with known minions + 1 unknown minion
        phase = Phase(13)
        phase.characters[0] = Role.SCARLET_WOMAN
        phase.characters[1] = Role.SPY
        phase.characters[2] = Role.ANY_OTHER_MINION
        phase.minion_types = [Role.SCARLET_WOMAN, Role.SPY, Role.BARON]
        phase.make_deductions(13)
        self.assertEqual(Role.BARON, phase.characters[2])

        # if all good players are accounted for, assign evil roles to the unknown players
        phase = Phase()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER]
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_EVIL, phase.characters[3])
        self.assertEqual(Role.ANY_OTHER_EVIL, phase.characters[4])

        # if all good players are accounted for, non-demons should become any minion
        phase = Phase()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON, Role.ANY_OTHER]
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[3])

        # if there is only 1 spot left for an alive demon, assign Imp to that player
        # case with no dead players
        phase = Phase()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.NON_DEMON, Role.ANY_OTHER_MINION, Role.ANY_OTHER]
        phase.make_deductions(5)
        self.assertEqual(Role.IMP, phase.characters[4])
        # case with dead Imp
        phase = Phase()
        phase.characters = [Role.MONK, Role.ANY_OTHER_GOOD, Role.NON_DEMON, Role.ANY_OTHER, Role.IMP]
        phase.dead[4] = True
        phase.make_deductions(5)
        self.assertEqual(Role.IMP, phase.characters[3])

        # if the alive demon is known, assign minions to the other evil players
        # case with alive Imp
        phase = Phase()
        phase.characters[0] = Role.IMP
        phase.characters[1] = Role.ANY_OTHER_EVIL
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[1])
        # case with dead Imp and alive Imp
        phase = Phase(13)
        phase.characters[0] = Role.IMP
        phase.characters[1] = Role.IMP
        phase.dead[0] = True
        phase.characters[2] = Role.ANY_OTHER_EVIL
        phase.characters[3] = Role.ANY_OTHER_EVIL
        phase.make_deductions(13)
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[2])
        self.assertEqual(Role.ANY_OTHER_MINION, phase.characters[3])

        # if all minions are known and some players have NON_DEMON role, assign ANY_OTHER_GOOD to those players
        phase = Phase()
        phase.characters[0] = Role.ANY_OTHER_MINION
        phase.characters[1] = Role.NON_DEMON
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[1])

        # if all evils are known, assign ANY_OTHER_GOOD to NON_DEMON roles
        phase = Phase()
        phase.characters[0] = Role.ANY_OTHER_EVIL
        phase.characters[1] = Role.ANY_OTHER_EVIL
        phase.characters[2] = Role.NON_DEMON
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[2])

        # if all evils are accounted for, assign good roles to any unknowns
        phase = Phase()
        phase.characters = [Role.IMP, Role.ANY_OTHER_MINION, Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER, Role.ANY_OTHER]
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[3])
        self.assertEqual(Role.ANY_OTHER_GOOD, phase.characters[4])

        # if outsider count is known, assign leftover outsiders to unknown good players
        # case with Baron
        phase = Phase()
        phase.characters = [Role.BARON, Role.IMP, Role.MONK, Role.SAINT, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.BARON]
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_OUTSIDER, phase.characters[4])
        # case without Baron
        phase = Phase(6)
        phase.characters = [Role.SCARLET_WOMAN, Role.IMP, Role.ANY_OTHER_TOWNSFOLK, Role.MAYOR, Role.MONK, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.SCARLET_WOMAN]
        phase.make_deductions(6)
        self.assertEqual(Role.ANY_OTHER_OUTSIDER, phase.characters[5])
        # if outsider count is known, assign leftover townsfolk to unknown good players
        phase = Phase()
        phase.characters = [Role.POISONER, Role.IMP, Role.MONK, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.POISONER]
        phase.make_deductions(5)
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, phase.characters[3])
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, phase.characters[4])

        #TODO: deduce minion types from characters?
        #TODO: deduce evil / good players from chef number

        # multi-stage deductions
        phase = Phase()
        phase.characters = [Role.ANY_OTHER, Role.NON_DEMON, Role.MONK, Role.EMPATH, Role.ANY_OTHER_GOOD]
        phase.minion_types = [Role.POISONER]
        phase.make_deductions(5)
        self.assertEqual(Role.IMP, phase.characters[0])
        self.assertEqual(Role.POISONER, phase.characters[1])
        self.assertEqual(Role.ANY_OTHER_TOWNSFOLK, phase.characters[4])


if __name__ == "__main__":
    _ = unittest.main()