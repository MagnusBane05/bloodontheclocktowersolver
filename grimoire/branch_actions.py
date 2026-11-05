from typing import Callable

from . import validators

from .grimoire_page import GrimoirePage

from .grimoire import Grimoire, gamerules
from .nightOrderPosition import NightOrderPosition
from .role import Role
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

def _deduce_and_validate(changed_pages: list[GrimoirePage]) -> bool:
    for page in changed_pages:
        page.make_deductions()
        valid, _reason = validators.is_page_valid(page)
        if not valid:
            return False
    return True
    
def character_action(
    role: Role,
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        # grim is a throwaway copy, so there's no need to check the role fits before applying it
        try:
            changed_pages = grim.apply_character(role, player, night, order)
            return _deduce_and_validate(changed_pages)
        except (RuntimeError, ValueError):
            return False
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
        deduced = page.apply_character(Role.IMP, player)
        return _deduce_and_validate([page] if deduced else [])
    return action

def no_outsiders_action() -> BranchAction:
    def action(grim: Grimoire) -> bool:
        first_page = grim.get_first_page()
        if not first_page.can_have_no_outsiders():
            return False
        first_page.apply_no_outsiders()
        return _deduce_and_validate([first_page])
    return action

def chef_number_action(number: int) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        first_page = grim.get_first_page()
        if not first_page.can_have_chef_number(number):
            return False
        first_page.apply_chef_number(number)
        return _deduce_and_validate([first_page])
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
    red_herring_spy_catches: bool,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        if not gamerules.can_imp_starpass(page, imp, red_herring_spy_catches):
            return False
        grim.apply_starpass(imp, page, red_herring_spy_catches)
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
