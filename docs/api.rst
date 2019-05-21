.. currentmodule:: coc
API Reference
==============

The following section outlines the API Reference of coc.py


Client
-------

.. autoclass:: Client
    :members:

EventsClient
--------------

.. autoclass:: coc.ext.events.EventsClient
    :members:
    :inherited-members:

Event Reference
----------------

Events are called when using the :class:`EventsClient` client, clans/players/wars
have been registered, and have been started.

Events need to be registered in order to be called by the client. You can register events by
using either :meth:`EventsClient.event`, or :meth:`EventsClient.add_events`.

All events the client will dispatch are listed below.

.. py:function:: on_event_error(event_name, \*args, \*\*kwargs)

    This event is called when another event raises an exception and fails.
    By default, it will print the traceback to stderr and the exception will
    be ignored.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to ``sys.exc_info()``.

    :param event_name: The event which caused the error
    :param args: The positional args for the event which raised the error
    :param kwargs: The keyword-args for the event which raised the error

.. py:function:: on_clan_update(old_clan, new_clan)

    This event is called when a clan has been updated.
    This could be a member join/leave, settings or other update.
    This is called before, and regardless whether, any other events are called,
    ie. :func:`on_clan_member_join`

    :param old_clan: The clan object before the change
    :type old_clan: :class:`SearchClan`
    :param new_clan: The clan object after the change
    :type new_clan: :class:`SearchClan`

.. py:function:: on_clan_member_join(member, clan)

    This event is called when a member joins a clan.

    :param member: The member who joined.
    :type member: :class:`BasicPlayer`
    :param clan: The clan the member joined.
    :type clan: :class:`SearchClan`

.. py:function:: on_clan_member_leave(member, clan)

    This event is called when a member leaves a clan.

    :param member: The member who left.
    :type member: :class:`BasicPlayer`
    :param clan: The clan the member left.
    :type clan: :class:`SearchClan`

.. py:function:: on_clan_settings_update(old_clan, new_clan)

    This event is called when the clan settings have been updated.
    Basically that means this is called whenever a clan change has been made,
    however that change isn't just a member join/leave.
    Multiple changes may be present if the ``retry_interval`` is large enough.

    This will be called in addition to :func:`on_clan_update`

    :param old_clan: The clan object before the change
    :type old_clan: :class:`SearchClan`
    :param new_clan: The clan object after the change
    :type new_clan: :class:`SearchClan`

.. py:function:: on_war_update(old_war, new_war)

    This event is called when a war update occurs, regardless of it's nature.
    This could be an attack, state change or other.

    :param old_war: The war object before the change
    :type old_war: :class:`War`
    :param new_war: The war object after the change
    :type new_war: :class:`War`

.. py:function:: on_war_attack(attack, war)

    This event is called when a new war attack has been made.
    This could be an offensive or defensive attack.
    This will be called once per new attack, even if multiple
    new attacks are found.

    :param attack: The new attack.
    :type attack: :class:`WarAttack`
    :param war: The war this attack belongs to.
    :type war: :class:`War`

.. py:function:: on_war_state_change(current_state, war)

    This event is called when a change of war state occurs.
    This will not necessarily be called when the client checks
    for a change, as a task will be created at the last update to
    wait for new state changes.

    :param current_state: The current war state it has changed to.
    :type current_state: :class:`str`
    :param war: The war that has changed state
    :type war: :class:`War`

.. py:function:: on_player_update(old_player, new_player)

    This event is called when a player changes.
    This event will be called regardless of the update that follows.
    This could be a name or level change, or a troop/spell upgrade.

    :param old_war: The player object before the change
    :type old_war: :class:`SearchPlayer`
    :param new_war: The player object after the change
    :type new_war: :class:`SearchPlayer`

.. py:function:: on_player_name_change(old_name, new_name, player)

    This event is called when a player's name has changed.

    :param old_name: The player's old name
    :type old_name: :class:`str`
    :param new_name: The player's new name
    :type new_name: :class:`str`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_townhall_upgrade(old_townhall, new_townhall, player)

    This event is called when a player's townhall has been upgraded.

    :param old_townhall: The player's old townhall level
    :type old_townhall: :class:`int`
    :param new_townhall: The player's new townhall level
    :type new_townhall: :class:`int`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_builderhall_upgrade(old_builderhall, new_builderhall, player)

    This event is called when a player's builder hall has been upgraded.

    :param old_builderhall: The player's old builder hall level
    :type old_builderhall: :class:`int`
    :param new_builderhall: The player's new builder hall level
    :type new_builderhall: :class:`int`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_achievement_update(old_achievement, new_achievement, player)

    This event is called when a player's achievement has changed.

    :param old_achievement: The player's old achievement.
    :type old_achievement: :class:`Achievement`
    :param new_achievement: The player's new achievement.
    :type new_achievement: :class:`Achievement`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_troop_upgrade(old_troop, new_troop, player)

    This event is called when a player's troop has been upgraded.

    :param old_troop: The player's old troop.
    :type old_troop: :class:`Troop`
    :param new_troop: The player's new troop.
    :type new_troop: :class:`Troop`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_spell_upgrade(old_spell, new_spell, player)

    This event is called when a player's spell has been upgraded.

    :param old_spell: The player's old spell.
    :type old_spell: :class:`Spell`
    :param new_spell: The player's new spell.
    :type new_spell: :class:`Spell`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_troop_upgrade(old_hero, new_hero, player)

    This event is called when a player's hero has been upgraded.

    :param old_hero: The player's old hero.
    :type old_hero: :class:`Hero`
    :param new_hero: The player's new hero.
    :type new_hero: :class:`Hero`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. py:function:: on_player_other_update(old_player, new_player)

    This event is called when there is another change not called in an above event.
    .. note:: Please do not rely upon `old_player._data` for events fired above;
              they may be incorrect.

    :param old_player: The player object prior to change.
    :type old_player: :class:`SearchPlayer`
    :param new_player: The player object after the change.
    :type new_player: :class:`SearchPlayer`


Data Models
-------------------------
These are the data models used by the API. All calls will return one of these

Due to the unpredictable nature of the API and what Supercell returns, all attributes
have the possibility of being `None`. However, as much as possible, the library tries
to return an object most appropriate to results returned.

Due to this, there are many objects for what may seem like similar things.

Note: If a :class:`SearchPlayer` inherits :class:`BasicPlayer`, it will inherit all
attributes of both :class:`Player` and :class:`BasicPlayer`, however it will **not necessarily**
inherit :class:`WarMember`

Clans
~~~~~~

.. autoclass:: Clan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: BasicClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: SearchClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarClan()
    :members:
    :private-members:
    :inherited-members:


Players
~~~~~~~~

.. autoclass:: Player()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: BasicPlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarMember()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: SearchPlayer()
    :members:
    :private-members:
    :inherited-members:


Wars
~~~~~

.. autoclass:: BaseWar()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarLog()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: CurrentWar()
    :members:
    :private-members:
    :inherited-members:


WarAttack
~~~~~~~~~~

.. autoclass:: WarAttack()
    :members:
    :private-members:


Achievement
~~~~~~~~~~~~

.. autoclass:: Achievement()
    :members:
    :private-members:


Troop
~~~~~~
.. autoclass:: Troop()
    :members:
    :private-members:


Hero
~~~~~

.. autoclass:: Hero()
    :members:
    :private-members:


Spell
~~~~~~

.. autoclass:: Spell()
    :members:
    :private-members:


Location
~~~~~~~~~

.. autoclass:: Location()
    :members:
    :private-members:


League Objects
~~~~~~~~~~~~~~~

.. autoclass:: League()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueRankedPlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LegendStatistics()
    :members:
    :private-members:
    :inherited-members:


Badge
~~~~~~

.. autoclass:: Badge()
    :members:
    :private-members:


Timestamp
~~~~~~~~~~

.. autoclass:: Timestamp()
    :members:
    :private-members:


League War Objects
~~~~~~~~~~~~~~~~~~~

.. autoclass:: LeaguePlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueGroup()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueWar()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueWarLogEntry()
    :members:
    :private-members:


Exceptions
--------------------
The following exceptions are thrown by the library.

.. autoexception:: ClashOfClansException

.. autoexception:: HTTPException

.. autoexception:: InvalidArgument

.. autoexception:: InvalidCredentials

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: Maitenance