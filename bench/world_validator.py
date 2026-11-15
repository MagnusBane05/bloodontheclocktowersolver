"""Checks whether a world could really have happened: whether at least one complete game fits it.

A world is valid when some full set of characters, starpasses and Storyteller choices (how the
Spy and Recluse register, the red herring, Monk protection, who the Imp attacks) matches every
page of the world and every info and death in the scenario, following the Trouble Brewing rules
on the wiki (https://wiki.bloodontheclocktower.com). It runs after solving, so it's written for
accuracy rather than speed. It uses none of the solver's validators or deductions, so a bug in
those can't hide an invalid world here.

Assumptions shared with the solver and the simulator:
- good players never lie. A good player's claims and info come from the character they think
  they are (their own, or the Drunk's token), even when the info itself is false
- a world with no poison mark on a night means no one's poisoning changed anything, so no one
  is treated as poisoned. A mark means that player is poisoned that night and the next day
- a world with no red herring mark means the red herring is on a player that no Fortune Teller
  reading depends on
- the Poisoner only poisons good players
- the Spy can be the red herring, and the red herring moves if a Spy red herring catches a starpass
- the Drunk's token is a Townsfolk that isn't in play
- the Mayor and Butler can be in play, but their abilities have no effect
- the game hasn't ended
"""
from __future__ import annotations

from typing import Any, Iterator, NamedTuple

from grimoire import Grimoire, NightOrderPosition, Role
from grimoire.gamerules import ROLE_BREAKDOWNS
from grimoire.info import DeathInfo, Info

TOWNSFOLK = frozenset({
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR,
})
OUTSIDERS = frozenset({Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK})
MINIONS = frozenset({Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN})
GOOD = TOWNSFOLK | OUTSIDERS
EVIL = MINIONS | {Role.IMP}
CHARACTERS = GOOD | EVIL

# the real characters each of the world's roles allows
_COVERED: dict[Role, frozenset[Role]] = {
    Role.ANY_OTHER: CHARACTERS,
    Role.ANY_OTHER_EVIL: EVIL,
    Role.ANY_OTHER_GOOD: GOOD,
    Role.ANY_OTHER_MINION: MINIONS,
    Role.ANY_OTHER_TOWNSFOLK: TOWNSFOLK,
    Role.ANY_OTHER_OUTSIDER: OUTSIDERS,
    Role.NON_DEMON: CHARACTERS - {Role.IMP},
}

def covers(world_role: Role, character: Role) -> bool:
    return world_role == character or character in _COVERED.get(world_role, ())

# the character a player claims to be by giving each kind of info
INFO_ROLES = {
    "washerwoman": Role.WASHERWOMAN,
    "librarian": Role.LIBRARIAN,
    "investigator": Role.INVESTIGATOR,
    "chef": Role.CHEF,
    "empath": Role.EMPATH,
    "fortune teller": Role.FORTUNE_TELLER,
    "undertaker": Role.UNDERTAKER,
    "ravenkeeper": Role.RAVENKEEPER,
    "virgin": Role.VIRGIN,
    "slayer": Role.SLAYER,
}
SOURCE_FIELDS = {kind: kind.replace(" ", "_") for kind in INFO_ROLES} | {"claim": "player"}
FIRST_NIGHT_KINDS = {"washerwoman", "librarian", "investigator", "chef"}

AFTER_IMP = NightOrderPosition.AFTER_IMP
AFTER_SLAYER = NightOrderPosition.AFTER_SLAYER
AFTER_EXECUTION = NightOrderPosition.AFTER_EXECUTION
_DEATH_ORDERS = {"demon": AFTER_IMP, "slayer": AFTER_SLAYER, "execution": AFTER_EXECUTION}

type Key = tuple[int, int]
START: Key = (0, 0)

# how far a branch got before failing, so the reported reason comes from the most promising one
_SETUP, _FIRST_NIGHT, _TIMELINE, _PAGES, _INFO = range(5)

class State(NamedTuple):
    key: Key
    roles: tuple[Role, ...]
    dead: tuple[bool, ...]

class Timeline(NamedTuple):
    states: list[State]
    # (key, seat) for each minion who became the Imp
    promotions: list[tuple[Key, int]]

class _Failed(Exception):
    def __init__(self, stage: int, reason: str):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason

def source_of(info: Info) -> int:
    return info[SOURCE_FIELDS[info["kind"]]]  # pyright: ignore[reportUnknownVariableType, reportTypedDictNotRequiredAccess]

def claimed_role(info: Info) -> Role:
    if info["kind"] == "claim":
        return info["character"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
    return INFO_ROLES[info["kind"]]

def info_night(info: Info) -> int:
    return info.get("night", 1)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

def find_world_problem(world: Grimoire, info: list[Info], deaths: list[DeathInfo], nights: int) -> str | None:
    """None if at least one complete game fits the world, scenario info and deaths, else why not."""
    return _WorldCheck(world, info, deaths, nights).run()

def is_world_valid(world: Grimoire, info: list[Info], deaths: list[DeathInfo], nights: int) -> bool:
    return find_world_problem(world, info, deaths, nights) is None

class _WorldCheck:
    def __init__(self, world: Grimoire, info: list[Info], deaths: list[DeathInfo], nights: int):
        self.world = world
        self.info = info
        self.nights = nights
        self.n = world.num_players
        breakdown = ROLE_BREAKDOWNS[self.n]
        self.minion_count = breakdown["minions"]
        self.townsfolk_count = breakdown["townsfolk"]
        self.outsider_count = breakdown["outsiders"]
        self.pages = sorted(
            ((page.night, int(page.night_order_position)), page) for page in world.pages
        )
        self.deaths = sorted(
            ((d["night"], int(_DEATH_ORDERS[d["kind"]])), d["player"], d["kind"]) for d in deaths
        )
        self.best: _Failed | None = None
        self.poison: dict[int, int] = {}

    def run(self) -> str | None:
        try:
            self._check_structure()
            self._check_world_marks()
        except _Failed as e:
            return e.reason
        domains = self._domains()
        for seat, domain in enumerate(domains):
            if not domain:
                return f"no character fits player {seat}"
        for roles in self._assignments(domains):
            try:
                self._check_setup(roles)
                self._check_first_night(roles)
                for timeline in self._timelines(roles):
                    try:
                        self._check_quiet_nights(timeline)
                        self._check_pages(timeline)
                        self._check_info(roles, timeline)
                        return None
                    except _Failed as e:
                        self._note(e)
            except _Failed as e:
                self._note(e)
        if self.best is None:
            return "no assignment of characters fits the character counts"
        return self.best.reason

    def _note(self, failure: _Failed):
        if self.best is None or failure.stage > self.best.stage:
            self.best = failure

    # --- checks that don't depend on who is which character ---

    def _check_structure(self):
        dead: set[int] = set()
        demon_nights: set[int] = set()
        execution_days: set[int] = set()
        for key, player, kind in self.deaths:
            night = key[0]
            if player in dead:
                raise _Failed(_SETUP, f"player {player} died twice")
            if kind == "demon":
                if night == 1:
                    raise _Failed(_SETUP, "the Imp doesn't kill on night 1")
                if night in demon_nights:
                    raise _Failed(_SETUP, f"two demon kills on night {night}")
                demon_nights.add(night)
            if kind == "execution":
                if night in execution_days:
                    raise _Failed(_SETUP, f"two executions on day {night}")
                execution_days.add(night)
            dead.add(player)
            if self.n - len(dead) <= 2:
                raise _Failed(_SETUP, f"only {self.n - len(dead)} players alive after day/night {night}, so the game is over")

        for key, page in self.pages:
            expected = self._dead_at(key)
            if tuple(page.dead) != expected:
                raise _Failed(_SETUP, f"night {key[0]} {NightOrderPosition(key[1]).name} page deaths don't match the scenario")

        successful_shots = {
            (info_night(i), i["target"])  # pyright: ignore[reportTypedDictNotRequiredAccess]
            for i in self.info if i["kind"] == "slayer" and i["successful"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        }
        slayer_deaths = {(key[0], player) for key, player, kind in self.deaths if kind == "slayer"}
        if successful_shots != slayer_deaths:
            raise _Failed(_SETUP, "successful Slayer shots don't match the Slayer deaths")

        executions = {(key[0], player) for key, player, kind in self.deaths if kind == "execution"}
        for i in self.info:
            if i["kind"] == "virgin" and i["executed"]:  # pyright: ignore[reportTypedDictNotRequiredAccess]
                if (info_night(i), i["nominator"]) not in executions:  # pyright: ignore[reportTypedDictNotRequiredAccess]
                    raise _Failed(_SETUP, f"the Virgin's nominator {i['nominator']} wasn't executed on day {info_night(i)}")  # pyright: ignore[reportTypedDictNotRequiredAccess]

    def _dead_at(self, key: Key) -> tuple[bool, ...]:
        dead = [False] * self.n
        for death_key, player, _ in self.deaths:
            if death_key <= key:
                dead[player] = True
        return tuple(dead)

    def _check_world_marks(self):
        for key, page in self.pages:
            poisoned = [i for i, p in enumerate(page.poisoned) if p]
            if len(poisoned) > 1:
                raise _Failed(_SETUP, f"two players poisoned on night {key[0]}")
            if poisoned:
                if self.poison.setdefault(key[0], poisoned[0]) != poisoned[0]:
                    raise _Failed(_SETUP, f"two players poisoned on night {key[0]}")
            if sum(page.red_herring) > 1:
                raise _Failed(_SETUP, "two red herrings on one page")
            named = [m for m in page.minion_types if m != Role.ANY_OTHER_MINION]
            if len(page.minion_types) != self.minion_count or len(named) != len(set(named)):
                raise _Failed(_SETUP, "invalid minion types")

    # --- starting characters ---

    def _claims(self) -> list[set[Role]]:
        claims: list[set[Role]] = [set() for _ in range(self.n)]
        for i in self.info:
            claims[source_of(i)].add(claimed_role(i))
        return claims

    def _domains(self) -> list[list[Role]]:
        claims = self._claims()
        domains: list[list[Role]] = []
        for seat in range(self.n):
            domain: list[Role] = []
            for character in sorted(CHARACTERS):
                if character in GOOD and not self._good_claims_fit(character, claims[seat]):
                    continue
                if not all(self._fits_page(page.characters[seat], character) for _, page in self.pages):
                    continue
                domain.append(character)
            domains.append(domain)
        return domains

    @staticmethod
    def _good_claims_fit(character: Role, claims: set[Role]) -> bool:
        if not claims:
            return True
        if len(claims) > 1:
            return False
        claim = next(iter(claims))
        return claim == character or (character == Role.DRUNK and claim in TOWNSFOLK)

    @staticmethod
    def _fits_page(world_role: Role, character: Role) -> bool:
        # a starting minion can be the Imp on a later page
        return covers(world_role, character) or (character in MINIONS and covers(world_role, Role.IMP))

    def _assignments(self, domains: list[list[Role]]) -> Iterator[tuple[Role, ...]]:
        order = sorted(range(self.n), key=lambda s: len(domains[s]))
        roles: list[Role | None] = [None] * self.n
        used: set[Role] = set()
        max_outsiders = self.outsider_count + 2
        counts = {"townsfolk": 0, "outsider": 0, "minion": 0, "demon": 0}

        def kind(c: Role) -> str:
            if c in TOWNSFOLK:
                return "townsfolk"
            if c in OUTSIDERS:
                return "outsider"
            if c in MINIONS:
                return "minion"
            return "demon"

        limits = {"townsfolk": self.townsfolk_count, "outsider": max_outsiders, "minion": self.minion_count, "demon": 1}

        def place(i: int) -> Iterator[tuple[Role, ...]]:
            if i == self.n:
                baron = Role.BARON in used
                outsiders = self.outsider_count + (2 if baron else 0)
                if counts["outsider"] == outsiders and counts["minion"] == self.minion_count and counts["demon"] == 1:
                    yield tuple(roles)  # pyright: ignore[reportReturnType]
                return
            seat = order[i]
            for c in domains[seat]:
                if c in used:
                    continue
                k = kind(c)
                if counts[k] >= limits[k]:
                    continue
                roles[seat] = c
                used.add(c)
                counts[k] += 1
                yield from place(i + 1)
                counts[k] -= 1
                used.discard(c)
            roles[seat] = None

        yield from place(0)

    def _check_setup(self, roles: tuple[Role, ...]):
        minions = {c for c in roles if c in MINIONS}
        for _, page in self.pages:
            for m in page.minion_types:
                if m != Role.ANY_OTHER_MINION and m not in minions:
                    raise _Failed(_SETUP, f"minion type {m.name} isn't in play")

        world_tokens = {page.drunk_token for _, page in self.pages if page.drunk_token is not None}
        if len(world_tokens) > 1:
            raise _Failed(_SETUP, "different Drunk tokens")
        if Role.DRUNK not in roles:
            if world_tokens:
                raise _Failed(_SETUP, "Drunk token without a Drunk")
            return
        drunk = roles.index(Role.DRUNK)
        tokens = set(TOWNSFOLK - set(roles))
        claims = {claimed_role(i) for i in self.info if source_of(i) == drunk} & TOWNSFOLK
        if claims:
            tokens &= claims
        if world_tokens:
            tokens &= world_tokens
        if not tokens:
            raise _Failed(_SETUP, "the Drunk's token must be a Townsfolk not in play that they claim")

    # --- poison ---

    def _poisoner_active(self, state: State) -> bool:
        return any(c == Role.POISONER and not state.dead[s] for s, c in enumerate(state.roles))

    def _poisoned(self, seat: int, night: int, state: State) -> bool:
        return self.poison.get(night) == seat and self._poisoner_active(state)

    # --- night 1 info, which only needs the starting characters ---

    def _check_first_night(self, roles: tuple[Role, ...]):
        state = State(START, roles, (False,) * self.n)
        for i in self.info:
            if i["kind"] not in FIRST_NIGHT_KINDS:
                continue
            source = source_of(i)
            if roles[source] in EVIL or roles[source] != claimed_role(i) or self._poisoned(source, 1, state):
                continue
            problem = self._first_night_problem(i, state)
            if problem is not None:
                raise _Failed(_FIRST_NIGHT, problem)

    def _first_night_problem(self, i: Info, state: State) -> str | None:
        roles = state.roles
        kind = i["kind"]

        def sober(seat: int) -> bool:
            return not self._poisoned(seat, 1, state)

        if kind == "washerwoman":
            shown: Role = i["townsfolk"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            pair = (i["first_player"], i["second_player"])  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if not any(roles[p] == shown or (roles[p] == Role.SPY and sober(p) and shown in TOWNSFOLK) for p in pair):
                return f"Washerwoman: neither {pair} is the {shown.name}"
        elif kind == "investigator":
            shown = i["minion"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            pair = (i["first_player"], i["second_player"])  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if not any(roles[p] == shown or (roles[p] == Role.RECLUSE and sober(p) and shown in MINIONS) for p in pair):
                return f"Investigator: neither {pair} is the {shown.name}"
        elif kind == "librarian":
            token: Role | None = i["token"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if token is None:
                # a sober Recluse can register as a Minion, so it can be hidden
                if any(c in OUTSIDERS and not (c == Role.RECLUSE and sober(s)) for s, c in enumerate(roles)):
                    return "Librarian: learnt zero Outsiders but one is in play"
            else:
                pair = (i["first_player"], i["second_player"])  # pyright: ignore[reportTypedDictNotRequiredAccess]
                if not any(roles[p] == token or (roles[p] == Role.SPY and sober(p) and token in OUTSIDERS) for p in pair if p is not None):
                    return f"Librarian: neither {pair} is the {token.name}"
        elif kind == "chef":
            number: int = i["number"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            options = [self._registers_evil(roles[s], sober(s)) for s in range(self.n)]
            if number not in self._chef_numbers(options):
                return f"Chef: {number} pairs isn't possible"
        return None

    @staticmethod
    def _registers_evil(character: Role, sober: bool) -> tuple[bool, ...]:
        if sober and character in (Role.SPY, Role.RECLUSE):
            return (False, True)
        return (character in EVIL,)

    def _chef_numbers(self, options: list[tuple[bool, ...]]) -> set[int]:
        # the Spy and Recluse can register differently for each pair they're in, so a pair
        # counts for sure only when both players are evil, and might count if both could be
        certain = possible = 0
        for s in range(self.n):
            a, b = options[s], options[(s + 1) % self.n]
            if False not in a and False not in b:
                certain += 1
            elif True in a and True in b:
                possible += 1
        return set(range(certain, certain + possible + 1))

    # --- deaths and starpasses ---

    def _timelines(self, roles: tuple[Role, ...]) -> Iterator[Timeline]:
        """Every way the deaths can play out, branching on who catches a starpass."""
        events = self.deaths

        def step(i: int, state: State, states: list[State], promotions: list[tuple[Key, int]]) -> Iterator[Timeline]:
            if i == len(events):
                yield Timeline(states, promotions)
                return
            key, player, kind = events[i]
            night = key[0]
            roles = list(state.roles)
            dead = list(state.dead)
            alive_before = dead.count(False)
            victim = roles[player]
            sober_victim = not self._poisoned(player, night, state)
            if kind == "demon" and victim == Role.SOLDIER and sober_victim:
                self._note(_Failed(_TIMELINE, f"the Imp killed sober Soldier {player} on night {night}"))
                return
            if kind == "execution" and victim == Role.SAINT and sober_victim:
                self._note(_Failed(_TIMELINE, f"sober Saint {player} executed on day {night}, so evil won"))
                return
            if kind == "slayer" and not (victim == Role.IMP or (victim == Role.RECLUSE and sober_victim)):
                self._note(_Failed(_TIMELINE, f"the Slayer killed player {player}, who can't register as the Imp"))
                return
            dead[player] = True
            if victim != Role.IMP:
                new_state = State(key, tuple(roles), tuple(dead))
                yield from step(i + 1, new_state, states + [new_state], promotions)
                return

            # 5 or more alive counts the dying Imp
            scarlet_women = [
                s for s, c in enumerate(roles)
                if c == Role.SCARLET_WOMAN and not dead[s] and not self._poisoned(s, night, state)
            ]
            if scarlet_women and alive_before >= 5:
                heirs = scarlet_women
            elif kind == "demon":
                heirs = [s for s, c in enumerate(roles) if c in MINIONS and not dead[s]]
            else:
                heirs = []
            if not heirs:
                when = "night" if kind == "demon" else "day"
                self._note(_Failed(_TIMELINE, f"the Imp died on {when} {night} and no one became the Imp, so good won"))
                return
            for heir in heirs:
                new_roles = list(roles)
                new_roles[heir] = Role.IMP
                new_state = State(key, tuple(new_roles), tuple(dead))
                yield from step(i + 1, new_state, states + [new_state], promotions + [(key, heir)])

        start = State(START, roles, (False,) * self.n)
        yield from step(0, start, [start], [])

    def _check_quiet_nights(self, timeline: Timeline):
        """A night after the first with no demon kill needs a reason no one died."""
        demon_nights = {key[0] for key, _, kind in self.deaths if kind == "demon"}
        for night in range(2, self.nights + 1):
            if night in demon_nights:
                continue
            state = self._state_before(timeline, (night, int(AFTER_IMP)))
            if any(state.dead):
                continue  # the Imp chose a dead player
            protected = any(
                c in (Role.SOLDIER, Role.MONK) and not state.dead[s] and not self._poisoned(s, night, state)
                for s, c in enumerate(state.roles)
            )
            if not protected:
                raise _Failed(_TIMELINE, f"no one died on night {night} and no Monk, Soldier or dead player explains it")

    @staticmethod
    def _state_at(timeline: Timeline, key: Key) -> State:
        """The state after every event up to and including key."""
        found = timeline.states[0]
        for state in timeline.states:
            if state.key <= key:
                found = state
        return found

    @staticmethod
    def _state_before(timeline: Timeline, key: Key) -> State:
        found = timeline.states[0]
        for state in timeline.states:
            if state.key < key:
                found = state
        return found

    # --- the world's pages ---

    def _check_pages(self, timeline: Timeline):
        roles0 = timeline.states[0].roles
        for key, page in self.pages:
            state = self._state_at(timeline, key)
            for seat, (world_role, character) in enumerate(zip(page.characters, state.roles)):
                if not covers(world_role, character):
                    raise _Failed(_PAGES, f"player {seat} is the {character.name} on night {key[0]} {NightOrderPosition(key[1]).name}, not {world_role.name}")
            for seat, poisoned in enumerate(page.poisoned):
                if not poisoned:
                    continue
                if not self._poisoner_active(state):
                    raise _Failed(_PAGES, f"player {seat} poisoned on night {key[0]} without an alive Poisoner")
                if roles0[seat] not in GOOD:
                    raise _Failed(_PAGES, f"player {seat} poisoned on night {key[0]} isn't good")

    # --- red herring ---

    def _red_herring_segments(self, timeline: Timeline) -> list[tuple[Key, Key, int | None]]:
        """(start, end, marked seat or None) for each stretch of the game the red herring stays put.
        It only moves when a Spy red herring becomes the Imp."""
        roles0 = timeline.states[0].roles
        marks = sorted((key, page.red_herring.index(True)) for key, page in self.pages if True in page.red_herring)
        end: Key = (self.nights + 1, 0)
        if not marks:
            return [(START, end, None)]
        if Role.FORTUNE_TELLER not in roles0:
            raise _Failed(_INFO, "red herring without a Fortune Teller in play")
        first = marks[0][1]
        move = next((k for k, s in timeline.promotions if s == first and roles0[s] == Role.SPY), None)
        if move is None:
            if len({s for _, s in marks}) > 1:
                raise _Failed(_INFO, "the red herring changed")
            return [(START, end, first)]
        if any(s != first for k, s in marks if k < move):
            raise _Failed(_INFO, "the red herring changed")
        after = {s for k, s in marks if k >= move and s != first}
        if any(s == first for k, s in marks if k >= move):
            raise _Failed(_INFO, f"red herring {first} became the Imp")
        if len(after) > 1:
            raise _Failed(_INFO, "the red herring changed")
        return [(START, move, first), (move, end, next(iter(after)) if after else None)]

    def _check_red_herring(self, timeline: Timeline, readings: list[tuple[Key, tuple[int, int], bool]]):
        roles0 = timeline.states[0].roles
        segments = self._red_herring_segments(timeline)
        if Role.FORTUNE_TELLER not in roles0:
            return
        for start, end, seat in segments:
            in_segment = [(k, pair, ping) for k, pair, ping in readings if start <= k < end]
            if seat is not None and not self._can_be_red_herring(timeline, seat, start):
                raise _Failed(_INFO, f"red herring {seat} isn't good")
            for key, pair, ping in in_segment:
                if not self._fortune_teller_fits(timeline, key, pair, ping, seat):
                    if seat is None:
                        raise _Failed(_INFO, f"Fortune Teller reading {pair} on night {key[0]} needs a red herring the world doesn't mark")
                    raise _Failed(_INFO, f"Fortune Teller reading {pair} on night {key[0]} doesn't fit red herring {seat}")
            if seat is None and not self._unmarked_red_herring_possible(timeline, readings, start, end):
                raise _Failed(_INFO, "no player can be the red herring without changing a Fortune Teller reading")

    def _can_be_red_herring(self, timeline: Timeline, seat: int, start: Key) -> bool:
        character = timeline.states[0].roles[seat]
        return (character in GOOD or character == Role.SPY) and self._state_at(timeline, start).roles[seat] != Role.IMP

    def _unmarked_red_herring_possible(self, timeline: Timeline, readings: list[tuple[Key, tuple[int, int], bool]], start: Key, end: Key) -> bool:
        def avoids_no_pairs(seat: int, a: Key, b: Key) -> bool:
            return not any(a <= k < b and not ping and seat in pair for k, pair, ping in readings)

        for seat in range(self.n):
            if not self._can_be_red_herring(timeline, seat, start):
                continue
            move = next((k for k, s in timeline.promotions if s == seat and start <= k < end), None)
            if move is None:
                if avoids_no_pairs(seat, start, end):
                    return True
            elif avoids_no_pairs(seat, start, move) and self._unmarked_red_herring_possible(timeline, readings, move, end):
                # a Spy red herring became the Imp, so the red herring moved
                return True
        return False

    def _fortune_teller_fits(self, timeline: Timeline, key: Key, pair: tuple[int, int], ping: bool, red_herring: int | None) -> bool:
        state = self._state_at(timeline, key)
        night = key[0]
        can_ping = [
            state.roles[p] == Role.IMP
            or (state.roles[p] == Role.RECLUSE and not self._poisoned(p, night, state))
            or p == red_herring
            for p in pair
        ]
        must_ping = [state.roles[p] == Role.IMP or p == red_herring for p in pair]
        if ping:
            return any(can_ping)
        return not any(must_ping)

    # --- info from later nights and days ---

    def _check_info(self, roles0: tuple[Role, ...], timeline: Timeline):
        readings: list[tuple[Key, tuple[int, int], bool]] = []
        executions = {key[0]: player for key, player, kind in self.deaths if kind == "execution"}
        demon_deaths = {(key[0], player) for key, player, kind in self.deaths if kind == "demon"}
        earlier_virgin: set[tuple[int, int]] = set()
        earlier_slayer: set[tuple[int, int]] = set()
        for i in self.info:
            if i["kind"] == "virgin":
                earlier_virgin.add((source_of(i), info_night(i)))
            if i["kind"] == "slayer":
                earlier_slayer.add((source_of(i), info_night(i)))

        for i in self.info:
            kind = i["kind"]
            source = source_of(i)
            night = info_night(i)
            character = roles0[source]
            good = character in GOOD
            real = character == claimed_role(i)

            if kind == "virgin":
                problem = self._virgin_problem(i, timeline, good, real, earlier_virgin)
            elif kind == "slayer":
                problem = self._slayer_problem(i, timeline, good, real, earlier_slayer)
            elif kind in FIRST_NIGHT_KINDS or kind == "claim":
                problem = None
            else:
                key: Key = (night, int(AFTER_IMP))
                state = self._state_at(timeline, key)
                problem = None
                if good:
                    problem = self._activity_problem(i, state, executions, demon_deaths)
                if problem is None and good and real and not self._poisoned(source, night, state):
                    if kind == "fortune teller":
                        (a, b), ping = i["pings"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
                        readings.append((key, (a, b), ping))
                    else:
                        problem = self._night_problem(i, timeline, state, executions)
            if problem is not None:
                raise _Failed(_INFO, problem)

        self._check_red_herring(timeline, readings)

    def _activity_problem(self, i: Info, state: State, executions: dict[int, int], demon_deaths: set[tuple[int, int]]) -> str | None:
        """When a good player, sober or not, can get this info at all."""
        kind = i["kind"]
        source = source_of(i)
        night = info_night(i)
        if night > self.nights:
            return f"{kind} info on night {night}, after the game"
        if kind == "ravenkeeper":
            if (night, source) not in demon_deaths:
                return f"good Ravenkeeper {source} didn't die on night {night}"
            return None
        if state.dead[source]:
            return f"good {kind} {source} was dead on night {night}"
        if kind == "undertaker":
            if night < 2 or night - 1 not in executions:
                return f"good Undertaker {source} has no execution to learn about on night {night}"
            if i["body"] != executions[night - 1]:  # pyright: ignore[reportTypedDictNotRequiredAccess]
                return f"Undertaker body {i['body']} wasn't executed on day {night - 1}"  # pyright: ignore[reportTypedDictNotRequiredAccess]
        return None

    def _night_problem(self, i: Info, timeline: Timeline, state: State, executions: dict[int, int]) -> str | None:
        kind = i["kind"]
        night = info_night(i)
        if kind == "empath":
            empath = source_of(i)
            alive = [s for s in range(self.n) if not state.dead[s]]
            index = alive.index(empath)
            neighbours = {alive[(index - 1) % len(alive)], alive[(index + 1) % len(alive)]}
            counts = {0}
            for p in neighbours:
                options = self._registers_evil(state.roles[p], not self._poisoned(p, night, state))
                counts = {c + int(o) for c in counts for o in options}
            if i["number"] not in counts:  # pyright: ignore[reportTypedDictNotRequiredAccess]
                return f"Empath: {i['number']} evil neighbours isn't possible on night {night}"  # pyright: ignore[reportTypedDictNotRequiredAccess]
        elif kind == "undertaker":
            body = executions[night - 1]
            executed_state = self._state_at(timeline, (night - 1, int(AFTER_EXECUTION)))
            if not self._registers_as(executed_state.roles[body], i["token"], not self._poisoned(body, night, state)):  # pyright: ignore[reportTypedDictNotRequiredAccess]
                return f"Undertaker: executed player {body} can't show as {i['token'].name}"  # pyright: ignore[reportTypedDictNotRequiredAccess]
        elif kind == "ravenkeeper":
            chosen = i["chosen"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if not self._registers_as(state.roles[chosen], i["token"], not self._poisoned(chosen, night, state)):  # pyright: ignore[reportTypedDictNotRequiredAccess]
                return f"Ravenkeeper: player {chosen} can't show as {i['token'].name}"  # pyright: ignore[reportTypedDictNotRequiredAccess]
        return None

    @staticmethod
    def _registers_as(character: Role, shown: Role, sober: bool) -> bool:
        if character == shown:
            return True
        if sober and character == Role.SPY and shown in GOOD:
            return True
        if sober and character == Role.RECLUSE and shown in EVIL:
            return True
        return False

    def _virgin_problem(self, i: Info, timeline: Timeline, good: bool, real: bool, earlier: set[tuple[int, int]]) -> str | None:
        virgin = source_of(i)
        night = info_night(i)
        nominator = i["nominator"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        state = self._state_at(timeline, (night, int(AFTER_SLAYER)))
        spent = any(s == virgin and n < night for s, n in earlier)
        sober = real and not self._poisoned(virgin, night, state)
        if good and (state.dead[virgin] or state.dead[nominator]):
            return f"good Virgin {virgin} or nominator {nominator} dead on day {night}"
        nominator_role = state.roles[nominator]
        nominator_sober = not self._poisoned(nominator, night, state)
        can_be_townsfolk = nominator_role in TOWNSFOLK or (nominator_role == Role.SPY and nominator_sober)
        can_be_other = nominator_role not in TOWNSFOLK
        if i["executed"]:  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if not (good and sober and not spent):
                return f"Virgin {virgin} executed their nominator without a working ability"
            if not can_be_townsfolk:
                return f"Virgin {virgin}'s nominator {nominator} isn't a Townsfolk"
        elif good and sober and not spent and not can_be_other:
            return f"Townsfolk {nominator} nominated sober Virgin {virgin} but wasn't executed"
        return None

    def _slayer_problem(self, i: Info, timeline: Timeline, good: bool, real: bool, earlier: set[tuple[int, int]]) -> str | None:
        slayer = source_of(i)
        night = info_night(i)
        target = i["target"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        state = self._state_at(timeline, (night, int(AFTER_IMP)))
        spent = any(s == slayer and n < night for s, n in earlier)
        sober = real and not self._poisoned(slayer, night, state)
        if good and state.dead[slayer]:
            return f"good Slayer {slayer} was dead on day {night}"
        target_role = state.roles[target]
        if i["successful"]:  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if not (good and sober and not spent):
                return f"Slayer {slayer} killed {target} without a working ability"
            if state.dead[target]:
                return f"Slayer {slayer} killed {target}, who was already dead"
            if not (target_role == Role.IMP or (target_role == Role.RECLUSE and not self._poisoned(target, night, state))):
                return f"Slayer {slayer} killed {target}, who isn't the Imp"
        elif good and sober and not spent and not state.dead[target] and target_role == Role.IMP:
            return f"sober Slayer {slayer} shot the Imp {target} and missed"
        return None
