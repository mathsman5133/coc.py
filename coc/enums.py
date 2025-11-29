"""
MIT License

Copyright (c) 2019-2020 mathsman5133

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from enum import Enum


class ExtendedEnum(Enum):
    """An Enum class that allows for the `__str__` method to be implemented."""

    def __str__(self):
        return self.in_game_name

    def __eq__(self, other):
        """Check if the enum is equal to another enum or a string."""
        if isinstance(other, Enum):
            return self.value == other.value
        elif isinstance(other, str):
            return str(self.name) == other or str(self.value) == other
        return False

    @property
    def in_game_name(self) -> str:
        raise NotImplementedError

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def names(cls):
        return list(map(lambda c: c.name, cls))


class PlayerHouseElementType(ExtendedEnum):
    """Enum to map the type of element of the player house."""

    ground = "ground"
    roof = "roof"
    foot = "foot"  # API docs say this exists, but unable to find it anywhere. Looks like this means `walls`
    deco = "decoration"
    walls = "walls"

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the element type."""
        lookup = {"ground": "Ground", "roof": "Roof", "foot": "Foot", "decoration": "Decoration", "walls": "Walls"}
        return lookup[self.value]


class Role(ExtendedEnum):
    """Enum to map a player's role in the clan."""

    member = "member"
    elder = "admin"
    co_leader = "coLeader"
    leader = "leader"

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the role."""
        lookup = {"member": "Member", "admin": "Elder", "coLeader": "Co-Leader", "leader": "Leader"}
        return lookup[self.value]


class WarRound(ExtendedEnum):
    previous_war = 0
    current_war = 1
    current_preparation = 2

    def __str__(self):
        return self.name

    @property
    def in_game_name(self) -> str:
        lookup = ["Previous War", "Current War", "Current Preparation"]
        return lookup[self.value]


class BattleModifier(ExtendedEnum):
    """Enum to map the type of battle modifiers."""
    none = "none"
    hard_mode = "hardMode"

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the battle modifier."""
        lookup = {"none": "None", "hardMode": "Hard Mode"}
        return lookup[self.value]


class WarState(ExtendedEnum):
    """Enum to map the state of the war.
    Compared to the api docs a few states are missing, but those were never observed in the wild."""
    not_in_war = "notInWar"
    preparation = "preparation"
    in_war = "inWar"
    war_ended = "warEnded"

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the war state."""
        lookup = {"notInWar": "Not in War", "preparation": "Preparation", "inWar": "In War", "warEnded": "War Ended"}
        return lookup[self.value]


class WarResult(ExtendedEnum):
    """Enum to map the result of the war"""
    win = "win"
    lose = "lose"
    tie = "tie"

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the war state."""
        lookup = {"win": "Win", "lose": "Lose", "tie": "Tie"}
        return lookup[self.value]


class ProductionBuildingType(ExtendedEnum):
    barracks = "Barracks"
    dark_barracks = "Dark Barracks"
    spell_factory = "Spell Factory"
    dark_spell_factory = "Dark Spell Factory"
    hero_hall = "Hero Hall"
    builder_barracks = "Builder Barracks"
    blacksmith = "Blacksmith"
    pet_house = "Pet House"
    workshop = "Workshop"
    none = "None"


class Resource(ExtendedEnum):
    gold = "Gold"
    elixir = "Elixir"
    dark_elixir = "Dark Elixir"
    builder_gold = "Builder Gold"
    builder_elixir = "Builder Elixir"
    gems = "Gems"
    shiny_ore = "Shiny Ore"
    glowy_ore = "Glowy Ore"
    starry_ore = "Starry Ore"


class BuildingType(ExtendedEnum):
    army = "Army"
    town_hall = "Town Hall"
    town_hall_weapon = "Town Hall Weapon"
    builder_hall = "Town Hall2"
    resource = "Resource"
    wall = "Wall"
    defense = "Defense"
    worker = "Worker"
    worker_2 = "Worker2"
    helper = "Helper"


class VillageType(ExtendedEnum):
    home = "home"
    builder_base = "builderBase"

class SceneryType(ExtendedEnum):
    home = "home"
    builder_base = "builderBase"
    war = "war"

class EquipmentRarity(ExtendedEnum):
    common = "Common"
    epic = "Epic"


class SkinTier(ExtendedEnum):
    default = "Default"
    standard = "Basic"
    gold = "Gold"
    legendary = "Legendary"



class Gender(ExtendedEnum):
    male = "M"
    female = "F"


UNRANKED_LEAGUE_DATA = {
    "id": 105000000,
    "name": "Unranked",
    "iconUrls": {
        "small": "https://api-assets.clashofclans.com/leaguetiers/125/yyYo5DUFeFBZvmMEQh0ZxvG-1sUOZ_S3kDMB7RllXX0.png",
        "large": "https://api-assets.clashofclans.com/leaguetiers/326/yyYo5DUFeFBZvmMEQh0ZxvG-1sUOZ_S3kDMB7RllXX0.png"
    }
}


