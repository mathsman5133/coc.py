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





