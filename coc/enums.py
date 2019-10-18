from enum import Enum


class CacheType(Enum):
    search_clans = 'cache_search_clans'
    war_clans = 'cache_war_clans'

    search_players = 'cache_search_players'
    war_players = 'cache_war_players'

    current_wars = 'cache_current_wars'
    war_logs = 'cache_war_logs'

    league_groups = 'cache_league_groups'
    league_wars = 'cache_league_wars'

    locations = 'cache_locations'
    leagues = 'cache_leagues'
    seasons = 'cache_seasons'

    def __str__(self):
        return self.value


HOME_TROOP_ORDER = [
    'Barbarian',
    'Archer',
    'Giant',
    'Goblin',
    'Wall Breaker',
    'Balloon',
    'Wizard',
    'Healer',
    'Dragon',
    'P.E.K.K.A',
    'Baby Dragon',
    'Miner',
    'Electro Dragon',
    'Minion',
    'Hog Rider',
    'Valkyrie',
    'Golem',
    'Witch',
    'Lava Hound',
    'Bowler',
    'Ice Golem',
    'Wall Wrecker',
    'Battle Blimp',
    'Stone Slammer'
]

BUILDER_TROOPS_ORDER = [
    'Raged Barbarian',
    'Sneaky Archer',
    'Boxer Giant',
    'Beta Minion',
    'Bomber',
    'Baby Dragon',
    'Cannon Cart',
    'Night Witch',
    'Drop Ship',
    'Super P.E.K.K.A',
    'Hog Glider'
]

SPELL_ORDER = [
    'Lightning Spell',
    'Healing Spell',
    'Rage Spell',
    'Jump Spell',
    'Freeze Spell',
    'Clone Spell',
    'Poison Spell',
    'Earthquake Spell',
    'Haste Spell',
    'Skeleton Spell',
    'Bat Spell'
]

HERO_ORDER = [
    'Barbarian King',
    'Archer Queen',
    'Grand Warden',
    'Battle Machine'
]

SIEGE_MACHINE_ORDER = [
    'Wall Wrecker',
    'Battle Blimp',
    'Stone Slammer'
]

ACHIEVEMENT_ORDER = [
    'Bigger Coffers',
    'Get those Goblins!',
    'Bigger & Better',
    'Nice and Tidy',
    'Release the Beasts',
    'Gold Grab',
    'Elixir Escapade',
    'Sweet Victory!',
    'Empire Builder',
    'Wall Buster',
    'Humiliator',
    'Union Buster',
    'Conqueror',
    'Unbreakable',
    'Friend in Need',
    'Mortar Mauler',
    'Heroic Heist',
    'League All-Star',
    'X-Bow Exterminator',
    'Firefighter',
    'War Hero',
    'Treasurer',
    'Anti-Artillery',
    'Sharing is caring',
    'Keep your village safe',
    'Master Engineering',
    'Next Generation Model',
    'Un-Build It',
    'Champion Builder',
    'High Gear',
    'Hidden Treasures',
    'Games Champion',
    'Dragon Slayer',
    'War League Legend',
    'Keep your village safe'
]


CORRECT_PLAYER_LABELS = {
    56000000: {
        "small": "https://api-assets.clashofclans.com/labels/64/JOzAO4r91eVaJELAPB-iuAx6f_zBbRPCLM_ag5mpK4s.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/JOzAO4r91eVaJELAPB-iuAx6f_zBbRPCLM_ag5mpK4s.png"
    },
    56000001: {
        "small": "https://api-assets.clashofclans.com/labels/64/tINt65InVEc35rFYkxqFQqGDTsBpVRqY9K7BJf5kr4A.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/tINt65InVEc35rFYkxqFQqGDTsBpVRqY9K7BJf5kr4A.png",
    },
    56000002: {
        "small": "https://api-assets.clashofclans.com/labels/64/LIXkluJJeg4ATNVQgO6scLheXxmNpyBLRYGldtv-Miw.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/LIXkluJJeg4ATNVQgO6scLheXxmNpyBLRYGldtv-Miw.png"
    },
    56000003: {
        "small": "https://api-assets.clashofclans.com/labels/64/UEjY-kAdKcE6bPfI_X1L4s-ADYI_IJLuxx5cmClykdU.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/UEjY-kAdKcE6bPfI_X1L4s-ADYI_IJLuxx5cmClykdU.png"
    },
    56000004: {
        "small": "https://api-assets.clashofclans.com/labels/64/ZxJp9606Vl1sa0GHg5JmGp8TdHS4l0jE4WFuil1ENvA.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/ZxJp9606Vl1sa0GHg5JmGp8TdHS4l0jE4WFuil1ENvA.png"
    },
    56000005: {
        "small": "https://api-assets.clashofclans.com/labels/64/8Q08M2dj1xz1Zx-sAre6QO14hOX2aiEvg-FaGGSX-7M.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/8Q08M2dj1xz1Zx-sAre6QO14hOX2aiEvg-FaGGSX-7M.png"
    },
    56000006: {
        "small": "https://api-assets.clashofclans.com/labels/64/PcgplBTQo2W_PXYqMi0i6g6nrNMjzCM8Ipd_umSnuHw.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/PcgplBTQo2W_PXYqMi0i6g6nrNMjzCM8Ipd_umSnuHw.png"
    },
    56000007: {
        "small": "https://api-assets.clashofclans.com/labels/64/L1JDFhgOJyt1jcNnb6-IkBddd9vQSn2UeoQQGjVLEYI.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/L1JDFhgOJyt1jcNnb6-IkBddd9vQSn2UeoQQGjVLEYI.png"
    },
    56000008: {
        "small": "https://api-assets.clashofclans.com/labels/64/mcWhk0ii7CyjiiHOidhRofrSulpVrxjDu24cQtGCQbE.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/mcWhk0ii7CyjiiHOidhRofrSulpVrxjDu24cQtGCQbE.png"
    },
    56000009: {
        "small": "https://api-assets.clashofclans.com/labels/64/jEvZf9PnfPaqYh2PMLBoJfB1BoBpomerqmsYWDYisKY.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/jEvZf9PnfPaqYh2PMLBoJfB1BoBpomerqmsYWDYisKY.png"
    },
    56000010: {
        "small": "https://api-assets.clashofclans.com/labels/64/H75LWbZqe5Lm2rXYUrEDgQNa3kpZdtFCjiyvnNSvh00.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/H75LWbZqe5Lm2rXYUrEDgQNa3kpZdtFCjiyvnNSvh00.png"
    },
    56000011: {
        "small": "https://api-assets.clashofclans.com/labels/64/aKHRoHhkn6n3wj09tWxAA3DfKL6s45dHe3_VtKgkkhQ.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/aKHRoHhkn6n3wj09tWxAA3DfKL6s45dHe3_VtKgkkhQ.png"
    },
    56000012: {
        "small": "https://api-assets.clashofclans.com/labels/64/MvL0LDt0yv9AI-Vevpu8yE5NAJUIV05Ofpsr4IfGRxQ.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/MvL0LDt0yv9AI-Vevpu8yE5NAJUIV05Ofpsr4IfGRxQ.png"
    },
    56000013: {
        "small": "https://api-assets.clashofclans.com/labels/64/sy5nJmT4BFjS4iT4_iILE02rfrO8VjgpGKFE0rLmot4.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/sy5nJmT4BFjS4iT4_iILE02rfrO8VjgpGKFE0rLmot4.png"
    },
    56000014: {
        "small": "https://api-assets.clashofclans.com/labels/64/gwTgG4oOwkse3eCpFL05AFArJMmMULIlecXNrl1Mv2g.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/gwTgG4oOwkse3eCpFL05AFArJMmMULIlecXNrl1Mv2g.png"
    },
    56000015: {
        "small": "https://api-assets.clashofclans.com/labels/64/DfTPKAsvjdsD-CFfbpmfIJiT2uF3FQLfftRdJgBA37Y.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/DfTPKAsvjdsD-CFfbpmfIJiT2uF3FQLfftRdJgBA37Y.png"
    },
    56000016: {
        "small": "https://api-assets.clashofclans.com/labels/64/u-VKK5y0hj0U8B1xdawjxNcXciv-fwMK3VqEBWCn1oM.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/u-VKK5y0hj0U8B1xdawjxNcXciv-fwMK3VqEBWCn1oM.png"
    },
    56000017: {
        "small": "https://api-assets.clashofclans.com/labels/64/t0KZ4173i9vJFrD5F06-2TFNFk9UwJXxPjfutcG-dig.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/t0KZ4173i9vJFrD5F06-2TFNFk9UwJXxPjfutcG-dig.png"
    }
}

CORRECT_CLAN_LABELS = {
    56000000: {
        "small": "https://api-assets.clashofclans.com/labels/64/5w60_3bdtYUe9SM6rkxBRyV_8VvWw_jTlDS5ieU3IsI.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/5w60_3bdtYUe9SM6rkxBRyV_8VvWw_jTlDS5ieU3IsI.png"
    },
    56000001: {
        "small": "https://api-assets.clashofclans.com/labels/64/hNtigjuwJjs6PWhVtVt5HvJgAp4ZOMO8e2nyjHX29sA.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/hNtigjuwJjs6PWhVtVt5HvJgAp4ZOMO8e2nyjHX29sA.png",
    },
    56000002: {
        "small": "https://api-assets.clashofclans.com/labels/64/7qU7tQGERiVITVG0CPFov1-BnFldu4bMN2gXML5bLIU.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/7qU7tQGERiVITVG0CPFov1-BnFldu4bMN2gXML5bLIU.png"
    },
    56000003: {
        "small": "https://api-assets.clashofclans.com/labels/64/kyuaiAWdnD9v3ReYPS3_x6QP3V3e0nNAPyDroOIDFZQ.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/kyuaiAWdnD9v3ReYPS3_x6QP3V3e0nNAPyDroOIDFZQ.png"
    },
    56000004: {
        "small": "https://api-assets.clashofclans.com/labels/64/lXaIuoTlfoNOY5fKcQGeT57apz1KFWkN9-raxqIlMbE.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/lXaIuoTlfoNOY5fKcQGeT57apz1KFWkN9-raxqIlMbE.png"
    },
    56000005: {
        "small": "https://api-assets.clashofclans.com/labels/64/3oOuYkPdkjWVrBUITgByz9Ur0nmJ4GsERXc-1NUrjKg.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/3oOuYkPdkjWVrBUITgByz9Ur0nmJ4GsERXc-1NUrjKg.png"
    },
    56000006: {
        "small": "https://api-assets.clashofclans.com/labels/64/DhBE-1SSnrZQtsfjVHyNW-BTBWMc8Zoo34MNRCNiRsA.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/DhBE-1SSnrZQtsfjVHyNW-BTBWMc8Zoo34MNRCNiRsA.png"
    },
    56000007: {
        "small": "https://api-assets.clashofclans.com/labels/64/T1c8AYalTn_RruVkY0mRPwNYF5n802thTBEEnOtNTMw.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/T1c8AYalTn_RruVkY0mRPwNYF5n802thTBEEnOtNTMw.png"
    },
    56000008: {
        "small": "https://api-assets.clashofclans.com/labels/64/6NxZMDn9ryFw8-FHJJimcEkKwnXZHMVUp_0cCVT6onY.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/6NxZMDn9ryFw8-FHJJimcEkKwnXZHMVUp_0cCVT6onY.png"
    },
    56000009: {
        "small": "https://api-assets.clashofclans.com/labels/64/ImSgCg88EEl80mwzFZMIiJTqa33bJmJPcl4v2eT6O04.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/ImSgCg88EEl80mwzFZMIiJTqa33bJmJPcl4v2eT6O04.png"
    },
    56000010: {
        "small": "https://api-assets.clashofclans.com/labels/64/zyaTKuJXrsPiU3DvjgdqaSA6B1qvcQ0cjD6ktRah4xs.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/zyaTKuJXrsPiU3DvjgdqaSA6B1qvcQ0cjD6ktRah4xs.png"
    },
    56000011: {
        "small": "https://api-assets.clashofclans.com/labels/64/iLWz6AiaIHg_DqfG6s9vAxUJKb-RsPbSYl_S0ii9GAM.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/iLWz6AiaIHg_DqfG6s9vAxUJKb-RsPbSYl_S0ii9GAM.png"
    },
    56000012: {
        "small": "https://api-assets.clashofclans.com/labels/64/Kv1MZQfd5A7DLwf1Zw3tOaUiwQHGMwmRpjZqOalu_hI.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/Kv1MZQfd5A7DLwf1Zw3tOaUiwQHGMwmRpjZqOalu_hI.png"
    },
    56000013: {
        "small": "https://api-assets.clashofclans.com/labels/64/RauzS-02tv4vWm1edZ-q3gPQGWKGANLZ-85HCw_NVP0.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/RauzS-02tv4vWm1edZ-q3gPQGWKGANLZ-85HCw_NVP0.png"
    },
    56000014: {
        "small": "https://api-assets.clashofclans.com/labels/64/LG966XuC6YoEJsPthcgtyJ8uS46LqYDAeiHJNQKR3YQ.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/LG966XuC6YoEJsPthcgtyJ8uS46LqYDAeiHJNQKR3YQ.png"
    },
    56000015: {
        "small": "https://api-assets.clashofclans.com/labels/64/hM7SHnN0x7syFa-s6fE7LzeO5yWG2sfFpZUHuzgMwQg.png",
        "medium": "https://api-assets.clashofclans.com/labels/128/hM7SHnN0x7syFa-s6fE7LzeO5yWG2sfFpZUHuzgMwQg.png"
    }
}


class LabelType(Enum):
    player = CORRECT_PLAYER_LABELS
    clan = CORRECT_CLAN_LABELS
