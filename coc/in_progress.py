







def parse_building_data():
    account_data = open_file("static/building_data.json")
    static_data = open_file("static/static_data.json")

    def get_static_data_item(section: str, item_id: int):
        item_data = next((item for item in static_data[section] if item["_id"] == item_id), None)
        return item_data

    def add_upgrade(item: dict, target: LeveledUnit) -> Upgrade | None:
        if "timer" in item:
            helper_timer = None
            if "helper_timer" in item:
                helper_timer = TimeDelta(seconds=item["helper_timer"])
            return Upgrade(
                is_goblin=item.get("extra", False),
                target=target,
                timer=TimeDelta(seconds=item["timer"]),
                helper_timer=helper_timer,
                recurrent_helper=item.get("recurrent_helper", False)
            )

    account = AccountData()
    account.boosts = Boosts(data=account_data.get("boosts", {}))

    # section is "guardians", "buildings", etc,
    for section, items in account_data.items(): #type: str, list[dict]
        if not isinstance(items, list) or "2" in section:
            continue

        items.extend(account_data.get(f"{section}2", []))
        if section == "helpers":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                helper = Helper(
                    level=item.get("lvl", 0), data=item_data
                )
                if "helper_cooldown" in item:
                    account.boosts.helper_cooldown = TimeDelta(seconds=item["helper_cooldown"])
                account.helpers.append(helper)

        elif section == "guardians":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                guardian = Guardian(
                    level=item.get("lvl"), data=item_data
                )
                if upgrade := add_upgrade(item, guardian):
                    account.upgrades.append(upgrade)
                account.guardians.append(guardian)

        elif section == "buildings":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)

                seasonal_defenses = []
                if "types" in item:
                    crafting_station: list[dict] = item["types"]
                    for seasonal_defense in crafting_station:
                        seasonal_def_data = get_static_data_item(
                            section="seasonal_defenses",
                            item_id=seasonal_defense["data"]
                        )
                        modules = []
                        for module in seasonal_defense["modules"]:
                            module_data = next((
                                item for item in seasonal_def_data["modules"] if item["_id"] == module["data"]
                            ))
                            modules.append(SeasonalDefenseModule(level=module["lvl"], data=module_data))
                        seasonal_defenses.append(SeasonalDefense(data=seasonal_def_data, modules=modules))

                building = Building(
                    level=item.get("lvl", 0),
                    data=item_data,
                    weapon_level=item.get("weapon", 0),
                    supercharge_level=item.get("supercharge", 0),
                    supercharge_data=get_static_data_item(section="supercharges", item_id=item_id),
                    seasonal_defenses=seasonal_defenses
                )
                if building.type == BuildingType.TOWN_HALL:
                    account.townhall_level = building.level
                if upgrade := add_upgrade(item, building):
                    account.upgrades.append(upgrade)
                account.buildings.append((building, item.get("cnt", 1)))

        elif section == "traps":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                trap = Trap(
                    level=item.get("lvl"), data=item_data
                )
                if upgrade:= add_upgrade(item, trap):
                    account.upgrades.append(upgrade)
                account.traps.append((trap, item.get("cnt", 1)))

        elif section == "decos":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section="decorations", item_id=item_id)
                deco = Decoration(data=item_data)
                account.decorations.append((deco, item.get("cnt", 1)))

        elif section == "obstacles":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                obstacle = Obstacle(data=item_data)
                account.obstacles.append((obstacle, item.get("cnt", 1)))

        elif section == "units":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section="troops", item_id=item_id)
                troop = Troop(data={}, static_data=item_data, level=item["lvl"])
                if upgrade := add_upgrade(item, troop):
                    account.upgrades.append(upgrade)
                account.troops.append(troop)

        elif section == "spells":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                spell = Spell(data={}, static_data=item_data, level=item["lvl"])
                if upgrade := add_upgrade(item, spell):
                    account.upgrades.append(upgrade)
                account.spells.append(spell)

        elif section == "siege_machines":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section="troops", item_id=item_id)
                troop = Troop(data={}, static_data=item_data, level=item["lvl"])
                if upgrade := add_upgrade(item, troop):
                    account.upgrades.append(upgrade)
                account.siege_machines.append(troop)

        elif section == "heroes":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                hero = Hero(data={}, static_data=item_data, level=item["lvl"])
                if upgrade := add_upgrade(item, hero):
                    account.upgrades.append(upgrade)
                account.heroes.append(hero)

        elif section == "pets":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                pet = Pet(data={}, static_data=item_data, level=item["lvl"])
                if upgrade := add_upgrade(item, pet):
                    account.upgrades.append(upgrade)
                account.pets.append(pet)

        elif section == "equipment":
            for item in items:
                item_id = item["data"]
                item_data = get_static_data_item(section=section, item_id=item_id)
                equipment = Equipment(data={}, static_data=item_data, level=item["lvl"])
                account.equipment.append(equipment)

        elif section == "skins":
            for item_id in items:
                item_data = get_static_data_item(section=section, item_id=item_id)
                if not item_data:
                    continue
                skin = Skin(data=item_data)
                account.skins.append(skin)

        elif section == "sceneries":
            for item_id in items:
                item_data = get_static_data_item(section=section, item_id=item_id)
                scenery = Scenery(data=item_data)
                account.sceneries.append(scenery)

        elif section == "house_parts":
            for item_id in items:
                item_data = get_static_data_item(section="capital_house_parts", item_id=item_id)
                house_part = ClanCapitalHousePart(data=item_data)
                account.capital_house_parts.append(house_part)

parse_building_data()


