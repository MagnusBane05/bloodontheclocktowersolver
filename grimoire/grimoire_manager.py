from __future__ import annotations
from collections import Counter, defaultdict
import logging
import time
from typing import Any, Callable, NamedTuple

from .traces import TrueGrimTrace

from .errors import TrueGrimLostError
# logging.basicConfig(level=logging.DEBUG)

from .info import Info, DeathInfo, FIRST_NIGHT_INFO, ANY_NIGHT_INFO
from .info_to_grim import info_to_grimoires
from .game import Game
from .grimoire import Grimoire
from .role import EVIL_CHARACTERS, GOOD_CHARACTERS, Role
from . import helper
from .add_info_to_grims import add_death_info_to_grims, add_info_to_grims

SAMPLE_CHANCE = 0

BRANCHING_INFO = ["fortune teller", "empath", "undertaker", "ravenkeeper", "virgin", "slayer"]

class StepRecord(NamedTuple):
    stage: str
    grims_before: int
    grims_after: int
    seconds: float

class GrimoireManager():
    
    def __init__(
            self, 
            game: Game, 
            true_grim: Grimoire | None = None, 
            on_step: Callable[[StepRecord], None] | None = None):
        self.game: Game = game
        self.grims: list[Grimoire] = []
        self.true_grim: Grimoire | None = true_grim
        self.on_step: Callable[[StepRecord], None] | None = on_step
        self.step_started: float = time.perf_counter()

    def _make_trace(self, stage: str) -> TrueGrimTrace | None:
        if self.true_grim is None:
            return None
        return TrueGrimTrace(
            true_grim=self.true_grim,
            stage=stage,
        )
    
    def _add_branching_info(self, info: Info, stage: str | None = None):
        before = self.grims
        if len(before) == 0:
            self.grims.append(Grimoire(self.game["players"]))
        night = info['night'] if "night" in info else 1
        trace = self._make_trace(f"night {night} {info['kind']} info")
        new_grims = add_info_to_grims(info, self.grims, trace)
        self._set_grims_checked(
            new_grims,
            stage or f"info {info}",
            previous_grims=before,
        )

    def add_full_game(self, info_list: list[Info], death_info: list[DeathInfo], nights: int):
        self.step_started = time.perf_counter()
        for night in range(1,nights+1):
            # add imp kill
            for imp_kill in [
                d for d in death_info 
                if d["kind"] == "demon" 
                and d["night"] == night
            ]:
                before = self.grims
                stage = f"night {night} imp kill {imp_kill}"
                trace = self._make_trace(stage)
                new_grims = add_death_info_to_grims(imp_kill, self.grims, trace)
                self._set_grims_checked(
                    new_grims,
                    f"night {night} imp kill {imp_kill}",
                    previous_grims=before,
                )

            # add info
            for info in info_list:
                if night == 1 and info["kind"] in FIRST_NIGHT_INFO:
                    self._add_branching_info(info)
                elif info["kind"] in ANY_NIGHT_INFO and "night" in info and info['night'] == night:
                    self._add_branching_info(info, f"night {night} {info["kind"]} info.")
                # elif info["kind"] in ANY_NIGHT_INFO and "night" in info and info['night'] == night:
                #     self.add_info(info)

            for death in [d for d in death_info if d["night"] == night]:
                # add slayer shot and execution
                if death["kind"] == "slayer" or death["kind"] == "execution":
                    before = self.grims
                    stage = f"night {night} death {death}"
                    trace = self._make_trace(stage)
                    new_grims = add_death_info_to_grims(death, self.grims, trace)
                    self._set_grims_checked(
                        new_grims,
                        stage,
                        previous_grims=before,
                    )

    def add_info(self, info: Info, stage: str | None = None):
        before = self.grims
        before_count = len(self.grims)
        new_grims = info_to_grimoires(self.game, info)

        logging.debug(
            f"add_info {info['kind']}: before={before_count}, " +
            f"new_grims={len(new_grims)}, " +
            f"potential_pairs={before_count * len(new_grims)}"
        )

        valid_grims = self._merge_new_grims(new_grims)

        logging.debug(
            f"add_info {info['kind']}: after_merge={len(valid_grims)}"
        )

        self._set_grims_checked(
            valid_grims,
            stage or f"info {info}",
            previous_grims=before
        )

    def set_grims(self, new_grims: list[Grimoire]):
        if self.true_grim != None:
            if not self._does_grim_list_contain_true_grim(new_grims, self.true_grim):
                for i,grim in enumerate(self.grims):
                    if grim .loose_equals(self.true_grim):
                        print(i,grim)
        self.grims = new_grims
        
    def _set_grims_checked(
        self,
        new_grims: list[Grimoire],
        stage: str,
        *,
        previous_grims: list[Grimoire] | None = None,
    ):
        new_grims = GrimoireManager.remove_unneeded_poison(new_grims)

        if self.on_step is not None:
            seconds = time.perf_counter() - self.step_started
            grims_before = len(previous_grims) if previous_grims is not None else len(self.grims)
            record = StepRecord(stage, grims_before, len(new_grims), seconds)
            self.on_step(record)
            self.step_started = time.perf_counter()

        if len(new_grims) > 250000:
            raise RuntimeError(f"{len(new_grims)} is too many solutions.")

        if self.true_grim is not None and not self._contains_true_grim(new_grims):
            previous = previous_grims if previous_grims is not None else self.grims

            previous_true_matches = [
                grim for grim in previous
                if self.true_grim.loose_equals(grim)
            ]

            raise TrueGrimLostError(
                f"True grim lost at {stage}. " + 
                f"before={len(previous)}, after={len(new_grims)}, " + 
                f"previous_true_matches={len(previous_true_matches)}"
            )

        self.grims = new_grims

    def _merge_new_grims(self, new_grims: list[Grimoire]) -> list[Grimoire]:
        if len(self.grims) == 0:
            return new_grims
        
        valid_worlds: set[Grimoire] = set()

        total = 0
        quick_rejected = 0
        invalid = 0
        accepted = 0
        duplicate = 0
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
                    valid_worlds.add(combined_world)
                else:  
                    invalid += 1
                    invalid_reasons[reason] += 1

        logging.debug(
            f"merge: total={total}, quick_rejected={quick_rejected}, "
            f"invalid={invalid}, accepted={accepted}, duplicate={duplicate}, "
            f"final={len(valid_worlds)}"
        )

        return list(valid_worlds)

    @staticmethod
    def _quick_reject(g1: Grimoire, g2: Grimoire) -> bool:
        if len(g2.pages) > 2:
            logging.warning(f"New grim has more pages than expected ({len(g2.pages)})")
        for p2 in g2.pages:
            p1 = g1.get_page(p2.night, p2.night_order_position)
            if p1 == None:
                continue
            
            for i,c in enumerate(p2.characters):
                if not helper.roleLooseEquals(c, p1.characters[i]):
                    return True
                
        return False
    
    @staticmethod
    def remove_unneeded_poison(grims: list[Grimoire]) -> list[Grimoire]:
        """Drops a grim if another is the same apart from having strictly less poison.
        That world has recorded what the info implies, so the poison isn't needed to explain anything."""
        by_state: dict[tuple[Any, ...], list[Grimoire]] = defaultdict(list)  # pyright: ignore[reportExplicitAny]
        for grim in grims:
            by_state[grim.state_without_poison()].append(grim)

        kept: list[Grimoire] = []
        for group in by_state.values():
            if len(group) == 1:
                kept.append(group[0])
                continue
            poisonings = [g.get_all_poisonings() for g in group]
            kept.extend(
                g for g, mine in zip(group, poisonings)
                if not any(other < mine for other in poisonings)
            )
        return kept

    def _contains_true_grim(self, grims: list[Grimoire]) -> bool:
        if self.true_grim is None:
            return True
        return any(self.true_grim.loose_equals(grim) for grim in grims)

    def do_grims_contain_true_grim(self) -> bool:
        if self.true_grim is None:
            print("No true grim has been added.")
            return True
        
        return self._does_grim_list_contain_true_grim(self.grims, self.true_grim)
    
    @staticmethod
    def _does_grim_list_contain_true_grim(
        grims: list[Grimoire], 
        true_grim: Grimoire,
    ):
        for grim in grims:
            if true_grim.loose_equals(grim):
                return True
        logging.warning("True grim not found in grims")
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
