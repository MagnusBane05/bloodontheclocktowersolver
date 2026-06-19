import unittest

from grimoire import Role, get_overlapping

class TestRole(unittest.TestCase):  
  def test_get_overlapping_specific(self):
    ## Valid cases

    # Specific role with any other
    specific = get_overlapping(Role.LIBRARIAN, Role.ANY_OTHER, True)
    self.assertEqual(specific, Role.LIBRARIAN)

    # Specific non-demon role with non-demon
    specific = get_overlapping(Role.NON_DEMON, Role.SPY, True)
    self.assertEqual(specific, Role.SPY)

    # Specific good role with any other good
    specific = get_overlapping(Role.MAYOR, Role.ANY_OTHER_GOOD, True)
    self.assertEqual(specific, Role.MAYOR)

    # Specific evil role with any other evil
    specific = get_overlapping(Role.ANY_OTHER_EVIL, Role.POISONER, True)
    self.assertEqual(specific, Role.POISONER)

    # Specific outsider with any other outsider
    specific = get_overlapping(Role.DRUNK, Role.ANY_OTHER_OUTSIDER, True)
    self.assertEqual(specific, Role.DRUNK)

    # Specific townsfolk with any other townsfolk
    specific = get_overlapping(Role.ANY_OTHER_TOWNSFOLK, Role.MONK, True)
    self.assertEqual(specific, Role.MONK)

    # Specific minion with any other minion
    specific = get_overlapping(Role.ANY_OTHER_MINION, Role.SPY, True)
    self.assertEqual(specific, Role.SPY)

    # Any other evil with any other
    specific = get_overlapping(Role.ANY_OTHER_EVIL, Role.ANY_OTHER, True)
    self.assertEqual(specific, Role.ANY_OTHER_EVIL)

    # Any other evil with non-demon becomes any other minion
    specific = get_overlapping(Role.NON_DEMON, Role.ANY_OTHER_EVIL, True)
    self.assertEqual(specific, Role.ANY_OTHER_MINION)

    # Any other townsfolk with any other good
    specific = get_overlapping(Role.ANY_OTHER_TOWNSFOLK, Role.ANY_OTHER_GOOD, True)
    self.assertEqual(specific, Role.ANY_OTHER_TOWNSFOLK)

    ## Invalid cases

    # Two different specific roles
    specific = get_overlapping(Role.MAYOR, Role.MONK, True)
    self.assertIsNone(specific)

    # Specific evil role with any other good
    specific = get_overlapping(Role.ANY_OTHER_GOOD, Role.POISONER, True)
    self.assertIsNone(specific)

    # Specific good role with any other evil
    specific = get_overlapping(Role.MAYOR, Role.ANY_OTHER_EVIL, True)
    self.assertIsNone(specific)

    # Imp with non-demon
    specific = get_overlapping(Role.NON_DEMON, Role.IMP, True)
    self.assertIsNone(specific)

    # Specific outsider with any other townsfolk
    specific = get_overlapping(Role.ANY_OTHER_TOWNSFOLK, Role.DRUNK, True)
    self.assertIsNone(specific)

    # Specific townsfolk with any other outsider
    specific = get_overlapping(Role.ANY_OTHER_OUTSIDER, Role.MONK, True)
    self.assertIsNone(specific)

    # Specific townsfolk with any other minion
    specific = get_overlapping(Role.ANY_OTHER_MINION, Role.MONK, True)
    self.assertIsNone(specific)

if __name__ == '__main__':
    _ = unittest.main()