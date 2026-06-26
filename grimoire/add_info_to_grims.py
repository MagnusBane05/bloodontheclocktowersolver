from typing import TypeVar, Callable
import logging

from .traces import TrueGrimTrace
# logging.basicConfig(level=logging.DEBUG)

from .info import *
from .grimoire import *
from .role import *
from .nightOrderPosition import NightOrderPosition

BranchAction = Callable[[Grimoire], bool]

def _finalize(grim: Grimoire) -> Grimoire | None:
    valid, _reason = Grimoire.pass_through_pages(grim)
    if not valid:
        return None
    grim.make_deductions()
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

def _get_info_page(
    grim: Grimoire, 
    night: int, 
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> GrimoirePage:
    page = grim.get_page(night, order)
    if page is not None:
        return page
    return grim.add_page(night, order)

def character_action(
    role: Role,
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        if not grim.can_be_character(role, player, night, order):
            return False
        grim.apply_character(role, player, night, order)
        return True
    return action

def drunk_action(
    drunk_token: Role,
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        if not grim.can_be_character(Role.DRUNK, player, night, order):
            return False
        grim.apply_drunk(drunk_token, player, night, order)
        return True
    return action

def poisoned_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if not page.can_be_poisoned(player):
            return False
        page.apply_poisoned(player)
        return True
    return action

def red_herring_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        if not grim.can_be_red_herring(player, night, order):
            return False
        page = _get_info_page(grim, night, order)
        page.apply_red_herring(player)
        return True
    return action

def mark_dead_action(
    player: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if page.dead[player]:
            return False
        page.dead[player] = True
        return True
    return action


def mark_executee_action(
    executee: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if page.executee is not None:
            return False
        page.executee = executee
        return True
    return action


def sw_catch_action(
    demon: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if page.dead[demon]:
            return False
        if not gamerules.can_scarlet_woman_catch(page, demon):
            return False
        page.dead[demon] = True
        grim.apply_sw_catch(demon, page)
        return True
    return action


def starpass_action(
    imp: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if page.dead[imp]:
            return False
        page.dead[imp] = True
        if not gamerules.can_imp_starpass(page, imp):
            return False
        grim.apply_starpass(imp, page)
        return True
    return action


def saint_execution_poisoning_action(
    executee: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if page.characters[executee] != Role.SAINT:
            return True
        if not page.can_be_poisoned(executee):
            return False
        page.apply_poisoned(executee)
        return True
    return action


def recluse_death_action(
    target: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if not grim.can_be_character(Role.RECLUSE, target, night, order):
            return False
        if page.dead[target]:
            return False
        page.dead[target] = True
        grim.apply_character(Role.RECLUSE, target, night, order)
        return True
    return action

def slayer_shot_action(
    target: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if not page.can_be_slayer_shot(target):
            return False
        page.apply_slayer_shot(target)
        return True
    return action
    
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

    real_base = _try_branch(
        grim,
        character_action(claim, player, night, order),
    )

    return out, real_base

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
            # target is the demon
            _add_branch(
                out,
                ft_base,
                character_action(Role.IMP, target, night, order)
            )

            # target is the red herring and Spy
            _add_branch(
                out,
                ft_base,
                character_action(Role.SPY, target, night, order),
                red_herring_action(target, night, order)
            )

            # target is the red herring and good
            _add_branch(
                out,
                ft_base,
                character_action(Role.ANY_OTHER_GOOD, target, night, order),
                red_herring_action(target, night, order)
            )

            # target is Recluse registering as demon
            _add_branch(
                out,
                ft_base,
                character_action(Role.RECLUSE, target, night, order)
            )

    else:
        _add_branch(
            out,
            ft_base,
            character_action(Role.NON_DEMON, a, night, order),
            character_action(Role.NON_DEMON, b, night, order)
        )

    return list(out)

Y = TypeVar("Y", bound=Info)
def _apply_info(
    info: Y, 
    grims: list[Grimoire], 
    add_info_fn: Callable[[Y, Grimoire], list[Grimoire]]
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

def add_info_to_grims(info: Info, grims: list[Grimoire]):
    if info['kind'] == "fortune teller":
        return _apply_info(info, grims, _add_fortune_teller_info)
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
        sw_catch_action(target, night, order),
    )

    # Slayer killed the Recluse registering as demon
    _add_branch(
        new_grims,
        grim,
        recluse_death_action(target, night, order),
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

