from .enums import Resource
from .miscmodels import TimeDelta

class Troop:
    """Represents a Troop object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The troop's unique ID.
    name: :class:`str`
        The troop's name.
    range: :class:`int`
        The troop's attack range.
    lab_level: :class:`int`
        The required labatory level to upgrade the troop to this level.
    dps: :class:`int`
        The troop's Damage Per Second (DPS).
    hitpoints: :class:`int`
        The number of hitpoints the troop has at this level.
    ground_target: :class:`bool`
        Whether the troop is ground-targetting.
    speed: :class:`int`
        The troop's speed.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the troop to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this troop.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this troop to the next level.
    training_cost: :class:`int`
        The amount of resources required to train this troop.
    training_resource: :class:`Resource`
        The type of resource used to train this troop.
    training_time: :class:`TimeDelta`
        The amount of time required to train this troop.
    is_elixir_troop: :class:`bool`
        Whether this troop is a regular troop from the Barracks
    is_dark_troop: :class:`bool`
        Whether this troop is a dark-troop, trained in the Dark Barracks.
    is_siege_machine: :class:`bool`
        Whether this troop is a Siege Machine.
    is_super_troop: :class:`bool`
        Whether this troop is a Super Troop.

    cooldown: :class:`TimeDelta`
        The cooldown on this super troop before being able to be reactivated [Super Troops Only].
    duration: :class:`TimeDelta`
        The length of time this super troop is active for [Super Troops Only].
    min_original_level: :class:`int`
        The minimum level required of the original troop in order to boost this troop [Super Troops Only].
    original_troop: :class:`Troop`
        The "original" counterpart troop to this super troop [Super Troops Only].

    is_loaded: :class:`bool`
        Whether the API data has been loaded for this troop.
    level: :class:`int`
        The troop's level
    max_level: :class:`int`
        The max level for this troop.
    village: :class:`str`
        Either ``home`` or ``builderBase``, indicating which village this troop belongs to.
    """

    def __init__(self, *, data, client, load_game_data=None, **_):
        self._client = client

        if load_game_data is not None:
            self._load_game_data = load_game_data
        elif self._client and self._client.load_game_data.never:
            self._load_game_data = False
        else:
            self._load_game_data = True

        self._from_data(data=data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.name: str = data_get("name")
        self.level: int = data_get("level")
        self.max_level: int = data_get("max_level")
        self.village: str = data_get("village")
        self.is_active: bool = data.get("superTroopIsActive")

        self.is_fully_max: bool = self.level == self.max_level

        if self._load_game_data:
            troop_id = self._client._static_name_to_id.get((self.name, self.village))
            troop_data = self._client._troop_holder.get(troop_id)
            self._troop_data: dict = troop_data

            self.id: int = troop_data.get("_id")
            self.name: str = troop_data.get("name")
            self.info: str = troop_data.get("info")
            self.TID: dict = troop_data.get("TID")

            self.timer = TimeDelta(seconds=data.get("timer", 0))
            self.production_building: str = troop_data.get("production_building")
            self.production_building_level: int = troop_data.get("production_building_level")
            self.upgrade_resource: Resource = Resource(value=troop_data.get("upgrade_resource"))

            self.is_flying: bool = troop_data.get("is_flying")
            self.is_air_targeting: bool = troop_data.get("is_air_targeting")
            self.is_ground_targeting: bool = troop_data.get("is_ground_targeting")
            self.is_super_troop: bool = troop_data.get("super_troop") is not None

            self.is_active = self.is_super_troop

            self.is_seasonal: bool = troop_data.get("is_seasonal", False)

            self.movement_speed: int = troop_data.get("movement_speed")
            self.attack_speed: int = troop_data.get("attack_speed")
            self.attack_range: int = troop_data.get("attack_range")
            self.housing_space: int = troop_data.get("housing_space")
            self.village: str = troop_data.get("village_type")
            self.is_home_village: bool = self.village == "home"

            #level data
            level_data: dict = troop_data.get("levels")[self.level]
            self.hitpoints: int = level_data.get("hitpoints")
            self.dps: int = level_data.get("dps")
            self.upgrade_time: TimeDelta = TimeDelta(seconds=level_data.get("upgrade_time"))
            self.upgrade_cost: int = level_data.get("upgrade_cost")
            self.required_lab_level: int = level_data.get("required_lab_level")
            self.required_townhall: int = level_data.get("required_townhall")

            self.max_level: int = len(level_data)


    def get_max_level_for_townhall(self, townhall: int):
        """Get the maximum level for a troop for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum troop level for.

        Returns
        --------
        :class:`int`
            The maximum troop level, or ``None`` if the troop hasn't been unlocked at that level.

        """

        max_level = None
        for level in self._troop_data.get("levels", []):
            if level.get("required_townhall") <= townhall:
                max_level = level.get("level")
            else:
                break

        return max_level


class Spell:
    """Represents a Spell object as returned by the API, optionally filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The spell's unique ID.
    name: :class:`str`
        The spell's name.
    range: :class:`int`
        The spell's attack range.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the spell to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this spell.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this spell to the next level.
    training_cost: :class:`int`
        The amount of resources required to train this spell.
    training_resource: :class:`Resource`
        The type of resource used to train this spell.
    training_time: :class:`TimeDelta`
        The amount of time required to train this spell.
    is_elixir_spell: :class:`bool`
        Whether this spell is a regular spell from the Barracks
    is_dark_spell: :class:`bool`
        Whether this spell is a dark-spell, trained in the Dark Barracks.
    is_loaded: :class:`bool`
        Whether the API data has been loaded for this spell.
    level: :class:`int`
        The spell's level
    max_level: :class:`int`
        The max level for this spell.
    village: :class:`str`
        Either ``home`` or ``builderBase``, indicating which village this spell belongs to.
    """

    def __init__(self, *, data, client, load_game_data=None, **_):
        self._client = client

        if load_game_data is not None:
            self._load_game_data = load_game_data
        elif self._client and self._client.load_game_data.never:
            self._load_game_data = False
        else:
            self._load_game_data = True

        self._from_data(data=data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.name: str = data_get("name")
        self.level: int = data_get("level")
        self.max_level: int = data_get("max_level")
        self.village: str = data_get("village")
        self.is_active: bool = data.get("superTroopIsActive")

        self.is_fully_max: bool = self.level == self.max_level

        if self._load_game_data:
            spell_id = self._client._static_name_to_id.get(self.name)
            spell_data = self._client._spell_holder.get(spell_id)
            self._spell_data: dict = spell_data

            self.id: int = spell_data.get("_id")
            self.name: str = spell_data.get("name")
            self.info: str = spell_data.get("info")
            self.TID: dict = spell_data.get("TID")
            self.timer = TimeDelta(seconds=data.get("timer", 0))

            self.production_building: str = spell_data.get("production_building")
            self.production_building_level: int = spell_data.get("production_building_level")
            self.upgrade_resource: Resource = Resource(value=spell_data.get("upgrade_resource"))

            self.is_seasonal: bool = spell_data.get("is_seasonal", False)

            self.radius: int = spell_data.get("radius")
            self.housing_space: int = spell_data.get("housing_space")

            #level data
            level_data: dict = spell_data.get("levels")[self.level]
            self.damage: int = level_data.get("damage")
            self.upgrade_time: TimeDelta = TimeDelta(seconds=level_data.get("upgrade_time"))
            self.upgrade_cost: int = level_data.get("upgrade_cost")
            self.required_lab_level: int = level_data.get("required_lab_level")
            self.required_townhall: int = level_data.get("required_townhall")

            self.max_level: int = len(level_data)


    def get_max_level_for_townhall(self, townhall: int):
        """Get the maximum level for a spell for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum spell level for.

        Returns
        --------
        :class:`int`
            The maximum spell level, or ``None`` if the spell hasn't been unlocked at that level.

        """

        max_level = None
        for level in self._spell_data.get("levels", []):
            if level.get("required_townhall") <= townhall:
                max_level = level.get("level")
            else:
                break

        return max_level


class Hero:
    """
    Represents a Hero object as returned by the API, optionally
    filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The hero's unique ID.
    name: :class:`str`
        The hero's name.
    range: :class:`int`
        The hero's attack range.
    dps: :class:`int`
        The hero's Damage Per Second (DPS).
    hitpoints: :class:`int`
        The number of hitpoints the troop has at this level.
    ground_target: :class:`bool`
        Whether the hero is ground-targetting. The Grand Warden is classified as ground targetting always.
    speed: :class:`int`
        The hero's speed.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the hero to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this hero.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this hero to the next level.
    ability_time: :class:`int`
        The number of milliseconds the hero's ability lasts for.
    required_th_level: :class:`int`
        The minimum required townhall to unlock this level of the hero.
    regeneration_time: :class:`TimeDelta`
        The time required for this hero to regenerate after being "knocked out".
    equipment: :class:`List[Equipment]`
        a list of the equipment currently used by this hero
    is_loaded: :class:`bool`
        Whether the API data has been loaded for this hero.
    level: :class:`int`
        The hero's level
    max_level: :class:`int`
        The max level for this hero.
    village: :class:`str`
        Either ``home`` or ``builderBase``, indicating which village this hero belongs to.
    """

    def __init__(self, *, data, client, load_game_data=None, **_):
        self._client = client

        if load_game_data is not None:
            self._load_game_data = load_game_data
        elif self._client and self._client.load_game_data.never:
            self._load_game_data = False
        else:
            self._load_game_data = True

        self._from_data(data=data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.name: str = data_get("name")
        self.level: int = data_get("level")
        self.max_level: int = data_get("max_level")
        self.village: str = data_get("village")
        self.is_active: bool = data.get("superTroopIsActive")

        self.equipment: list[Equipment] = [Equipment() for equipment in data.get('equipment', [])]

        self.is_fully_max: bool = self.level == self.max_level

        if self._load_game_data:
            hero_id = self._client._static_name_to_id.get(self.name)
            hero_data = self._client._hero_holder.get(hero_id)
            self._hero_data: dict = hero_data

            self.id: int = hero_data.get("_id")
            self.name: str = hero_data.get("name")
            self.info: str = hero_data.get("info")
            self.TID: dict = hero_data.get("TID")
            self.timer = TimeDelta(seconds=data.get("timer", 0))

            self.production_building: str = hero_data.get("production_building")
            self.production_building_level: int = hero_data.get("production_building_level")
            self.upgrade_resource: Resource = Resource(value=hero_data.get("upgrade_resource"))

            self.is_flying: bool = hero_data.get("is_flying")
            self.is_air_targeting: bool = hero_data.get("is_air_targeting")
            self.is_ground_targeting: bool = hero_data.get("is_ground_targeting")

            self.movement_speed: int = hero_data.get("movement_speed")
            self.attack_speed: int = hero_data.get("attack_speed")
            self.attack_range: int = hero_data.get("attack_range")
            self.housing_space: int = hero_data.get("housing_space")
            self.village: str = hero_data.get("village_type")
            self.is_home_village: bool = self.village == "home"

            #level data
            level_data: dict = hero_data.get("levels")[self.level]
            self.hitpoints: int = level_data.get("hitpoints")
            self.dps: int = level_data.get("dps")
            self.upgrade_time: TimeDelta = TimeDelta(seconds=level_data.get("upgrade_time"))
            self.upgrade_cost: int = level_data.get("upgrade_cost")
            self.required_lab_level: int = level_data.get("required_hero_tavern_level")
            self.required_townhall: int = level_data.get("required_townhall")

            self.max_level: int = len(level_data)


    def get_max_level_for_townhall(self, townhall: int):
        """Get the maximum level for a hero for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum hero level for.

        Returns
        --------
        :class:`int`
            The maximum hero level, or ``None`` if the hero hasn't been unlocked at that level.

        """

        max_level = None
        for level in self._hero_data.get("levels", []):
            if level.get("required_townhall") <= townhall:
                max_level = level.get("level")
            else:
                break

        return max_level


class EquipmentResource:
    def __init__(self, shiny_ore: int, glowy_ore: int, starry_ore: int):
        self.shiny_ore = shiny_ore
        self.glowy_ore = glowy_ore
        self.starry_ore = starry_ore


class Equipment:
    """
    Represents a Hero object as returned by the API, optionally
    filled with game data.

    Attributes
    ----------
    id: :class:`int`
        The hero's unique ID.
    name: :class:`str`
        The hero's name.
    range: :class:`int`
        The hero's attack range.
    dps: :class:`int`
        The hero's Damage Per Second (DPS).
    hitpoints: :class:`int`
        The number of hitpoints the troop has at this level.
    ground_target: :class:`bool`
        Whether the hero is ground-targetting. The Grand Warden is classified as ground targetting always.
    speed: :class:`int`
        The hero's speed.
    upgrade_cost: :class:`int`
        The amount of resources required to upgrade the hero to the next level.
    upgrade_resource: :class:`Resource`
        The type of resource used to upgrade this hero.
    upgrade_time: :class:`TimeDelta`
        The time taken to upgrade this hero to the next level.
    ability_time: :class:`int`
        The number of milliseconds the hero's ability lasts for.
    required_th_level: :class:`int`
        The minimum required townhall to unlock this level of the hero.
    regeneration_time: :class:`TimeDelta`
        The time required for this hero to regenerate after being "knocked out".
    equipment: :class:`List[Equipment]`
        a list of the equipment currently used by this hero
    is_loaded: :class:`bool`
        Whether the API data has been loaded for this hero.
    level: :class:`int`
        The hero's level
    max_level: :class:`int`
        The max level for this hero.
    village: :class:`str`
        Either ``home`` or ``builderBase``, indicating which village this hero belongs to.
    """

    def __init__(self, *, data, client, load_game_data=None, **_):
        self._client = client

        if load_game_data is not None:
            self._load_game_data = load_game_data
        elif self._client and self._client.load_game_data.never:
            self._load_game_data = False
        else:
            self._load_game_data = True

        self._from_data(data=data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.name: str = data_get("name")
        self.level: int = data_get("level")
        self.max_level: int = data_get("max_level")
        self.village: str = data_get("village")

        self.is_fully_max: bool = self.level == self.max_level

        if self._load_game_data:
            equipment_id = self._client._static_name_to_id.get(self.name)
            equipment_data = self._client._equipment_holder.get(equipment_id)
            self._equipment_data: dict = equipment_data

            self.id: int = equipment_data.get("_id")
            self.name: str = equipment_data.get("name")
            self.info: str = equipment_data.get("info")
            self.TID: dict = equipment_data.get("TID")

            self.production_building: str = equipment_data.get("production_building")
            self.production_building_level: int = equipment_data.get("production_building_level")
            self.rarity: str = equipment_data.get("rarity")
            self.hero: str = equipment_data.get("hero")

            #level data
            level_data: dict = equipment_data.get("levels")[self.level]
            self.hitpoints: int = level_data.get("hitpoints") or 0
            self.dps: int = level_data.get("dps") or 0
            self.heal_on_activation: int = level_data.get("heal_on_activation") or 0

            self.upgrade_cost: EquipmentResource = EquipmentResource(
                shiny_ore=level_data.get("shiny_ore"),
                glowy_ore=level_data.get("glowy_ore"),
                starry_ore=level_data.get("starry_ore")
            )

            self.main_abilities: list[dict] = level_data.get("main_abilities")
            self.extra_abilities: list[dict] = level_data.get("extra_abilities")

            self.required_blacksmith_level: int = level_data.get("required_blacksmith_level")
            self.required_townhall: int = level_data.get("required_townhall")

            self.max_level: int = len(level_data)


    def get_max_level_for_townhall(self, townhall: int):
        """Get the maximum level for equipment for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum equipment level for.

        Returns
        --------
        :class:`int`
            The maximum equipment level, or ``None`` if the equipment hasn't been unlocked at that level.

        """

        max_level = None
        for level in self._equipment_data.get("levels", []):
            if level.get("required_townhall") <= townhall:
                max_level = level.get("level")
            else:
                break

        return max_level


class Module:
    def __init__(self, *, data, client, **_):
        self._client = client
        self._from_data(data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.id = data_get("data")
        self.level = data_get("lvl")

        self.TID = data_get("TID")
        self.timer = TimeDelta(seconds=data_get("timer", 0))

        self.upgrade_resource: Resource = Resource(value=data_get("upgrade_resource"))

        level_data: dict = data_get("levels")[self.level]
        self.upgrade_cost: int = level_data.get("upgrade_cost")
        self.upgrade_time: TimeDelta = TimeDelta(seconds=level_data.get("upgrade_time"))
        self.ability_data: dict = level_data.get("ability_data")


class SeasonalDefense:
    def __init__(self, *, data, client, **_):
        self._client = client
        self._from_data(data=data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.id = data_get("data")

        seasonal_defense_data = self._client._seasonal_defense_holder.get(self.id)
        self.seasonal_defense_data: dict = seasonal_defense_data

        self.name: str = seasonal_defense_data.get("name")
        self.info: str = seasonal_defense_data.get("info")
        self.TID: dict = seasonal_defense_data.get("TID")

        module_map = {m.get("_id"): m for m in seasonal_defense_data.get("modules")}

        self.modules: list[Module] = [
            Module(client=self._client, data=module | module_map.get(module.get("data")))
            for module in seasonal_defense_data.get("modules")
        ]

        self.level = sum(m.level for m in self.modules)


class Building:

    def __init__(self, *, client, **_):
        self._client = client

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict, supercharge: bool = False, gear_up: bool = False) -> None:
        data_get = data.get

        self.id = data_get("data")
        self.level = data_get("lvl")

        building_data = self._client._building_holder.get(self.id)
        self._building_data: dict = building_data

        self.name: str = building_data.get("name")
        self.info: str = building_data.get("info")
        self.TID: dict = building_data.get("TID")
        self.timer = TimeDelta(seconds=data.get("timer", 0))

        self.type: str = building_data.get("Army")
        self.upgrade_resource: Resource = Resource(value=building_data.get("upgrade_resource"))

        self.village: str = building_data.get("village_type")
        self.is_home_village: bool = self.village == "home"
        self.width: int = building_data.get("width")

        self.supercharged: bool = supercharge
        self.geared_up: bool = gear_up
        self.is_superchargeable: bool = building_data.get("superchargeable")

        #level data
        if building_data.get("levels"):
            level_data: dict = building_data.get("levels")[self.level]
            self.upgrade_cost: int = level_data.get("upgrade_cost")
            self.upgrade_time: TimeDelta = TimeDelta(seconds=level_data.get("upgrade_time"))
            self.required_townhall: int = level_data.get("required_townhall")
            self.hitpoints: int = level_data.get("hitpoints")
            self.dps: int = level_data.get("dps") or 0

            self.main_abilities: list[dict] = level_data.get("main_abilities")
            self.extra_abilities: list[dict] = level_data.get("extra_abilities")

            self.required_blacksmith_level: int = level_data.get("required_blacksmith_level")
            self.required_townhall: int = level_data.get("required_townhall")
            self.max_level: int = len(level_data)

        # is for crafting defense
        if self.id == 1000097:
            self.seasonal_defenses: list[SeasonalDefense] = [
                SeasonalDefense(data=d, client=self._client)
                for d in building_data.get("types")
            ]


    def get_max_level_for_townhall(self, townhall: int):
        """Get the maximum level for a building for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum building level for.

        Returns
        --------
        :class:`int`
            The maximum building level, or ``None`` if the building hasn't been unlocked at that level.

        """

        max_level = None
        for level in self._building_data.get("levels", []):
            if level.get("required_townhall") <= townhall:
                max_level = level.get("level")
            else:
                break

        return max_level


class Helper:
    def __init__(self, *, data, client, **_):
        self._client = client
        self._from_data(data)

    def __repr__(self):
        attrs = [
            ("name", self.name),
            ("id", self.id),
        ]
        return "<%s %s>" % (
            self.__class__.__name__, " ".join("%s=%r" % t for t in attrs),)

    def _from_data(self, data: dict) -> None:
        data_get = data.get

        self.id = data_get("data")
        self.level = data_get("lvl")

        helper_data = self._client._helper_holder.get(self.id)
        self._helper_data: dict = helper_data

        self.gender = helper_data.get("gender")
        self.TID = data_get("TID")
        self.upgrade_resource: Resource = Resource(value=data_get("upgrade_resource"))

        level_data: dict = data_get("levels")[self.level]
        self.upgrade_cost: int = level_data.get("upgrade_cost")
        self.required_townhall: int = level_data.get("required_townhall")
        self.boost_time: TimeDelta = TimeDelta(seconds=level_data.get("boost_time_seconds"))
        self.boost_multiplier: int = level_data.get("boost_multiplier")


    def get_max_level_for_townhall(self, townhall: int):
        """Get the maximum level for a helper for a given townhall level.

        Parameters
        ----------
        townhall
            The townhall level to get the maximum helper level for.

        Returns
        --------
        :class:`int`
            The maximum helper level, or ``None`` if the helper hasn't been unlocked at that level.

        """

        max_level = None
        for level in self._helper_data.get("levels", []):
            if level.get("required_townhall") <= townhall:
                max_level = level.get("level")
            else:
                break

        return max_level