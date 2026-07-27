from typing import NamedTuple

from . import gamerules

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
    
def is_chef_pair_combination_valid(combination: tuple[ChefPair, ...], num_players: int) -> bool:
    max_evils = gamerules.get_evil_count(num_players)
    max_recluse = 1
    players = {i for pair in combination for i in (pair.a, pair.b)}
    return len(players) <= max_evils + max_recluse
            