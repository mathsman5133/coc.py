.. currentmodule:: coc
.. _game_data:

Game Data
=========

The following provides a detailed how-to for use of static game data that is loaded into coc.py.

All game data has been retrieved from https://coc.guide and is freely available.

Why?
----
While the API provides all data about a player's current troops and spells, often people want to know "does this player
have a maxed Barbarian for their TH level?" or "how much does it cost to upgrade all a player's spells to max?".

This then results in an often clumsy and hard-to-maintain dictionary, csv, json or other form of static data being made
and utilised. The integration of these game files into coc.py means there's less need to duplicate this process, and
upgrading/updating code should be as easy as upgrading versions of coc.py whenever an update lands.

Other benefits include integration into existing :class:`Troop` and other data models, meaning the process for getting
a troop's upgrade cost for a player is the exact same as getting the troop's name, or level. But more on that later.

Additionally, speed and memory consumption has been prioritised and optimised where possible.


.. _initialising_game_data:

Initialising the Client
-----------------------

There are a few options you can choose from as to how coc.py will handle when to inject game data and when not to.
Although all efforts have been made to minimise overheads, some may prefer to only use game data when they choose to.


1. Always

    If you want coc.py to always inject game metadata, regardless of when or where you call :meth:`Client.get_player`,
    including in events, use this option.

    Game metadata will be loaded on startup using this option, which means you can use :meth:`Client.parse_army_link` etc.
    without issue.

.. code-block:: python3

        client = coc.login('email', 'password', load_game_data=coc.LoadGameData(always=True))


2. Default

    In this option, coc.py will always inject game metadata when using :meth:`Client.get_player`, however will not
    load game metadata for any events dispatched. Instead see :ref:`loading_game_data` for how to load it
    when using events.

    Game metadata will be loaded on startup using this option, which means you can use :meth:`Client.parse_army_link` etc.
    without issue.

.. code-block:: python3

        client = coc.login('email', 'password', load_game_data=coc.LoadGameData(default=True))


3. Startup Only

    With this option, coc.py will load game metadata on startup, but will **never** automatically load it into Player
    objects. This means you must manually call :meth:`Player.load_game_data` to load game data for a player.

    Using this option means game metadata is loaded on startup, which means :meth:`Client.parse_army_link` etc. will
    will work fine.

.. code-block:: python3

        client = coc.login('email', 'password', load_game_data=coc.LoadGameData(startup_only=True))


4. Never

    With this option, game metadata is **not** loaded on startup, and will **never** be injected into player objects.
    This means that you **cannot use** :meth:`Client.parse_army_link` methods, nor the :meth:`Player.load_game_data` to
    manually load the data.

.. code-block:: python3

        client = coc.login('email', 'password', load_game_data=coc.LoadGameData(never=True))



.. _loading_game_data:

Loading Game Data Manually
--------------------------

The preferred way of telling coc.py that you want to load game data for player requests is either through setting
``load_game_metadata`` to ``Always`` or ``Default``, or by passing ``load_game_data=True`` into your :meth:`Client.get_player` call.

.. code-block:: python3

    player = await client.get_player("#tag", load_game_data=True)


Alternatively, if you initialised the client with ``load_game_data`` set to ``Always`` or ``Default`` and don't wish to
load game data, you can set it to False:

.. code-block:: python3

    player = await client.get_player("#tag", load_game_data=False)


By default, however, it is set to whatever you initialised at Client startup.


If you're using the :class:`EventsClient` and don't have ``load_game_metadata`` set to ``Always``, your player events
won't have metadata loaded. This is easy to fix, with the :meth:`Player.load_game_data` call:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.troop_change()
    async def player_troop_upgraded(cached_player, player, troop):
        player.load_game_data()

        print("Player {} upgraded {}, which costs {} to upgrade again.", player.name, troop.name, troop.upgrade_cost)


.. warning::

    This is not designed for regular use. **Please don't use it where there's an alternative**. It manually injects
    troop data into the existing objects which takes longer than creating them at the start of the call.
    The example given is the only use-case I can think of at present.


.. _accessing_game_data:

Accessing Game Data
-------------------

When you retrieve a player with game data loaded, all :class:`Troop`, :class:`Spell`, :class:`Hero`, :class:`Pet`, 
and :class:`Equipment` objects will have their game data attributes populated based on their current level.

All attributes return their appropriate type (int, bool, :class:`TimeDelta`, etc.)


.. code-block:: python3

    player = await client.get_player("#2pp")
    barb = player.get_troop("Barbarian")

    print(barb.dps)  # prints 56
    print(barb.hitpoints)  # prints 129


You can dynamically change the level to see stats at different levels:

.. code-block:: python3

    player = await client.get_player("#2pp")
    barb = player.get_troop("Barbarian")

    barb.level += 1  # set the level to be 1 higher

    print(barb.dps)  # prints stats for the new level
    print(barb.hitpoints)  # prints stats for the new level


To iterate over all levels of a troop:

.. code-block:: python3

    player = await client.get_player("#2pp")
    barb = player.get_troop("Barbarian")
    
    for level in range(1, barb.max_level + 1):
        barb.level = level
        print(f"Level {level}: {barb.dps} DPS, {barb.hitpoints} HP, costs {barb.upgrade_cost} to upgrade")


Available Attributes
~~~~~~~~~~~~~~~~~~~~

Game data provides many attributes for troops, spells, heroes, pets, and equipment. Common level-varying attributes include:

* ``dps`` - Damage per second
* ``hitpoints`` - Health points
* ``upgrade_cost`` - Cost to upgrade to the next level
* ``upgrade_time`` - Time required to upgrade
* ``required_townhall`` - Townhall level required
* ``required_lab_level`` - Laboratory level required (troops/spells)

See the API documentation for :class:`Troop`, :class:`Spell`, :class:`Hero`, :class:`Pet`, and :class:`Equipment` 
for complete attribute lists

