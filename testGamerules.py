import unittest

from grimoire import Grimoire, gamerules
from grimoire.role import Role


class TestGameRules(unittest.TestCase):
    
    def test_validate_world(self):
        # Sanity test, simple world works
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.SCARLET_WOMAN, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        valid = gamerules.is_grim_valid(world)
        self.assertTrue(valid)

        # Only 1 alive imp is okay
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        valid = gamerules.is_grim_valid(world)
        self.assertFalse(valid)

        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.FORTUNE_TELLER, Role.SLAYER, Role.CHEF]
        phase.dead[1] = True
        valid = gamerules.is_grim_valid(world)
        self.assertTrue(valid)

        # More than 2 evils is not
        world = Grimoire()
        phase = world.pages[0]
        phase.characters = [Role.IMP, Role.IMP, Role.IMP, Role.SLAYER, Role.CHEF]
        phase.dead = [True, True, False, False, False]
        valid = gamerules.is_grim_valid(world)
        self.assertFalse(valid)

        
if __name__ == '__main__':
    _ = unittest.main()