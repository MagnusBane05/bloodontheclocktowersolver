from typing import Callable

from grimoire.grimoire import Grimoire, GrimoirePage, NightOrderPosition, Role, gamerules
from grimoire.info import Role
from grimoire.nightOrderPosition import NightOrderPosition
from grimoire.role import Role
BranchAction = Callable[[Grimoire], bool]

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
        deduce = grim.apply_character(role, player, night, order)
        if deduce:
            grim.make_deductions()
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

def imp_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if not page.can_be_character(Role.IMP, player):
            return False
        page.apply_character(Role.IMP, player)
        return True
    return action

def mark_dead_action(
    player: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if not page.can_be_dead(player):
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
        if not gamerules.can_scarlet_woman_catch(page, demon):
            return False
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