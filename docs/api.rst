.. currentmodule:: coc
API Reference
==============

The following section outlines the API of coc.py


Client
-------

.. autoclass:: Client
    :members:

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

.. autoclass:: Clan
.. autoclass:: BasicClan
.. autoclass:: SearchClan
.. autoclass:: WarClan

Players
~~~~~~~~
.. autoclass:: Player
.. autoclass:: BasicPlayer
.. autoclass:: WarMember
.. autoclass:: SearchPlayer

Wars
~~~~~
.. autoclass:: BaseWar
.. autoclass:: WarLog
.. autoclass:: CurrentWar

WarAttack
~~~~~~~~~~
.. autoclass:: WarAttack

Acheivement
~~~~~~~~~~~~
.. autoclass:: Acheivement

Troop
~~~~~~
.. autoclass:: Troop

Hero
~~~~~
.. autoclass:: Hero

Spell
~~~~~~
.. autoclass:: Spell

Location
~~~~~~~~~
.. autoclass:: Location

League Objects
~~~~~~~~~~~~~~~
.. autoclass:: League
.. autoclass:: LeagueRankedPlayer
.. autoclass:: LegendStatistics

Badge
~~~~~~
.. autoclass:: Badge

Timestamp
~~~~~~~~~~
.. autoclass:: Timestamp

League War Objects
~~~~~~~~~~~~~~~~~~~
.. autoclass:: LeaguePlayer
.. autoclass:: LeagueClan
.. autoclass:: LeagueGroup
.. autoclass:: LeagueWar




Exceptions
--------------------
The following exceptions are thrown by the library.

.. autoexception:: ClashOfClansException

.. autoexception:: HTTPException

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: InvalidArguement

.. autoexception:: InvalidToken

.. autoexception:: Maitenance