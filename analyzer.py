from world.world import *
from worldCreator import *
from pprint import pprint
import pandas as pd
import numpy as np
import seaborn
import matplotlib.pyplot as plt

game = {
    'players': 5
}

investigator_info = {
    'investigator': 0,
    'first_player': 2,
    'second_player': 3,
    'minion': Role.SCARLET_WOMAN
}

washerwoman_info = {
    'washerwoman': 1,
    'first_player': 0,
    'second_player': 4,
    'townsfolk': Role.INVESTIGATOR
}
soldier_claim = {
    'player': 2,
    'character': Role.SOLDIER
}
execution = {
    'player': 2
}
night_2_death = {
    'player': 0
}
saint_claim = {
    'player': 4,
    'character': Role.SAINT
}
fortune_teller_n1_info = {
    'player': 3,
    'pings': ((0,2), False),
    'night': 1
}
fortune_teller_n2_info = {
    'player': 3,
    'pings': ((1,4), True),
    'night': 2
}

investigator_worlds = create_worlds_from_investigator_info(game, investigator_info)
washerwoman_worlds = create_worlds_from_washerwoman_info(game, washerwoman_info)
soldier_worlds = create_worlds_from_claim(game, soldier_claim)
valid_worlds, conflicting_worlds = combine_worlds([investigator_worlds, washerwoman_worlds, soldier_worlds])
execution_worlds = create_worlds_from_execution(valid_worlds, execution['player'], 2)
night_death_worlds = create_worlds_from_night_kill(execution_worlds, night_2_death['player'], 2)
saint_worlds = create_worlds_from_claim(game, saint_claim)
valid_worlds, conflicting_worlds = combine_worlds([night_death_worlds, saint_worlds])
fortune_teller_n1_worlds = create_worlds_from_fortune_teller_info(game, fortune_teller_n1_info)
fortune_teller_n2_worlds = create_worlds_from_fortune_teller_info(game, fortune_teller_n2_info)
valid_worlds, conflicting_worlds = combine_worlds([valid_worlds, fortune_teller_n1_worlds, fortune_teller_n2_worlds])

# valid_worlds, conflicting_worlds = combine_worlds([investigator_worlds, washerwoman_worlds, soldier_worlds, execution_worlds])
# valid_worlds, conflicting_worlds = combine_worlds([investigator_worlds, washerwoman_worlds, soldier_worlds, execution_worlds, night_death_worlds, saint_worlds, fortune_teller_n1_worlds, fortune_teller_n2_worlds])
# valid_worlds, conflicting_worlds = combine_worlds(investigator_worlds + washerwoman_worlds + soldier_worlds + execution_worlds + night_death_worlds + saint_worlds + fortune_teller_n1_worlds + fortune_teller_n2_worlds)
final_worlds = valid_worlds
culled_worlds = remove_duplicate_complete_worlds(valid_worlds)

def analyze():

    print(f"Original valid worlds: {len(valid_worlds)}\n\
    Culled valid worlds: {len(culled_worlds)}")

    for i, world in enumerate(culled_worlds):
        print(f"World {i+1}\n{str(world)}")

    zeros = np.zeros((game['players'],Role.__len__()))
    player_characters = pd.DataFrame(zeros, columns=[x.name for x in Role])
    for world in culled_worlds:
        for i,c in enumerate(world.phases[-1].characters):
            player_characters.loc[i,c.name] += 1/len(culled_worlds)

    # remove roles with zero probability
    player_characters = player_characters.loc[:, (player_characters != 0).any(axis=0)]

    heatmap = seaborn.heatmap(player_characters,vmin=0,vmax=1,annot=True,square=True)
    plt.show()

    evil_players = player_characters.copy()
    evil_cols = [
        Role.ANY_OTHER.name,
        Role.ANY_OTHER_EVIL.name,
        Role.ANY_OTHER_MINION.name,
        Role.NON_DEMON.name,
        Role.POISONER.name,
        Role.SPY.name,
        Role.SCARLET_WOMAN.name,
        Role.BARON.name,
        Role.IMP.name,
    ]
    evil_players["evil"] = sum(player_characters[col] for col in evil_cols if col in player_characters.columns)
    evil_players = evil_players[['evil']]

    ax = evil_players.plot.bar(ylim=(0,1))
    plt.show()

    demon_players = player_characters.copy()
    demon_cols = [
        Role.ANY_OTHER.name,
        Role.ANY_OTHER_EVIL.name,
        Role.IMP.name,
    ]
    demon_players["demon"] = sum(player_characters[col] for col in demon_cols if col in player_characters.columns)
    demon_players = demon_players[['demon']]

    ax = demon_players.plot.bar(ylim=(0,1))
    plt.show()

if __name__ == "__main__":
    analyze()