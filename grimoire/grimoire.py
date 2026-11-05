from __future__ import annotations
import bisect
from typing import Any, NamedTuple, override


from .gamerules import ROLE_BREAKDOWNS, ALLOWED_MULTIPLES

from .nightOrderPosition import NightOrderPosition

from . import gamerules
from .role import *
from .errors import *
from .grimoire_page import GrimoirePage
from grimoire import role, validators

class PassBetweenPagesResult(NamedTuple):
    valid: bool
    reason: str
    curr_changed: bool

class PassThroughPagesResult(NamedTuple):
    valid: bool
    reason: str
    changed: set[int]

class GrimoireKey(NamedTuple):
    night: int
    order: NightOrderPosition

class Poisoning(NamedTuple):
    night: int
    order: NightOrderPosition
    player: int

class Grimoire:
    def __init__(self, num_players:int=5):
        if num_players not in ROLE_BREAKDOWNS.keys():
            raise ValueError(f"{num_players} player worlds are not yet handled.")
        self.pages: list[GrimoirePage] = [GrimoirePage(num_players,1)]
        self.keys: list[GrimoireKey]= [self._page_key(GrimoirePage(num_players,1))]
        self.num_players: int = num_players
        self.unsettled: set[GrimoireKey] | None = None

    @override
    def __eq__(self, value: object):
        if not isinstance(value, Grimoire):
            return False
        return self.keys == value.keys and self.pages == value.pages

    @override
    def __hash__(self):
        return hash((tuple(self.keys), tuple(self.pages)))

    @override
    def __str__(self):
        s = ""
        for i, phase in enumerate(self.pages):
            ps = f"--- Phase {i+1} ---\n"
            for j in range(len(phase.characters)):
                character = phase.characters[j]
                dead = phase.dead[j]
                red_herring = phase.red_herring[j]
                if character in ANY_OTHER_ROLES:
                    ps += f"Player {j} is {CHARACTER_STRINGS[character]}.\n"
                else:
                    ps += f"Player {j} is the {CHARACTER_STRINGS[character]}.\n"
                if phase.poisoned[j]:
                    ps += f"Player {j} was poisoned N{phase.night}.\n"
                if dead:
                    ps += f"Player {j} is dead.\n"
                if red_herring:
                    ps += f"Player {j} is the red herring.\n"
            s += ps
        s += "Minion types: "
        s += ", ".join([m.name for m in self.pages[-1].minion_types])
        s += "\n"
        s += "---------------------"
        return s
    
    def loose_equals(self, other: Grimoire):
        players = self.num_players
        if players != other.num_players:
            return False
        for page in self.pages:
            night = page.night
            night_order_position = page.night_order_position
            other_page = other.get_page(night, night_order_position)
            if other_page == None:
                continue
            if not page.loose_equals(other_page):
                return False
        return True

    def subsumes(self, other: Grimoire) -> bool:
        for page in self.pages:
            other_page = other.get_page(page.night, page.night_order_position)
            if other_page == None:
                continue
            if not page.subsumes(other_page):
                return False
        return True
    
    def clone(self):
        new = Grimoire(self.num_players)
        new.pages = [p.clone() for p in self.pages]
        new.keys = self.keys.copy()
        new.unsettled = self.unsettled
        return new

    def get_all_poisonings(self) -> frozenset[Poisoning]:
        return frozenset(
            Poisoning(page.night, page.night_order_position, page.poisoned.index(True)) 
            for page in self.pages 
            if True in page.poisoned
        )

    def state_without_poison(self) -> tuple[Any, ...]:  # pyright: ignore[reportExplicitAny]
        states: list[tuple[GrimoireKey, tuple[Any, ...]]] = []  # pyright: ignore[reportExplicitAny]
        previous = None
        for key, page in zip(self.keys, self.pages):
            state = page.state_without_poison()
            if state != previous:
                states.append((key, state))
                previous = state
        return tuple(states)
    
    @staticmethod
    def _page_key(page: GrimoirePage) -> GrimoireKey:
        return GrimoireKey(page.night, page.night_order_position)
    
    def get_first_page(self):
        assert (
            len(self.pages) > 0 
            and self.pages[0].night == 1
            and self.pages[0].night_order_position == NightOrderPosition.AFTER_IMP
        )
        return self.pages[0]

    def get_page(self, night: int, night_order_position: NightOrderPosition) -> GrimoirePage | None:
        key = (night, night_order_position)
        i = bisect.bisect_left(self.keys, key)

        if i < len(self.pages) and self._page_key(self.pages[i]) == key:
            return self.pages[i]

        return None
    
    def add_page(self, night: int, night_order_position: NightOrderPosition) -> GrimoirePage:
        key = GrimoireKey(night, night_order_position)
        i = bisect.bisect_left(self.keys, key)

        if i < len(self.pages) and self._page_key(self.pages[i]) == key:
            raise PhaseInWorldError(f"Grimoire already contains page with night {night} and night order position {night_order_position}")
        
        if i == 0:
            raise IndexError("You should not be adding a page before the first page.")

        prev = self.pages[i-1]
        new_page = prev.clone()
        if night != new_page.night:
            new_page.executee = None
        new_page.night = night
        new_page.night_order_position = night_order_position
        new_page.poisoned = [False]*len(new_page.poisoned)
        new_page.chef_number = None
        self.pages.insert(i, new_page)
        self.keys.insert(i, key)
        return new_page

    def changed_pages_since(self, base: Grimoire) -> set[GrimoireKey]:
        if base.unsettled is None:
            return set(self.keys)
        changed = set(base.unsettled)
        for page, key in zip(self.pages, self.keys):
            base_page = base.get_page(key.night, key.order)
            if base_page is None or not page.same_state(base_page):
                changed.add(key)
        return changed

    def apply_starpass(self, demon: int, page: GrimoirePage, red_herring_spy_catches: bool = False):
        new_demon = page.apply_starpass(demon, red_herring_spy_catches)

        # make new demon a minion in past pages
        if new_demon is not None:
            for p in self.get_all_previous_pages(page):
                _ =p.apply_character(Role.ANY_OTHER_MINION, new_demon)
    
    def apply_sw_catch(self, demon: int, page: GrimoirePage):
        new_demon = page.apply_sw_catch(demon)

        # add Scarlet Woman to previous page minion types
        prev_pages = self.get_all_previous_pages(page)
        for i, p in enumerate(prev_pages):
            try:
                p.add_minion_type(Role.SCARLET_WOMAN)
            except ValueError:
                raise Exception(f"Scarlet Woman is not a valid minion type in previous page {i}.")
            
        # make new demon the Scarlet Woman in previous pages
        if new_demon is not None:
            for p in prev_pages:
                p.characters[new_demon] = Role.SCARLET_WOMAN

    # TODO deprecate
    # TODO deprecate?
    def get_all_previous_pages(self, page: GrimoirePage):
        key = self._page_key(page)
        i = bisect.bisect_left(self.keys, key)

        return [self.pages[j] for j in range(0, i)]
    
    def get_unique_nights(self):
        nights: set[int] = set()
        for page in self.pages:
            nights.add(page.night)        
        return nights
    
    def apply_character(
        self, 
        character: Role, 
        player: int, 
        night: int, 
        night_order_position: NightOrderPosition
    ) -> list[GrimoirePage]:
        changed_pages: list[GrimoirePage] = []
        for page in self.pages:
            if (
                page.night >= night 
                and page.night_order_position > night_order_position
            ):
                continue
            if page.apply_character(character, player):
                changed_pages.append(page)
        return changed_pages

    def apply_drunk(
        self, 
        character: Role, 
        player: int,
        night: int,
        night_order_position: NightOrderPosition
    ):
        for page in self.pages:
            if (
                page.night >= night 
                and page.night_order_position > night_order_position
            ):
                continue
            page.apply_drunk(character, player)
        

    def can_be_character(
        self, 
        character: Role, 
        player: int,
        night: int,
        night_order_position: NightOrderPosition
    ):
        for page in self.pages:
            if (
                page.night >= night
                and page.night_order_position > night_order_position
            ):
                continue
            if not page.can_be_character(character, player):
                return False
        return True

    def can_be_red_herring(
        self, 
        player: int,
        night: int,
        night_order_position: NightOrderPosition
    ):
        for page in self.pages:
            if (
                page.night >= night
                and page.night_order_position > night_order_position
            ):
                continue
            if not page.can_be_red_herring( player):
                return False
        return True

    def make_deductions(self) -> bool:
        deduced = False
        for phase in self.pages:
            deduced |= phase.make_deductions()
        return deduced
    
    @staticmethod
    def _merge_character(c1: Role, c2: Role, p1: GrimoirePage):
        specific = role.get_overlapping(c1, c2, True)
        if (specific is None
            or (specific != c1 
                and specific not in ALLOWED_MULTIPLES 
                and specific in p1.characters)
            or (p1.drunk_token is not None 
                and specific == p1.drunk_token)):
            return None
        else:
            return specific

    @staticmethod
    def pass_through_pages(grim: Grimoire, to_pass: set[int]) -> PassThroughPagesResult: 
        changed: set[int] = set()
        for i in range(1, len(grim.pages)):
            if i-1 not in to_pass and i-1 not in changed and i not in to_pass:
                continue
            prev = grim.pages[i-1]
            curr = grim.pages[i]
            valid, reason, curr_changed = Grimoire.pass_between_pages(prev, curr)
            if not valid:
                return PassThroughPagesResult(False, reason, changed)
            if curr_changed:
                changed.add(i)
        return PassThroughPagesResult(True, "", changed)
    
    @staticmethod
    def pass_between_pages(prev: GrimoirePage, curr: GrimoirePage) -> PassBetweenPagesResult:
        changed = False
        # pass minion types
        for minion_type in prev.minion_types:
            if minion_type in curr.minion_types or minion_type == Role.ANY_OTHER_MINION:
                continue
            try:
                changed |= curr.add_minion_type(minion_type)
            except ValueError:
                return PassBetweenPagesResult(False, "mismatched minion types between pages", changed)
            
        # pass characters
        promotions = 0
        for i in range(len(prev.characters)):
            c1, c2 = curr.characters[i], prev.characters[i]
            # minion became demon
            if c1 == Role.IMP and c2 in GENERIC_MINION_SET:
                if gamerules.can_minion_become_demon(prev, curr, i):
                    promotions += 1
                    continue
                else:
                    return PassBetweenPagesResult(False, "invalid minion to demon character change", changed)
            # non demon can now be demon
            if (
                (c1 == Role.ANY_OTHER and c2 == Role.NON_DEMON)
                # known minions too, e.g. a Spy who caught a starpass
                or ((c1 == Role.ANY_OTHER_EVIL or c1 == Role.ANY_OTHER) and c2 in GENERIC_MINION_SET)
            ):
                if gamerules.can_non_demon_become_potential_demon(prev, curr, i):
                    continue
            result = Grimoire._merge_character(c1, c2, curr)
            if result is None:
                return PassBetweenPagesResult(False, "mismatched characters between pages", changed)
            changed |= curr.set_character(result, i)
        if promotions > 1:
            return PassBetweenPagesResult(False, "too many minions became demons", changed)
        
        # pass red herring
        if not curr.red_herring_moved:
            try:
                changed |= curr.add_red_herring(prev.red_herring)
            except ValueError:
                return PassBetweenPagesResult(False, "different red herrings", changed)

        # pass drunk token
        try:
            changed |= curr.set_drunk_token(prev.drunk_token)
        except ValueError:
            return PassBetweenPagesResult(False, "different Drunk tokens", changed)
            
        # pass deaths            
        changed |= curr.add_deaths(prev.dead)

        # check poisoning didn't change during same night
        if (prev.night == curr.night
            and True in prev.poisoned 
            and True in curr.poisoned
            and prev.poisoned.index(True) != curr.poisoned.index(True)):
            return PassBetweenPagesResult(False, "mismatched poisoned between pages", changed)
        
        valid, reason = validators.is_page_valid(curr)
        if not valid:
            return PassBetweenPagesResult(False, f"night {curr.night} {curr.night_order_position.name} page validity check failed. {reason}", changed)
        return PassBetweenPagesResult(True, "", changed)
