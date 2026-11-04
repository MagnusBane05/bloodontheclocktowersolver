from __future__ import annotations

from typing import Any, Callable, override

from .validators import ChangeType, get_affected_validators_forall, run_validators
from .deduced_page import deduce_from_chef_number
from . import helper
from .gamerules import ROLE_BREAKDOWNS
from . import gamerules, role, character_type
from itertools import compress
from .role import *
from grimoire.nightOrderPosition import NightOrderPosition
from .character_type import CharacterType

DEMON_CANDIDATE_SET = {
    Role.ANY_OTHER,
    Role.ANY_OTHER_EVIL,
    Role.IMP,
}

DEMON_OR_ANY_OTHER_SET = ANY_OTHER_ROLES_SET | {
    Role.IMP
}

MINION_CANDIDATE_SET = MINIONS_SET | {
    Role.ANY_OTHER_MINION,
    Role.ANY_OTHER_EVIL,
    Role.NON_DEMON,
    Role.ANY_OTHER
}

SCARLET_WOMAN_CANDIDATE_SET = {
    Role.ANY_OTHER_MINION,
    Role.ANY_OTHER_EVIL,
    Role.NON_DEMON,
    Role.ANY_OTHER
}

SLAYER_CANDIDATE_SET = {
    Role.SLAYER,
    Role.ANY_OTHER_TOWNSFOLK,
    Role.ANY_OTHER_GOOD,
    Role.ANY_OTHER
}

POSSIBLE_CHEF_PAIR_ROLES = EVIL_ROLES_SET | {
    Role.NON_DEMON,
    Role.ANY_OTHER,
}

_FIELD_CHANGE_TYPES = {
    'characters': ChangeType.CHARACTER,
    'minion_types': ChangeType.MINION_TYPE,
    'no_outsiders': ChangeType.LIBRARIAN_NO,
    'dead': ChangeType.DEATH,
    'poisoned': ChangeType.POISONED,
    'night_order_position': ChangeType.NIGHT_ORDER,
    'executee': ChangeType.EXECUTEE,
    'chef_number': ChangeType.CHEF_NUMBER,
    'in_chef_pair': ChangeType.CHEF_NUMBER,
    'not_in_chef_pair': ChangeType.CHEF_NUMBER,
    'recluse_needed': ChangeType.CHEF_NUMBER,
    'red_herring': ChangeType.RED_HERRING,
}

_FIELDS_NOT_VALIDATED = {
    'num_players',
    'drunk_token',
    'night',
    'star_passed',
    'slayer_shot',
    'red_herring_moved',
}

_FIELDS_NOT_IN_POISON_FREE_STATE = {'poisoned', 'night', 'night_order_position'}

class GrimoirePage:
    def __init__(self, num_players: int=5, night: int=1, night_order_position: NightOrderPosition=NightOrderPosition.AFTER_IMP):
        self.num_players: int = num_players
        self.characters: list[Role] = [Role.ANY_OTHER]*num_players
        self.poisoned: list[bool] = [False]*num_players
        self.minion_types: list[Role] = [Role.ANY_OTHER_MINION]*ROLE_BREAKDOWNS[num_players]['minions']
        self.red_herring: list[bool] = [False]*num_players
        self.dead: list[bool] = [False]*num_players
        self.drunk_token: Role | None = None
        self.chef_number: int | None = None
        self.in_chef_pair: int = 0
        self.not_in_chef_pair: int = 0
        self.recluse_needed: bool = False
        self.no_outsiders: bool = False
        self.night: int = night
        self.night_order_position: NightOrderPosition = night_order_position
        self.star_passed: bool = False
        self.executee: int | None = None
        self.slayer_shot: list[bool] = [False]*num_players
        self.red_herring_moved: bool = False
        
    @override
    def __eq__(self, other): # type: ignore  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        if not isinstance(other, GrimoirePage):
            return False
        other_vars = vars(other)
        for field, value in vars(self).items():  # pyright: ignore[reportAny]
            if field == "minion_types":
                # which minion slot a type was deduced in doesn't matter
                if set(self.minion_types) != set(other.minion_types):
                    return False
            elif value != other_vars[field]:
                return False
        return True
    
    @override
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
        page.slayer_shot = list(self.slayer_shot)
        page.drunk_token = self.drunk_token
        page.chef_number = self.chef_number
        page.in_chef_pair = self.in_chef_pair
        page.not_in_chef_pair = self.not_in_chef_pair
        page.recluse_needed = self.recluse_needed
        page.no_outsiders = self.no_outsiders
        page.star_passed = self.star_passed
        page.executee = self.executee
        page.red_herring_moved = self.red_herring_moved
        return page
    
    def loose_equals(self, other: GrimoirePage) -> bool:
        # A page with less poison still matches, so this can't tell if a poisoning was wrongly dropped
        return (
            all(helper.roleLooseEquals(self.characters[p], other.characters[p]) for p in range(self.num_players)) and 
            helper.minion_types_loose_equals(self.minion_types, other.minion_types) and
            sum(a or b for a, b in zip(self.poisoned, other.poisoned)) <= 1 and 
            sum(a or b for a, b in zip(self.red_herring, other.red_herring)) <= 1 and
            (self.chef_number is None or other.chef_number is None or self.chef_number == other.chef_number) and
            (self.drunk_token is None or other.drunk_token is None or self.drunk_token == other.drunk_token)
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

    def state_without_poison(self) -> tuple[Any,...]:  # pyright: ignore[reportExplicitAny]
        # hashable: minion types ignore order
        return tuple(  # pyright: ignore[reportUnknownVariableType]
            frozenset(value) if field == "minion_types"  # pyright: ignore[reportUnknownArgumentType, reportAny]
            else tuple(value) if isinstance(value, list) else value  # pyright: ignore[reportUnknownArgumentType]
            for field, value in vars(self).items()  # pyright: ignore[reportAny]
            if field not in _FIELDS_NOT_IN_POISON_FREE_STATE
        )

    def same_state(self, other: GrimoirePage) -> bool:
        other_vars = vars(other)
        for field, value in vars(self).items():  # pyright: ignore[reportAny]
            if value != other_vars[field]:
                return False
        return True

    def add_minion_type(self, type: Role) -> bool:
        if type not in MINIONS:
            raise ValueError("You are trying to add a non-minion role as a minion type.")
        if type in self.minion_types:
            return False
        try:
            idx = self.minion_types.index(Role.ANY_OTHER_MINION)
            self.minion_types[idx] = type
            return True
        except ValueError:
            raise ValueError("You are trying to add a minion type but this phase already has all minion types determined.")
    
    def remove_minion_type(self) -> None:
        if len(self.minion_types) == 0:
            raise Exception("You are trying to remove a minion from a phase with no minions.")
        self.minion_types = [Role.ANY_OTHER_MINION]*(len(self.minion_types)-1)
    
    def set_character(self, character: Role, player: int) -> bool:
        if self.characters[player] == character:
            return False
        self.characters[player] = character
        return True

    def apply_character(self, character: Role, player: int):
        original = self.characters[player]
        overlapping = role.get_overlapping(character, original)
        if overlapping is None:
            raise RuntimeError(f"Failed to apply {character.name} to player {player} with character {original.name}")
        self.characters[player] = overlapping
        # Need to add minion type if character is a minion
        if (character in MINIONS_SET and character not in self.minion_types):
            self.add_minion_type(character)
        if character in OUTSIDERS_SET or character == Role.ANY_OTHER_OUTSIDER:
            outsider_count = self.get_characters_of_type(CharacterType.OUTSIDER)
            max_outsider_count_baron = gamerules.get_outsider_count(self.num_players, True)
            if outsider_count > max_outsider_count_baron:
                raise RuntimeError(
                    f"Too many outsiders after adding {character}. "
                    f"Outsider count: {outsider_count}. "
                    f"Max outsiders with baron: {max_outsider_count_baron}"
                )
            max_outsider_count = gamerules.get_outsider_count(self.num_players, False)
            # If Baron is required, add it
            if (
                outsider_count > max_outsider_count 
                and Role.BARON not in self.minion_types
            ):
                self.add_minion_type(Role.BARON)
        return overlapping != original

    def set_drunk_token(self, token: Role | None) -> bool:
        if token is None:
            return False
        if self.drunk_token is None:
            self.drunk_token = token
            return True
        if self.drunk_token == token:
            return False
        raise ValueError(f"You're trying to add a Drunk token different to the current Drunk token, new: {token}, current: {self.drunk_token}")

    def apply_drunk(self, character: Role, player: int):
        _ = self.apply_character(Role.DRUNK, player)
        self.drunk_token = character

    def add_red_herring(self, rh: list[bool]) -> bool:
        combined = [a or b for a, b in zip(rh, self.red_herring)]
        if sum(combined) > 1:
            raise ValueError(f"You cannot add a red herring when a different red herring exists, new: {rh}, existing: {self.red_herring}")
        changed = combined != self.red_herring
        self.red_herring = combined
        return changed

    def apply_red_herring(self, player: int):
        self.red_herring[player] = True

    def clear_poisoned(self):
        self.poisoned = [False] * len(self.poisoned)

    def apply_poisoned(self, player: int):
        self.poisoned[player] = True
        _ = self.add_minion_type(Role.POISONER)

    def apply_no_outsiders(self):
        self.no_outsiders = True

    def apply_chef_number(self, number: int):
        self.chef_number = number

    def apply_slayer_shot(self, player: int):
        self.slayer_shot[player] = True

    def add_deaths(self, deaths: list[bool]) -> bool:
        new = [a or b for a, b in zip(deaths, self.dead)]
        changed = new != self.dead
        self.dead = new
        return changed

    def _can_apply(self, apply: Callable[[GrimoirePage], object]) -> bool:
        candidate = self.clone()
        try:
            _ = apply(candidate)
        except (RuntimeError, ValueError):
            return False
        changed = {changeType for field, changeType in _FIELD_CHANGE_TYPES.items()
                    if getattr(candidate, field) != getattr(self, field)}
        valid, _ = run_validators(candidate, get_affected_validators_forall(changed))
        return valid

    def can_be_character(self, character: Role, player: int) -> bool:
        original = self.characters[player]
        if original == character:
            return True
        
        overlapping = get_overlapping(character, original)
        if overlapping is None:
            return False
        # New character is broader than original        
        if overlapping == original:
            return True

        return self._can_apply(lambda page: page.apply_character(character, player))

    def can_be_red_herring(self, player: int):
        return self._can_apply(lambda page: page.apply_red_herring(player))
    
    def can_be_poisoned(self, player: int) -> bool:
        return self._can_apply(lambda page: page.apply_poisoned(player))
    
    def can_have_no_outsiders(self) -> bool:
        return self._can_apply(lambda page: page.apply_no_outsiders())

    def can_have_chef_number(self, number: int) -> bool:
        return self._can_apply(lambda page: page.apply_chef_number(number))

    def can_be_slayer_shot(self, player: int) -> bool:
        # Can't have other slayer shot
        for i, p in enumerate(self.slayer_shot):
            if i == player:
                continue
            if p:
                return False
            
        # Must be a Slayer claim or room for a Slayer
        return any(
            c in self.characters
            for c in SLAYER_CANDIDATE_SET
        )
    
    def can_be_dead(self, player: int) -> bool:
        # Can't be dead already
        if self.dead[player]:
            return False
        # Poisoner can't die if poisoning is active
        if self.characters[player] == Role.POISONER and True in self.poisoned:
            return False
        return True
    
    def make_deductions(self) -> bool:
        max_depth = 5
        deduced = False
        for _ in range(max_depth):
            deduced_this_step = self._deduction_step()
            if not deduced_this_step:
                break
            else:
                deduced = True
        return deduced

    def _deduction_step(self) -> bool:
        deduced = False

        dead = self.dead
        characters = self.characters
        minion_types = self.minion_types
        num_players = self.num_players

        known_good_count = 0
        known_minion_count = 0
        known_evil_count = 0
        evil_or_recluse_count = 0

        for i, c in enumerate(characters):
            if c in GOOD_ROLES:
                known_good_count += 1
            elif c in GENERIC_MINION_SET:
                known_minion_count += 1
                known_evil_count += 1
            elif c in EVIL_ROLES:
                known_evil_count += 1
            elif self.in_chef_pair & (1 << i):
                evil_or_recluse_count += 1

        if evil_or_recluse_count > 0:
            known_evil_count = known_evil_count + evil_or_recluse_count - 1

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
            if not dead[i] and c in DEMON_CANDIDATE_SET:
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
        if known_minion_count == minion_count:
            for i,c in enumerate(characters):
                if c == Role.NON_DEMON:
                    self.characters[i] = Role.ANY_OTHER_GOOD
                    deduced = True

        # assign good role to unknowns if all evils are accounted for
        evil_count = ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']
        if known_evil_count == evil_count:
            for i,c in enumerate(characters):
                if (
                    (c == Role.NON_DEMON or c == Role.ANY_OTHER)
                    and not self.in_chef_pair & (1 << i)
                ):
                    self.characters[i] = Role.ANY_OTHER_GOOD
                    deduced = True

        known_townsfolk_count = 0
        for c in characters:
            if c in GENERIC_TOWNSFOLK_SET:
                known_townsfolk_count += 1
        townsfolk_count_with_baron = gamerules.get_townsfolk_count(num_players, True)
        # assign leftover outsiders to good players if outsider count is known
        outsider_count_known = (
            Role.BARON in minion_types 
            or Role.ANY_OTHER_MINION not in minion_types
            or known_townsfolk_count > townsfolk_count_with_baron
        )

        if outsider_count_known:
            townsfolk_count = ROLE_BREAKDOWNS[num_players]["townsfolk"]-2 if Role.BARON in minion_types else ROLE_BREAKDOWNS[num_players]["townsfolk"]
            if known_townsfolk_count == townsfolk_count:
                for i,c in enumerate(characters):
                    if c == Role.ANY_OTHER_GOOD:
                        self.characters[i] = Role.ANY_OTHER_OUTSIDER
                        deduced = True

        # assign townsfolk to good players if outsider count is known
        if outsider_count_known:
            outsider_count = gamerules.get_outsider_count(num_players, Role.BARON in self.minion_types)
            known_outsider_count = 0
            for c in characters:
                if c in GENERIC_OUTSIDER_SET:
                    known_outsider_count += 1
            if known_outsider_count == outsider_count:
                for i,c in enumerate(characters):
                    if c == Role.ANY_OTHER_GOOD:
                        self.characters[i] = Role.ANY_OTHER_TOWNSFOLK
                        deduced = True
        
        if self.chef_number is not None:
            deduced |= deduce_from_chef_number(self)

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
            return idx
        except:
            pass
        known_minion_count = sum(1 for c in self.characters if c in GENERIC_MINION_SET)
        minions_accounted_for = known_minion_count == gamerules.get_minion_count(self.num_players)
        alive_known_minions = self.get_alive_players_of_type(GENERIC_MINION_SET)
        alive_possible_sw = self.get_alive_players_of_type(SCARLET_WOMAN_CANDIDATE_SET)
        assert(len(alive_possible_sw) > 0)
        alive_minion = None
        # All minions are known and there is only 1 alive
        if len(alive_known_minions) == 1 and minions_accounted_for:
            alive_minion = alive_known_minions[0]
            assert(self.characters[alive_minion]) == Role.ANY_OTHER_MINION
        # Only 1 alive player could possibly be the minion
        elif len(alive_possible_sw) == 1:
            alive_minion = alive_possible_sw[0]
        # Alive minion becomes the Imp
        if alive_minion is not None:
            self.characters[alive_minion] = Role.IMP
            return alive_minion

        # otherwise, all alive potential scarlet women could be the new demon
        for i in alive_possible_sw:
            c = self.characters[i]
            if c == Role.NON_DEMON:
                self.characters[i] = Role.ANY_OTHER
                continue
            elif c == Role.ANY_OTHER_MINION:
                self.characters[i] = Role.ANY_OTHER_EVIL

    def _promote_minion(self, minion: int):
        if self.dead[minion]:
            raise ValueError("Cannot promote a dead minion")
        if self.characters[minion] == Role.SPY and self.red_herring[minion]:
            self.red_herring[minion] = False
            self.red_herring_moved = True
        elif self.characters[minion] == Role.POISONER:
            self.poisoned = [False]*self.num_players
        self.characters[minion] = Role.IMP

    def find_red_herring_spy(self) -> int | None:
        characters = self.characters
        for i in range(len(characters)):
            if characters[i] == Role.SPY and self.red_herring[i] and not self.dead[i]:
                return i
        return None

    def find_scarlet_woman(self) -> int | None:
        characters = self.characters
        for i in range(len(characters)):
            if characters[i] == Role.SCARLET_WOMAN and not self.poisoned[i] and not self.dead[i]:
                return i
        return None

    # returns new imp if known
    def apply_starpass(self, imp: int, red_herring_spy_catches: bool = False) -> int | None:
        # dead player was the imp
        self.characters[imp] = Role.IMP
        self.star_passed = True
        
        if red_herring_spy_catches:
            spy = self.find_red_herring_spy()
            if spy is None:
                raise ValueError("Cannot apply starpass with Red Herring Spy catching without a Red Herring Spy")
            self._promote_minion(spy)
            return spy

        # if there's a known alive scarlet woman, they become the demon
        if Role.SCARLET_WOMAN in self.get_alive_characters():
            idx = self.characters.index(Role.SCARLET_WOMAN)
            if not self.poisoned[idx]:
                self._promote_minion(idx)
                return idx
        
        known_minion_count = sum(1 for c in self.characters if c in GENERIC_MINION_SET)
        minions_accounted_for = known_minion_count == gamerules.get_minion_count(self.num_players)
        alive_known_minions = self.get_alive_players_of_type(GENERIC_MINION_SET)
        alive_potential_minions = self.get_alive_players_of_type(MINION_CANDIDATE_SET)
        alive_minion = None
        # All minions are known and there is only 1 alive
        if len(alive_known_minions) == 1 and minions_accounted_for:
            alive_minion = alive_known_minions[0]
        # Only 1 alive player could possibly be the minion
        elif len(alive_potential_minions) == 1:
            alive_minion = alive_potential_minions[0]
        # Alive minion becomes the new demon
        if alive_minion is not None:
            self._promote_minion(alive_minion)
            return alive_minion

        # non-demons become any role
        # minions become any other evil
        # known demons become any other evil
        for i,c in enumerate(self.characters):
            if self.dead[i]:
                continue
            if c == Role.NON_DEMON:
                self.characters[i] = Role.ANY_OTHER
            if c == Role.ANY_OTHER_MINION or (c in MINIONS and not (c == Role.SPY and self.red_herring[i])):
                self.characters[i] = Role.ANY_OTHER_EVIL
    
    def get_alive_characters(self) -> list[Role]:
        return list(compress(self.characters, [not x for x in self.dead]))
    
    def get_alive_players(self) -> list[int]:
        return list(compress(range(len(self.characters)), [not x for x in self.dead]))
    
    def get_dead_players(self) -> list[int]:
        return list(compress(range(len(self.characters)), self.dead))
    
    def get_potential_alive_demons(self):
        alive_demons = [i for i, c in enumerate(self.characters) if not self.dead[i] and helper.roleLooseEquals(Role.IMP, c)]
        return alive_demons
    
    def get_known_evil_team(self):
        evil_team = [i for i,c in enumerate(self.characters) if c in EVIL_ROLES]
        return evil_team
    
    def get_characters_of_type(self, type: CharacterType):
        return sum(1 for c in self.characters if character_type.get_type(c) == type)

    def get_alive_characters_of_type(self, type: set[Role]):
        return [c for i, c in enumerate(self.characters) if not self.dead[i] and c in type]

    def get_alive_players_of_type(self, type: set[Role]):
        return [i for i,(c,d) in enumerate(zip(self.characters, self.dead)) if not d and c in type]

    def get_dead_characters_of_type(self, type: set[Role]):
        return [c for i, c in enumerate(self.characters) if self.dead[i] and c in type]

    def get_evil_count(self) -> int:
        return sum(1 for c in self.characters if c in EVIL_ROLES_SET)

    def get_good_count(self) -> int:
        return sum(1 for c in self.characters if c in GOOD_ROLES_SET)
