from .grimoire import Grimoire

from dataclasses import dataclass, field


@dataclass
class TrueGrimTrace:
    true_grim: Grimoire
    stage: str
    matching_branches: list[str] = field(default_factory=list) # type: ignore
    produced_count: int = 0

    def record_candidate(self, label: str, candidate: Grimoire):
        self.produced_count += 1
        if self.true_grim.loose_equals(candidate):
            self.matching_branches.append(label)