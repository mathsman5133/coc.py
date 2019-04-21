.. currentmodule:: coc
API Reference
==============

The following section outlines the API Reference of coc.py


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

.. autoexception:: InvalidToken

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: Maitenance