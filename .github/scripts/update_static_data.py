"""
Update coc/static/static_data.json, coc/static/translations.json and coc/constants.py from
ClashKingInc/ClashKingAssets.

Usage (from the repo root): python .github/scripts/update_static_data.py
"""
import json
import urllib.request
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/ClashKingInc/ClashKingAssets/main/assets/"
ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "coc" / "static"

# the sections coc.py loads (see coc/game_data.py)
SECTIONS = [
    "buildings", "traps", "troops", "guardians", "spells", "heroes", "pets", "equipment", "decorations",
    "obstacles", "sceneries", "skins", "capital_house_parts", "helpers", "war_leagues", "league_tiers",
    "achievements",
]


def fetch(path):
    request = urllib.request.Request(SOURCE + path, headers={"User-Agent": "coc.py static data update"})
    with urllib.request.urlopen(request) as fp:
        return json.load(fp)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(json.dumps(data, separators=(",", ":")))


def add_equipment_abilities(static_data, abilities):
    """abilities.json has each equipment's abilities with one entry per equipment level; put them on
    the equipment levels, where coc.py reads them (Equipment.abilities)."""
    by_id = {item["_id"]: item["abilities"] for item in abilities["items"]}
    for equipment in static_data["equipment"]:
        item_abilities = by_id.get(equipment["_id"], [])
        for index, level in enumerate(equipment["levels"]):
            level["abilities"] = [
                {
                    **{k: v for k, v in ability.items() if k != "levels"},
                    **{k: v for k, v in ability["levels"][index].items() if k != "level"},
                }
                for ability in item_abilities
                if index < len(ability["levels"])
            ]


def keep_level_numbers(static_data, previous):
    """Some units (super troops, some builder base troops and heroes) start at a level above 1 in-game,
    which is what the API and account exports use. Where the source numbers them from 1 instead, shift
    them back to the numbering already in our static_data.json."""
    for section in ("troops", "spells", "heroes", "pets", "equipment"):
        previous_start = {
            item["_id"]: item["levels"][0]["level"] for item in previous.get(section, []) if item.get("levels")
        }
        for item in static_data[section]:
            start = previous_start.get(item["_id"])
            if not item.get("levels") or start is None:
                continue
            offset = start - item["levels"][0]["level"]
            if offset:
                for level in item["levels"]:
                    level["level"] += offset


def generate_constants(static_data):
    troops = static_data["troops"]
    spells = static_data["spells"]
    heroes = static_data["heroes"]
    equipment = static_data["equipment"]
    pets = static_data["pets"]
    buildings = static_data["buildings"]
    achievements = static_data["achievements"]

    lists_to_write = {
        'ELIXIR_TROOP_ORDER': [
            t["name"] for t in troops
            if t["production_building"] == "Barracks"
            and not t.get("is_seasonal", False)
            and "super_troop" not in t
        ],
        'DARK_ELIXIR_TROOP_ORDER': [
            t["name"] for t in troops
            if t["production_building"] == "Dark Barracks"
            and not t.get("is_seasonal", False)
            and "super_troop" not in t
        ],
        'HV_TROOP_ORDER': 'ELIXIR_TROOP_ORDER + DARK_ELIXIR_TROOP_ORDER',
        'SIEGE_MACHINE_ORDER': [t["name"] for t in troops if t["production_building"] == "Workshop"],
        'SUPER_TROOP_ORDER': [t["name"] for t in troops if "super_troop" in t],
        'HOME_TROOP_ORDER': 'HV_TROOP_ORDER + SIEGE_MACHINE_ORDER',
        'SEASONAL_TROOP_ORDER': [t["name"] for t in troops if t.get("is_seasonal", False)],
        'BUILDER_TROOPS_ORDER': [t["name"] for t in troops if t["village"] == "builderBase"],
        'ELIXIR_SPELL_ORDER': [
            s["name"] for s in spells
            if s["upgrade_resource"] == "Elixir"
            and not s.get("is_seasonal", False)
        ],
        'DARK_ELIXIR_SPELL_ORDER': [s["name"] for s in spells if s["upgrade_resource"] == "Dark Elixir"],
        'SEASONAL_SPELL_ORDER': [s["name"] for s in spells if s.get("is_seasonal", False)],
        'SPELL_ORDER': 'ELIXIR_SPELL_ORDER + DARK_ELIXIR_SPELL_ORDER',
        'HOME_BASE_HERO_ORDER': [
            h["name"] for h in sorted(heroes, key=lambda x: x["levels"][0]["required_townhall"])
            if h["village"] == "home"
        ],
        'BUILDER_BASE_HERO_ORDER': [h["name"] for h in heroes if h["village"] == "builderBase"],
        'HERO_ORDER': 'HOME_BASE_HERO_ORDER + BUILDER_BASE_HERO_ORDER',
        'PETS_ORDER': [p["name"] for p in pets],
        'EQUIPMENT': [e["name"] for e in equipment],
        'HV_BUILDINGS': [b["name"] for b in buildings if b["village"] == "home"],
        'ACHIEVEMENT_ORDER': [
            a["name"] for a in sorted(
                achievements,
                key=lambda x: ({'home': 0, 'builderBase': 1, 'clanCapital': 2}.get(x["village"], 0), -x["ui_priority"])
            )
        ],  # same order as in-game
    }

    with open(ROOT / "coc" / "constants.py", "w", encoding="utf-8") as f:
        f.write('"""Auto-generated constants from static game data."""\n\n')
        for name, lst in lists_to_write.items():
            if isinstance(lst, str):
                f.write(f"{name} = {lst}\n\n")
            else:
                f.write(f"{name} = [\n")
                for item in lst:
                    f.write(f"    {repr(item)},\n")
                f.write("]\n\n")


def main():
    source = fetch("static_data.json")
    static_data = {section: source.get(section, []) for section in SECTIONS}
    # keep a stable order by id, so the generated constants and name -> id lookups don't shuffle
    for items in static_data.values():
        if all(isinstance(item, dict) and "_id" in item for item in items):
            items.sort(key=lambda item: item["_id"])
    add_equipment_abilities(static_data, fetch("static_data/abilities.json"))
    with open(STATIC / "static_data.json", encoding="utf-8") as fp:
        previous = json.load(fp)
    keep_level_numbers(static_data, previous)

    write_json(STATIC / "static_data.json", static_data)
    write_json(STATIC / "translations.json", fetch("translations.json"))
    generate_constants(static_data)


if __name__ == "__main__":
    main()
