import copy
from typing import Self, override
from itertools import compress
from .role import *
from .errors import *
from .phase import Phase

class World:
    def __init__(self, num_players:int=5):
        if num_players not in ROLE_BREAKDOWNS.keys():
            raise ValueError(f"{num_players} player worlds are not yet handled.")
        self.phases: list[Phase] = [Phase(num_players,1)]

    def __eq__(self, value):
        if not isinstance(value, World):
            return False
        players = len(self.phases[0].characters)
        if players != len(value.phases[0].characters):
            return False
        last_phase = self.phases[-1]
        other_phase = value.phases[-1]
        return all(last_phase[p] == other_phase[p] for p in range(players)) and all(m in other_phase.minion_types for m in last_phase.minion_types)

    @override
    def __str__(self):
        s = ""
        for i, phase in enumerate(self.phases):
            ps = f"--- Phase {i+1} ---\n"
            for j in range(len(phase.characters)):
                character = phase.characters[j]
                dead = phase.dead[j]
                red_herring = phase.red_herring[j]
                if character != Role.ANY_OTHER:
                    if character in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.NON_DEMON]:
                        ps += f"Player {j} is {CHARACTER_STRINGS[character]}.\n"
                    else:
                        ps += f"Player {j} is the {CHARACTER_STRINGS[character]}.\n"
                if phase.poisoned[j]:
                    ps += f"Player {j} was poisoned N{phase.night}.\n"
                if dead:
                    ps += f"Player {j} is dead.\n"
                if red_herring:
                    ps += f"Player {j} is the red herring.\n"
            s += ps
        s += "Minion types: "
        s += ", ".join([m.name for m in self.phases[-1].minion_types])
        s += "\n"
        s += "---------------------"
        return s

    def get_phase(self, night: int) -> Phase:
        for phase in self.phases:
            if phase.night == night:
                return phase
        raise PhaseNotFoundError(f"World does not contain phase with night {night}")

    def add_phase(self, night: int) -> Phase:
        inserted = False
        previous = None
        position = 0
        for i, phase in enumerate(self.phases):
            if phase.night == night:
                raise PhaseInWorldError(f"World already contains phase with night {night}")
            if phase.night < night:
                continue
            previous = self.phases[i-1]
            position = i
            inserted = True
            break
        if not inserted:
            previous = self.phases[-1]
            position = len(self.phases)

        new_phase = copy.deepcopy(previous)
        new_phase.night = night
        self.phases.insert(position, new_phase)
        
        return new_phase

    def execute_player(self: World, player: int, night: int) -> tuple[World, World | None]:
        try:
            phase: Phase = self.get_phase(night)
        except PhaseNotFoundError:
            phase: Phase = self.add_phase(night)      

        phase.dead[player] = True
        phase.executee = player
        
        non_sw_world: World = copy.deepcopy(self)
        non_sw_phase = non_sw_world.get_phase(night)

        # dead player is a non-demon
        if non_sw_phase.characters[player] == Role.ANY_OTHER:
            non_sw_phase.characters[player] = Role.NON_DEMON
        elif non_sw_phase.characters[player] == Role.ANY_OTHER_EVIL:
            non_sw_phase.characters[player] = Role.ANY_OTHER_MINION

        # also update all previous phases
        for n in range(1, night):
            prev_non_sw_phase = non_sw_world.get_phase(n)
            if prev_non_sw_phase.characters[player] == Role.ANY_OTHER:
                prev_non_sw_phase.characters[player] = Role.NON_DEMON
            elif prev_non_sw_phase.characters[player] == Role.ANY_OTHER_EVIL:
                prev_non_sw_phase.characters[player] = Role.ANY_OTHER_MINION
            
        non_sw_world = non_sw_world if World._validate_world(non_sw_world) else None

        if phase.characters[player] == Role.IMP:
            non_sw_world = None

        # known non-demon player executed
        if phase.characters[player] in [Role.NON_DEMON] + GOOD_CHARACTERS + MINIONS:
            return non_sw_world, None

        # known scarlet woman is dead already
        if any(c == Role.SCARLET_WOMAN for c in compress(phase.characters,[x for x in phase.dead])):
            return non_sw_world, None
        
        # all minions are dead already
        dead_minions = [c for i,c in enumerate(phase.characters) if phase.dead[i] and c in MINIONS + [Role.ANY_OTHER_MINION]]
        if len(dead_minions) >= len(phase.minion_types):
            return non_sw_world, None

        # none of the alive players could be a scarlet woman
        if not any(c in compress(phase.characters,[not x for x in phase.dead]) for c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.NON_DEMON, Role.SCARLET_WOMAN]):
            return non_sw_world, None
        
        # if there's room for a scarlet woman
        sw_world: World = copy.deepcopy(self)
        sw_phase = sw_world.get_phase(night)

        # dead player was the imp
        sw_phase.characters[player] = Role.IMP
        sw_phase.star_passed = True

        # also update all previous phases
        for n in range(1, night):
            prev_phase = sw_world.get_phase(n)
            prev_phase.characters[player] = Role.IMP

        # minion type becomes scarlet woman
        try:
            sw_phase.add_minion_type(Role.SCARLET_WOMAN)
            for n in range(1, night):
                prev_phase = sw_world.get_phase(n)
                prev_phase.add_minion_type(Role.SCARLET_WOMAN)
        except ValueError:
            return non_sw_world, None

        # if there's a known scarlet woman, they become the demon
        try:
            idx = sw_phase.characters.index(Role.SCARLET_WOMAN)
            sw_phase.characters[idx] = Role.IMP
            sw_phase.character_changed[idx] = True
            return non_sw_world, sw_world
        except:
            pass

        # single alive minion becomes the demon
        alive_known_minions = [c for c in compress(sw_phase.characters,[not x for x in sw_phase.dead]) if c == Role.ANY_OTHER_MINION]
        if len(alive_known_minions) == 1:
            for i,c in enumerate(sw_phase.characters):
                if sw_phase.dead[i]:
                    continue
                if c in alive_known_minions:
                    sw_phase.characters[i] = Role.IMP
                    sw_phase.character_changed[i] = True
                    for n in range(1, night):
                        prev_phase = sw_world.get_phase(n)
                        prev_phase.characters[i] = Role.SCARLET_WOMAN
                    return non_sw_world, sw_world

        # if all minions are accounted for, there cannot be NON_DEMON roles, so any NON_DEMON roles could be potential scarlet women
        for i,c in enumerate(sw_phase.characters):
            if sw_phase.dead[i]:
                continue
            if c == Role.NON_DEMON:
                sw_phase.characters[i] = Role.ANY_OTHER
                sw_phase.character_changed[i] = True
                continue
            if c == Role.ANY_OTHER_MINION:
                sw_phase.characters[i] = Role.ANY_OTHER_EVIL
                sw_phase.character_changed[i] = True

        sw_world = sw_world if World._validate_world(sw_world) else None

        return non_sw_world, sw_world

    def killed_by_demon(self: World, player: int, night: int) -> tuple[World, World | None]:
        try:
            phase: Phase = self.get_phase(night)
        except PhaseNotFoundError:
            phase: Phase = self.add_phase(night)

        phase.dead[player] = True
        
        non_sp_world: World = copy.deepcopy(self)
        non_sp_phase = non_sp_world.get_phase(night)

        # dead player is a non-demon
        if phase.characters[player] == Role.ANY_OTHER:
            non_sp_phase.characters[player] = Role.NON_DEMON
        elif phase.characters[player] == Role.ANY_OTHER_EVIL:
            non_sp_phase.characters[player] = Role.ANY_OTHER_MINION

        # also update all previous phases
        for n in range(1, night):
            prev_non_sp_phase = non_sp_world.get_phase(n)
            if prev_non_sp_phase.characters[player] == Role.ANY_OTHER:
                prev_non_sp_phase.characters[player] = Role.NON_DEMON
            elif prev_non_sp_phase.characters[player] == Role.ANY_OTHER_EVIL:
                prev_non_sp_phase.characters[player] = Role.ANY_OTHER_MINION

        non_sp_world = non_sp_world if World._validate_world(non_sp_world) else None

        if phase.characters[player] == Role.IMP:
            non_sp_world = None

        ## worlds where a starpass is not possible
        # known non-demon player killed by demon
        if phase.characters[player] in [Role.NON_DEMON] + GOOD_CHARACTERS + MINIONS:
            return non_sp_world, None
        
        # all minions are dead already
        dead_minions = [c for i,c in enumerate(phase.characters) if phase.dead[i] and c in MINIONS + [Role.ANY_OTHER_MINION]]
        if len(dead_minions) >= len(phase.minion_types):
            return non_sp_world, None
        
        # none of the alive players could be a minion
        alive_potential_minions = [c for c in compress(phase.characters,[not x for x in phase.dead]) if c in MINIONS + [Role.ANY_OTHER_MINION, Role.ANY_OTHER_EVIL, Role.ANY_OTHER, Role.NON_DEMON]]
        if len(alive_potential_minions) == 0:
            return non_sp_world, None
        
        # no room in minion types
        if not any(c in phase.minion_types for c in MINIONS + [Role.ANY_OTHER_MINION]):
            return non_sp_world, None
        
        ## a starpass is possible
        sp_world = copy.deepcopy(self)
        sp_phase = sp_world.get_phase(night)

        # dead player was the imp
        sp_phase.characters[player] = Role.IMP
        sp_phase.star_passed = True

        # also update all previous phases
        for n in range(1, night):
            prev_phase = sp_world.get_phase(n)
            prev_phase.characters[player] = Role.IMP

        # if there's a known scarlet woman, they become the demon
        try:
            idx = sp_phase.characters.index(Role.SCARLET_WOMAN)
            sp_phase.characters[idx] = Role.IMP
            sp_phase.character_changed[idx] = True
            return non_sp_world, sp_world
        except:
            pass

        # single alive minion becomes the demon
        alive_known_minions = [c for c in compress(sp_phase.characters,[not x for x in sp_phase.dead]) if c in MINIONS + [Role.ANY_OTHER_MINION]]
        if len(alive_potential_minions) == 1 or len(alive_known_minions) == 1:
            for i,c in enumerate(sp_phase.characters):
                if sp_phase.dead[i]:
                    continue
                if c in alive_known_minions or (len(alive_potential_minions) == 1 and c in alive_potential_minions):
                    sp_phase.characters[i] = Role.IMP
                    sp_phase.character_changed[i] = True
                    return non_sp_world, sp_world

        # non-demons become any role
        # any other minions become any other evil
        for i,c in enumerate(sp_phase.characters):
            if sp_phase.dead[i]:
                continue
            if c == Role.NON_DEMON:
                sp_phase.characters[i] = Role.ANY_OTHER
                sp_phase.character_changed[i] = True
            if c == Role.ANY_OTHER_MINION:
                sp_phase.characters[i] = Role.ANY_OTHER_EVIL
                sp_phase.character_changed[i] = True

        sp_world = sp_world if World._validate_world(sp_world) else None

        return non_sp_world, sp_world
    
    def killed_by_slayer(self: World, target: int, night: int) -> tuple[World | None, World | None]:
        try:
            phase = self.get_phase(night)
        except PhaseNotFoundError:
            phase = self.add_phase(night)

        phase.dead[target] = True

        recluse_world = copy.deepcopy(self)
        recluse_phase = recluse_world.get_phase(night)

        if recluse_phase.characters[target] != Role.RECLUSE and recluse_phase.characters[target] != Role.ANY_OTHER_OUTSIDER and \
         recluse_phase.characters[target] != Role.ANY_OTHER_GOOD and recluse_phase.characters[target] != Role.ANY_OTHER:
            # target cannot be the recluse
            recluse_world = None
        else:
            recluse_phase.characters[target] = Role.RECLUSE
            for n in range(1,night):
                phase = recluse_world.get_phase(n)
                phase.characters[target] = Role.RECLUSE

        # make sure the world is sill valid
        if recluse_world is not None and not World._validate_world(recluse_world):
            recluse_world = None

        demon_world = copy.deepcopy(self)
        demon_phase = demon_world.get_phase(night)
        
        # target cannot be the imp
        if demon_phase.characters[target] != Role.IMP and demon_phase.characters[target] != Role.ANY_OTHER_EVIL and \
         demon_phase.characters[target] != Role.ANY_OTHER:
            return recluse_world, None
        
        demon_phase.characters[target] = Role.IMP
        for n in range(1,night):
            phase = demon_world.get_phase(n)
            phase.characters[target] = Role.IMP

        # known scarlet woman is dead already
        if any(c == Role.SCARLET_WOMAN for c in compress(demon_phase.characters,[x for x in demon_phase.dead])):
            return recluse_world, None
        
        # all minions are dead already
        dead_minions = [c for i,c in enumerate(demon_phase.characters) if demon_phase.dead[i] and c in MINIONS + [Role.ANY_OTHER_MINION]]
        if len(dead_minions) >= len(demon_phase.minion_types):
            return recluse_world, None

        # none of the alive players could be a scarlet woman
        if not any(c in compress(demon_phase.characters,[not x for x in demon_phase.dead]) for c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.NON_DEMON, Role.SCARLET_WOMAN]):
            return recluse_world, None

        # minion type becomes scarlet woman
        try:
            demon_phase.add_minion_type(Role.SCARLET_WOMAN)
            for n in range(1, night):
                prev_phase = demon_world.get_phase(n)
                prev_phase.add_minion_type(Role.SCARLET_WOMAN)
        except ValueError:
            return recluse_world, None

        # if there's a known scarlet woman, they become the demon
        try:
            idx = demon_phase.characters.index(Role.SCARLET_WOMAN)
            demon_phase.characters[idx] = Role.IMP
            demon_phase.character_changed[idx] = True
            return recluse_world, demon_world
        except:
            pass

        # single alive minion becomes the demon
        alive_known_minions = [c for c in compress(demon_phase.characters,[not x for x in demon_phase.dead]) if c == Role.ANY_OTHER_MINION]
        if len(alive_known_minions) == 1:
            for i,c in enumerate(demon_phase.characters):
                if demon_phase.dead[i]:
                    continue
                if c in alive_known_minions:
                    demon_phase.characters[i] = Role.IMP
                    demon_phase.character_changed[i] = True
                    for n in range(1, night):
                        prev_phase = demon_world.get_phase(n)
                        prev_phase.characters[i] = Role.SCARLET_WOMAN
                    return recluse_world, demon_world

        # if all minions are accounted for, there cannot be NON_DEMON roles, so any NON_DEMON roles could be potential scarlet women
        for i,c in enumerate(demon_phase.characters):
            if demon_phase.dead[i]:
                continue
            if c == Role.NON_DEMON:
                demon_phase.characters[i] = Role.ANY_OTHER
                demon_phase.character_changed[i] = True
                continue
            if c == Role.ANY_OTHER_MINION:
                demon_phase.characters[i] = Role.ANY_OTHER_EVIL
                demon_phase.character_changed[i] = True

        demon_world = demon_world if World._validate_world(demon_world) else None

    
    @staticmethod
    def _validate_world(world: World) -> bool:
        for phase in world.phases:
            valid = all([
                World._validate_character_counts(phase, world.phases[0], len(phase.characters)),
                World._validate_minion_types(phase)])
            if not valid:
                return False
        return True
    
    @classmethod
    def combine(cls, w1: Self, w2: Self) -> tuple[Self, bool]:
        if len(w1.phases[0].characters) != len(w2.phases[0].characters):
            raise Exception("You are trying to combine world with different numbers of players. Something has gone terribly wrong.")
        num_players = len(w1.phases[0].characters)
        new_world = cls(num_players)
        w1_copy = copy.deepcopy(w1)
        w2_copy = copy.deepcopy(w2)

        for night in range(1, max(w1.phases[-1].night, w2.phases[-1].night)+1):
            p1 = None
            p2 = None
            try:
                p1 = w1_copy.get_phase(night)
            except PhaseNotFoundError:
                pass
            try:
                p2 = w2_copy.get_phase(night)
            except PhaseNotFoundError:
                pass

            if p1 is None and p2 is None:
                continue
            if p1 is None:
                new_world.phases.append(copy.deepcopy(p2))
                continue
            if p2 is None:
                new_world.phases.append(copy.deepcopy(p1))
                continue

            if night > 1:
                new_phase: Phase = Phase(num_players, night)
                new_world.phases.append(new_phase)
            else: 
                new_phase = new_world.phases[0]

            if not World._combine_phases(new_world.phases[0], new_phase, num_players, p1, p2):
                return w1, False
            
            World._make_deductions(new_phase, num_players)
            
        if not World._pass_through_phases(new_world):
            return w1, False

        return new_world, True

    @staticmethod
    def _combine_phases(phase_0: Phase, new_phase: Phase, num_players: int, p1: Phase, p2: Phase):
        # Minion types
        if not World._combine_minion_types(new_phase, p1, p2):
            return False

        for i in range(num_players):
            c1, c2 = p1.characters[i], p2.characters[i]
            result = World._combine_characters(c1, c2, p1)
            if result is None:
                return False
            new_phase.characters[i] = result

        # Make sure the minions match the minion types
        if not World._validate_minion_types(new_phase):
            return False

        # Combine and validate chef numbers
        if not World._combine_chef_number(new_phase, p1, p2, num_players):
            return False
        
        if not World._combine_deaths(new_phase, p1, p2, num_players):
            return False

        # Poisoner logic
        if not World._combine_poisoned(new_phase, p1, p2, num_players):
            return False

        # Outsider, evil and good count checks
        if not World._validate_character_counts(new_phase, phase_0, num_players):
            return False
        
        # Check if there's more than one red herring or if the red herring is on an evil player
        if not World._combine_red_herring(new_phase, p1, p2, num_players):
            return False

        return True

    @staticmethod
    def _combine_minion_types(new_phase: Phase, p1: Phase, p2: Phase):
        if len(p1.minion_types) != len(p2.minion_types):
            raise Exception('Trying to combine phases with different numbers of minions. Something has gone terribly wrong.')
        
        # combine the two lists of minions, remove duplicates and ANY_OTHER_MINION
        unique_minions = list(set(p1.minion_types + p2.minion_types) - set([Role.ANY_OTHER_MINION]))

        # if the resulting list of minions is greater than either phase allows, that's an invalid world
        if len(unique_minions) > len(p1.minion_types):
            return False
        
        # add back in ANY_OTHER_MINION until we're at the right number of minions
        while len(unique_minions) < len(p1.minion_types):
            unique_minions.append(Role.ANY_OTHER_MINION)

        new_phase.minion_types = unique_minions
        return True

    @staticmethod
    def _combine_characters(c1: Role, c2: Role, p1: Phase):
        if c1 == c2:
            return c1
        if c1 not in ANY_OTHER_ROLES:
            return World._combine_specific_character(c1, c2)
        if c1 == Role.ANY_OTHER_EVIL:
            return World._combine_any_evil(c2, p1)
        if c1 == Role.ANY_OTHER_GOOD:
            return World._combine_any_good(c2, p1)
        if c1 == Role.ANY_OTHER_MINION:
            return World._combine_any_other_minion(c2, p1)
        if c1 == Role.ANY_OTHER_TOWNSFOLK:
            return World._combine_any_other_townsfolk(c2, p1)
        if c1 == Role.ANY_OTHER_OUTSIDER:
            return World._combine_any_other_outsider(c2, p1)
        if c1 == Role.NON_DEMON:
            return World._combine_non_demon(c2, p1)
        if c1 == Role.ANY_OTHER:
            return World._combine_any_other(c2, p1)
        return None

    @staticmethod
    def _combine_specific_character(c1: Role, c2: Role):
        if c2 not in ANY_OTHER_ROLES and c2 != c1:
            return None
        if c2 == Role.ANY_OTHER_EVIL and c1 in EVIL_CHARACTERS:
            return c1
        if c2 == Role.ANY_OTHER_GOOD and c1 in GOOD_CHARACTERS:
            return c1
        if c2 == Role.ANY_OTHER_MINION and c1 in MINIONS:
            return c1
        if c2 == Role.ANY_OTHER_OUTSIDER and c1 in OUTSIDERS:
            return c1
        if c2 == Role.ANY_OTHER_TOWNSFOLK and c1 in TOWNSFOLK:
            return c1
        if c2 == Role.NON_DEMON and c1 != Role.IMP:
            return c1
        if c2 in [Role.ANY_OTHER, c1]:
            return c1
        return None

    @staticmethod
    def _combine_any_evil(c2: Role, p1: Phase):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_EVIL
        if c2 == Role.ANY_OTHER_GOOD:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return c2
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_MINION
        if c2 not in EVIL_CHARACTERS:
            return None
        if c2 == Role.IMP:
            return c2
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_good(c2: Role, p1: Phase):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_GOOD
        if c2 == Role.ANY_OTHER_EVIL:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return None
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return c2
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_GOOD
        if c2 not in GOOD_CHARACTERS:
            return None
        if p1.drunk_token is not None and c2 == p1.drunk_token:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other_minion(c2: Role, p1: Phase):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_MINION
        if c2 == Role.ANY_OTHER_GOOD:
            return None
        if c2 == Role.ANY_OTHER_EVIL:
            return Role.ANY_OTHER_MINION
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_MINION
        if c2 not in MINIONS:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other_townsfolk(c2: Role, p1: Phase):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_TOWNSFOLK
        if c2 == Role.ANY_OTHER_GOOD:
            return Role.ANY_OTHER_TOWNSFOLK
        if c2 == Role.ANY_OTHER_EVIL:
            return None
        if c2 == Role.ANY_OTHER_OUTSIDER:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_TOWNSFOLK
        if c2 not in TOWNSFOLK:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other_outsider(c2: Role, p1: Phase):
        if c2 == Role.ANY_OTHER:
            return Role.ANY_OTHER_OUTSIDER
        if c2 == Role.ANY_OTHER_GOOD:
            return Role.ANY_OTHER_OUTSIDER
        if c2 == Role.ANY_OTHER_EVIL:
            return None
        if c2 == Role.ANY_OTHER_TOWNSFOLK:
            return None
        if c2 == Role.ANY_OTHER_MINION:
            return None
        if c2 == Role.NON_DEMON:
            return Role.ANY_OTHER_OUTSIDER
        if c2 not in OUTSIDERS:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_non_demon(c2: Role, p1: Phase):
        if c2 == Role.ANY_OTHER:
            return Role.NON_DEMON
        if c2 == Role.ANY_OTHER_EVIL:
            return Role.ANY_OTHER_MINION
        if c2 == Role.ANY_OTHER_GOOD:
            return Role.NON_DEMON
        if c2 == Role.ANY_OTHER_MINION:
            return c2
        if c2 == Role.ANY_OTHER_TOWNSFOLK or c2 == Role.ANY_OTHER_OUTSIDER:
            return c2
        if c2 == Role.IMP:
            return None
        if p1.drunk_token is not None and c2 == p1.drunk_token:
            return None
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _combine_any_other(c2: Role, p1: Phase):
        if c2 in ANY_OTHER_ROLES:
            return c2
        if p1.drunk_token is not None and c2 == p1.drunk_token:
            return None
        if c2 == Role.IMP:
            return c2
        if c2 in p1.characters:
            return None
        return c2

    @staticmethod
    def _validate_minion_types(phase: Phase):
        for c in phase.characters:
            if c not in MINIONS or c in phase.minion_types:
                continue
            try:
                # if there's room to replace ANY_OTHER_MINION with the specific character, do it. Otherwise, not a valid world
                idx = phase.minion_types.index(Role.ANY_OTHER_MINION)
                phase.minion_types[idx] = c
            except ValueError:
                return False
        return True

    @staticmethod
    def _combine_chef_number(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        if p1.chef_number is not None and p2.chef_number is not None and p1.chef_number is not p2.chef_number:
            return False
        
        new_phase.chef_number = p1.chef_number if p1.chef_number is not None else p2.chef_number
        if new_phase.chef_number is None:
            return True
        
        characters = new_phase.characters
        # set a minimum number of non-Spy evil pairs
        minimum = 0
        for i in range(num_players):
            j = (i+1) % num_players
            if characters[i] in EVIL_CHARACTERS and characters[i] != Role.SPY and characters[j] in EVIL_CHARACTERS and characters[j] != Role.SPY:
                minimum += 1

        possible_numbers = [minimum]
        maximum = minimum
        for i in range(num_players):
            j = (i+1) % num_players
            if (characters[i] in EVIL_CHARACTERS or characters[i] == Role.RECLUSE) and (characters[j] in EVIL_CHARACTERS or characters[j] == Role.RECLUSE):
                maximum += 1
                possible_numbers.append(maximum)

        return new_phase.chef_number in possible_numbers

    @staticmethod
    def _combine_poisoned(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        for i in range(num_players):
            new_phase.poisoned[i] = p1.poisoned[i] or p2.poisoned[i]
        # don't allow 2 instances of poisoning
        if sum([int(p) for p in new_phase.poisoned]) > 1:
            return False
        # return false if no room for poisoner
        if any(new_phase.poisoned) and Role.POISONER not in new_phase.minion_types and Role.ANY_OTHER_MINION not in new_phase.minion_types:
            return False
        # return false if known poisoner or all minions are dead
        if Role.POISONER in compress(new_phase.characters,new_phase.dead):
            return False
        if sum([x for x in compress(new_phase.characters,new_phase.dead) if x == Role.ANY_OTHER_MINION]) == ROLE_BREAKDOWNS[num_players]['minions']:
            return False

        return True

    @staticmethod
    def _validate_character_counts(new_phase: Phase, phase_0: Phase, num_players: int):
        return World._validate_outsider_count(phase_0, num_players) and World._validate_evil_count(new_phase, num_players) and World._validate_good_count(new_phase, num_players)

    @staticmethod
    def _validate_outsider_count(phase_0: Phase, num_players: int):
        # librarian told no outsiders
        if phase_0.no_outsiders and World._num_characters_of_type(phase_0, OUTSIDERS) > 0:
            return False
        # base outsider count or if a Baron is in play, base outsider count plus 2
        valid_counts = [ROLE_BREAKDOWNS[num_players]['outsiders']] if Role.BARON not in phase_0.minion_types else [ROLE_BREAKDOWNS[num_players]['outsiders']+2]
        # we don't know if a baron is in play, valid counts could be base and base plus 2
        if Role.BARON not in phase_0.minion_types and Role.ANY_OTHER_MINION in phase_0.minion_types:
            valid_counts.append(ROLE_BREAKDOWNS[num_players]['outsiders']+2)
        minimum = sum([1 if c in OUTSIDERS else 0 for c in phase_0.characters])
        maximum = minimum + sum([1 if c in [Role.ANY_OTHER_GOOD, Role.ANY_OTHER, Role.NON_DEMON] else 0 for c in phase_0.characters])
        # valid if any possible number of outsiders is in one of the valid counts
        return any([c in valid_counts for c in range(minimum, maximum+1)])

    @staticmethod
    def _validate_evil_count(new_phase: Phase, num_players: int):
        # validate room for evils
        potential_evils = World._num_characters_of_type(new_phase, EVIL_ROLES) + sum([1 if c in [Role.NON_DEMON, Role.ANY_OTHER] else 0 for c in new_phase.characters])
        if potential_evils < ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']:
            return False
        # validate room for imp
        potential_imps = sum([1 if c in [Role.IMP, Role.ANY_OTHER_EVIL, Role.ANY_OTHER] and not new_phase.dead[i] else 0 for i,c in enumerate(new_phase.characters)])
        if potential_imps == 0:
            return False
        # validate only 1 alive Imp
        if sum([1 if c == Role.IMP and not new_phase.dead[i] else 0 for i,c in enumerate(new_phase.characters)]) > 1:
            return False
        # validate not all evils are dead
        if sum([1 if c in EVIL_ROLES and new_phase.dead[i] else 0 for i,c in enumerate(new_phase.characters)]) >= ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']:
            return False
        if World._num_characters_of_type(new_phase, EVIL_ROLES) > ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons']:
            return False
        return True

    @staticmethod
    def _validate_good_count(new_phase: Phase, num_players: int):
        if World._num_characters_of_type(new_phase, GOOD_ROLES) > ROLE_BREAKDOWNS[num_players]['townsfolk'] + ROLE_BREAKDOWNS[num_players]['outsiders']:
            return False
        return True

    @staticmethod
    def _combine_red_herring(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        # combine the two phases
        for i in range(num_players):
            new_phase.red_herring[i] = p1.red_herring[i] or p2.red_herring[i]

        # more than one red herring
        if sum([int(x) for x in new_phase.red_herring]) > 1:
            return False

        # make sure the red herring doesn't belong to an evil player
        for i in range(num_players):
            if new_phase.red_herring[i] and new_phase.characters[i] in [Role.ANY_OTHER_EVIL, Role.ANY_OTHER_MINION, Role.IMP] + MINIONS:
                    return False
                
        return True

    @staticmethod
    def _combine_deaths(new_phase: Phase, p1: Phase, p2: Phase, num_players: int):
        # combine the phases
        for i in range(num_players):
            new_phase.dead[i] = p1.dead[i] or p2.dead[i]
        
        return True

    @staticmethod
    def _num_characters_of_type(phase: Phase, character_type: list[Role]):
        n = 0
        for character in phase.characters:
            if character in character_type:
                n += 1
        return n
    
    @staticmethod
    def _make_deductions(phase: Phase, num_players: int):
        deduced = True
        max_depth = 5
        d = 0
        while deduced and d < max_depth:
            deduced = World._deduction_step(phase, num_players)
            d += 1

    @staticmethod
    def _deduction_step(phase: Phase, num_players: int) -> bool:
        deduced = False

        # If no other spot for alive demon, assign demon
        alive_demon_candidates = [
            i for i, c in enumerate(phase.characters)
            if c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.IMP] and not phase.dead[i]
        ]
        if len(alive_demon_candidates) == 1 and phase.characters[alive_demon_candidates[0]] != Role.IMP:
            phase.characters[alive_demon_candidates[0]] = Role.IMP
            deduced = True
        
        # If no other spot for evils, assign evil
        evil_indices = [i for i, c in enumerate(phase.characters) if c in EVIL_ROLES]
        if ROLE_BREAKDOWNS[num_players]['minions'] + ROLE_BREAKDOWNS[num_players]['demons'] - len(evil_indices) > 0:
            if all(c in GOOD_ROLES or i in evil_indices for i,c in enumerate(phase.characters)):
                for i,c in enumerate(phase.characters):
                    if c == Role.ANY_OTHER:
                        phase.characters[i] = Role.ANY_OTHER_EVIL
                        deduced = True
                    if c == Role.NON_DEMON:
                        phase.characters[i] = Role.ANY_OTHER_MINION
                        deduced = True


        # If 2 evil players and one is known minion / demon, assign the opposite to the unknown evil
        evil_indices = [i for i, c in enumerate(phase.characters) if c in EVIL_ROLES]
        if len(evil_indices) == 2:
            roles = [phase.characters[i] for i in evil_indices]
            # If one is Imp and the other is ANY_OTHER_EVIL, assign the other as minion
            if Role.IMP in roles:
                for i in evil_indices:
                    if phase.characters[i] == Role.ANY_OTHER_EVIL:
                        phase.characters[i] = Role.ANY_OTHER_MINION
                        deduced = True
            # If one is a known minion and the other is ANY_OTHER_EVIL, assign the other as Imp
            elif any(r in MINIONS for r in roles) or Role.ANY_OTHER_MINION in roles:
                for i in evil_indices:
                    if phase.characters[i] == Role.ANY_OTHER_EVIL:
                        phase.characters[i] = Role.IMP
                        deduced = True

        # If all minion types are known and there is one player with the ANY_OTHER_MINION role, we can assign that player the unasigned minion type
        if Role.ANY_OTHER_MINION not in phase.minion_types:
            unassigned_types = list(set(phase.minion_types) - set([c for c in phase.characters if c in MINIONS]))
            if len(unassigned_types) == 1 and Role.ANY_OTHER_MINION in phase.characters:
                phase.characters[phase.characters.index(Role.ANY_OTHER_MINION)] = unassigned_types[0]
                deduced = True

        # TODO: If all minion players are known and there are one or more players with the NON_DEMON role, assign ANY_OTHER_GOOD to those players
                
        return deduced
    
    @staticmethod
    def _pass_through_phases(world: World) -> bool:
        for i in range(1, len(world.phases)):
            prev_phase = world.phases[i-1]
            curr_phase = world.phases[i]

            # pass characters
            star_pass_caught: float = 0
            for i in range(len(prev_phase.characters)):
                if curr_phase.character_changed[i]:
                    continue
                c1, c2 = curr_phase.characters[i], prev_phase.characters[i]
                if curr_phase.star_passed and c2 == Role.SCARLET_WOMAN:
                    c2 = Role.IMP
                    star_pass_caught = 1
                elif curr_phase.star_passed and c2 in MINIONS + [Role.ANY_OTHER_MINION] and star_pass_caught != 1:
                    c2 = Role.ANY_OTHER_EVIL
                    star_pass_caught += 1.0/ROLE_BREAKDOWNS[len(curr_phase.characters)]['minions']
                elif curr_phase.star_passed and c2 == Role.NON_DEMON and star_pass_caught != 1:
                    c2 = Role.ANY_OTHER
                result = World._combine_characters(c1, c2, curr_phase)
                if result is None:
                    return False
                curr_phase.characters[i] = result            

            # pass minion types
            for minion_type in prev_phase.minion_types:
                if minion_type in curr_phase.minion_types or minion_type == Role.ANY_OTHER_MINION:
                    continue
                try:
                    curr_phase.add_minion_type(minion_type)
                except ValueError:
                    return False
            
            # pass red herring
            for j, value in enumerate(prev_phase.red_herring):
                if value:
                    curr_phase.red_herring[j] = True
            
            if sum([int(x) for x in curr_phase.red_herring]) > 1:
                return False

            # pass drunk token
            if prev_phase.drunk_token is not None:
                if curr_phase.drunk_token is None:
                    curr_phase.drunk_token = prev_phase.drunk_token
                elif prev_phase.drunk_token != curr_phase.drunk_token:
                    return False                

            # pass chef number
            if prev_phase.chef_number is not None:
                if curr_phase.chef_number is None:
                    curr_phase.chef_number = prev_phase.chef_number
                elif prev_phase.chef_number != curr_phase.chef_number:
                    return False
                
        if not World._validate_world(world):
            return False

        return True

def combine_worlds(world_lists: list[list[World]]):
    starting_worlds: list[World] = world_lists[0]
    conflicting_worlds: list[list[World]] = []

    for i in range(1, len(world_lists)):
        valid_worlds: list[World] = []
        for w1 in starting_worlds:
            for w2 in world_lists[i]:
                combined_world, valid = World.combine(w1, w2)
                if valid: 
                    valid_worlds.append(combined_world)
                else:
                    conflicting_worlds.append([w1, w2])
        starting_worlds = valid_worlds[:]

    return starting_worlds, conflicting_worlds

def remove_duplicate_complete_worlds(world_list: list[World]) -> list[World]:
    culled_list = copy.copy(world_list)
    i=0
    while i < len(culled_list):
        w1_characters = culled_list[i].phases[-1].characters
        if any(c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.NON_DEMON] for c in w1_characters):
            i+=1
            continue
        j=i+1
        while j < len(culled_list):
            w2_characters = culled_list[j].phases[-1].characters
            if any(c in [Role.ANY_OTHER, Role.ANY_OTHER_EVIL, Role.ANY_OTHER_GOOD, Role.ANY_OTHER_MINION, Role.NON_DEMON] for c in w2_characters):
                j+=1
                continue
            if culled_list[i].phases[-1].characters == culled_list[j].phases[-1].characters:
                _ = culled_list.pop(j)
                continue
            j+=1
        i+=1

    return culled_list