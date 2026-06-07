from __future__ import annotations
from . import gamerules
from itertools import compress
from .role import *
from grimoire.nightOrderPosition import NightOrderPosition
from . import helper

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
        
    def clone(self) -> GrimoirePage:
        page = GrimoirePage(self.num_players, self.night, self.night_order_position)
        page.characters = list(self.characters)
        page.poisoned = list(self.poisoned)
        page.minion_types = list(self.minion_types)
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
    
    def remove_minion_type(self) -> None:
        if len(self.minion_types) == 0:
            raise Exception("You are trying to remove a minion from a phase with no minions.")
        self.minion_types = [Role.ANY_OTHER_MINION]*(len(self.minion_types)-1)
    
    def clear_poisoned(self):
        self.poisoned = [False] * len(self.poisoned)
    
    def make_deductions(self: GrimoirePage, num_players: int):
        deduced = True
        max_depth = 5
        d = 0
        while deduced and d < max_depth:
            deduced = self._deduction_step(num_players)
            d += 1

    def _deduction_step(self: GrimoirePage, num_players: int) -> bool:
        deduced = False

        minion_types = self.minion_types
        characters = self.characters
        alive_players = [i for i in range(num_players) if not self.dead[i]]
        alive_characters = [characters[i] for i in alive_players]

        # assign evil roles to player if all good players are accounted for
        good_player_count = ROLE_BREAKDOWNS[num_players]['townsfolk'] + ROLE_BREAKDOWNS[num_players]['outsiders']
        known_good_players = [i for i,c in enumerate(characters) if c in GOOD_ROLES]
        if len(known_good_players) == good_player_count:
            for i,c in enumerate(characters):
                if c == Role.ANY_OTHER:
                    self.characters[i] = Role.ANY_OTHER_EVIL
                    deduced = True
                elif c == Role.NON_DEMON:
                    self.characters[i] = Role.ANY_OTHER_MINION
                    deduced = True

        # assign Imp to player if only one alive player could be the Imp
        demon_roles = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.IMP]
        potential_demons = [i for i in alive_players if characters[i] in demon_roles]
        if len(potential_demons) == 1 and characters[potential_demons[0]] != Role.IMP:
            self.characters[potential_demons[0]] = Role.IMP
            deduced = True

        # assign minions to evil players if alive Imp is known
        if Role.IMP in alive_characters:
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
        minion_roles = MINIONS + [Role.ANY_OTHER_MINION]
        minion_count = ROLE_BREAKDOWNS[num_players]['minions']
        known_minions = [i for i,c in enumerate(characters) if c in minion_roles]
        if len(known_minions) == minion_count:
            for i,c in enumerate(characters):
                if c == Role.NON_DEMON:
                    self.characters[i] = Role.ANY_OTHER_GOOD
                    deduced = True

        # assign good role to unknowns if all evils are accounted for
        evil_count = ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']
        known_evil_players = [i for i,c in enumerate(characters) if c in EVIL_ROLES]
        if len(known_evil_players) == evil_count:
            for i,c in enumerate(characters):
                if c == Role.NON_DEMON or c == Role.ANY_OTHER:
                    self.characters[i] = Role.ANY_OTHER_GOOD
                    deduced = True

        # assign leftover outsiders to good players if outsider count is known
        outsider_count_known = Role.BARON in minion_types or Role.ANY_OTHER_MINION not in minion_types
        townsfolk_count = ROLE_BREAKDOWNS[num_players]["townsfolk"]-2 if Role.BARON in minion_types else ROLE_BREAKDOWNS[num_players]["townsfolk"]
        townsfolk_roles = TOWNSFOLK + [Role.ANY_OTHER_TOWNSFOLK]
        known_townsfolk = [i for i,c in enumerate(characters) if c in townsfolk_roles]
        if outsider_count_known and len(known_townsfolk) == townsfolk_count:
            for i,c in enumerate(characters):
                if c == Role.ANY_OTHER_GOOD:
                    self.characters[i] = Role.ANY_OTHER_OUTSIDER
                    deduced = True

        # assign townsfolk to good players if outsider count is known
        outsider_count = gamerules.get_outsider_count(num_players, Role.BARON in self.minion_types)
        outsider_roles = OUTSIDERS + [Role.ANY_OTHER_OUTSIDER]
        known_outsiders = [i for i,c in enumerate(characters) if c in outsider_roles]
        if outsider_count_known and len(known_outsiders) == outsider_count:
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
        alive_known_minions = gamerules.get_alive_characters_of_type(self, {Role.ANY_OTHER_MINION}) 
        if len(alive_known_minions) == 1:
            for i,c in enumerate(self.characters):
                if self.dead[i]:
                    continue
                if c in alive_known_minions:
                    self.characters[i] = Role.IMP
                    self.character_changed[i] = True
                    return i

        # if all minions are accounted for, there cannot be NON_DEMON roles, so any NON_DEMON roles could be potential scarlet women
        for i,c in enumerate(self.characters):
            if self.dead[i]:
                continue
            if c == Role.NON_DEMON:
                self.characters[i] = Role.ANY_OTHER
                self.character_changed[i] = True
                continue
            if c == Role.ANY_OTHER_MINION:
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
        alive_potential_minion_players = gamerules.get_alive_players_of_type(self, MINIONS_SET | {Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON})
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