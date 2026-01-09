from world.world import World
from world.phase import Phase
from world.role import *
import random
from itertools import compress
from worldCreator import Info, WasherwomanInfo, LibrarianInfo, InvestigatorInfo, ChefInfo, EmpathInfo, FortuneTellerInfo, UndertakerInfo, RavenkeeperInfo, VirginInfo, SlayerInfo, Claim
from typing import TypedDict

class DeathInfo(TypedDict):
    executed: tuple[int,int] | None
    slayer_shot: tuple[int,int] | None
    killed_by_demon: tuple[int,int] | None

def simulate_info(n: int, players: int, seed=None) -> list[tuple[tuple[list[Info],DeathInfo], World]]:
    random.seed(seed)
    worlds: list[tuple[list, World]] = []
    for _ in range(n):
        info_list = []
        true_world = World(players)
        first_phase = true_world.phases[0]
        death_info: DeathInfo = {
            'executed': None,
            'slayer_shot': None,
            'killed_by_demon': None
        }
        characters = [Role.IMP]
        # pick minions
        minions = random.sample(MINIONS,ROLE_BREAKDOWNS[players]['minions'])
        characters.extend(random.sample(MINIONS,ROLE_BREAKDOWNS[players]['minions']))
        first_phase.minion_types = minions
        # pick outsiders
        num_outsiders = ROLE_BREAKDOWNS[players]['outsiders'] + 2 if Role.BARON in characters else ROLE_BREAKDOWNS[players]['outsiders']
        characters.extend(random.sample(OUTSIDERS,num_outsiders))
        # pick townsfolk
        characters.extend(random.sample(TOWNSFOLK,players-len(characters)))
        # if the drunk is in the game, pick a drunk token not in play
        first_phase.drunk_token = random.choice(list(set(TOWNSFOLK)-set(characters)))
        # pick bluffs
        bluffs = random.sample(list(set(GOOD_CHARACTERS) - set(characters + [Role.DRUNK])), 3)
        # assign roles
        first_phase.characters = random.sample(characters, players)
        if Role.FORTUNE_TELLER in characters:
            red_herring = random.choice([p for p in range(players) if first_phase.characters[p] not in EVIL_CHARACTERS or first_phase.characters[p] == Role.SPY])
            first_phase.red_herring[red_herring] = True
        # if minion is poisoner, choose a poisoned target
        if Role.POISONER in characters:
            targets = [i for i,x in enumerate(first_phase.characters) if x != Role.IMP and x not in MINIONS]
            first_phase.poisoned[random.choice(targets)] = True
        # if there's a slayer, they take their shot
        slayer_claim = None
        if Role.SLAYER in characters:
            slayer_claim = first_phase.characters.index(Role.SLAYER)
            real = not first_phase.poisoned[slayer_claim]
            slayer_info = create_slayer_info(first_phase, slayer_claim, real)
            if slayer_info['successful']:
                true_world.killed_by_slayer(slayer_info['target'], 2)
                death_info['slayer_shot'] = (slayer_info['target'], 2)
            info_list.append(slayer_info)
        # choose execution
        if death_info['slayer_shot'] is None:
            execution_target, virgin_claim = get_execution_target(first_phase, info_list, bluffs)
            true_world.execute_player(execution_target,2)
            death_info['executed'] = (execution_target, 2)
        second_phase = true_world.phases[1]
        # if poisoner is still alive, choose a poisoned target
        if Role.POISONER in characters and second_phase.characters[execution_target] != Role.POISONER:
            targets = [i for i,x in enumerate(second_phase.characters) if x != Role.IMP and x not in MINIONS]
            second_phase.poisoned[random.choice(targets)] = True
        # choose death
        if second_phase.characters[second_phase.dead.index(True)] in MINIONS:
            death_targets = [i for i,x in enumerate(second_phase.characters) if x != Role.IMP and x not in MINIONS]
        else:
            death_targets = list(compress(range(players),second_phase.dead))
        death_target = random.choice(death_targets)
        saved = False
        ravenkeeper_claim = None
        if Role.MONK in characters and not second_phase.poisoned[characters.index(Role.MONK)]:
            saved = random.random()*(players-1) < 1
        if (second_phase.characters[death_target] != Role.SOLDIER or second_phase.poisoned[death_target]) and not saved:
            true_world.killed_by_demon(death_target,2)
            death_info['killed_by_demon'] = (death_target, 2)
            # if poisoner was killed by demon, remove poisoned
            if second_phase.characters[death_target] == Role.POISONER:
                second_phase.poisoned = [False]*players
            # if ravenkeeper was killed by demon, get ravenkeeper info
            if second_phase.characters[death_target] == Role.RAVENKEEPER or \
              (second_phase.characters[death_target] == Role.DRUNK and second_phase.drunk_token == Role.RAVENKEEPER) or \
              (second_phase.characters[death_target] == Role.IMP and Role.RAVENKEEPER in bluffs) or \
              (second_phase.characters[death_target] in MINIONS and random.random() < 0.25):
                real = not second_phase.poisoned[death_target] and \
                  second_phase.drunk_token != Role.RAVENKEEPER and \
                  second_phase.characters[death_target] not in EVIL_CHARACTERS
                info_list.append(create_ravenkeeper_info(second_phase, death_target, real))
                ravenkeeper_claim = death_target
        for j,character in enumerate(first_phase.characters):
            if j == ravenkeeper_claim or j == virgin_claim or j == slayer_claim:
                continue
            if character == Role.IMP:
                # create fake info with bluff
                info_list.extend(create_bluff_info(true_world, j, bluffs))
            elif character in MINIONS:
                # create fake info with no bluff
                info_list.extend(create_no_bluff_info(true_world, j))
            elif character == Role.DRUNK:
                info_list.extend(create_info(true_world, first_phase.drunk_token, j, False))
            else:
                # simulate info
                info_list.extend(create_info(true_world, character, j, True))
        
        worlds.append(((info_list, death_info), true_world))
    return worlds
    
def get_execution_target(phase: Phase, info_list: list, bluffs: list[Role]) -> tuple[int,int|None]:
    if Role.SCARLET_WOMAN in phase.characters:
        execution_targets = range(len(phase.characters))
    else:
        execution_targets = [i for i,x in enumerate(phase.characters) if x != Role.IMP]
    execution_target = random.choice(execution_targets)
    virgin_claim = None
    # if virgin was nominated, get virgin info
    if phase.characters[execution_target] == Role.VIRGIN or \
        (phase.characters[execution_target] == Role.DRUNK and phase.drunk_token == Role.VIRGIN) or \
        (phase.characters[execution_target] == Role.IMP and Role.VIRGIN in bluffs) or \
        (phase.characters[execution_target] in MINIONS and random.random() < 0.25):
        virgin_claim = execution_target
        real = not phase.poisoned[virgin_claim] and \
            phase.drunk_token != Role.VIRGIN and \
            phase.characters[virgin_claim] not in EVIL_CHARACTERS
        virgin_info = create_virgin_info(phase, virgin_claim, real)
        info_list.append(virgin_info)
        if virgin_info['executed']:
            execution_target = virgin_info['nominator']

    return execution_target, virgin_claim

def create_bluff_info(world: World, player: int, bluffs: list[Role]) -> list[Info]:
    bluff = random.choice(bluffs)
    return create_info(world, bluff, player, False)

def create_no_bluff_info(world: World, player: int) -> list[Info]:
    bluff = random.choice(list(set(GOOD_CHARACTERS) - set([Role.DRUNK])))
    return create_info(world, bluff, player, False)

def create_info(world: World, character: Role, player: int, real: bool) -> list[Info]:
    first_phase = world.phases[0]
    if character == Role.WASHERWOMAN:
        return [create_washerwoman_info(first_phase, player, real)]
    elif character == Role.LIBRARIAN:
        return [create_librarian_info(first_phase, player, real)]
    elif character == Role.INVESTIGATOR:
        return [create_investigator_info(first_phase, player, real)]
    elif character == Role.EMPATH:
        info = []
        for phase in world.phases:
            if not phase.dead[player]:
                info.append(create_empath_info(phase, player, real and not phase.poisoned[player]))
        return info
    elif character == Role.FORTUNE_TELLER:
        info = []
        for phase in world.phases:
            if not phase.dead[player]:
                info.append(create_fortune_teller_info(phase, player, real and not phase.poisoned[player]))
        return info
    elif character == Role.UNDERTAKER:
        info = []
        for phase in world.phases:
            if not phase.dead[player] and phase.executee is not None:
                info.append(create_undertaker_info(phase, player, real and not phase.poisoned[player], phase.executee))
        return info
    elif character == Role.RAVENKEEPER:
        return [create_ravenkeeper_info(first_phase, player, real)]
    elif character == Role.VIRGIN:
        return [create_virgin_info(first_phase, player, real)]
    elif character == Role.SLAYER:
        return [create_slayer_info(first_phase, player, real)]
    else:
        return [create_claim_info(player, character)]
    
def create_washerwoman_info(phase: Phase, player: int, real: bool) -> WasherwomanInfo:
    if real:
        townsfolk_options = [i for i,x in enumerate(phase.characters) if x in TOWNSFOLK or x == Role.SPY and i != player]
    else:
        townsfolk_options = [i for i in range(len(phase.characters)) if i != player]
    townsfolk = random.choice(townsfolk_options)
    other_options = [i for i in range(len(phase.characters)) if i != player and i != townsfolk]
    other = random.choice(other_options)
    character = phase.characters[townsfolk] if real and phase.characters[townsfolk] != Role.SPY else random.choice(TOWNSFOLK)
    info: WasherwomanInfo = {
        'washerwoman': player,
        'first_player': townsfolk,
        'second_player': other,
        'townsfolk': character
    }
    return info

def create_librarian_info(phase: Phase, player: int, real: bool) -> LibrarianInfo:
    if real:
        outsider_options = [i for i,x in enumerate(phase.characters) if x in OUTSIDERS or x == Role.SPY and i != player]
    else:
        outsider_options = [i for i in range(len(phase.characters)) if i != player] + [None]
    if len(outsider_options) == 0:
        outsider_options.append(None)
    outsider = random.choice(outsider_options)
    other_options = [i for i in range(len(phase.characters)) if i != player and i != outsider]
    other = None if outsider is None else random.choice(other_options)
    character = None if outsider is None else phase.characters[outsider] if real and phase.characters[outsider] != Role.SPY else random.choice(OUTSIDERS)
    info: LibrarianInfo = {
        'librarian': player,
        'first_player': outsider,
        'second_player': other,
        'token': character
    }
    return info

def create_investigator_info(phase: Phase, player: int, real: bool) -> InvestigatorInfo:
    if real:
        minion_options = [i for i,x in enumerate(phase.characters) if x in MINIONS or x == Role.RECLUSE and i != player]
    else:
        minion_options = [i for i in range(len(phase.characters)) if i != player]
    minion = random.choice(minion_options)
    other_options = [i for i in range(len(phase.characters)) if i != player and i != minion]
    other = random.choice(other_options)
    character = phase.characters[minion] if real and phase.characters[minion] != Role.RECLUSE else random.choice(MINIONS)
    info: InvestigatorInfo = {
        'investigator': player,
        'first_player': minion,
        'second_player': other,
        'minion': character
    }
    return info

def create_chef_info(phase: Phase, player: int, real: bool) -> ChefInfo:
    if real:
        chef_number = 0
        for i,c in enumerate(phase.characters):
            j = (i+1)%len(phase.characters)
            c_j = phase.characters[j]
            if c in EVIL_CHARACTERS and c_j in EVIL_CHARACTERS and c != Role.SPY and c_j != Role.SPY:
                chef_number += 1
            elif c in EVIL_CHARACTERS + [Role.SPY, Role.RECLUSE] and c_j in EVIL_CHARACTERS + [Role.SPY, Role.RECLUSE]:
                chef_number += 1 if random.random() < 0.5 else 0
    else: 
        chef_number = random.randint(0,ROLE_BREAKDOWNS[len(phase.characters)]['minions']+1)

    info: ChefInfo = {
        'chef': player,
        'number': chef_number
    }
    return info

def create_empath_info(phase: Phase, player: int, real: bool) -> EmpathInfo:
    alive_players = list(compress(range(len(phase.characters)), [not x for x in phase.dead]))
    player_idx = alive_players.index(player)
    alive_neighbours = [alive_players[(player_idx-1)%len(alive_players)], alive_players[(player_idx+1)%len(alive_players)]]
    if real:
        evil_neighbours = sum([1 if phase.characters[p] in EVIL_CHARACTERS and phase.characters[p] != Role.SPY else 0 for p in alive_neighbours])
        evil_neighbours += 1 if (phase.characters[alive_neighbours[0]] == Role.SPY or phase.characters[alive_neighbours[0]] == Role.RECLUSE) and random.random() < 0.5 else 0
        evil_neighbours += 1 if (phase.characters[alive_neighbours[1]] == Role.SPY or phase.characters[alive_neighbours[1]] == Role.RECLUSE) and random.random() < 0.5 else 0
    else:
        evil_neighbours = random.randint(0,2)
    info = {
        'empath': player,
        'number': evil_neighbours,
        'night': phase.night,
        'left_neighbour': alive_neighbours[0],
        'right_neighbour': alive_neighbours[1]
    }
    return info

def create_fortune_teller_info(phase: Phase, player: int, real: bool) -> FortuneTellerInfo:
    picks = random.sample(list(compress(range(len(phase.characters)), [not x for x in phase.dead])), 2)
    if real:
        response = any([phase.characters[p] == Role.IMP or phase.red_herring[p] for p in picks])
        response = True if any([phase.characters[p] == Role.RECLUSE for p in picks]) and random.random() < 0.5 else response
    else:
        response = random.random() < 0.5
    info = {
        'player': player,
        'night': phase.night,
        'pings': (tuple(picks),response)
    }
    return info

def create_undertaker_info(phase: Phase, player: int, executee: int, real: bool) -> UndertakerInfo:
    character = phase.characters[executee] if real else random.choice(ALL_CHARACTERS)
    character = random.choice(GOOD_CHARACTERS) if phase.characters[executee] == Role.SPY and random.random() < 0.5 else character
    character = random.choice(EVIL_CHARACTERS) if phase.characters[executee] == Role.RECLUSE and random.random() < 0.5 else character
    info = {
        'undertaker': player,
        'body': executee,
        'token': character,
        'night': phase.night
    }
    return info

def create_ravenkeeper_info(phase: Phase, player: int, real: bool) -> RavenkeeperInfo:
    choice = random.choice(list(compress(range(len(phase.characters)), [not x for x in phase.dead])))
    character = phase.characters[choice] if real else random.choice(ALL_CHARACTERS)
    character = random.choice(GOOD_CHARACTERS) if phase.characters[choice] == Role.SPY and random.random() < 0.5 else character
    character = random.choice(EVIL_CHARACTERS) if phase.characters[choice] == Role.RECLUSE and random.random() < 0.5 else character
    info: RavenkeeperInfo = {
        'ravenkeeper': player,
        'chosen': choice,
        'token': character,
        'night': phase.night
    }
    return info

def create_virgin_info(phase: Phase, player: int, real: bool) -> VirginInfo:
    nominator = random.choice([p for p in range(len(phase.characters)) if p != player])
    executed = real and \
     (phase.characters[nominator] in TOWNSFOLK or \
     (phase.characters[nominator] == Role.SPY and random.random() < 0.5))
    info: VirginInfo = {
        'executed': executed,
        'night': phase.night,
        'nominator': nominator,
        'virgin': player
    }
    return info

def create_slayer_info(phase: Phase, player: int, real: bool) -> SlayerInfo:
    if Role.SCARLET_WOMAN in phase.characters:
        target = random.choice([p for p in range(len(phase.characters)) if p != player])
    else:
        target = random.choice([p for p in range(len(phase.characters)) if p != player and phase.characters[p] != Role.IMP])
    successful = real and \
     (phase.characters[target] == Role.IMP and Role.SCARLET_WOMAN in phase.characters or \
     (phase.characters[target] == Role.RECLUSE and random.random() < 0.5))

    info: SlayerInfo = {
        'slayer': player,
        'target': target,
        'successful': successful,
        'night': phase.night
    }
    return info

def create_claim_info(player: int, claim: Role) -> Claim:
    info: Claim = {
        'character': player,
        'claim': claim
    }
    return info
