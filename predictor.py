from world.world import World
import numpy as np
import pandas as pd
from worldCreator import Game
from world.role import Role, ROLE_BREAKDOWNS, MINIONS
from pprint import pprint
from itertools import permutations
from collections import defaultdict
import random
from simulator import simulate_info

def _set_up_worlds(worlds: list[World], game: Game) -> pd.DataFrame:
    zeros = np.zeros((game['players'],Role.__len__()))
    player_characters = pd.DataFrame(zeros, columns=[x.name for x in Role])
    for world in worlds:
        for i,c in enumerate(world.phases[-1].characters):
            player_characters.loc[i,c.name] += 1

    # remove roles with zero probability
    player_characters = player_characters.loc[:, (player_characters != 0).any(axis=0)]

    return player_characters

def _calculate_demon_df(worlds: list[World], game: Game) -> pd.DataFrame:
    player_characters = _set_up_worlds(worlds, game)
    demon_cols = [
        Role.ANY_OTHER.name,
        Role.ANY_OTHER_EVIL.name,
        Role.IMP.name,
    ]
    player_characters["demon"] = sum(player_characters[col] for col in demon_cols if col in player_characters.columns)
    player_characters = player_characters[['demon']]

    total_possible_demons = sum(player_characters['demon'])
    player_characters['weights'] = player_characters['demon'] / total_possible_demons
    return player_characters

def predict_demon(worlds: list[World], game: Game) -> tuple[int,float]:
    player_characters: pd.DataFrame = _calculate_demon_df(worlds, game)
    pprint(player_characters)
    player_characters.sort_values(by='weights', ascending=False, inplace=True)
    return player_characters.index[0].item(), player_characters['weights'][player_characters.index[0]].item()

def _calculate_evil_team_df(worlds: list[World], game: Game) -> pd.DataFrame:
    possible_teams = permutations(range(game['players']), r=1+ROLE_BREAKDOWNS[game['players']]['minions'])
    
    worlds_viable_for_team = defaultdict(int)
    for team in possible_teams:
        demon = team[0]
        for world in worlds:
            if world.phases[-1].characters[demon] in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.IMP] and \
              all([world.phases[-1].characters[x] in MINIONS + [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION] for x in team[1:]]):
                worlds_viable_for_team[team] += 1

    viable_worlds = pd.DataFrame.from_dict(worlds_viable_for_team, orient='index', columns=['viable_worlds'])
    viable_worlds['probability'] = viable_worlds['viable_worlds'] / sum(viable_worlds['viable_worlds'])
    return viable_worlds

def predict_evil_team(worlds: list[World], game: Game) -> tuple[tuple[int,...], float]:
    viable_worlds: pd.DataFrame = _calculate_evil_team_df(worlds, game)
    pprint(viable_worlds)
    viable_worlds.sort_values(by='probability', ascending=False, inplace=True)
    return viable_worlds.index[0], viable_worlds['probability'][viable_worlds.index[0]].item()

def _calculate_minion_types_df(worlds: list[World], game: Game) -> pd.DataFrame:
    minion_type_counts = defaultdict(int)

    for world in worlds:
        for minion_type in world.phases[-1].minion_types:
            minion_type_counts[minion_type] += 1

    minion_type_df = pd.DataFrame.from_dict(minion_type_counts, orient='index', columns=['count'])
    minion_type_df['probability'] = minion_type_df['count'] / sum(minion_type_df['count'])
    return minion_type_df

def predict_minion_type(worlds: list[World], game: Game) -> tuple[Role, float]:
    minion_type_df: pd.DataFrame = _calculate_minion_types_df(worlds, game)
    pprint(minion_type_df)
    minion_type_df.sort_values(by='probability', ascending=False, inplace=True)
    return minion_type_df.index[0], minion_type_df['probability'][minion_type_df.index[0]].item()

def guess_correct_world(worlds: list[World], game: Game) -> World:
    demon_df = _calculate_demon_df(worlds, game)
    evil_team_df = _calculate_evil_team_df(worlds, game)
    minion_type_df = _calculate_minion_types_df(worlds, game)
    worlds_df = pd.DataFrame({'world': list(range(len(worlds)))})
    worlds_df['demon_weight'] = 0.0
    worlds_df['evil_team_weight'] = 0.0
    worlds_df['minion_type_weight'] = 0.0

    demon_roles = [Role.IMP, Role.ANY_OTHER_EVIL, Role.ANY_OTHER]
    minion_allowed = MINIONS + [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION]

    for i, world in enumerate(worlds):
        # demon weight: sum demon_df player's weights when that player can be demon in this world
        for player in range(game['players']):
            if world.phases[-1].characters[player] in demon_roles:
                if player in demon_df.index:
                    worlds_df.at[i, 'demon_weight'] += demon_df.at[player, 'weights']

        # evil team weight: sum team probabilities where team[0] can be demon and team[1] can be minion
        for team, row in evil_team_df.iterrows():
            prob = row['probability']
            if world.phases[-1].characters[team[0]] in demon_roles and world.phases[-1].characters[team[1]] in minion_allowed:
                worlds_df.at[i, 'evil_team_weight'] += prob

        # minion type weight: add probability for minion types that match this world's minion types
        for mt in world.phases[-1].minion_types:
            if mt in minion_type_df.index:
                worlds_df.at[i, 'minion_type_weight'] += minion_type_df.at[mt, 'probability']

    # normalize each column to sum to 1 (if there is any weight)
    total = worlds_df['demon_weight'].sum()
    if total > 0:
        worlds_df['demon_weight'] = worlds_df['demon_weight'] / total

    total = worlds_df['evil_team_weight'].sum()
    if total > 0:
        worlds_df['evil_team_weight'] = worlds_df['evil_team_weight'] / total

    total = worlds_df['minion_type_weight'].sum()
    if total > 0:
        worlds_df['minion_type_weight'] = worlds_df['minion_type_weight'] / total

    demon_weight = 1
    evil_team_weight = 1
    minion_type_weight = 1
    worlds_df['total_weight'] = (worlds_df['demon_weight']*demon_weight+worlds_df['evil_team_weight']*evil_team_weight+worlds_df['minion_type_weight']*minion_type_weight)/(demon_weight+evil_team_weight+minion_type_weight)

    pprint(worlds_df)
    
    worlds_df.sort_values(by='total_weight', ascending=False, inplace=True)
    return worlds[worlds_df.index[0]], worlds_df['total_weight'][worlds_df.index[0]].item()


players = 5
n = 5
seed = 42
x = simulate_info(n, players, seed)
for x_i,y in x:
    print(y)