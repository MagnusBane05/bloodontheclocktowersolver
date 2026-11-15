import unittest
from typing import Any

from bench.scenarios import load_scenarios
from bench.world_validator import covers, find_world_problem
from grimoire import Grimoire, NightOrderPosition, Role
from grimoire.info import DeathInfo, Info

AFTER_IMP = NightOrderPosition.AFTER_IMP
AFTER_SLAYER = NightOrderPosition.AFTER_SLAYER
AFTER_EXECUTION = NightOrderPosition.AFTER_EXECUTION
_ORDERS = {"demon": AFTER_IMP, "slayer": AFTER_SLAYER, "execution": AFTER_EXECUTION}

# 5 players, no Baron: 3 townsfolk, 1 minion, 1 demon
BASE = [Role.IMP, Role.POISONER, Role.CHEF, Role.EMPATH, Role.MONK]

def world(
    characters: list[Role],
    deaths: list[DeathInfo] = [],
    nights: int = 1,
    minion_types: list[Role] | None = None,
    later: dict[tuple[int, NightOrderPosition], list[Role]] = {},
    poisoned: dict[int, int] = {},
    red_herring: int | None = None,
    drunk_token: Role | None = None,
) -> Grimoire:
    """A world with a page for every night, every death, and the given character changes.
    `poisoned` maps night to the poisoned player and is marked on every page of that night."""
    grim = Grimoire(len(characters))
    keys = {(night, AFTER_IMP) for night in range(1, nights + 1)}
    keys |= {(d["night"], _ORDERS[d["kind"]]) for d in deaths}
    for night, order in sorted(keys - {(1, AFTER_IMP)}):
        _ = grim.add_page(night, order)
    current = list(characters)
    for page in grim.pages:
        key = (page.night, page.night_order_position)
        if key in later:
            current = list(later[key])
        page.characters = list(current)
        if minion_types is None:
            named = [c for c in characters if c in {Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN}]
            minion_types = named + [Role.ANY_OTHER_MINION] * (len(page.minion_types) - len(named))
        page.minion_types = list(minion_types)
        page.dead = [any(d["player"] == p and (d["night"], _ORDERS[d["kind"]]) <= key for d in deaths) for p in range(len(characters))]
        page.poisoned = [poisoned.get(page.night) == p for p in range(len(characters))]
        page.red_herring = [red_herring == p for p in range(len(characters))]
        page.drunk_token = drunk_token
    return grim

def claim(player: int, character: Role) -> Info:
    return {"kind": "claim", "player": player, "character": character}

def death(kind: str, player: int, night: int) -> DeathInfo:
    return {"kind": kind, "player": player, "night": night}  # pyright: ignore[reportReturnType]

def info(kind: str, **fields: Any) -> Info:
    return {"kind": kind, **fields}  # pyright: ignore[reportReturnType]

def problem(grim: Grimoire, infos: list[Info], deaths: list[DeathInfo] = [], nights: int = 1) -> str | None:
    return find_world_problem(grim, infos, deaths, nights)

class WorldValidatorCase(unittest.TestCase):
    def assertValid(self, grim: Grimoire, infos: list[Info], deaths: list[DeathInfo] = [], nights: int = 1):
        self.assertIsNone(problem(grim, infos, deaths, nights))

    def assertInvalid(self, grim: Grimoire, infos: list[Info], deaths: list[DeathInfo] = [], nights: int = 1, reason: str = ""):
        found = problem(grim, infos, deaths, nights)
        self.assertIsNotNone(found, "Expected the world to be rejected.")
        self.assertIn(reason, found)

class TestTrueGrims(unittest.TestCase):
    def test_every_true_grim_is_valid(self):
        failures: list[str] = []
        for players in (5, 10, 15):
            for s in load_scenarios(players):
                found = find_world_problem(s.true_grim, s.info, s.deaths, s.nights)
                if found is not None:
                    failures.append(f"{s.id}: {found}")
        self.assertEqual(failures, [])

class TestCovers(unittest.TestCase):
    def test_generic_roles(self):
        self.assertTrue(covers(Role.NON_DEMON, Role.SPY))
        self.assertFalse(covers(Role.NON_DEMON, Role.IMP))
        self.assertTrue(covers(Role.ANY_OTHER_GOOD, Role.DRUNK))
        self.assertFalse(covers(Role.ANY_OTHER_TOWNSFOLK, Role.DRUNK))
        self.assertFalse(covers(Role.ANY_OTHER_MINION, Role.IMP))

class TestSetup(WorldValidatorCase):
    def test_counts(self):
        self.assertValid(world(BASE), [])
        self.assertInvalid(world([Role.IMP, Role.POISONER, Role.CHEF, Role.EMPATH, Role.SAINT]), [])

    def test_baron_adds_two_outsiders(self):
        self.assertValid(world([Role.IMP, Role.BARON, Role.SAINT, Role.RECLUSE, Role.CHEF]), [])
        self.assertInvalid(world([Role.IMP, Role.BARON, Role.SAINT, Role.MONK, Role.CHEF]), [])

    def test_generic_roles_resolve(self):
        self.assertValid(world([Role.ANY_OTHER] * 5), [])
        self.assertInvalid(world([Role.ANY_OTHER_EVIL] * 3 + [Role.ANY_OTHER] * 2), [])

    def test_minion_types_in_play(self):
        self.assertValid(world(BASE, minion_types=[Role.POISONER]), [])
        self.assertInvalid(world(BASE, minion_types=[Role.SPY]), [], reason="minion type")

    def test_drunk_token(self):
        drunk = [Role.IMP, Role.BARON, Role.DRUNK, Role.RECLUSE, Role.CHEF]
        self.assertValid(world(drunk, drunk_token=Role.EMPATH), [claim(2, Role.EMPATH)])
        # the Drunk's token can't be in play
        self.assertInvalid(world(drunk, drunk_token=Role.CHEF), [claim(2, Role.CHEF)], reason="Drunk")
        # a Drunk token with no Drunk
        self.assertInvalid(world(BASE, drunk_token=Role.EMPATH), [], reason="Drunk token")

class TestGoodPlayersDontLie(WorldValidatorCase):
    def test_claim_matches_character(self):
        self.assertValid(world(BASE), [claim(2, Role.CHEF)])
        self.assertInvalid(world(BASE), [claim(2, Role.MONK)])

    def test_evil_can_claim_anything(self):
        self.assertValid(world(BASE), [claim(1, Role.MONK)])

    def test_two_claims_means_evil(self):
        self.assertValid(world([Role.ANY_OTHER] * 5), [claim(1, Role.MONK), claim(1, Role.CHEF)])
        self.assertInvalid(world([Role.IMP, Role.POISONER, Role.ANY_OTHER_GOOD, Role.EMPATH, Role.MONK]), [claim(2, Role.MONK), claim(2, Role.CHEF)], reason="no character fits")

    def test_drunk_claims_their_token(self):
        drunk = [Role.IMP, Role.BARON, Role.DRUNK, Role.RECLUSE, Role.CHEF]
        self.assertValid(world(drunk), [claim(2, Role.EMPATH)])
        self.assertInvalid(world(drunk), [claim(2, Role.SAINT)])

class TestFirstNightInfo(WorldValidatorCase):
    def test_washerwoman(self):
        grim = world([Role.IMP, Role.POISONER, Role.WASHERWOMAN, Role.EMPATH, Role.MONK])
        self.assertValid(grim, [info("washerwoman", washerwoman=2, first_player=3, second_player=0, townsfolk=Role.EMPATH)])
        self.assertInvalid(grim, [info("washerwoman", washerwoman=2, first_player=3, second_player=0, townsfolk=Role.CHEF)], reason="Washerwoman")

    def test_washerwoman_sees_spy_as_townsfolk(self):
        grim = world([Role.IMP, Role.SPY, Role.WASHERWOMAN, Role.EMPATH, Role.MONK])
        self.assertValid(grim, [info("washerwoman", washerwoman=2, first_player=1, second_player=0, townsfolk=Role.CHEF)])

    def test_poisoned_washerwoman_can_be_wrong(self):
        characters = [Role.IMP, Role.POISONER, Role.WASHERWOMAN, Role.EMPATH, Role.MONK]
        wrong = [info("washerwoman", washerwoman=2, first_player=3, second_player=0, townsfolk=Role.CHEF)]
        self.assertValid(world(characters, poisoned={1: 2}), wrong)

    def test_investigator_sees_recluse_as_minion(self):
        grim = world([Role.IMP, Role.BARON, Role.INVESTIGATOR, Role.RECLUSE, Role.SAINT])
        self.assertValid(grim, [info("investigator", investigator=2, first_player=3, second_player=4, minion=Role.POISONER)])
        self.assertInvalid(grim, [info("investigator", investigator=2, first_player=4, second_player=0, minion=Role.POISONER)], reason="Investigator")

    def test_librarian_zero(self):
        self.assertValid(world([Role.IMP, Role.POISONER, Role.LIBRARIAN, Role.EMPATH, Role.MONK]), [info("librarian", librarian=2, first_player=None, second_player=None, token=None)])
        baron = [Role.IMP, Role.BARON, Role.LIBRARIAN, Role.SAINT, Role.RECLUSE]
        self.assertInvalid(world(baron), [info("librarian", librarian=2, first_player=None, second_player=None, token=None)], reason="zero")

    def test_librarian_zero_hides_recluse(self):
        # 6 players have 1 outsider; a Recluse can register as a minion
        grim = world([Role.IMP, Role.POISONER, Role.LIBRARIAN, Role.RECLUSE, Role.MONK, Role.CHEF])
        self.assertValid(grim, [info("librarian", librarian=2, first_player=None, second_player=None, token=None)])

    def test_chef(self):
        grim = world([Role.IMP, Role.POISONER, Role.CHEF, Role.EMPATH, Role.MONK])
        self.assertValid(grim, [info("chef", chef=2, number=1)])
        self.assertInvalid(grim, [info("chef", chef=2, number=0)], reason="Chef")

    def test_chef_recluse_registers_per_pair(self):
        # Baron, Recluse, Imp in a row: the Recluse can count as evil for one pair only
        grim = world([Role.BARON, Role.RECLUSE, Role.IMP, Role.SAINT, Role.CHEF])
        for number in (0, 1, 2):
            self.assertValid(grim, [info("chef", chef=4, number=number)])
        self.assertInvalid(grim, [info("chef", chef=4, number=3)], reason="Chef")

class TestDeaths(WorldValidatorCase):
    def test_no_kill_on_night_one(self):
        deaths = [death("demon", 3, 1)]
        self.assertInvalid(world(BASE, deaths), [], deaths, reason="night 1")

    def test_soldier_survives_the_imp(self):
        characters = [Role.IMP, Role.POISONER, Role.SOLDIER, Role.EMPATH, Role.MONK]
        deaths = [death("execution", 3, 1), death("demon", 2, 2)]
        self.assertInvalid(world(characters, deaths, nights=2), [], deaths, nights=2, reason="Soldier")
        self.assertValid(world(characters, deaths, nights=2, poisoned={2: 2}), [], deaths, nights=2)

    def test_quiet_night_needs_a_reason(self):
        characters = [Role.IMP, Role.POISONER, Role.CHEF, Role.EMPATH, Role.WASHERWOMAN]
        self.assertInvalid(world(characters, nights=2), [], [], nights=2, reason="no one died")
        # the Imp chose a dead player
        deaths = [death("execution", 3, 1)]
        self.assertValid(world(characters, deaths, nights=2), [], deaths, nights=2)
        # a sober Monk protected someone
        self.assertValid(world(BASE, nights=2), [], [], nights=2)
        self.assertInvalid(world(BASE, nights=2, poisoned={2: 4}), [], [], nights=2, reason="no one died")

    def test_sober_saint_execution_loses(self):
        characters = [Role.IMP, Role.BARON, Role.SAINT, Role.RECLUSE, Role.CHEF]
        deaths = [death("execution", 2, 1)]
        self.assertInvalid(world(characters, deaths), [], deaths, reason="Saint")

    def test_two_alive_ends_the_game(self):
        deaths = [death("execution", 3, 1), death("demon", 4, 2), death("execution", 2, 2)]
        self.assertInvalid(world(BASE, deaths, nights=2), [], deaths, nights=2, reason="game is over")

    def test_deaths_match_pages(self):
        deaths = [death("execution", 3, 1)]
        grim = world(BASE, deaths)
        grim.pages[-1].dead = [False] * 5
        self.assertInvalid(grim, [], deaths, reason="deaths don't match")

class TestDemonDeaths(WorldValidatorCase):
    SW = [Role.IMP, Role.SCARLET_WOMAN, Role.CHEF, Role.EMPATH, Role.MONK]

    def test_executed_imp_needs_a_scarlet_woman(self):
        deaths = [death("execution", 0, 1)]
        caught = {(1, AFTER_EXECUTION): [Role.IMP, Role.IMP, Role.CHEF, Role.EMPATH, Role.MONK]}
        self.assertValid(world(self.SW, deaths, later=caught), [], deaths)
        self.assertInvalid(world(BASE, deaths, later={(1, AFTER_EXECUTION): [Role.IMP, Role.IMP, Role.CHEF, Role.EMPATH, Role.MONK]}), [], deaths, reason="good won")

    def test_scarlet_woman_needs_five_alive(self):
        deaths = [death("execution", 3, 1), death("execution", 0, 2)]
        caught = {(2, AFTER_EXECUTION): [Role.IMP, Role.IMP, Role.CHEF, Role.EMPATH, Role.MONK]}
        self.assertInvalid(world(self.SW, deaths, nights=2, later=caught), [], deaths, nights=2, reason="good won")

    def test_starpass(self):
        deaths = [death("execution", 3, 1), death("demon", 0, 2)]
        passed = {(2, AFTER_IMP): [Role.IMP, Role.IMP, Role.CHEF, Role.EMPATH, Role.MONK]}
        self.assertValid(world(BASE, deaths, nights=2, later=passed), [], deaths, nights=2)
        # the page must show who became the Imp
        self.assertInvalid(world(BASE, deaths, nights=2), [], deaths, nights=2, reason="not POISONER")

    def test_starpass_must_go_to_scarlet_woman(self):
        # 10 players: 7 townsfolk, 2 minions, 1 demon
        ten = [Role.IMP, Role.SCARLET_WOMAN, Role.CHEF, Role.EMPATH, Role.MONK, Role.POISONER, Role.SOLDIER, Role.MAYOR, Role.VIRGIN, Role.SLAYER]
        deaths = [death("demon", 0, 2)]
        to_sw = {(2, AFTER_IMP): [Role.IMP, Role.IMP] + ten[2:]}
        to_poisoner = {(2, AFTER_IMP): ten[:5] + [Role.IMP] + ten[6:]}
        self.assertValid(world(ten, deaths, nights=2, later=to_sw), [], deaths, 2)
        self.assertInvalid(world(ten, deaths, nights=2, later=to_poisoner), [], deaths, 2)

class TestPoison(WorldValidatorCase):
    def test_needs_an_alive_poisoner(self):
        characters = [Role.IMP, Role.SPY, Role.CHEF, Role.EMPATH, Role.MONK]
        self.assertInvalid(world(characters, poisoned={1: 3}), [], reason="Poisoner")
        deaths = [death("execution", 1, 1)]
        self.assertInvalid(world(BASE, deaths, nights=2, poisoned={2: 3}), [], deaths, nights=2, reason="Poisoner")
        # poison ends when the Poisoner dies, so it can't still be marked after the execution
        self.assertInvalid(world(BASE, deaths, nights=2, poisoned={1: 3}), [], deaths, nights=2, reason="Poisoner")
        grim = world(BASE, deaths, nights=2, poisoned={1: 3})
        grim.pages[1].poisoned = [False] * 5
        self.assertValid(grim, [], deaths, nights=2)

    def test_only_good_players(self):
        self.assertInvalid(world(BASE, poisoned={1: 0}), [], reason="isn't good")

class TestLaterInfo(WorldValidatorCase):
    def test_empath_counts_alive_neighbours(self):
        characters = [Role.IMP, Role.POISONER, Role.CHEF, Role.EMPATH, Role.MONK]
        self.assertValid(world(characters), [info("empath", empath=3, number=0, night=1, left_neighbour=2, right_neighbour=4)])
        deaths = [death("execution", 4, 1)]
        # with player 4 dead, the Empath's neighbours are 2 and the Imp
        self.assertValid(world(characters, deaths, nights=2), [info("empath", empath=3, number=1, night=2, left_neighbour=2, right_neighbour=0)], deaths, nights=2)
        self.assertInvalid(world(characters, deaths, nights=2), [info("empath", empath=3, number=0, night=2, left_neighbour=2, right_neighbour=0)], deaths, nights=2, reason="Empath")

    def test_poisoned_recluse_doesnt_register(self):
        characters = [Role.IMP, Role.POISONER, Role.EMPATH, Role.RECLUSE, Role.CHEF, Role.MONK]
        empath = [info("empath", empath=2, number=2, night=1, left_neighbour=1, right_neighbour=3)]
        self.assertValid(world(characters), empath)
        self.assertInvalid(world(characters, poisoned={1: 3}), empath, reason="Empath")

    def test_dead_good_players_dont_wake(self):
        deaths = [death("execution", 3, 1)]
        self.assertInvalid(world(BASE, deaths, nights=2), [info("empath", empath=3, number=0, night=2, left_neighbour=2, right_neighbour=4)], deaths, nights=2, reason="dead")

    def test_fortune_teller(self):
        characters = [Role.IMP, Role.POISONER, Role.FORTUNE_TELLER, Role.EMPATH, Role.MONK]
        yes = [info("fortune teller", fortune_teller=2, night=1, pings=((0, 3), True))]
        no = [info("fortune teller", fortune_teller=2, night=1, pings=((0, 3), False))]
        self.assertValid(world(characters), yes)
        self.assertInvalid(world(characters), no, reason="Fortune Teller")

    def test_red_herring(self):
        characters = [Role.IMP, Role.POISONER, Role.FORTUNE_TELLER, Role.EMPATH, Role.MONK]
        yes = [info("fortune teller", fortune_teller=2, night=1, pings=((3, 4), True))]
        self.assertValid(world(characters, red_herring=3), yes)
        # a yes from a red herring the world doesn't mark
        self.assertInvalid(world(characters), yes, reason="red herring")
        # a no that includes the marked red herring
        no = [info("fortune teller", fortune_teller=2, night=1, pings=((3, 4), False))]
        self.assertInvalid(world(characters, red_herring=3), no, reason="red herring")
        self.assertInvalid(world([Role.IMP, Role.POISONER, Role.CHEF, Role.EMPATH, Role.MONK], red_herring=3), [], reason="without a Fortune Teller")

    def test_unmarked_red_herring_must_fit_somewhere(self):
        characters = [Role.IMP, Role.POISONER, Role.FORTUNE_TELLER, Role.EMPATH, Role.MONK]
        # every good player is in a "no" reading, so wherever the red herring is it changes one
        readings = [
            info("fortune teller", fortune_teller=2, night=1, pings=((2, 3), False)),
            info("fortune teller", fortune_teller=2, night=2, pings=((4, 1), False)),
        ]
        self.assertInvalid(world(characters, nights=2), readings, [], nights=2, reason="red herring")
        self.assertValid(world(characters, nights=2), readings[:1], [], nights=2)

    def test_undertaker(self):
        characters = [Role.IMP, Role.POISONER, Role.UNDERTAKER, Role.EMPATH, Role.MONK]
        deaths = [death("execution", 3, 1)]
        self.assertValid(world(characters, deaths, nights=2), [info("undertaker", undertaker=2, body=3, token=Role.EMPATH, night=2)], deaths, nights=2)
        self.assertInvalid(world(characters, deaths, nights=2), [info("undertaker", undertaker=2, body=3, token=Role.MONK, night=2)], deaths, nights=2, reason="Undertaker")
        # no execution the day before
        self.assertInvalid(world(characters, nights=2), [info("undertaker", undertaker=2, body=3, token=Role.EMPATH, night=2)], [], nights=2, reason="Undertaker")

    def test_ravenkeeper(self):
        characters = [Role.IMP, Role.POISONER, Role.RAVENKEEPER, Role.EMPATH, Role.MONK]
        deaths = [death("demon", 2, 2)]
        rk_imp = [info("ravenkeeper", ravenkeeper=2, chosen=0, token=Role.IMP, night=2)]
        self.assertValid(world(characters, deaths, nights=2), rk_imp, deaths, nights=2)
        self.assertInvalid(world(characters, deaths, nights=2), [info("ravenkeeper", ravenkeeper=2, chosen=0, token=Role.MONK, night=2)], deaths, nights=2, reason="Ravenkeeper")
        # a good Ravenkeeper only learns something when killed at night
        self.assertInvalid(world(characters, nights=2), rk_imp, [], nights=2, reason="Ravenkeeper")

    def test_virgin(self):
        characters = [Role.IMP, Role.POISONER, Role.VIRGIN, Role.EMPATH, Role.MONK]
        deaths = [death("execution", 3, 1)]
        executed = [info("virgin", virgin=2, nominator=3, executed=True, night=1)]
        self.assertValid(world(characters, deaths), executed, deaths)
        # the Imp nominated, so no one is executed
        self.assertValid(world(characters), [info("virgin", virgin=2, nominator=0, executed=False, night=1)])
        self.assertInvalid(world(characters), [info("virgin", virgin=2, nominator=3, executed=False, night=1)], reason="Virgin")
        # an evil nominator can't trigger it
        evil_nominator = [info("virgin", virgin=2, nominator=1, executed=True, night=1)]
        evil_death = [death("execution", 1, 1)]
        self.assertInvalid(world(characters, evil_death), evil_nominator, evil_death, reason="Townsfolk")

    def test_virgin_only_once(self):
        # 7 players: 5 townsfolk, 1 minion, 1 demon
        characters = [Role.IMP, Role.POISONER, Role.VIRGIN, Role.EMPATH, Role.MONK, Role.CHEF, Role.MAYOR]
        deaths = [death("execution", 3, 1), death("execution", 5, 2)]
        first = info("virgin", virgin=2, nominator=3, executed=True, night=1)
        second = info("virgin", virgin=2, nominator=5, executed=True, night=2)
        self.assertValid(world(characters, deaths[:1], nights=2), [first], deaths[:1], nights=2)
        self.assertInvalid(world(characters, deaths, nights=2), [first, second], deaths, nights=2, reason="Virgin")

    def test_slayer(self):
        characters = [Role.IMP, Role.SCARLET_WOMAN, Role.SLAYER, Role.EMPATH, Role.MONK]
        deaths = [death("slayer", 0, 1)]
        caught = {(1, AFTER_SLAYER): [Role.IMP, Role.IMP, Role.SLAYER, Role.EMPATH, Role.MONK]}
        shot = [info("slayer", slayer=2, target=0, successful=True, night=1)]
        self.assertValid(world(characters, deaths, later=caught), shot, deaths)
        # a successful shot needs a death, and the other way around
        self.assertInvalid(world(characters), shot, [], reason="Slayer")
        self.assertInvalid(world(characters), [info("slayer", slayer=2, target=0, successful=False, night=1)], reason="missed")

    def test_evil_slayer_cant_kill(self):
        characters = [Role.IMP, Role.SCARLET_WOMAN, Role.CHEF, Role.EMPATH, Role.MONK]
        deaths = [death("slayer", 0, 1)]
        caught = {(1, AFTER_SLAYER): [Role.IMP, Role.IMP, Role.CHEF, Role.EMPATH, Role.MONK]}
        shot = [info("slayer", slayer=1, target=0, successful=True, night=1)]
        self.assertInvalid(world(characters, deaths, later=caught), shot, deaths, reason="Slayer")

if __name__ == "__main__":
    unittest.main()
