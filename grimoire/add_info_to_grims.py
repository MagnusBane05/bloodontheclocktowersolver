from .info import *
from .grimoire import *

def add_info_to_grims(info: Info, grims: list[Grimoire]):
    pass

def _add_demon_kill(info: DemonKillInfo, grims: list[Grimoire]) -> list[Grimoire]:
    night = info['night']
    player = info['player']
    new_grims: set[Grimoire] = set()

    for grim in grims:
        page = grim.get_page(night, NightOrderPosition.AFTER_IMP)
        if page == None:
            page = grim.add_page(night, NightOrderPosition.AFTER_IMP)

        assert(not page.dead[player])


        if gamerules.can_imp_starpass(page, player):
            sw_grim = grim.clone()
            sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_IMP)
            assert(sw_page != None)
            sw_page.dead[player] = True
            sw_page.apply_starpass(player)
            valid = Grimoire.pass_through_pages(sw_grim)
            if valid and gamerules.is_grim_valid(sw_grim):
                Grimoire.make_deductions(sw_grim)
                new_grims.add(sw_grim)
        if page.characters[player] != Role.IMP:
            non_sw_grim = grim.clone()
            non_sw_page = non_sw_grim.get_page(night, NightOrderPosition.AFTER_IMP)
            assert(non_sw_page != None)
            non_sw_page.dead[player] = True
            non_sw_grim.apply_non_demon_to_player(player, non_sw_page)
            valid = Grimoire.pass_through_pages(non_sw_grim)
            if valid and gamerules.is_grim_valid(non_sw_grim):
                Grimoire.make_deductions(non_sw_grim)
                new_grims.add(non_sw_grim)

    return list(new_grims)

def _add_execution(info: ExecutionInfo, grims: list[Grimoire]) -> list[Grimoire]:
    night = info['night']
    executee = info['player']
    new_grims: set[Grimoire] = set()

    for grim in grims:
        page = grim.get_page(night, NightOrderPosition.AFTER_EXECUTION)
        if page == None:
            page = grim.add_page(night, NightOrderPosition.AFTER_EXECUTION)

        assert(not page.dead[executee])

        if gamerules.can_scarlet_woman_catch(page, executee):
            sw_grim = grim.clone()
            sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_EXECUTION)
            assert(sw_page != None)
            sw_page.dead[executee] = True
            sw_page.executee = executee
            sw_grim.apply_sw_catch(executee, sw_page)
            valid = Grimoire.pass_through_pages(sw_grim)
            if valid and gamerules.is_grim_valid(sw_grim):
                Grimoire.make_deductions(sw_grim)
                new_grims.add(sw_grim)
        if page.characters[executee] != Role.IMP:
            non_sw_grim = grim.clone()
            non_sw_page = non_sw_grim.get_page(night, NightOrderPosition.AFTER_EXECUTION)
            assert(non_sw_page != None)
            non_sw_page.dead[executee] = True
            non_sw_page.executee = executee
            if page.characters[executee] == Role.SAINT:
                non_sw_page.poisoned[executee] = True
                try:
                    non_sw_page.add_minion_type(Role.POISONER)
                except ValueError:
                    continue
            non_sw_grim.apply_non_demon_to_player(executee, non_sw_page)
            valid = Grimoire.pass_through_pages(non_sw_grim)
            if valid and gamerules.is_grim_valid(non_sw_grim):
                Grimoire.make_deductions(non_sw_grim)
                new_grims.add(non_sw_grim)

    return list(new_grims)

def _add_slayer_shot(info: SlayerKillInfo, grims: list[Grimoire]) -> list[Grimoire]:
    night = info['night']
    target = info['player']
    new_grims: set[Grimoire] = set()

    for grim in grims:
        page = grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
        if page == None:
            page = grim.add_page(night, NightOrderPosition.AFTER_SLAYER)

        assert(not page.dead[target])

        if gamerules.can_scarlet_woman_catch(page, target):
            sw_grim = grim.clone()
            sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
            assert(sw_page != None)
            sw_page.dead[target] = True
            sw_grim.apply_sw_catch(target, sw_page)
            valid = Grimoire.pass_through_pages(sw_grim)
            if valid and gamerules.is_grim_valid(sw_grim):
                Grimoire.make_deductions(sw_grim)
                new_grims.add(sw_grim)
        if gamerules.can_player_be_recluse(page.characters[target]):
            recluse_grim = grim.clone()
            recluse_page = recluse_grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
            assert(recluse_page != None)
            recluse_page.dead[target] = True
            recluse_grim.apply_role_to_player(target, Role.RECLUSE, recluse_page)
            valid = Grimoire.pass_through_pages(recluse_grim)
            if valid and gamerules.is_grim_valid(recluse_grim):
                Grimoire.make_deductions(recluse_grim)
                new_grims.add(recluse_grim)

    return list(new_grims)

def add_death_info_to_grims(info: DeathInfo, grims: list[Grimoire]) -> list[Grimoire]:
    if info['kind'] == "demon":
        return _add_demon_kill(info, grims)
    elif info['kind'] == "execution":
        return _add_execution(info, grims)
    elif info['kind'] == "slayer":
        return _add_slayer_shot(info, grims)
    else:
        raise RuntimeError(f"{info['kind']} death info type not handled.")
