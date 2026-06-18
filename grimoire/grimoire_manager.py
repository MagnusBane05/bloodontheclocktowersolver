from __future__ import annotations
from collections import Counter
from logging import warning
from random import random

from .nightOrderPosition import NightOrderPosition

from . import gamerules
from .info import Info, DeathInfo, FIRST_NIGHT_INFO, ANY_NIGHT_INFO
from .info_to_grim import info_to_grimoires
from .game import Game
from .grimoire import Grimoire
from .role import EVIL_CHARACTERS, GOOD_CHARACTERS, Role
from . import role

SAMPLE_CHANCE = 0


class GrimoireManager():
    
    def __init__(self, game: Game, true_grim: Grimoire | None = None):
        self.game = game
        self.grims: list[Grimoire] = []
        self.true_grim = true_grim

    def add_full_game(self, info_list: list[Info], death_info: list[DeathInfo], nights: int):
        for night in range(1,nights+1):
            # add imp kill
            for imp_kill in [
                d for d in death_info 
                if d["kind"] == "demon" 
                and d["night"] == night
            ]:
                self.add_demon_kill(imp_kill["player"], night)

            # add info
            for info in info_list:
                if night == 1 and info["kind"] in FIRST_NIGHT_INFO:
                    self.add_info(info)
                elif info["kind"] in ANY_NIGHT_INFO and "night" in info and info['night'] == night:
                    self.add_info(info)

            for death in [d for d in death_info if d["night"] == night]:
                # add slayer shot
                if death["kind"] == "slayer":
                    self.add_slayer_kill(death["player"], night)
                elif death["kind"] == "execution":
                    # add execution
                    self.add_execution(death["player"], night)

            self.remove_duplicates() # faster than calling every time we add info

    def add_info(self, info: Info):
        new_grims = info_to_grimoires(self.game, info)
        valid_grims = self._merge_new_grims(new_grims)
        self.set_grims(valid_grims)

    def set_grims(self, new_grims: list[Grimoire]):
        if self.true_grim != None:
            if not self._does_grim_list_contain_true_grim(new_grims, self.true_grim):
                for i,grim in enumerate(self.grims):
                    if grim == self.true_grim:
                        print(i,grim)
        self.grims = new_grims

    def _merge_new_grims(self, new_grims: list[Grimoire]) -> list[Grimoire]:
        if len(self.grims) == 0:
            return new_grims
        
        valid_worlds: list[Grimoire] = []

        total = 0
        quick_rejected = 0
        invalid = 0
        accepted = 0

        invalid_reasons: Counter[str] = Counter()
        for w1 in self.grims:
            for w2 in new_grims:
                total += 1
                if self._quick_reject(w1, w2):
                    quick_rejected += 1
                    continue
                combined_world, valid, reason = Grimoire.combine(w1, w2)
                if valid: 
                    accepted += 1
                    valid_worlds.append(combined_world)
                else:  
                    invalid += 1
                    invalid_reasons[reason] += 1

        if random() < SAMPLE_CHANCE:
            print()
            print(f"total: {total}, quick rejected: {quick_rejected}, invalid: {invalid}, accepted: {accepted}")
            print(f"total: 100%, quick rejected: {round(quick_rejected*100./total)}%, invalid: {round(invalid*100./total)}%, accepted: {round(accepted*100./total)}%")
            print()
            print(invalid_reasons.most_common(5))
            print()
        return valid_worlds

    @staticmethod
    def _quick_reject(g1: Grimoire, g2: Grimoire) -> bool:
        p2 = g2.pages[-1]
        p1 = g1.get_page(p2.night, p2.night_order_position)
        if p1 == None:
            return False
        
        for i,c in enumerate(p2.characters):
            if not role.roleLooseEquals(c, p1.characters[i]):
                return True
            
        return False

    
    def remove_duplicates(self):
        self.grims = list(set(self.grims))
    
    def add_slayer_kill(self, target: int, night: int):
        new_grims: list[Grimoire] = []

        for grim in self.grims:
            page = grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
            if page == None:
                page = grim.add_page(night, NightOrderPosition.AFTER_SLAYER)

            assert(not page.dead[target])

            page.dead[target] = True

            if gamerules.can_scarlet_woman_catch(page, target):
                sw_grim = grim.clone()
                sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
                assert(sw_page != None)
                sw_grim.apply_sw_catch(target, sw_page)
                valid = Grimoire.pass_through_pages(sw_grim)
                if valid and gamerules.is_grim_valid(sw_grim):
                    Grimoire.make_deductions(sw_grim)
                    new_grims.append(sw_grim)
            if gamerules.can_player_be_recluse(page.characters[target]):
                recluse_grim = grim.clone()
                recluse_page = recluse_grim.get_page(night, NightOrderPosition.AFTER_SLAYER)
                assert(recluse_page != None)
                recluse_grim.apply_role_to_player(target, Role.RECLUSE, recluse_page)
                valid = Grimoire.pass_through_pages(recluse_grim)
                if valid and gamerules.is_grim_valid(recluse_grim):
                    Grimoire.make_deductions(recluse_grim)
                    new_grims.append(recluse_grim)

        self.set_grims(new_grims)
    
    def add_execution(self, executee: int, night: int):
        new_grims: list[Grimoire] = []

        for grim in self.grims:
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
                    new_grims.append(sw_grim)
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
                # non_sw_page.make_deductions(len(non_sw_page.characters))
                # if (len(gamerules.get_alive_characters_of_type(non_sw_page, {Role.POISONER, Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER})) == 0 
                #     or non_sw_page.characters[executee] == Role.POISONER):
                #     non_sw_page.clear_poisoned()
                valid = Grimoire.pass_through_pages(non_sw_grim)
                if valid and gamerules.is_grim_valid(non_sw_grim):
                    Grimoire.make_deductions(non_sw_grim)
                    new_grims.append(non_sw_grim)

        self.set_grims(new_grims)

    def add_demon_kill(self, player: int, night: int):
        new_grims: list[Grimoire] = []

        for grim in self.grims:
            page = grim.get_page(night, NightOrderPosition.AFTER_IMP)
            if page == None:
                page = grim.add_page(night, NightOrderPosition.AFTER_IMP)

            assert(not page.dead[player])

            page.dead[player] = True

            if gamerules.can_imp_starpass(page, player):
                sw_grim = grim.clone()
                sw_page = sw_grim.get_page(night, NightOrderPosition.AFTER_IMP)
                assert(sw_page != None)
                sw_page.apply_starpass(player)
                valid = Grimoire.pass_through_pages(sw_grim)
                if valid and gamerules.is_grim_valid(sw_grim):
                    Grimoire.make_deductions(sw_grim)
                    new_grims.append(sw_grim)
            if page.characters[player] != Role.IMP:
                non_sw_grim = grim.clone()
                non_sw_page = non_sw_grim.get_page(night, NightOrderPosition.AFTER_IMP)
                assert(non_sw_page != None)
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
            if role.roleLooseEquals(character, true_character):
                return True
            if character == Role.DRUNK and page.drunk_token == true_character:
                return True
            if true_character == Role.DRUNK and true_grim.pages[-1].drunk_token == character:
                return True
        return False
