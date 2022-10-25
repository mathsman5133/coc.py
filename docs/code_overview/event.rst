.. currentmodule:: coc

Events
======
The following section provides an overview of the Events Client, providing
an easy introduction with a wealth of examples.

What are they?
--------------
The Clash of Clans API, currently, provides no reasonable way to know when
for example, someone upgrades a troop, or attacks in war, without making repeated
calls and comparing objects over time.

The coc.py events client does exactly that: making requests to the API every X seconds,
comparing the results internally and dispatching relevant "events".

Functions are called, known as "callbacks" when these events occur, and are named as such.
You must register the functions you wish to be called, in addition to telling the library which
clan and player tags you wish to "track".

Getting Started
---------------

Before receiving events for your clan/players, you must first register the clans and players you wish to "watch",
as well as registering callback functions that will be called when events are found.

Events Client
~~~~~~~~~~~~~

When using events, you must use the dedicated :class:`EventsClient` class. This class extends the :class:`Client` class,
and allows all of the same operations, as well as more specific to events.

You can tell the library you wish to use the :class:`EventsClient` by passing it to the :meth:`coc.login`.
The returned client instance will be of :class:`EventsClient`.

Example:

.. code-block:: python3

    import coc

    client = coc.login("email", "password", client=coc.EventsClient)


Decorators
~~~~~~~~~~

Decorators are a simple, easy way to interact with coc.py events. They are grouped into 4 categories:

    - ``coc.PlayerEvents``: Events for players.
    - ``coc.ClanEvents``: Events for clans.
    - ``coc.WarEvents``: Events for wars.
    - ``coc.ClientEvents``: Events for miscellaneous client events.

A simple example of how decorators are intended to work is below:

.. code-block:: python3

    import coc

    @coc.PlayerEvents.donations(tags=["#282L8GLJ"])
    async def my_function(old_player, new_player):
        new_donations = new_player.donations - old_player.donations
        print(f"{new_player} just donated {new_donations} troops.")

Each event group corresponds to a specific model, and client method.

+----------------------+------------------+--------------------------------+
| Decorator            | Model            | Method                         |
+----------------------+------------------+--------------------------------+
| ``coc.PlayerEvents`` | :class:`Player`  | :meth:`Client.get_player`      |
+----------------------+------------------+--------------------------------+
| ``coc.ClanEvents``   | :class:`Clan`    | :meth:`Client.get_clan`        |
+----------------------+------------------+--------------------------------+
| ``coc.WarEvents``    | :class:`ClanWar` | :meth:`Client.get_current_war` |
+----------------------+------------------+--------------------------------+

Events are dynamically created. This means that you can have an event for *any* attribute of the decorator's corresponding
model. For example, if you use ``@coc.PlayerEvents``, you can have an event for a player name change, level change, donations change.

The format is simple. You use the name of the attribute as the attribute you access from the decorator.

For Example,

To get an event for a player's donations, ie. when the :attr:`Player.donations` changes, you would do: ::

    @coc.PlayerEvents.donations()

To get an event for when a clan's level, ie when the :attr:`Clan.level` changes, you would do: ::

    @coc.ClanEvents.level()

To get an event for when a war's state, ie :attr:`ClanWar.state` changes, you would do: ::

    @coc.WarEvents.state()

The pattern is simple, and holds true for all attributes.

Some more examples:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.trophies()  # an event that is run for every player, when their `.trophies` attribute changes.
    async def foo(old_player, new_player):
        assert old_player.trophies != new_player.trophies

    @client.event
    @coc.WarEvents.state()  # an event that is run when a war `.state` has changed
    async def foo(old_war, new_war):
        assert old_war.state != new_war.state

    @client.event
    @coc.ClanEvents.public_war_log()  # an event that is run when a clan's `.public_war_log` attribute has changed.
    async def foo(old_clan, new_clan):
        assert old_clan.public_war_log != new_clan.public_war_log

    @client.event
    @coc.ClanEvents.member_donations()  # an event that is run for every clan member when their `.donations` have changed.
    async def foo(old_member, new_member):
        assert old_member.donations != new_member.donations

    @client.event
    @coc.PlayerEvents.clan_level()  # an event that is called when a player's clan's level has changed.
    async def foo(old_player, new_player):
        assert old_player.clan.level != new_player.clan.level

You can also stack decorators to get multiple events reported to one callback:

.. code-block:: python3

    @client.event
    @coc.ClanEvents.public_war_log()
    @coc.ClanEvents.description()
    @coc.ClanEvents.level()
    async def foo(old_clan, new_clan):
        if old_clan.level != new_clan.level:
            ...
        elif old_clan.description != new_clan.description:
            ...


Callbacks
~~~~~~~~~

Callbacks are the functions that are called when your event "happens".

For Example:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.name()
    async def my_function(old_player, new_player):  # <-- this is the line I'm talking about
        ...

A few points when dealing with callbacks:


1. They must be an async function, in other words they must start with ``async def``.

2. They must have 2, **and only 2** parameters: the old object, and the new object.

3. There is **no naming convention**, that is, you can call it whatever you want.


Elaborating on point 2, the "old" object is the one *before* the event/change, and the
"new" object is the one *after* the event/change. It's often helpful to name them like so.

If your event is ``@coc.PlayerEvents.name()``, you can expect the names of the old and new players to be *different*,
for example:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.name()
    async def foo(old_player, new_player):
        assert old_player.name != new_player.name  # True


For ``@coc.ClanEvents.member_x`` events, the first parameter should be the old member, and the second parameter the new member.
You can access the member's clan object via ``member.clan``.

For Example:

.. code-block:: python3

    @client.event
    @coc.ClanEvents.member_donations()
    async def foo(old_member, new_member):
        assert old_member.donations != new_member.donations
        print("The clan is {}".format(new_member.clan.name))


Retry / Refresh Intervals
~~~~~~~~~~~~~~~~~~~~~~~~~
Unless you wish to only check for new events once every hour or 6 hours, or any time greater than the refresh time
for objects in the API, **it is suggested to omit the ``retry_interval`` parameter.** The library will automatically
determine when the next fresh object is available, and instead of sleeping for a predefined 60seconds between every loop,
it will instead sleep until a fresh object is available from the API. This means some events could see an up to 50% reduction in
latency between when the event happens in game and when coc.py reports it.

For example:

.. code-block:: python3

    @client.event
    @coc.ClanEvents.level()
    async def foo(...): ...  # check as often as API updates the clan for an event

    @client.event
    @coc.ClanEvents.level(retry_interval=1800)  # check every 30 minutes for a new event.
    async def foo(...): ...


Adding Clan and Player Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tags can be added via the :meth:`EventsClient.add_player_updates`, :meth:`EventsClient.add_clan_updates` or
:meth:`EventsClient.add_war_updates`. Alternatively, they can be passed to the decorator function.


For example:

.. code-block:: python3

    @client.event
    @coc.PlayerEvents.name(tags=['#tag', '#tag2', '#tag3'])
    async def foo(old_player, new_player): ...

    # alternatively:

    @client.event
    @coc.PlayerEvents.name()
    async def foo(old_player, new_player): ...

    client.add_player_updates('#tag', '#tag2', '#tag3')


A few points to note:

- Tags will be automatically corrected via the :meth:`coc.correct_tag` function.

- **Every tag** that is added to the client will be sent to **every callback for that event group**.

This makes for a much simpler internal design.


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


Removing Clan and Player Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v1.0 provides added functionality of removing player and clan tags from the list of tags being updated:
:meth:`EventsClient.remove_player_updates`, :meth:`EventsClient.remove_clan_updates` and :meth:`EventsClient.remove_war_updates`.

The usage is intuitive, and identical to adding the tags:

.. code-block:: python3

    client.remove_player_updates("#tag1", "#tag2", "#tag3")

    tags = ["#tag1", "#tag2", "#tag3"]
    client.remove_player_updates(*tags)


Custom Classes
--------------
For more information on custom class support, please see :ref:`custom_classes`.

Client (coc.py) Events
----------------------
coc.py has a few events that are unique to the library, and which provide some useful information. They are:

+------------------------------------------------+-------------------------+--------------------------------------------------+
|      Event                                     |        Parameter(s)     |    Description                                   |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.maintenance_start()``      | None                    | Fired when API (and in-game) maintenance starts. |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.maintenance_completion()`` |  start_datetime         | Fired when API (and in-game) maintenance ends.   |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.new_season_start()``       | None                    | Fired when a season starts.                      |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.event_error()``            | exception               | Fired when an event hits an unhandled exception  |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.clan_loop_start()``        | iteration_number        | Fired when the clan loop starts an iteration     |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.clan_loop_finish()``       | iteration_number        | Fired when the clan loop finishes an iteration   |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.player_loop_start()``      | iteration_number        | Fired when the player loop starts an iteration   |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.player_loop_finish()``     | iteration_number        | Fired when the player loop finishes an iteration |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.war_loop_start()``         | iteration_number        | Fired when the war loop starts an iteration      |
+------------------------------------------------+-------------------------+--------------------------------------------------+
| ``@coc.ClientEvents.war_loop_finish()``        | iteration_number        | Fired when the war loop finishes an iteration    |
+------------------------------------------------+-------------------------+--------------------------------------------------+

Parameters refer to the parameters of the callback function, for example:

.. code-block:: python3

    @coc.ClientEvents.maintenance_start()
    async def my_callback():
        print('Maintenance has started!')

    @coc.ClientEvents.maintenance_completion()
    async def second_callback(time_started):
        print('Maintenance has finished, started at' + str(time_started))


For maintenance_completion, the parameter is of type :class:`datetime.datetime`.
Iteration_number is an integer indicating how many times the client has run update loops so far.
Exception is an exception class that can be passed into an exception log, for example

.. code-block:: python3

    import logging

    log = logging.getLogger()

    @coc.ClientEvents.event_error()
    async def callback(exception):
        log.error("events had an error!", exc_info=exception)

