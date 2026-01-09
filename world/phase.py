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
        try:
            idx = self.minion_types.index(Role.ANY_OTHER_MINION)
            self.minion_types[idx] = type
        except ValueError:
            raise ValueError("You are trying to add a minion type but this phase already has all minion types determined.")
        
    def remove_minion_type(self) -> None:
        if len(self.minion_types) == 0:
            raise Exception("You are trying to remove a minion from a phase with no minions.")
        self.minion_types = [Role.ANY_OTHER_MINION]*(len(self.minion_types)-1)