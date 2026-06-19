from __future__ import annotations

from . import helper


from .gamerules import ROLE_BREAKDOWNS
from . import gamerules
from itertools import compress
from .role import *
from grimoire.nightOrderPosition import NightOrderPosition

DEMON_CANDIDATE_ROLES = {
    Role.ANY_OTHER,
    Role.ANY_OTHER_EVIL,
    Role.IMP,
}

GENERIC_MINION_SET = MINIONS_SET | {
    Role.ANY_OTHER_MINION,
}

GENERIC_TOWNSFOLK_SET = TOWNSFOLK_SET | {
    Role.ANY_OTHER_TOWNSFOLK,
}

GENERIC_OUTSIDER_SET = OUTSIDERS_SET | {
    Role.ANY_OTHER_OUTSIDER,
}

class GrimoirePage:
    def __init__(self, num_players: int=5, night: int=1, night_order_position: NightOrderPosition=NightOrderPosition.AFTER_IMP):
        self.num_players = num_players
        self.characters: list[Role] = [Role.ANY_OTHER]*num_players
        self.poisoned: list[bool] = [False]*num_players
        self.minion_types: list[Role] = [Role.ANY_OTHER_MINION]*ROLE_BREAKDOWNS[num_players]['minions']
        self.red_herring: list[bool] = [False]*num_players
        self.dead: list[bool] = [False]*num_players
        self.drunk_token: Role | None = None
        self.chef_number: int | None = None
        self.no_outsiders: bool = False
        self.night: int = night
        self.night_order_position: NightOrderPosition = night_order_position
        self.character_changed: list[bool] = [False]*num_players
        self.star_passed: bool = False
        self.executee: int | None = None
        self.slayer_shot: list[bool] = [False]*num_players
        self.red_herring_moved = False
        
    def __eq__(self, other): # type: ignore
        if not isinstance(other, GrimoirePage):
            return False
        return (
            self.characters == other.characters and
            set(self.minion_types) == set(other.minion_types) and
            self.poisoned == other.poisoned and
            self.red_herring == other.red_herring
        )
    
    def __hash__(self):
        return hash((
            tuple(self.characters),
            frozenset(self.minion_types),
            tuple(self.poisoned),
            tuple(self.red_herring),
        ))
        
    def clone(self) -> GrimoirePage:
        page = GrimoirePage(self.num_players, self.night, self.night_order_position)
        page.characters = list(self.characters)
        page.minion_types = list(self.minion_types)
        page.poisoned = list(self.poisoned)
        page.red_herring = list(self.red_herring)
        page.dead = list(self.dead)
        page.character_changed = list(self.character_changed)
        page.slayer_shot = list(self.slayer_shot)
        page.drunk_token = self.drunk_token
        page.chef_number = self.chef_number
        page.no_outsiders = self.no_outsiders
        page.star_passed = self.star_passed
        page.executee = self.executee
        page.red_herring_moved = self.red_herring_moved
        return page
    
    def loose_equals(self, other: GrimoirePage) -> bool:
        return (
            all(helper.roleLooseEquals(self.characters[p], other.characters[p]) for p in range(self.num_players)) and 
            helper.minion_types_loose_equals(self.minion_types, other.minion_types) and
            sum(a or b for a, b in zip(self.poisoned, other.poisoned)) <= 1 and 
            sum(a or b for a, b in zip(self.red_herring, other.red_herring)) <= 1 and
            (self.chef_number is None or other.chef_number is None or self.chef_number == other.chef_number) and
            (self.chef_number is None or other.drunk_token is None or self.drunk_token == other.drunk_token)
        )
    
    def subsumes(self, other: GrimoirePage) -> bool:
        # Characters subsume     
        for i,c1 in enumerate(self.characters):
            c2 = other.characters[i]
            if not helper.role_subsumes(c1, c2):
                return False

        if not helper.minion_types_subsume(self.minion_types, other.minion_types):
            return False
        
        if self.poisoned != other.poisoned:
            return False
        
        if self.red_herring != other.red_herring:
            return False
        
        if (
            self.drunk_token is not None
            and other.drunk_token is not None
            and self.drunk_token != other.drunk_token
        ):
            return False
        
        # If both have chef numbers, make sure they match
        if (self.chef_number is not None 
            and other.chef_number is not None 
            and self.chef_number != other.chef_number
        ):
            return False
        
        return True

    def add_minion_type(self, type: Role) -> None:
        if type not in MINIONS:
            raise ValueError("You are trying to add a non-minion role as a minion type.")
        if type in self.minion_types:
            return
        try:
            idx = self.minion_types.index(Role.ANY_OTHER_MINION)
            self.minion_types[idx] = type
        except ValueError:
            raise ValueError("You are trying to add a minion type but this phase already has all minion types determined.")
    
    def remove_minion_type(self) -> None:
        if len(self.minion_types) == 0:
            raise Exception("You are trying to remove a minion from a phase with no minions.")
        self.minion_types = [Role.ANY_OTHER_MINION]*(len(self.minion_types)-1)
    
    def clear_poisoned(self):
        self.poisoned = [False] * len(self.poisoned)
    
    def make_deductions(self: GrimoirePage, num_players: int):
        max_depth = 5
        for _ in range(max_depth):
            if not self._deduction_step(num_players):
                break

    def _deduction_step(self: GrimoirePage, num_players: int) -> bool:
        deduced = False

        dead = self.dead
        characters = self.characters
        minion_types = self.minion_types

        known_good_count = 0
        known_minion_count = 0
        known_evil_count = 0

        for c in characters:
            if c in GOOD_ROLES:
                known_good_count += 1
            if c in GENERIC_MINION_SET:
                known_minion_count += 1
            if c in EVIL_ROLES:
                known_evil_count += 1

        # assign evil roles to player if all good players are accounted for
        good_player_count = ROLE_BREAKDOWNS[num_players]['townsfolk'] + ROLE_BREAKDOWNS[num_players]['outsiders']
        # known_good_count = sum(1 for c in characters if c in GOOD_ROLES)
        if known_good_count == good_player_count:
            for i,c in enumerate(characters):
                if c == Role.ANY_OTHER:
                    self.characters[i] = Role.ANY_OTHER_EVIL
                    deduced = True
                elif c == Role.NON_DEMON:
                    self.characters[i] = Role.ANY_OTHER_MINION
                    deduced = True

        # assign Imp to player if only one alive player could be the Imp
        potential_demon_count = 0
        potential_demon_idx = -1
        for i,c in enumerate(characters):
            if not dead[i] and c in DEMON_CANDIDATE_ROLES:
                potential_demon_count += 1
                potential_demon_idx = i
                if potential_demon_count > 1:
                    break

        if potential_demon_count == 1 and characters[potential_demon_idx] != Role.IMP:
            self.characters[potential_demon_idx] = Role.IMP
            deduced = True

        # check if alive Imp is known
        alive_imp = False
        for i,c in enumerate(characters):
            if c == Role.IMP and not dead[i]:
                alive_imp = True
                break
        # assign minions to evil players if alive Imp is known
        if alive_imp:
            for i,c in enumerate(characters):
                if c == Role.ANY_OTHER_EVIL:
                    self.characters[i] = Role.ANY_OTHER_MINION
                    deduced = True

        # assign minion types to one unknown minion if all minion types are known
        know_all_minion_types = Role.ANY_OTHER_MINION not in minion_types
        unassigned_minion_types = [c for c in minion_types if c not in characters]
        unknown_minions = [i for i,c in enumerate(characters) if c == Role.ANY_OTHER_MINION]
        if len(unknown_minions) == 1 and know_all_minion_types and len(unassigned_minion_types) == 1:
            self.characters[unknown_minions[0]] = unassigned_minion_types[0]
            deduced = True

        # assign good role to non demons and if all minions are accounted for
        minion_count = ROLE_BREAKDOWNS[num_players]['minions']
        # known_minion_count = sum(1 for c in characters if c in GENERIC_MINION_SET)
        if known_minion_count == minion_count:
            for i,c in enumerate(characters):
                if c == Role.NON_DEMON:
                    self.characters[i] = Role.ANY_OTHER_GOOD
                    deduced = True

        # assign good role to unknowns if all evils are accounted for
        evil_count = ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']
        # known_evil_count = sum(1 for c in characters if c in EVIL_ROLES)
        if known_evil_count == evil_count:
            for i,c in enumerate(characters):
                if c == Role.NON_DEMON or c == Role.ANY_OTHER:
                    self.characters[i] = Role.ANY_OTHER_GOOD
                    deduced = True

        # assign leftover outsiders to good players if outsider count is known
        outsider_count_known = Role.BARON in minion_types or Role.ANY_OTHER_MINION not in minion_types
        if outsider_count_known:
            townsfolk_count = ROLE_BREAKDOWNS[num_players]["townsfolk"]-2 if Role.BARON in minion_types else ROLE_BREAKDOWNS[num_players]["townsfolk"]
            # known_townsfolk_count = sum(1 for c in characters if c in GENERIC_TOWNSFOLK_SET)
            known_townsfolk_count = 0
            for c in characters:
                if c in GENERIC_TOWNSFOLK_SET:
                    known_townsfolk_count += 1
            if known_townsfolk_count == townsfolk_count:
                for i,c in enumerate(characters):
                    if c == Role.ANY_OTHER_GOOD:
                        self.characters[i] = Role.ANY_OTHER_OUTSIDER
                        deduced = True

        # assign townsfolk to good players if outsider count is known
        if outsider_count_known:
            outsider_count = gamerules.get_outsider_count(num_players, Role.BARON in self.minion_types)
            # known_outsider_count = sum(1 for c in characters if c in GENERIC_OUTSIDER_SET)
            known_outsider_count = 0
            for c in characters:
                if c in GENERIC_OUTSIDER_SET:
                    known_outsider_count += 1
            if known_outsider_count == outsider_count:
                for i,c in enumerate(characters):
                    if c == Role.ANY_OTHER_GOOD:
                        self.characters[i] = Role.ANY_OTHER_TOWNSFOLK
                        deduced = True
        
        return deduced
    
    # returns the index of the new demon if known
    def apply_sw_catch(self, demon: int):
        # dead player was the demon
        self.characters[demon] = Role.IMP
        self.star_passed = True

        # minion type becomes scarlet woman
        try:
            self.add_minion_type(Role.SCARLET_WOMAN)
        except ValueError:
            raise Exception("Scarlet Woman is not a valid minion type.")

        # if there's a known scarlet woman, they become the demon
        try:
            idx = self.characters.index(Role.SCARLET_WOMAN)
            self.characters[idx] = Role.IMP
            self.character_changed[idx] = True
            return idx
        except:
            pass

        # single alive minion becomes the demon
        # alive_known_minions = gamerules.get_alive_characters_of_type(self, {Role.ANY_OTHER_MINION})
        alive_possible_sw = self.get_alive_players_of_type({
            Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON
        })
        assert(len(alive_possible_sw) > 0)
        if len(alive_possible_sw) == 1:
            alive_sw = alive_possible_sw[0]
            self.characters[alive_sw] = Role.IMP
            self.character_changed[alive_sw] = True
            return alive_sw

        # otherwise, all alive potential scarlet women could be the new demon
        for i in alive_possible_sw:
            c = self.characters[i]
            if c == Role.NON_DEMON:
                self.characters[i] = Role.ANY_OTHER
                self.character_changed[i] = True
                continue
            elif c == Role.ANY_OTHER_MINION:
                self.characters[i] = Role.ANY_OTHER_EVIL
                self.character_changed[i] = True

    # returns new imp if known
    def apply_starpass(self, imp: int) -> int | None:
        # dead player was the imp
        self.characters[imp] = Role.IMP
        self.star_passed = True

        # if there's a known alive scarlet woman, they become the demon
        if Role.SCARLET_WOMAN in self.get_alive_characters():
            idx = self.characters.index(Role.SCARLET_WOMAN)
            if not self.poisoned[idx]:
                self.characters[idx] = Role.IMP
                self.character_changed[idx] = True
                return idx

        # single alive minion becomes the demon
        alive_potential_minion_players = self.get_alive_players_of_type(MINIONS_SET | {Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON})
        if len(alive_potential_minion_players) == 1:
            alive_minion_player = alive_potential_minion_players[0]
            old_minion = self.characters[alive_minion_player]
            assert not self.dead[alive_minion_player]
            self.characters[alive_minion_player] = Role.IMP
            self.character_changed[alive_minion_player] = True
            if old_minion == Role.POISONER:
                self.poisoned = [False]*self.num_players
            elif old_minion == Role.SPY and self.red_herring[alive_minion_player]:
                self.red_herring[alive_minion_player] = False
                self.red_herring_moved = True
            return alive_minion_player

        # non-demons become any role
        # any other minions become any other evil
        # known demons become any other evil
        for i,c in enumerate(self.characters):
            if self.dead[i]:
                continue
            if c == Role.NON_DEMON:
                self.characters[i] = Role.ANY_OTHER
                self.character_changed[i] = True
            if c == Role.ANY_OTHER_MINION or c in MINIONS:
                self.characters[i] = Role.ANY_OTHER_EVIL
                self.character_changed[i] = True

    def apply_non_demon_to_player(self, player: int):
        if self.characters[player] == Role.ANY_OTHER:
            self.characters[player] = Role.NON_DEMON
        elif self.characters[player] == Role.ANY_OTHER_EVIL:
            self.characters[player] = Role.ANY_OTHER_MINION
    
    def get_alive_characters(self) -> list[Role]:
        return list(compress(self.characters, [not x for x in self.dead]))
    
    def get_alive_players(self) -> list[int]:
        return list(compress(range(len(self.characters)), [not x for x in self.dead]))
    
    def get_dead_players(self) -> list[int]:
        return list(compress(range(len(self.characters)), self.dead))
    
    def get_potential_alive_demons(self):
        alive_demons = [i for i in self.get_alive_players() if helper.roleLooseEquals(Role.IMP, self.characters[i])]
        return alive_demons
    
    def get_known_evil_team(self):
        evil_team = [i for i,c in enumerate(self.characters) if c in EVIL_ROLES]
        return evil_team

    def get_alive_characters_of_type(self, type: set[Role]):
        return [c for i, c in enumerate(self.characters) if not self.dead[i] and c in type]

    def get_alive_players_of_type(self, type: set[Role]):
        return [i for i,(c,d) in enumerate(zip(self.characters, self.dead)) if not d and c in type]

    def get_dead_characters_of_type(self, type: set[Role]):
        return [c for i, c in enumerate(self.characters) if self.dead[i] and c in type]