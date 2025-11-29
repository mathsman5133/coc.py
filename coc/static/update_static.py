"""
Automates updating the static files.
Now saves both the raw CSV and the generated JSON files.
If new files need to be added, then place them in the TARGETS list.
"""
import aiohttp
import asyncio
import json
import logging
import csv
import os
import zipfile
import zstandard
import lzma
from pathlib import Path

class StaticUpdater:
    def __init__(self):

        self.TARGETS = []
        self.supported_languages: list[str] = []
        self.USED_TIDS = set()

        # keep the raw CSV files
        self.KEEP_CSV = False
        # keep the raw JSON files
        self.KEEP_JSON = False
        # removes any TIDs not used in the static files
        self.PRUNE_TRANSLATIONS = True
        # base path for the static files to be stored in
        self.BASE_PATH = ""


        self.FINGERPRINT = "475cb6a2d13043762034ddd6a198bad23e0782eb"
        self.CLASH_VERSION = "" or "latest"
        self.VERSION_PARAM = "version" if self.CLASH_VERSION == "latest" else "versionCode"
        self.APK_URL = f"https://d.apkpure.net/b/APK/com.supercell.clashofclans?{self.VERSION_PARAM}={self.CLASH_VERSION}"

        self.translation_data = {}
        self.full_building_data = {}
        self.full_supercharges_data = {}
        self.full_abilities_data = {}
        self.full_hero_data = {}
        self.full_townhall_data = {}
        self.full_troop_data = {}
        self.full_resource_data = {}

        self.lab_to_townhall = {}
        self.smithy_to_townhall = {}
        self.bb_lab_to_townhall = {}
        self.pethouse_to_townhall = {}


    async def download(self, url: str, as_json: bool = False):
        async with aiohttp.request('GET', url) as fp:
            if as_json:
                c = await fp.json()
            else:
                c = await fp.read()
        return c

    async def get_fingerprint(self):
        data = await self.download(self.APK_URL)

        with open("apk.zip", "wb") as f:
            f.write(data)
        zf = zipfile.ZipFile("apk.zip")
        with zf.open('assets/fingerprint.json') as fp:
            fingerprint = json.loads(fp.read())['sha']

        os.remove("apk.zip")
        return fingerprint

    def decompress(self, data):
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
        decompressed = lzma.LZMADecompressor().decompress(data)
        return decompressed, {"lzma_prop": o_prop}

    def process_csv(self, data, file_path, save_name):
        """
        1. Decompress data -> raw CSV
        2. Write raw CSV to disk
        3. Parse disk CSV -> final_data with levels:
        - If columns[1] is an int-type (e.g. “Level”), use that for your level keys.
        - Otherwise auto-enumerate each row under the same troop as levels “1”, “2”, …
        4. Post-process:
        - Promote any column that only appears in level “1” up to troop-level.
        - If a troop ends up with only one level, flatten it.
        5. Write out JSON with (troop → levels + troop-level props).
        6. Delete the CSV file.
        """
        # Check if data is compressed
        if self.is_compressed(data):
            # Strip signature header if present (Sig: + 64 bytes signature)
            if data[:4] == b"Sig:":
                logging.debug("Stripping Sig: header and signature...")
                data = data[68:]  # Skip "Sig:" (4 bytes) + 64-byte signature
            decompressed_data, _ = self.decompress(data)
        else:
            decompressed_data = data

        # 1) Write out the raw CSV
        with open(file_path, "wb") as f:
            f.write(decompressed_data)

        # 2) Load rows and grab the header + type row
        with open(file_path, encoding="utf-8") as csvf:
            rows = list(csv.reader(csvf))
        if len(rows) < 2:
            with open(f"{save_name}.json", "w", encoding="utf-8") as jf:
                jf.write("{}")
            os.remove(file_path)
            return

        columns   = rows[0]
        types_row = rows[1]

        # detect if col[1] really is a numeric level
        is_numeric_level = (
            types_row[1].lower() == "int"
            or "level" in columns[1].lower()
        )

        final_data     = {}
        current_troop  = None
        level_counter  = None
        current_level  = None

        # 3) Parse & build final_data
        for row in rows[2:]:
            if not any(cell.strip() for cell in row):
                continue

            # new troop?
            if row[0].strip():
                current_troop = row[0].strip()
                final_data[current_troop] = {}
                # reset counters
                if not is_numeric_level:
                    level_counter = 1
                current_level = None

            if current_troop is None:
                continue

            # pick level key
            if is_numeric_level:
                # existing behavior: use col[1]
                if len(row) > 1 and row[1].strip():
                    current_level = row[1].strip()
                if not current_level:
                    continue
                lvl_key = current_level
            else:
                # auto-enumerate each data-row
                lvl_key = str(level_counter)
                level_counter += 1

            # grab/create dict for this level
            level_dict = final_data[current_troop].setdefault(lvl_key, {})

            # fill in columns
            for idx, col_name in enumerate(columns):
                if idx >= len(row):
                    break
                val = row[idx].strip()
                if val == "":
                    continue
                low = val.lower()
                if low == "true":
                    conv = True
                elif low == "false":
                    conv = False
                elif val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
                    conv = int(val)
                else:
                    conv = val
                level_dict[col_name] = conv

        # 4a) Promote any base-level-only columns up to troop-level
        for troop, levels in list(final_data.items()):
            lvl_keys = sorted(levels.keys(), key=lambda x: int(x) if x.isdigit() else 999999)
            if len(lvl_keys) <= 1:
                continue
            base = lvl_keys[0]
            for col in list(levels[base].keys()):
                if not any(col in levels[l] for l in lvl_keys[1:]):
                    final_data[troop][col] = levels[base][col]
                    del levels[base][col]

        # 4b) Flatten troops with exactly one level
        for troop in list(final_data.keys()):
            levels = final_data[troop]
            if isinstance(levels, dict) and len(levels) == 1:
                only_lvl, data_dict = next(iter(levels.items()))
                if isinstance(data_dict, dict):
                    final_data[troop] = data_dict

        # 5) Write final JSON
        with open(f"{save_name}.json", "w", encoding="utf-8") as jf:
            json.dump(final_data, jf, indent=2)

        # 6) Delete the CSV
        if not self.KEEP_CSV:
            try:
                os.remove(file_path)
            except OSError as e:
                logging.warning(f"Could not delete {file_path}: {e}")

    def is_compressed(self, data):
        """Check if data is compressed by looking for compression signatures."""
        # Check for Sig: header (signed compressed data)
        if data[:4] == b"Sig:":
            return True
        # Check for SCLZ (LZHAM)
        if data[:4] == b"SCLZ":
            return True
        # Check for ZSTD magic number
        if len(data) >= 4 and int.from_bytes(data[0:4], byteorder="little") == zstandard.MAGIC_NUMBER:
            return True
        # Check for LZMA (starts with 0x5D)
        if data[0] == 0x5D:
            return True
        # Check for SC header (Supercell compression)
        if data[:2] == b"\x53\x43":
            return True
        # If it looks like plain CSV text, it's not compressed
        if data[:6] == b'"Name"' or data[:6] == b'"name"' or data[:5] == b'"TID"':
            return False
        # Default to compressed if we're not sure
        return True

    def open_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            data: dict = json.load(f)
        return data

    def _translate(self, tid: str):
        self.USED_TIDS.add(tid)
        return self.translation_data.get(tid, {}).get("EN")

    def _parse_resource(self, resource: str) -> str:
        resource_TID: str = self.full_resource_data.get(resource, {}).get("TID")
        return self._translate(resource_TID)

    def _parse_translation_data(self):
        full_translation_data = self.open_file("texts.json")
        other_translations = []
        for language in self.supported_languages:
            with open(f"texts_{language}.json", "r", encoding="utf-8") as f:
                other_translations.append((language, json.load(f)))

        new_translation_data = {}
        for translation_key, translation_data in full_translation_data.items():
            new_translation_data[translation_key] = {"EN": translation_data.get("EN")}
            for lang, language_data in other_translations:
                if not language_data.get(translation_key):
                    continue
                new_translation_data[translation_key][lang.upper()] = language_data.get(translation_key).get(
                    lang.upper())

        self.translation_data = new_translation_data
        return new_translation_data

    def _parse_achievement_data(self):
        self.full_achievement_data = self.open_file("achievements.json")
        new_achievement_data = {}
        for achievement_name, achievement_data in self.full_achievement_data.items():
            tid = achievement_data.get("TID")
            if tid not in new_achievement_data:
                new_achievement_data[tid] = {
                    "name": self._translate(achievement_data.get("TID")),
                    "info": self._translate(achievement_data.get("InfoTID")),
                    "completed_message": self._translate(achievement_data.get("CompletedTID")),
                    "TID": {
                        "name": achievement_data.get("TID"),
                        "info": achievement_data.get("InfoTID"),
                        "completed_message": achievement_data.get("CompletedTID"),
                    },
                    "levels" : [{
                        "level": achievement_data.get("Level") + 1,
                        "action_count": achievement_data.get("ActionCount"),
                        "action_data": achievement_data.get("ActionData"),
                        "xp": achievement_data.get("ExpReward", 0),
                        "gems": achievement_data.get("DiamondReward", 0)
                    }]
                }
            else:
                new_achievement_data[tid]["levels"].append({
                    "level": achievement_data.get("Level") + 1,
                    "action_count": achievement_data.get("ActionCount"),
                    "action_data": achievement_data.get("ActionData"),
                    "xp": achievement_data.get("ExpReward", 0),
                    "gems": achievement_data.get("DiamondReward", 0)
                })

        return list(new_achievement_data.values())

    def _parse_building_data(self):
        self.full_building_data = self.open_file("buildings.json")
        self.full_supercharges_data = self.open_file("mini_levels.json")
        self.full_townhall_data = self.open_file("townhall_levels.json")
        full_weapon_data: dict = self.open_file("weapons.json")

        new_building_data = []

        #fill in ids, make it easier
        for _id, (building_name, building_data) in enumerate(self.full_building_data.items(), 1000000):
            building_data["_id"] = _id

        for _id, (building_name, building_data) in enumerate(self.full_building_data.items(), 1000000):
            if building_data.get("BuildingClass") in ["Npc", "NonFunctional",
                                                      "Npc Town Hall"] or "Unused" in building_name:
                continue

            village_type = building_data.get("VillageType", 0)
            superchargeable = False

            supercharge_level_data = {}
            for supercharge_data in self.full_supercharges_data.values():
                if supercharge_data.get("TargetBuilding") == building_name:
                    superchargeable = True
                    hold_data = {
                        "upgrade_resource": self._parse_resource(resource=supercharge_data.get("BuildResource")),
                        "levels": []
                    }
                    for level, level_data in supercharge_data.items():
                        if not isinstance(level_data, dict):
                            continue
                        upgrade_time_seconds = level_data.get("BuildTimeD", 0) * 24 * 60 * 60
                        upgrade_time_seconds += level_data.get("BuildTimeH", 0) * 60 * 60
                        upgrade_time_seconds += level_data.get("BuildTimeM", 0) * 60
                        upgrade_time_seconds += level_data.get("BuildTimeS", 0)

                        DPS = level_data.get("DPS", 0)
                        # if the level doesnt have a DPS & there is no hitpoints for this row, that means it is a DPS upgrade
                        # unless it is a resource pump, but we dont handle those anyways
                        if not DPS and not level_data.get("Hitpoints"):
                            DPS = supercharge_data.get("DPS", 0)
                        hold_data["levels"].append({
                            "level": int(level),
                            "upgrade_cost": level_data.get("BuildCost"),
                            "upgrade_time": upgrade_time_seconds,
                            "hitpoints_buff": level_data.get("Hitpoints", 0),
                            "dps_buff": DPS,
                        })
                    supercharge_level_data = hold_data
                    break

            #for merged buildings, move the requirement to level 1 since that is when the requirement is actually needed
            if building_data.get("MergeRequirement") is not None:
                building_data["1"]["MergeRequirement"] = building_data.get("MergeRequirement")

            hold_data = {
                "_id": _id,
                "name": self._translate(tid=building_data.get("TID")),
                "info": self._translate(tid=building_data.get("InfoTID")),
                "TID": {
                    "name": building_data.get("TID"),
                    "info": building_data.get("InfoTID"),
                },
                "type": building_data.get("BuildingClass"),
                # we are going to do this purely for builder hut purposes bc lv 1 is gems
                "upgrade_resource": self._parse_resource(
                    resource=building_data.get("BuildResource") or building_data.get("2").get("BuildResource")
                ),
                "village": "home" if not village_type else "builderBase",
                "width": building_data.get("Width", 1), #walls are null for some reason, so let's make it 1
                "superchargeable": superchargeable,
                "levels": []
            }

            if building_data.get("GearUpLevelRequirement"):
                hold_data["gear_up"] = {
                    "level_required": building_data.get("GearUpLevelRequirement"),
                    "resource": self._parse_resource(resource=building_data.get("GearUpResource")),
                    "building_id": self.full_building_data.get(building_data.get("GearUpBuilding")).get("_id")
                }

            for level, level_data in building_data.items():
                if not isinstance(level_data, dict):
                    continue

                upgrade_time_seconds = level_data.get("BuildTimeD", 0) * 24 * 60 * 60
                upgrade_time_seconds += level_data.get("BuildTimeH", 0) * 60 * 60
                upgrade_time_seconds += level_data.get("BuildTimeM", 0) * 60
                upgrade_time_seconds += level_data.get("BuildTimeS", 0)

                hold_level_data = {
                    "level": level_data.get("BuildingLevel"),
                    "upgrade_cost": level_data.get("BuildCost", 0),
                    "upgrade_time": upgrade_time_seconds,
                    "required_townhall": level_data.get("TownHallLevel"),
                    "hitpoints": level_data.get("Hitpoints", 0),
                    "dps": level_data.get("DPS", 0) or level_data.get("Damage", 0),
                }

                if "AltBuildResource" in level_data:
                    # a wall specific thing since they can use gold + elixir at certain levels
                    hold_level_data["alt_upgrade_resource"] = self._parse_resource(resource=level_data["AltBuildResource"])

                if merge_requirement := level_data.get("MergeRequirement"):
                    merge_list = []
                    buildings = merge_requirement.split(";")
                    for building in buildings:
                        name, level, geared_up = building.split(":")
                        merge_building_data = self.full_building_data.get(name)
                        merge_list.append({
                            "name": self._translate(tid=merge_building_data.get("TID")),
                            "_id": merge_building_data.get("_id"),
                            "geared_up": True if geared_up == "1" else False,
                            "level": int(level)
                        })

                    hold_level_data["merge_requirement"] = merge_list

                if (weapon_name := level_data.get("Weapon")) is not None:

                    weapon_data: dict = full_weapon_data[weapon_name]

                    #if the townhall only has 1 level of weapon, then it is inherently part of the base level,
                    # so just set the dps and continue
                    if weapon_data.get("1") is None:
                        hold_level_data["dps"] = weapon_data.get("DPS")
                    else:
                        hold_weapon_data = {
                            "name": self._translate(tid=weapon_data["TID"]),
                            "info": self._translate(tid=weapon_data["InfoTID"]),
                            "TID": {
                                "name": weapon_data.get("TID"),
                                "info": weapon_data.get("InfoTID"),
                            },
                            "upgrade_resource": self._parse_resource(resource=building_data.get("BuildResource")),
                            "levels": []
                        }
                        for weapon_level, weapon_level_data in weapon_data.items():
                            if not isinstance(weapon_level_data, dict):
                                continue

                            upgrade_time_seconds = weapon_level_data.get("BuildTimeD", 0) * 24 * 60 * 60
                            upgrade_time_seconds += weapon_level_data.get("BuildTimeH", 0) * 60 * 60
                            upgrade_time_seconds += weapon_level_data.get("BuildTimeM", 0) * 60
                            upgrade_time_seconds += weapon_level_data.get("BuildTimeS", 0)

                            hold_weapon_data["levels"].append({
                                "level": weapon_level_data.get("Level"),
                                "upgrade_cost": level_data.get("BuildCost"),
                                "upgrade_time": upgrade_time_seconds,
                                "dps": weapon_level_data.get("DPS"),
                            })
                        hold_level_data["weapon"] = hold_weapon_data

                hold_data["levels"].append(hold_level_data)

            if superchargeable:
                #supercharges are always on the last available level
                hold_data["levels"][-1]["supercharge"] = supercharge_level_data
            new_building_data.append(hold_data)

        lab_data = next((item for item in new_building_data if item["name"] == "Laboratory")).get("levels")
        lab_to_townhall = {spot : level_data.get("required_townhall") for spot, level_data in enumerate(lab_data, 1)}
        lab_to_townhall[-1] = 1 # there are troops with no lab ...
        lab_to_townhall[0] = 2
        self.lab_to_townhall = lab_to_townhall

        blacksmith_data = next((item for item in new_building_data if item["name"] == "Blacksmith")).get("levels")
        self.smithy_to_townhall = {spot: level_data.get("required_townhall") for spot, level_data in
                              enumerate(blacksmith_data, 1)}

        pet_house_data = next((item for item in new_building_data if item["name"] == "Pet House")).get("levels")
        self.pethouse_to_townhall = {spot: level_data.get("required_townhall") for spot, level_data in
                                enumerate(pet_house_data, 1)}

        bb_lab_data = next((item for item in new_building_data if item["name"] == "Star Laboratory")).get("levels")
        self.bb_lab_to_townhall = {spot: level_data.get("required_townhall") for spot, level_data in
                              enumerate(bb_lab_data, 1)}

        townhall_unlocks, builderhall_unlocks = self._parse_hall_data()

        for building in new_building_data:
            unlocks = []
            if building["type"] == "Town Hall":
                unlocks = townhall_unlocks
            elif building["type"] == "Town Hall2":
                unlocks = builderhall_unlocks

            for unlock_data in unlocks:
                building["levels"][(unlock_data["level"] - 1)]["unlocks"] = unlock_data["buildings_unlocked"]

        return new_building_data

    def _parse_seasonal_defense_data(self):
        full_seasonal_defenses = self.open_file("seasonal_defense_archetypes.json")
        full_seasonal_modules = self.open_file("seasonal_defense_modules.json")
        full_season_data = self.open_file("seasonal_defense.json")

        seasons = []
        for season_data in full_season_data.values():
            seasons.append(season_data)

        current_season = next((item for item in reversed(seasons) if item.get("TID")), {})
        current_seasonal_defenses: list[str] = [v.get("Archetypes") for k, v in current_season.items() if k.isdigit()]

        for _id, (n, d) in enumerate(full_seasonal_modules.items(), 102000000):
            d["_id"] = _id

        current_max_townhall = int(list(self.full_townhall_data.keys())[-1])
        new_seasonal_defense_data = []
        for _id, (seasonal_def_name, seasonal_def_data) in enumerate(full_seasonal_defenses.items(), 103000000):

            if seasonal_def_name not in current_seasonal_defenses:
                continue

            season_defense_ability = self.full_abilities_data.get(seasonal_def_data.get("SpecialAbility"))

            name_TID = season_defense_ability.get("OverrideTID")
            info_TID = season_defense_ability.get("OverrideInfoTID")

            hold_data = {
                "_id": _id,
                "name": self._translate(tid=name_TID),
                "info": self._translate(tid=info_TID),
                "TID": {
                    "name": name_TID,
                    "info": info_TID,
                },
                "required_townhall": current_max_townhall,
                "modules" : []
            }
            for count, module in enumerate(seasonal_def_data.get("Modules").split(";"), 1):
                module_data = full_seasonal_modules.get(module)

                module_hold_data = {
                    "_id": module_data.get("_id"),
                    "name": self._translate(tid=module_data.get("TID")),
                    "TID": {
                        "name": module_data.get("TID"),
                    },
                    "upgrade_resource": self._parse_resource(module_data.get("BuildResource")),
                    "levels": []
                }
                for level, level_data in module_data.items():
                    if not isinstance(level_data, dict):
                        continue
                    upgrade_time_seconds = level_data.get("BuildTimeD", 0) * 24 * 60 * 60
                    upgrade_time_seconds += level_data.get("BuildTimeH", 0) * 60 * 60
                    upgrade_time_seconds += level_data.get("BuildTimeM", 0) * 60
                    upgrade_time_seconds += level_data.get("BuildTimeS", 0)

                    ability_data = self.full_abilities_data.get(module_data.get("SpecialAbility")).get(level)
                    ability_data.pop("ActivateFromGameSystem", None)
                    ability_data.pop("DeactivateFromGameSystem", None)
                    ability_data.pop("Level", None)

                    module_hold_data["levels"].append({
                        "level": int(level),
                        "upgrade_cost": level_data.get("BuildCost"),
                        "upgrade_time": upgrade_time_seconds,
                        "ability_data": ability_data
                    })

                hold_data["modules"].append(module_hold_data)

            new_seasonal_defense_data.append(hold_data)

        return new_seasonal_defense_data

    def _parse_troop_data(self):
        self.full_troop_data = self.open_file("characters.json")
        full_super_troop_data = self.open_file("super_licences.json")
        full_super_troop_data = {v.get("Replacement"): v for k, v in full_super_troop_data.items()}

        name_to_id = {}
        new_troop_data = []
        for _id, (troop_name, troop_data) in enumerate(self.full_troop_data.items(), 4000000):
            if troop_data.get("DisableProduction", False):
                continue
            village_type = troop_data.get("VillageType", 0)
            production_building = self.full_building_data.get(troop_data.get("ProductionBuilding")).get("TID")

            name_to_id[(troop_name, village_type)] = _id
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=troop_data.get("TID")),
                "info": self._translate(tid=troop_data.get("InfoTID")),
                "TID": {
                    "name": troop_data.get("TID"),
                    "info": troop_data.get("InfoTID"),
                },
                "production_building": self._translate(tid=production_building),
                "production_building_level": troop_data.get("BarrackLevel"),
                "upgrade_resource": self._parse_resource(resource=troop_data.get("UpgradeResource")),

                "is_flying": troop_data.get("IsFlying"),
                "is_air_targeting": troop_data.get("AirTargets"),
                "is_ground_targeting": troop_data.get("GroundTargets"),

                "movement_speed": troop_data.get("Speed", 0),

                "attack_speed": troop_data.get("AttackSpeed", 0),
                "attack_range": troop_data.get("AttackRange", 0),
                "housing_space": troop_data.get("HousingSpace"),
                "village": "home" if not village_type else "builderBase",
            }
            is_super_troop = troop_data.get("EnabledBySuperLicence", False)
            is_seasonal_troop = troop_data.get("EnabledByCalendar", False)
            super_troop_data = None
            if is_super_troop:
                super_troop_data = full_super_troop_data.get(troop_name)
                hold_data["super_troop"] = {"original_id": name_to_id[(super_troop_data["Original"], 0)],
                                            "original_min_level": super_troop_data["MinOriginalLevel"]}
            if is_seasonal_troop:
                hold_data["is_seasonal"] = True
            hold_data["levels"] = []

            max_townhall_converter = self.lab_to_townhall
            if troop_data.get("ProductionBuilding") == "Barrack2":
                max_townhall_converter = self.bb_lab_to_townhall

            for level, level_data in troop_data.items():
                if not isinstance(level_data, dict):
                    continue
                #convert times to seconds, all times for all things will be in seconds
                upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60

                if not is_super_troop and not is_seasonal_troop:
                    required_lab_level = level_data.get("LaboratoryLevel")
                    required_townhall = max_townhall_converter[level_data.get("LaboratoryLevel")]
                elif is_super_troop: #for super troops use the original troop's lab level'
                    original_troop = self.full_troop_data.get(super_troop_data["Original"])
                    required_lab_level = original_troop.get(level).get("LaboratoryLevel")
                    required_townhall = max_townhall_converter[required_lab_level]
                elif is_seasonal_troop:
                    required_lab_level = None
                    required_townhall = level_data.get("UpgradeLevelByTH")
                else:
                    continue

                new_level_data = {
                    "level": int(level),
                    "hitpoints": level_data.get("Hitpoints", 0),
                    "dps": level_data.get("DPS", 0),

                    "upgrade_time": upgrade_time_seconds,
                    "upgrade_cost": level_data.get("UpgradeCost", 0),
                    "required_lab_level": required_lab_level,
                    "required_townhall": required_townhall,
                }
                hold_data["levels"].append(new_level_data)

            if not hold_data["levels"]:
                continue
            new_troop_data.append(hold_data)

        return new_troop_data

    def _parse_guardian_data(self):
        full_guardian_data = self.open_file("guardians.json")

        new_guardian_data = []
        for _id, (guardian_name, guardian_data) in enumerate(full_guardian_data.items(), 107000000):
            if guardian_data.get("Deprecated", False):
                continue
            character_data = self.full_troop_data.get(guardian_data.get("CharacterDatas"))
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=guardian_data.get("TID")),
                "info": self._translate(tid=guardian_data.get("InfoTID")),
                "TID": {
                    "name": guardian_data.get("TID"),
                    "info": guardian_data.get("InfoTID"),
                },
                "upgrade_resource": self._parse_resource(resource=character_data.get("UpgradeResource")),

                "is_flying": character_data.get("IsFlying"),
                "is_air_targeting": character_data.get("AirTargets"),
                "is_ground_targeting": character_data.get("GroundTargets"),

                "movement_speed": character_data.get("Speed"),

                "attack_speed": character_data.get("AttackSpeed"),
                "attack_range": character_data.get("AttackRange"),
                "levels": []
            }

            for level, level_data in character_data.items():
                if not isinstance(level_data, dict):
                    continue
                #convert times to seconds, all times for all things will be in seconds
                upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60

                #hard coded for now, didn't find where this is defined, except "HousesGuardians" on the Townhall data
                required_townhall = 18

                new_level_data = {
                    "level": int(level),
                    "hitpoints": level_data.get("Hitpoints"),
                    "dps": level_data.get("DPS"),

                    "upgrade_time": upgrade_time_seconds,
                    "upgrade_cost": level_data.get("UpgradeCost", 0),
                    "required_townhall": required_townhall,
                }
                hold_data["levels"].append(new_level_data)

            new_guardian_data.append(hold_data)

        return new_guardian_data

    def _parse_spell_data(self):
        full_spell_data = self.open_file("spells.json")

        new_spell_data = []
        for _id, (spell_name, spell_data) in enumerate(full_spell_data.items(), 26000000):
            if spell_data.get("DisableProduction", False):
                continue

            production_building = self.full_building_data.get(spell_data.get("ProductionBuilding")).get("TID")
            hold_data = {
                "_id": _id,
                "name": self._translate(spell_data.get("TID")),
                "info": self._translate(spell_data.get("InfoTID")),
                "TID": {
                    "name": spell_data.get("TID"),
                    "info": spell_data.get("InfoTID"),
                },
                "production_building": self._translate(production_building),
                "production_building_level": spell_data.get("SpellForgeLevel"),
                "upgrade_resource": self._parse_resource(resource=spell_data.get("UpgradeResource")),
                "housing_space": spell_data.get("HousingSpace"),
            }
            is_seasonal_spell = spell_data.get("EnabledByCalendar", False)
            if is_seasonal_spell:
                hold_data["is_seasonal"] = is_seasonal_spell
            hold_data["levels"] = []

            for level, level_data in spell_data.items():
                if not isinstance(level_data, dict):
                    continue
                # convert times to seconds, all times for all things will be in seconds
                upgrade_time_seconds = level_data.get("UpgradeTimeH", 0) * 60 * 60

                duration_ms = level_data.get("NumberOfHits", 0) * level_data.get("TimeBetweenHitsMS", 0)
                radius = spell_data.get("Radius", 0) or level_data.get("Radius", 0)
                new_level_data = {
                    "level": int(level),
                    "duration": int(duration_ms / 1000),
                    "radius": round(radius / 100, 1),
                    "damage": level_data.get("Damage", 0) or level_data.get("PoisonDPS", 0),
                    "upgrade_time": upgrade_time_seconds,
                    "upgrade_cost": level_data.get("UpgradeCost", 0),
                    "required_lab_level": level_data.get("LaboratoryLevel"),
                    "required_townhall": level_data.get("UpgradeLevelByTH") or self.lab_to_townhall[level_data.get("LaboratoryLevel")],
                }
                hold_data["levels"].append(new_level_data)

            if not hold_data["levels"]:
                continue
            new_spell_data.append(hold_data)

        return new_spell_data

    def _parse_hero_data(self):
        self.full_hero_data = self.open_file("heroes.json")

        new_hero_data = []
        for _id, (hero_name, hero_data) in enumerate(self.full_hero_data.items(), 28000000):
            village_type = hero_data.get("VillageType", 0)
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=hero_data.get("TID")),
                "info": self._translate(hero_data.get("InfoTID")),
                "TID": {
                    "name": hero_data.get("TID"),
                    "info": hero_data.get("InfoTID"),
                },
                "production_building": self._translate(tid="TID_HERO_TAVERN") if not village_type else None,
                "production_building_level": hero_data.get("1", {}).get("RequiredHeroTavernLevel"),
                "upgrade_resource": self._parse_resource(resource=hero_data.get("UpgradeResource")),

                "is_flying": hero_data.get("IsFlying"),
                "is_air_targeting": hero_data.get("AirTargets"),
                "is_ground_targeting": hero_data.get("GroundTargets"),

                "movement_speed": hero_data.get("Speed"),
                "attack_speed": hero_data.get("AttackSpeed"),
                "attack_range": hero_data.get("AttackRange"),
                "village": "home" if not village_type else "builderBase",
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

        return new_hero_data

    def _parse_pet_data(self):
        full_pet_data = self.open_file("pets.json")

        new_pet_data = []
        for _id, (pet_name, pet_data) in enumerate(full_pet_data.items(), 73000000):
            if pet_data.get("Deprecated", False) or pet_name in ["PhoenixEgg"]:
                continue

            hold_data = {
                "_id": _id,
                "name": self._translate(tid=pet_data.get("TID")),
                "info": self._translate(tid=pet_data.get("InfoTID")),
                "TID": {
                    "name": pet_data.get("TID"),
                    "info": pet_data.get("InfoTID"),
                },
                "production_building": self._translate(tid="TID_PET_SHOP"),
                "production_building_level": pet_data.get("1").get("LaboratoryLevel"),
                "upgrade_resource": self._parse_resource('DarkElixir'),

                "is_flying": pet_data.get("IsFlying"),
                "is_air_targeting": pet_data.get("AirTargets"),
                "is_ground_targeting": pet_data.get("GroundTargets"),

                "movement_speed": pet_data.get("Speed"),
                "attack_speed": pet_data.get("AttackSpeed"),
                "attack_range": pet_data.get("AttackRange"),
                "levels": []
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
                    "required_pet_house_level": level_data.get("LaboratoryLevel"),
                    "required_townhall": self.pethouse_to_townhall[level_data.get("LaboratoryLevel")],
                }
                hold_data["levels"].append(new_level_data)

            new_pet_data.append(hold_data)

        return new_pet_data

    def _parse_equipment_data(self):
        full_equipment_data = self.open_file("character_items.json")

        new_equipment_data = []
        for _id, (equipment_name, equipment_data) in enumerate(full_equipment_data.items(), 90000000):
            if equipment_data.get("Deprecated", False):
                continue

            main_abilities = equipment_data.get("MainAbilities").split(";")
            extra_abilities = equipment_data.get("ExtraAbilities", "").split(";")
            hero_TID = self.full_hero_data.get(equipment_data.get("AllowedCharacters").split(";")[0]).get("TID")
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=equipment_data.get("TID")),
                "info": self._translate(tid=equipment_data.get("InfoTID")),
                "TID": {
                    "name": equipment_data.get("TID"),
                    "info": equipment_data.get("InfoTID"),
                    "production_building": "TID_SMITHY",
                },
                "production_building": self._translate(tid="TID_SMITHY"),
                "production_building_level": equipment_data.get("1").get("RequiredBlacksmithLevel"),
                "rarity": equipment_data.get("Rarity"),
                "hero": self._translate(tid=hero_TID),
                "levels": []
            }

            for level, level_data in equipment_data.items():
                if not isinstance(level_data, dict):
                    continue

                shiny_ore = 0
                glowy_ore = 0
                starry_ore = 0
                upgrade_resources = level_data.get("UpgradeResources", "").split(";")
                upgrade_costs = str(level_data.get("UpgradeCosts", "")).split(";")

                if upgrade_costs[0] != "":
                    for resource, cost in zip(upgrade_resources, upgrade_costs):
                        resource = resource.strip()
                        cost = int(cost)
                        if resource == "CommonOre":
                            shiny_ore += cost
                        elif resource == "RareOre":
                            glowy_ore += cost
                        elif resource == "EpicOre":
                            starry_ore += cost

                new_level_data = {
                    "level": int(level),
                    "hitpoints": level_data.get("Hitpoints", 0),
                    "dps": level_data.get("DPS", 0),
                    "heal_on_activation" : level_data.get("HealOnActivation", 0),
                    "required_blacksmith_level": level_data.get("RequiredBlacksmithLevel"),
                    "required_townhall": self.smithy_to_townhall[level_data.get("RequiredBlacksmithLevel")],
                    "upgrade_cost": {
                        "shiny_ore": shiny_ore,
                        "glowy_ore": glowy_ore,
                        "starry_ore": starry_ore
                    }
                }

                main_ability_levels = str(level_data.get("MainAbilityLevels", "")).split(";")

                if main_ability_levels[0] != "":
                    main_ability_json = []
                    for main_ability, main_ability_level in zip(main_abilities, main_ability_levels):
                        full_ability = self.full_abilities_data.get(main_ability)
                        ability = full_ability.get(main_ability_level)
                        ability["name"] = self._translate(tid=full_ability.get("TID"))
                        ability["info"] = self._translate(tid=full_ability.get("InfoTID"))
                        main_ability_json.append(ability)

                    if main_ability_json:
                        new_level_data["abilities"] = main_ability_json

                extra_ability_levels = str(level_data.get("ExtraAbilityLevels", "")).split(";")
                if extra_ability_levels[0] != "":
                    extra_ability_json = []
                    for extra_ability, extra_ability_level in zip(extra_abilities, extra_ability_levels):
                        full_ability = self.full_abilities_data.get(extra_ability)
                        ability = full_ability.get(extra_ability_level)
                        if ability:
                            ability["name"] = self._translate(tid=full_ability.get("TID"))
                            extra_ability_json.append(ability)

                    if extra_ability_json:
                        new_level_data["abilities"].extend(extra_ability_json)

                hold_data["levels"].append(new_level_data)

            new_equipment_data.append(hold_data)

        return new_equipment_data

    def _parse_trap_data(self):
        full_trap_data = self.open_file("traps.json")

        new_trap_data = []
        for _id, (trap_name, trap_data) in enumerate(full_trap_data.items(), 12000000):
            if trap_data.get("Disabled", False) or trap_data.get("EnabledByCalendar", False):
                continue
            village_type = trap_data.get("VillageType", 0)

            hold_data = {
                "_id": _id,
                "name": self._translate(tid=trap_data.get("TID")),
                "info": self._translate(tid=trap_data.get("InfoTID")),
                "TID" : {
                    "name" : trap_data.get("TID"),
                    "info" : trap_data.get("InfoTID"),
                },
                "width": trap_data.get("Width"),
                "air_trigger": trap_data.get("AirTrigger", False),
                "ground_trigger": trap_data.get("GroundTrigger", False),
                "damage_radius": trap_data.get("DamageRadius"),
                "trigger_radius": trap_data.get("TriggerRadius"),
                "village": "home" if not village_type else "builderBase",

                "upgrade_resource": self._parse_resource(resource=trap_data.get("BuildResource")),
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
                    "damage": level_data.get("Damage", 0),
                })

            new_trap_data.append(hold_data)

        return new_trap_data

    def _parse_decoration_data(self):
        full_deco_data = self.open_file("decos.json")
        new_deco_data = []
        for _id, (deco_name, deco_data) in enumerate(full_deco_data.items(), 18000000):
            if deco_data.get("TID") in ["TID_DECORATION_GENERIC", "TID_DECORATION_NATIONAL_FLAG"]:
                continue
            village_type = deco_data.get("VillageType", 0)
            hold_data = {
                "_id": _id,
                "name": self._translate(deco_data.get("TID")),
                "TID": {
                    "name": deco_data.get("TID"),
                },
                "width": deco_data.get("Width"),
                "not_in_shop": deco_data.get("NotInShop", False),
                "pass_reward": deco_data.get("BPReward", False),
                "max_count": deco_data.get("MaxCount", 1),
                "build_resource": self._parse_resource(resource=deco_data.get("BuildResource")),
                "build_cost": deco_data.get("BuildCost"),
                "village": "home" if not village_type else "builderBase"
            }
            new_deco_data.append(hold_data)

        return new_deco_data

    def _parse_capital_part_data(self):
        full_capital_part_data = self.open_file("building_parts.json")
        new_capital_part_data = []
        for _id, (part_name, part_data) in enumerate(full_capital_part_data.items(), 82000000):
            if part_data.get("Deprecated", False):
                continue
            name = part_name.replace("PlayerHouse_", "").replace("_", " ").title()
            nums = 0
            for phrase in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]:
                if phrase in name:
                    name = name.replace(phrase, "")
                    nums = int(phrase)
            name = name.split(" ", 1)
            name = f"{name[1]} {name[0]}"
            if nums:
                name = f"{name} {nums}"
            new_capital_part_data.append({
                "_id": _id,
                "name": name.title(),
                "slot_type": part_data.get("LayoutSlot"),
                "pass_reward": part_data.get("BattlePassReward", False),
            })

        return new_capital_part_data

    def _parse_obstacle_data(self):
        full_obstacle_data = self.open_file("obstacles.json")

        new_obstacle_data = []
        for _id, (obstacle_name, obstacle_data) in enumerate(full_obstacle_data.items(), 8000000):
            village_type = obstacle_data.get("VillageType", 0)
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=obstacle_data.get("TID")),
                "TID": {
                    "name": obstacle_data.get("TID"),
                },
                "width": obstacle_data.get("Width"),
                "clear_resource": self._parse_resource(resource=obstacle_data.get("ClearResource")),
                "clear_cost": obstacle_data.get("ClearCost"),
                "loot_resource": self._parse_resource(resource=obstacle_data.get("LootResource")),
                "loot_count": obstacle_data.get("LootCount"),
                "village": "home" if not village_type else "builderBase"
            }
            new_obstacle_data.append(hold_data)

        return new_obstacle_data

    def _parse_scenery_data(self):
        full_scenery_data = self.open_file("village_backgrounds.json")

        new_scenery_data = []
        for _id, (scenery_name, scenery_data) in enumerate(full_scenery_data.items(), 60000000):
            type_map = {
                "WAR" : "war",
                "BB" : "builderBase",
                "HOME" : "home"
            }
            if scenery_data.get("HomeType") not in type_map:
                continue

            if not self._translate(tid=scenery_data.get("TID")):
                continue

            hold_data = {
                "_id": _id,
                "name": self._translate(tid=scenery_data.get("TID")),
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

        return new_scenery_data

    def _parse_skin_data(self):
        full_skin_data = self.open_file("skins.json")

        new_skins_data = []
        for _id, (skin_name, skin_data) in enumerate(full_skin_data.items(), 52000000):
            character = skin_data.get("character") or skin_data.get("Character")
            if not skin_data.get("TID") or character not in self.full_hero_data.keys() or not skin_data.get("Tier"):
                continue
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=skin_data.get("TID")),
                "TID": {
                    "name": skin_data.get("TID"),
                },
                "tier": skin_data.get("Tier").title(),
                "character" : character,
            }
            new_skins_data.append(hold_data)

        return new_skins_data

    def _parse_helper_data(self):
        full_helper_data = self.open_file("villager_apprentices.json")

        new_helper_data = []
        for _id, (helper_name, helper_data) in enumerate(full_helper_data.items(), 93000000):
            hold_data = {
                "_id": _id,
                "name": self._translate(tid=helper_data.get("TID")),
                "info": self._translate(tid=helper_data.get("InfoTID")),
                "TID": {
                    "name": helper_data.get("TID"),
                    "info": helper_data.get("InfoTID"),
                },
                "gender": helper_data.get("Gender"),
                "upgrade_resource": self._parse_resource(resource=helper_data.get("CostResource")),
                "levels": []
            }
            for level, level_data in helper_data.items():
                if not isinstance(level_data, dict):
                    continue
                hold_data["levels"].append({
                    "required_townhall": level_data.get("RequiredTownHallLevel"),
                    "upgrade_cost": level_data.get("Cost"),
                    "boost_time_seconds": level_data.get("BoostTimeSeconds"),
                    "boost_multiplier": level_data.get("BoostMultiplier"),
                })

            new_helper_data.append(hold_data)

        return new_helper_data

    def _parse_war_league_data(self):
        full_war_league_data = self.open_file("war_leagues.json")

        new_war_league_data = []
        for _id, (war_league_name, war_league_data) in enumerate(full_war_league_data.items(), 48000000):
            if not war_league_data.get("Name"): #skip Unranked, no data
                continue
            new_war_league_data.append({
                "_id": _id,
                "name": self._translate(tid=war_league_data.get("TID")),
                "TID": {
                    "name": war_league_data.get("TID"),
                },
                "cwl_medals": {
                    "first_place": war_league_data.get("LeagueWinReward"),
                    "position_medal_diff": war_league_data.get("LeaguePosRewardEffect"),
                    "bonus_reward": war_league_data.get("BonusMedalReward"),
                    "minimum_bonus_amount": war_league_data.get("MinNumMedalBonuses"),
                },
                "promotions": war_league_data.get("NumPromotions"),
                "demotions": war_league_data.get("NumDemotions"),
                "15v15_only": war_league_data.get("AllowFirstWarSizeOnly")
            })

        return new_war_league_data

    def _parse_league_tier_data(self):
        full_league_tier_data = self.open_file("league_tiers.json")

        new_league_tier_data = []
        for _id, (league_name, league_data) in enumerate(full_league_tier_data.items(), 105000000):
            league_tier = _id - 105000000
            hold_data = {
                "name": self._translate(tid=league_data.get("TID")),
                "league_tier": league_tier,
                "TID": {
                    "name": league_data.get("TID"),
                },
                "group_size": league_data.get("GroupSizeMax"),
                "demote_percentage": league_data.get("DemotePercentage"),
                "promote_percentage": league_data.get("PromotePercentage"),
                "battle_count": league_data.get("MaxBattleCount"),
                "trophy_start": league_data.get("TrophyFloor"),
                "clan_score": league_data.get("TopClanScore"),
                "townhall_cap": None,
                "rewards" : []
            }
            highest_townhall = 0
            rewards = []
            for tier, level_data in league_data.items():
                if not isinstance(level_data, dict):
                    continue
                if tier == "1": #always empty idky
                    continue
                townhall_level = level_data.get("TH")
                th_min_league_tier = self.full_townhall_data.get(str(townhall_level)).get("LeagueTier", 0)
                if league_tier < th_min_league_tier and league_tier != 0:
                    continue
                highest_townhall = max(townhall_level, highest_townhall)
                rewards.append({
                    "townhall_level": townhall_level,
                    "resources": {
                        "gold": level_data.get("GoldReward"),
                        "elixir": level_data.get("ElixirReward"),
                        "dark_elixir": level_data.get("DarkElixirReward")
                    },
                    "star_bonus": {
                        "gold": level_data.get("GoldRewardStarBonus"),
                        "elixir": level_data.get("ElixirRewardStarBonus"),
                        "dark_elixir": level_data.get("DarkElixirRewardStarBonus"),
                        "shiny_ore": level_data.get("CommonOreRewardStarBonus"),
                        "glowy_ore": level_data.get("RareOreRewardStarBonus"),
                        "starry_ore": level_data.get("EpicOreRewardStarBonus")
                    }
                })
            hold_data["townhall_cap"] = highest_townhall
            hold_data["rewards"] = rewards
            new_league_tier_data.append(hold_data)

        return new_league_tier_data

    def _parse_hall_data(self):
        builderhall_data = []
        townhall_data = []
        id_quantity_map = {}

        for _id, (hall_level, hall_data) in enumerate(self.full_townhall_data.items(), 1):
            builderhall_unlocks = []
            townhall_unlocks = []
            for field, data in hall_data.items():
                building_data = self.full_building_data.get(field)
                if not building_data:
                    continue
                village_type = building_data.get("VillageType", 0)
                id = building_data.get("_id")
                quantity = data

                current_quantity = id_quantity_map.get(id, 0)
                new_quantity = quantity - current_quantity

                if not new_quantity:
                    continue

                if id not in id_quantity_map:
                    id_quantity_map[id] = new_quantity
                else:
                    id_quantity_map[id] += new_quantity

                if not village_type: #is home village
                    townhall_unlocks.append({
                        "name": self._translate(tid=building_data.get("TID")),
                        "_id": id,
                        "quantity": new_quantity
                    })
                else:
                    builderhall_unlocks.append({
                        "name": self._translate(tid=building_data.get("TID")),
                        "_id": id,
                        "quantity": new_quantity
                    })
            townhall_data.append({"level": _id, "buildings_unlocked": townhall_unlocks})
            if builderhall_unlocks:
                builderhall_data.append({"level": _id, "buildings_unlocked": builderhall_unlocks})

        return townhall_data, builderhall_data

    def create_master_json(self):
        self._parse_translation_data()

        self.full_abilities_data = self.open_file("special_abilities.json")
        self.full_resource_data = self.open_file("resources.json")

        master_data = {
            "buildings": self._parse_building_data(),
            "seasonal_defenses": self._parse_seasonal_defense_data(),
            "traps" : self._parse_trap_data(),
            "troops": self._parse_troop_data(),
            "guardians": self._parse_guardian_data(),
            "spells" : self._parse_spell_data(),
            "heroes": self._parse_hero_data(),
            "pets": self._parse_pet_data(),
            "equipment": self._parse_equipment_data(),
            "decorations": self._parse_decoration_data(),
            "obstacles": self._parse_obstacle_data(),
            "sceneries": self._parse_scenery_data(),
            "skins": self._parse_skin_data(),
            "capital_house_parts": self._parse_capital_part_data(),
            "helpers": self._parse_helper_data(),
            "war_leagues": self._parse_war_league_data(),
            "league_tiers": self._parse_league_tier_data(),
            "achievements": self._parse_achievement_data(),
        }
        with open(f"{self.BASE_PATH}static_data.json", "w", encoding="utf-8") as jf:
            jf.write(json.dumps(master_data, indent=2))

        if self.PRUNE_TRANSLATIONS:
            for key in list(self.translation_data.keys()):
                if key not in self.USED_TIDS:
                    del self.translation_data[key]

        with open(f"{self.BASE_PATH}translations.json", "w", encoding="utf-8") as jf:
            jf.write(json.dumps(self.translation_data, indent=2))

        for file_path in self.TARGETS:
            # 6) Delete the extra jsons
            if self.KEEP_JSON:
                continue
            try:
                file_path = file_path.replace("csv", "json")
                os.remove(file_path)
            except OSError as e:
                logging.warning(f"Could not delete {file_path}: {e}")

    def generate_constants(self):
        static_data = self.open_file("static_data.json")

        troops = static_data["troops"]
        spells = static_data["spells"]
        heroes = static_data["heroes"]
        equipment = static_data["equipment"]
        pets = static_data["pets"]
        buildings = static_data["buildings"]
        achievements = static_data["achievements"]

        lists_to_write = {
            'ELIXIR_TROOP_ORDER':  [
                t["name"] for t in troops
                if t["production_building"] == "Barracks"
                and not t.get("is_seasonal", False)
                and not "super_troop" in t
            ],
            'DARK_ELIXIR_TROOP_ORDER': [
                t["name"] for t in troops
                if t["production_building"] == "Dark Barracks"
                and not t.get("is_seasonal", False)
                and not "super_troop" in t
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
            'HOME_BASE_HERO_ORDER': [h["name"] for h in heroes if h["village"] == "home"],
            'BUILDER_BASE_HERO_ORDER': [h["name"] for h in heroes if h["village"] == "builderBase"],
            'HERO_ORDER': 'HOME_BASE_HERO_ORDER + BUILDER_BASE_HERO_ORDER',
            'PETS_ORDER': [p["name"] for p in pets],
            'EQUIPMENT': [e["name"] for e in equipment],
            'HV_BUILDINGS': [b["name"] for b in buildings if b["village"] == "home"],
            'ACHIEVEMENT_ORDER': [a["name"] for a in achievements],
        }

        constants_path = Path(__file__).parent.parent / "constants.py"

        with open(constants_path, 'w') as f:
            f.write('"""Auto-generated constants from static game data."""\n\n')
            for name, lst in lists_to_write.items():
                if isinstance(lst, str):
                    f.write(f"{name} = {lst}\n\n")
                else:
                    # Manual formatting: each item on its own line
                    f.write(f"{name} = [\n")
                    for item in lst:
                        f.write(f"    {repr(item)},\n")
                    f.write("]\n\n")
        
        print(f"Constants written to {constants_path}")


    async def download_files(self):
        if not self.FINGERPRINT:
            self.FINGERPRINT = await self.get_fingerprint()

        BASE_URL = f"https://game-assets.clashofclans.com/{self.FINGERPRINT}"

        fingerprint_file = await self.download(url=f"{BASE_URL}/fingerprint.json", as_json=True)

        for file_data in fingerprint_file.get("files"):
            file_path: str = file_data["file"]
            if not file_path.startswith("logic/") and not file_path.startswith("localization/"):
                continue

            download_url = f"{BASE_URL}/{file_path}"
            print(f"Downloading: {download_url}")
            data = await self.download(url=download_url)

            save_path = file_path.split("/", )[-1]

            if file_path.startswith("localization/") and "texts" not in save_path:
                self.supported_languages.append(save_path.replace(".csv", ""))
                save_path = f"texts_{save_path}"

            with open(save_path, "wb") as f:
                f.write(data)

            print(f"Processing: {save_path}")
            self.process_csv(data=data, file_path=save_path, save_name=save_path.split(".")[0])
            self.TARGETS.append(save_path)

        self.create_master_json()


    def run(self):
        asyncio.run(self.download_files())

if __name__ == "__main__":
    StaticUpdater().generate_constants()

