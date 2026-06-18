import os
import sys
from pathlib import Path
import typing

from flask import Flask, request, jsonify
from flask_cors import CORS

from grimoire.gamerules import ROLE_BREAKDOWNS

# Add the parent directory to the path so we can import grimoire
sys.path.insert(0, str(Path(__file__).parent.parent))

from grimoire import GrimoireManager, Grimoire, Game
from grimoire.role import ROLE_CATEGORIES, Role, MINIONS, TOWNSFOLK, CHARACTER_STRINGS, EVIL_ROLES, GOOD_ROLES
from grimoire.info import Info

app = Flask(__name__)
CORS(app)

# Role enum to string mapping
ROLE_TO_STRING = {key: value for key, value in CHARACTER_STRINGS.items()}
STRING_TO_ROLE = {value: key for key, value in CHARACTER_STRINGS.items()}

def serialize_grimoire(grimoire: Grimoire) -> dict[str, typing.Any]:
    """Convert a Grimoire object to a JSON-serializable dictionary."""
    pages: list[dict[str, typing.Any]] = []
    for page in grimoire.pages:
        page_data: dict[str, typing.Any] = {
            "night": page.night,
            "characters": [ROLE_TO_STRING.get(c, str(c)) for c in page.characters],
            "dead": page.dead,
            "redHerring": page.red_herring,
            "chefNumber": page.chef_number,
            "drunkToken": ROLE_TO_STRING.get(page.drunk_token) if page.drunk_token else None,
            "minionTypes": [ROLE_TO_STRING.get(m, str(m)) for m in page.minion_types],
            "noOutsiders": page.no_outsiders,
            "poisoned": page.poisoned
        }
        pages.append(page_data)
    
    return {
        "pages": pages,
    }

def parse_role(role_str: str) -> Role | None:
    """Convert a string to a Role enum value."""
    return STRING_TO_ROLE.get(role_str)

def parse_info(info_dict: dict[str, typing.Any]) -> Info | None:
    """Parse a JSON object into an Info TypedDict."""
    # Convert role strings to Role enums
    info_copy: dict[str, typing.Any] = info_dict.copy()
    
    # Handle kind-specific role fields
    kind = info_dict.get("kind")
    
    role_fields = {
        "investigator": ["minion"],
        "washerwoman": ["townsfolk"],
        "librarian": ["token"],
        "chef": [],
        "claim": ["character"],
        "fortune_teller": [],
        "empath": [],
        "undertaker": ["token"],
        "ravenkeeper": ["token"],
        "virgin": [],
        "slayer": [],
    }
    
    if kind in role_fields:
        for field in role_fields[kind]:
            if field in info_copy and info_copy[field]:
                role = parse_role(info_copy[field])
                if role:
                    info_copy[field] = role
    
    return info_copy

@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    """Return metadata about supported roles, info kinds, and player counts."""
    return jsonify({
        "roles": list(ROLE_TO_STRING.values()),
        "infoKinds": [
            "claim", "investigator", "washerwoman", "librarian", "chef",
            "fortune teller", "empath", "undertaker", "ravenkeeper", "virgin", "slayer"
        ],
        "minionRoles": [ROLE_TO_STRING[m] for m in MINIONS],
        "townsfolkRoles": [ROLE_TO_STRING[t] for t in TOWNSFOLK],
        "evilRoles": [ROLE_TO_STRING[r] for r in EVIL_ROLES],
        "goodRoles": [ROLE_TO_STRING[r] for r in GOOD_ROLES],
        "characterTypes": [ROLE_TO_STRING[r] for r in ROLE_CATEGORIES],
    })

@app.route("/api/solve", methods=["POST"])
def solve():
    """Solve the grimoire given game info and death info."""
    try:
        payload = request.get_json()
        
        players = payload.get("players")
        infos = payload.get("infos", [])
        death_info = payload.get("deathInfo")
        
        # Validate input
        if not players or players not in ROLE_BREAKDOWNS:
            return jsonify({"error": f"Invalid player count: {players}"}), 400
        
        if not death_info:
            return jsonify({"error": "Missing deathInfo"}), 400
        
        # Parse infos: convert role strings to Role enums
        parsed_infos: list[Info] = []
        for info in infos:
            parsed_info: Info | None = parse_info(info)
            if parsed_info is not None:
                parsed_infos.append(parsed_info)
        
        # Convert death_info role strings to Role enums where applicable
        # parsed_death_info: list[DeathInfo] = [{
        #     "player": death["player"],
        #     "night": death["night"],
        #     "kind": death["kind"],
        # } for death in death_info]
        
        # Infer nights from info
        max_night = 1
        for death in death_info:
            max_night = max(max_night, death["night"])
        # for _, night in death_info.get("killed_by_demon", []):
        #     max_night = max(max_night, night)
        # if death_info.get("slayer_shot"):
        #     max_night = max(max_night, death_info["slayer_shot"][1])
        for info in parsed_infos:
            if info["kind"] in ['undertaker', 'empath', 'fortune teller']:
                max_night = max(max_night, info["night"])
        nights = max_night
        
        # Run the solver
        game: Game = {"players": players}
        manager = GrimoireManager(game)
        manager.add_full_game(parsed_infos, death_info, nights)
        
        # Serialize results
        solutions = [serialize_grimoire(grim) for grim in manager.grims]
        
        return jsonify({
            "solutionCount": len(solutions),
            "solutions": solutions,
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    """Serve a simple health check."""
    return jsonify({"message": "Blood on the Clocktower Solver API"}), 200

if __name__ == "__main__":
    host = os.environ.get("APP_HOST", "127.0.0.1")
    app.run(debug=True, host=host, port=5000)
