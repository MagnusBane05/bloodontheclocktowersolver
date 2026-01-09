from typing import TypedDict, Protocol, runtime_checkable
from world.world import World, Role, OUTSIDERS, ROLE_BREAKDOWNS, MINIONS, EVIL_CHARACTERS, GOOD_CHARACTERS

class Game(TypedDict):
    players: int

@runtime_checkable
class Info(Protocol):
    pass

class Claim(Info):
    player: int
    character: Role

class InvestigatorInfo(Info):
    investigator: int
    first_player: int
    second_player: int
    minion: Role

class WasherwomanInfo(Info):
    washerwoman: int
    first_player: int
    second_player: int
    townsfolk: Role

class LibrarianInfo(Info):
    player: int
    first_player: int | None
    second_player: int | None
    token: Role | None

class ChefInfo(Info):
    chef: int
    number: int

class FortuneTellerInfo(Info):
    player: int
    night: int
    pings: tuple[tuple[int,int],bool]

class EmpathInfo(Info):
    empath: int
    number: int
    night: int
    left_neighbour: int
    right_neighbour: int    

class UndertakerInfo(Info):
    undertaker: int
    body: int
    token: Role
    night: int

class RavenkeeperInfo(Info):
    ravenkeeper: int
    chosen: int
    token: Role
    night: int

class VirginInfo(Info):
    virgin: int
    nominator: int
    executed: bool
    night: int

class SlayerInfo(Info):
    slayer: int
    target: int
    successful: bool
    night: int

def create_drunk_evil_poisoned_worlds(game: Game, player: int, token: Role, night:int=1) -> list[World]:
    worlds: list[World] = []

    world1 = World(game['players'])
    if night == 1:
        phase1 = world1.phases[0]
    else:
        phase1 = world1.add_phase(night)
    phase1.characters[player] = Role.DRUNK
    phase1.drunk_token = token
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase1.add_minion_type(Role.BARON)
    worlds.append(world1)

    world2 = World(game['players'])
    if night == 1:
        phase2 = world2.phases[0]
    else:
        phase2 = world2.add_phase(night)
    phase2.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world2)

    world3 = World(game['players'])
    if night == 1:
        phase3 = world3.phases[0]
    else:
        phase3 = world3.add_phase(night)
    phase3.characters[player] = token
    phase3.poisoned[player] = True
    phase3.add_minion_type(Role.POISONER)
    worlds.append(world3)

    return worlds


def create_worlds_from_claim(game: Game, claim: Claim) -> list[World]:
    player = claim['player']
    character = claim['character']
    worlds: list[World] = []

    # World where the player is the Drunk
    if character not in OUTSIDERS:
        world_drunk = World(game['players'])
        phase_drunk = world_drunk.phases[0]
        phase_drunk.characters[player] = Role.DRUNK
        phase_drunk.drunk_token = character
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase_drunk.add_minion_type(Role.BARON)
        worlds.append(world_drunk)

    # World where the player is an unspecified evil character
    world_evil = World(game['players'])
    phase_evil = world_evil.phases[0]
    phase_evil.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world_evil)

    # World where the player is exactly the claimed character
    world_claimed = World(game['players'])
    phase_claimed = world_claimed.phases[0]
    phase_claimed.characters[player] = character
    if character in OUTSIDERS:
        phase_claimed.add_minion_type(Role.BARON)
    worlds.append(world_claimed)

    return worlds

def create_worlds_from_investigator_info(game: Game, info: InvestigatorInfo):
    player = info['investigator']
    worlds = create_drunk_evil_poisoned_worlds(game, player, Role.INVESTIGATOR)

    world3 = World(game['players'])
    phase3 = world3.phases[0]
    phase3.characters[player] = Role.INVESTIGATOR
    phase3.characters[info['first_player']] = info['minion']
    phase3.add_minion_type(info['minion'])
    worlds.append(world3)

    world4 = World(game['players'])
    phase4 = world4.phases[0]
    phase4.characters[player] = Role.INVESTIGATOR
    phase4.characters[info['second_player']] = info['minion']
    phase4.add_minion_type(info['minion'])
    worlds.append(world4)

    world5 = World(game['players'])
    phase5 = world5.phases[0]
    phase5.characters[player] = Role.INVESTIGATOR
    phase5.characters[info['first_player']] = Role.RECLUSE
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase5.add_minion_type(Role.BARON)
    worlds.append(world5)

    world6 = World(game['players'])
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

    world3 = World(game['players'])
    phase3 = world3.phases[0]
    phase3.characters[player] = Role.WASHERWOMAN
    phase3.characters[info['first_player']] = info['townsfolk']
    worlds.append(world3)

    world4 = World(game['players'])
    phase4 = world4.phases[0]
    phase4.characters[player] = Role.WASHERWOMAN
    phase4.characters[info['second_player']] = info['townsfolk']
    worlds.append(world4)

    world5 = World(game['players'])
    phase5 = world5.phases[0]
    phase5.characters[player] = Role.WASHERWOMAN
    phase5.characters[info['first_player']] = Role.SPY
    phase5.add_minion_type(Role.SPY)
    worlds.append(world5)

    world6 = World(game['players'])
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

    world = World(game['players'])
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
        world_no_outsiders = World(game['players'])
        world_no_outsiders.phases[0].characters[player] = Role.LIBRARIAN
        world_no_outsiders.phases[0].no_outsiders = True
        worlds.append(world_no_outsiders)
        return

    world3 = World(game['players'])
    phase3 = world3.phases[0]
    phase3.characters[player] = Role.LIBRARIAN
    phase3.characters[first_player] = token
    worlds.append(world3)

    world4 = World(game['players'])
    phase4 = world4.phases[0]
    phase4.characters[player] = Role.LIBRARIAN
    phase4.characters[second_player] = token
    worlds.append(world4)

    world5 = World(game['players'])
    phase5 = world5.phases[0]
    phase5.characters[player] = Role.LIBRARIAN
    phase5.characters[first_player] = Role.SPY
    phase5.add_minion_type(Role.SPY)
    worlds.append(world5)

    world6 = World(game['players'])
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
        world4 = World(game['players'])
        if night == 1:
            phase4 = world4.phases[0]
        else:
            phase4 = world4.add_phase(night)
        phase4.characters[player] = Role.FORTUNE_TELLER
        phase4.characters[a] = Role.IMP
        worlds.append(world4)

        ## Player b is the Demon
        world5 = World(game['players'])
        if night == 1:
            phase5 = world5.phases[0]
        else:
            phase5 = world5.add_phase(night)
        phase5.characters[player] = Role.FORTUNE_TELLER
        phase5.characters[b] = Role.IMP
        worlds.append(world5)

        ## Player a is the Red Herring
        world6 = World(game['players'])
        if night == 1:
            phase6 = world6.phases[0]
        else:
            phase6 = world6.add_phase(night)
        phase6.characters[player] = Role.FORTUNE_TELLER
        phase6.characters[a] = Role.ANY_OTHER_GOOD
        phase6.red_herring[a] = True
        worlds.append(world6)

        ## Player b is the Red Herring
        world7 = World(game['players'])
        if night == 1:
            phase7 = world7.phases[0]
        else:
            phase7 = world7.add_phase(night)
        phase7.characters[player] = Role.FORTUNE_TELLER
        phase7.characters[b] = Role.ANY_OTHER_GOOD
        phase7.red_herring[b] = True
        worlds.append(world7)

        ## Player a is the Recluse
        world8 = World(game['players'])
        if night == 1:
            phase8 = world8.phases[0]
        else:
            phase8 = world8.add_phase(night)
        phase8.characters[player] = Role.FORTUNE_TELLER
        phase8.characters[a] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase8.add_minion_type(Role.BARON)
        worlds.append(world8)

        ## Player b is the Recluse
        world9 = World(game['players'])
        if night == 1:
            phase9 = world9.phases[0]
        else:
            phase9 = world9.add_phase(night)
        phase9.characters[player] = Role.FORTUNE_TELLER
        phase9.characters[b] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase9.add_minion_type(Role.BARON)
        worlds.append(world9)

    else:
        ## Player a is not the Imp and Player b is not the Imp
        world10 = World(game['players'])
        if night == 1:
            phase10 = world10.phases[0]
        else:
            phase10 = world10.add_phase(night)
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
        world1 = World(game['players'])
        if night == 1:
            phase1 = world1.phases[0]
        else:
            phase1 = world1.add_phase(night)
        phase1.characters[player] = Role.EMPATH
        phase1.characters[left] = Role.ANY_OTHER_GOOD
        phase1.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world1)

        # Left neighbour is the Spy (registering as good)
        world2 = World(game['players'])
        if night == 1:
            phase2 = world2.phases[0]
        else:
            phase2 = world2.add_phase(night)
        phase2.characters[player] = Role.EMPATH
        phase2.characters[left] = Role.SPY
        phase2.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world2)

        # Right neighbour is the Spy (registering as good)
        world3 = World(game['players'])
        if night == 1:
            phase3 = world3.phases[0]
        else:
            phase3 = world3.add_phase(night)
        phase3.characters[player] = Role.EMPATH
        phase3.characters[left] = Role.ANY_OTHER_GOOD
        phase3.characters[right] = Role.SPY
        worlds.append(world3)

    elif number == 1:
        # Left neighbour is any other evil and right neighbour is good
        world4 = World(game['players'])
        if night == 1:
            phase4 = world4.phases[0]
        else:
            phase4 = world4.add_phase(night)
        phase4.characters[player] = Role.EMPATH
        phase4.characters[left] = Role.ANY_OTHER_EVIL
        phase4.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world4)

        # Right neighbour is any other evil and left neighbour is good
        world5 = World(game['players'])
        if night == 1:
            phase5 = world5.phases[0]
        else:
            phase5 = world5.add_phase(night)
        phase5.characters[player] = Role.EMPATH
        phase5.characters[left] = Role.ANY_OTHER_GOOD
        phase5.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world5)

        # Left neighbour is any other evil and right neighbour is the Spy
        world6 = World(game['players'])
        if night == 1:
            phase6 = world6.phases[0]
        else:
            phase6 = world6.add_phase(night)
        phase6.characters[player] = Role.EMPATH
        phase6.characters[left] = Role.ANY_OTHER_EVIL
        phase6.characters[right] = Role.SPY
        worlds.append(world6)

        # Right neighbour is any other evil and left neighbour is the Spy
        world7 = World(game['players'])
        if night == 1:
            phase7 = world7.phases[0]
        else:
            phase7 = world7.add_phase(night)
        phase7.characters[player] = Role.EMPATH
        phase7.characters[left] = Role.SPY
        phase7.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world7)

        # Left neighbour is the Recluse and right neighbour is good
        world8 = World(game['players'])
        if night == 1:
            phase8 = world8.phases[0]
        else:
            phase8 = world8.add_phase(night)
        phase8.characters[player] = Role.EMPATH
        phase8.characters[left] = Role.RECLUSE
        phase8.characters[right] = Role.ANY_OTHER_GOOD
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase8.add_minion_type(Role.BARON)
        worlds.append(world8)

        # Right neighbour is the Recluse and left neighbour is good
        world9 = World(game['players'])
        if night == 1:
            phase9 = world9.phases[0]
        else:
            phase9 = world9.add_phase(night)
        phase9.characters[player] = Role.EMPATH
        phase9.characters[left] = Role.ANY_OTHER_GOOD
        phase9.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase9.add_minion_type(Role.BARON)
        worlds.append(world9)

        # Left neighbour is the Recluse and right neighbour is the Spy
        world10 = World(game['players'])
        if night == 1:
            phase10 = world10.phases[0]
        else:
            phase10 = world10.add_phase(night)
        phase10.characters[player] = Role.EMPATH
        phase10.characters[left] = Role.RECLUSE
        phase10.characters[right] = Role.SPY
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase10.add_minion_type(Role.BARON)
        worlds.append(world10)

        # Right neighbour is the Recluse and left neighbour is the Spy
        world11 = World(game['players'])
        if night == 1:
            phase11 = world11.phases[0]
        else:
            phase11 = world11.add_phase(night)
        phase11.characters[player] = Role.EMPATH
        phase11.characters[left] = Role.SPY
        phase11.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase11.add_minion_type(Role.BARON)
        worlds.append(world11)

    else:  # number == 2
        # Both neighbours are evil
        world12 = World(game['players'])
        if night == 1:
            phase12 = world12.phases[0]
        else:
            phase12 = world12.add_phase(night)
        phase12.characters[player] = Role.EMPATH
        phase12.characters[left] = Role.ANY_OTHER_EVIL
        phase12.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world12)

        # Left neighbour is evil and right is the Recluse
        world13 = World(game['players'])
        if night == 1:
            phase13 = world13.phases[0]
        else:
            phase13 = world13.add_phase(night)
        phase13.characters[player] = Role.EMPATH
        phase13.characters[left] = Role.ANY_OTHER_EVIL
        phase13.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase13.add_minion_type(Role.BARON)
        worlds.append(world13)

        # Right neighbour is evil and left is the Recluse
        world14 = World(game['players'])
        if night == 1:
            phase14 = world14.phases[0]
        else:
            phase14 = world14.add_phase(night)
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
    world1 = World(game['players'])
    if night == 1:
        phase1 = world1.phases[0]
    else:
        phase1 = world1.add_phase(night)
    phase1.characters[player] = Role.UNDERTAKER
    phase1.characters[body] = token
    worlds.append(world1)

    # If the token is an evil character, the body could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = World(game['players'])
        if night == 1:
            phase2 = world2.phases[0]
        else:
            phase2 = world2.add_phase(night)
        phase2.characters[player] = Role.UNDERTAKER
        phase2.characters[body] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the body could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = World(game['players'])
        if night == 1:
            phase3 = world3.phases[0]
        else:
            phase3 = world3.add_phase(night)
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
    world1 = World(game['players'])
    if night == 1:
        phase1 = world1.phases[0]
    else:
        phase1 = world1.add_phase(night)
    phase1.characters[player] = Role.RAVENKEEPER
    phase1.characters[chosen] = token
    worlds.append(world1)

    # If the token is an evil character, the chosen player could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = World(game['players'])
        if night == 1:
            phase2 = world2.phases[0]
        else:
            phase2 = world2.add_phase(night)
        phase2.characters[player] = Role.RAVENKEEPER
        phase2.characters[chosen] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the chosen player could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = World(game['players'])
        if night == 1:
            phase3 = world3.phases[0]
        else:
            phase3 = world3.add_phase(night)
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
        world1 = World(game['players'])
        if night == 1:
            phase1 = world1.phases[0]
        else:
            phase1 = world1.add_phase(night)
        phase1.characters[virgin] = Role.VIRGIN
        phase1.characters[nominator] = Role.ANY_OTHER_TOWNSFOLK
        phase1.dead[nominator] = True
        worlds.append(world1)
        
        world2 = World(game['players'])
        if night == 1:
            phase2 = world2.phases[0]
        else:
            phase2 = world2.add_phase(night)
        phase2.characters[virgin] = Role.VIRGIN
        phase2.characters[nominator] = Role.SPY
        phase2.dead[nominator] = True
        worlds.append(world2)

    else:
        worlds += create_drunk_evil_poisoned_worlds(game, virgin, Role.VIRGIN, night)

        world3 = World(game['players'])
        if night == 1:
            phase3 = world3.phases[0]
        else:
            phase3 = world3.add_phase(night)
        phase3.characters[virgin] = Role.VIRGIN
        phase3.characters[nominator] = Role.ANY_OTHER_EVIL
        worlds.append(world3)

        world4 = World(game['players'])
        if night == 1:
            phase4 = world4.phases[0]
        else:
            phase4 = world4.add_phase(night)
        phase4.characters[virgin] = Role.VIRGIN
        phase4.characters[nominator] = Role.ANY_OTHER_OUTSIDER
        worlds.append(world4)

    return worlds

def create_worlds_from_slayer_info(game: Game, info: SlayerInfo):
    slayer = info['slayer']
    target = info['target']
    successful = info['successful']
    night = info['night']

    worlds = create_drunk_evil_poisoned_worlds(game, slayer, Role.SLAYER, night)

    if successful:
        # World where the slayer killed the Imp
        world1 = World(game['players'])
        if night == 1:
            phase1 = world1.phases[0]
        else:
            phase1 = world1.add_phase(night)
        phase1.characters[slayer] = Role.SLAYER
        phase1.characters[target] = Role.IMP
        worlds.append(world1)

        # World where the slayer killed the Recluse (registering as evil)
        world2 = World(game['players'])
        if night == 1:
            phase2 = world2.phases[0]
        else:
            phase2 = world2.add_phase(night)
        phase2.characters[slayer] = Role.SLAYER
        phase2.characters[target] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    else:
        # World where the slayer's shot hit a non-demon
        world3 = World(game['players'])
        if night == 1:
            phase3 = world3.phases[0]
        else:
            phase3 = world3.add_phase(night)
        phase3.characters[slayer] = Role.SLAYER
        phase3.characters[target] = Role.NON_DEMON
        worlds.append(world3)

    return worlds

def create_worlds_from_slayer_kill(worlds: list[World], target: int, night: int):
    new_worlds: list[World] = []
    for world in worlds:
        recluse_world, imp_world = world.killed_by_slayer(target, night)
        if recluse_world is not None:
            new_worlds.append(recluse_world)
        if imp_world is not None:
            new_worlds.append(imp_world)

    return new_worlds


def create_worlds_from_execution(worlds: list[World], player: int, night: int):
    new_worlds: list[World] = []
    for world in worlds:
        no_sw_world, sw_world = world.execute_player(player, night)
        if no_sw_world != None:
            new_worlds.append(no_sw_world)
        if sw_world != None:
            new_worlds.append(sw_world)

    return new_worlds

def create_worlds_from_night_kill(worlds: list[World], player: int, night: int):
    new_worlds: list[World] = []
    for world in worlds:
        no_sp_world, sp_world = world.killed_by_demon(player, night)
        if no_sp_world != None:
            new_worlds.append(no_sp_world)
        if sp_world != None:
            new_worlds.append(sp_world)

    return new_worlds