"""
MIT License

Copyright (c) 2019 mathsman5133

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


class CacheType(Enum):
    """Enum to map cache types to strings."""

    search_clans = "cache_search_clans"
    war_clans = "cache_war_clans"

    search_players = "cache_search_players"
    war_players = "cache_war_players"

    current_wars = "cache_current_wars"
    war_logs = "cache_war_logs"

    league_groups = "cache_league_groups"
    league_wars = "cache_league_wars"

    locations = "cache_locations"
    leagues = "cache_leagues"
    seasons = "cache_seasons"

    def __str__(self):
        return self.value


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
    "Minion",
    "Hog Rider",
    "Valkyrie",
    "Golem",
    "Witch",
    "Lava Hound",
    "Bowler",
    "Ice Golem",
    "Wall Wrecker",
    "Battle Blimp",
    "Stone Slammer",
]

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
    "Poison Spell",
    "Earthquake Spell",
    "Haste Spell",
    "Skeleton Spell",
    "Bat Spell",
]

HERO_ORDER = ["Barbarian King", "Archer Queen", "Grand Warden", "Battle Machine"]

SIEGE_MACHINE_ORDER = ["Wall Wrecker", "Battle Blimp", "Stone Slammer"]

ACHIEVEMENT_ORDER = [
    "Bigger Coffers",
    "Get those Goblins!",
    "Bigger & Better",
    "Nice and Tidy",
    "Release the Beasts",
    "Gold Grab",
    "Elixir Escapade",
    "Sweet Victory!",
    "Empire Builder",
    "Wall Buster",
    "Humiliator",
    "Union Buster",
    "Conqueror",
    "Unbreakable",
    "Friend in Need",
    "Mortar Mauler",
    "Heroic Heist",
    "League All-Star",
    "X-Bow Exterminator",
    "Firefighter",
    "War Hero",
    "Treasurer",
    "Anti-Artillery",
    "Sharing is caring",
    "Keep your village safe",
    "Master Engineering",
    "Next Generation Model",
    "Un-Build It",
    "Champion Builder",
    "High Gear",
    "Hidden Treasures",
    "Games Champion",
    "Dragon Slayer",
    "War League Legend",
    "Keep your village safe",
]
