from typing import TypeVar, Callable
import logging

# logging.basicConfig(level=logging.DEBUG)

from .branch_actions import *
from .info import *
from .grimoire import *
from .role import *
from .traces import TrueGrimTrace
from .nightOrderPosition import NightOrderPosition

def _finalize(grim: Grimoire) -> Grimoire | None:
    valid, _reason = Grimoire.pass_through_pages(grim)
    if not valid:
        # logging.warning(_reason)
        return None
    grim.make_deductions()
    if not gamerules.is_grim_valid(grim):
        return None
    return grim

def _try_branch(
    base: Grimoire,
    *actions: BranchAction,
    finalize: bool = True
) -> Grimoire | None:
    candidate = base.clone()

    try:
        for action in actions:
            if not action(candidate):
                return None
            
        if finalize:
            return _finalize(candidate)
            
        return candidate
    
    except (RuntimeError, ValueError):
        return None
    
def _try_intermediate_branch(
    base: Grimoire,
    *actions: BranchAction,
) -> Grimoire | None:
    return _try_branch(base, *actions, finalize=False)
    
def _add_branch(
    out: set[Grimoire],
    base: Grimoire,
    *actions: BranchAction,
    finalize: bool = True,
    label: str = "",
    trace: TrueGrimTrace | None = None,
) -> Grimoire | None:
    candidate = _try_branch(base, *actions, finalize=finalize)
    if candidate is not None:
        out.add(candidate)
        if trace is not None:
            trace.record_candidate(label, candidate)
    return candidate

def _add_drunk_evil_poisoned(
    player: int, 
    claim: Role, 
    grim: Grimoire, 
    night: int
) -> tuple[set[Grimoire], Grimoire | None]:
    out: set[Grimoire] = set()
    order = NightOrderPosition.AFTER_IMP

    # Drunk
    if claim in TOWNSFOLK_SET:
        _add_branch(
            out,
            grim,
            drunk_action(claim, player, night, order)
        )

    # Evil
    assert claim in GOOD_ROLES_SET
    _add_branch(
        out,
        grim,
        character_action(Role.ANY_OTHER_EVIL, player, night, order)
    )

    # Poisoned
    _add_branch(
        out,
        grim,
        character_action(claim, player, night, order),
        poisoned_action(player, night, order)
    )

    real_base = _try_intermediate_branch(
        grim,
        character_action(claim, player, night, order),
    )

    return out, real_base

def _add_claim(info: Claim, grim: Grimoire) -> list[Grimoire]:
    player = info["player"]
    claim = info["character"]
    night = 1
    order = NightOrderPosition.AFTER_IMP

    out: set[Grimoire] = set()

    # World where the player is the Drunk
    if claim in TOWNSFOLK_SET:
        _add_branch(
            out,
            grim,
            character_action(Role.DRUNK, player, night, order)
        )

    # World where the player is an unspecified evil character
    _add_branch(
        out,
        grim,
        character_action(Role.ANY_OTHER_EVIL, player, night, order)
    )

    # World where the player is exactly the claimed character
    _add_branch(
        out,
        grim,
        character_action(claim, player, night, order)
    )

    return list(out)

def _add_investigator_info(info: InvestigatorInfo, grim: Grimoire) -> list[Grimoire]:
    player = info["investigator"]
    a = info["first_player"]
    b = info["second_player"]
    minion = info["minion"]
    night = 1
    order = NightOrderPosition.AFTER_IMP

    out, base = _add_drunk_evil_poisoned(
        player, 
        Role.INVESTIGATOR,
        grim,
        night
    )

    if base is None:
        return list(out)
    
    for target in (a, b):
        # Target is the minion
        _add_branch(
            out,
            base,
            character_action(minion, target, night, order)
        )

        # Target is the Recluse
        _add_branch(
            out,
            base,
            character_action(Role.RECLUSE, target, night, order)
        )

    return list(out)

def _add_washerwoman_info(info: WasherwomanInfo, grim: Grimoire) -> list[Grimoire]:
    player = info["washerwoman"]
    a = info["first_player"]
    b = info["second_player"]
    townsfolk = info["townsfolk"]
    night = 1
    order = NightOrderPosition.AFTER_IMP

    out, base = _add_drunk_evil_poisoned(
        player, 
        Role.WASHERWOMAN,
        grim,
        night
    )

    if base is None:
        return list(out)
    
    for target in (a, b):
        # Target is the townsfolk
        _add_branch(
            out,
            base,
            character_action(townsfolk, target, night, order)
        )

        # Target is the Spy
        _add_branch(
            out,
            base,
            character_action(Role.SPY, target, night, order)
        )

    return list(out)

def _add_librarian_info(info: LibrarianInfo, grim: Grimoire) -> list[Grimoire]:
    player = info["librarian"]
    a = info["first_player"]
    b = info["second_player"]
    outsider = info["token"]
    night = 1
    order = NightOrderPosition.AFTER_IMP

    out, base = _add_drunk_evil_poisoned(
        player, 
        Role.LIBRARIAN,
        grim,
        night
    )

    if base is None:
        return list(out)
    
    if outsider is None:
        _add_branch(
            out,
            base,
            no_outsiders_action()
        )
        return list(out)
    
    if a is None or b is None:
        raise RuntimeError(f"Librarian info with token {outsider} shown but no players.")
    
    for target in (a, b):
        # Target is the outsider
        _add_branch(
            out,
            base,
            character_action(outsider, target, night, order)
        )

        # Target is the Spy
        _add_branch(
            out,
            base,
            character_action(Role.SPY, target, night, order)
        )

    return list(out)

def _add_chef_info(info: ChefInfo, grim: Grimoire) -> list[Grimoire]:
    player = info["chef"]
    number = info["number"]
    night = 1

    out, base = _add_drunk_evil_poisoned(
        player,
        Role.CHEF,
        grim,
        night
    )

    if base is None:
        return list(out)
    
    _add_branch(
        out,
        base,
        chef_number_action(number)
    )

    return list(out)




def _add_fortune_teller_info(info: FortuneTellerInfo, grim: Grimoire) -> list[Grimoire]:
    player = info['fortune_teller']
    night = info['night']
    order = NightOrderPosition.AFTER_IMP
    (a, b), ping = info['pings']
    
    out, ft_base = _add_drunk_evil_poisoned(
        player, 
        Role.FORTUNE_TELLER, 
        grim,
        night
    )

    if ft_base is None:
        return list(out)

    if ping:
        for target in (a, b):
            # Target is the demon
            _add_branch(
                out,
                ft_base,
                imp_action(target, night, order)
            )

            # Target is the red herring and Spy
            _add_branch(
                out,
                ft_base,
                character_action(Role.SPY, target, night, order),
                red_herring_action(target, night, order)
            )

            # Target is the red herring and good
            _add_branch(
                out,
                ft_base,
                character_action(Role.ANY_OTHER_GOOD, target, night, order),
                red_herring_action(target, night, order)
            )

            # Target is Recluse registering as demon
            _add_branch(
                out,
                ft_base,
                character_action(Role.RECLUSE, target, night, order)
            )

    else:
        # Both targets are not the demon
        _add_branch(
            out,
            ft_base,
            character_action(Role.NON_DEMON, a, night, order),
            character_action(Role.NON_DEMON, b, night, order)
        )

    return list(out)

def _add_empath_info(info: EmpathInfo, grim: Grimoire) -> list[Grimoire]:
    player = info["empath"]
    night = info["night"]
    order = NightOrderPosition.AFTER_IMP
    number = info["number"]
    left = info["left_neighbour"]
    right = info["right_neighbour"]

    out, empath_base = _add_drunk_evil_poisoned(
        player,
        Role.EMPATH,
        grim,
        night
    )

    if empath_base is None:
        return list(out)
    
    if number == 0:
        # Both neighbours are good
        _add_branch(
            out,
            empath_base,
            character_action(Role.ANY_OTHER_GOOD, left, night, order),
            character_action(Role.ANY_OTHER_GOOD, right, night, order),
        )

        # Left neighbour is the Spy
        _add_branch(
            out,
            empath_base,
            character_action(Role.SPY, left, night, order),
            character_action(Role.ANY_OTHER_GOOD, right, night, order),
        )

        # Right neighbour is the Spy
        _add_branch(
            out,
            empath_base,
            character_action(Role.SPY, right, night, order),
            character_action(Role.ANY_OTHER_GOOD, left, night, order),
        )

    elif number == 1:
        for a, b in ((left, right), (right, left)):
            # Neighbour a is evil and b is good
            _add_branch(
                out,
                empath_base,
                character_action(Role.ANY_OTHER_EVIL, a, night, order),
                character_action(Role.ANY_OTHER_GOOD, b, night, order),
            )

            # Neighbour a is evil and b is the Spy
            _add_branch(
                out,
                empath_base,
                character_action(Role.ANY_OTHER_EVIL, a, night, order),
                character_action(Role.SPY, b, night, order),
            )

            # Neighbour a is the Recluse and b is good
            _add_branch(
                out,
                empath_base,
                character_action(Role.RECLUSE, a, night, order),
                character_action(Role.ANY_OTHER_GOOD, b, night, order),
            )

            # Neighbour a is Revluse and b is the Spy
            _add_branch(
                out,
                empath_base,
                character_action(Role.RECLUSE, a, night, order),
                character_action(Role.SPY, b, night, order),
            )

    elif number == 2:
        # Both neighbours are evil
        _add_branch(
            out,
            empath_base,
            character_action(Role.ANY_OTHER_EVIL, left, night, order),
            character_action(Role.ANY_OTHER_EVIL, right, night, order),
        )

        # Left is evil and right is Recluse
        _add_branch(
            out,
            empath_base,
            character_action(Role.ANY_OTHER_EVIL, left, night, order),
            character_action(Role.RECLUSE, right, night, order),
        )

        # Right is evil and left is Recluse
        _add_branch(
            out,
            empath_base,
            character_action(Role.RECLUSE, left, night, order),
            character_action(Role.ANY_OTHER_EVIL, right, night, order),
        )

    else:
        raise RuntimeError("Empath number cannot be greater than 2.")
    
    return list(out)

def _add_undertaker_info(info: UndertakerInfo, grim: Grimoire) -> list[Grimoire]:
    player = info["undertaker"]
    night = info["night"]
    character = info["token"]
    executee = info["body"]
    order = NightOrderPosition.AFTER_IMP

    out, ut_base = _add_drunk_evil_poisoned(
        player,
        Role.UNDERTAKER,
        grim,
        night
    )

    if ut_base is None:
        return list(out)
    
    # World where the undertaker sees the actual token (body is that token)
    if character == Role.IMP:
        _add_branch(
            out,
            ut_base,
            imp_action(executee, night, order)
        )
    else:
        _add_branch(
            out,
            ut_base,
            character_action(character, executee, night, order)
        )

    # If the token is an evil character, the body could be the Recluse (registering as evil)
    if character in EVIL_CHARACTERS_SET:
        _add_branch(
            out,
            ut_base,
            character_action(Role.RECLUSE, executee, night, order)
        )

    elif character in GOOD_CHARACTERS_SET:
        _add_branch(
            out,
            ut_base,
            character_action(Role.SPY, executee, night, order)
        )

    return list(out)

def _add_ravenkeeper_info(info: RavenkeeperInfo, grim: Grimoire) -> list[Grimoire]:
    player=  info["ravenkeeper"]
    night = info["night"]
    character = info["token"]
    chosen = info["chosen"]
    order = NightOrderPosition.AFTER_IMP

    out, rk_base = _add_drunk_evil_poisoned(
        player,
        Role.RAVENKEEPER,
        grim,
        night
    )

    if rk_base is None:
        return list(out)
    
    # World where the Ravenkeeper sees the actual token (chosen player is that token)
    if character == Role.IMP:
        _add_branch(
            out,
            rk_base,
            imp_action(chosen, night, order)
        )
    else:
        _add_branch(
            out,
            rk_base,
            character_action(character, chosen, night, order)
        )

    # If the token is an evil character, the body could be the Recluse (registering as evil)
    if character in EVIL_CHARACTERS_SET:
        _add_branch(
            out,
            rk_base,
            character_action(Role.RECLUSE, chosen, night, order)
        )

    elif character in GOOD_CHARACTERS_SET:
        _add_branch(
            out,
            rk_base,
            character_action(Role.SPY, chosen, night, order)
        )

    return list(out)   

def _add_virgin_info(info: VirginInfo, grim: Grimoire)  -> list[Grimoire]:
    player=  info["virgin"]
    night = info["night"]
    nominator = info["nominator"]
    executed = info["executed"]
    order = NightOrderPosition.AFTER_IMP

    if executed:
        out: set[Grimoire] = set()

        # Townsfolk nominated virgin
        _add_branch(
            out,
            grim,
            character_action(Role.VIRGIN, player, night, order),
            character_action(Role.ANY_OTHER_TOWNSFOLK, nominator, night, order)
        )

        # Spy nominated virgin
        _add_branch(
            out,
            grim,
            character_action(Role.VIRGIN, player, night, order),
            character_action(Role.SPY, nominator, night, order)
        )

    else:
        out, virgin_base = _add_drunk_evil_poisoned(
            player,
            Role.VIRGIN,
            grim,
            night
        )

        if virgin_base is None or nominator == player:
            return list(out)

        # Evil nominated Virgin
        _add_branch(
            out,
            virgin_base,
            character_action(Role.ANY_OTHER_EVIL, nominator, night, order)
        )

        # Outsider nominated Virgin
        _add_branch(
            out,
            virgin_base,
            character_action(Role.ANY_OTHER_OUTSIDER, nominator, night, order)
        )

    return list(out)

def _add_slayer_info(info: SlayerInfo, grim: Grimoire) -> list[Grimoire]:
    player=  info["slayer"]
    night = info["night"]
    target = info["target"]
    successful = info["successful"]
    order = NightOrderPosition.AFTER_IMP

    if successful:
        out: set[Grimoire] = set()
        
        # World where the Slayer killed the Imp
        _add_branch(
            out,
            grim,
            character_action(Role.SLAYER, player, night, order),
            character_action(Role.IMP, target, night, order)
        )

        # World where the Slayer killed the Recluse (registering as the demon)
        _add_branch(
            out,
            grim,
            character_action(Role.SLAYER, player, night, order),
            character_action(Role.RECLUSE, target, night, order)
        )

    else:
        out, slayer_base = _add_drunk_evil_poisoned(
            player,
            Role.SLAYER,
            grim,
            night
        )

        if slayer_base is None or target == player:
            return list(out)

        # World where the slayer's shot hit a non-demon
        _add_branch(
            out,
            slayer_base,
            character_action(Role.NON_DEMON, target, night, order)
        )

    return list(out)


Y = TypeVar("Y", bound=Info)
def _apply_info(
    info: Y, 
    grims: list[Grimoire], 
    add_info_fn: Callable[[Y, Grimoire], list[Grimoire]],
    trace: TrueGrimTrace | None = None
) -> list[Grimoire]:
    new_grims: set[Grimoire] = set()
    before = len(grims)

    for grim in grims:
        new_grims.update(add_info_fn(info, grim))

    after = len(new_grims)
    logging.debug(
        f"added {info['kind']} info "
        f"before: {before}, after: {after}"
    )
    return list(new_grims)

def add_info_to_grims(
    info: Info, 
    grims: list[Grimoire], 
    trace: TrueGrimTrace | None = None
):
    if info["kind"] == "claim":
        return _apply_info(info, grims, _add_claim, trace)
    elif info["kind"] == "investigator":
        return _apply_info(info, grims, _add_investigator_info, trace)
    elif info["kind"] == "washerwoman":
        return _apply_info(info, grims, _add_washerwoman_info, trace)
    elif info["kind"] == "librarian":
        return _apply_info(info, grims, _add_librarian_info, trace)
    elif info["kind"] == "chef":
        return _apply_info(info, grims, _add_chef_info, trace)
    elif info["kind"] == "fortune teller":
        return _apply_info(info, grims, _add_fortune_teller_info, trace)
    elif info["kind"] == "empath":
        return _apply_info(info, grims, _add_empath_info, trace)
    elif info["kind"] == "undertaker":
        return _apply_info(info, grims, _add_undertaker_info, trace)
    elif info["kind"] == "ravenkeeper":
        return _apply_info(info, grims, _add_ravenkeeper_info, trace)
    elif info["kind"] == "virgin":
        return _apply_info(info, grims, _add_virgin_info, trace)
    elif info["kind"] == "slayer":
        return _apply_info(info, grims, _add_slayer_info, trace)
    else:
        raise RuntimeError(f"{info['kind']} info type not handled.")
    
def _add_demon_kill(
    info: DemonKillInfo, 
    grim: Grimoire, 
    trace: TrueGrimTrace | None = None,
) -> list[Grimoire]:
    night = info["night"]
    player = info["player"]
    order = NightOrderPosition.AFTER_IMP

    new_grims: set[Grimoire] = set()

    # Killed player was the Imp who starpassed
    _add_branch(
        new_grims,
        grim,
        mark_dead_action(player, night, order),
        starpass_action(player, night, order),
        label=f"player {player} is Imp who starpassed",
    )

    # Killed player was not the Imp
    _add_branch(
        new_grims,
        grim,
        mark_dead_action(player, night, order),
        character_action(Role.NON_DEMON, player, night, order),
    )

    return list(new_grims)

def _add_execution(
    info: ExecutionInfo, 
    grim: Grimoire,
    trace: TrueGrimTrace | None = None,
) -> list[Grimoire]:
    night = info["night"]
    executee = info["player"]
    order = NightOrderPosition.AFTER_EXECUTION

    new_grims: set[Grimoire] = set()

    # Executee was the demon and Scarlet Woman catches
    _add_branch(
        new_grims,
        grim,
        mark_dead_action(executee, night, order),
        sw_catch_action(executee, night, order),
        mark_executee_action(executee, night, order),
        label=f"execution: player {executee} was the demon",
        trace=trace
    )

    # Executee was not the demon
    _add_branch(
        new_grims,
        grim,
        mark_dead_action(executee, night, order),
        mark_executee_action(executee, night, order),
        saint_execution_poisoning_action(executee, night, order),
        character_action(Role.NON_DEMON, executee, night, order),
        label=f"execution: player {executee} was not the demon",
        trace=trace
    )

    return list(new_grims)

def _add_slayer_shot(
    info: SlayerKillInfo, 
    grim: Grimoire,
    trace: TrueGrimTrace | None = None,
) -> list[Grimoire]:
    night = info["night"]
    target = info["player"]
    order = NightOrderPosition.AFTER_SLAYER

    new_grims: set[Grimoire] = set()

    # Slayer killed the demon and Scarlet Woman caught
    _add_branch(
        new_grims,
        grim,
        slayer_shot_action(target, night, order),
        mark_dead_action(target, night, order),
        sw_catch_action(target, night, order),
    )

    # Slayer killed the Recluse registering as demon
    _add_branch(
        new_grims,
        grim,
        mark_dead_action(target, night, order),
        character_action(Role.RECLUSE, target, night, order),
    )

    return list(new_grims)

T = TypeVar("T", bound=DeathInfo)
def _apply_death_info(
    info: T, 
    grims: list[Grimoire], 
    add_info_fn: Callable[[T, Grimoire, TrueGrimTrace | None], list[Grimoire]],
    trace: TrueGrimTrace | None = None,
) -> list[Grimoire]:
    new_grims: set[Grimoire] = set()
    before = len(grims)

    for grim in grims:
        new_grims.update(add_info_fn(info, grim, trace))

    after = len(new_grims)
    logging.debug(
        f"added {info['kind']} death info "
        f"before: {before}, after: {after}"
    )
    return list(new_grims)

def add_death_info_to_grims(
    info: DeathInfo, 
    grims: list[Grimoire],
    trace: TrueGrimTrace | None = None,
)-> list[Grimoire]:
    if info['kind'] == "demon":
        return _apply_death_info(info, grims, _add_demon_kill, trace)
    elif info['kind'] == "execution":
        return _apply_death_info(info, grims, _add_execution, trace)
    elif info['kind'] == "slayer":
        return _apply_death_info(info, grims, _add_slayer_shot, trace)
    else:
        raise RuntimeError(f"{info['kind']} death info type not handled.")

