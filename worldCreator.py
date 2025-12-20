from typing import TypedDict
from solver import World, Role, OUTSIDERS, ROLE_BREAKDOWNS, MINIONS, EVIL_CHARACTERS, GOOD_CHARACTERS
import copy

class Game(TypedDict):
    players: int

class Claim(TypedDict):
    player: int
    character: Role

class InvestigatorInfo(TypedDict):
    investigator: int
    first_player: int
    second_player: int
    minion: Role

class WasherwomanInfo(TypedDict):
    washerwoman: int
    first_player: int
    second_player: int
    townsfolk: Role

class LibrarianInfo(TypedDict):
    player: int
    first_player: int
    second_player: int
    token: Role | None

class ChefInfo(TypedDict):
    chef: int
    number: int

class FortuneTellerInfo(TypedDict):
    player: int
    night: int
    pings: tuple[tuple[int,int],bool]

class EmpathInfo(TypedDict):
    empath: int
    number: int
    night: int
    left_neighbour: int
    right_neighbour: int    

class UndertakerInfo(TypedDict):
    undertaker: int
    body: int
    token: Role
    night: int

class RavenkeeperInfo(TypedDict):
    ravenkeeper: int
    chosen: int
    token: Role
    night: int

class VirginInfo(TypedDict):
    virgin: int
    nominator: int
    executed: bool
    night: int

def create_drunk_evil_poisoned_worlds(game: Game, player: int, token: Role, night:int=0) -> list[World]:
    worlds: list[World] = []

    world1 = World()
    phase1 = world1.phases[0]
    phase1.characters[player] = Role.DRUNK
    phase1.drunk_token = token
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase1.add_minion_type(Role.BARON)
    worlds.append(world1)

    world2 = World()
    phase2 = world2.phases[0]
    phase2.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world2)

    world3 = World()
    phase3 = world3.phases[0]
    phase3.characters[player] = token
    while len(phase3.poisoned) < night:
        phase3.poisoned.append([False]*game['players'])
    phase3.poisoned[night-1][player] = True
    phase3.add_minion_type(Role.POISONER)
    worlds.append(world3)

    return worlds


def create_worlds_from_claim(game: Game, claim: Claim) -> list[World]:
    player = claim['player']
    character = claim['character']
    worlds: list[World] = []

    # World where the player is the Drunk
    if character not in OUTSIDERS:
        world_drunk = World()
        phase_drunk = world_drunk.phases[0]
        phase_drunk.characters[player] = Role.DRUNK
        phase_drunk.drunk_token = character
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase_drunk.add_minion_type(Role.BARON)
        worlds.append(world_drunk)

    # World where the player is an unspecified evil character
    world_evil = World()
    phase_evil = world_evil.phases[0]
    phase_evil.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world_evil)

    # World where the player is exactly the claimed character
    world_claimed = World()
    phase_claimed = world_claimed.phases[0]
    phase_claimed.characters[player] = character
    if character in OUTSIDERS:
        phase_claimed.add_minion_type(Role.BARON)
    worlds.append(world_claimed)

    return worlds

def create_worlds_from_investigator_info(game: Game, info: InvestigatorInfo):
    player = info['investigator']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.INVESTIGATOR)

    world3 = World()
    phase3 = world3.phases[0]
    phase3.characters[player] = Role.INVESTIGATOR
    phase3.characters[info['first_player']] = info['minion']
    phase3.add_minion_type(info['minion'])
    worlds.append(world3)

    world4 = World()
    phase4 = world4.phases[0]
    phase4.characters[player] = Role.INVESTIGATOR
    phase4.characters[info['second_player']] = info['minion']
    phase4.add_minion_type(info['minion'])
    worlds.append(world4)

    world5 = World()
    phase5 = world5.phases[0]
    phase5.characters[player] = Role.INVESTIGATOR
    phase5.characters[info['first_player']] = Role.RECLUSE
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase5.add_minion_type(Role.BARON)
    worlds.append(world5)

    world6 = World()
    phase6 = world6.phases[0]
    phase6.characters[player] = Role.INVESTIGATOR
    phase6.characters[info['second_player']] = Role.RECLUSE
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase6.add_minion_type(Role.BARON)
    worlds.append(world6)

    return worlds

def create_worlds_from_washerwoman_info(game: Game, info: WasherwomanInfo):
    player = info['washerwoman']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.WASHERWOMAN)

    world3 = World()
    phase3 = world3.phases[0]
    phase3.characters[player] = Role.WASHERWOMAN
    phase3.characters[info['first_player']] = info['townsfolk']
    worlds.append(world3)

    world4 = World()
    phase4 = world4.phases[0]
    phase4.characters[player] = Role.WASHERWOMAN
    phase4.characters[info['second_player']] = info['townsfolk']
    worlds.append(world4)

    world5 = World()
    phase5 = world5.phases[0]
    phase5.characters[player] = Role.WASHERWOMAN
    phase5.characters[info['first_player']] = Role.SPY
    phase5.add_minion_type(Role.SPY)
    worlds.append(world5)

    world6 = World()
    phase6 = world6.phases[0]
    phase6.characters[player] = Role.WASHERWOMAN
    phase6.characters[info['second_player']] = Role.SPY
    phase6.add_minion_type(Role.SPY)
    worlds.append(world6)

    return worlds

def create_worlds_from_chef_info(game: Game, info: ChefInfo):
    player = info['chef']
    number = info['number']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.CHEF)

    world = World()
    world.phases[0].characters[player] = Role.CHEF
    world.phases[0].chef_number = number
    worlds.append(world)

    return worlds

def create_worlds_from_librarian_info(game: Game, info: LibrarianInfo):
    player = info['player']
    first_player = info['first_player']
    second_player = info['second_player']
    token = info['token']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.LIBRARIAN)

    if token is None:
        world_no_outsiders = World()
        world_no_outsiders.phases[0].characters[player] = Role.LIBRARIAN
        world_no_outsiders.phases[0].no_outsiders = True
        worlds.append(world_no_outsiders)
        return

    world3 = World()
    phase3 = world3.phases[0]
    phase3.characters[player] = Role.LIBRARIAN
    phase3.characters[first_player] = token
    worlds.append(world3)

    world4 = World()
    phase4 = world4.phases[0]
    phase4.characters[player] = Role.LIBRARIAN
    phase4.characters[second_player] = token
    worlds.append(world4)

    world5 = World()
    phase5 = world5.phases[0]
    phase5.characters[player] = Role.LIBRARIAN
    phase5.characters[first_player] = Role.SPY
    phase5.add_minion_type(Role.SPY)
    worlds.append(world5)

    world6 = World()
    phase6 = world6.phases[0]
    phase6.characters[player] = Role.LIBRARIAN
    phase6.characters[second_player] = Role.SPY
    phase6.add_minion_type(Role.SPY)
    worlds.append(world6)

    return worlds

def create_worlds_from_fortune_teller_info(game: Game, info: FortuneTellerInfo):
    player = info['player']
    pings, result = info['pings']
    a, b = pings
    night = info['night']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.FORTUNE_TELLER, night)

    if result:
        ## Player a is the Demon
        world4 = World()
        phase4 = world4.phases[0]
        phase4.characters[player] = Role.FORTUNE_TELLER
        phase4.characters[a] = Role.IMP
        worlds.append(world4)

        ## Player b is the Demon
        world5 = World()
        phase5 = world5.phases[0]
        phase5.characters[player] = Role.FORTUNE_TELLER
        phase5.characters[b] = Role.IMP
        worlds.append(world5)

        ## Player a is the Red Herring
        world6 = World()
        phase6 = world6.phases[0]
        phase6.characters[player] = Role.FORTUNE_TELLER
        phase6.characters[a] = Role.ANY_OTHER_GOOD
        phase6.red_herring[a] = True
        worlds.append(world6)

        ## Player b is the Red Herring
        world7 = World()
        phase7 = world7.phases[0]
        phase7.characters[player] = Role.FORTUNE_TELLER
        phase7.characters[b] = Role.ANY_OTHER_GOOD
        phase7.red_herring[b] = True
        worlds.append(world7)

        ## Player a is the Recluse
        world8 = World()
        phase8 = world8.phases[0]
        phase8.characters[player] = Role.FORTUNE_TELLER
        phase8.characters[a] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase8.add_minion_type(Role.BARON)
        worlds.append(world8)

        ## Player b is the Recluse
        world9 = World()
        phase9 = world9.phases[0]
        phase9.characters[player] = Role.FORTUNE_TELLER
        phase9.characters[b] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase9.add_minion_type(Role.BARON)
        worlds.append(world9)

    else:
        ## Player a is not the Imp and Player b is not the Imp
        world10 = World()
        phase10 = world10.phases[0]
        phase10.characters[player] = Role.FORTUNE_TELLER
        phase10.characters[a] = Role.NON_DEMON
        phase10.characters[b] = Role.NON_DEMON
        worlds.append(world10)

    return worlds

def create_worlds_from_empath_info(game: Game, info: EmpathInfo):
    player = info['empath']
    number = info['number']
    night = info['night']
    left = info['left_neighbour']
    right = info['right_neighbour']
    if number < 0 or number > 2:
        raise ValueError('An empath was given an invalid number')

    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.EMPATH, night)

    if number == 0:
        # Both neighbours are good
        world1 = World()
        phase1 = world1.phases[0]
        phase1.characters[player] = Role.EMPATH
        phase1.characters[left] = Role.ANY_OTHER_GOOD
        phase1.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world1)

        # Left neighbour is the Spy (registering as good)
        world2 = World()
        phase2 = world2.phases[0]
        phase2.characters[player] = Role.EMPATH
        phase2.characters[left] = Role.SPY
        phase2.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world2)

        # Right neighbour is the Spy (registering as good)
        world3 = World()
        phase3 = world3.phases[0]
        phase3.characters[player] = Role.EMPATH
        phase3.characters[left] = Role.ANY_OTHER_GOOD
        phase3.characters[right] = Role.SPY
        worlds.append(world3)

    elif number == 1:
        # Left neighbour is any other evil and right neighbour is good
        world4 = World()
        phase4 = world4.phases[0]
        phase4.characters[player] = Role.EMPATH
        phase4.characters[left] = Role.ANY_OTHER_EVIL
        phase4.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world4)

        # Right neighbour is any other evil and left neighbour is good
        world5 = World()
        phase5 = world5.phases[0]
        phase5.characters[player] = Role.EMPATH
        phase5.characters[left] = Role.ANY_OTHER_GOOD
        phase5.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world5)

        # Left neighbour is any other evil and right neighbour is the Spy
        world6 = World()
        phase6 = world6.phases[0]
        phase6.characters[player] = Role.EMPATH
        phase6.characters[left] = Role.ANY_OTHER_EVIL
        phase6.characters[right] = Role.SPY
        worlds.append(world6)

        # Right neighbour is any other evil and left neighbour is the Spy
        world7 = World()
        phase7 = world7.phases[0]
        phase7.characters[player] = Role.EMPATH
        phase7.characters[left] = Role.SPY
        phase7.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world7)

        # Left neighbour is the Recluse and right neighbour is good
        world8 = World()
        phase8 = world8.phases[0]
        phase8.characters[player] = Role.EMPATH
        phase8.characters[left] = Role.RECLUSE
        phase8.characters[right] = Role.ANY_OTHER_GOOD
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase8.add_minion_type(Role.BARON)
        worlds.append(world8)

        # Right neighbour is the Recluse and left neighbour is good
        world9 = World()
        phase9 = world9.phases[0]
        phase9.characters[player] = Role.EMPATH
        phase9.characters[left] = Role.ANY_OTHER_GOOD
        phase9.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase9.add_minion_type(Role.BARON)
        worlds.append(world9)

        # Left neighbour is the Recluse and right neighbour is the Spy
        world10 = World()
        phase10 = world10.phases[0]
        phase10.characters[player] = Role.EMPATH
        phase10.characters[left] = Role.RECLUSE
        phase10.characters[right] = Role.SPY
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase10.add_minion_type(Role.BARON)
        worlds.append(world10)

        # Right neighbour is the Recluse and left neighbour is the Spy
        world11 = World()
        phase11 = world11.phases[0]
        phase11.characters[player] = Role.EMPATH
        phase11.characters[left] = Role.SPY
        phase11.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase11.add_minion_type(Role.BARON)
        worlds.append(world11)

    else:  # number == 2
        # Both neighbours are evil
        world12 = World()
        phase12 = world12.phases[0]
        phase12.characters[player] = Role.EMPATH
        phase12.characters[left] = Role.ANY_OTHER_EVIL
        phase12.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world12)

        # Left neighbour is evil and right is the Recluse
        world13 = World()
        phase13 = world13.phases[0]
        phase13.characters[player] = Role.EMPATH
        phase13.characters[left] = Role.ANY_OTHER_EVIL
        phase13.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase13.add_minion_type(Role.BARON)
        worlds.append(world13)

        # Right neighbour is evil and left is the Recluse
        world14 = World()
        phase14 = world14.phases[0]
        phase14.characters[player] = Role.EMPATH
        phase14.characters[left] = Role.RECLUSE
        phase14.characters[right] = Role.ANY_OTHER_EVIL
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase14.add_minion_type(Role.BARON)
        worlds.append(world14)

    return worlds

def create_worlds_from_undertaker_info(game: Game, info: UndertakerInfo):
    player = info['undertaker']
    body = info['body']
    token = info['token']
    night = info['night']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.UNDERTAKER, night=night)

    # World where the undertaker sees the actual token (body is that token)
    world1 = World()
    phase1 = world1.phases[0]
    phase1.characters[player] = Role.UNDERTAKER
    phase1.characters[body] = token
    worlds.append(world1)

    # If the token is an evil character, the body could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = World()
        phase2 = world2.phases[0]
        phase2.characters[player] = Role.UNDERTAKER
        phase2.characters[body] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the body could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = World()
        phase3 = world3.phases[0]
        phase3.characters[player] = Role.UNDERTAKER
        phase3.characters[body] = Role.SPY
        worlds.append(world3)

    return worlds

def create_worlds_from_ravenkeeper_info(game: Game, info: RavenkeeperInfo):
    player = info['ravenkeeper']
    chosen = info['chosen']
    token = info['token']
    night = info['night']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.RAVENKEEPER, night=night)

    # World where the Ravenkeeper sees the actual token (chosen player is that token)
    world1 = World()
    phase1 = world1.phases[0]
    phase1.characters[player] = Role.RAVENKEEPER
    phase1.characters[chosen] = token
    worlds.append(world1)

    # If the token is an evil character, the chosen player could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = World()
        phase2 = world2.phases[0]
        phase2.characters[player] = Role.RAVENKEEPER
        phase2.characters[chosen] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the chosen player could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = World()
        phase3 = world3.phases[0]
        phase3.characters[player] = Role.RAVENKEEPER
        phase3.characters[chosen] = Role.SPY
        worlds.append(world3)

    return worlds

def create_worlds_from_virgin_nominated(game: Game, info: VirginInfo):
    virgin:int = info['virgin']
    nominator:int = info['nominator']
    executed:bool = info['executed']
    night = info['night']

    worlds: list[World] = []

    if executed:
        world1 = World()
        world1.phases[0].characters[virgin] = Role.VIRGIN
        world1.phases[0].characters[nominator] = Role.ANY_OTHER_TOWNSFOLK
        world1.phases[0].dead[nominator] = True
        worlds.append(world1)
        
        world2 = World()
        world2.phases[0].characters[virgin] = Role.VIRGIN
        world2.phases[0].characters[nominator] = Role.SPY
        world2.phases[0].dead[nominator] = True
        worlds.append(world2)

    else:
        worlds += create_drunk_evil_poisoned_worlds(game, virgin, Role.VIRGIN, night)

        world3 = World()
        world3.phases[0].characters[virgin] = Role.VIRGIN
        world3.phases[0].characters[nominator] = Role.ANY_OTHER_EVIL
        worlds.append(world3)

        world4 = World()
        world4.phases[0].characters[virgin] = Role.VIRGIN
        world4.phases[0].characters[nominator] = Role.ANY_OTHER_OUTSIDER
        worlds.append(world4)

    return worlds

def create_worlds_from_execution(execution: dict[str,int]):
    player = execution['player']
    worlds: list[World] = []

    # Not the demon
    world1 = World()
    phase1 = world1.phases[0]
    phase1.dead[player] = True
    phase1.characters[player] = Role.NON_DEMON
    worlds.append(world1)

    # Is the demon with a Scarlet Woman who is now the demon
    world2 = World()
    phase2 = world2.phases[0]
    phase2.characters[player] = Role.IMP
    phase2.add_minion_type(Role.SCARLET_WOMAN)
    _ = world2.extend_phases()
    phase2_1 = world2.phases[-1]
    phase2_1.dead[player] = True
    phase2_1.on_extend = on_extend_sw_promoted
    _ = on_extend_sw_promoted(phase2_1)
    worlds.append(world2)

    return worlds

def create_worlds_from_night_death(death: dict[str,int]):
    player = death['player']
    worlds: list[World] = []

    # Not the Imp
    world1 = World()
    phase1 = world1.phases[0]
    phase1.dead[player] = True
    phase1.characters[player] = Role.NON_DEMON
    worlds.append(world1)

    # Is the Imp who starpassed and a minion became the Imp
    world2 = World()
    phase2 = world2.phases[0]
    phase2.characters[player] = Role.IMP
    _ = world2.extend_phases()
    phase2_1 = world2.phases[-1]
    phase2_1.dead[player] = True
    phase2_1.on_extend = on_extend_starpass
    _ = on_extend_starpass(phase2_1)
    worlds.append(world2)

    return worlds

def execute_player(world: World, player: int, night: int) -> tuple[World, World | None]:

    phase: World.Phase | None = world.get_phase(night)
    if phase == None:
        phase: World.Phase = world.add_phase(night)      

    phase.dead[player] = True

    # world with no scarlet woman
    if not (Role.ANY_OTHER_MINION in phase.minion_types or Role.SCARLET_WOMAN in phase.minion_types):
        return world, None

    # if there's room for a scarlet woman
    sw_world = copy.deepcopy(self)
    sw_phase = self.get_phase(night)

    # if there's a known scarlet woman, they become the demon
    try:
        idx = sw_phase.characters.index(Role.SCARLET_WOMAN)
        sw_phase.characters[idx] = Role.IMP
    except:
        pass

    # if all minions are accounted for, there cannot be NON_DEMON roles, so any NON_DEMON roles could be potential scarlet women
    for i,c in enumerate(sw_phase.characters):
        if c == Role.NON_DEMON:
            sw_phase[i] = Role.ANY_OTHER
            continue
        if c == Role.ANY_OTHER_MINION:
            sw_phase[i] = Role.ANY_OTHER_EVIL

    # one minion type become Imp
    try:
        idx = sw_phase.minion_types.index(Role.SCARLET_WOMAN)
        sw_phase.minion_types[idx] = Role.IMP
    except:
        idx = sw_phase.minion_types.index(Role.ANY_OTHER_MINION)
        sw_phase.minion_types[idx] = Role.IMP

    return self, sw_world

# def on_extend_sw_promoted(p: World.Phase):
#     # Reasons this could result in an invalid world:
#     # There's no room for a Scarlet Woman
#     # The minion is dead

#     try:
#         p.remove_minion_type()
#     except:
#         return False

#     minion_caught = False
#     for i,c in enumerate(p.characters):
#         if (c == Role.SCARLET_WOMAN or c == Role.ANY_OTHER_MINION or c == Role.ANY_OTHER_EVIL) and not p.dead[i]:
#             p.characters[i] = Role.IMP
#             minion_caught = True
#             continue
#         # If the Scarlet Woman or other minion is dead, return False
#         if (c == Role.SCARLET_WOMAN or c == Role.ANY_OTHER_MINION or c == Role.ANY_OTHER_EVIL) and p.dead[i]:
#             return False
#         if c in MINIONS:
#             return False

#     # Alive non-demons could now be the demon if we don't know who caught the starpass
#     if not minion_caught:
#         for i,c in enumerate(p.characters):
#             if c == Role.NON_DEMON and not p.dead[i]:
#                 p.characters[i] = Role.ANY_OTHER

#     return True

# def on_extend_starpass(p: World.Phase):
#     # Reasons this could result in an invalid world:
#     # The minion is dead
#     try:
#         p.remove_minion_type()
#     except:
#         return False
    
#     minion_caught = False
#     for i,c in enumerate(p.characters):
#         if c in MINIONS or c == Role.ANY_OTHER_MINION or c == Role.ANY_OTHER_EVIL and not p.dead[i]:
#             p.characters[i] = Role.IMP
#             minion_caught = True
#             continue
#         # If the minion is dead, return False
#         if c in MINIONS or c == Role.ANY_OTHER_EVIL and p.dead[i]:
#             return False

#     # Alive non-demons could now be the demon if we don't know who caught the starpass
#     if not minion_caught:
#         for i,c in enumerate(p.characters):
#             if c == Role.NON_DEMON and not p.dead[i]:
#                 p.characters[i] = Role.ANY_OTHER

#     return True