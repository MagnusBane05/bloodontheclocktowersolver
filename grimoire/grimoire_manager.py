from __future__ import annotations
from collections import defaultdict
import logging
import time
from typing import Any, Callable, NamedTuple

from .traces import TrueGrimTrace

from .errors import TrueGrimLostError
# logging.basicConfig(level=logging.DEBUG)

from .info import Info, DeathInfo, FIRST_NIGHT_INFO, ANY_NIGHT_INFO
from .game import Game
from .grimoire import Grimoire
from .role import EVIL_CHARACTERS, GOOD_CHARACTERS, Role
from . import helper
from .add_info_to_grims import add_death_info_to_grims, add_info_to_grims

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
    
    def _add_info(self, info: Info, stage: str | None = None):
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
                    self._add_info(info)
                elif info["kind"] in ANY_NIGHT_INFO and "night" in info and info['night'] == night:
                    self._add_info(info, f"night {night} {info["kind"]} info.")

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

        before = self.grims
        self.remove_subsumed_grims() # clean up subsumed grims before we return
        self._set_grims_checked(
            self.grims,
            "final remove_subsumed_grims",
            previous_grims=before,
        )

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

    def remove_subsumed_grims(self, max_bucket_size: int = 500):
        buckets: dict[tuple, list[Grimoire]] = defaultdict(list) # type: ignore
        for grim in self.grims:
            buckets[self.subsumtion_buket_key(grim)].append(grim) # type: ignore

        result: list[Grimoire] = []
        before = len(self.grims)

        for bucket in buckets.values():
            if len(bucket) > max_bucket_size:
                result.extend(
                    self.remove_subsumed_from_large_bucket(
                        bucket,
                        max_checks_per_grim=100,
                    )
                )
            else:
                result.extend(self.remove_subsumed_from_bucket(bucket))

        self.grims = result
        after = len(result)
        logging.debug(f"removed {before - after} subsumed grims")

    @staticmethod
    def remove_subsumed_from_bucket(grims: list[Grimoire]) -> list[Grimoire]:
        unique: list[Grimoire] = []

        for grim in grims:
            should_add = True
            indexes_to_remove: list[int] = []

            for idx, other in enumerate(unique):
                if other.subsumes(grim):
                    # Existing grim is more general, so new grim adds nothing.
                    should_add = False
                    break

                if grim.subsumes(other):
                    # New grim is more general, so remove existing one.
                    indexes_to_remove.append(idx)

            if should_add:
                for idx in reversed(indexes_to_remove):
                    del unique[idx]
                unique.append(grim)

        return unique
    
    @staticmethod
    def remove_subsumed_from_large_bucket(
        grims: list[Grimoire],
        max_checks_per_grim: int = 100,
    ) -> list[Grimoire]:
        grims = sorted(grims, key=GrimoireManager.grim_generality_score, reverse=True)

        unique: list[Grimoire] = []

        for grim in grims:
            subsumed = False

            for other in unique[:max_checks_per_grim]:
                if other.subsumes(grim):
                    subsumed = True
                    break

            if not subsumed:
                unique.append(grim)

        return unique
    
    @staticmethod
    def grim_generality_score(grim: Grimoire) -> int:
        score = 0

        for page in grim.pages:
            for c in page.characters:
                if c == Role.ANY_OTHER:
                    score += 10
                elif c in {Role.ANY_OTHER_GOOD, Role.ANY_OTHER_EVIL, Role.NON_DEMON}:
                    score += 7
                elif c in {
                    Role.ANY_OTHER_TOWNSFOLK,
                    Role.ANY_OTHER_OUTSIDER,
                    Role.ANY_OTHER_MINION,
                }:
                    score += 5

            score += page.minion_types.count(Role.ANY_OTHER_MINION) * 5

            if page.drunk_token is None:
                score += 1

            if page.chef_number is None:
                score += 1

        return score

    @staticmethod
    def subsumtion_buket_key(grim: Grimoire) -> tuple: # type: ignore
        return (
            grim.num_players,
            tuple(grim.keys),
            tuple(
                (
                    tuple(page.poisoned),
                    tuple(page.red_herring),
                    page.drunk_token,
                    page.chef_number,
                    page.no_outsiders
                )
                for page in grim.pages
            ),
        )
    
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
