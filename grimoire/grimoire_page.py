from __future__ import annotations

from collections import Counter
from typing import NamedTuple

from . import helper


from .gamerules import ROLE_BREAKDOWNS
from . import gamerules, role, character_type
from itertools import combinations, compress
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

DEDUCIBLE_UNKNOWN_ROLES = {
    Role.ANY_OTHER,
    Role.NON_DEMON,
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
        self.in_chef_pair: int = 0
        self.not_in_chef_pair: int = 0
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
        page.in_chef_pair = self.in_chef_pair
        page.not_in_chef_pair = self.not_in_chef_pair
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

    def apply_drunk(self, character: Role, player: int):
        self.apply_character(Role.DRUNK, player)
        self.drunk_token = character

    def apply_red_herring(self, player: int):
        self.red_herring[player] = True

    def apply_poisoned(self, player: int):
        self.poisoned[player] = True
        self.add_minion_type(Role.POISONER)

    def apply_no_outsiders(self):
        self.no_outsiders = True

    def apply_chef_number(self, number: int):
        self.chef_number = number

    def apply_slayer_shot(self, player: int):
        self.slayer_shot[player] = True

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
        # New character is more specific
        if not self._can_be_type(overlapping, player):
            return False
        # No repeats
        for i, c in enumerate(self.characters):
            if i == player:
                continue
            if character in DEMON_OR_ANY_OTHER_SET:
                continue
            if character == c:
                return False
        # Minion is in or can be added to minion types
        if overlapping in MINIONS_SET:
            if not (
                overlapping in self.minion_types
                or Role.ANY_OTHER_MINION in self.minion_types
            ):
                return False
        # If minion is Baron, make sure +2 outsiders is possible
        if overlapping == Role.BARON:
            townsfolk_count = self.get_characters_of_type(CharacterType.TOWNSFOLK)
            max_townsfolk_count_baron = gamerules.get_townsfolk_count(self.num_players, True)
            if townsfolk_count > max_townsfolk_count_baron:
                return False
        # If player is in Chef pair, make sure character is evil or Recluse
        if self.in_chef_pair & (1 << player):
            if (
                overlapping != Role.RECLUSE
                and overlapping not in EVIL_ROLES_SET
                and overlapping not in (Role.NON_DEMON, Role.ANY_OTHER)
            ):
                return False
        return True

    def _can_be_type(self, character: Role, player: int) -> bool:
        type = character_type.get_type(character)
        original_type = character_type.get_type(self.characters[player])
        num_players = self.num_players
        # this should be covered by can_be_character
        if not type.loose_equals(original_type):
            return False
        # same with this
        if type == original_type:
            return True
        # and this
        if type == CharacterType.ANY:
            return True
        elif type == CharacterType.NON_DEMON:
            return True
        elif type == CharacterType.ANY_EVIL:
            evils = self.get_evil_count()
            max_evils = gamerules.get_evil_count(num_players)
            return evils < max_evils
        elif type == CharacterType.ANY_GOOD:
            goods = self.get_good_count()
            max_goods = gamerules.get_good_count(num_players)
            return goods < max_goods
        elif type == CharacterType.TOWNSFOLK:
            townsfolk = self.get_characters_of_type(CharacterType.TOWNSFOLK)
            baron = Role.BARON in self.minion_types
            max_townsfolk = gamerules.get_townsfolk_count(num_players, baron)
            return townsfolk < max_townsfolk
        elif type == CharacterType.OUTSIDER:
            if self.no_outsiders:
                if character in NON_RECLUSE_OUTSIDERS:
                    return False
                # Recluse with outsider count of 0 or 2 with Librarian None
                no_baron_outsider_count = gamerules.get_outsider_count(num_players, False)
                if no_baron_outsider_count == 0 or no_baron_outsider_count == 2:
                    return False
            outsiders = self.get_characters_of_type(CharacterType.OUTSIDER)
            baron = Role.BARON in self.minion_types or Role.ANY_OTHER_MINION in self.minion_types
            # check that there aren't too many townsfolk for a Baron
            townsfolk_count = self.get_characters_of_type(CharacterType.TOWNSFOLK)
            townsfolk_count_with_baron = gamerules.get_townsfolk_count(num_players, True)
            if townsfolk_count > townsfolk_count_with_baron:
                baron = False
            max_outsiders = gamerules.get_outsider_count(num_players, baron)
            return outsiders < max_outsiders
        elif type == CharacterType.MINION:
            minions = self.get_characters_of_type(CharacterType.MINION)
            max_minions = gamerules.get_minion_count(num_players)
            return  minions < max_minions
        elif type == CharacterType.DEMON:
            return not Role.IMP in self.get_alive_characters()
        else:
            raise RuntimeError(f"Character cannot be type {type.name}")     

    def can_be_red_herring(self, player: int):
        # Can't have another red herring
        for i, rh in enumerate(self.red_herring):
            if i == player:
                continue
            if rh:
                return False
        return True
    
    def can_be_poisoned(self, player: int) -> bool:
        # Can't have other poisoning
        for i, p in enumerate(self.poisoned):
            if i == player:
                continue
            if p:
                return False
            
        # Poisoner must be in minion types or can be added to minion types
        if not (
            Role.POISONER in self.minion_types
            or Role.ANY_OTHER_MINION in self.minion_types
        ) :
            return False
    
        # Poisoner can't be dead
        dead_characters = [c for i, c in enumerate(self.characters) if self.dead[i]]
        if Role.POISONER in dead_characters:
            return False
        
        # false if all minions are dead (check evil roles, not just minions, in case of star passes)
        if sum(1 for c in dead_characters if c in EVIL_ROLES) == gamerules.get_minion_count(self.num_players):
            return False
        
        return True
    
    def can_have_no_outsiders(self) -> bool:
        # Can't have any non-recluse outsiders
        if any(c in NON_RECLUSE_OUTSIDERS for c in self.characters):
            return False
        
        # Can't have Baron
        if Role.BARON in self.minion_types:
            return False

        base_outsider_count = gamerules.get_outsider_count(self.num_players, False)
        recluse = any(gamerules.can_player_be_recluse(c) for c in self.characters)
        non_recluse_outsiders = base_outsider_count - 1 if recluse else base_outsider_count
        return non_recluse_outsiders <= 0
    
    def can_have_chef_number(self, number: int) -> bool:
        if number < 0:
            return False
        if self.chef_number is not None and self.chef_number != number:
            return False

        characters = self.characters
        minion_types = self.minion_types
        num_players = self.num_players

        spy_possible = (
            Role.SPY not in characters
            and (Role.SPY in minion_types or Role.ANY_OTHER_MINION in minion_types)
        )

        known_outsiders = sum(1 for c in characters if c in OUTSIDERS)
        baron_possible = Role.BARON in minion_types or Role.ANY_OTHER_MINION in minion_types
        max_outsiders = gamerules.get_outsider_count(num_players, baron_possible)
        recluse_possible = Role.RECLUSE not in characters and known_outsiders < max_outsiders

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

        max_evils = gamerules.get_evil_count(num_players)
        max_pairs = min(max_pairs, max_evils)

        return min_pairs <= number <= max_pairs

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
    
    def make_deductions(self):
        max_depth = 5
        for _ in range(max_depth):
            if not self._deduction_step():
                break

    def _deduction_step(self) -> bool:
        deduced = False

        dead = self.dead
        characters = self.characters
        minion_types = self.minion_types
        num_players = self.num_players

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
            deduced |= self._deduce_from_chef_number()

        return deduced
    
    def _deduce_from_chef_number(self) -> bool:
        deduced = False
        chef_number = self.chef_number
        if chef_number == None:
            return False

        class ChefPair(NamedTuple):
            a: int
            b: int
            a_evil: bool = False
            b_evil: bool = False
            a_spy: bool = False
            b_spy: bool = False
            a_recluse: bool = False
            b_recluse: bool = False
            a_unknown: bool = False
            b_unknown: bool = False

        def get_chef_pairs(
            spy_possible: bool,
            recluse_possible: bool,
            evils_available: int,
            new_outsider_possible: bool,
            spy_and_new_outsider_possible: bool,
        ) -> tuple[list[ChefPair], list[ChefPair]]:
            known_pairs: list[ChefPair] = []
            possible_pairs: list[ChefPair] = []
            unknown_can_be_evil = evils_available >= 1
            unknown_can_be_recluse = recluse_possible and new_outsider_possible

            def is_known_non_spy_evil(character: Role) -> bool:
                return (
                    character in NON_SPY_EVIL_CHARACTERS
                    or (
                        not spy_possible
                        and character != Role.SPY
                        and character in EVIL_ROLES_SET
                    )
                )
            def can_be_recluse(character: Role) -> bool:
                return (
                    character == Role.RECLUSE
                    or (
                        recluse_possible
                        and (
                            character == Role.ANY_OTHER_OUTSIDER
                            or (
                                new_outsider_possible
                                and character == Role.ANY_OTHER_GOOD
                            )
                        )
                    )
                )
            def can_be_spy(
                character: Role,
                *,
                allow_any_evil_role: bool,
            ) -> bool:
                if character == Role.SPY:
                    return True
                if not spy_possible:
                    return False
                if allow_any_evil_role:
                    return character in EVIL_ROLES_SET
                return character in (
                    Role.ANY_OTHER_MINION,
                    Role.ANY_OTHER_EVIL,
                )

            def classify_pair(
                player: int,
                partner: int,
            ) -> tuple[ChefPair, bool] | None:
                """
                Returns (pair, is_known), or None if this orientation cannot
                produce a Chef pair.
                """
                a = self.characters[player]
                b = self.characters[partner]
                a_unknown = a in DEDUCIBLE_UNKNOWN_ROLES
                b_unknown = b in DEDUCIBLE_UNKNOWN_ROLES

                # Partner is definitely evil
                if is_known_non_spy_evil(b):
                    if is_known_non_spy_evil(a):
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_evil=True,
                                b_evil=True,
                            ),
                            True,
                        )
                    if can_be_spy(a, allow_any_evil_role=True):
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_spy=True,
                                b_evil=True,
                            ),
                            False,
                        )
                    if can_be_recluse(a):
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_recluse=True,
                                b_evil=True,
                            ),
                            False,
                        )
                    if a_unknown:
                        if unknown_can_be_evil:
                            return (
                                ChefPair(
                                    player,
                                    partner,
                                    a_unknown=True,
                                    b_evil=True,
                                ),
                                False,
                            )
                        if unknown_can_be_recluse:
                            return (
                                ChefPair(
                                    player,
                                    partner,
                                    a_recluse=True,
                                    b_evil=True,
                                ),
                                False,
                            )
                    return None

                # Partner is evil and possible Spy.
                if b == Role.SPY or b in EVIL_ROLES_SET:
                    if can_be_spy(a, allow_any_evil_role=False):
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_spy=True,
                                b_spy=True,
                            ),
                            False,
                        )
                    if can_be_recluse(a):
                        if spy_and_new_outsider_possible:
                            return (
                                ChefPair(
                                    player,
                                    partner,
                                    a_recluse=True,
                                    b_spy=True,
                                ),
                                False,
                            )
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_recluse=True,
                                b_evil=True,
                            ),
                            False,
                        )
                    if a_unknown:
                        if unknown_can_be_evil:
                            return (
                                ChefPair(
                                    player,
                                    partner,
                                    a_unknown=True,
                                    b_spy=True,
                                ),
                                False,
                            )
                        if unknown_can_be_recluse:
                            return (
                                ChefPair(
                                    player,
                                    partner,
                                    a_recluse=True,
                                    b_spy=True,
                                ),
                                False,
                            )
                    return None

                # Partner is possibly Recluse
                if can_be_recluse(b):
                    if a_unknown and unknown_can_be_evil:
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_unknown=True,
                                b_recluse=True,
                            ),
                            False,
                        )
                    return None

                # Both players could be evil or Recluse
                if b_unknown and a_unknown:
                    evil_and_recluse_possible = (
                        evils_available == 1
                        and unknown_can_be_recluse
                    )
                    if evils_available >= 2 or evil_and_recluse_possible:
                        return (
                            ChefPair(
                                player,
                                partner,
                                a_unknown=True,
                                b_unknown=True,
                            ),
                            False,
                        )
                return None

            for i in range(self.num_players):
                j = (i + 1) % self.num_players
                for player, partner in ((i, j), (j, i)):
                    result = classify_pair(player, partner)
                    if result is None:
                        continue
                    pair, is_known = result
                    if is_known:
                        known_pairs.append(pair)
                    else:
                        possible_pairs.append(pair)
                    break
            return known_pairs, possible_pairs
        
        spy_possible = (
            Role.SPY not in self.characters
            and (
                Role.SPY in self.minion_types
                or Role.ANY_OTHER_MINION in self.minion_types
            )
        )
        baron_possible = (
            Role.BARON in self.minion_types
            or Role.ANY_OTHER_MINION in self.minion_types
        )
        recluse_possible = (
            Role.RECLUSE not in self.characters
            and gamerules.get_outsider_count(self.num_players, baron_possible) > 0
        )
        evil_count = self.get_evil_count()
        evils_available = gamerules.get_evil_count(self.num_players) - evil_count
        outsider_count = sum(1 for c in self.characters if c in GENERIC_OUTSIDER_SET)
        new_outsider_possible = (
            gamerules.get_outsider_count(self.num_players, baron_possible) >= outsider_count + 1
        )
        baron_needed = (
            gamerules.get_outsider_count(self.num_players, False) < outsider_count + 1
        )
        spy_and_new_outsider_possible = (
            new_outsider_possible
            and (
                Role.SPY in self.minion_types
                or (
                    Role.BARON in self.minion_types
                    or not baron_needed
                    or self.minion_types.count(Role.ANY_OTHER_MINION) >= 2
                )
            )
        )

        if (
            chef_number == gamerules.get_evil_count(self.num_players)
            and Role.BARON not in self.minion_types
            and Role.RECLUSE not in self.characters 
            and Role.ANY_OTHER_OUTSIDER not in self.characters
            and gamerules.get_outsider_count(self.num_players, False) - outsider_count == 0
        ):
            self.add_minion_type(Role.BARON)

        known_pairs, possible_pairs = get_chef_pairs(
            spy_possible, 
            recluse_possible, 
            evils_available, 
            new_outsider_possible, 
            spy_and_new_outsider_possible
        )

        def is_spy_needed(pair: ChefPair) -> tuple[bool, ...]:
            """
            Returns is_spy_needed, is_spy_found
            """
            # Either player could be the Spy
            if pair.a_spy and pair.b_spy:
                return True, False
            # B has to be the Spy
            if pair.a_evil and pair.b_spy:
                self.characters[pair.b] = Role.SPY
                self.add_minion_type(Role.SPY)
                return False, True
            # A has to be the Spy
            if pair.b_evil and pair.a_spy:
                self.characters[pair.a] = Role.SPY
                self.add_minion_type(Role.SPY)
                return False, True
            return False, False

        def handle_pair_not_in_chef_number(pair: ChefPair, spy_possible: bool) -> bool:
            if spy_possible:
                return False
            # B has to be good
            if pair.a_evil and pair.b_unknown:
                self.characters[pair.b] = Role.ANY_OTHER_GOOD
                return True
            # A has to be good
            if pair.b_evil and pair.a_unknown:
                self.characters[pair.a] = Role.ANY_OTHER_GOOD
                return True
            return False  
        
        def add_baron_if_needed(player: int):
            if Role.BARON in self.minion_types:
                return
            if self.characters[player] in GENERIC_OUTSIDER_SET:
                return
            outsider_count = self.get_characters_of_type(CharacterType.OUTSIDER)
            max_outsider_count = gamerules.get_outsider_count(self.num_players, False)
            if outsider_count + 1 > max_outsider_count:
                self.add_minion_type(Role.BARON)

        def handle_pair_in_chef_number(pair: ChefPair, recluse_possible: bool) -> bool:
            # B has to be the Recluse
            if pair.b_recluse: # I don't think it's possible for a_recluse and b_recluse to be contributing to a Chef number
                self.characters[pair.b] = Role.RECLUSE
                add_baron_if_needed(pair.b)
                return True
            # A has to be the Recluse
            if pair.a_recluse: # I don't think it's possible for a_recluse and b_recluse to be contributing to a Chef number
                self.characters[pair.a] = Role.RECLUSE
                add_baron_if_needed(pair.a)
                return True
            if pair.a_unknown and not recluse_possible:
                self.apply_character(Role.ANY_OTHER_EVIL, pair.a)
                return True
            if pair.b_unknown and not recluse_possible:
                self.apply_character(Role.ANY_OTHER_EVIL, pair.b)
                return True
            # Recluse or evil is possible, but they're definitely in the chef number
            if (
                recluse_possible
                and (
                    pair.a_unknown
                    or pair.b_unknown
                )
            ):
                if pair.a_unknown:
                    self.in_chef_pair |= 1 << pair.a
                if pair.b_unknown:
                    self.in_chef_pair |= 1 << pair.b
                return True
            return False

        # All pairs explained by definite pairs, possible pairs can't be contributing to the number
        if len(known_pairs) == chef_number:
            spy_candidates: list[ChefPair] = []
            spy_found = False
            for pair in possible_pairs:
                spy_needed, spy_in_pair = is_spy_needed(pair)
                spy_found |= spy_in_pair
                if spy_needed and not spy_found:
                    spy_candidates.append(pair)
                if not spy_needed and not spy_in_pair:
                    pair_deduced = handle_pair_not_in_chef_number(pair, spy_possible)
                    deduced |= pair_deduced
            deduced |= spy_found
            if len(spy_candidates) > 1:
                for spy_candidate in {player for pair in spy_candidates for player in (pair.a, pair.b)}:
                    if all(spy_candidate in (pair.a, pair.b) for pair in spy_candidates):
                        self.characters[spy_candidate] = Role.SPY
                        self.add_minion_type(Role.SPY)
                        deduced = True

        # Not all pairs explained by definite pairs, some possible pairs must contribute to the number
        else:
            effective_chef_number = chef_number - len(known_pairs) # effective chef number is > 0
            pair_combinations = [
                combination
                for combination in combinations(possible_pairs, effective_chef_number)
            ]
            for pair in possible_pairs:
                a, b = pair.a, pair.b
                if all(
                    any(p.a == a or p.b == a for p in pairs)
                    and any(p.a == b or p.b == b for p in pairs)
                    for pairs in pair_combinations
                ):
                    deduced |= handle_pair_in_chef_number(pair, recluse_possible)

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
            self.character_changed[alive_minion] = True
            return alive_minion

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
            old_minion = self.characters[alive_minion]
            assert not self.dead[alive_minion]
            self.characters[alive_minion] = Role.IMP
            if old_minion == Role.POISONER:
                self.poisoned = [False]*self.num_players
            elif old_minion == Role.SPY and self.red_herring[alive_minion]:
                self.red_herring[alive_minion] = False
                self.red_herring_moved = True
            return alive_minion

        # non-demons become any role
        # minions become any other evil
        # known demons become any other evil
        for i,c in enumerate(self.characters):
            if self.dead[i]:
                continue
            if c == Role.NON_DEMON:
                self.characters[i] = Role.ANY_OTHER
            if c == Role.ANY_OTHER_MINION or c in MINIONS:
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