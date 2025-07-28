"""
Automates updating the static files.
Now saves both the raw CSV and the generated JSON files.
If new files need to be added, then place them in the TARGETS list.
"""
import aiohttp
import asyncio
import json
import traceback
import urllib
import urllib.request
import logging
import zstandard
import lzma
import csv
import os
import zipfile
from collections import defaultdict

TARGETS = [
    ("logic/buildings.csv", "buildings.csv"),
    ("logic/traps.csv", "traps.csv"),
    ("logic/mini_levels.csv", "supercharges.csv"),
    ("logic/seasonal_defense_archetypes.csv", "seasonal_defense_archetypes.csv"),
    ("logic/seasonal_defense_modules.csv", "seasonal_defense_modules.csv"),
    ("logic/special_abilities.csv", "special_abilities.csv"),
    ("logic/characters.csv", "characters.csv"),
    ("logic/heroes.csv", "heroes.csv"),
    ("logic/pets.csv", "pets.csv"),
    ("logic/spells.csv", "spells.csv"),
    ("logic/super_licences.csv", "supers.csv"),
    ("logic/townhall_levels.csv", "townhall_levels.csv"),
    ("logic/character_items.csv", "equipment.csv"),
    ("logic/obstacles.csv", "obstacles.csv"),
    ("logic/decos.csv", "decos.csv"),
    ("logic/building_parts.csv", "clan_capital_parts.csv"),
    ("logic/skins.csv", "skins.csv"),
    ("logic/village_backgrounds.csv", "sceneries.csv"),
    ("localization/texts.csv", "translations/texts_EN.csv"),
]

supported_languages = [
    "ar", "cn", "cnt", "de", "es", "fa", "fi", "fr", "id", "it", "jp", "kr",
    "ms", "nl", "no", "pl", "pt", "ru", "th", "tr", "vi"
]

for language in supported_languages:
    TARGETS.append((f"localization/{language}.csv", f"translations/texts_{language}.csv"))

APK_URL = "https://d.apkpure.net/b/APK/com.supercell.clashofclans?version=latest"

def get_fingerprint():
    async def download():
        async with aiohttp.request('GET', APK_URL) as fp:
            c = await fp.read()
        return c

    data = asyncio.run(download())

    with open("apk.zip", "wb") as f:
        f.write(data)
    zf = zipfile.ZipFile("apk.zip")
    with zf.open('assets/fingerprint.json') as fp:
        fingerprint = json.loads(fp.read())['sha']

    os.unlink("apk.zip")
    return fingerprint


def decompress(data):
    """
    Decompresses the given bytes 'data' if needed (LZHAM, ZSTD, or LZMA).
    Returns (decompressed_bytes, compression_details).
    """
    if data[0:4] == b"SCLZ":
        logging.debug("Decompressing using LZHAM ...")
        import lzham

        dict_size = int.from_bytes(data[4:5], byteorder="big")
        uncompressed_size = int.from_bytes(data[5:9], byteorder="little")

        decompressed = lzham.decompress(data[9:], uncompressed_size, {"dict_size_log2": dict_size})
        return decompressed, {
            "dict_size": dict_size,
            "uncompressed_size": uncompressed_size,
        }

    import zstandard
    if int.from_bytes(data[0:4], byteorder="little") == zstandard.MAGIC_NUMBER:
        logging.debug("Decompressing using ZSTD ...")
        decompressed = zstandard.decompress(data)
        return decompressed, {
            "dict_size": None,
            "uncompressed_size": None,
        }

    # Otherwise, assume LZMA
    logging.debug("Decompressing using LZMA ...")
    data = data[0:9] + (b"\x00" * 4) + data[9:]
    prop = data[0]
    o_prop = prop
    if prop > (4 * 5 + 4) * 9 + 8:
        raise Exception("LZMA properties error")
    import lzma
    decompressed = lzma.LZMADecompressor().decompress(data)
    return decompressed, {"lzma_prop": o_prop}


def process_csv(data, file_path, save_name):
    """
    1. Decompress data -> raw CSV
    2. Write raw CSV to disk
    3. Parse disk CSV -> final_data
    4. Post-process, flatten single-level troops
    5. Write out JSON
    6. Delete the CSV file
    """
    decompressed_data, _ = decompress(data)

    # 1) Write out the raw CSV
    with open(file_path, "wb") as f:
        f.write(decompressed_data)

    # 2) Read & parse it
    with open(file_path, encoding='utf-8') as csvf:
        rows = list(csv.reader(csvf))

    if len(rows) < 2:
        with open(f"{save_name}.json", "w", encoding="utf-8") as jf:
            jf.write("{}")
        # delete the csv before returning
        try:
            os.remove(file_path)
        except OSError as e:
            logging.warning(f"Could not delete {file_path}: {e}")
        return

    columns = rows[0]
    final_data = {}
    current_troop = None
    current_level = None

    # 3) Build final_data
    for row in rows[2:]:
        if not row:
            continue
        if row[0].strip():
            current_troop = row[0].strip()
        if len(row) > 1 and row[1].strip():
            current_level = row[1].strip()
        if not (current_troop and current_level):
            continue

        troop_dict = final_data.setdefault(current_troop, {})
        level_dict = troop_dict.setdefault(current_level, {})

        for idx, col_name in enumerate(columns):
            if idx < len(row):
                val = row[idx].strip()
                if not val:
                    continue
                if val.lower() == "true":
                    conv = True
                elif val.lower() == "false":
                    conv = False
                elif val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
                    conv = int(val)
                else:
                    conv = val
                level_dict[col_name] = conv

    # 4) Promote base-only columns
    for troop, levels in list(final_data.items()):
        lvls = sorted(levels.keys(), key=lambda x: int(x) if x.isdigit() else 999999)
        if len(lvls) > 1:
            base = lvls[0]
            for col in list(levels[base].keys()):
                if not any(col in levels[l] for l in lvls[1:]):
                    final_data[troop][col] = levels[base][col]
                    del levels[base][col]

    # 5) Flatten single-level troops
    for troop in list(final_data.keys()):
        levels = final_data[troop]
        if isinstance(levels, dict) and len(levels) == 1:
            only, data_dict = next(iter(levels.items()))
            if isinstance(data_dict, dict):
                final_data[troop] = data_dict

    # 6) Write JSON
    with open(f"{save_name}.json", "w", encoding="utf-8") as jf:
        jf.write(json.dumps(final_data, indent=2))

    # ---- new: delete the CSV file ----
    try:
        os.remove(file_path)
    except OSError as e:
        logging.warning(f"Could not delete {file_path}: {e}")


def check_header(data):
    if data[0] == 0x5D:
        return "csv"
    if data[:2] == b"\x53\x43":
        return "sc"
    if data[:4] == b"\x53\x69\x67\x3a":
        return "sig:"
    if data[:6] == b'"Name"' or data[:6] == b'"name"':
        return "decoded csv"
    raise Exception("Unknown header")


def master_json():

    with open(f"translations/texts_EN.json", "r", encoding="utf-8") as f:
        full_translation_data: dict = json.load(f)

    other_translations = []
    for language in supported_languages:
        with open(f"translations/texts_{language}.json", "r", encoding="utf-8") as f:
            other_translations.append((language, json.load(f)))

    with open(f"buildings.json", "r", encoding="utf-8") as f:
        full_building_data: dict = json.load(f)

    with open(f"characters.json", "r", encoding="utf-8") as f:
        full_troop_data: dict = json.load(f)

    with open(f"traps.json", "r", encoding="utf-8") as f:
        full_trap_data: dict = json.load(f)

    with open(f"decos.json", "r", encoding="utf-8") as f:
        full_deco_data: dict = json.load(f)

    with open(f"obstacles.json", "r", encoding="utf-8") as f:
        full_obstacle_data: dict = json.load(f)

    with open(f"pets.json", "r", encoding="utf-8") as f:
        full_pet_data: dict = json.load(f)

    with open(f"heroes.json", "r", encoding="utf-8") as f:
        full_hero_data: dict = json.load(f)

    with open(f"clan_capital_parts.json", "r", encoding="utf-8") as f:
        full_capital_part_data: dict = json.load(f)

    with open(f"equipment.json", "r", encoding="utf-8") as f:
        full_equipment_data: dict = json.load(f)

    with open(f"special_abilities.json", "r", encoding="utf-8") as f:
        full_abilities_data: dict = json.load(f)

    with open(f"sceneries.json", "r", encoding="utf-8") as f:
        full_scenery_data: dict = json.load(f)

    with open(f"skins.json", "r", encoding="utf-8") as f:
        full_skin_data: dict = json.load(f)

    new_translation_data = {}
    for translation_key, translation_data in full_translation_data.items():
        new_translation_data[translation_key] = {"EN" : translation_data.get("EN")}
        for lang, language_data in other_translations:
            new_translation_data[translation_key][lang.upper()] = language_data.get(translation_key).get(lang.upper())

    #BUILDING JSON BUILD
    new_building_data = []
    for _id, (building_name, building_data) in enumerate(full_building_data.items(), 1000000):
        if building_data.get("BuildingClass") in ["Npc", "NonFunctional", "Npc Town Hall"] or "Unused" in building_name:
            continue
        resource_TID = f'TID_{building_data.get("BuildResource")}'.upper()
        village_type = building_data.get("VillageType", 0)

        hold_data = {
            "_id" : _id,
            "name": new_translation_data.get(building_data.get("TID")).get("EN"),
            "info": new_translation_data.get(building_data.get("InfoTID")).get("EN"),
            "TID": {
                "name": building_data.get("TID"),
                "info": building_data.get("InfoTID"),
            },
            "type": building_data.get("BuildingClass"),
            "upgrade_resource": new_translation_data.get(resource_TID, {}).get("EN"),
            "village_type": "home" if not village_type else "builder_base",
            "width" : building_data.get("Width"),
            "levels" : []
        }
        for level, level_data in building_data.items():
            if not isinstance(level_data, dict):
                continue
            upgrade_time_seconds = level_data.get("BuildTimeD", 0) * 24 * 60 * 60
            upgrade_time_seconds += level_data.get("BuildTimeH", 0) * 60 * 60
            upgrade_time_seconds += level_data.get("BuildTimeM", 0) * 60
            upgrade_time_seconds += level_data.get("BuildTimeS", 0)
            hold_data["levels"].append({
                "level": level_data.get("BuildingLevel"),
                "upgrade_cost": level_data.get("BuildCost"),
                "upgrade_time": upgrade_time_seconds,
                "required_townhall": level_data.get("TownHallLevel"),
                "hitpoints": level_data.get("Hitpoints"),
                "dps": level_data.get("DPS"),
            })

        new_building_data.append(hold_data)

    #TROOP JSON BUILD
    lab_data = next((item for item in new_building_data if item["name"] == "Laboratory")).get("levels")
    lab_to_townhall = {spot : level_data.get("required_townhall") for spot, level_data in enumerate(lab_data, 1)}
    lab_to_townhall[-1] = 1 # there are troops with no lab ...
    lab_to_townhall[0] = 2

    blacksmith_data = next((item for item in new_building_data if item["name"] == "Blacksmith")).get("levels")
    smithy_to_townhall = {spot : level_data.get("required_townhall") for spot, level_data in enumerate(blacksmith_data, 1)}

    pet_house_data = next((item for item in new_building_data if item["name"] == "Pet House")).get("levels")
    pethouse_to_townhall = {spot: level_data.get("required_townhall") for spot, level_data in enumerate(pet_house_data, 1)}

    bb_lab_data = next((item for item in new_building_data if item["name"] == "Star Laboratory")).get("levels")
    bb_lab_to_townhall = {spot: level_data.get("required_townhall") for spot, level_data in enumerate(bb_lab_data, 1)}

    new_troop_data = []
    for _id, (troop_name, troop_data) in enumerate(full_troop_data.items(), 4000000):
        if troop_data.get("DisableProduction", False):
            continue
        village_type = troop_data.get("VillageType", 0)
        production_building = full_building_data.get(troop_data.get("ProductionBuilding")).get("TID")
        resource_TID = f'TID_{troop_data.get("UpgradeResource")}'.upper()
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(troop_data.get("TID")).get("EN"),
            "info": new_translation_data.get(troop_data.get("InfoTID")).get("EN"),
            "TID": {
                "name": troop_data.get("TID"),
                "info": troop_data.get("InfoTID"),
            },
            "production_building": new_translation_data.get(production_building).get("EN"),
            "production_building_level": troop_data.get("BarrackLevel"),
            "upgrade_resource": new_translation_data.get(resource_TID, {}).get("EN"),

            "is_flying": troop_data.get("IsFlying"),
            "is_air_targeting": troop_data.get("AirTargets"),
            "is_ground_targeting": troop_data.get("GroundTargets"),

            "movement_speed": troop_data.get("Speed"),

            "attack_speed": troop_data.get("AttackSpeed"),
            "attack_range": troop_data.get("AttackRange"),
            "housing_space": troop_data.get("HousingSpace"),
            "village_type": "home" if not village_type else "builder_base",
        }
        is_super_troop = troop_data.get("EnabledBySuperLicence", False)
        is_seasonal_troop = troop_data.get("EnabledByCalendar", False)
        if is_super_troop:
            hold_data["is_super_troop"] = True

        if is_seasonal_troop:
            hold_data["is_seasonal_troop"] = True
        hold_data["levels"] = []

        max_townhall_converter = lab_to_townhall

        if troop_data.get("ProductionBuilding") == "Barrack2":
            max_townhall_converter = bb_lab_to_townhall

        for level, level_data in troop_data.items():
            if not isinstance(level_data, dict):
                continue
            #convert times to seconds, all times for all things will be in seconds
            upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60

            required_townhall = None
            if not is_super_troop and not is_seasonal_troop:
                required_townhall = max_townhall_converter[level_data.get("LaboratoryLevel")]

            new_level_data = {
                "level": int(level),
                "hitpoints": level_data.get("Hitpoints"),
                "dps": level_data.get("DPS"),

                "upgrade_time": upgrade_time_seconds,
                "upgrade_cost": level_data.get("UpgradeCost", 0),
                "required_lab_level": level_data.get("LaboratoryLevel"),
                "required_townhall": required_townhall,
            }
            hold_data["levels"].append(new_level_data)

        if not hold_data["levels"]:
            continue
        new_troop_data.append(hold_data)

    #BUILD HERO JSON
    new_hero_data = []
    for _id, (hero_name, hero_data) in enumerate(full_hero_data.items(), 28000000):
        resource = hero_data.get("UpgradeResource")
        resource = resource if resource != "DarkElixir" else "Dark_Elixir"
        village_type = hero_data.get("VillageType", 0)
        resource_TID = f'TID_{resource}'.upper()
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(hero_data.get("TID")).get("EN"),
            "info": new_translation_data.get(hero_data.get("InfoTID")).get("EN"),
            "TID": {
                "name": hero_data.get("TID"),
                "info": hero_data.get("InfoTID"),
            },
            "production_building": new_translation_data.get("TID_HERO_TAVERN").get("EN") if not village_type else None,
            "production_building_level": hero_data.get("1", {}).get("RequiredHeroTavernLevel"),
            "upgrade_resource": new_translation_data.get(resource_TID).get("EN"),

            "is_flying": hero_data.get("IsFlying"),
            "is_air_targeting": hero_data.get("AirTargets"),
            "is_ground_targeting": hero_data.get("GroundTargets"),

            "movement_speed": hero_data.get("Speed"),
            "attack_speed": hero_data.get("AttackSpeed"),
            "attack_range": hero_data.get("AttackRange"),
            "village_type": "home" if not village_type else "builder_base",
            "levels": []
        }

        for level, level_data in hero_data.items():
            if not isinstance(level_data, dict):
                continue
            # convert times to seconds, all times for all things will be in seconds
            upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60

            new_level_data = {
                "level": int(level),
                "hitpoints": level_data.get("Hitpoints"),
                "dps": level_data.get("DPS"),

                "upgrade_time": upgrade_time_seconds,
                "upgrade_cost": level_data.get("UpgradeCost", 0),

                "required_townhall": level_data.get("RequiredTownHallLevel"),
                "required_hero_tavern_level": level_data.get("RequiredHeroTavernLevel"),
            }
            hold_data["levels"].append(new_level_data)

        new_hero_data.append(hold_data)


    #BUILD PET JSON
    new_pet_data = []
    for _id, (pet_name, pet_data) in enumerate(full_pet_data.items(), 73000000):
        if pet_data.get("Deprecated", False) or pet_name in ["PhoenixEgg"]:
            continue

        resource_TID = f'TID_DARK_ELIXIR'.upper()
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(pet_data.get("TID")).get("EN"),
            "info": new_translation_data.get(pet_data.get("InfoTID")).get("EN"),
            "TID": {
                "name": pet_data.get("TID"),
                "info": pet_data.get("InfoTID"),
            },
            "production_building": new_translation_data.get("TID_PET_SHOP").get("EN"),
            "production_building_level": pet_data.get("1").get("LaboratoryLevel"),
            "upgrade_resource": new_translation_data.get(resource_TID).get("EN"),

            "is_flying": pet_data.get("IsFlying"),
            "is_air_targeting": pet_data.get("AirTargets"),
            "is_ground_targeting": pet_data.get("GroundTargets"),

            "movement_speed": pet_data.get("Speed"),
            "attack_speed": pet_data.get("AttackSpeed"),
            "attack_range": pet_data.get("AttackRange"),
            "levels" : []
        }

        for level, level_data in pet_data.items():
            if not isinstance(level_data, dict):
                continue
            # convert times to seconds, all times for all things will be in seconds
            upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60


            new_level_data = {
                "level": int(level),
                "hitpoints": level_data.get("Hitpoints"),
                "dps": level_data.get("DPS"),

                "upgrade_time": upgrade_time_seconds,
                "upgrade_cost": level_data.get("UpgradeCost", 0),
                "lab_level": level_data.get("LaboratoryLevel"),
                "required_townhall": pethouse_to_townhall[level_data.get("LaboratoryLevel")],
            }
            hold_data["levels"].append(new_level_data)

        new_pet_data.append(hold_data)

    # BUILD EQUIPMENT JSON
    new_equipment_data = []
    for _id, (equipment_name, equipment_data) in enumerate(full_equipment_data.items(), 90000000):
        if equipment_data.get("Deprecated", False):
            continue

        main_abilities = equipment_data.get("MainAbilities").split(";")
        extra_abilities = equipment_data.get("ExtraAbilities", "").split(";")
        hero_TID = full_hero_data.get(equipment_data.get("AllowedCharacters").split(";")[0]).get("TID")
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(equipment_data.get("TID")).get("EN"),
            "info": new_translation_data.get(equipment_data.get("InfoTID")).get("EN"),
            "TID": {
                "name": equipment_data.get("TID"),
                "info": equipment_data.get("InfoTID"),
                "production_building": "TID_SMITHY",
            },
            "production_building": new_translation_data.get("TID_SMITHY").get("EN"),
            "production_building_level": equipment_data.get("1").get("RequiredBlacksmithLevel"),
            "rarity": equipment_data.get("Rarity"),
            "hero": new_translation_data.get(hero_TID).get("EN"),
            "levels": []
        }

        for level, level_data in equipment_data.items():
            if not isinstance(level_data, dict):
                continue
            # convert times to seconds, all times for all things will be in seconds
            upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60


            shiny_ore = 0
            glowy_ore = 0
            starry_ore = 0
            upgrade_resources = level_data.get("UpgradeResources", "").split(";")
            upgrade_costs = str(level_data.get("UpgradeCosts", "")).split(";")

            if upgrade_costs[0] != "":
                for resource, cost in zip(upgrade_resources, upgrade_costs):
                    cost = int(cost)
                    if resource == "CommonOre":
                        shiny_ore += cost
                    elif resource == "RareOre":
                        glowy_ore += cost
                    elif resource == "EpicOre":
                        starry_ore += cost

            new_level_data = {
                "level": int(level),
                "hitpoints": level_data.get("Hitpoints"),
                "dps": level_data.get("DPS"),
                "heal_on_activation" : level_data.get("HealOnActivation"),

                "upgrade_time": upgrade_time_seconds,
                "upgrade_cost": level_data.get("UpgradeCost", 0),
                "required_blacksmith_level": level_data.get("RequiredBlacksmithLevel"),
                "required_townhall": smithy_to_townhall[level_data.get("RequiredBlacksmithLevel")],
            }

            main_ability_levels = str(level_data.get("MainAbilityLevels", "")).split(";")

            if main_ability_levels[0] != "":
                main_ability_json = []
                for main_ability, main_ability_level in zip(main_abilities, main_ability_levels):
                    full_ability = full_abilities_data.get(main_ability)
                    ability = full_ability.get(main_ability_level)
                    ability["name"] = new_translation_data.get(full_ability.get("TID")).get("EN")
                    ability["info"] = new_translation_data.get(full_ability.get("InfoTID")).get("EN")
                    main_ability_json.append(ability)

                if main_ability_json:
                    new_level_data["main_abilities"] = main_ability_json

            extra_ability_levels = str(level_data.get("ExtraAbilityLevels", "")).split(";")
            if extra_ability_levels[0] != "":
                extra_ability_json = []
                for extra_ability, extra_ability_level in zip(extra_abilities, extra_ability_levels):
                    full_ability = full_abilities_data.get(extra_ability)
                    ability = full_ability.get(extra_ability_level)
                    if ability:
                        ability["name"] = new_translation_data.get(full_ability.get("TID")).get("EN")
                        extra_ability_json.append(ability)

                if extra_ability_json:
                    new_level_data["extra_abilities"] = extra_ability_json

            hold_data["levels"].append(new_level_data)

        new_equipment_data.append(hold_data)


    #TRAP JSON BUILD
    new_trap_data = []
    for _id, (trap_name, trap_data) in enumerate(full_trap_data.items(), 12000000):
        if trap_data.get("Disabled", False) or trap_data.get("EnabledByCalendar", False):
            continue
        resource_TID = f'TID_{trap_data.get("BuildResource")}'.upper()
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(trap_data.get("TID")).get("EN"),
            "info": new_translation_data.get(trap_data.get("InfoTID")).get("EN"),
            "TID" : {
                "name" : trap_data.get("TID"),
                "info" : trap_data.get("InfoTID"),
            },
            "width": trap_data.get("Width"),
            "air_trigger": trap_data.get("AirTrigger", False),
            "ground_trigger": trap_data.get("GroundTrigger", False),
            "damage_radius": trap_data.get("DamageRadius"),
            "trigger_radius": trap_data.get("TriggerRadius"),

            "upgrade_resource": new_translation_data.get(resource_TID).get("EN"),
            "levels" : []
        }
        for level, level_data in trap_data.items():
            if not isinstance(level_data, dict):
                continue
            upgrade_time_seconds = level_data.get("BuildTimeD", 0) * 24 * 60 * 60
            upgrade_time_seconds += level_data.get("BuildTimeH", 0) * 60 * 60
            upgrade_time_seconds += level_data.get("BuildTimeM", 0) * 60
            upgrade_time_seconds += level_data.get("BuildTimeS", 0)

            hold_data["levels"].append({
                "level": int(level),
                "upgrade_cost": level_data.get("BuildCost"),
                "upgrade_time": upgrade_time_seconds,
                "required_townhall": level_data.get("TownHallLevel"),
                "damage": level_data.get("Damage"),
            })

        new_trap_data.append(hold_data)

    #DECORATION JSON BUILD
    new_deco_data = []
    for _id, (deco_name, deco_data) in enumerate(full_deco_data.items(), 18000000):
        if deco_data.get("TID") in ["TID_DECORATION_GENERIC", "TID_DECORATION_NATIONAL_FLAG"]:
            continue
        village_type = deco_data.get("VillageType", 0)
        resource_TID = f'TID_{deco_data.get("BuildResource")}'.upper()
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(deco_data.get("TID")).get("EN"),
            "TID": {
                "name": deco_data.get("TID"),
            },
            "width": deco_data.get("Width"),
            "not_in_shop": deco_data.get("NotInShop"),
            "pass_reward": deco_data.get("BPReward"),
            "max_count": deco_data.get("MaxCount", 1),
            "build_resource": new_translation_data.get(resource_TID).get("EN"),
            "build_cost": deco_data.get("BuildCost"),
            "village_type": "home" if not village_type else "builder_base"
        }
        new_deco_data.append(hold_data)

    #CLAN CAPITAL HOUSE JSON BUILD
    new_capital_part_data = []
    for _id, (part_name, part_data) in enumerate(full_capital_part_data.items(), 82000000):
        if part_data.get("Deprecated", False):
            continue

        new_capital_part_data.append({
            "_id": _id,
            "name": new_translation_data.get(part_data.get("TID")).get("EN"),
            "TID": {
                "name": part_data.get("TID"),
            },
            "slot_type": part_data.get("LayoutSlot"),
            "pass_reward": part_data.get("BattlePassReward", False),
        })

    # OBSTACLES JSON BUILD
    new_obstacle_data = []
    for _id, (obstacle_name, obstacle_data) in enumerate(full_obstacle_data.items(), 8000000):
        village_type = obstacle_data.get("VillageType", 0)
        clear_resource_TID = f'TID_{obstacle_data.get("ClearResource")}'.upper()
        loot_resource_TID = f'TID_{obstacle_data.get("LootResource")}'.upper()

        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(obstacle_data.get("TID")).get("EN"),
            "TID": {
                "name": obstacle_data.get("TID"),
            },
            "width": obstacle_data.get("Width"),
            "clear_resource": new_translation_data.get(clear_resource_TID).get("EN"),
            "clear_cost": obstacle_data.get("ClearCost"),
            "loot_resource": new_translation_data.get(loot_resource_TID, {}).get("EN"),
            "loot_count": obstacle_data.get("LootCount"),
            "village_type": "home" if not village_type else "builder_base"
        }
        new_obstacle_data.append(hold_data)

    #SCENERIES JSON BUILD
    new_scenery_data = []
    for _id, (scenery_name, scenery_data) in enumerate(full_scenery_data.items(), 60000000):
        type_map = {
            "WAR" : "war",
            "BB" : "builder_base",
            "HOME" : "home"
        }
        if scenery_data.get("HomeType") not in type_map:
            continue

        if new_translation_data.get(scenery_data.get("TID"), {}).get("EN") is None:
            continue
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(scenery_data.get("TID")).get("EN"),
            "TID": {
                "name": scenery_data.get("TID"),
            },
            "type": type_map.get(scenery_data.get("HomeType")),
            "music" : scenery_data.get("Music"),
        }
        if  scenery_data.get("FreeBackground", False):
            scenery_data["free"] = True
        if scenery_data.get("DefaultBackground", False):
            scenery_data["default"] = True

        new_scenery_data.append(hold_data)

    #SKINS JSON BUILD
    new_skins_data = []
    for _id, (skin_name, skin_data) in enumerate(full_skin_data.items(), 52000000):
        character = skin_data.get("character") or skin_data.get("Character")
        if not skin_data.get("TID") or character not in full_hero_data.keys():
            continue
        hold_data = {
            "_id": _id,
            "name": new_translation_data.get(skin_data.get("TID")).get("EN"),
            "TID": {
                "name": skin_data.get("TID"),
            },
            "tier": skin_data.get("Tier"),
            "character" : character,
        }
        new_skins_data.append(hold_data)

    master_data = {
        "buildings": new_building_data,
        "traps" : new_trap_data,
        "troops": new_troop_data,
        "heroes": new_hero_data,
        "pets": new_pet_data,
        "equipment": new_equipment_data,
        "decorations": new_deco_data,
        "obstacles": new_obstacle_data,
        "sceneries": new_scenery_data,
        "skins": new_skins_data,
        "capital_house_parts": new_capital_part_data,
    }
    with open(f"static_data.json", "w", encoding="utf-8") as jf:
        jf.write(json.dumps(master_data, indent=2))

    with open(f"translations.json", "w", encoding="utf-8") as jf:
        jf.write(json.dumps(new_translation_data, indent=2))


def main():
    # Hard-code or fallback
    FINGERPRINT = get_fingerprint()
    BASE_URL = f"https://game-assets.clashofclans.com/{FINGERPRINT}"
    for target_file, target_save in TARGETS:
        target_save = target_file if target_save is None else target_save
        download_url = f"{BASE_URL}/{target_file}"

        print(f"Downloading: {download_url}")
        with urllib.request.urlopen(download_url, timeout=10) as conn:
            data = conn.read()

        # Save raw compressed data
        with open(target_save, "wb") as f:
            f.write(data)

        file_type = check_header(data)
        if file_type == "csv":
            # data is already uncompressed CSV
            process_csv(data=data, file_path=target_save, save_name=target_save.split(".")[0])
        elif file_type == "sig:":
            # skip first 68 bytes, then decompress
            process_csv(data=data[68:], file_path=target_save, save_name=target_save.split(".")[0])
        else:
            # treat as compressed
            process_csv(data=data, file_path=target_save, save_name=target_save.split(".")[0])

if __name__ == "__main__":
    main()
    #master_json()
