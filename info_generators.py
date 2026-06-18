import random
from itertools import compress

from grimoire import Grimoire, GrimoirePage, NightOrderPosition
from grimoire.gamerules import ROLE_BREAKDOWNS
from grimoire.info import *
from grimoire.role import *

def create_bluff_info(world: Grimoire, player: int, bluffs: list[Role]) -> list[Info]:
    bluff = random.choice(bluffs)
    return create_info(world, bluff, player, False)

def create_no_bluff_info(world: Grimoire, player: int) -> list[Info]:
    bluff_pool = [c for c in GOOD_CHARACTERS if c not  in {Role.DRUNK, Role.VIRGIN, Role.RAVENKEEPER}]
    bluff = random.choice(bluff_pool)
    return create_info(world, bluff, player, False)

def create_info(world: Grimoire, character: Role, player: int, real: bool) -> list[Info]:
    first_phase = world.pages[0]
    unique_nights = world.get_unique_nights()
    if character == Role.WASHERWOMAN:
        return [create_washerwoman_info(first_phase, player, real and not first_phase.poisoned[player])]
    elif character == Role.LIBRARIAN:
        return [create_librarian_info(first_phase, player, real and not first_phase.poisoned[player])]
    elif character == Role.INVESTIGATOR:
        return [create_investigator_info(first_phase, player, real and not first_phase.poisoned[player])]
    elif character == Role.CHEF:
        return [create_chef_info(first_phase, player, real and not first_phase.poisoned[player])]
    elif character == Role.EMPATH:
        info: list[Info] = []
        count = 0
        for night in unique_nights:
            page = world.get_page(night, NightOrderPosition.AFTER_IMP)
            assert(page != None)
            if not page.dead[player]:
                info.append(create_empath_info(page, player, real and not page.poisoned[player]))
                count += 1
        if count == 0:
            return [create_claim_info(player, character)]
        return info
    elif character == Role.FORTUNE_TELLER:
        info = []
        count = 0
        for night in unique_nights:
            page = world.get_page(night, NightOrderPosition.AFTER_IMP)
            assert(page != None)
            if not page.dead[player]:
                info.append(create_fortune_teller_info(page, player, real and not page.poisoned[player]))
                count += 1
        if count == 0:
            return [create_claim_info(player, character)]
        return info
    elif character == Role.UNDERTAKER:
        info = []
        count = 0
        for night in unique_nights:
            page = world.get_page(night, NightOrderPosition.AFTER_IMP)
            assert(page != None)
            executed_page = world.get_page(night-1, NightOrderPosition.AFTER_EXECUTION)
            if executed_page == None:
                continue
            executee = executed_page.executee
            assert executee is not None
            if not page.dead[player]:
                info.append(create_undertaker_info(page, player, executee, executed_page.characters[executee], real and not page.poisoned[player]))
                count += 1
        if count == 0:
            return [create_claim_info(player, character)]
        return info
    elif character == Role.SLAYER:
        return [create_slayer_info(first_phase, player, real and not first_phase.poisoned[player])]
    else:
        return [create_claim_info(player, character)]
    
def create_washerwoman_info(phase: GrimoirePage, player: int, real: bool) -> WasherwomanInfo:
    if real:
        townsfolk_options = [i for i,x in enumerate(phase.characters) if x in TOWNSFOLK or x == Role.SPY and i != player]
    else:
        townsfolk_options = [i for i in range(len(phase.characters)) if i != player]
    townsfolk = random.choice(townsfolk_options)
    other_options = [i for i in range(len(phase.characters)) if i != player and i != townsfolk]
    other = random.choice(other_options)
    character = phase.characters[townsfolk] if real and phase.characters[townsfolk] != Role.SPY else random.choice(TOWNSFOLK)
    info: WasherwomanInfo = {
        'kind': "washerwoman",
        'washerwoman': player,
        'first_player': townsfolk,
        'second_player': other,
        'townsfolk': character
    }
    return info

def create_librarian_info(phase: GrimoirePage, player: int, real: bool) -> LibrarianInfo:
    if real:
        outsider_options: list[int | None] = [i for i,x in enumerate(phase.characters) if x in OUTSIDERS or x == Role.SPY and i != player]
    else:
        outsider_options = [i for i in range(len(phase.characters)) if i != player] + [None]
    if len(outsider_options) == 0:
        outsider_options.append(None)
    outsider = random.choice(outsider_options)
    other_options = [i for i in range(len(phase.characters)) if i != player and i != outsider]
    other = None if outsider is None else random.choice(other_options)
    character = None if outsider is None else phase.characters[outsider] if real and phase.characters[outsider] != Role.SPY else random.choice(OUTSIDERS)
    info: LibrarianInfo = {
        'kind': "librarian",
        'librarian': player,
        'first_player': outsider,
        'second_player': other,
        'token': character
    }
    return info

def create_investigator_info(phase: GrimoirePage, player: int, real: bool) -> InvestigatorInfo:
    if real:
        minion_options = [i for i,x in enumerate(phase.characters) if x in MINIONS or x == Role.RECLUSE and i != player]
    else:
        minion_options = [i for i in range(len(phase.characters)) if i != player]
    minion = random.choice(minion_options)
    other_options = [i for i in range(len(phase.characters)) if i != player and i != minion]
    other = random.choice(other_options)
    character = phase.characters[minion] if real and phase.characters[minion] != Role.RECLUSE else random.choice(MINIONS)
    info: InvestigatorInfo = {
        'kind': "investigator",
        'investigator': player,
        'first_player': minion,
        'second_player': other,
        'minion': character
    }
    return info

def create_chef_info(phase: GrimoirePage, player: int, real: bool) -> ChefInfo:
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
        'kind': "chef",
        'chef': player,
        'number': chef_number
    }
    return info

def create_empath_info(phase: GrimoirePage, player: int, real: bool) -> EmpathInfo:
    alive_players = list(compress(range(len(phase.characters)), [not x for x in phase.dead]))
    player_idx = alive_players.index(player)
    alive_neighbours = [alive_players[(player_idx-1)%len(alive_players)], alive_players[(player_idx+1)%len(alive_players)]]
    if real:
        evil_neighbours = sum([1 if phase.characters[p] in EVIL_CHARACTERS and phase.characters[p] != Role.SPY else 0 for p in alive_neighbours])
        evil_neighbours += 1 if (phase.characters[alive_neighbours[0]] == Role.SPY or phase.characters[alive_neighbours[0]] == Role.RECLUSE) and random.random() < 0.5 else 0
        evil_neighbours += 1 if (phase.characters[alive_neighbours[1]] == Role.SPY or phase.characters[alive_neighbours[1]] == Role.RECLUSE) and random.random() < 0.5 else 0
    else:
        evil_neighbours = random.randint(0,2)
    info: EmpathInfo = {
        'kind': "empath",
        'empath': player,
        'number': evil_neighbours,
        'night': phase.night,
        'left_neighbour': alive_neighbours[0],
        'right_neighbour': alive_neighbours[1]
    }
    return info

def create_fortune_teller_info(phase: GrimoirePage, player: int, real: bool) -> FortuneTellerInfo:
    a,b = random.sample(list(compress(range(len(phase.characters)), [not x for x in phase.dead])), 2)
    picks: tuple[int,int] = (a,b)
    if real:
        response = any([phase.characters[p] == Role.IMP or phase.red_herring[p] for p in picks])
        response = True if any([phase.characters[p] == Role.RECLUSE for p in picks]) and random.random() < 0.5 else response
    else:
        response = random.random() < 0.5
    info: FortuneTellerInfo = {
        'kind': "fortune teller",
        'fortune_teller': player,
        'night': phase.night,
        'pings': (picks,response)
    }
    return info

def create_undertaker_info(phase: GrimoirePage, player: int, executee: int, executed_character: Role, real: bool) -> UndertakerInfo:
    assert isinstance(ALL_CHARACTERS, list)
    assert isinstance(GOOD_CHARACTERS, list)
    assert isinstance(EVIL_CHARACTERS, list)

    character = executed_character if real else random.choice(ALL_CHARACTERS)
    character = random.choice(GOOD_CHARACTERS) if executed_character == Role.SPY and random.random() < 0.5 else character
    character = random.choice(EVIL_CHARACTERS) if executed_character == Role.RECLUSE and random.random() < 0.5 else character
    info: UndertakerInfo = {
        'kind': "undertaker",
        'undertaker': player,
        'body': executee,
        'token': character,
        'night': phase.night
    }
    return info

def create_ravenkeeper_info(phase: GrimoirePage, player: int, real: bool) -> RavenkeeperInfo:
    assert isinstance(ALL_CHARACTERS, list)
    assert isinstance(GOOD_CHARACTERS, list)
    assert isinstance(EVIL_CHARACTERS, list)

    choice = random.choice(list(compress(range(len(phase.characters)), [not x for x in phase.dead])))
    character = phase.characters[choice] if real else random.choice(ALL_CHARACTERS)
    character = random.choice(GOOD_CHARACTERS) if phase.characters[choice] == Role.SPY and random.random() < 0.5 else character
    character = random.choice(EVIL_CHARACTERS) if phase.characters[choice] == Role.RECLUSE and random.random() < 0.5 else character
    info: RavenkeeperInfo = {
        'kind': "ravenkeeper",
        'ravenkeeper': player,
        'chosen': choice,
        'token': character,
        'night': phase.night
    }
    return info

def create_virgin_info(phase: GrimoirePage, player: int, real: bool) -> VirginInfo:
    nominator = random.choice([p for p in range(len(phase.characters)) if p != player and not phase.dead[p]])
    executed = real and \
     (phase.characters[nominator] in TOWNSFOLK or \
     (phase.characters[nominator] == Role.SPY and random.random() < 0.5))
    info: VirginInfo = {
        'kind': "virgin",
        'executed': executed,
        'night': phase.night,
        'nominator': nominator,
        'virgin': player
    }
    return info

def create_slayer_info(phase: GrimoirePage, player: int, real: bool) -> SlayerInfo:
    if Role.SCARLET_WOMAN in phase.get_alive_characters():
        target = random.choice([p for p in range(len(phase.characters)) if p != player])
    else:
        target = random.choice([p for p in range(len(phase.characters)) if p != player and phase.characters[p] != Role.IMP])
    successful = real and \
     (phase.characters[target] == Role.IMP or \
     (phase.characters[target] == Role.RECLUSE and random.random() < 0.5))

    info: SlayerInfo = {
        'kind': "slayer",
        'slayer': player,
        'target': target,
        'successful': successful,
        'night': phase.night
    }
    return info

def create_claim_info(player: int, claim: Role) -> Claim:
    info: Claim = {
        'kind': "claim",
        'player': player,
        'character': claim
    }
    return info