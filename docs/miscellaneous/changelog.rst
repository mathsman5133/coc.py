.. currentmodule:: coc

.. _whats_new:

Changelog
===========
This page keeps a fairly detailed, human readable version
of what has changed, and whats new for each version of the lib.

v3.9.1
------

Changes:
~~~~~~~~
- Minimum Python version required was changed from `3.7` to `3.9` as `3.7` and `3.8` are end-of-life.

Additions:
~~~~~~~~~~
- Added the achievement 'Supercharger'

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug when installing coc.py that would cause not all dependencies being installed

Removals:
~~~~~~~~~
- Removal of the `full_war_api` extension, as it is not longer maintained

v3.9.0
------

Additions:
~~~~~~~~~~
- Added the new Metal Pants & Snake Bracelet equipment to :class:`coc.EQUIPMENT`
- Added the new Troop Launcher Siege
- Updated static data & enums for the February 2025 update
- Changed from ujson to orjson for improved performance and future-proofing

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug that would cause :meth:`coc.Client.get_members` to return an empty list

v3.8.4
------

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug in army ids where "Super Hog Rider" was defined as "Super Hog"

v3.8.3
------

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug in several war related endpoints that passed realtime twice to the http client.

v3.8.2
------

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug with :func:`coc.Client.get_current_war` that caused it to not fetch the correct current CWL war

v3.8.1
------

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug with `**kwargs` in :class:`coc.Client` functions that caused duplicated values

v3.8.0
------

Additions:
~~~~~~~~~~
- Added the new Lavaloon & Electro Boots equipment to :class:`coc.EQUIPMENT`
- Added :func:`coc.Client.get_equipment`
- Added new Minion Prince hero to :class:`Hero`
- Updated static data & enums for TH17
- Added explicit cache control to every endpoint
   - Use :attr:`coc.Client.lookup_cache` (default `True`) or pass it as a kwarg to API calling methods (default `None`) to control whether a lookup in the cache is performed. If `None`, it defaults to :attr:`client.lookup_cache`.
   - Use :attr:`coc.Client.update_cache` to control whether the cache is updated after a request.
   - Use :attr:`coc.Client.ignore_cached_errors` to specify status codes to ignore in the cache. For example, cached `404 Not Found` responses can be bypassed by setting `ignore_cached_errors=[404]`.
- Moved `cls` functionality from `EventClient` to `Client` via :func:`coc.Client.set_object_cls`
   - Previously, `cls` could only be set at the `EventClient` level and applied to every event automatically. Now, it can be set directly in the normal `Client` when initializing and can override the API call if needed. This eliminates the need to change `cls` for every individual API call.

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug that would cause the first war of CWL to not appear while it was in prep & caused an index error appearing in output/logs
- :func:`coc.Client.verify_player_token` requests are no longer cached

v3.7.2
------

Additions:
~~~~~~~~~~
- Enable gzip and deflate encoding/compression

v3.7.1
------

Additions:
~~~~~~~~~~
- Added the new Magic Mirror equipment to :class:`coc.EQUIPMENT`
- updated static data

Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug that would cause coc.py to break if a request was sent with an empty string for a tag

v3.7.0
------

Additions:
~~~~~~~~~~
- Added inheritance of classes into the docs to make it easier to see what classes inherit from others.
- Added the new :class:`BattleModifier` to :attr:`ClanWar.battle_modifier` and :class:`ClanWarLogEntry.battle_modifier`.
- Added the new troop and equipment in June 2024 update to the static data.

Changes:
~~~~~~~~
- Changed the way the :class:`ClanWar` and :class:`ClanWarLogEntry` classes handles the :attr:`state` and :attr:`result`
  attribute, respectively. It now returns a :class:`WarState`/:class:`WarResult` enumeration object instead of a string
  to allow better type hinting and easier comparison.
- Updated the static data to reflect the June 2024 update changes.

v3.6.0
------

Bugs Fixed:
~~~~~~~~~~~
- Issues causing the documentation to not build properly have been fixed.
- Fixed a few spelling errors in the documentation.

Additions:
~~~~~~~~~~
- Added :attr:`coc.Client.ip` to manually overwrite the IP address used for generating API keys. This is especially useful
  for using the API with a proxy.

v3.5.3
------

Bugs Fixed:
~~~~~~~~~~~
- :attr:`coc.Badge.url` and :attr:`coc.Icon.url` now use differently sized fallbacks if the default URL is not
  available. The same is true if :func:`coc.Badge.save` or :func:`coc.Icon.save` are called without the optional
  size parameter
- corrected the default value for the ``league_id`` parameter of :func:`coc.Client.get_seasons` to point at Legends
  league and fixed a type hint in :func:`coc.Client.get_season_rankings` as well as a few doc strings

v3.5.2
------

Additions:
~~~~~~~~~~
- added the option to change the base url of the API in :class:`coc.Client` to allow an easier use of proxies
- added the new events :class:`coc.PlayerEvents.equipment_change` and :class:`coc.PlayerEvents.active_equipment_change`
- added the new names for builder base related events to :class:`coc.ClanEvents` and :class:`coc.PlayerEvents`
- added the change in the api model for ClanMembers. :class:`coc.ClanMember` now has a new attribute `town_hall` which
  is the town hall level.

Bugs Fixed:
~~~~~~~~~~~
- Fixed an issue with the renaming of versus_trophies to builder_base_trophies and similar name changes in the event
  related code

v3.4.2
------

Additions:
~~~~~~~~~~
- added the new Angry Jelly pet to :class:`coc.PETS_ORDER`
- updated static data to reflect the April 2024 update

v3.4.1
------

Additions:
~~~~~~~~~~
- added the missing achievements to :class:`coc.ACHIEVEMENT_ORDER`
- updated static data to reflect the March 26th balance patch

v3.4.0
------

Additions:
~~~~~~~~~~
- added the new Fireball equipment to :class:`coc.EQUIPMENT`

Bugs Fixed:
~~~~~~~~~~~
- Fixed an oversight that caused static equipment data not to be updated, which in turn resulted in some newer
  equipment pieces not showing up in :attr:`coc.Player.equipment` if game data was enabled
- Fixed some errors in the docs

v3.3.1
------

Bugs Fixed:
~~~~~~~~~~~
- Fixed a behaviour where in some cases (when the API responds with an unusual status code), coc.py would not
  properly raise an :class:`HTTPException`

v3.3.0
------

Additions:
~~~~~~~~~~
- Added dedicated enums for elixir/dark elixir troops and spells: `coc.ELIXIR_TROOP_ORDER`,
  `coc.DARK_ELIXIR_TROOP_ORDER`, `coc.ELIXIR_SPELL_ORDER` and `coc.DARK_ELIXIR_SPELL_ORDER`
- Added the new Overgrowth Spell
- Added the new equipment introduced since the last release (up to and including the February 2024 update)

Bugs Fixed:
~~~~~~~~~~~
- The Root Rider is now correctly sorted with the elixir troops

v3.2.1
------

Bugs Fixed:
~~~~~~~~~~~
- Fixed an issue that would cause spells to not be properly looked up, breaking :func:`coc.Client.get_spell` and
  :attr:`Player.spells`
- Fixed a month overflow issue with clan game start/end events that would occur from Dec 28th to Dec 31st

v3.2.0
------

Additions:
~~~~~~~~~~
- Added custom class support to a few more classes:

  - :class:`ClanWarMember` now supports the :attr:`attack_cls` attribute to customize the type returned in
    :func:`ClanWarMember.attacks` (and, by extension also :func:`WarClan.attacks` and :func:`ClanWar.attacks`)
  - :class:`WarClan` now supports the :attr:`member_cls` attribute to customize the type returned in
    :func:`WarClan.members` (and, by extension also :func:`ClanWar.members`)
  - :class:`ClanWar` now supports the :attr:`clan_cls` attribute to customize the types of
    :func:`ClanWar.clan` and :func:`ClanWar.opponent`
  - the :class:`Equipment` class can now be imported as ``coc.Equipment``

v3.1.0
------

Additions:
~~~~~~~~~~
- Added support for Hero Equipment:

  - an :class:`Equipment` class
  - a cached :func:`Player.equipment` property and :func:`Player.get_equipment` method. Equipment obtained this way
    will be enriched with game data if enabled
  - a :attr:`Hero.equipment` attribute to return the currently active equipment for a hero. Equipment obtained this
    way will never be enriched with game data and only have the basic ``name``, ``level``, ``max_level`` and ``village``
    attributes
- Added the new Root Rider troop
- Added the new Spirit Fox pet
- The :class:`ClanMember` class now has a :attr:``town_hall`` attribute that will also be present in
  :attr:`Clan.members` and :meth:`Clan.get_members`

Bugs Fixed:
~~~~~~~~~~~
- Fixed an issue that would cause troop and hero change events to fire even when no upgrades were detected
- Fixed the army link parser

v3.0.0
------
Please see :ref:`migrating_to_v3_0` for more info, as changes are described more in-depth there.


v2.4.1
------

Bugs Fixed:
~~~~~~~~~~~

- Fixed a bug with the retrieval of api keys

- Fixed :func:`ClanEvents.member_count`


v2.4.0
------
Additions:
~~~~~~~~~~

- Added support for Player Houses in the clan capital: :func:`coc.Player.player_house_elements`

- Added optional cls parameters to all the :func:`coc.Client.get_location_...` methods
  in order to allow the usage of custom classes

- Added the :ref:`triggers_extension` as an extension

- Added some cached properties to raid classes: :func:`coc.RaidClan.looted`,
  :func:`coc.RaidLogEntry.total_defensive_loot`, :func:`coc.RaidLogEntry.defense_attack_count`
  and :func:`coc.RaidLogEntry.defensive_destroyed_district_count`

- Added `before`, `after` and `limit` parameters to :func:`coc.Client.get_members`, :func:`coc.Client.get_warlog` and
  :func:`coc.Client.get_raidlog`

- Added :func:`coc.Client.search_war_leagues`, :func:`coc.Client.get_war_league`,
  :func:`coc.Client.get_war_league_named`, :func:`coc.Client.search_capital_leagues`,
  :func:`coc.Client.get_capital_league` and :func:`coc.Client.get_capital_league_named`


Changes:
~~~~~~~~

- Changed the default value of the :attr:`coc.Client.throttle_limit` to a more reasonable value (30 instead of 10)


Bugs Fixed:
~~~~~~~~~~~

- Fixed a bug which affected :func:`coc.Client.login_with_keys`

- Fixed a bug which caused an overwrite of user set parameters if the client was used with a context manager

- Fixed a bug which resulted in the client using more keys than the key_count was

- Fixed a bug which caused a wrong throttle_limit if :func:`coc.Client.login_with_keys` or
  :func:`coc.Client.login_with_tokens` was used

- Added previously missing Attribute :attr:`coc.RaidAttack.stars` which fixed a bug when checking
  if two :class:`coc.RaidAttack` objects are equal

- Fixed a bug in :func:`coc.WarEvents.new_war`

- Fixed a bug in :func:`coc.Client.get_current_war` which caused Exceptions or wrong return values


v2.3.1
------

- Added back :func:`coc.Client.get_location_clans_capital` which was accidentally reverted in 2.3.0

- Fixed some minor typos in the docs

v2.3.0
------
Additions:
~~~~~~~~~~

- Added new events :func:`ClientEvents.raid_weekend_start`, :func:`ClientEvents.raid_weekend_end`,
  :func:`ClientEvents.clan_games_start`, :func:`ClientEvents.clan_games_end`,
  :func:`WarEvents.new_war` and :func:`ClanEvents.member_versus_rank`

- Added utility functions :func:`utils.get_clan_games_start`, :func:`utils.get_clan_games_end`
  :func:`utils.get_raid_weekend_start` and :func:`utils.get_raid_weekend_end`

- Added clan capital leaderboards

- Added :attr:`Clan.capital_points` and :attr:`Clan.family_friendly`

- Added :attr:`ClanMember.versus_rank`

- Added :attr:`Client.raw_attribute` to control if the new `_raw_data` attribute of various objects gets populated

- Added `full_war_api` as an extension

- Added :func:`Client.login_with_tokens` offering the same functionality as :func:`Client.login_with_keys` as an asynchronous function


Changes:
~~~~~~~~

- Rename of LRU to FIFO in order to match the cache type (this is only internal)

- Restructured the documentation

- :func:`Client.login_with_keys` was marked as deprecated


Bugs Fixed:
~~~~~~~~~~~
- Fixed a bug which affected the key creation if there are 10 keys with at least one having the correct name but wrong ip range

- Fixed a memory leak caused by python not properly freeing disk space after the removal of cache entries

- Fixed a bug that prevented :attr:`Client.http.stats` from collecting api response time stats

- Fixed a bug that tried to use a cache when `max_cache_size` was set to 0

- Corrected order of elixir troops

- Fixed a bug when clans faced each other multiple times in one raid weekend

- Fixed a bug that caused automated tests on forks to fail

- Fixed a bug that prevented you from importing some classes as :class:`coc.Class`


v2.2.3
------
Bugs Fixed:
~~~~~~~~~~~

- Fixed some issues related to the documentation

- Fixed a bug which affected the max level for a townhall for various troops, spells and sieges

This release includes:
`#144 <https://github.com/mathsman5133/coc.py/pull/144>`_

v2.2.2
------
Additions:
~~~~~~~~~~

- Added "Super Miner" to the troops

Bugs Fixed:
~~~~~~~~~~~

- Fixed a bug with calculating the season start/end date

- Fixed a bug with calculating the amount of attacks for a :class:`WarClan`

- Fixed a bug with creating keys for realtime access accounts caused by a wrong scope

This release includes:
`#146 <https://github.com/mathsman5133/coc.py/pull/146>`_,
`#148 <https://github.com/mathsman5133/coc.py/pull/148>`_,
`#149 <https://github.com/mathsman5133/coc.py/pull/149>`_,
`#150 <https://github.com/mathsman5133/coc.py/pull/150>`_,
`#151 <https://github.com/mathsman5133/coc.py/pull/151>`_

v2.2.1
------
Bugs Fixed:
~~~~~~~~~~~

- Moved "Recall Spell" at the end of elixir spells (rather than end of all spells)

- Fixed a bug with CWL where the final war can be retrieved properly on the last day as `current_war`

- Fixed a bug with iterators and comparing clan tags to skip wars.


This release includes:
`#138 <https://github.com/mathsman5133/coc.py/pull/138>`_,
`#139 <https://github.com/mathsman5133/coc.py/pull/139>`_,
`#140 <https://github.com/mathsman5133/coc.py/pull/140>`_,



v2.2.0
------
This update has quite a bit of change without breaking backward compatibility.

For starters, support for the context manager was added #121 allowing the use of::

    async def main():
        async with coc.Client() as client:
            # do stuff...

    if __name__ == "__main__":
        asyncio.run(main())

Additionally, with the release of CapitalRaidSeasons we needed to improve the performance of fetching warlogs and capital raid logs. Previously, all records available from the API were fetched when in most cases, folks just needed the newest data. A `limit` parameter has been added to both `get_warlog` and `get_raidlog`.

Additionally, support for `async for warlog` has been added with the ability to fetch more data if needed.::

    raid_logs = await client.get_raidlog(clan_tag, page=True, limit=5)

    # Set `paginate=True` to enable fetching beyond the limit value until
    # there are more values to fetch
    count = 0
    async for i in raid_with_page:
        print(f"[{count}]-async limit: 5 page: True {i.start_time.time}")
        count += 1

This release includes:
`#121 <https://github.com/mathsman5133/coc.py/pull/121>`_,
`#122 <https://github.com/mathsman5133/coc.py/pull/122>`_,
`#130 <https://github.com/mathsman5133/coc.py/pull/130>`_,
`#131 <https://github.com/mathsman5133/coc.py/pull/131>`_,


v2.1.1
------
- Support for Clan Capitals!

- Updated our examples

- Bug fixes and improvements!

- Fixed bug with iterating over :meth:`Clan.get_detailed_members` where player objects were missing attributes #109

- Cleaned up how the async loop was being managed by library #111

- Please be sure to create issues for any bug fixes or feature requests!


v2.0.1
------
- New achievements for clan capital

- Switched to using Tuba's new links API (Thanks, Tuba)

- Get the IP Address from logging into the developer site to save an API call (Thanks, Roshan)


v2.0
-----
Please see :ref:`migrating_to_v2_0` for more info, as changes are described more in-depth there.

v1.3.0
------
- Added Dragon Rider and Rocket Balloon

- Added `cls` parameter for :meth:`Clan.get_detailed_members()`

- Troops no longer included in `Player.home_troops`

- :exc:`InvalidArgument` will now return a more helpful message.

- ``limit`` parameter is now correctly cached when using ``search_x`` endpoints.

- Added more typings and documentation improvements


v1.2.1
------
- Fixes an issue where `Clan.members` was empty if `Clan.get_member` was called before `Clan.members`.
    There was a similar issue with `Player.heroes` and `Player.spells`.

v1.2.0
------

- Adds new achievements and updated the order of existing ones.

- Added :attr:`Player.super_troops` and :attr:`Player.hero_pets`.

- Added :attr:`Troop.is_active` to check whether a super troop is active.

- Added :attr:`WarAttack.duration`

- Added :attr:`Clan.chat_language` which is a :class:`ChatLanguage` object.

- Fixed errors when coc.py tried to parse 5xx (e.g. 502) errors as HTML when they were dicts.

- Improved docs for :attr:`RankedPlayer.previous_rank`.


v1.1.0
------

- Adds support for the new Player API verification endpoint - see :meth:`Client.verify_player_token`

- Fixes a bug where members in `clan.get_detailed_members()` wouldn't have the `clan_rank` attribute, for example::

    # before
    async for member in clan.get_detailed_members():
        print(member.clan_rank)  # prints "None"

    # after
    async for member in clan.get_detailed_members():
        print(member.clan_rank)  # prints "1" or "10" or their clan rank.


- Fixes a bug where getting the warlog failed for clans with (>3yr) old war logs. See <https://github.com/mathsman5133/coc.py/issues/72>

- Fixed docs for :attr:`Player.clan_previous_rank` since it was misleading before.

v1.0.4
------

- Support aiohttp v3.7

- Add retry handling to the HTTPClient - if a request fails with a GatewayError (or TimeoutError), it will sleep and then retry for a maximum of 5 times.

- Super Minion, Super Wizard, Ice Hound, Log Launcher and Invisibility Spells were added.

v1.0.3
------

- Fixed an issue where the HTTP cache layer was not being utilised.

- Fixed an issue where :meth:`utils.get_season_start` and :meth:`utils.get_season_end` got the previous season information if the system time had not yet passed 5am UTC.



v1.0.2
------

- Fixed an issue where hitting Maintenance errors when using the normal Client would raise an Attribute Error.

- Fixed an issue where using `Clan.get_member` without calling `Clan.members` would build an incorrect player lookup dict.

- Fixed an issue where events wouldn't start because the maintenance event wasn't set properly.


v1.0.1
------

- Maintenance event poller logic has been reworked to enable the use of :class:`EventsClient` without any player/clan/war updates.

- 5min preparation time has been included in the list of valid prep times for friendly wars.

- The warlog example has been updated to properly close the client, and a typo fixed in the README example.

- The ``correct_tags`` parameter has been changed to default to ``True``. There is no side-effects of having this enabled.

v1.0
-----
Please see :ref:`migrating_to_v1_0` for more info, as the change-set is too large to describe here.

v0.3.3
-------
Breaking Changes
~~~~~~~~~~~~~~~~
- ``SearchPlayer.versus_attacks_wins`` has been renamed to ``SearchPlayer.versus_attack_wins``.
- The ``on_player_versus_attacks_change`` event has been renamed to ``on_player_versus_attack_change`` to match the above change.
- There was a typo with the spelling of the ``coc.Maintenance`` exception. It has been renamed from ``coc.Maitenance`` to ``coc.Maintenance``.

New Things
~~~~~~~~~~
- Add a default `Unranked` league to ``BasicPlayer.league``.
- Added TH13 content.

BugFixes
~~~~~~~~
- Fixed :meth:`client.get_members`` raising :exc:`AttributeError` if no clan is found in the cache.
- :meth:`client.get_warlog`` was only returning league wars. This has been fixed.


v0.3.2
-------
New Features.
~~~~~~~~~~~~~
- Rename :attr:`~SearchClan.member_dict` --> :attr:`~SearchClan.members_dict` for consistency.
- New helper function: :func:`LeagueGroup.get_wars(round_number)` which will return a
  :class:`LeagueWarIterator` of all SCCWL wars in that round.

Bug Fixes
~~~~~~~~~
- BugFix for cache not updating properly on clans going into prep.
- Add list of possible friendly war prep times (in seconds).
  If prep time is not in that list, assume random war.
  This helps when the API reports weird prep times that aren't exactly 23 hours for a random war.

v0.3.1
--------
New Features.
~~~~~~~~~~~~~
- :meth:`on_clan_member_trophy_change`, :meth:`on_clan_member_versus_trophy_change` and
  :meth:`on_clan_member_league_change` were added as new events.
- Add ability to pass async and other iterables into methods that return iterators.
- Add the `HogGlider` to list of builder base troops.
- Added support for `SearchClan.labels` and `SearchPlayer.labels`. They will return a :class:`~coc.Label` object.
- Add a special parameter to :class:`Client` to automatically "fix" or call :meth:`utils.correct_tag` on any tags passed in to calls.
- :func:`Client.get_clan_labels()` and :func:`Client.get_player_labels()` are now valid client calls.

BugFixes
~~~~~~~~
- Getting clans and players for a location will now default to getting for the global leaderboard.
- :class:`LeagueWar` will no longer throw an :exc:`AttributeError` when no clan is found.
- Never update the cache automatically when the :class:`EventsClient` is used.
- Fixed :meth:`WarEvents.on_war_state_change` not firing properly when a clan entered `preparation` or `warEnded`.

v0.3.0
-------
Bug Fixes
~~~~~~~~~
- All iterators have been fixed in python 3.7
- :meth:`ClanEvents.on_clan_member_join` will now fire events correctly
- Properly parse HTML errors thrown by CloudFlare
- Accessing the ``League.badge`` attribute has been fixed
- Clan events now sleep for the correct interval
- ``WarMember.town_hall`` has been fixed
- The API used to fetch IP has been changed (##19) to https://api.ipify.org/
- Ensure the clan is in war before trying to find prep time (##21)

New Things
~~~~~~~~~~
- Check out the `Cache` tab in sidebar for a how-to work with the new cache. It still works out of the box!
- You can now call utils with ``coc.utils.X``
- All events now have callbacks as an extra layer of security to stop them from failing.
- New Properties: ``Clan.share_link`` and ``Player.share_link``.
- Add ``utils.maybe_sort()`` as an easy tool to sort clan war attacks.
- All attributes that were prefaced with a ``_`` to dictate being iterables have been changed to be prefixed
  with ``iter``, ie. ``_attacks`` becomes ``iterattacks``.
- Rename ``SearchPlayer.level`` to ``SearchPlayer.exp_level`` - keep in line with API naming.
- Default value can be passed to ``BasicPlayer.league``; defaults to `None`
- Default value for ``SearchPlayer.builder_hall`` is 0.
- New Error: `PrivateWarLog`:

  - Subclass of `Forbidden` and a special case for when a 403 is thrown from trying to access war info for a clan with a private war log.
  - Redirect all `Forbidden` thrown errors in get_WARS methods to throw `PrivateWarLog`

  - A valid operation is to do either:

.. code-block:: python3

    try:
        await coc.get_current_war(...)
    except coc.Forbidden:
        pass

    # or:

    try:
        await coc.get_current_war(...)
    except coc.PrivateWarLog:
        pass

- ``EventsClient.add_X_update`` now accepts either a string or iterable.
- New Method: :meth:`client.remove_events()`` which works in the same way as :meth:`client.add_events()`
- Speed up `utils.get`
- New Events:
    - :meth:`PlayerEvents.joined_clan` - when a player joins a clan
    - :meth:`PlayerEvens.left_clan` - when a player leaves a clan
    - :meth:`on_player_clan_level_change` - when a player's clan's level changes
    - :meth:`on_player_clan_badge_change` - when a player's clan's badges change.
    - `on_client_close` which is dispatched upon closing the client

- Rename `x_achievement_update` --> `x_achievement_change` for consistency
- Add ``localised_name`` and ``localised_short_name`` attributes to :class:`League` and :class:`Location`
    - These have no effect at present.

Documentation
~~~~~~~~~~~~~
- Lots of the docs have had tidy-ups, with 2 new how-to's dedicated to Cache and the Events Client.



v0.2.0
--------
EventsClient
~~~~~~~~~~~~
- :class:`EventsClient`
- Provides all functionality of :class:`Client`, as well as an events-like system.
- It will constantly request to the API every X seconds and detect indifferences between the cached and new results
  returned by API. It will then send out 'events', basically calling functions that you must register, to tell you that
  these things have happened
- Split into 3 categories: player, clan and war

Player
~~~~~~
    - All events regarding anything in the API that can change.
    - E.g, name, troop levels (and unlocking), spells, heroes, donations, trophies etc.

Clans
~~~~~
    - All events regarding anything in the API that can change.
    - E.g. description, type (invite only etc.), ranks, donations etc. of members, levelups.

Wars
~~~~
    - All events regarding anything in the API that can change.
    - E.g. new war attack, war state change

- You must register the funtions events will call with :meth:`EventsClient.add_events`
- You must 'subscribe' any clans, players or (clans in) wars you want to get with :meth:`EventsClient.add_clan_updates`,
  :meth:`EventsClient.add_player_update`, :meth:`EventsClient.add_war_update`.

- This can be a script that you run and will continue to run forever, calling your functions as events come through,
  it doesn't have to be integrated into a bot. To ease this use-case, :meth:`EventsClient.run_forever` is handy.

Other Importants
~~~~~~~~~~~~~~~~
- Cache has had another overhaul about how it works, is called and default operational use.

- From above, ``default_cache`` is a kwarg, and method of :class:`Client`. It defaults to the inbuilt method,
  however you can pass your own function into this.

- Logging in: the new recommended way of logging in is via ``client = coc.login(email, pass, **kwargs)`` with ``client``
  being one of these kwargs: pass in either :class:`EventsClient` or :class:`Client` to use respective clients. This
  makes both Client class creation and HTTP logging in easy through one function. Any additional kwargs passed will become
  kwargs for the client you are using.

- ``CurrentWar`` has been renamed, revamped and relooked at. A regular clan-war is now a :class:`ClanWar`, with
  ``WarIterator`` being renamed to ``ClanWarIterator``. ``LeagueWarIterator`` and ``CurrentWarIterator`` now exist,
  Current wars being a mix of either clan or league wars.

- :meth:`Client.get_clan_war` now retrieves the current :class:`ClanWar`

- :meth:`Client.get_current_war` now attempts to retrieve the current :class:`ClanWar`, and if in the ``notInWar`` state,
  will attempt to search for a leauge war and return that, if found. This makes getting league wars and
  clan wars from the API much easier than before.
- :attr:`ClanWar.type` and :attr:`LeagueWar.type` now return a string of either ``cwl, friendly, random`` - which war type it is.
- :attr:`Timestamp.time` has been renamed to :attr:`Timestamp.raw_time`, and replaced with :attr:`Timestamp.utc_timestamp` (now called :attr:`Timestamp.time`)
- Add :attr:`ClanWar.status` returns a string ``winning, losing, tied, won, lost, tie`` depending on stars + destruction.

BugFixes
~~~~~~~~
- Lots of little ones with cache
- Performance upgrades with use of ``__slots__`` on more classes
- Trying to iterate over used up iterators
- Only log requests throttled as debug
- Trying to pop a cache item failed
- Few little regex and other bugs in cache.

v0.1.3
------
BugFixes
~~~~~~~~
- TypeError will no longer be raised if no tags were found
- Iterators will continue to search for next item if one fails

Important
~~~~~~~~~
New Properties/Attributes

    - :attr:`WarMember.is_opponent` indicates if the member is a clanmate (false) or opponent (true)
    - :attr:`SearchPlayer.ordered_home_troops`, :attr:`SearchPlayer.ordered_builder_troops` - returns an
      :class:`collections.OrderedDict` of players troops, in the order found in game.
      Note: Siege Machines are included at the end of this.
    - :attr:`SearchPlayer.ordered_spells` - same, but for spells
    - :attr:`SearchPlayer.ordered_heroes` - same, but for heroes.
    - :attr:`BaseWar.clan_tag` - all wars now have a permenant `clan_tag` attribute regardless of war state.
    - :attr:`cache.fully_populated` - helper bool to indicate if all possible items are cached,
      for eg. with locations and leagues - static information

New Methods:
~~~~~~~~~~~~
    - :meth:`client.get_league_named()` - get a league (ie. Bronze III etc.) by name.
    - :meth:`client.get_location_named()` - get a location (ie. Australia etc.) by name.
    - :meth:`cache.clear()` - reset the cache and clear all objects inside for that instance.
    - :meth:`cache.get_all_values()` - returns all values in the cache.
    - :meth:`cache.get_limit(limit)` - get the first limit number of items in cache.

New Iterators:
~~~~~~~~~~~~~~
    - :class:`PlayerIterator`, :class:`ClanIterator`, :class:`WarIterator` - returned when a function eg.
      :meth:`client.get_players(tags)` is called. These allow normal dot notion to be used inside `async for`,
      eg. `async for clan in client.get_clans(tags): print(clan.name)`.
    - :meth:`Iterator.flatten()` will return a list of all objects inside the iterator. Note: operation may be slow.

Changed Attribute:
~~~~~~~~~~~~~~~~~~
    - :attr:`SearchPlayer.troops_dict` has been changed to both :attr:`SearchPlayer.home_troops_dict` and
      :attr:`SearchPlayer.builder_troops_dict`, returning a dict of either home, or builder troops respectively.

    - :attr:`SearchPlayer.ordered_troops_dict` has been changed to both :attr:`SearchPlayer.ordered_home_troops_dict`
      and :attr:`SearchPlayer.ordered_builder_troops_dict`, returning a dict of either home, or builder troops respectively.

Removed Dependency:
~~~~~~~~~~~~~~~~~~~
    - `lru-dict` has been removed as a dependency due to a few windows problems while installing,
      and utilising :class:`collections.OrderedDict` appears to be faster.


Documentation
~~~~~~~~~~~~~

- Many type-hints were added to functions to aid IDE integration
- Documentation was re-written to use the NumPy style.
- Discord Bot examples were updated


v0.1.2
------
BugFixes
~~~~~~~~
- Fixed 2 problems which meant automatic token resets weren't working.
  Please report any more bugs!

v0.1.1
------
BugFixes
~~~~~~~~
- Stop nested asyncio loops from failing.

Important
~~~~~~~~~

- New methods

    - :meth:`.Client.get_clans(tags)` returns an AsyncIterator of clans.
    - :meth:`.Client.get_current_wars(tags)` returns an AsyncIterator of current wars
    - :meth:`.Client.get_players(tags)` returns an AsyncIterator of players
    - :meth:`.SearchClan.get_detailed_members` returns an AsyncIterator of :class:`.SearchPlayer` for clans members
    - :meth:`.Client.set_cache(*cache_names, max_size, expiry)` enables you to override the default cache settings
      on a per-cache basis. Expiry is in seconds.

- Removed parameters

    - ``json=False`` on all calls has been removed. Use :attr:`DataClass._data` to get the dict as returned by the API
      if you so desire

- Implemented ratelimits

    - ``throttle_limit`` has been added as a parameter to :class:`.Client`. This is the number of calls per token, per second,
      to be made

- asyncio.Semaphore lock has been implemented

- New cache structure and implementation.

    - Max size and expiry (in seconds) can be set with :meth:`Client.set_cache`
    - New instances of cache on a per-object (returned) basis, so different methods will implement
      different instances of the cache.
    - ``lru-dict`` has been added as a requirement.
    - LRU is very fast and memory efficient, written in C.

- Enum for :class:`CacheType` has been implemented. This is the preferred way to pass in ``cache_names`` to :meth:`Client.set_cache`
  as string names may change.

    - Can be called with :meth:`Client.set_cache(CacheType.search_clans, max_size=128, expiry=10)`

- New Exception: :exc:`InvalidCredentials`

    - This essentially replaces the (now redundant) :exc:`InvalidToken` exception, and is called when the email/pass pair
      passed is incorrect.

- New util function: :func:`coc.utils.clean_tag(tag, prefix='#')` will return a 'cleaned up' version of the tag.
  It will:

    - Make all letters UPPERCASE
    - Replace o ('oh') with 0 (zero)s
    - Remove non-alphanumeric and whitespace



v0.1.0
------
BugFixes
~~~~~~~~
- Fixed bug with loops breaking when reloading the client in a discord cog.
- A more specific error, ``aiohttp.ContentTypeError`` is raised when parsing non-json responses.

Important
~~~~~~~~~
- Big thanks to Jab for some of these.

- Big one! Client now only accepts an email/password pair rather than tokens.
  This pair is what you use to login to https://developer.clashofclans.com/#/login
  and will allow the client to automatically use, create, reset and find tokens,
  making it a much more streamlined process.


- As such, the following parameters to client have been added:

    - ``key_count``: int: the number of tokens to rotate between when making API requests.
      This defaults to 1, and can be between 1 and 10

    - ``key_names``: str: The name to use when creating tokens on the developer page.
      This defaults to `Created with coc.py Client`

- Email and Password are now mandatory parameters and must be passed

- `update_tokens` parameter has been removed. The client will automatically reset bad tokens.

- In order to keep consistency with the official API docs, `token` has been renamed to `key`.
  This affects the following method/parameters:

    - ``on_token_reset(new_token)`` --> ``on_key_reset(new_key)``
    - ``HTTPClient.login()`` --> ``HTTPClient.get_keys()``

  and otherwise consistent use of `key` during internals, docs, code and examples.

- `pytz` and `python-dateutil` have both been removed as dependencies due to the ability to
  parse timestamps manually. This has been added to utils as a function: ``from_timestamp(ts)``,
  returning a utc-datetime object.

- Dataclasses have received a makeover! Many new attributes are present, these are listed below.
  Most importantly, any property beginning with an underscore (_) use and return iterator objects.
  These are **not** lists, and relevant python documentation is here:
  https://docs.python.org/3/glossary.html#term-iterator.

  These are up to 12x faster than lists, and
  as such for those who are concerned about speed, performance and memory should use these, while
  for the majority, calling the regular property should be fine (usually returning a list rather than iter).

    -   :attr:`SearchClan._members`
    -   :attr:`WarClan._members`
    -   :attr:`WarClan._attacks`
    -   :attr:`WarClan._defenses`
    -   :attr:`WarMember._attacks`
    -   :attr:`WarMember._defenses`
    -   :attr:`SearchPlayer._achievements`
    -   :attr:`CurrentWar._attacks`
    -   :attr:`CurrentWar._members`
    -   :attr:`LeagueClan._members`
    -   :attr:`LeagueGroup._clans`

- The following **new** attributes were added:

    -   :attr:`SearchClan.member_dict`
    -   :attr:`WarClan.member_dict`
    -   :attr:`WarClan.attacks`
    -   :attr:`WarClan.defenses`
    -   :attr:`WarMember.attacks`
    -   :attr:`WarMember.defenses`
    -   :attr:`SearchPlayer.achievements_dict`
    -   :attr:`SearchPlayer.troops_dict`
    -   :attr:`SearchPlayer.heroes_dict`
    -   :attr:`SearchPlayer.spells_dict`
    -   :attr:`Timestamp.time`


- The folowwing **new** methods were added:

    -   `SearchClan.get_member(tag)`
    -   `CurrentWar.get_member(tag)`

- New utility functions:

    - `utils.get(iterable, **attrs)`
        - Searches the iterable until a value with the given attribute is found.
          Unlike ``filter()``, this will return when the first value is found.
    - `utils.find(function, iterable)`
        - Searches through the iterable until a value which satisfies the function is found.

    - `from_timestamp(ts)`
        - Parses an ISO8601 timestamp as returned by the COC API into a datetime object


Documentation:
~~~~~~~~~~~~~~
- Many docstrings were reformatted or worded, with punctuation and other typo's fixed
- All new properties, attributes and methods have been documented.
- Update some examples, including a `clan_info` function in discord bots (Thanks, Tuba).



v0.0.6
------
BugFixes
~~~~~~~~
- Fix bug with always raising RuntimeError

v0.0.5
-------
BugFixes
~~~~~~~~~
- Fixed how the lib detects an invalid IP error, as SC changed how the error message works
- Fixed bug with semi-complete URL when using the API dev site
- ``email`` and ``password`` in :class:`Client` are now ``None`` by default. This was throwing
  and error before.
- str() for :class:`Achievement`, :class:`Hero`, :class:`Troop`, :class:`Spell` now all return
  respective names

Important
~~~~~~~~~~

- Added a new exception: :exc:`Forbidden`. This is thrown when a 403 is returned, but the error is not
  one of invalid token, instead when you aren't allowed to get the resource eg. private war log.

- A :exc:`RuntimeError` will be raised if you try to pass ``update_stats`` as ``True`` but don't set
  the ``email`` or ``password``

- Added the :func:`Client.on_token_reset` which is called whenever the lib updates your token.
  By default this does nothing, however you can override it by either subclassing or
  using the decorator ``@Client.event()`` above your new ``async def on_token_reset``.
  This function can be a regular or coroutine.

Documentation
~~~~~~~~~~~~~~
- Add examples. I will expand on these as I see fit. Feel free to let me know if you want more.
- Fix broken codeblock examples
- Update incorrect function name in the example in README.rst (``player_name`` --> ``get_some_player``

v0.0.4
-------
BugFixes
~~~~~~~~~
- Fix some problems comparing naive and aware timestamps in :class:`.Timestamp`
- Add a private ``_data`` attribute to all data classes.
  This is the json as the API returns it. It makes ``json=True`` parameters in
  requests easy to handle.
- Only cache complete clan results - ie. ``Client.search_clans`` only returned a :class:`BasicClan`,
  so in order to add some cache consistency, cached clans now only contain :class:`SearchClan`.

Important
~~~~~~~~~~
- New Class - :class:`.LeagueWarLogEntry` is similar to :class:`WarLog`, however it has it's own
  set of attributes to ensure it is easier to use and know which ones are present and not.
- This new class is utilised in ``Client.get_warlog``, which returns a ``list`` of both
  ``LeagueWarLogEntry`` and ``WarLog``, depending on the war.

Documentation
~~~~~~~~~~~~~~
- Utilise `sphinx_rtd_theme` for the RTD page
- Add this changelog
- Continue to fix typos and little errors as they are found.


v0.0.2
-------
BugFixes
~~~~~~~~~
- Fix some attributes from inherited classes not being present
- Fix some :exc:`AttributeError` from being thrown due to incomplete data from API
- When a clan is not in war, :class:`.WarClan` will not be present.
  Some errors were being thrown due to incomplete data being given from API
- Allow for text-only responses from API (ie. not json)


Important Changes
~~~~~~~~~~~~~~~~~~
- Actually specify that the package coc needs to be installed when installing with pip
- Fix incorrect spelling of both :class:`.Achievement` and :exc:`InvalidArgument`
- Update the examples in the README to work (search_players is not a thing)


v0.0.1
-------
Initial Commit!
