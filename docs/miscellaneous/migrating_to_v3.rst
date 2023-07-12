.. currentmodule:: coc
.. _migrating_to_v3_0:

Migrating to coc.py v3.0
========================

Most of the outward facing library is the same, with a few changes detailed below. Significant changes are caused
by builder base 2.0 update.

Logging in
----------

The functions :func:`coc.login` and :func:`coc.login_with_keys` were removed.
Use :func:`coc.Client.login` or :func:`coc.Client.login_with_tokens` instead.

Builder Base v2
---------------

The builder base revamp has caused a bunch of breaking changes.
The most significant change is renaming all the :attr:`versus` things to :attr:`builder_base` things,
but there were some additions and a removal as well:

- :func:`coc.Client.get_location_clans_versus` -> :func:`coc.Client.get_location_clans_builder_base`
- :func:`coc.Client.get_location_players_versus` -> :func:`coc.Client.get_location_players_builder_base`
- :func:`coc.Clan.versus_points` -> :func:`coc.Clan.builder_base_points`
- :func:`coc.RankedClan.versus_points` -> :func:`coc.RankedClan.builder_base_points`
- :func:`coc.ClanMember.versus_trophies` -> :func:`coc.ClanMember.builder_base_trophies`
- :func:`coc.ClanMember.versus_rank` -> :func:`coc.ClanMember.builder_base_rank`
- :func:`coc.RankedPlayer.versus_trophies` -> :func:`coc.RankedPlayer.builder_base_trophies`
- :func:`coc.Player.versus_trophies` -> :func:`coc.Player.builder_base_trophies`
- :func:`coc.Player.best_versus_trophies` -> :func:`coc.Player.best_builder_base_trophies`
- :func:`coc.LegendStatistics.previous_versus_season` -> :func:`coc.LegendStatistics.previous_builder_base_season`
- :func:`coc.LegendStatistics.best_versus_season` -> :func:`coc.LegendStatistics.best_builder_base_season`
- :func:`coc.Player.versus_attack_wins` was removed
- :func:`coc.Clan.required_builder_base_trophies` was added
- :func:`coc.ClanMember.builder_base_league` was added
- :func:`coc.Client.search_builder_base_leagues` was added
- :func:`coc.Client.get_builder_base_league` was added
- :func:`coc.Client.get_builder_base_league_named` was added

Game Objects
------------

coc.py game data was updated and now includes all the recently added troops and heros.
This is also reflected in the following enumerations:

- :class:`coc.HOME_TROOP_ORDER` now knows the "Apprentice Warden"
- :class:`coc.SUPER_TROOP_ORDER` now knows the "Super Hog Rider"
- in the :class:`coc.BUILDER_TROOPS_ORDER`, "Super P.E.K.K.A" got renamed to "Power P.E.K.K.A"
- :class:`coc.BUILDER_TROOPS_ORDER` now knows the "Electrofire Wizard"
- :class:`coc.HERO_ORDER` now knows the "Battle Copter"

Leagues
-------

Previously the structure of Leagues was a bit messy and not well aligned with what the API provides.
Therefore they got a small rework:

- :class:`WarLeague` was replaced with :class:`BaseLeague` which has the same attributes, but is also used for the builder base league and the clan capital league
- :class:`League` inherits from :class:`BaseLeague` now and adds the :attr:`icon` attribute which is present for home village leagues
- :class:`League` lost its :attr:`localized_name` and :attr:`localized_short_name` attributes as they are not present in the API

Furthermore
-----------

In order to get more in line with our coding style, the following methods were renamed:

- :func:`coc.Client.get_warlog` -> :func:`coc.Client.get_war_log`
- :func:`coc.Client.get_raidlog` -> :func:`coc.Client.get_raid_log`

:class:`coc.ClanMember` has a new cached property: :func:`player_house_elements`

:class:`coc.RaidDistrict` has a new :attr:`stars` attribute
