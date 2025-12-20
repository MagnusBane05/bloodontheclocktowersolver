from enum import Enum, auto
import copy
from sys import exception
from typing import Self, override
from collections.abc import Callable

class Role(Enum):
    WASHERWOMAN = auto()
    LIBRARIAN = auto()
    INVESTIGATOR = auto()
    CHEF = auto()
    EMPATH = auto()
    FORTUNE_TELLER = auto()
    UNDERTAKER = auto()
    MONK = auto()
    RAVENKEEPER = auto()
    VIRGIN = auto()
    SLAYER = auto()
    SOLDIER = auto()
    MAYOR = auto()
    BUTLER = auto()
    SAINT = auto()
    RECLUSE = auto()
    DRUNK = auto()
    POISONER = auto()
    SPY = auto()
    BARON = auto()
    SCARLET_WOMAN = auto()
    IMP = auto()
    ANY_OTHER_TOWNSFOLK = auto()
    ANY_OTHER_OUTSIDER = auto()
    ANY_OTHER_MINION = auto()
    ANY_OTHER_GOOD = auto()
    ANY_OTHER_EVIL = auto()
    NON_DEMON = auto()
    ANY_OTHER = auto()

ROLE_BREAKDOWNS = {
    5: {
        'minions': 1,
        'demons': 1,
        'townsfolk': 3,
        'outsiders': 0
    },
    6: {
        'minions': 1,
        'demons': 1,
        'townsfolk': 3,
        'outsiders': 1
    },
    13: {
        'minions': 3,
        'demons': 1,
        'townsfolk': 9,
        'outsiders': 0
    }
}

EVIL_CHARACTERS = [Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN, Role.IMP]
GOOD_CHARACTERS = [
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR, Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK
]
MINIONS = [Role.POISONER, Role.SPY, Role.BARON, Role.SCARLET_WOMAN]
TOWNSFOLK = [
    Role.WASHERWOMAN, Role.LIBRARIAN, Role.INVESTIGATOR, Role.CHEF, Role.EMPATH,
    Role.FORTUNE_TELLER, Role.UNDERTAKER, Role.MONK, Role.RAVENKEEPER, Role.VIRGIN,
    Role.SLAYER, Role.SOLDIER, Role.MAYOR
]
OUTSIDERS = [Role.BUTLER, Role.SAINT, Role.RECLUSE, Role.DRUNK]
DEMONS = [Role.IMP]
EVIL_ROLES = EVIL_CHARACTERS + [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]
GOOD_ROLES = GOOD_CHARACTERS + [Role.ANY_OTHER_GOOD]
ANY_OTHER_ROLES = [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.ANY_OTHER_OUTSIDER, Role.ANY_OTHER_TOWNSFOLK, Role.NON_DEMON]

CHARACTER_STRINGS = {
    Role.ANY_OTHER: "any other character",
    Role.ANY_OTHER_EVIL: "any other Evil character",
    Role.ANY_OTHER_GOOD: "any other Good character",
    Role.ANY_OTHER_MINION: "any other minion",
    Role.NON_DEMON: "any non demon character",
    Role.WASHERWOMAN: "Washerwoman", 
    Role.LIBRARIAN: "Librarian", 
    Role.INVESTIGATOR: "Investigator", 
    Role.CHEF: "Chef", 
    Role.EMPATH: "Empath", 
    Role.FORTUNE_TELLER: "Fortune Teller", 
    Role.UNDERTAKER: "Undertaker", 
    Role.MONK: "Monk", 
    Role.RAVENKEEPER: "Ravenkeeper", 
    Role.VIRGIN: "Virgin", 
    Role.SLAYER: "Slayer", 
    Role.SOLDIER: "Soldier", 
    Role.MAYOR: "Mayor", 
    Role.BUTLER: "Butler", 
    Role.SAINT: "Saint", 
    Role.RECLUSE: "Recluse", 
    Role.DRUNK: "Drunk", 
    Role.POISONER: "Poisoner", 
    Role.SPY: "Spy", 
    Role.BARON: "Baron", 
    Role.SCARLET_WOMAN: "Scarlet Woman", 
    Role.IMP: "Imp"
}

class PhaseNotFoundError(ValueError):
    pass

class World:

    class Phase:
        def __init__(self, num_players: int=5, night: int=1):
            self.characters: list[Role] = [Role.ANY_OTHER]*num_players
            self.poisoned: list[list[bool]] = [[False]*num_players]
            self.minion_types: list[Role] = [Role.ANY_OTHER_MINION]*ROLE_BREAKDOWNS[num_players]['minions']
            self.on_extend: Callable[[Self], bool] | None = None
            self.red_herring: list[bool] = [False]*num_players
            self.dead: list[bool] = [False]*num_players
            self.drunk_token: Role | None = None
            self.chef_number: int | None = None
            self.no_outsiders: bool = False
            self.night: int = night
    
        def add_minion_type(self, type: Role) -> None:
            if type not in MINIONS:
                raise ValueError("You are trying to add a non-minion role as a minion type.")
            try:
                idx = self.minion_types.index(Role.ANY_OTHER_MINION)
                self.minion_types[idx] = type
            except ValueError:
                raise ValueError("You are trying to add a minion type but this phase already has all minion types determined.")
            
        def remove_minion_type(self) -> None:
            if len(self.minion_types) == 0:
                raise Exception("You are trying to remove a minion forma phase with no minions.")
            self.minion_types = [Role.ANY_OTHER_MINION]*(len(self.minion_types)-1)

    def __init__(self, num_players:int=5):
        if num_players not in ROLE_BREAKDOWNS.keys():
            raise ValueError(f"{num_players} player worlds are not yet handled.")
        self.phases: list[World.Phase] = [self.Phase(num_players)]

    @override
    def __str__(self):
        s = ""
        for i, phase in enumerate(self.phases):
            ps = f"--- Phase {i+1} ---\n"
            for j in range(len(phase.characters)):
                character = phase.characters[j]
                dead = phase.dead[j]
                red_herring = phase.red_herring[j]
                if character != Role.ANY_OTHER:
                    if character in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.NON_DEMON]:
                        ps += f"Player {j} is {CHARACTER_STRINGS[character]}.\n"
                    else:
                        ps += f"Player {j} is the {CHARACTER_STRINGS[character]}.\n"
                for k,poison in enumerate(phase.poisoned):
                    poisoned = poison[j]
                    if poisoned:
                        ps += f"Player {j} was poisoned N{k+1}.\n"
                if dead:
                    ps += f"Player {j} is dead.\n"
                if red_herring:
                    ps += f"Player {j} is the red herring.\n"
            # if phase.minion_type is None:
            #     ps += f"There are no minions.\n"
            # elif phase.minion_type != Role.ANY_OTHER_MINION:
            #     ps += f"The minion type is {CHARACTER_STRINGS[phase.minion_type]}.\n"
            s += ps
        s += "---------------------"
        return s

    def get_phase(self, night: int) -> Phase:
        for phase in self.phases:
            if phase.night == night:
                return phase
        raise PhaseNotFoundError(f"World does not contain phase with night {night}")

    def add_phase(self, night: int) -> Phase:
        return self.Phase()
    
    def extend_phases(self) -> Phase:
        lastPhase = self.phases[-1]
        newPhase = self._create_phase(lastPhase)
        self.phases.append(newPhase)
        return newPhase
    
    def insert_phase(self, i: int) -> Phase:
        assert i > 0 and len(self.phases) >= i
        previous_phase = self.phases[i-1]
        newPhase = self._create_phase(previous_phase)
        self.phases.insert(i,newPhase)
        return newPhase

    @staticmethod
    def _create_phase(old_phase: Phase) -> Phase:
        newPhase = World.Phase()
        newPhase.characters = copy.copy(old_phase.characters)
        newPhase.minion_types = copy.copy(old_phase.minion_types)
        newPhase.dead = copy.copy(old_phase.dead)
        return newPhase

    @classmethod
    def combine(cls, w1: Self, w2: Self) -> tuple[Self, bool]:
        if len(w1.phases[0].characters) != len(w2.phases[0].characters):
            raise Exception("You are trying to combine world with different numbers of players. Something has gone terribly wrong.")
        num_players = len(w1.phases[0].characters)
        new_world = cls(num_players)
        w1_copy = copy.deepcopy(w1)
        w2_copy = copy.deepcopy(w2)

        num_unique_phases = len(w1_copy.phases) + len(w2_copy.phases) - 1

        for i in range(num_unique_phases - 1):
            new_world.phases.append(cls.Phase(num_players))

        for i in range(num_unique_phases):
            new_phase = new_world.phases[i]

            # first phase
            if i == 0:
                p1 = w1_copy.phases[0]
                p2 = w2_copy.phases[0]
            # go through first world phases first
            elif i < len(w1_copy.phases):
                p1 = w1_copy.phases[i]
                p2 = w2_copy.insert_phase(i)
                if p1.on_extend is not None:
                    if not p1.on_extend(p2):
                        return w1, False
            # second world phases should have first world phases inserted by this point, so go through second world phases next
            else:
                p2 = w2_copy.phases[i]
                p1 = w1_copy.extend_phases()
                if p2.on_extend is not None:
                    if not p2.on_extend(p1):
                        return w2, False

            if not cls._combine_phases(new_world.phases[0], new_phase, num_players, p1, p2):
                return w1, False

        return new_world, True
    
    @staticmethod
    def _combine_phases(phase_0: Phase, new_phase: Phase, num_players: int, p1: Phase, p2: Phase):
        # Minion types
        if not World._combine_minion_types(new_phase, p1, p2):
            return False

        for i in range(num_players):
            c1, c2 = p1.characters[i], p2.characters[i]
            result = World._combine_characters(c1, c2, p1)
            if result is None:
                return False
            new_phase.characters[i] = result

        # Make sure the minions match the minion types
        if not World._validate_minion_types(new_phase):
            return False

        # Combine and validate chef numbers
        if not World._combine_chef_number(new_phase, p1, p2, num_players):
            return False

        # Poisoner logic
        if not World._combine_poisoned(new_phase, p1, p2, num_players):
            return False
        
        if not World._combine_deaths(new_phase, p1, p2, num_players):
            return False

        # Outsider, evil and good count checks
        if not World._validate_character_counts(new_phase, phase_0, num_players):
            return False
        
        # Check if there's more than one red herring or if the red herring is on an evil player
        if not World._combine_red_herring(new_phase, p1, p2, num_players):
            return False
        
        if not World._combine_on_extend(new_phase, p1, p2):
            return False
        
        World._make_deductions(new_phase, num_players)

        return True

    @staticmethod
    def _combine_minion_types(new_phase: Phase, p1: Phase, p2: Phase):
        if len(p1.minion_types) != len(p2.minion_types):
            raise Exception('Trying to combine phases with different numbers of minions. Something has gone terribly wrong.')
        
        # combine the two lists of minions, remove duplicates and ANY_OTHER_MINION
        unique_minions = list(set(p1.minion_types + p2.minion_types) - set([Role.ANY_OTHER_MINION]))

        # if the resulting list of minions is greater that either phase allows, that's an invalid world
        if len(unique_minions) > len(p1.minion_types):
            return False
        
        # add back in ANY_OTHER_MINION until we're at the right number of minions
        while len(unique_minions) < len(p1.minion_types):
            unique_minions.append(Role.ANY_OTHER_MINION)

        new_phase.minion_types = unique_minions
        return True

    @staticmethod
    def _combine_characters(c1: Role, c2: Role, p1: Phase):
        if c1 == c2:
            return c1
        if c1 not in ANY_OTHER_ROLES:
            return World._combine_specific_character(c1, c2)
        if c1 == Role.ANY_OTHER_EVIL:
            return World._combine_any_evil(c2, p1)
        if c1 == Role.ANY_OTHER_GOOD:
            return World._combine_any_good(c2, p1)
        if c1 == Role.ANY_OTHER_MINION:
            return World._combine_any_other_minion(c2, p1)
        if c1 == Role.ANY_OTHER_TOWNSFOLK:
            return World._combine_any_other_townsfolk(c2, p1)
        if c1 == Role.ANY_OTHER_OUTSIDER:
            return World._combine_any_other_outsider(c2, p1)
        if c1 == Role.NON_DEMON:
            return World._combine_non_demon(c2, p1)
        if c1 == Role.ANY_OTHER:
            return World._combine_any_other(c2, p1)
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
    def _combine_any_evil(c2: Role, p1: Phase):
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
    def _combine_any_good(c2: Role, p1: Phase):
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
    def _combine_any_other_minion(c2: Role, p1: Phase):
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
    def _combine_any_other_townsfolk(c2: Role, p1: Phase):
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
    def _combine_any_other_outsider(c2: Role, p1: Phase):
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
    def _combine_non_demon(c2: Role, p1: Phase):
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
    def _combine_any_other(c2: Role, p1: Phase):
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
    def _validate_minion_types(phase: Phase):
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
    def _combine_chef_number(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        if p1.chef_number is not None and p2.chef_number is not None and p1.chef_number is not p2.chef_number:
            return False
        
        new_phase.chef_number = p1.chef_number if p1.chef_number is not None else p2.chef_number
        if new_phase.chef_number is None:
            return True
        
        characters = new_phase.characters
        # set a minimum number of non-Spy evil pairs
        minimum = 0
        for i in range(num_players):
            j = (i+1) % num_players
            if characters[i] in EVIL_CHARACTERS and characters[i] != Role.SPY and characters[j] in EVIL_CHARACTERS and characters[j] != Role.SPY:
                minimum += 1

        possible_numbers = [minimum]
        maximum = minimum
        for i in range(num_players):
            j = (i+1) % num_players
            if (characters[i] in EVIL_CHARACTERS or characters[i] == Role.RECLUSE) and (characters[j] in EVIL_CHARACTERS or characters[j] == Role.RECLUSE):
                maximum += 1
                possible_numbers.append(maximum)

        return new_phase.chef_number in possible_numbers

    @staticmethod
    def _combine_poisoned(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        poisoned_nights = max(len(p1.poisoned),len(p2.poisoned))
        new_phase.poisoned = [[False]*num_players for _ in range(poisoned_nights)]
        for i in range(poisoned_nights - len(p1.poisoned)):
            p1.poisoned.append([False]*num_players)
        for i in range(poisoned_nights - len(p2.poisoned)):
            p2.poisoned.append([False]*num_players)
        for n in range(poisoned_nights):
            for i in range(num_players):
                new_phase.poisoned[n][i] = p1.poisoned[n][i] or p2.poisoned[n][i]
            # don't allow 2 instances of poisoning
            if sum([int(p) for p in new_phase.poisoned[n]]) > 1:
                return False
            # return false if no room for poisoner
            if any(new_phase.poisoned[n]) and Role.POISONER not in new_phase.minion_types and Role.ANY_OTHER_MINION not in new_phase.minion_types:
                return False
        return True
    
    @staticmethod
    def _validate_character_counts(new_phase: Phase, phase_0: Phase, num_players: int):
        if World._validate_outsider_count(phase_0, num_players) and World._validate_evil_count(new_phase, num_players) and World._validate_good_count(new_phase, num_players):
            return True
        return False

    @staticmethod
    def _validate_outsider_count(phase_0: Phase, num_players: int):
        # librarian told no outsiders
        if phase_0.no_outsiders and World.num_characters_of_type(phase_0, OUTSIDERS) > 0:
            return False
        # base outsider count or if a Baron is in play, base outsider count plus 2
        valid_counts = [ROLE_BREAKDOWNS[num_players]['outsiders']] if Role.BARON not in phase_0.minion_types else [ROLE_BREAKDOWNS[num_players]['outsiders']+2]
        # we don't know if a baron is in play, valid counts could be base and base plus 2
        if Role.BARON not in phase_0.minion_types and Role.ANY_OTHER_MINION in phase_0.minion_types:
            valid_counts.append(ROLE_BREAKDOWNS[num_players]['outsiders']+2)
        minimum = sum([1 if c in OUTSIDERS else 0 for c in phase_0.characters])
        maximum = minimum + sum([1 if c in [Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON] else 0 for c in phase_0.characters])
        # valid if any possible number of outsiders is in one of the valid counts
        if any([c in valid_counts for c in range(minimum, maximum+1)]):
            return True
        return False

    @staticmethod
    def _validate_evil_count(new_phase: Phase, num_players: int):
        # validate only 1 alive Imp
        if sum([1 if c == Role.IMP and not new_phase.dead[i] else 0 for i,c in enumerate(new_phase.characters)]) > 1:
            return False
        # validate not all evils are dead
        if sum([1 if c in EVIL_ROLES and new_phase.dead[i] else 0 for i,c in enumerate(new_phase.characters)]) >= ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']:
            return False
        if World.num_characters_of_type(new_phase, EVIL_ROLES) > ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']:
            return False
        return True

    @staticmethod
    def _validate_good_count(new_phase: Phase, num_players: int):
        if World.num_characters_of_type(new_phase, GOOD_ROLES) > ROLE_BREAKDOWNS[num_players]['townsfolk'] + ROLE_BREAKDOWNS[num_players]['outsiders']:
            return False
        return True
    
    @staticmethod
    def _combine_red_herring(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        # combine the two phases
        for i in range(num_players):
            new_phase.red_herring[i] = p1.red_herring[i] or p2.red_herring[i]

        # more than one red herring
        if sum([int(x) for x in new_phase.red_herring]) > 1:
            return False

        # make sure the red herring doesn't belong to an evil player
        for i in range(num_players):
            if new_phase.red_herring[i] and new_phase.characters[i] in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.IMP] + MINIONS:
                    return False
                
        return True
    
    @staticmethod
    def _combine_deaths(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        # combine the phases
        for i in range(num_players):
            new_phase.dead[i] = p1.dead[i] or p2.dead[i]
        
        return True
    
    @staticmethod
    def _combine_on_extend(new_phase: Phase, p1: Phase, p2: Phase) -> bool:
        # on_extend should be exclusive to each phase, if not return False
        if p1.on_extend is not None and p2.on_extend is not None:
            return False
        if p1.on_extend is not None:
            new_phase.on_extend = p1.on_extend
            return True
        new_phase.on_extend = p2.on_extend
        return True
    
    @staticmethod
    def _make_deductions(phase: Phase, num_players: int):
        deduced = True
        max_depth = 5
        d = 0
        while deduced and d < max_depth:
            deduced = World._deduction_step(phase, num_players)
            d += 1

    @staticmethod
    def _deduction_step(phase: Phase, num_players: int) -> bool:
        deduced = False

        # If no other spot for alive demon, assign demon
        alive_demon_candidates = [
            i for i, c in enumerate(phase.characters)
            if c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.IMP] and not phase.dead[i]
        ]
        if len(alive_demon_candidates) == 1 and phase.characters[alive_demon_candidates[0]] != Role.IMP:
            phase.characters[alive_demon_candidates[0]] = Role.IMP
            deduced = True
        
        # If no other spot for evils, assign evil
        evil_indices = [i for i, c in enumerate(phase.characters) if c in EVIL_ROLES]
        if ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons'] - len(evil_indices) > 0:
            if all(c in GOOD_ROLES or i in evil_indices for i,c in enumerate(phase.characters)):
                for i,c in enumerate(phase.characters):
                    if c == Role.ANY_OTHER:
                        phase.characters[i] = Role.ANY_OTHER_EVIL
                        deduced = True
                    if c == Role.NON_DEMON:
                        phase.characters[i] = Role.ANY_OTHER_MINION
                        deduced = True


        # If 2 evil players and one is known minion / demon, assign the opposite to the unknown evil
        evil_indices = [i for i, c in enumerate(phase.characters) if c in EVIL_ROLES]
        if len(evil_indices) == 2:
            roles = [phase.characters[i] for i in evil_indices]
            # If one is Imp and the other is ANY_OTHER_EVIL, assign the other as minion
            if Role.IMP in roles:
                for i in evil_indices:
                    if phase.characters[i] == Role.ANY_OTHER_EVIL:
                        phase.characters[i] = Role.ANY_OTHER_MINION
                        deduced = True
            # If one is a known minion and the other is ANY_OTHER_EVIL, assign the other as Imp
            elif any(r in MINIONS for r in roles) or Role.ANY_OTHER_MINION in roles:
                for i in evil_indices:
                    if phase.characters[i] == Role.ANY_OTHER_EVIL:
                        phase.characters[i] = Role.IMP
                        deduced = True

        # If all minion types are known and there is one player with the ANY_OTHER_MINION role, we can assign that player the unasigned minion type
        if Role.ANY_OTHER_MINION not in phase.minion_types:
            unassigned_types = list(set(phase.minion_types) - set([c for c in phase.characters if c in MINIONS]))
            if len(unassigned_types) == 1 and Role.ANY_OTHER_MINION in phase.characters:
                phase.characters[phase.characters.index(Role.ANY_OTHER_MINION)] = unassigned_types[0]
                deduced = True

        # TODO: If all minion players are known and there are one or more players with the NON_DEMON role, assign ANY_OTHER_GOOD to those players
                
        return deduced

    @staticmethod
    def num_characters_of_type(phase: Phase, character_type: list[Role]):
        n = 0
        for character in phase.characters:
            if character in character_type:
                n += 1
        return n

def combine_worlds(world_lists: list[list[World]]):
    starting_worlds: list[World] = world_lists[0]
    conflicting_worlds: list[list[World]] = []

    for i in range(1, len(world_lists)):
        valid_worlds: list[World] = []
        for w1 in starting_worlds:
            for w2 in world_lists[i]:
                combined_world, valid = World.combine(w1, w2)
                if valid: 
                    valid_worlds.append(combined_world)
                else:
                    conflicting_worlds.append([w1, w2])
        starting_worlds = valid_worlds[:]

    return starting_worlds, conflicting_worlds

def remove_duplicate_complete_worlds(world_list: list[World]) -> list[World]:
    culled_list = copy.copy(world_list)
    i=0
    while i < len(culled_list):
        w1_characters = culled_list[i].phases[-1].characters
        if any(c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.NON_DEMON] for c in w1_characters):
            i+=1
            continue
        j=i+1
        while j < len(culled_list):
            w2_characters = culled_list[j].phases[-1].characters
            if any(c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.NON_DEMON] for c in w2_characters):
                j+=1
                continue
            if culled_list[i].phases[-1].characters == culled_list[j].phases[-1].characters:
                _ = culled_list.pop(j)
                continue
            j+=1
        i+=1

    return culled_list