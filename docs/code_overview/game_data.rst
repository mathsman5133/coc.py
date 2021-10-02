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
    load game metadata for any events dispatched. Instead see :ref:`manually_loading_metadata` for how to load it
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


.. _initiated_v_uninitiated:
Initiated vs Uninitiated Objects
--------------------------------

Due to internal design, Troop (and other, but they mimic Troop so we'll use Troop as an example) classes are stored
internally as uninitiated classes, with all the properties from game data stored as class attributes. When you call
:meth:`Client.get_player`, the client will retrieve these uninitiated classes, and create instances of them, which
is what you use when accessing :attr:`Player.troops`.

When you use :meth:`Client.get_troop`, you receive an uninitiated class, which has slightly different ways of dealing
with attributes.


.. _initiated_objects:
Initiated Objects
~~~~~~~~~~~~~~~~~

These are what you receive when you use :meth:`Player.get_troop` with a player retrieved with :meth:`Client.get_player`,
or a troop retrieved with :meth:`Client.get_troop` when passing in ``level`` or ``townhall`` parameters.

The important thing to note is that all attributes found under :class:`Troop` (and :class:`Spell`, :class:`Hero`, :class:`Pet`)
all return their type (int, bool, etc.)


.. code-block:: python3

    player = await client.get_player("#2pp")
    barb = player.get_troop("Barbarian")

    print(barb.dps)  # prints 56
    print(barb.hitpoints)  # prints 129


If you wanted to get the statistics of the barbarian 1 level up from the current level, you could do

.. code-block:: python3

    player = await client.get_player("#2pp")
    barb = player.get_troop("Barbarian")

    barb.level += 1  # set the level to be 1 higher

    print(barb.dps)  # prints 64
    print(barb.hitpoints)  # prints 132


.. note::

    Be very careful when adjusting the level that you store a copy of what the original troop level it, because
    coc.py won't. Changing the level will effect the duration of that player object, and may introduce unintended bugs.


If you wanted to get a dictionary of all the troop level/hitpoints, you could do the following:

.. code-block:: python3

    player = await client.get_player("#2pp")
    barb = player.get_troop("Barbarian")

    for level, hitpoints in enumerate(barb.__class__.hitpoints, start=1):
        print("Barbarian has {} hitpoints at Lv{}.".format(hitpoints, level))


.. note::

    ``__class__`` is a descriptor that provides access to the uninitiated root class of the instance object.
    If that doesn't make sense, it basically means that ``barb.__class__`` gives you an :ref:`uninitiated_objects`.


Alternatively, you could use :meth:`Client.get_troop` and use the unititiated object returned from that. See below.


.. _uninitiated_objects:
Uninitiated Objects
~~~~~~~~~~~~~~~~~~~

These are perhaps the less common variant of :class:`Troop` and other classes you'll come across. Internally, all
data objects are stored as these, and instances are created on-demand when you request a player.

You can get these with :meth:`Client.get_troop`, but they function a little differently to :ref:`initiated_objects`.

.. code-block:: python3

    barb = client.get_troop("Barbarian")
    print(barb.id)  # prints 4000000

    print(barb.hitpoints)  # prints [56, 64, 67, 71, ...]


**Anything that varies with level will return a list of statistics when using uninitiated objects.**

This includes (and note, where applicable, these attributes apply to :class:`Spell`, :class:`Hero` and :class:`Pet` too:


* :attr:`Troop.range`
* :attr:`Troop.dps`
* :attr:`Troop.hitpoints`
* :attr:`Troop.lab_level`
* :attr:`Troop.speed`
* :attr:`Troop.upgrade_cost`
* :attr:`Troop.upgrade_time`
* :attr:`Troop.training_cost`
* :attr:`Troop.cooldown` (Super Troops Only)
* :attr:`Troop.duration` (Super Troops Only)
* :attr:`Hero.ability_time`
* :attr:`Hero.ability_troop_count`
* :attr:`Hero.required_th_level`
* :attr:`Hero.regeneration_time`


A few more examples:

.. code-block:: python3

    barb = client.get_troop("Barbarian")

    for level, hitpoints in enumerate(barb.hitpoints, start=1):
        print("Barbarian has {} hitpoints at Lv{}.".format(hitpoints, level))


    barb_king = client.get_hero("Barbarian King")
    for level, regeneration_time in enumerate(barb_king.regeneration_time, start=1):
        print("BK has {}min regeneration time at level {}".format(level, regeneration_time.minutes))


One interesting thing to note it that ``barb.hitpoints`` will return a list of ``[34, 43, 54, 65, 76, ...]`` which
may look like a normal list, but if you index it, i.e. ``hitpoints[4]``, you'll get stats for level 4, rather than
the 5th item in the list, or level 5 if it were to be 0-indexed.
If you use ``enumerate``, you still need to specify that you're starting from 1, however: ``enumerate(barb.hitpoints, start=1)``.

Put simply, this means ``barb.hitpoints[1]`` will return stats for barb level 1, and ``barb.hitpoints[0]`` will raise an error.


.. code-block:: python3

    barb = client.get_troop("Barbarian")

    lv_1_stats = barb.hitpoints[1]  # returns 96
    lv_14_stats = barb.hitpoints[14]  # returns 234

    # or, assigning hitpoints as a variable
    hitpoints = barb.hitpoints  # returns [96, 123, 145, 167, ..., 234]
    hitpoints_lv_1 = hitpoints[1]  # hitpoints is still 1-indexed
    hitpoints_lv_14 = hitpoints[14]

    print(hitpoints)  # will print <UnitStatList [96, 123, 145, 167, ..., 234]>, to show it's not a normal list.


Here's a simple example, if that was all very confusing:

.. code-block::

    barb_king = client.get_hero("Barbarian King")

    print(f"Barb King has an upgrade cost of {barb_king.upgrade_cost[43]} at level 43!")

