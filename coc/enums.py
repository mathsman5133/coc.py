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


class Resource(ExtendedEnum):
    elixir = "Elixir"
    builder_elixir = "Elixir2"
    dark_elixir = "DarkElixir"
    gold = "Gold"
    builder_gold = "Gold2"
    shiny_ore = "CommonOre"
    glowy_ore = "RareOre"
    starry_ore = "EpicOre"

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the resource."""
        lookup = {"Elixir": "Elixir", "Elixir2": "Builder Elixir",
                  "DarkElixir": "Dark Elixir", "Gold": "Gold", "Gold2": "Builder Gold",
                  "CommonOre": "Shiny Ore", "RareOre": "Glowy Ore", "EpicOre": "Starry Ore"}
        return lookup[self.value]


ELIXIR_TROOP_ORDER = [
    "Barbarian",
    "Archer",
    "Giant",
    "Goblin",
    "Wall Breaker",
    "Balloon",
    "Wizard",
    "Healer",
    "Dragon",
    "P.E.K.K.A",
    "Baby Dragon",
    "Miner",
    "Electro Dragon",
    "Yeti",
    "Dragon Rider",
    "Electro Titan",
    "Root Rider",
    "Thrower"
]


DARK_ELIXIR_TROOP_ORDER = [
    "Minion",
    "Hog Rider",
    "Valkyrie",
    "Golem",
    "Witch",
    "Lava Hound",
    "Bowler",
    "Ice Golem",
    "Headhunter",
    "Apprentice Warden",
    "Druid",
]

SIEGE_MACHINE_ORDER = [
    "Wall Wrecker",
    "Battle Blimp",
    "Stone Slammer",
    "Siege Barracks",
    "Log Launcher",
    "Flame Flinger",
    "Battle Drill",
]

SUPER_TROOP_ORDER = [
    "Super Barbarian",
    "Super Archer",
    "Super Giant",
    "Sneaky Goblin",
    "Super Wall Breaker",
    "Rocket Balloon",
    "Super Wizard",
    "Super Dragon",
    "Inferno Dragon",
    "Super Minion",
    "Super Valkyrie",
    "Super Witch",
    "Ice Hound",
    "Super Bowler",
    "Super Miner",
    "Super Hog Rider",
]

HV_TROOP_ORDER = ELIXIR_TROOP_ORDER + DARK_ELIXIR_TROOP_ORDER
HOME_TROOP_ORDER = HV_TROOP_ORDER + SIEGE_MACHINE_ORDER


BUILDER_TROOPS_ORDER = [
    "Raged Barbarian",
    "Sneaky Archer",
    "Boxer Giant",
    "Beta Minion",
    "Bomber",
    "Baby Dragon",
    "Cannon Cart",
    "Night Witch",
    "Drop Ship",
    "Power P.E.K.K.A",
    "Hog Glider",
    "Electrofire Wizard",
]


ELIXIR_SPELL_ORDER = [
    "Lightning Spell",
    "Healing Spell",
    "Rage Spell",
    "Jump Spell",
    "Freeze Spell",
    "Clone Spell",
    "Invisibility Spell",
    "Recall Spell",
    "Revive Spell"
]


DARK_ELIXIR_SPELL_ORDER = [
    "Poison Spell",
    "Earthquake Spell",
    "Haste Spell",
    "Skeleton Spell",
    "Bat Spell",
    "Overgrowth Spell",
]


SPELL_ORDER = ELIXIR_SPELL_ORDER + DARK_ELIXIR_SPELL_ORDER

HOME_BASE_HERO_ORDER = ["Barbarian King", "Archer Queen", "Minion Prince", "Grand Warden", "Royal Champion"]
BUILDER_BASE_HERO_ORDER = ["Battle Machine", "Battle Copter"]
HERO_ORDER = HOME_BASE_HERO_ORDER + BUILDER_BASE_HERO_ORDER

PETS_ORDER = [
    "L.A.S.S.I",
    "Electro Owl",
    "Mighty Yak",
    "Unicorn",
    "Frosty",
    "Diggy",
    "Poison Lizard",
    "Phoenix",
    "Spirit Fox",
    "Angry Jelly",
]

EQUIPMENT = [
    "Barbarian Puppet",
    "Rage Vial",
    "Archer Puppet",
    "Invisibility Vial",
    "Eternal Tome",
    "Life Gem",
    "Seeking Shield",
    "Royal Gem",
    "Earthquake Boots",
    "Vampstache",
    "Giant Arrow",
    "Healer Puppet",
    "Rage Gem",
    "Healing Tome",
    "Giant Gauntlet",
    "Frozen Arrow",
    "Hog Rider Puppet",
    "Haste Vial",
    "Fireball",
    "Spiky Ball",
    "Rocket Spear",
    "Lavaloon Puppet",
    "Magic Mirror",
    "Henchmen Puppet",
    "Dark Orb",
    "Electro Boots"
]

ACHIEVEMENT_ORDER = [
    # Home Base
    "Keep Your Account Safe!",
    "Bigger & Better",
    "Discover New Troops",
    "Bigger Coffers",
    "Gold Grab",
    "Elixir Escapade",
    "Heroic Heist",
    "Well Seasoned",
    "Nice and Tidy",
    "Empire Builder",
    "Clan War Wealth",
    "Friend in Need",
    "Sharing is caring",
    "Siege Sharer",
    "War Hero",
    "War League Legend",
    "Games Champion",
    "Unbreakable",
    "Sweet Victory!",
    "Conqueror",
    "League All-Star",
    "Humiliator",
    "Not So Easy This Time",
    "Union Buster",
    "Bust This!",
    "Wall Buster",
    "Mortar Mauler",
    "X-Bow Exterminator",
    "Firefighter",
    "Anti-Artillery",
    "Shattered and Scattered",
    "Counterspell",
    "Monolith Masher",
    "Get those Goblins!",
    "Get those other Goblins!",
    "Get even more Goblins!",
    "Dragon Slayer",
    "Ungrateful Child",
    "Superb Work",

    # Builder Base
    "Master Engineering",
    "Hidden Treasures",
    "High Gear",
    "Next Generation Model",
    "Un-Build It",
    "Champion Builder",
    
    # Clan Capital
    "Aggressive Capitalism",
    "Most Valuable Clanmate",
]

UNRANKED_LEAGUE_DATA = {
    "id": 29000000,
    "name": "Unranked",
    "iconUrls": {
        "small": "https://api-assets.clashofclans.com/leagues/72/e--YMyIexEQQhE4imLoJcwhYn6Uy8KqlgyY3_kFV6t4.png",
        "tiny": "https://api-assets.clashofclans.com/leagues/36/e--YMyIexEQQhE4imLoJcwhYn6Uy8KqlgyY3_kFV6t4.png",
    },
}
