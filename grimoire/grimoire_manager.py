from logging import warning

from grimoire import helper

from .nightOrderPosition import NightOrderPosition

from . import gamerules
from .errors import PhaseNotFoundError
from .info import Info, DeathInfo, FIRST_NIGHT_INFO, ANY_NIGHT_INFO
from .info_to_grim import info_to_grimoires
from .game import Game
from .grimoire import Grimoire
from .grimoire_page import GrimoirePage
from .role import EVIL_CHARACTERS, GOOD_CHARACTERS, Role


class GrimoireManager():
    
    def __init__(self, game: Game, true_grim: Grimoire | None = None):
        self.game = game
        self.grims: list[Grimoire] = []
        self.true_grim = true_grim

    def add_full_game(self, info_list: list[Info], death_info: DeathInfo, nights: int):
        for night in range(1,nights+1):
            # add imp kill
            for imp_kill in death_info['killed_by_demon']:
                if imp_kill[1] == night:
                    self.add_demon_kill(imp_kill[0], night)

            # add info
            for info in info_list:
                if night == 1 and info["kind"] in FIRST_NIGHT_INFO:
                    self.add_info(info)
                elif info["kind"] in ANY_NIGHT_INFO and "night" in info and info['night'] == night:
                    self.add_info(info)

            # add slayer shot
            if death_info["slayer_shot"] is not None and death_info["slayer_shot"][1] == night:
                self.add_slayer_kill(death_info["slayer_shot"][0], night)

            # add execution
            for execution in death_info["executed"]:
                if execution[1] == night:
                    self.add_execution(execution[0], night)

            self.remove_duplicates() # faster than after adding info for games with 10 players

    def add_info(self, info: Info):
        new_grims = info_to_grimoires(self.game, info)
        valid_grims, _ = self._merge_new_grims(new_grims)
        self.set_grims(valid_grims)

    def set_grims(self, new_grims: list[Grimoire]):
        if self.true_grim != None:
            if not self._does_grim_list_contain_true_grim(new_grims, self.true_grim):
                for i,grim in enumerate(self.grims):
                    if grim == self.true_grim:
                        print(i,grim)
        self.grims = new_grims

    def _merge_new_grims(self, new_grims: list[Grimoire]) -> tuple[list[Grimoire], list[tuple[Grimoire,Grimoire]]]:
        if len(self.grims) == 0:
            return new_grims, []
        
        conflicting_worlds: list[tuple[Grimoire,Grimoire]] = []
        valid_worlds: list[Grimoire] = []

        for w1 in self.grims:
            for w2 in new_grims:
                combined_world, valid = Grimoire.combine(w1, w2)
                if valid: 
                    valid_worlds.append(combined_world)
                else:
                    conflicting_worlds.append((w1, w2))

        return valid_worlds, conflicting_worlds
    
    def remove_duplicates(self):
        self.grims = list(set(self.grims))
    
    def add_slayer_kill(self, target: int, night: int):
        new_grims: list[Grimoire] = []

        for grim in self.grims:
            try:
                page: GrimoirePage = grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
            except PhaseNotFoundError:
                page: GrimoirePage = grim.add_page(night, NightOrderPosition.AFTER_SLAYER)

            assert(not page.dead[target])

            page.dead[target] = True

            if gamerules.can_scarlet_woman_catch(page, target):
                sw_grim = grim.clone()
                sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
                sw_grim.apply_sw_catch(target, sw_page)
                valid = Grimoire.pass_through_pages(sw_grim)
                if valid and gamerules.is_grim_valid(sw_grim):
                    Grimoire.make_deductions(sw_grim)
                    new_grims.append(sw_grim)
            if gamerules.can_player_be_recluse(page.characters[target]):
                recluse_grim = grim.clone()
                recluse_page = recluse_grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
                recluse_grim.apply_role_to_player(target, Role.RECLUSE, recluse_page)
                valid = Grimoire.pass_through_pages(recluse_grim)
                if valid and gamerules.is_grim_valid(recluse_grim):
                    Grimoire.make_deductions(recluse_grim)
                    new_grims.append(recluse_grim)

        self.set_grims(new_grims)
    
    def add_execution(self, executee: int, night: int):
        new_grims: list[Grimoire] = []

        for grim in self.grims:
            try:
                page: GrimoirePage = grim.get_page(night, NightOrderPosition.AFTER_EXECUTION)
            except PhaseNotFoundError:
                page: GrimoirePage = grim.add_page(night, NightOrderPosition.AFTER_EXECUTION)

            assert(not page.dead[executee])

            if page.characters[executee] == Role.SAINT and not page.poisoned[executee]:
                continue

            page.dead[executee] = True
            page.executee = executee

            if gamerules.can_scarlet_woman_catch(page, executee):
                sw_grim = grim.clone()
                sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_EXECUTION)
                sw_grim.apply_sw_catch(executee, sw_page)
                valid = Grimoire.pass_through_pages(sw_grim)
                if valid and gamerules.is_grim_valid(sw_grim):
                    Grimoire.make_deductions(sw_grim)
                    new_grims.append(sw_grim)
            if page.characters[executee] != Role.IMP:
                non_sw_grim = grim.clone()
                non_sw_page = non_sw_grim.get_page(night, NightOrderPosition.AFTER_EXECUTION)
                non_sw_grim.apply_non_demon_to_player(executee, non_sw_page)
                valid = Grimoire.pass_through_pages(non_sw_grim)
                if valid and gamerules.is_grim_valid(non_sw_grim):
                    Grimoire.make_deductions(non_sw_grim)
                    new_grims.append(non_sw_grim)

        self.set_grims(new_grims)

    def add_demon_kill(self, player: int, night: int):
        new_grims: list[Grimoire] = []

        for grim in self.grims:
            try:
                page: GrimoirePage = grim.get_page(night, NightOrderPosition.AFTER_IMP)
            except PhaseNotFoundError:
                page: GrimoirePage = grim.add_page(night, NightOrderPosition.AFTER_IMP)

            assert(not page.dead[player])

            page.dead[player] = True

            if gamerules.can_imp_starpass(page, player):
                sw_grim = grim.clone()
                sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_IMP)
                sw_page.apply_starpass(player)
                valid = Grimoire.pass_through_pages(sw_grim)
                if valid and gamerules.is_grim_valid(sw_grim):
                    Grimoire.make_deductions(sw_grim)
                    new_grims.append(sw_grim)
            if page.characters[player] != Role.IMP:
                non_sw_grim = grim.clone()
                non_sw_page = non_sw_grim.get_page(night, NightOrderPosition.AFTER_IMP)
                non_sw_grim.apply_non_demon_to_player(player, non_sw_page)
                valid = Grimoire.pass_through_pages(non_sw_grim)
                if valid and gamerules.is_grim_valid(non_sw_grim):
                    Grimoire.make_deductions(non_sw_grim)
                    new_grims.append(non_sw_grim)

        self.set_grims(new_grims)

    def do_grims_contain_true_grim(self) -> bool:
        if self.true_grim is None:
            print("No true grim has been added.")
            return True
        
        return self._does_grim_list_contain_true_grim(self.grims, self.true_grim)
    
    @staticmethod
    def _does_grim_list_contain_true_grim(grims: list[Grimoire], true_grim: Grimoire, 
                                          conflicting_grims: list[tuple[Grimoire, Grimoire]] | None = None):
        for grim in grims:
            if true_grim == grim:
                return True
        warning("True grim not found in grims")
        if conflicting_grims is not None:
            for w1, w2 in conflicting_grims:
                if true_grim == w1:
                    warning("True grim found in conflicting grims")
                if true_grim == w2:
                    warning("True grim found in conflicting grims")
        return False
    
    def get_player_perspective(self, player: int) -> GrimoireManager:
        if self.true_grim is None:
            raise ValueError("True grim must be set to get perspective of player.")
        new_manager = GrimoireManager(self.game)
        for grim in self.grims:
            if not self._is_grim_valid_from_player_perspective(grim, player, self.true_grim):
                continue
            grim_copy = grim.clone()
            new_manager.grims.append(grim_copy)
        return new_manager
    
    @staticmethod
    def _is_grim_valid_from_player_perspective(grim: Grimoire, player: int, true_grim: Grimoire) -> bool:
        page = grim.pages[-1]
        character = page.characters[player]
        true_character = true_grim.pages[-1].characters[player]
        if true_character in EVIL_CHARACTERS:
            raise NotImplementedError("Getting perspective of evil player not implemented yet.")
        elif true_character in GOOD_CHARACTERS:
            if helper.roleLooseEquals(character, true_character):
                return True
            if character == Role.DRUNK and page.drunk_token == true_character:
                return True
            if true_character == Role.DRUNK and true_grim.pages[-1].drunk_token == character:
                return True
        return False
