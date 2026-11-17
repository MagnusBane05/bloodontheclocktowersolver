from typing import Callable

from .grimoire_page import GrimoirePage

from .grimoire import Grimoire, gamerules
from .nightOrderPosition import NightOrderPosition
from .role import Role
# Changes a throwaway copy of a grim. An impossible change returns False or raises RuntimeError
# or ValueError, and _try_branch treats all of these as a rejected branch. Actions don't validate
# the pages they change: _finalize deduces and validates every page that changed. The only checks
# an action makes itself are game rules that no validator covers (starpass, Scarlet Woman catch).
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
        # grim is a throwaway copy, and _finalize deduces and validates the pages this changes
        try:
            _ = grim.apply_character(role, player, night, order)
            return True
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
        grim.apply_drunk(drunk_token, player, night, order)
        return True
    return action

def poisoned_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        # _finalize validates this page
        _get_info_page(grim, night, order).apply_poisoned(player)
        return True
    return action

def red_herring_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        # _finalize validates this page and copies the red herring to the pages around it
        _get_info_page(grim, night, order).apply_red_herring(player)
        return True
    return action

def not_red_herring_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        # _finalize validates this page
        _get_info_page(grim, night, order).apply_not_red_herring(player)
        return True
    return action

def imp_action(
    player: int,
    night: int,
    order: NightOrderPosition = NightOrderPosition.AFTER_IMP
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        _ = _get_info_page(grim, night, order).apply_character(Role.IMP, player)
        return True
    return action

def no_outsiders_action() -> BranchAction:
    def action(grim: Grimoire) -> bool:
        first_page = grim.get_first_page()
        first_page.apply_no_outsiders()
        return True
    return action

def chef_number_action(number: int) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        first_page = grim.get_first_page()
        first_page.apply_chef_number(number)
        return True
    return action

def mark_dead_action(
    player: int,
    night: int,
    order: NightOrderPosition,
) -> BranchAction:
    def action(grim: Grimoire) -> bool:
        page = _get_info_page(grim, night, order)
        assert page.can_be_dead(player), f"player {player} can't die on night {night} {order.name}"
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
        assert page.executee is None, f"night {night} already has an executee"
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
        # a game rule, not a validity check: no validator rejects an impossible catch
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
        # a game rule, not a validity check: no validator rejects an impossible starpass
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
        assert page.can_be_slayer_shot(target), f"player {target} can't be shot by the Slayer on night {night}"
        page.apply_slayer_shot(target)
        return True
    return action
