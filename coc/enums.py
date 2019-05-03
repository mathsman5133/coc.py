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
