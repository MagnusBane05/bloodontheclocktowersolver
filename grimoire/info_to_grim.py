from .info import *
from .grimoire import Grimoire
from .role import Role, OUTSIDERS, ROLE_BREAKDOWNS, EVIL_CHARACTERS, GOOD_CHARACTERS
from .game import Game
from .nightOrderPosition import NightOrderPosition

def _create_drunk_evil_poisoned_worlds(
        game: Game, 
        player: int, 
        token: Role, 
        night:int=1, 
        night_order_position: NightOrderPosition = NightOrderPosition.AFTER_IMP
        ) -> list[Grimoire]:
    
    worlds: list[Grimoire] = []

    world1 = Grimoire(game['players'])
    if night == 1:
        phase1 = world1.pages[0]
    else:
        phase1 = world1.add_page(night, night_order_position)
    phase1.characters[player] = Role.DRUNK
    phase1.drunk_token = token
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
        phase1.add_minion_type(Role.BARON)
    worlds.append(world1)

    world2 = Grimoire(game['players'])
    if night == 1:
        phase2 = world2.pages[0]
    else:
        phase2 = world2.add_page(night, night_order_position)
    phase2.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world2)

    world3 = Grimoire(game['players'])
    if night == 1:
        phase3 = world3.pages[0]
    else:
        phase3 = world3.add_page(night, night_order_position)
    phase3.characters[player] = token
    phase3.poisoned[player] = True
    phase3.add_minion_type(Role.POISONER)
    worlds.append(world3)

    return worlds


def _create_worlds_from_claim(game: Game, claim: Claim) -> list[Grimoire]:
    player = claim['player']
    character = claim['character']
    worlds: list[Grimoire] = []

    # World where the player is the Drunk
    if character not in OUTSIDERS:
        world_drunk = Grimoire(game['players'])
        phase_drunk = world_drunk.pages[0]
        phase_drunk.characters[player] = Role.DRUNK
        phase_drunk.drunk_token = character
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase_drunk.add_minion_type(Role.BARON)
        worlds.append(world_drunk)

    # World where the player is an unspecified evil character
    world_evil = Grimoire(game['players'])
    phase_evil = world_evil.pages[0]
    phase_evil.characters[player] = Role.ANY_OTHER_EVIL
    worlds.append(world_evil)

    # World where the player is exactly the claimed character
    world_claimed = Grimoire(game['players'])
    phase_claimed = world_claimed.pages[0]
    phase_claimed.characters[player] = character
    if character in OUTSIDERS:
        phase_claimed.add_minion_type(Role.BARON)
    worlds.append(world_claimed)

    return worlds

def _create_worlds_from_investigator_info(game: Game, info: InvestigatorInfo):
    player = info['investigator']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.INVESTIGATOR)

    world3 = Grimoire(game['players'])
    phase3 = world3.pages[0]
    phase3.characters[info['first_player']] = info['minion']
    phase3.characters[player] = Role.INVESTIGATOR
    phase3.add_minion_type(info['minion'])
    worlds.append(world3)

    world4 = Grimoire(game['players'])
    phase4 = world4.pages[0]
    phase4.characters[info['second_player']] = info['minion']
    phase4.characters[player] = Role.INVESTIGATOR
    phase4.add_minion_type(info['minion'])
    worlds.append(world4)

    world5 = Grimoire(game['players'])
    phase5 = world5.pages[0]
    phase5.characters[info['first_player']] = Role.RECLUSE
    phase5.characters[player] = Role.INVESTIGATOR
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase5.characters[info['first_player']] == Role.RECLUSE: # have to add an extra check in the case where the investigator saw themselves!
        phase5.add_minion_type(Role.BARON)
    worlds.append(world5)

    world6 = Grimoire(game['players'])
    phase6 = world6.pages[0]
    phase6.characters[info['second_player']] = Role.RECLUSE
    phase6.characters[player] = Role.INVESTIGATOR
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase6.characters[info['second_player']] == Role.RECLUSE:
        phase6.add_minion_type(Role.BARON)
    worlds.append(world6)

    return worlds

def _create_worlds_from_washerwoman_info(game: Game, info: WasherwomanInfo):
    player = info['washerwoman']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.WASHERWOMAN)

    world3 = Grimoire(game['players'])
    phase3 = world3.pages[0]
    phase3.characters[info['first_player']] = info['townsfolk']
    phase3.characters[player] = Role.WASHERWOMAN
    worlds.append(world3)

    world4 = Grimoire(game['players'])
    phase4 = world4.pages[0]
    phase4.characters[info['second_player']] = info['townsfolk']
    phase4.characters[player] = Role.WASHERWOMAN
    worlds.append(world4)

    world5 = Grimoire(game['players'])
    phase5 = world5.pages[0]
    phase5.characters[info['first_player']] = Role.SPY
    phase5.characters[player] = Role.WASHERWOMAN
    if phase5.characters[info['first_player']] == Role.SPY: # have to add an extra check in the case where the washerwoman saw themselves!
        phase5.add_minion_type(Role.SPY)
    worlds.append(world5)

    world6 = Grimoire(game['players'])
    phase6 = world6.pages[0]
    phase6.characters[info['second_player']] = Role.SPY
    phase6.characters[player] = Role.WASHERWOMAN
    if phase6.characters[info['second_player']] == Role.SPY:
        phase6.add_minion_type(Role.SPY)
    worlds.append(world6)

    return worlds

def _create_worlds_from_chef_info(game: Game, info: ChefInfo):
    player = info['chef']
    number = info['number']
    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.CHEF)

    world = Grimoire(game['players'])
    world.pages[0].characters[player] = Role.CHEF
    world.pages[0].chef_number = number
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
        world_no_outsiders.pages[0].characters[player] = Role.LIBRARIAN
        world_no_outsiders.pages[0].no_outsiders = True
        worlds.append(world_no_outsiders)
        return worlds

    assert first_player is not None and second_player is not None

    world3 = Grimoire(game['players'])
    phase3 = world3.pages[0]
    phase3.characters[first_player] = token
    phase3.characters[player] = Role.LIBRARIAN
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase3.characters[first_player] == token: # have to add an extra check in the case where the librarian saw themselves!
        phase3.add_minion_type(Role.BARON)
    worlds.append(world3)

    world4 = Grimoire(game['players'])
    phase4 = world4.pages[0]
    phase4.characters[second_player] = token
    phase4.characters[player] = Role.LIBRARIAN
    if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase4.characters[second_player] == token: # have to add an extra check in the case where the librarian saw themselves!
        phase4.add_minion_type(Role.BARON)
    worlds.append(world4)

    world5 = Grimoire(game['players'])
    phase5 = world5.pages[0]
    phase5.characters[player] = Role.LIBRARIAN
    if player != first_player:
        phase5.characters[first_player] = Role.SPY
        phase5.add_minion_type(Role.SPY)
    worlds.append(world5)

    world6 = Grimoire(game['players'])
    phase6 = world6.pages[0]
    phase6.characters[player] = Role.LIBRARIAN
    if player != second_player:
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
        ## Player a is the Demon
        world4 = Grimoire(game['players'])
        if night == 1:
            phase4 = world4.pages[0]
        else:
            phase4 = world4.add_page(night, NightOrderPosition.AFTER_IMP)
        phase4.characters[a] = Role.IMP
        phase4.characters[player] = Role.FORTUNE_TELLER
        worlds.append(world4)

        ## Player b is the Demon
        world5 = Grimoire(game['players'])
        if night == 1:
            phase5 = world5.pages[0]
        else:
            phase5 = world5.add_page(night, NightOrderPosition.AFTER_IMP)
        phase5.characters[b] = Role.IMP
        phase5.characters[player] = Role.FORTUNE_TELLER
        worlds.append(world5)

        ## Player a is the Red Herring and is good
        world6 = Grimoire(game['players'])
        if night == 1:
            phase6 = world6.pages[0]
        else:
            phase6 = world6.add_page(night, NightOrderPosition.AFTER_IMP)
        phase6.characters[a] = Role.ANY_OTHER_GOOD
        phase6.characters[player] = Role.FORTUNE_TELLER
        phase6.red_herring[a] = True
        worlds.append(world6)

        ## Player b is the Red Herring and is good
        world7 = Grimoire(game['players'])
        if night == 1:
            phase7 = world7.pages[0]
        else:
            phase7 = world7.add_page(night, NightOrderPosition.AFTER_IMP)
        phase7.characters[b] = Role.ANY_OTHER_GOOD
        phase7.characters[player] = Role.FORTUNE_TELLER
        phase7.red_herring[b] = True
        worlds.append(world7)

        ## Player a is the Red Herring and is the Spy
        world6 = Grimoire(game['players'])
        if night == 1:
            phase6 = world6.pages[0]
        else:
            phase6 = world6.add_page(night, NightOrderPosition.AFTER_IMP)
        phase6.characters[player] = Role.FORTUNE_TELLER
        if player != a:
            phase6.characters[a] = Role.SPY
            phase6.add_minion_type(Role.SPY)
        phase6.red_herring[a] = True
        worlds.append(world6)

        ## Player b is the Red Herring and is the Spy
        world7 = Grimoire(game['players'])
        if night == 1:
            phase7 = world7.pages[0]
        else:
            phase7 = world7.add_page(night, NightOrderPosition.AFTER_IMP)
        phase7.characters[player] = Role.FORTUNE_TELLER
        if player != b:
            phase7.characters[b] = Role.SPY
            phase7.add_minion_type(Role.SPY)
        phase7.red_herring[b] = True
        worlds.append(world7)

        ## Player a is the Recluse
        world8 = Grimoire(game['players'])
        if night == 1:
            phase8 = world8.pages[0]
        else:
            phase8 = world8.add_page(night, NightOrderPosition.AFTER_IMP)
        phase8.characters[a] = Role.RECLUSE
        phase8.characters[player] = Role.FORTUNE_TELLER
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase8.characters[a] == Role.RECLUSE:
            phase8.add_minion_type(Role.BARON)
        worlds.append(world8)

        ## Player b is the Recluse
        world9 = Grimoire(game['players'])
        if night == 1:
            phase9 = world9.pages[0]
        else:
            phase9 = world9.add_page(night, NightOrderPosition.AFTER_IMP)
        phase9.characters[b] = Role.RECLUSE
        phase9.characters[player] = Role.FORTUNE_TELLER
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase9.characters[b] == Role.RECLUSE:
            phase9.add_minion_type(Role.BARON)
        worlds.append(world9)

    else:
        ## Player a is not the Imp and Player b is not the Imp
        world10 = Grimoire(game['players'])
        if night == 1:
            phase10 = world10.pages[0]
        else:
            phase10 = world10.add_page(night, NightOrderPosition.AFTER_IMP)
        phase10.characters[a] = Role.NON_DEMON
        phase10.characters[b] = Role.NON_DEMON
        phase10.characters[player] = Role.FORTUNE_TELLER
        worlds.append(world10)

    return worlds

def _create_worlds_from_empath_info(game: Game, info: EmpathInfo):
    player = info['empath']
    number = info['number']
    night = info['night']
    left = info['left_neighbour']
    right = info['right_neighbour']
    if number < 0 or number > 2:
        raise ValueError('An empath was given an invalid number')

    worlds = _create_drunk_evil_poisoned_worlds(game, player, Role.EMPATH, night)

    if number == 0:
        # Both neighbours are good
        world1 = Grimoire(game['players'])
        if night == 1:
            phase1 = world1.pages[0]
        else:
            phase1 = world1.add_page(night, NightOrderPosition.AFTER_IMP)
        phase1.characters[player] = Role.EMPATH
        phase1.characters[left] = Role.ANY_OTHER_GOOD
        phase1.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world1)

        # Left neighbour is the Spy (registering as good)
        world2 = Grimoire(game['players'])
        if night == 1:
            phase2 = world2.pages[0]
        else:
            phase2 = world2.add_page(night, NightOrderPosition.AFTER_IMP)
        phase2.characters[player] = Role.EMPATH
        phase2.characters[left] = Role.SPY
        phase2.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world2)

        # Right neighbour is the Spy (registering as good)
        world3 = Grimoire(game['players'])
        if night == 1:
            phase3 = world3.pages[0]
        else:
            phase3 = world3.add_page(night, NightOrderPosition.AFTER_IMP)
        phase3.characters[player] = Role.EMPATH
        phase3.characters[left] = Role.ANY_OTHER_GOOD
        phase3.characters[right] = Role.SPY
        worlds.append(world3)

    elif number == 1:
        # Left neighbour is any other evil and right neighbour is good
        world4 = Grimoire(game['players'])
        if night == 1:
            phase4 = world4.pages[0]
        else:
            phase4 = world4.add_page(night, NightOrderPosition.AFTER_IMP)
        phase4.characters[player] = Role.EMPATH
        phase4.characters[left] = Role.ANY_OTHER_EVIL
        phase4.characters[right] = Role.ANY_OTHER_GOOD
        worlds.append(world4)

        # Right neighbour is any other evil and left neighbour is good
        world5 = Grimoire(game['players'])
        if night == 1:
            phase5 = world5.pages[0]
        else:
            phase5 = world5.add_page(night, NightOrderPosition.AFTER_IMP)
        phase5.characters[player] = Role.EMPATH
        phase5.characters[left] = Role.ANY_OTHER_GOOD
        phase5.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world5)

        # Left neighbour is any other evil and right neighbour is the Spy
        world6 = Grimoire(game['players'])
        if night == 1:
            phase6 = world6.pages[0]
        else:
            phase6 = world6.add_page(night, NightOrderPosition.AFTER_IMP)
        phase6.characters[player] = Role.EMPATH
        phase6.characters[left] = Role.ANY_OTHER_EVIL
        phase6.characters[right] = Role.SPY
        worlds.append(world6)

        # Right neighbour is any other evil and left neighbour is the Spy
        world7 = Grimoire(game['players'])
        if night == 1:
            phase7 = world7.pages[0]
        else:
            phase7 = world7.add_page(night, NightOrderPosition.AFTER_IMP)
        phase7.characters[player] = Role.EMPATH
        phase7.characters[left] = Role.SPY
        phase7.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world7)

        # Left neighbour is the Recluse and right neighbour is good
        world8 = Grimoire(game['players'])
        if night == 1:
            phase8 = world8.pages[0]
        else:
            phase8 = world8.add_page(night, NightOrderPosition.AFTER_IMP)
        phase8.characters[player] = Role.EMPATH
        phase8.characters[left] = Role.RECLUSE
        phase8.characters[right] = Role.ANY_OTHER_GOOD
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase8.add_minion_type(Role.BARON)
        worlds.append(world8)

        # Right neighbour is the Recluse and left neighbour is good
        world9 = Grimoire(game['players'])
        if night == 1:
            phase9 = world9.pages[0]
        else:
            phase9 = world9.add_page(night, NightOrderPosition.AFTER_IMP)
        phase9.characters[player] = Role.EMPATH
        phase9.characters[left] = Role.ANY_OTHER_GOOD
        phase9.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase9.add_minion_type(Role.BARON)
        worlds.append(world9)

        # Left neighbour is the Recluse and right neighbour is the Spy
        world10 = Grimoire(game['players'])
        if night == 1:
            phase10 = world10.pages[0]
        else:
            phase10 = world10.add_page(night, NightOrderPosition.AFTER_IMP)
        phase10.characters[player] = Role.EMPATH
        phase10.characters[left] = Role.RECLUSE
        phase10.characters[right] = Role.SPY
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase10.add_minion_type(Role.BARON)
        worlds.append(world10)

        # Right neighbour is the Recluse and left neighbour is the Spy
        world11 = Grimoire(game['players'])
        if night == 1:
            phase11 = world11.pages[0]
        else:
            phase11 = world11.add_page(night, NightOrderPosition.AFTER_IMP)
        phase11.characters[player] = Role.EMPATH
        phase11.characters[left] = Role.SPY
        phase11.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase11.add_minion_type(Role.BARON)
        worlds.append(world11)

    else:  # number == 2
        # Both neighbours are evil
        world12 = Grimoire(game['players'])
        if night == 1:
            phase12 = world12.pages[0]
        else:
            phase12 = world12.add_page(night, NightOrderPosition.AFTER_IMP)
        phase12.characters[player] = Role.EMPATH
        phase12.characters[left] = Role.ANY_OTHER_EVIL
        phase12.characters[right] = Role.ANY_OTHER_EVIL
        worlds.append(world12)

        # Left neighbour is evil and right is the Recluse
        world13 = Grimoire(game['players'])
        if night == 1:
            phase13 = world13.pages[0]
        else:
            phase13 = world13.add_page(night, NightOrderPosition.AFTER_IMP)
        phase13.characters[player] = Role.EMPATH
        phase13.characters[left] = Role.ANY_OTHER_EVIL
        phase13.characters[right] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase13.add_minion_type(Role.BARON)
        worlds.append(world13)

        # Right neighbour is evil and left is the Recluse
        world14 = Grimoire(game['players'])
        if night == 1:
            phase14 = world14.pages[0]
        else:
            phase14 = world14.add_page(night, NightOrderPosition.AFTER_IMP)
        phase14.characters[player] = Role.EMPATH
        phase14.characters[left] = Role.RECLUSE
        phase14.characters[right] = Role.ANY_OTHER_EVIL
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase14.add_minion_type(Role.BARON)
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
    if night == 1:
        phase1 = world1.pages[0]
    else:
        phase1 = world1.add_page(night, NightOrderPosition.AFTER_IMP)
    phase1.characters[player] = Role.UNDERTAKER
    phase1.characters[body] = token
    worlds.append(world1)

    # If the token is an evil character, the body could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = Grimoire(game['players'])
        if night == 1:
            phase2 = world2.pages[0]
        else:
            phase2 = world2.add_page(night, NightOrderPosition.AFTER_IMP)
        phase2.characters[player] = Role.UNDERTAKER
        phase2.characters[body] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the body could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = Grimoire(game['players'])
        if night == 1:
            phase3 = world3.pages[0]
        else:
            phase3 = world3.add_page(night, NightOrderPosition.AFTER_IMP)
        phase3.characters[player] = Role.UNDERTAKER
        phase3.characters[body] = Role.SPY
        phase3.add_minion_type(Role.SPY)
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
    if night == 1:
        phase1 = world1.pages[0]
    else:
        phase1 = world1.add_page(night, NightOrderPosition.AFTER_IMP)
    phase1.characters[chosen] = token
    phase1.characters[player] = Role.RAVENKEEPER
    worlds.append(world1)

    # If the token is an evil character, the chosen player could be the Recluse (registering as evil)
    if token in EVIL_CHARACTERS:
        world2 = Grimoire(game['players'])
        if night == 1:
            phase2 = world2.pages[0]
        else:
            phase2 = world2.add_page(night, NightOrderPosition.AFTER_IMP)
        phase2.characters[chosen] = Role.RECLUSE
        phase2.characters[player] = Role.RAVENKEEPER
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0 and phase2.characters[chosen] == Role.RECLUSE:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    # If the token is a good character, the chosen player could be the Spy (registering as good)
    if token in GOOD_CHARACTERS:
        world3 = Grimoire(game['players'])
        if night == 1:
            phase3 = world3.pages[0]
        else:
            phase3 = world3.add_page(night, NightOrderPosition.AFTER_IMP)
        phase3.characters[player] = Role.RAVENKEEPER
        if player != chosen:
            phase3.characters[chosen] = Role.SPY
            phase3.add_minion_type(Role.SPY)
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
        phase1 = world1.add_page(night, NightOrderPosition.AFTER_EXECUTION)
        phase1.characters[nominator] = Role.ANY_OTHER_TOWNSFOLK
        phase1.characters[virgin] = Role.VIRGIN
        worlds.append(world1)
        
        world2 = Grimoire(game['players'])
        phase2 = world2.add_page(night, NightOrderPosition.AFTER_EXECUTION)
        phase2.characters[virgin] = Role.VIRGIN
        if virgin != nominator:
            phase2.characters[nominator] = Role.SPY
            phase2.add_minion_type(Role.SPY)
        worlds.append(world2)

    else:
        worlds += _create_drunk_evil_poisoned_worlds(game, virgin, Role.VIRGIN, night)

        if virgin == nominator:
            return worlds

        world3 = Grimoire(game['players'])
        if night == 1:
            phase3 = world3.pages[0]
        else:
            phase3 = world3.add_page(night, NightOrderPosition.AFTER_IMP)
        phase3.characters[virgin] = Role.VIRGIN
        phase3.characters[nominator] = Role.ANY_OTHER_EVIL
        worlds.append(world3)

        world4 = Grimoire(game['players'])
        if night == 1:
            phase4 = world4.pages[0]
        else:
            phase4 = world4.add_page(night, NightOrderPosition.AFTER_IMP)
        phase4.characters[virgin] = Role.VIRGIN
        phase4.characters[nominator] = Role.ANY_OTHER_OUTSIDER
        worlds.append(world4)

    return worlds

def _create_worlds_from_slayer_info(game: Game, info: SlayerInfo):
    slayer = info['slayer']
    target = info['target']
    successful = info['successful']
    night = info['night']

    worlds = _create_drunk_evil_poisoned_worlds(game, slayer, Role.SLAYER, night)

    if successful:
        # World where the slayer killed the Imp
        world1 = Grimoire(game['players'])
        if night == 1:
            phase1 = world1.pages[0]
        else:
            phase1 = world1.add_page(night, NightOrderPosition.AFTER_IMP)
        phase1.characters[slayer] = Role.SLAYER
        phase1.characters[target] = Role.IMP
        worlds.append(world1)

        # World where the slayer killed the Recluse (registering as evil)
        world2 = Grimoire(game['players'])
        if night == 1:
            phase2 = world2.pages[0]
        else:
            phase2 = world2.add_page(night, NightOrderPosition.AFTER_IMP)
        phase2.characters[slayer] = Role.SLAYER
        phase2.characters[target] = Role.RECLUSE
        if ROLE_BREAKDOWNS[game['players']]['outsiders'] == 0:
            phase2.add_minion_type(Role.BARON)
        worlds.append(world2)

    else:
        # World where the slayer's shot hit a non-demon
        world3 = Grimoire(game['players'])
        if night == 1:
            phase3 = world3.pages[0]
        else:
            phase3 = world3.add_page(night, NightOrderPosition.AFTER_IMP)
        phase3.characters[target] = Role.NON_DEMON
        phase3.characters[slayer] = Role.SLAYER
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
    

# def create_worlds_from_info(game: Game, info_list: list[Info], death_info: DeathInfo, true_world: Grimoire) -> tuple[list[Grimoire], list[tuple[Grimoire, Grimoire]]]:
#     def true_world_in_worlds(true_world: Grimoire, worlds: list[Grimoire]):
#         for world in worlds:
#             if true_world == world:
#                 return True
#         return False
    
#     worlds_list: list[list[Grimoire]] = []
#     for info in info_list:
#         if info["kind"] == "washerwoman":
#             worlds_list.append(create_worlds_from_washerwoman_info(game, info))
#         elif info["kind"]  == "librarian":
#             worlds_list.append(create_worlds_from_librarian_info(game, info))
#         elif info["kind"]  == "investigator":
#             worlds_list.append(create_worlds_from_investigator_info(game, info))
#         elif info["kind"]  == "chef":
#             worlds_list.append(create_worlds_from_chef_info(game, info))
#         elif info["kind"]  == "fortune teller" and info["night"] == 1:
#             worlds_list.append(create_worlds_from_fortune_teller_info(game, info))
#         elif info["kind"]  == "empath" and info["night"] == 1:
#             worlds_list.append(create_worlds_from_empath_info(game, info))
#         elif info["kind"]  == "virgin":
#             worlds_list.append(create_worlds_from_virgin_nominated(game, info))
#         elif info["kind"]  == "slayer":
#             worlds_list.append(create_worlds_from_slayer_info(game, info))
#         elif info["kind"]  == "claim":
#             worlds_list.append(create_worlds_from_claim(game, info))
#         if not true_world_in_worlds(true_world, [x for xs in worlds_list for x in xs]):
#             pass
#     combined_worlds, conflicting_worlds = combine_worlds(worlds_list)
#     if death_info['slayer_shot'] is not None:
#         target = death_info['slayer_shot'][0]
#         night = death_info['slayer_shot'][1]
#         combined_worlds = create_worlds_from_slayer_kill(combined_worlds, target, night)
#         if not true_world_in_worlds(true_world, combined_worlds):
#             pass        
#     if death_info['executed'] is not None:
#         executed = death_info['executed'][0]
#         night = death_info['executed'][1]
#         combined_worlds = create_worlds_from_execution(combined_worlds, executed, night)
#         if not true_world_in_worlds(true_world, combined_worlds):
#             pass     
#     if death_info['killed_by_demon'] is not None:
#         target = death_info['killed_by_demon'][0]
#         night = death_info['killed_by_demon'][1]
#         combined_worlds = create_worlds_from_night_kill(combined_worlds, target, night)
#         if not true_world_in_worlds(true_world, combined_worlds):
#             pass     
#     worlds_list = [combined_worlds]
#     for info in info_list:
#         if info["kind"]  == "fortune teller" and info["night"] == 2:
#             worlds_list.append(create_worlds_from_fortune_teller_info(game, info))
#         elif info["kind"]  == "empath" and info["night"] == 2:
#             worlds_list.append(create_worlds_from_empath_info(game, info))
#         elif info["kind"]  == "undertaker":
#             worlds_list.append(create_worlds_from_undertaker_info(game, info))
#         elif info["kind"]  == "ravenkeeper":
#             worlds_list.append(create_worlds_from_ravenkeeper_info(game, info))
#         if not true_world_in_worlds(true_world, combined_worlds):
#             pass     

#     if len(worlds_list) > 1:
#         combined_worlds, conflicting_worlds = combine_worlds(worlds_list)
#         if not true_world_in_worlds(true_world, combined_worlds):
#             pass     

#     return combined_worlds, conflicting_worlds