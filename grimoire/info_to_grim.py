from .gamerules import ROLE_BREAKDOWNS

from .info import *
from .grimoire import Grimoire
from .grimoire_page import GrimoirePage
from .role import Role, TOWNSFOLK, OUTSIDERS, EVIL_CHARACTERS, GOOD_CHARACTERS
from .game import Game
from .nightOrderPosition import NightOrderPosition

def get_info_page(
    grim: Grimoire, 
    night: int, 
    night_order_position: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> GrimoirePage:
    if night == 1:
        return grim.get_first_page()
    return grim.add_page(night, night_order_position)

def _create_drunk_evil_poisoned_worlds(
    game: Game, 
    player: int, 
    token: Role, 
    night:int=1, 
    night_order_position: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> list[Grimoire]:
    
    assert(token in TOWNSFOLK)
    
    worlds: list[Grimoire] = []

    world1 = Grimoire(game['players'])
    phase1 = world1.get_first_page()
    phase1.characters[player] = Role.DRUNK
    phase1.drunk_token = token
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase1.add_minion_type(Role.BARON)
    worlds.append(world1)

    world2 = Grimoire(game['players'])
    phase2 = world2.get_first_page()
    phase2.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world2)

    world3 = Grimoire(game['players'])
    first_page = world3.get_first_page()
    page = get_info_page(world3, night, night_order_position)
    first_page.characters[player] = token
    page.poisoned[player] = True
    page.add_minion_type(Role.POISONER)
    worlds.append(world3)

    return worlds


def _create_worlds_from_claim(game: Game, claim: Claim) -> list[Grimoire]:
    player = claim['player']
    character = claim['character']
    worlds: list[Grimoire] = []

    # World where the player is the Drunk
    if character in TOWNSFOLK:
        world_drunk = Grimoire(game['players'])
        phase_drunk = world_drunk.get_first_page()
        phase_drunk.characters[player] = Role.DRUNK
        phase_drunk.drunk_token = character
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase_drunk.add_minion_type(Role.BARON)
        worlds.append(world_drunk)

    # World where the player is an unspecified evil character
    world_evil = Grimoire(game['players'])
    phase_evil = world_evil.get_first_page()
    phase_evil.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world_evil)

    # World where the player is exactly the claimed character
    world_claimed = Grimoire(game['players'])
    phase_claimed = world_claimed.get_first_page()
    phase_claimed.characters[player] = character
    if character in OUTSIDERS and ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase_claimed.add_minion_type(Role.BARON)
    worlds.append(world_claimed)

    return worlds

def _create_worlds_from_investigator_info(game: Game, info: InvestigatorInfo):
    player = info['investigator']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.INVESTIGATOR)

    # disregard worlds where they saw themselves as an evil player
    if info['first_player'] != player:
        world3 = Grimoire(game['players'])
        phase3 = world3.get_first_page()
        phase3.characters[info['first_player']] = info['minion']
        phase3.characters[player] = Role.INVESTIGATOR
        phase3.add_minion_type(info['minion'])
        worlds.append(world3)

        world5 = Grimoire(game['players'])
        phase5 = world5.get_first_page()
        phase5.characters[info['first_player']] = Role.RECLUSE
        phase5.characters[player] = Role.INVESTIGATOR
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase5.add_minion_type(Role.BARON)
        worlds.append(world5)

    if info['second_player'] != player:
        world4 = Grimoire(game['players'])
        phase4 = world4.get_first_page()
        phase4.characters[info['second_player']] = info['minion']
        phase4.characters[player] = Role.INVESTIGATOR
        phase4.add_minion_type(info['minion'])
        worlds.append(world4)

        world6 = Grimoire(game['players'])
        phase6 = world6.get_first_page()
        phase6.characters[info['second_player']] = Role.RECLUSE
        phase6.characters[player] = Role.INVESTIGATOR
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase6.add_minion_type(Role.BARON)
        worlds.append(world6)

    return worlds

def _create_worlds_from_washerwoman_info(game: Game, info: WasherwomanInfo):
    player = info['washerwoman']
    num_players = game['players']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.WASHERWOMAN)

    if info['townsfolk'] == Role.WASHERWOMAN:
        world = Grimoire(num_players)
        page = world.get_first_page()
        page.characters[player] = Role.WASHERWOMAN
        worlds.append(world)

    # disregard worlds where they saw themselves as not the washerwoman
    if info['first_player'] != player:
        world3 = Grimoire(num_players)
        phase3 = world3.get_first_page()
        phase3.characters[info['first_player']] = info['townsfolk']
        phase3.characters[player] = Role.WASHERWOMAN
        worlds.append(world3)
        
        world5 = Grimoire(num_players)
        phase5 = world5.get_first_page()
        phase5.characters[info['first_player']] = Role.SPY
        phase5.characters[player] = Role.WASHERWOMAN
        phase5.add_minion_type(Role.SPY)
        worlds.append(world5)

    if info['second_player'] != player:
        world4 = Grimoire(num_players)
        phase4 = world4.get_first_page()
        phase4.characters[info['second_player']] = info['townsfolk']
        phase4.characters[player] = Role.WASHERWOMAN
        worlds.append(world4)
        
        world6 = Grimoire(num_players)
        phase6 = world6.get_first_page()
        phase6.characters[info['second_player']] = Role.SPY
        phase6.characters[player] = Role.WASHERWOMAN
        phase6.add_minion_type(Role.SPY)
        worlds.append(world6)

    return worlds

def _create_worlds_from_chef_info(game: Game, info: ChefInfo):
    player = info['chef']
    number = info['number']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.CHEF)

    world = Grimoire(game['players'])
    world.get_first_page().characters[player] = Role.CHEF
    world.get_first_page().chef_number = number
    worlds.append(world)

    return worlds

def _create_worlds_from_librarian_info(game: Game, info: LibrarianInfo) -> list[Grimoire]:
    player = info['librarian']
    first_player = info['first_player']
    second_player = info['second_player']
    token = info['token']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.LIBRARIAN)

    if token is None:
        world_no_outsiders = Grimoire(game['players'])
        world_no_outsiders.get_first_page().characters[player] = Role.LIBRARIAN
        world_no_outsiders.get_first_page().no_outsiders = True
        worlds.append(world_no_outsiders)
        return worlds

    assert first_player is not None and second_player is not None

    # disregard worlds where librarian saw themselves
    if first_player != player:
        world3 = Grimoire(game['players'])
        phase3 = world3.get_first_page()
        phase3.characters[first_player] = token
        phase3.characters[player] = Role.LIBRARIAN
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase3.add_minion_type(Role.BARON)
        worlds.append(world3)
        
        world5 = Grimoire(game['players'])
        phase5 = world5.get_first_page()
        phase5.characters[player] = Role.LIBRARIAN
        phase5.characters[first_player] = Role.SPY
        phase5.add_minion_type(Role.SPY)
        worlds.append(world5)

    if second_player != player:
        world4 = Grimoire(game['players'])
        phase4 = world4.get_first_page()
        phase4.characters[second_player] = token
        phase4.characters[player] = Role.LIBRARIAN
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase4.add_minion_type(Role.BARON)
        worlds.append(world4)
        
        world6 = Grimoire(game['players'])
        phase6 = world6.get_first_page()
        phase6.characters[player] = Role.LIBRARIAN
        phase6.characters[second_player] = Role.SPY
        phase6.add_minion_type(Role.SPY)
        worlds.append(world6)

    return worlds

def _create_worlds_from_fortune_teller_info(game: Game, info: FortuneTellerInfo):
    player = info['fortune_teller']
    pings, result = info['pings']
    a, b = pings
    night = info['night']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.FORTUNE_TELLER, night)

    if result:
        # disregard worlds where player chose themselves (other than red herring)
        if a != player:
            ## Player a is the Demon
            world4 = Grimoire(game['players'])
            phase4 = get_info_page(world4, night)
            phase4.characters[a] = Role.IMP
            world4.get_first_page().characters[player] = Role.FORTUNE_TELLER # WARNING: this is only true on TB. If characters can change (S&V), this should get changed to the info page
            worlds.append(world4)

            ## Player a is the Red Herring and is the Spy
            world6 = Grimoire(game['players'])
            phase6 = get_info_page(world6, night)
            world6.get_first_page().characters[player] = Role.FORTUNE_TELLER
            phase6.characters[a] = Role.SPY
            world6.get_first_page().add_minion_type(Role.SPY)
            phase6.red_herring[a] = True
            worlds.append(world6)

            ## Player a is the Recluse
            world8 = Grimoire(game['players'])
            phase8 = get_info_page(world8, night)
            world8.get_first_page().characters[a] = Role.RECLUSE
            world8.get_first_page().characters[player] = Role.FORTUNE_TELLER
            if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase8.characters[a] == Role.RECLUSE:
                world8.get_first_page().add_minion_type(Role.BARON)
            worlds.append(world8)

        if b != player:
            ## Player b is the Demon
            world5 = Grimoire(game['players'])
            phase5 = get_info_page(world5, night)
            phase5.characters[b] = Role.IMP
            world5.get_first_page().characters[player] = Role.FORTUNE_TELLER
            worlds.append(world5)

            ## Player b is the Red Herring and is the Spy
            world7 = Grimoire(game['players'])
            phase7 = get_info_page(world7, night)
            world7.get_first_page().characters[player] = Role.FORTUNE_TELLER
            phase7.characters[b] = Role.SPY
            world7.get_first_page().add_minion_type(Role.SPY)
            phase7.red_herring[b] = True
            worlds.append(world7)

            ## Player b is the Recluse
            world9 = Grimoire(game['players'])
            phase9 = get_info_page(world9, night)
            world9.get_first_page().characters[b] = Role.RECLUSE
            world9.get_first_page().characters[player] = Role.FORTUNE_TELLER
            if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase9.characters[b] == Role.RECLUSE:
                world9.get_first_page().add_minion_type(Role.BARON)
            worlds.append(world9)

        ## Player a is the Red Herring and is good
        world6 = Grimoire(game['players'])
        phase6 = get_info_page(world6, night)
        world6.get_first_page().characters[a] = Role.ANY_OTHER_GOOD
        world6.get_first_page().characters[player] = Role.FORTUNE_TELLER
        phase6.red_herring[a] = True
        worlds.append(world6)

        ## Player b is the Red Herring and is good
        world7 = Grimoire(game['players'])
        phase7 = get_info_page(world7, night)
        world7.get_first_page().characters[b] = Role.ANY_OTHER_GOOD
        world7.get_first_page().characters[player] = Role.FORTUNE_TELLER
        phase7.red_herring[b] = True
        worlds.append(world7)

    else:
        ## Player a is not the Imp and Player b is not the Imp
        world10 = Grimoire(game['players'])
        world10.get_first_page().characters[a] = Role.NON_DEMON
        world10.get_first_page().characters[b] = Role.NON_DEMON
        world10.get_first_page().characters[player] = Role.FORTUNE_TELLER
        worlds.append(world10)

    return worlds

def _create_worlds_from_empath_info(game: Game, info: EmpathInfo):
    player = info['empath']
    number = info['number']
    night = info['night']
    left = info['left_neighbour']
    right = info['right_neighbour']
    players = game['players']
    if number < 0 or number > 2:
        raise ValueError('An empath was given an invalid number')

    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.EMPATH, night)

    if number == 0:
        # Both neighbours are good
        world1 = Grimoire(players)
        world1.get_first_page().characters[player] = Role.EMPATH
        world1.get_first_page().characters[left] = Role.ANY_OTHER_GOOD
        world1.get_first_page().characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world1)

        # Left neighbour is the Spy (registering as good)
        world2 = Grimoire(players)
        phase2 = get_info_page(world2, night)
        world2.get_first_page().characters[player] = Role.EMPATH
        phase2.characters[left] = Role.SPY
        world2.get_first_page().add_minion_type(Role.SPY)
        world2.get_first_page().characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world2)

        # Right neighbour is the Spy (registering as good)
        world3 = Grimoire(players)
        phase3 = get_info_page(world3, night)
        world3.get_first_page().characters[player] = Role.EMPATH
        world3.get_first_page().characters[left] = Role.ANY_OTHER_GOOD
        phase3.characters[right] = Role.SPY
        world3.get_first_page().add_minion_type(Role.SPY)
        worlds.append(world3)

    elif number == 1:
        # Left neighbour is any other evil and right neighbour is good
        world4 = Grimoire(players)
        phase4 = get_info_page(world4, night)
        world4.get_first_page().characters[player] = Role.EMPATH
        phase4.characters[left] = Role.ANY_OTHER_EVIL
        world4.get_first_page().characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world4)

        # Right neighbour is any other evil and left neighbour is good
        world5 = Grimoire(players)
        phase5 = get_info_page(world5, night)
        world5.get_first_page().characters[player] = Role.EMPATH
        world5.get_first_page().characters[left] = Role.ANY_OTHER_GOOD
        phase5.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world5)

        # Left neighbour is any other evil and right neighbour is the Spy
        world6 = Grimoire(players)
        phase6 = get_info_page(world6, night)
        world6.get_first_page().characters[player] = Role.EMPATH
        phase6.characters[left] = Role.ANY_OTHER_EVIL
        phase6.characters[right] = Role.SPY
        world6.get_first_page().add_minion_type(Role.SPY)
        worlds.append(world6)

        # Right neighbour is any other evil and left neighbour is the Spy
        world7 = Grimoire(players)
        phase7 = get_info_page(world7, night)
        world7.get_first_page().characters[player] = Role.EMPATH
        phase7.characters[left] = Role.SPY
        phase7.characters[right] = Role.ANY_OTHER_EVIL
        world7.get_first_page().add_minion_type(Role.SPY)
        worlds.append(world7)

        # Left neighbour is the Recluse and right neighbour is good
        world8 = Grimoire(players)
        world8.get_first_page().characters[player] = Role.EMPATH
        world8.get_first_page().characters[left] = Role.RECLUSE
        world8.get_first_page().characters[right] = Role.ANY_OTHER_GOOD
        if ROLE_BREAKDOWNS[players]['outsiders'] == 0:
            world8.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world8)

        # Right neighbour is the Recluse and left neighbour is good
        world9 = Grimoire(players)
        world9.get_first_page().characters[player] = Role.EMPATH
        world9.get_first_page().characters[left] = Role.ANY_OTHER_GOOD
        world9.get_first_page().characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[players]['outsiders'] == 0:
            world9.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world9)

        # Left neighbour is the Recluse and right neighbour is the Spy
        if ROLE_BREAKDOWNS[players]['minions'] >= 2:
            world10 = Grimoire(players)
            phase10 = get_info_page(world10, night)
            world10.get_first_page().characters[player] = Role.EMPATH
            world10.get_first_page().characters[left] = Role.RECLUSE
            phase10.characters[right] = Role.SPY
            world10.get_first_page().add_minion_type(Role.SPY)
            if ROLE_BREAKDOWNS[players]['outsiders'] == 0:
                world10.get_first_page().add_minion_type(Role.BARON)
            worlds.append(world10)

            # Right neighbour is the Recluse and left neighbour is the Spy
            world11 = Grimoire(players)
            phase11 = get_info_page(world11, night)
            world11.get_first_page().characters[player] = Role.EMPATH
            phase11.characters[left] = Role.SPY
            world11.get_first_page().add_minion_type(Role.SPY)
            world11.get_first_page().characters[right] = Role.RECLUSE
            if ROLE_BREAKDOWNS[players]['outsiders'] == 0:
                world11.get_first_page().add_minion_type(Role.BARON)
            worlds.append(world11)

    else:  # number == 2
        # Both neighbours are evil
        world12 = Grimoire(players)
        phase12 = get_info_page(world12, night)
        world12.get_first_page().characters[player] = Role.EMPATH
        phase12.characters[left] = Role.ANY_OTHER_EVIL
        phase12.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world12)

        # Left neighbour is evil and right is the Recluse
        world13 = Grimoire(players)
        phase13 = get_info_page(world13, night)
        world13.get_first_page().characters[player] = Role.EMPATH
        phase13.characters[left] = Role.ANY_OTHER_EVIL
        world13.get_first_page().characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[players]['outsiders'] == 0:
            world13.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world13)

        # Right neighbour is evil and left is the Recluse
        world14 = Grimoire(players)
        phase14 = get_info_page(world14, night)
        world14.get_first_page().characters[player] = Role.EMPATH
        world14.get_first_page().characters[left] = Role.RECLUSE
        phase14.characters[right] = Role.ANY_OTHER_EVIL
        if ROLE_BREAKDOWNS[players]['outsiders'] == 0:
            world14.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world14)

    return worlds

def _create_worlds_from_undertaker_info(game: Game, info: UndertakerInfo):
    player = info['undertaker']
    body = info['body']
    token = info['token']
    night = info['night']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.UNDERTAKER, night=night)

    # World where the undertaker sees the actual token (body is that token)
    world1 = Grimoire(game['players'])
    phase1 = get_info_page(world1, night)
    world1.get_first_page().characters[player] = Role.UNDERTAKER
    phase1.characters[body] = token
    worlds.append(world1)

    # If the token is an evil character, the body could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = Grimoire(game['players'])
        world2.get_first_page().characters[player] = Role.UNDERTAKER
        world2.get_first_page().characters[body] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            world2.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the body could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = Grimoire(game['players'])
        phase3 = get_info_page(world3, night)
        world3.get_first_page().characters[player] = Role.UNDERTAKER
        phase3.characters[body] = Role.SPY
        world3.get_first_page().add_minion_type(Role.SPY)
        worlds.append(world3)

    return worlds

def _create_worlds_from_ravenkeeper_info(game: Game, info: RavenkeeperInfo):
    player = info['ravenkeeper']
    chosen = info['chosen']
    token = info['token']
    night = info['night']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.RAVENKEEPER, night=night)

    # World where the Ravenkeeper sees the actual token (chosen player is that token)
    world1 = Grimoire(game['players'])
    phase1 = get_info_page(world1, night)
    phase1.characters[chosen] = token
    world1.get_first_page().characters[player] = Role.RAVENKEEPER
    worlds.append(world1)

    # If the token is an evil character, the chosen player could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS and chosen != player:
        world2 = Grimoire(game['players'])
        world2.get_first_page().characters[chosen] = Role.RECLUSE
        world2.get_first_page().characters[player] = Role.RAVENKEEPER
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            world2.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the chosen player could be the Spy (registering as good)
    if token in GOOD_CHARACTERS and chosen != player:
        world3 = Grimoire(game['players'])
        phase3 = get_info_page(world3, night)
        world3.get_first_page().characters[player] = Role.RAVENKEEPER
        phase3.characters[chosen] = Role.SPY
        world3.get_first_page().add_minion_type(Role.SPY)
        worlds.append(world3)

    return worlds

def _create_worlds_from_virgin_nominated(game: Game, info: VirginInfo):
    virgin:int = info['virgin']
    nominator:int = info['nominator']
    executed:bool = info['executed']
    night = info['night']

    worlds: list[Grimoire] = []

    if executed:
        world1 = Grimoire(game['players'])
        world1.get_first_page().characters[nominator] = Role.ANY_OTHER_TOWNSFOLK
        world1.get_first_page().characters[virgin] = Role.VIRGIN
        worlds.append(world1)
        
        if nominator != virgin:
            world2 = Grimoire(game['players'])
            phase2 = get_info_page(world2, night)
            world2.get_first_page().characters[virgin] = Role.VIRGIN
            phase2.characters[nominator] = Role.SPY
            world2.get_first_page().add_minion_type(Role.SPY)
            worlds.append(world2)

    else:
        worlds += _create_drunk_evil_poisoned_worlds(game, virgin, Role.VIRGIN, night)

        if virgin == nominator:
            return worlds

        world3 = Grimoire(game['players'])
        phase3 = get_info_page(world3, night)
        world3.get_first_page().characters[virgin] = Role.VIRGIN
        phase3.characters[nominator] = Role.ANY_OTHER_EVIL
        worlds.append(world3)

        world4 = Grimoire(game['players'])
        phase4 = get_info_page(world4, night)
        world4.get_first_page().characters[virgin] = Role.VIRGIN
        phase4.characters[nominator] = Role.ANY_OTHER_OUTSIDER
        worlds.append(world4)

    return worlds

def _create_worlds_from_slayer_info(game: Game, info: SlayerInfo) -> list[Grimoire]:
    slayer = info['slayer']
    target = info['target']
    successful = info['successful']
    night = info['night']

    worlds: list[Grimoire] = []

    if successful:
        # World where the slayer killed the Imp
        world1 = Grimoire(game['players'])
        phase1 = get_info_page(world1, night)
        world1.get_first_page().characters[slayer] = Role.SLAYER
        phase1.characters[target] = Role.IMP
        worlds.append(world1)

        # World where the slayer killed the Recluse (registering as the demon)
        world2 = Grimoire(game['players'])
        world2.get_first_page().characters[slayer] = Role.SLAYER
        world2.get_first_page().characters[target] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            world2.get_first_page().add_minion_type(Role.BARON)
        worlds.append(world2)

    else:        
        worlds = _create_drunk_evil_poisoned_worlds(game, slayer, Role.SLAYER, night)

        if target == slayer:
            return worlds

        # World where the slayer's shot hit a non-demon
        world3 = Grimoire(game['players'])
        world3.get_first_page().characters[target] = Role.NON_DEMON
        world3.get_first_page().characters[slayer] = Role.SLAYER
        worlds.append(world3)

    return worlds

def info_to_grimoires(game: Game, info: Info):
    if info["kind"] == "washerwoman":
        return _create_worlds_from_washerwoman_info(game, info)
    elif info["kind"]  == "librarian":
        return _create_worlds_from_librarian_info(game, info)
    elif info["kind"]  == "investigator":
        return _create_worlds_from_investigator_info(game, info)
    elif info["kind"]  == "chef":
        return _create_worlds_from_chef_info(game, info)
    elif info["kind"]  == "fortune teller":
        return _create_worlds_from_fortune_teller_info(game, info)
    elif info["kind"]  == "empath":
        return _create_worlds_from_empath_info(game, info)
    elif info["kind"]  == "virgin":
        return _create_worlds_from_virgin_nominated(game, info)
    elif info["kind"]  == "slayer":
        return _create_worlds_from_slayer_info(game, info)
    elif info["kind"]  == "undertaker":
        return _create_worlds_from_undertaker_info(game, info)
    elif info["kind"]  == "ravenkeeper":
        return _create_worlds_from_ravenkeeper_info(game, info)
    elif info["kind"]  == "claim":
        return _create_worlds_from_claim(game, info)
    else:
        raise NotImplementedError(f"{info["kind"]} info has not been implemented.")