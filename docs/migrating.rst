.. currentmodule:: coc
.. _migrating_to_v1_0:

Migrating to coc.py v1.0
========================
v1.0 is a complete rewrite of the library, from top to bottom, and no effort was made to maintain backwards compatibility.

Most notably, all models have been rewritten and the :class:`EventsClient` has undergone a significant refactor.

All exceptions and iterators remain the same, and :class:`Client` methods remain similar.

Clans
-----
The naming of clan objects has been changed to align with the API naming, and to improve understand of what each model represents and where it may come from.

For example, previously, ``coc.BasicClan`` was an abstract name to describe a clan with limit information, belonging to a player, as returned in the :meth:`Client.get_player` method.
It has been renamed to :class:`coc.PlayerClan`.

+--------------------+-------------------------+
|      Before        |        After            |
+--------------------+-------------------------+
| ``coc.Clan``       | :class:`coc.BaseClan`   |
+--------------------+-------------------------+
| ``coc.BasicClan``  | :class:`coc.PlayerClan` |
+--------------------+-------------------------+
| ``coc.SearchClan`` | :class:`coc.Clan`       |
+--------------------+-------------------------+

Additionally, :class:`RankedClan` was added.
This is returned when the :meth:`Client.get_location_clans` or :meth:`Client.get_location_clans_versus` are called.
Also, :class:`ClanWarLeagueClan` was added, which represents a CWL clan retrieved in the :meth:`Client.get_league_group` method.

Properties and Methods
~~~~~~~~~~~~~~~~~~~~~~

+--------------------------+----------------------------+
|        Before            |         After              |
+--------------------------+----------------------------+
| ``Clan.iterlabels``      | :attr:`Clan.labels`        |
+--------------------------+----------------------------+
| ``Clan.itermembers``     | :attr:`Clan.members`       |
+--------------------------+----------------------------+
| ``Clan.members_dict``    | Removed                    |
+--------------------------+----------------------------+
| ``Clan.get_member``      | :meth:`Clan.get_member_by` |
+--------------------------+----------------------------+
| ``WarClan.itermembers``  | :attr:`Clan.members`       |
+--------------------------+----------------------------+
| ``WarClan.iterattacks``  | :attr:`WarClan.attacks`    |
+--------------------------+----------------------------+
| ``WarClan.iterdefenses`` | :attr:`WarClan.defenses`   |
+--------------------------+----------------------------+

A quick example about the use of :meth:`Clan.get_member` and :meth:`Clan.get_member_by`:

.. code-block:: python3

    # before
    member = clan.get_member(name="Bob the Builder")
    member = clan.get_member(tag="#P02VLYC")

    # after
    member = clan.get_member_by(name="Bob the Builder")
    member = clan.get_member("#P02VLYC")

This change vastly improves the efficiency of :meth:`Clan.get_member`.

Clans now have a ``__eq__`` comparison that is based on their tag. For example:

.. code-block:: python3

    # before
    player = await client.get_player('#P02VLYC')
    clan = await client.get_clan(player.clan.tag)
    assert player.clan == clan  # False

    # after
    player = await client.get_player('#P02VLYC')
    clan = await client.get_clan(player.clan.tag)
    assert player.clan == clan  # True


Players
--------
As with clans, the naming of player classes have also changed to align with API naming and improve readability of what an object contains.

+----------------------+----------------------------+
|      Before          |        After               |
+----------------------+----------------------------+
| ``coc.Player``       | :class:`coc.BasePlayer`    |
+----------------------+----------------------------+
| ``coc.BasicPlayer``  | :class:`coc.ClanMember`    |
+----------------------+----------------------------+
| ``coc.WarMember``    | :class:`coc.ClanWarMember` |
+----------------------+----------------------------+
| ``coc.SearchPlayer`` | :class:`coc.Player`        |
+----------------------+----------------------------+

Additionally, :class:`RankedPlayer` was added. This is returned when the :meth:`Client.get_location_players` or :meth:`Client.get_location_players_versus` are called.

Properties and Methods
~~~~~~~~~~~~~~~~~~~~~~

+-------------------------------------------+----------------------------------+
|        Before                             |         After                    |
+-------------------------------------------+----------------------------------+
| ``WarMember.iterattacks`                  | :attr:`ClanWarMember.attacks`    |
+-------------------------------------------+----------------------------------+
| ``WarMember.iterdefenses`                 | :attr:`ClanWarMember.defenses`   |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.iterachievements``         | :attr:`Player.achievements`      |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.iterlabels``               | :attr:`Player.labels`            |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.ordered_builder_troops``   | :attr:`Player.builder_troops`    |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.ordered_heroes``           | :attr:`Player.heroes`            |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.ordered_home_troops``      | :attr:`Player.home_troops`       |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.ordered_siege_machines``   | :attr:`Player.siege_machines`    |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.ordered_spells``           | :attr:`Player.spells`            |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.achievements_dict``        | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.builder_troops_dict``      | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.get_ordered_troops()``     | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.heroes_dict``              | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.home_troops_dict``         | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.ordered_super_troops``     | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.siege_machines_dict``      | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.spells_dict``              | Removed                          |
+-------------------------------------------+----------------------------------+
| ``SearchPlayer.super_troops_dict``        | Removed                          |
+-------------------------------------------+----------------------------------+
| Didn't exist                              | :meth:`Player.get_hero`          |
+-------------------------------------------+----------------------------------+
| Didn't exist                              | :meth:`Player.get_achievement`   |
+-------------------------------------------+----------------------------------+
| Didn't exist                              | :meth:`Player.legend_statistics` |
+-------------------------------------------+----------------------------------+

You will notice that a number of ``_dict`` and ``ordered_`` attributes were removed.
All properties returning troops and spells are now ordered, apart from :attr:`Player.troops`.
This is due to the baby dragon being in both home and builder troops, making it difficult to sort these troops,
at the expense of a less efficient property it has been decided to not order these.
Please use :attr:`Player.home_troops` or :attr:`Player.builder_troops` instead.

In addition, all properties return lists of their object (achievements, troops, spells, etc.).
This change was made to improve consistency and fluidity. Objects that are commonly used with a lookup
(achievements and heroes) are now stored internally as dicts, and a fast lookup can be performed with
:meth:`Player.get_hero` or :meth:`Player.get_achievement`. This is significantly faster than iterating over their
list counterparts.

Super troop support has been removed from the library until Supercell adds support for this to their API.

As with clans, players now have a useful ``__eq__`` operation that compares based on player tag.

.. code-block:: python3

    # before
    clan = await client.get_clan('#P02VLYC')
    player = await client.get_player(clan.members[0].tag)
    assert player == clan.members[0]  # False

    # after
    clan = await client.get_clan('#P02VLYC')
    player = await client.get_player(clan.members[0].tag)
    assert player == clan.members[0]  # True



Wars
----

As with players and clans, the naming of war classes have also changed to align with API naming and improve readability of what an object contains.

+---------------------+---------------------------------+
|      Before         |        After                    |
+---------------------+---------------------------------+
| ``coc.BaseWar``     | Removed                         |
+---------------------+---------------------------------+
| ``coc.WarLog``      | :class:`coc.ClanWarLogEntry`    |
+---------------------+---------------------------------+
| ``coc.LeagueGroup`` | :class:`coc.ClanWarLeagueGroup` |
+---------------------+---------------------------------+
| ``coc.LeagueWar``   | :class:`coc.ClanWar`            |
+---------------------+---------------------------------+

Note that :class:`coc.ClanWar` has not been renamed, although a LeagueWar is now bundled in with a ClanWar.

Properties and Methods
~~~~~~~~~~~~~~~~~~~~~~

+-------------------------+-----------------------------------------+
|        Before           |         After                           |
+-------------------------+-----------------------------------------+
| ``ClanWar.get_member``  | :meth:`ClanWar.get_member_by`           |
+-------------------------+-----------------------------------------+
| ``ClanWar.iterattacks`` | :meth:`ClanWar.attacks`                 |
+-------------------------+-----------------------------------------+
| ``ClanWar.itermembers`` | :meth:`ClanWar.members`                 |
+-------------------------+-----------------------------------------+
| Didn't exist            | :meth:`ClanWar.get_member`              |
+-------------------------+-----------------------------------------+
| Didn't exist            | :meth:`ClanWar.get_attack`              |
+-------------------------+-----------------------------------------+
| Didn't exist            | :attr:`ClanWar.is_cwl`                  |
+-------------------------+-----------------------------------------+
| Didn't exist            | :attr:`ClanWarLogEntry.is_league_entry` |
+-------------------------+-----------------------------------------+
| Didn't exist            | :attr:`WarAttack.is_fresh_attack`       |
+-------------------------+-----------------------------------------+


Cache
------

The entire "custom cache" section of the library has been removed. It was inefficient, not used and has been replaced
by a basic dictionary lookup-style cache. Please remove any references to the previous ``coc.Cache`` and assosiated classes.

Instead, objects will be cached automatically by the HTTP client until they are stale, that is a "fresh" object is available from
the API, at which point the library will retrieve and cache that. This is done based on the ``Cache-Control`` headers
returned by the API. Support may be made for setting custom cache expiries in the future.

Throttlers
-----------

A new throttler, :class:`coc.BasicThrottler` has been introduced as the new default throttler. It works on a "sleep between requests" approach,
which means that if you set the throttle limit to be 10, with 1 token, the library will speep for 0.1 seconds between each request.

The previous default throttler, :class:`coc.BatchThrottler` is still available and can be set by passing a kwarg to :meth:`coc.login`: ::

    client = coc.login("email", "password", throttler=coc.BatchThrottler)

This throttler works based on allowing the number of requests per second in, then sleeping until the next second passes.
For example, if you set the throttle limit to be 10, with 1 token, the library will let 10 requests in consecutively,
however will sleep until the next second when you request with the 11th, and so forth.


Events
-------

The events partition of the library has undergone a complete rewrite. Events are checked for and dispatched on-demand,
making them vastly more efficient.

Dynamic Predicates
~~~~~~~~~~~~~~~~~~
For example, if you wanted to know when a clan had changed their description, before
the library would check for your description change, as well as checking if every single other attribute of the clan
had changed. Now, it will only check to see if the description has changed every loop.

Decorators
~~~~~~~~~~
Events are no longer hard-coded into the library. This creates a more future-proof design, and adds support for a custom attribute
you may have with custom classes. Events are no longer defined by their function name, too, instead the name of the decorator assigned.

For example:

.. code-block:: python3

    # before
    @client.event
    async def on_clan_member_donations_change(old_donations, new_donations, player):
        ...

    # after
    @client.event
    @coc.ClanEvents.member_donations()
    async def my_cool_function_name(old_player, new_player):
        ...

This may appear more verbose, but it is clearer, more efficient and consistent.

The naming of the attribute following the event group's class is important. It should represent the name of the attribute
you wish to check in the predicate. For clan member events, this should be prefaced with ``member_``, and for a players' clans,
this should be prefaced with ``clan_``.

For example:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.trophies()  # an event that is run for every player, when their `.trophies` attribute changes.
    async def foo(...): ...

    @client.event
    @coc.WarEvents.state()  # an event that is run when a war `.state` has changed
    async def foo(...): ...

    @client.event
    @coc.ClanEvents.public_war_log()  # an event that is run when a clan's `.public_war_log` attribute has changed.
    async def foo(...): ...

    @client.event
    @coc.ClanEvents.member_donations()  # an event that is run for every clan member when their `.donations` have changed.
    async def foo(...): ...

    @client.event
    @coc.PlayerEvents.clan_level()  # an event that is called when a player's clan's level has changed.
    async def foo(...): ...

You can also stack decorators to get multiple events reported to one callback:

.. code-block:: python3

    @client.event
    @coc.ClanEvents.public_war_log()
    @coc.ClanEvents.description()
    @coc.ClanEvents.level()
    async def foo(old_clan, new_clan):
        if old_clan.level != new_clan.level:
            ...


Callback Arguments
~~~~~~~~~~~~~~~~~~~

Previously, events followed a rough ``old_value, new_value, object`` argument order. This wasn't always consistent between objects,
and so in v1.0.0 event callbacks will follow a much more consistent design, consisting of ``old_object, new_object``.
Inevitably there will be exceptions, but these will be few and well documented.

For example:

.. code-block:: python3

    # before
    @client.event
    async def on_clan_member_donations_change(old_donations, new_donations, member):
        assert old_donations != new_donations  # True

    # after
    @client.event
    @coc.ClanEvents.member_donations()
    async def foo(old_member, new_member):
        assert old_member.donations != new_member.donations  # True

Retry / Refresh Intervals
~~~~~~~~~~~~~~~~~~~~~~~~~
Also, unless you wish to only check for new events once every hour or 6 hours, or any time greater than the refresh time
for objects in the API, it is suggested to omit the ``retry_interval`` parameter. The library will automatically
determine when the next fresh object is available, and instead of sleeping for a predefined 60seconds between every loop,
it will instead sleep until a fresh object is available from the API. This means some events could see an up to 50% reduction in
latency between when the event happens in game and when coc.py reports it.

For example:

.. code-block:: python3

    # before
    @client.event
    async def on_clan_level_change(...): ...

    client.add_clan_update(tags, retry_interval=60)  # to check for new events every 60 seconds

    # after
    @client.event
    @coc.ClanEvents.level()
    async def foo(...): ...  # check as often as API updates the clan for an event

    @client.event
    @coc.ClanEvents.level(retry_interval=60)  # check every 60 seconds for a new event
    async def foo(...): ...


Adding Clan and Player Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Previously, events would require a lot of lines of function calls to get events up and running.
These have been streamlined into the decorator, and suggested registering of clan tags is via the decorator.
This makes for much cleaner and readable code.

For example:

.. code-block:: python3

    # before
    @client.event
    async def on_player_name_change(...): ...

    client.add_player_updates(['#tag', '#tag2', '#tag3', ...])

    # after
    @client.event
    @coc.PlayerEvents.name(tags=['#tag', '#tag2', '#tag3'])
    async def foo(...): ...

    # alternatively, if you must:
    @client.event
    @coc.PlayerEvents.name()
    async def foo(...): ...

    client.add_player_updates('#tag', '#tag2', '#tag3')

A few points to note:

- Tags will be automatically corrected via the :meth:`coc.correct_tag` function.

- *Every* tag that is added to the client will be sent to each function. This makes for a much simpler internal design.


For Example:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.exp_level("#tag1")
    async def foo(...):
        # events will be received for #tag1, #tag2, #tag3 and #tag4.

    @client.event
    @coc.PlayerEvents.name("#tag2")
    async def foo(...):
        # events will be received for #tag1, #tag2, #tag3 and #tag4.

    @client.event
    @coc.PlayerEvents.donations()
    async def foo(...):
        # events will be received for #tag1, #tag2, #tag3 and #tag4.

    client.add_player_updates("#tag3", "#tag4")

The inverse applies; you only need to register a tag with 1 decorator for it to apply to all events.

The :meth:`EventsClient.add_player_updates` and corresponding clan, war methods now take a list of positional arguments.

For example:

.. code-block:: python3

    # before
    client.add_player_updates(["#tag1", "#tag2"])

    # after
    client.add_player_updates("#tag1", "#tag2", "#tag3")

    tags = ["#tag1", "#tag2", "#tag3"]
    client.add_player_updates(*tags)


Custom Classes
--------------
For more information on custom class support, please see :ref:`custom_classes`.
