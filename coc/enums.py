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


class Role(Enum):
    """Enum to map a player's role in the clan."""

    member = "member"
    elder = "admin"
    co_leader = "coLeader"
    leader = "leader"

    def __str__(self):
        return self.in_game_name

    @property
    def in_game_name(self) -> str:
        """Get a neat client-facing string value for the role."""
        lookup = {Role.member: "Member", Role.elder: "Elder", Role.co_leader: "Co-Leader", Role.leader: "Leader"}
        return lookup[self]


class WarRound(Enum):
    previous_war = 0
    current_war = 1
    current_preparation = 2

    def __str__(self):
        return self.name


class Resource(Enum):
    elixir = "Elixir"
    builder_elixir = "Elixir2"
    dark_elixir = "DarkElixir"
    gold = "Gold"


HOME_TROOP_ORDER = [
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
    "Minion",
    "Hog Rider",
    "Valkyrie",
    "Golem",
    "Witch",
    "Lava Hound",
    "Bowler",
    "Ice Golem",
    "Headhunter",
]

SIEGE_MACHINE_ORDER = [
    "Wall Wrecker",
    "Battle Blimp",
    "Stone Slammer",
    "Siege Barracks",
    "Log Launcher",
    "Flame Flinger"
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
    "Super Bowler"
]

HOME_TROOP_ORDER = HOME_TROOP_ORDER + SIEGE_MACHINE_ORDER


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
    "Super P.E.K.K.A",
    "Hog Glider",
]

SPELL_ORDER = [
    "Lightning Spell",
    "Healing Spell",
    "Rage Spell",
    "Jump Spell",
    "Freeze Spell",
    "Clone Spell",
    "Invisibility Spell",
    "Poison Spell",
    "Earthquake Spell",
    "Haste Spell",
    "Skeleton Spell",
    "Bat Spell",
]

HERO_ORDER = ["Barbarian King", "Archer Queen", "Grand Warden", "Royal Champion", "Battle Machine"]

HERO_PETS_ORDER = ["L.A.S.S.I", "Electro Owl", "Mighty Yak", "Unicorn"]

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
    "Get those Goblins!",
    "Get those other Goblins!",
    "Dragon Slayer",
    "Superb Work",

    # Builder Base
    "Master Engineering",
    "Hidden Treasures",
    "High Gear",
    "Next Generation Model",
    "Un-Build It",
    "Champion Builder",
]

UNRANKED_LEAGUE_DATA = {
    "id": 29000000,
    "name": "Unranked",
    "iconUrls": {
        "small": "https://api-assets.clashofclans.com/leagues/72/e--YMyIexEQQhE4imLoJcwhYn6Uy8KqlgyY3_kFV6t4.png",
        "tiny": "https://api-assets.clashofclans.com/leagues/36/e--YMyIexEQQhE4imLoJcwhYn6Uy8KqlgyY3_kFV6t4.png",
    },
}
