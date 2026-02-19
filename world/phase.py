from itertools import compress
from .role import *

class Phase:
    def __init__(self, num_players: int=5, night: int=1):
        self.characters: list[Role] = [Role.ANY_OTHER]*num_players
        self.poisoned: list[bool] = [False]*num_players
        self.minion_types: list[Role] = [Role.ANY_OTHER_MINION]*ROLE_BREAKDOWNS[num_players]['minions']
        self.red_herring: list[bool] = [False]*num_players
        self.dead: list[bool] = [False]*num_players
        self.drunk_token: Role | None = None
        self.chef_number: int | None = None
        self.no_outsiders: bool = False
        self.night: int = night
        self.character_changed: list[bool] = [False]*num_players
        self.star_passed: bool = False
        self.executee: int | None = None

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

    def get_outsider_count(self, num_players: int) -> int:
        return ROLE_BREAKDOWNS[num_players]['outsiders']+2 if Role.BARON in self.minion_types else ROLE_BREAKDOWNS[num_players]['outsiders']
    
    def make_deductions(self: Phase, num_players: int):
        deduced = True
        max_depth = 5
        d = 0
        while deduced and d < max_depth:
            deduced = self._deduction_step(num_players)
            d += 1

    def _deduction_step(self: Phase, num_players: int) -> bool:
        deduced = False

        minion_types = self.minion_types
        characters = self.characters
        alive_players = list(compress(range(num_players), [not x for x in self.dead]))
        alive_characters = list(compress(characters, [not x for x in self.dead]))

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
        if len(unknown_minions) == 1 and know_all_minion_types:
            assert(len(unassigned_minion_types) == 1)
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
        outsider_count = self.get_outsider_count(num_players)
        outsider_roles = OUTSIDERS + [Role.ANY_OTHER_OUTSIDER]
        known_outsiders = [i for i,c in enumerate(characters) if c in outsider_roles]
        if outsider_count_known and len(known_outsiders) == outsider_count:
            for i,c in enumerate(characters):
                if c == Role.ANY_OTHER_GOOD:
                    self.characters[i] = Role.ANY_OTHER_TOWNSFOLK
                    deduced = True
        
        
        return deduced