import copy

from grimoire import Grimoire, GrimoirePage, Game, NightOrderPosition, GrimoireManager
import grimoire.gamerules as gamerules
import random
from itertools import compress
from grimoire.info import *
from grimoire.info import VirginInfo
from grimoire.role import *
from info_generators import create_bluff_info, create_no_bluff_info, create_info, create_slayer_info, create_ravenkeeper_info, create_virgin_info
from tqdm import tqdm

VIRGIN_BLUFF_CHANCE = 0.34
RAVENKEEPER_BLUFF_CHANCE = 0.34
VIRGIN_NO_BLUFF_CHANCE = 0.1
RAVENKEEPER_NO_BLUFF_CHANCE = 0.1

def run_simulations(n_simulations: int, game: Game, seed: int | None = None, subjective: bool = False, preset: list[Role] | None = None):
    games = simulate_info(n_simulations, game, seed, preset=preset)
    simulations: list[GrimoireManager] = []
    
    for i, ((info_list, death_info), true_grim) in tqdm(enumerate(games)):
        manager = GrimoireManager(game, true_grim)
        
        # Add all info to the manager
        nights = len(true_grim.get_unique_nights())
        manager.add_full_game(info_list, death_info, nights)

        true_world_found = manager.do_grims_contain_true_grim()
        assert true_world_found, f"True world {i} not in created worlds."
        
        perspective_player = random.sample([i for i in true_grim.pages[-1].get_dead_players() if true_grim.pages[-1].characters[i] in GOOD_ROLES], 1)[0]
        solutions = manager.get_player_perspective(perspective_player) if subjective else manager
        simulations.append(solutions)

    return simulations

def simulate_info(n: int, game: Game, seed: int|None=None, preset: list[Role] | None = None) -> list[tuple[tuple[list[Info],DeathInfo], Grimoire]]:
    worlds: list[tuple[tuple[list[Info],DeathInfo], Grimoire]] = []
    for i in range(n):
        sim_seed = seed + i if seed is not None else None
        worlds.append(simulate_single_game(game["players"], preset, sim_seed))
    return worlds

def simulate_single_game(players: int, preset: list[Role] | None, seed: int | None) -> tuple[tuple[list[Info],DeathInfo], Grimoire]:
    if seed is not None:
        random.seed(seed)
    info_list: list[Info] = []
    grim = Grimoire(players)
    first_page = grim.pages[0]
    death_info: DeathInfo = {
        'executed': [],
        'slayer_shot': None,
        'killed_by_demon': []
    }
    characters = choose_characters(players, preset)
    first_page.minion_types = gamerules.get_characters_of_type(characters, MINIONS_SET)
            
    # pick bluffs
    bluff_pool = [
        c for c in GOOD_CHARACTERS if
        c not in characters and
        c is not Role.DRUNK
    ]
    bluffs = random.sample(bluff_pool, 3)

    # assign roles
    first_page.characters = random.sample(characters, players)

    # assign drunk and red herring reminder tokens
    assign_reminder_tokens(first_page, players)

    night = 1

    ravenkeeper_claim = virgin_claim = slayer_claim = None
    while True:
        night_start_page = grim.get_page(night, NightOrderPosition.AFTER_IMP)

        # If poisoner is still alive, choose a poisoned target
        if Role.POISONER in characters and Role.POISONER not in compress(night_start_page.characters, night_start_page.dead):
            targets = [i for i,x in enumerate(night_start_page.characters) if x != Role.IMP and x not in MINIONS]
            night_start_page.poisoned[random.choice(targets)] = True

        if night > 1:
            ravenkeeper_claim = handle_demon_kill(night_start_page, info_list, bluffs, death_info)

        # If there's an alive slayer, they might take their shot
        slayer_claim = get_slayer_claim(night_start_page)
        slayer_info = apply_slayer_shot(slayer_claim, grim, night_start_page, death_info)
        if slayer_info is not None:
            info_list.append(slayer_info)

        alive_players = grim.pages[-1].get_alive_players()
        if len(alive_players) == 3:
            break
        alive_good_players = [i for i,c in enumerate(grim.pages[-1].characters) if i in alive_players and c in GOOD_CHARACTERS]
        if len(alive_good_players) == 1:
            break

        # Choose execution
        virgin_claim = None
        if slayer_info is None and len(alive_players) > 4:
            virgin_claim = handle_execution(grim.pages[-1], info_list, bluffs, grim, death_info)

        grim.add_page(night+1, NightOrderPosition.AFTER_IMP)
        night += 1

    assert gamerules.is_grim_valid(grim), f"Grim not valid \n {grim}"

    # Night info
    info_list.extend(generate_night_info(grim, bluffs, ravenkeeper_claim, virgin_claim, slayer_claim))
    
    random.shuffle(info_list)
    return ((info_list, death_info), grim)

def choose_characters(players: int, preset: list[Role] | None) -> list[Role]:
    characters: list[Role] = []
    if preset is not None:
        characters.extend(preset)
    if Role.IMP not in characters:
        characters.append(Role.IMP)
    # pick minions
    is_baron_needed = len(gamerules.get_characters_of_type(characters, OUTSIDERS_SET)) > gamerules.get_outsider_count(players, False)
    if is_baron_needed:
        characters.append(Role.BARON)
    is_baron_possible = players - (len(characters) - gamerules.get_characters_of_type_count(characters, OUTSIDERS_SET) + 1) >= 2
    possible_minions = MINIONS[:] if is_baron_possible else [m for m in MINIONS if m != Role.BARON]
    preset_minions = gamerules.get_characters_of_type(characters, MINIONS_SET)
    possible_minions = [m for m in possible_minions if m not in preset_minions]
    minions = random.sample(possible_minions, ROLE_BREAKDOWNS[players]['minions'] - len(preset_minions))
    characters.extend(minions)
    # pick outsiders
    preset_outsiders = gamerules.get_characters_of_type(characters, OUTSIDERS_SET)
    possible_outsiders = [o for o in OUTSIDERS if o not in preset_outsiders]
    num_outsiders = gamerules.get_outsider_count(players, Role.BARON in characters) - len(preset_outsiders)
    characters.extend(random.sample(possible_outsiders, num_outsiders))
    # pick townsfolk
    preset_townsfolk = gamerules.get_characters_of_type(characters, TOWNSFOLK_SET)
    possible_townsfolk = [t for t in TOWNSFOLK if t not in preset_townsfolk]
    characters.extend(random.sample(possible_townsfolk, players - len(characters)))
    assert len(characters) == players
    return characters

def assign_reminder_tokens(page: GrimoirePage, players: int):
    # If the drunk is in the game, pick a drunk token not in play
    if Role.DRUNK in page.characters:
        drunk_pool = [c for c in TOWNSFOLK if c not in page.characters]
        page.drunk_token = random.choice(drunk_pool)

    # Choose red herring
    if Role.FORTUNE_TELLER in page.characters:
        red_herring_options = gamerules.get_valid_red_herrings(page.characters)
        red_herring = random.choice(red_herring_options)
        page.red_herring[red_herring] = True

def get_slayer_claim(page: GrimoirePage) -> int | None:
    try:
        slayer_claim = page.characters.index(Role.SLAYER)
        if slayer_claim in page.get_alive_players():
            return slayer_claim
    except ValueError:
        return None

def apply_slayer_shot(slayer: int | None, grim: Grimoire, page: GrimoirePage, death_info: DeathInfo):
    if slayer is None or page.slayer_shot[slayer]:
        return None
    
    shot_chance = 1. / ((len(page.characters) - 5) / 2 + 1)
    if random.random() < 1 - shot_chance:
        return None
    
    page.slayer_shot[slayer] = True

    real = not page.poisoned[slayer]
    slayer_info = create_slayer_info(page, slayer, real)

    if slayer_info["successful"]:
        target = slayer_info["target"]
        night = page.night
        death_info["slayer_shot"] = (target, night)
        slayer_page = grim.add_page(night, NightOrderPosition.AFTER_SLAYER)
        slayer_page.dead[target] = True
        if page.characters[target] == Role.IMP:
            grim.apply_sw_catch(target, slayer_page)

    return slayer_info

def handle_execution(page: GrimoirePage, info_list: list[Info], bluffs: list[Role], true_world: Grimoire, death_info: DeathInfo):
    execution_target = get_execution_target(page)
    assert not page.dead[execution_target]
    virgin_claim = None
    virgin_info, nominator_executed = handle_virgin_claim(page, execution_target, bluffs, true_world, death_info)
    if virgin_info is not None:
        info_list.append(virgin_info)
        virgin_claim = virgin_info['virgin']
    if not nominator_executed:
        execute_player(execution_target, page.night, true_world, death_info)
    return virgin_claim

def get_execution_target(page: GrimoirePage):
    alive_characters = page.get_alive_characters()
    if Role.SCARLET_WOMAN in alive_characters and len(alive_characters) >= 5:
        execution_targets = [i for i,c in enumerate(page.characters) if c != Role.SAINT and not page.dead[i]]
    else:
        execution_targets = [i for i,c in enumerate(page.characters) if c != Role.IMP and c != Role.SAINT and not page.dead[i]]
    if Role.SAINT in alive_characters and page.poisoned[page.characters.index(Role.SAINT)]:
        execution_targets.append(page.characters.index(Role.SAINT))
    assert len(execution_targets) > 0, "No valid execution targets."
    return random.choice(execution_targets)

def handle_virgin_claim(page: GrimoirePage, nominated: int, bluffs: list[Role], grim: Grimoire, death_info: DeathInfo) -> tuple[VirginInfo | None, bool]:
    if page.characters[nominated] == Role.VIRGIN or \
        (page.characters[nominated] == Role.DRUNK and page.drunk_token == Role.VIRGIN) or \
        (page.characters[nominated] == Role.IMP and Role.VIRGIN in bluffs and random.random() < VIRGIN_BLUFF_CHANCE) or \
        (page.characters[nominated] in MINIONS and random.random() < VIRGIN_NO_BLUFF_CHANCE):
        real = (
            not page.poisoned[nominated] and
            page.drunk_token != Role.VIRGIN and
            page.characters[nominated] not in EVIL_CHARACTERS
        )
        virgin_info = create_virgin_info(page, nominated, real)
        if virgin_info['executed']:
            execute_player(virgin_info['nominator'], page.night, grim, death_info)
        return virgin_info, virgin_info['executed']
    return None, False

def execute_player(target: int, night: int, grim: Grimoire, death_info: DeathInfo):
    execution_page = grim.add_page(night, NightOrderPosition.AFTER_EXECUTION)
    execution_page.dead[target] = True
    execution_page.executee = target
    if execution_page.characters[target] == Role.IMP:
        grim.apply_sw_catch(target, execution_page)
    death_info['executed'].append((target, night))

def handle_demon_kill(page: GrimoirePage, info_list: list[Info], bluffs: list[Role], death_info: DeathInfo) -> int | None:
    # Choose target
    alive_imps = page.get_potential_alive_demons()
    if len(alive_imps) > 0:
        assert len(alive_imps) == 1
        alive_imp = alive_imps[0]
    else:
        raise Exception("No alive imps found.")
    if gamerules.can_imp_starpass(page, alive_imp):
        death_targets = page.get_alive_players()
    else:
        death_targets = [i for i in page.get_alive_players() if page.characters[i] != Role.IMP]
    # Add an arbitrary dead player as a valid target
    dead_players = page.get_dead_players()
    if len(dead_players) > 0:
        death_targets.append(dead_players[0])

    death_target = random.choice(death_targets)
    characters = page.characters

    # Monk saved
    if Role.MONK in characters and Role.MONK in page.get_alive_characters() and not page.poisoned[characters.index(Role.MONK)] and random.random() < 1.0/(len(page.get_alive_characters())-1):
        return    
    # Soldier targeted
    if page.characters[death_target] == Role.SOLDIER and not page.poisoned[death_target]:
        return    
    # Already dead
    if page.dead[death_target]:
        return
    
    death_info['killed_by_demon'].append((death_target, page.night))
    page.dead[death_target] = True
    # Starpass
    if page.characters[death_target] == Role.IMP:
        old_minions = [(i,page.characters[i]) for i in page.get_alive_players() if page.characters[i] in MINIONS]
        old_characters = copy.copy(page.characters)
        old_red_herring = copy.copy(page.red_herring)
        new_imp = page.apply_starpass(death_target)
        # Multiple targets to starpass to, need to pick one
        if new_imp is None:
            for i,c in old_minions:
                page.characters[i] = c
            new_imp = random.choice(old_minions)[0]
            page.characters[new_imp] = Role.IMP
            page.character_changed[new_imp] = True
        elif old_characters[new_imp] == Role.SPY and old_red_herring[new_imp]:
            new_red_herring = random.choice(gamerules.get_valid_red_herrings(page.characters))
            page.red_herring[new_red_herring] = True

    # If poisoner was killed by demon, remove poisoned
    if page.characters[death_target] == Role.POISONER:
        page.clear_poisoned()
    # If ravenkeeper claim was killed by demon, get ravenkeeper info
    if page.characters[death_target] == Role.RAVENKEEPER or \
        (page.characters[death_target] == Role.DRUNK and page.drunk_token == Role.RAVENKEEPER) or \
        (page.characters[death_target] == Role.IMP and Role.RAVENKEEPER in bluffs and random.random() < RAVENKEEPER_BLUFF_CHANCE) or \
        (page.characters[death_target] in MINIONS and random.random() < RAVENKEEPER_NO_BLUFF_CHANCE):
        real = (
            not page.poisoned[death_target] and
            page.drunk_token != Role.RAVENKEEPER and
            page.characters[death_target] not in EVIL_CHARACTERS
        )
        info_list.append(create_ravenkeeper_info(page, death_target, real))
        return death_target


def generate_night_info(
        grim: Grimoire, 
        bluffs: list[Role], 
        ravenkeeper_claim: int | None, 
        virgin_claim: int | None, 
        slayer_claim: int | None):
    
    info: list[Info] = []
    page = grim.pages[0]
    for j,character in enumerate(page.characters):
        if j == ravenkeeper_claim or j == virgin_claim or j == slayer_claim:
            continue
        if character == Role.IMP:
            info.extend(create_bluff_info(grim, j, bluffs))
        elif character in MINIONS:
            info.extend(create_no_bluff_info(grim, j))
        elif character == Role.DRUNK:
            assert page.drunk_token is not None
            info.extend(create_info(grim, page.drunk_token, j, False))
        else:
            info.extend(create_info(grim, character, j, True))
    return info


if __name__ == "__main__":
    game: Game = {
        'players': 5
    }
    n = 10
    seed = 12
    x = simulate_info(n, game, seed)
