import unittest
from worldCreator import *
from world.world import *

class TestSolver5Player(unittest.TestCase):
    def test_investigator_washerwoman(self):
        ## 5 player game
        ## You are claiming to be the Investigator
        ## Your pings are players 2 and 3 as the Scarlet Woman
        ## What are the possible worlds?
        ## You are evil and lying
        ## You are the Drunk
        ## You were are the Investigator but was poisoned N1
        ## You are the Investigator and player 2 is the Scarlet Woman
        ## You are the Investigator and player 3 is the Scarlet Woman
        ## You are the Investigator and player 2 is the Recluse
        ## You are the Investigator and player 3 is the Recluse

        game: Game = {
            'players': 5
        }

        investigator_info: InvestigatorInfo = {
            'kind': "investigator",
            'investigator': 0,
            'first_player': 2,
            'second_player': 3,
            'minion': Role.SCARLET_WOMAN
        }

        investigator_worlds = create_worlds_from_investigator_info(game, investigator_info)

        ## Player 1 is claiming to be the Washerwoman who saw you and player 4 as the Investigator
        ## What are the possible worlds?
        ## Player 1 is the Drunk
        ## Player 1 is evil and lying
        ## Player 1 is the Washerwoman but was poisoned N1
        ## Player 1 is the Washerwoman and you are the Investigator
        ## Player 1 is the Washerwoman and player 4 is the Investigator
        ## Player 1 is the Washerwoman and you are the Spy
        ## Player 1 is the Washerwoman and player 4 is the Spy
        washerwoman_info: WasherwomanInfo = {
            'kind': "washerwoman",
            'washerwoman': 1,
            'first_player': 0,
            'second_player': 4,
            'townsfolk': Role.INVESTIGATOR
        }

        washerwoman_worlds = create_worlds_from_washerwoman_info(game, washerwoman_info)

        ## Combining these two sets of worlds together, what are the possible valid worlds and which worlds conflict?
        ## Possible worlds:
        ## You are the Drunk and player 1 is the Drunk - INVALID
        ## You are the Drunk and player 1 is Evil - VALID (1)
        ## You are the Drunk and player 1 is the Washerwoman and player 1 was poisoned - INVALID
        ## You are the Drunk and player 1 is the Washerwoman and you are the Investigator - INVALID
        ## You are the Drunk and player 1 is the Washerwoman and player 4 is the Investigator - INVALID
        ## You are the Drunk and player 1 is the Washerwoman and you are the Spy - INVALID
        ## You are the Drunk and player 1 is the Washerwoman and player 4 is the Spy - INVALID

        ## You are Evil and player 1 is the Drunk - VALID (2)
        ## You are Evil and player 1 is Evil - VALID
        ## You are Evil and player 1 is the Washerwoman and player 1 was poisoned - VALID (3)
        ## You are Evil and player 1 is the Washerwoman and you are the Investigator - INVALID
        ## You are Evil and player 1 is the Washerwoman and player 4 is the Investigator - VALID
        ## You are Evil and player 1 is the Washerwoman and you are the Spy - VALID
        ## You are Evil and player 1 is the Washerwoman and player 4 is the Spy - VALID

        ## You are the Investigator and you were poisoned and player 1 is the Drunk - INVALID
        ## You are the Investigator and you were poisoned and player 1 is Evil - VALID
        ## You are the Investigator and you were poisoned and player 1 is the Washerwoman and player 1 was poisoned - INVALID
        ## You are the Investigator and you were poisoned and player 1 is the Washerwoman and you are the Investigator - VALID
        ## You are the Investigator and you were poisoned and player 1 is the Washerwoman and player 4 is the Investigator - INVALID
        ## You are the Investigator and you were poisoned and player 1 is the Washerwoman and you are the Spy - INVALID
        ## You are the Investigator and you were poisoned and player 1 is the Washerwoman and player 4 is the Spy - INVALID

        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is the Drunk - INVALID
        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is Evil - VALID
        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is the Washerwoman and player 1 was poisoned - INVALID
        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is the Washerwoman and you are the Investigator - VALID
        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is the Washerwoman and player 4 is the Investigator - INVALID
        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is the Washerwoman and you are the Spy - INVALID
        ## You are the Investigator and player 2 is the Scarlet Woman and player 1 is the Washerwoman and player 4 is the Spy - INVALID

        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is the Drunk - INVALID
        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is Evil - VALID
        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is the Washerwoman and player 1 was poisoned - INVALID
        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is the Washerwoman and you are the Investigator - VALID
        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is the Washerwoman and player 4 is the Investigator - INVALID
        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is the Washerwoman and you are the Spy - INVALID
        ## You are the Investigator and player 3 is the Scarlet Woman and player 1 is the Washerwoman and player 4 is the Spy - INVALID

        ## You are the Investigator and player 2 is the Recluse and player 1 is the Drunk - VALID
        ## You are the Investigator and player 2 is the Recluse and player 1 is Evil - VALID
        ## You are the Investigator and player 2 is the Recluse and player 1 is the Washerwoman and player 1 was poisoned - INVALID
        ## You are the Investigator and player 2 is the Recluse and player 1 is the Washerwoman and you are the Investigator - VALID
        ## You are the Investigator and player 2 is the Recluse and player 1 is the Washerwoman and player 4 is the Investigator - INVALID
        ## You are the Investigator and player 2 is the Recluse and player 1 is the Washerwoman and you are the Spy - INVALID
        ## You are the Investigator and player 2 is the Recluse and player 1 is the Washerwoman and player 4 is the Spy - INVALID

        ## You are the Investigator and player 3 is the Recluse and player 1 is the Drunk - VALID
        ## You are the Investigator and player 3 is the Recluse and player 1 is Evil - VALID
        ## You are the Investigator and player 3 is the Recluse and player 1 is the Washerwoman and player 1 was poisoned - INVALID
        ## You are the Investigator and player 3 is the Recluse and player 1 is the Washerwoman and you are the Investigator - VALID
        ## You are the Investigator and player 3 is the Recluse and player 1 is the Washerwoman and player 4 is the Investigator - INVALID
        ## You are the Investigator and player 3 is the Recluse and player 1 is the Washerwoman and you are the Spy - INVALID
        ## You are the Investigator and player 3 is the Recluse and player 1 is the Washerwoman and player 4 is the Spy - INVALID
        ## Valid worlds: 20
        ## Invalid worlds: 29

        valid_worlds, conflicting_worlds = combine_worlds([investigator_worlds, washerwoman_worlds])

        self.assertEqual(len(valid_worlds), 19)
        self.assertEqual(len(conflicting_worlds), 30)

    def test_soldier_claim_execution_night_death(self):
        game: Game = {
            'players': 5
        }

        # Player 2 claims Soldier

        ## Possible worlds
        ## Player 2 is the Drunk
        ## Player 2 is Evil and lying
        ## Player 2 is the Soldier
        soldier_claim: Claim = {
            'kind': "claim",
            'player': 2,
            'character': Role.SOLDIER
        }

        soldier_worlds = create_worlds_from_claim(game, soldier_claim)

        # Player 2 is executed

        ## Possible worlds
        ## Player 2 is not the demon
        ## Player 2 is the demon with a Scarlet Woman who is now the demon
        executed_player = 2

        soldier_execution_worlds = create_worlds_from_execution(soldier_worlds, executed_player, 2)
        ## Player 0 dies in the night

        ## Possible worlds
        ## Player 0 is not the Imp
        ## Player 0 is the Imp who starpassed and a minion became the Imp
        player_killed = 0

        night_death_worlds = create_worlds_from_night_kill(soldier_execution_worlds, player_killed, 2)

        ## Combined worlds:
        ## Player 2 is the Drunk and Player 2 is not the demon and Player 0 is not the Imp - VALID (1)
        ## Player 2 is the Drunk and Player 2 is not the demon and Player 0 is the Imp who starpassed and a minion became the Imp - VALID (2)
        ## Player 2 is the Drunk and Player 2 is the demon with a Scarlet Woman who is now the demon and Player 0 is not the Imp - INVALID
        ## Player 2 is the Drunk and Player 2 is the demon with a Scarlet Woman who is now the demon and Player 0 is the Imp who starpassed and a minion became the Imp - INVALID (covered by previous)

        ## Player 2 is Evil and lying and Player 2 is not the demon and Player 0 is not the Imp - VALID (3)
        ## Player 2 is Evil and lying and Player 2 is not the demon and Player 0 is the Imp who starpassed and a minion became the Imp - INVALID (4)
        ## Player 2 is Evil and lying and Player 2 is the demon with a Scarlet Woman who is now the demon and Player 0 is not the Imp - VALID (5)
        ## Player 2 is Evil and lying and Player 2 is the demon with a Scarlet Woman who is now the demon and Player 0 is the Imp who starpassed and a minion became the Imp - INVALID
        
        ## Player 2 is the Soldier and Player 2 is not the demon and Player 0 is not the Imp - VALID (6? two phases for some reason)
        ## Player 2 is the Soldier and Player 2 is not the demon and Player 0 is the Imp who starpassed and a minion became the Imp - VALID (7)
        ## Player 2 is the Soldier and Player 2 is the demon with a Scarlet Woman who is now the demon and Player 0 is not the Imp - INVALID
        ## Player 2 is the Soldier and Player 2 is the demon with a Scarlet Woman who is now the demon and Player 0 is the Imp who starpassed and a minion became the Imp - INVALID (covered by previous)

        self.assertEqual(len(night_death_worlds), 6)

    def test_saint_claim_fortune_teller_claim(self):
        game: Game = {
            'players': 5
        }

        ## Player 4 claims Saint

        ## Possible worlds:
        ## Player 4 is Evil and lying
        ## Player 4 is the Saint
        saint_claim: Claim = {
            'kind': "claim",
            'player': 4,
            'character': Role.SAINT
        }

        saint_worlds = create_worlds_from_claim(game, saint_claim)

        ## Player 3 claims Fortune Teller

        ## Possible worlds for N1:
        ## Player 3 is the Drunk
        ## Player 3 is Evil and lying
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp

        ## Possible worlds for N2:
        ## Player 3 is the Drunk
        ## Player 3 is Evil and lying
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N2
        ## Player 3 is the Fortune Teller and Player 1 is the Demon
        ## Player 3 is the Fortune Teller and Player 4 is the Demon
        ## Player 3 is the Fortune Teller and Player 1 is the Red Herring and good
        ## Player 3 is the Fortune Teller and Player 4 is the Red Herring and good
        ## Player 3 is the Fortune Teller and Player 1 is the Red Herring and the Spy
        ## Player 3 is the Fortune Teller and Player 4 is the Red Herring and the Spy
        ## Player 3 is the Fortune Teller and Player 1 is the Recluse
        ## Player 3 is the Fortune Teller and Player 4 is the Recluse

        ## Combined Fortune Teller worlds:
        ## Player 3 is the Drunk and Player 3 is the Drunk - Valid
        ## Player 3 is the Drunk and Player 3 is Evil and lying - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 3 was poisoned N2 - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 1 is the Demon - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 4 is the Demon - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 1 is the Red Herring and good - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 4 is the Red Herring and good - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 1 is the Red Herring and the Spy - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 4 is the Red Herring and the Spy - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 1 is the Recluse - Invalid
        ## Player 3 is the Drunk and Player 3 is the Fortune Teller and Player 4 is the Recluse - Invalid

        ## Player 3 is Evil and lying and Player 3 is the Drunk - Invalid
        ## Player 3 is Evil and lying and Player 3 is Evil and lying - Valid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N2 - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 1 is the Demon - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 4 is the Demon - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 1 is the Red Herring and good - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 4 is the Red Herring and good - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 1 is the Red Herring and the Spy - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 4 is the Red Herring and the Spy - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 1 is the Recluse - Invalid
        ## Player 3 is Evil and lying and Player 3 is the Fortune Teller and Player 4 is the Recluse - Invalid

        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Drunk - Invalid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is Evil and lying - Invalid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 3 was poisoned N2 - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 1 is the Demon - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 4 is the Demon - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 1 is the Red Herring and good - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 4 is the Red Herring and good - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 1 is the Red Herring and the Spy - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 4 is the Red Herring and the Spy - Valid
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 1 is the Recluse - Invalid (outsider count)
        ## Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 3 is the Fortune Teller and Player 4 is the Recluse - Invalid

        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Drunk - Invalid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is Evil and lying - Invalid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 3 was poisoned N2 - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 1 is the Demon - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 4 is the Demon - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 1 is the Red Herring and good - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 4 is the Red Herring and good - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 1 is the Red Herring and the Spy - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 4 is the Red Herring and the Spy - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 1 is the Recluse - Valid
        ## Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 is the Fortune Teller and Player 4 is the Recluse - Valid

        fortune_teller_n1_info: FortuneTellerInfo = {
            'kind': "fortune teller",
            'fortune_teller': 3,
            'pings': ((0,2), False),
            'night': 1
        }
        fortune_teller_n2_info: FortuneTellerInfo = {
            'kind': "fortune teller",
            'fortune_teller': 3,
            'pings': ((1,4), True),
            'night': 2
        }

        fortune_teller_n1_worlds = create_worlds_from_fortune_teller_info(game, fortune_teller_n1_info)
        fortune_teller_n2_worlds = create_worlds_from_fortune_teller_info(game, fortune_teller_n2_info)
        fortune_teller_worlds, ft_invalid_worlds = combine_worlds([fortune_teller_n1_worlds, fortune_teller_n2_worlds])

        self.assertEqual(len(fortune_teller_worlds), 18)
        self.assertEqual(len(ft_invalid_worlds), 26)

        ## Combined Saint and Fortune Teller Worlds
        ## Player 4 is Evil and lying and Player 3 is the Drunk - Valid (1)
        ## Player 4 is Evil and lying and Player 3 is Evil and lying - Valid (2)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and and Player 3 was poisoned N2 - Valid (3)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 1 is the Demon - Valid (4)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 4 is the Demon - Valid (5)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 1 is the Red Herring and good - Valid (6)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 4 is the Red Herring and good - Invalid
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 1 is the Red Herring and the Spy - Valid (6)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 4 is the Red Herring and the Spy - Valid (7)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and and Player 3 was poisoned N2 - Valid (8)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Demon - Valid (9)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Demon - Valid (10)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Red Herring and good - Valid (11)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Red Herring and good - Invalid
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Red Herring and the Spy - Valid (12)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Red Herring and the Spy - Valid (13)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Recluse - Valid (14)
        ## Player 4 is Evil and lying and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Recluse - Invalid

        ## Player 4 is the Saint and Player 3 is the Drunk - Valid (12)
        ## Player 4 is the Saint and Player 3 is Evil and lying - Valid (13)
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and and Player 3 was poisoned N2 - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 1 is the Demon - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 4 is the Demon - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 1 is the Red Herring and good - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 4 is the Red Herring and good - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 1 is the Red Herring and the Spy - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 3 was poisoned N1 and Player 4 is the Red Herring and the Spy - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 3 was poisoned N2 - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Demon - Valid (14)
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Demon - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Red Herring and good - Invalid (no room for demon)
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Red Herring and good - Valid (16)
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Red Herring and the Spy - Invalid (no room for demon)
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Red Herring and the Spy - Invalid
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 1 is the Recluse - Invalid (no room for demon)
        ## Player 4 is the Saint and Player 3 is the Fortune Teller and Player 0 is not the Imp and Player 2 is not the Imp and Player 4 is the Recluse - Invalid
    
        valid_worlds, invalid_worlds = combine_worlds([saint_worlds, fortune_teller_worlds])
        self.assertEqual(len(valid_worlds), 19)
        self.assertEqual(len(invalid_worlds), 17)

    def test_sw_promotion(self):

        world = World()
        phase = world.phases[0]
        phase.characters[4] = Role.ANY_OTHER_MINION

        ## Possible worlds
        ## Player 2 is not the Imp
        ## Player 2 is the Imp and the Scarlet Woman is now the Imp
        executed_player = 2
        valid_worlds = create_worlds_from_execution([world], executed_player, 2)

        ## World 1: Player 2 is not the Imp and Player 4 is still the minion
        self.assertIn(Role.ANY_OTHER_MINION, valid_worlds[0].phases[0].minion_types)
        self.assertEqual(valid_worlds[0].phases[0].characters[2], Role.NON_DEMON)

        ## World 2: Player 2 is the Imp and Player 4 is now the Imp
        self.assertIn(Role.SCARLET_WOMAN, valid_worlds[1].phases[0].minion_types)
        # self.assertEqual(valid_worlds[1].phases[0].characters[2], Role.IMP) we can't know if the character was the imp the previous night (sw passes after exeucting imp then star passes to third minion)
        self.assertEqual(valid_worlds[1].phases[0].characters[4], Role.SCARLET_WOMAN)
        self.assertIn(Role.SCARLET_WOMAN, valid_worlds[1].phases[1].minion_types)
        self.assertEqual(valid_worlds[1].phases[1].characters[2], Role.IMP)
        self.assertEqual(valid_worlds[1].phases[1].characters[4], Role.IMP)

        world2 = World()
        phase2 = world2.phases[0]
        phase2.add_minion_type(Role.SPY)

        valid_worlds = create_worlds_from_execution([world2], executed_player, 2)

        ## Only valid world: Player 2 is not the Imp
        self.assertEqual(len(valid_worlds), 1)
        self.assertIn(Role.SPY, valid_worlds[0].phases[0].minion_types)
        self.assertEqual(valid_worlds[0].phases[0].characters[2], Role.NON_DEMON)

        world3 = World()
        phase3 = world3.phases[0]
        phase3.characters[2] = Role.IMP

        world4 = World()
        phase4 = world4.phases[0]
        phase4.characters[2] = Role.IMP
        phase4.characters[3] = Role.ANY_OTHER_MINION

        valid_worlds = create_worlds_from_execution([world3], executed_player, 2)
        self.assertEqual(len(valid_worlds), 1)
        world6, _ = World.combine(world4, valid_worlds[0])
        self.assertEqual(world6.phases[1].characters[2], Role.IMP)
        self.assertEqual(world6.phases[1].characters[3], Role.IMP)
        self.assertTrue(world6.phases[1].dead[2])


if __name__ == '__main__':
    _ = unittest.main()