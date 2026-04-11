from typing import TypedDict, Literal
from .role import Role

FIRST_NIGHT_INFO = {"investigator", "washerwoman", "librarian", "chef", "claim"}
ANY_NIGHT_INFO = {"fortune teller", "empath", "undertaker", "ravenkeeper", "virgin", "slayer"}

class DeathInfo(TypedDict):
    executed: list[tuple[int,int]]
    slayer_shot: tuple[int,int] | None
    killed_by_demon: list[tuple[int,int]]

class Claim(TypedDict):
    kind: Literal["claim"]
    player: int
    character: Role

class InvestigatorInfo(TypedDict):
    kind: Literal["investigator"]
    investigator: int
    first_player: int
    second_player: int
    minion: Role

class WasherwomanInfo(TypedDict):
    kind: Literal["washerwoman"]
    washerwoman: int
    first_player: int
    second_player: int
    townsfolk: Role

class LibrarianInfo(TypedDict):
    kind: Literal["librarian"]
    librarian: int
    first_player: int | None
    second_player: int | None
    token: Role | None

class ChefInfo(TypedDict):
    kind: Literal["chef"]
    chef: int
    number: int

class FortuneTellerInfo(TypedDict):
    kind: Literal["fortune teller"]
    fortune_teller: int
    night: int
    pings: tuple[tuple[int,int],bool]

class EmpathInfo(TypedDict):
    kind: Literal["empath"]
    empath: int
    number: int
    night: int
    left_neighbour: int
    right_neighbour: int    

class UndertakerInfo(TypedDict):
    kind: Literal["undertaker"]
    undertaker: int
    body: int
    token: Role
    night: int

class RavenkeeperInfo(TypedDict):
    kind: Literal["ravenkeeper"]
    ravenkeeper: int
    chosen: int
    token: Role
    night: int

class VirginInfo(TypedDict):
    kind: Literal["virgin"]
    virgin: int
    nominator: int
    executed: bool
    night: int

class SlayerInfo(TypedDict):
    kind: Literal["slayer"]
    slayer: int
    target: int
    successful: bool
    night: int

Info = (
    Claim |
    InvestigatorInfo |
    WasherwomanInfo |
    LibrarianInfo |
    ChefInfo |
    FortuneTellerInfo |
    EmpathInfo |
    UndertakerInfo |
    RavenkeeperInfo |
    VirginInfo |
    SlayerInfo
)