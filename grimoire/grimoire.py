from __future__ import annotations
import bisect
from collections import Counter
from typing import override

from .nightOrderPosition import NightOrderPosition

from . import gamerules
from .role import *
from .errors import *
from .grimoire_page import GrimoirePage
from .helper import roleLooseEquals, minion_types_loose_equals

class Grimoire:
    def __init__(self, num_players:int=5):
        if num_players not in ROLE_BREAKDOWNS.keys():
            raise ValueError(f"{num_players} player worlds are not yet handled.")
        self.pages: list[GrimoirePage] = [GrimoirePage(num_players,1)]
        self.keys: list[tuple[int, NightOrderPosition]] = [self._page_key(GrimoirePage(num_players,1))]
        self.num_players = num_players

    @override
    def __eq__(self, value: object):
        if not isinstance(value, Grimoire):
            return False
        players = len(self.pages[0].characters)
        if players != len(value.pages[0].characters):
            return False
        for page in self.pages:
            night = page.night
            night_order_position = page.night_order_position
            other_page = value.get_page(night, night_order_position)
            if other_page == None:
                continue
            # print("Characters")
            # for i in range(players):
            #     print(f"{i}. {phase.characters[i].name:<15} - {other_phase.characters[i].name}")
            # print("Minion types")
            # for i in range(len(phase.minion_types)):
            #     print(f"{i}. {phase.minion_types[i].name:<15} - {other_phase.minion_types[i].name}")
            equal = (
                all(roleLooseEquals(page.characters[p], other_page.characters[p]) for p in range(players)) and 
                minion_types_loose_equals(page.minion_types, other_page.minion_types) and
                sum(a or b for a, b in zip(page.poisoned, other_page.poisoned)) <= 1 and 
                sum(a or b for a, b in zip(page.red_herring, other_page.red_herring)) <= 1
            )
            if not equal:
                return False
        return True

    def __hash__(self):
        return hash(tuple(hash(p) for p in self.pages))

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
    
    def clone(self):
        new = Grimoire(self.num_players)
        new.pages = [p.clone() for p in self.pages]
        new.keys = self.keys.copy()
        return new
    
    @staticmethod
    def _page_key(page: GrimoirePage) :
        return (page.night, page.night_order_position)

    def get_page(self, night: int, night_order_position: NightOrderPosition) -> GrimoirePage | None:
        key = (night, night_order_position)
        i = bisect.bisect_left(self.keys, key)

        if i < len(self.pages) and self._page_key(self.pages[i]) == key:
            return self.pages[i]

        return None
        # raise PhaseNotFoundError(f"Grimoire does not contain page with night {night} and night order position {night_order_position}")

    def add_page(self, night: int, night_order_position: NightOrderPosition, page: GrimoirePage | None = None) -> GrimoirePage:
        key = (night, night_order_position)
        i = bisect.bisect_left(self.keys, key)

        if i < len(self.pages) and self._page_key(self.pages[i]) == key:
            raise PhaseInWorldError(f"Grimoire already contains page with night {night} and night order position {night_order_position}")
        
        if i == 0:
            raise IndexError("You should not be adding a page before the first page.")

        prev = self.pages[i-1]
        new_page = prev.clone() if page is None else page
        new_page.night = night
        new_page.night_order_position = night_order_position
        if page is None:
            new_page.poisoned = [False]*len(new_page.poisoned)
        self.pages.insert(i, new_page)
        self.keys.insert(i, key)
        return new_page

    
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


    def apply_non_demon_to_player(self, player: int, page: GrimoirePage):
        page.apply_non_demon_to_player(player)
        for p in self.get_all_previous_pages(page):
            p.apply_non_demon_to_player(player)

    def apply_role_to_player(self, player: int, role: Role, page: GrimoirePage):
        page.characters[player] = role
        for p in self.get_all_previous_pages(page):
            p.characters[player] = role

    def get_all_previous_pages(self, page: GrimoirePage):
        key = self._page_key(page)
        i = bisect.bisect_left(self.keys, key)

        return [self.pages[j] for j in range(0, i)]
    
    def get_unique_nights(self):
        nights: set[int] = set()
        for page in self.pages:
            nights.add(page.night)        
        return nights

    def make_deductions(self):
        for phase in self.pages:
            phase.make_deductions(self.num_players)
    
    @classmethod
    def combine(cls, w1: Grimoire, w2: Grimoire) -> tuple[Grimoire, bool, str]:
        if w1.num_players != w2.num_players:
            raise Exception("You are trying to combine worlds with different numbers of players.")

        num_players = w1.num_players

        new_world = Grimoire(num_players)
        new_world.pages = []
        new_world.keys = []

        i = 0
        j = 0

        while i < len(w1.pages) or j < len(w2.pages):
            # page only in w1
            if j >= len(w2.pages) or (i < len(w1.pages) and w1.keys[i] < w2.keys[j]):
                key = w1.keys[i]
                new_page = w1.pages[i].clone()
                i += 1
            # page only in w2
            elif i >= len(w1.pages) or w2.keys[j] < w1.keys[i]:
                key = w2.keys[j]
                new_page = w2.pages[j].clone()
                j += 1
            # both grims have page with this key
            else:
                key = w1.keys[i]
                p1 = w1.pages[i]
                p2 = w2.pages[j]

                if key == (1, NightOrderPosition.AFTER_IMP):
                    new_page = GrimoirePage(num_players, 1)
                else:
                    new_page = GrimoirePage(num_players, key[0])
                    new_page.night_order_position = key[1]

                phase_0 = new_world.pages[0] if new_world.pages else new_page
                valid, reason = Grimoire._combine_pages(phase_0, new_page, num_players, p1, p2)
                if not valid:
                    return w1, False, reason
                i += 1
                j += 1

            new_page.night = key[0]
            new_page.night_order_position = key[1]

            new_world.pages.append(new_page)
            new_world.keys.append(key)

            if len(new_world.pages) > 1:
                valid, reason = Grimoire._pass_between_pages(new_world.pages[-2], new_world.pages[-1])
                if not valid:
                    return w1, False, reason

        if not gamerules.is_grim_valid(new_world):
            return w1, False, "invalid grim"

        Grimoire.make_deductions(new_world)

        return new_world, True, ""

    @staticmethod
    def _combine_pages(phase_0: GrimoirePage, new_phase: GrimoirePage, num_players: int, p1: GrimoirePage, p2: GrimoirePage) -> tuple[bool, str]:
        # Minion types
        if not Grimoire._combine_minion_types(new_phase, p1, p2):
            return False, "invalid combined minion types"

        for i in range(num_players):
            c1, c2 = p1.characters[i], p2.characters[i]
            result = Grimoire._combine_characters(c1, c2, p1)
            if result is None:
                return False, "characters do not match"
            new_phase.characters[i] = result

        # Make sure the minions match the minion types
        if not Grimoire._validate_minion_types(new_phase):
            return False, "invalid minion types"
        
        # Combine no outsiders and make sure Baron still works
        if not Grimoire._combine_no_outsiders(new_phase, p1, p2):
            return False, "mismatched no outsiders"

        # Combine and validate chef numbers
        if new_phase.night == 1 and not Grimoire._combine_chef_number(new_phase, p1, p2, num_players):
            return False, "mismatched chef numbers"
        
        if not Grimoire._combine_deaths(new_phase, p1, p2, num_players):
            return False, "mismatched deaths"

        # Poisoner logic
        if not Grimoire._combine_poisoned(new_phase, p1, p2, num_players):
            return False, "invalid poisoned"

        # Outsider, evil and good count checks
        if (not gamerules.is_outsider_count_valid(phase_0, num_players)
            or not gamerules.is_evil_count_valid(new_phase, num_players)
            or not gamerules.is_good_count_valid(new_phase, num_players)
        ):
            return False, "invalid player counts"
        
        # Check if there's more than one red herring or if the red herring is on an evil player
        if not Grimoire._combine_red_herring(new_phase, p1, p2, num_players):
            return False, "mismatched red herring"

        # Combine star passed and character changed
        new_phase.star_passed = p1.star_passed or p2.star_passed
        for i in range(num_players):
            new_phase.character_changed[i] = p1.character_changed[i] or p2.character_changed[i]

        return True, ""

    @staticmethod
    def _combine_minion_types(new_phase: GrimoirePage, p1: GrimoirePage, p2: GrimoirePage):
        if len(p1.minion_types) != len(p2.minion_types):
            raise Exception('Trying to combine phases with different numbers of minions. Something has gone terribly wrong.')
        
        # combine the two lists of minions, remove duplicates and ANY_OTHER_MINION
        unique_minions = list(set(p1.minion_types + p2.minion_types) - set([Role.ANY_OTHER_MINION]))

        # if the resulting list of minions is greater than either phase allows, that's an invalid world
        if len(unique_minions) > len(p1.minion_types):
            return False
        
        # add back in ANY_OTHER_MINION until we're at the right number of minions
        while len(unique_minions) < len(p1.minion_types):
            unique_minions.append(Role.ANY_OTHER_MINION)

        new_phase.minion_types = unique_minions
        return True

    @staticmethod
    def _combine_characters(c1: Role, c2: Role, p1: GrimoirePage):
        if c1 == c2:
            return c1
        if c1 not in ANY_OTHER_ROLES:
            return Grimoire._combine_specific_character(c1, c2)
        if c1 == Role.ANY_OTHER_EVIL:
            return Grimoire._combine_any_evil(c2, p1)
        if c1 == Role.ANY_OTHER_GOOD:
            return Grimoire._combine_any_good(c2, p1)
        if c1 == Role.ANY_OTHER_MINION:
            return Grimoire._combine_any_other_minion(c2, p1)
        if c1 == Role.ANY_OTHER_TOWNSFOLK:
            return Grimoire._combine_any_other_townsfolk(c2, p1)
        if c1 == Role.ANY_OTHER_OUTSIDER:
            return Grimoire._combine_any_other_outsider(c2, p1)
        if c1 == Role.NON_DEMON:
            return Grimoire._combine_non_demon(c2, p1)
        if c1 == Role.ANY_OTHER:
            return Grimoire._combine_any_other(c2, p1)
        return None

    @staticmethod
    def _combine_specific_character(c1: Role, c2: Role):
        if c2 not in ANY_OTHER_ROLES and c2 != c1:
            return None
        if c2 == Role.ANY_OTHER_EVIL and c1 in EVIL_CHARACTERS:
            return c1
        if c2 == Role.ANY_OTHER_GOOD and c1 in GOOD_CHARACTERS:
            return c1
        if c2 == Role.ANY_OTHER_MINION and c1 in MINIONS:
            return c1
        if c2 == Role.ANY_OTHER_OUTSIDER and c1 in OUTSIDERS:
            return c1
        if c2 == Role.ANY_OTHER_TOWNSFOLK and c1 in TOWNSFOLK:
            return c1
        if c2 == Role.NON_DEMON and c1 != Role.IMP:
            return c1
        if c2 in [Role.ANY_OTHER, c1]:
            return c1
        return None

    @staticmethod
    def _combine_any_evil(c2: Role, p1: GrimoirePage):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_EVIL
        if c2 == Role.ANY_OTHER_GOOD:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return c2
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_MINION
        if c2 not in EVIL_CHARACTERS:
            return None
        if c2 == Role.IMP:
            return c2
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_good(c2: Role, p1: GrimoirePage):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_GOOD
        if c2 == Role.ANY_OTHER_EVIL:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return None
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return c2
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_GOOD
        if c2 not in GOOD_CHARACTERS:
            return None
        if p1.drunk_token is not None and c2 == p1.drunk_token:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other_minion(c2: Role, p1: GrimoirePage):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_MINION
        if c2 == Role.ANY_OTHER_GOOD:
            return None
        if c2 == Role.ANY_OTHER_EVIL:
            return Role.ANY_OTHER_MINION
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_MINION
        if c2 not in MINIONS:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other_townsfolk(c2: Role, p1: GrimoirePage):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_TOWNSFOLK
        if c2 == Role.ANY_OTHER_GOOD:
            return Role.ANY_OTHER_TOWNSFOLK
        if c2 == Role.ANY_OTHER_EVIL:
            return None
        if c2 == Role.ANY_OTHER_OUTSIDER:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_TOWNSFOLK
        if c2 not in TOWNSFOLK:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other_outsider(c2: Role, p1: GrimoirePage):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_OUTSIDER
        if c2 == Role.ANY_OTHER_GOOD:
            return Role.ANY_OTHER_OUTSIDER
        if c2 == Role.ANY_OTHER_EVIL:
            return None
        if c2 == Role.ANY_OTHER_TOWNSFOLK:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_OUTSIDER
        if c2 not in OUTSIDERS:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_non_demon(c2: Role, p1: GrimoirePage):
        if c2 == Role.ANY_OTHER:
            return Role.NON_DEMON
        if c2 == Role.ANY_OTHER_EVIL:
            return Role.ANY_OTHER_MINION
        if c2 == Role.ANY_OTHER_GOOD:
            return Role.NON_DEMON
        if c2 == Role.ANY_OTHER_MINION:
            return c2
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return c2
        if c2 == Role.IMP:
            return None
        if p1.drunk_token is not None and c2 == p1.drunk_token:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other(c2: Role, p1: GrimoirePage):
        if c2 in ANY_OTHER_ROLES:
            return c2
        if p1.drunk_token is not None and c2 == p1.drunk_token:
            return None
        if c2 == Role.IMP:
            return c2
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _validate_minion_types(phase: GrimoirePage):
        for c in phase.characters:
            if c not in MINIONS or c in phase.minion_types:
                continue
            try:
                # if there's room to replace ANY_OTHER_MINION with the specific character, do it. Otherwise, not a valid world
                idx = phase.minion_types.index(Role.ANY_OTHER_MINION)
                phase.minion_types[idx] = c
            except ValueError:
                return False
        return True
    
    @staticmethod
    def _combine_no_outsiders(new_phase: GrimoirePage, p1: GrimoirePage, p2: GrimoirePage):
        new_phase.no_outsiders = p1.no_outsiders or p2.no_outsiders
        return not (new_phase.no_outsiders and Role.BARON in new_phase.minion_types)

    @staticmethod
    def _combine_chef_number(new_phase: GrimoirePage, p1: GrimoirePage, p2: GrimoirePage, num_players: int):
        # If both have chef numbers and they conflict, invalid
        if p1.chef_number is not None and p2.chef_number is not None and p1.chef_number != p2.chef_number:
            return False

        # Carry forward the known chef number if any
        new_phase.chef_number = p1.chef_number if p1.chef_number is not None else p2.chef_number
        if new_phase.chef_number is None:
            return True

        chef_number = new_phase.chef_number
        characters = new_phase.characters
        minion_types = new_phase.minion_types

        # Could an unknown player be the spy
        spy_possible = Role.SPY not in characters and (Role.SPY in minion_types or Role.ANY_OTHER_MINION in minion_types)

        # Could an unknown player be the recluse
        known_outsiders = sum(1 for c in characters if c in OUTSIDERS)
        baron_possible = Role.BARON in minion_types or Role.ANY_OTHER_MINION in minion_types
        max_outsiders = ROLE_BREAKDOWNS[num_players]['outsiders'] + 2 if baron_possible else ROLE_BREAKDOWNS[num_players]['outsiders']
        recluse_possible = Role.RECLUSE not in characters and known_outsiders < max_outsiders

        # Precompute predicates for each character
        definitely_evil = [False] * num_players
        possibly_evil = [False] * num_players
        could_be_recluse = [False] * num_players
        evil_could_be_spy = [False] * num_players

        for i in range(num_players):
            role = characters[i]
            if role == Role.SPY:
                definitely_evil[i] = False
                possibly_evil[i] = True
                could_be_recluse[i] = False
                evil_could_be_spy[i] = False
            elif role in EVIL_CHARACTERS:
                definitely_evil[i] = True
                possibly_evil[i] = True
                could_be_recluse[i] = False
                evil_could_be_spy[i] = False
            elif not spy_possible and role in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]:
                definitely_evil[i] = True
                possibly_evil[i] = True
                could_be_recluse[i] = False
                evil_could_be_spy[i] = False
            elif role in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]:
                definitely_evil[i] = False
                possibly_evil[i] = True
                could_be_recluse[i] = False
                evil_could_be_spy[i] = True
            elif role in [Role.ANY_OTHER, Role.NON_DEMON]:
                definitely_evil[i] = False
                possibly_evil[i] = True
                could_be_recluse[i] = True
                evil_could_be_spy[i] = False
            elif role == Role.RECLUSE:
                definitely_evil[i] = False
                possibly_evil[i] = True
                could_be_recluse[i] = False
                evil_could_be_spy[i] = False
            else:
                definitely_evil[i] = False
                possibly_evil[i] = False
                could_be_recluse[i] = role in [Role.ANY_OTHER, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_OUTSIDER]
                evil_could_be_spy[i] = False

        pairs = [(i, (i + 1) % num_players) for i in range(num_players)]

        min_pairs = 0
        max_pairs = 0

        recluse_needed: list[int] = []
        possible_spies: list[int] = []
        spies_needed = 0

        for i, j in pairs:
            if definitely_evil[i] and definitely_evil[j]:
                min_pairs += 1
            elif definitely_evil[i] and evil_could_be_spy[j]:
                possible_spies.append(j)
                spies_needed += 1
            elif evil_could_be_spy[i] and definitely_evil[j]:
                possible_spies.append(i)
                spies_needed += 1
            elif evil_could_be_spy[i] and evil_could_be_spy[j]:
                possible_spies.extend([i, j])
                spies_needed += 1

            if possibly_evil[i] and possibly_evil[j]:
                max_pairs += 1
            elif possibly_evil[i] and could_be_recluse[j]:
                recluse_needed.append(j)
            elif could_be_recluse[i] and possibly_evil[j]:
                recluse_needed.append(i)

        recluse_counter = Counter(recluse_needed)
        recluse_impact = max(recluse_counter.values()) if recluse_counter else 0
        max_pairs += recluse_impact if recluse_possible else 0

        spy_counter = Counter(possible_spies)
        spy_impact = max(spy_counter.values()) if spy_counter else 0
        min_pairs += spies_needed - spy_impact if spy_possible else 0

        # Global evil count constraint
        max_evils = ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']
        max_pairs = min(max_pairs, max_evils)

        return min_pairs <= chef_number <= max_pairs


    @staticmethod
    def _combine_poisoned(new_phase: GrimoirePage, p1: GrimoirePage, p2: GrimoirePage, num_players: int):
        for i in range(num_players):
            new_phase.poisoned[i] = p1.poisoned[i] or p2.poisoned[i]
        return gamerules.is_poisoning_valid(new_phase, num_players)

    @staticmethod
    def _combine_red_herring(new_phase: GrimoirePage, p1: GrimoirePage, p2: GrimoirePage, num_players: int):
        # combine the two phases
        for i in range(num_players):
            new_phase.red_herring[i] = p1.red_herring[i] or p2.red_herring[i]

        # more than one red herring
        if sum(new_phase.red_herring) > 1:
            return False

        # make sure the red herring doesn't belong to an evil player
        for i in range(num_players):
            if new_phase.red_herring[i] and new_phase.characters[i] in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.IMP] + MINIONS and new_phase.characters[i] != Role.SPY:
                    return False
                
        return True

    @staticmethod
    def _combine_deaths(new_phase: GrimoirePage, p1: GrimoirePage, p2: GrimoirePage, num_players: int):
        # combine the phases
        for i in range(num_players):
            new_phase.dead[i] = p1.dead[i] or p2.dead[i]
        
        return True

    @staticmethod
    def pass_through_pages(world: Grimoire) -> tuple[bool, str]:
        for i in range(1, len(world.pages)):
            prev = world.pages[i-1]
            curr = world.pages[i]
            valid, reason = Grimoire._pass_between_pages(prev, curr)
            if not valid:
                return False, reason
                
        if not gamerules.is_grim_valid(world):
            return False, "invalid grim"

        return True, ""
    
    @staticmethod
    def _pass_between_pages(prev: GrimoirePage, curr: GrimoirePage) -> tuple[bool, str]:

        # pass characters
        for i in range(len(prev.characters)):
            if curr.character_changed[i]:
                continue
            if prev.character_changed[i]:
                curr.characters[i] = prev.characters[i]
                curr.character_changed[i] = True
                continue
            c1, c2 = curr.characters[i], prev.characters[i]
            result = Grimoire._combine_characters(c1, c2, curr)
            if result is None:
                return False, "mismatched characters between pages"
            curr.characters[i] = result            

        # pass minion types
        for minion_type in prev.minion_types:
            if minion_type in curr.minion_types or minion_type == Role.ANY_OTHER_MINION:
                continue
            try:
                curr.add_minion_type(minion_type)
            except ValueError:
                return False, "mismatched minion types between pages"
        
        # pass red herring
        if not curr.red_herring_moved:
            for j, value in enumerate(prev.red_herring):
                if value:
                    curr.red_herring[j] = True
            
            if sum(curr.red_herring) > 1:
                return False, "mismatched red herrings between pages"

        # pass drunk token
        if prev.drunk_token is not None:
            if curr.drunk_token is None:
                curr.drunk_token = prev.drunk_token
            elif prev.drunk_token != curr.drunk_token:
                return False, "mismatched drunk token between pages"        

        # pass chef number
        if prev.chef_number is not None:
            if curr.chef_number is None:
                curr.chef_number = prev.chef_number
            elif prev.chef_number != curr.chef_number:
                return False, "mismatched chef number between pages"
            
        # pass deaths            
        curr.dead = [a or b for a, b in zip(curr.dead, prev.dead)]

        # check poisoning didn't change during same night
        if (prev.night == curr.night
            and True in prev.poisoned 
            and True in curr.poisoned
            and prev.poisoned.index(True) != curr.poisoned.index(True)):
            return False, "mismatched poisoned between pages"
        
        return True, ""
