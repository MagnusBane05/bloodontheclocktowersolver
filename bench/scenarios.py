import argparse
from datetime import datetime
from enum import Enum
import json
import os
from pathlib import Path
import subprocess
from typing import Any, NamedTuple

from analyze.simulator import simulate_single_game
from grimoire import Grimoire, GrimoirePage, NightOrderPosition, Role, validators
from grimoire.info import DeathInfo, Info

from .tiers import TIERS

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
SEED_START = 193

# enums are stored by name so adding or reordering roles doesn't change saved scenarios
_ENUMS: dict[str, type[Enum]] = {
    "Role": Role,
    "NightOrderPosition": NightOrderPosition,
}

class Scenario(NamedTuple):
    id: str
    seed: int
    info: list[Info]
    deaths: list[DeathInfo]
    true_grim: Grimoire
    nights: int

def _encode(value: Any) -> Any:
    # Role and NightOrderPosition are IntEnums, which json would silently write as ints,
    # so they have to be converted before json.dumps sees them
    if isinstance(value, Enum):
        return {"__enum__": f"{type(value).__name__}.{value.name}"}
    if isinstance(value, tuple):
        return {"__tuple__": [_encode(v) for v in value]}
    if isinstance(value, list):
        return [_encode(v) for v in value]
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    return value

def _decode_hook(d: dict[str, Any]) -> Any:
    if "__enum__" in d:
        type_name, member = d["__enum__"].split(".")
        if type_name not in _ENUMS:
            raise ValueError(f"Unknown enum type {type_name} in scenario file")
        return _ENUMS[type_name][member]
    if "__tuple__" in d:
        return tuple(d["__tuple__"])
    return d

def encode_grim(grim: Grimoire) -> dict[str, Any]:
    return {
        "num_players": grim.num_players,
        "pages": [_encode(vars(page)) for page in grim.pages],
    }

def decode_grim(data: dict[str, Any]) -> Grimoire:
    num_players = data["num_players"]
    grim = Grimoire(num_players)
    grim.pages = []
    grim.keys = []
    for fields in data["pages"]:
        page = GrimoirePage(num_players, fields["night"], fields["night_order_position"])
        known_fields = vars(page)
        for field, value in fields.items():
            if field not in known_fields:
                raise ValueError(
                    f"Scenario page field '{field}' no longer exists on GrimoirePage. " +
                    "Regenerate the scenarios as a new version."
                )
            setattr(page, field, value)
        grim.pages.append(page)
        grim.keys.append(Grimoire._page_key(page)) # pyright: ignore[reportPrivateUsage]
    return grim

def _encode_game(seed: int, info: list[Info], deaths: list[DeathInfo], true_grim: Grimoire) -> dict[str, Any]:
    return {
        "seed": seed,
        "info": _encode(info),
        "deaths": _encode(deaths),
        "true_grim": encode_grim(true_grim),
    }

def _decode_game(players: int, index: int, game: dict[str, Any]) -> Scenario:
    true_grim = decode_grim(game["true_grim"])
    return Scenario(
        id=f"{players}p-{index:04d}",
        seed=game["seed"],
        info=game["info"],
        deaths=game["deaths"],
        true_grim=true_grim,
        nights=len(true_grim.get_unique_nights()),
    )

def _scenario_path(players: int, version: str) -> Path:
    return SCENARIOS_DIR / version / f"{players}p.json"

def load_scenarios(players: int, version: str = "v1", limit: int | None = None) -> list[Scenario]:
    path = _scenario_path(players, version)
    if not path.exists():
        raise FileNotFoundError(
            f"No {version} scenarios for {players} players at {path}. " +
            f"Run `python -m bench.scenarios generate --version {version}`."
        )
    with open(path) as f:
        data = json.load(f, object_hook=_decode_hook)

    if data["players"] != players or data["version"] != version:
        raise ValueError(
            f"{path} contains {data['version']} scenarios for {data['players']} players, " +
            f"expected {version} for {players}."
        )

    games = data["games"]
    # never quietly run fewer games than asked for, otherwise results aren't comparable
    if limit is not None:
        if limit > len(games):
            raise ValueError(f"Requested {limit} {players} player scenarios but {path} only has {len(games)}.")
        games = games[:limit]

    return [_decode_game(players, i, game) for i, game in enumerate(games)]

def _pages_equal(g1: Grimoire, g2: Grimoire) -> bool:
    # GrimoirePage.__eq__ only compares some fields, so compare every field
    return (
        len(g1.pages) == len(g2.pages)
        and all(vars(p1) == vars(p2) for p1, p2 in zip(g1.pages, g2.pages))
        and g1.keys == g2.keys
    )

def _scenario_count(players: int) -> int:
    return max(tier[players] for tier in TIERS.values())

def _git_state() -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
    ).stdout.strip() != ""
    return commit, dirty

def generate(players: int, version: str, force: bool = False, git_state: tuple[str, bool] | None = None) -> Path:
    """git_state is (commit, dirty). Pass it in when generating several files, since writing
    one file would otherwise make the tree look dirty for the next."""
    path = _scenario_path(players, version)
    if path.exists() and not force:
        raise FileExistsError(
            f"{path} already exists. Use a new --version, or --force to overwrite it."
        )

    count = _scenario_count(players)
    games: list[dict[str, Any]] = []
    for i in range(count):
        seed = SEED_START + i
        (info, deaths), true_grim = simulate_single_game(players, None, seed)

        valid, reason = validators.is_grim_valid(true_grim)
        if not valid:
            raise RuntimeError(f"Simulated {players} player game with seed {seed} is invalid: {reason}")

        game = _encode_game(seed, info, deaths, true_grim)
        # make sure the game survives a round trip before anything is written
        decoded = json.loads(json.dumps(game), object_hook=_decode_hook)
        if (
            decoded["info"] != info
            or decoded["deaths"] != deaths
            or not _pages_equal(decode_grim(decoded["true_grim"]), true_grim)
        ):
            raise RuntimeError(f"{players} player game with seed {seed} doesn't survive a save/load round trip")
        games.append(game)

    commit, dirty = git_state if git_state is not None else _git_state()
    data = {
        "version": version,
        "players": players,
        "seed_start": SEED_START,
        "count": count,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "commit": commit,
        "dirty": dirty,
        "games": games,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(tmp_path, path)
    return path

def main():
    parser = argparse.ArgumentParser(description="Benchmark scenario files")
    subparsers = parser.add_subparsers(dest="command", required=True)
    gen = subparsers.add_parser("generate", help="Generate scenario files from the simulator")
    _ = gen.add_argument("--version", default="v1")
    _ = gen.add_argument("--players", type=int, nargs="+", default=sorted(next(iter(TIERS.values())).keys()))
    _ = gen.add_argument("--force", action="store_true", help="Overwrite existing scenario files")
    args = parser.parse_args()

    if args.command == "generate":
        # check once, before any files are written
        git_state = _git_state()
        if git_state[1]:
            print("Warning: the working tree has uncommitted changes, so these scenarios may not be reproducible.")
        for players in args.players:
            path = generate(players, args.version, args.force, git_state)
            size_kb = path.stat().st_size / 1024
            print(f"{players} players: {_scenario_count(players)} games -> {path} ({size_kb:.0f} KB)")

if __name__ == "__main__":
    main()
