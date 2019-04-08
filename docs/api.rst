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
	:inherited-members:
	
.. autoclass:: BasicClan()
	:members:
	:inherited-members:
	
.. autoclass:: SearchClan()
	:members:
	:inherited-members:
	
.. autoclass:: WarClan()
	:members:
	:inherited-members:
	

Players
~~~~~~~~

.. autoclass:: Player()
	:members:
	:inherited-members:
	
.. autoclass:: BasicPlayer()
	:members:
	:inherited-members:
	
.. autoclass:: WarMember()
	:members:
	:inherited-members:
	
.. autoclass:: SearchPlayer()
	:members:
	:inherited-members:
	

Wars
~~~~~

.. autoclass:: BaseWar()
	:members:
	:inherited-members:
	
.. autoclass:: WarLog()
	:members:
	:inherited-members:
	
.. autoclass:: CurrentWar()
	:members:
	:inherited-members:
	

WarAttack
~~~~~~~~~~

.. autoclass:: WarAttack()
	:members:
	

Acheivement
~~~~~~~~~~~~

.. autoclass:: Acheivement()
	:members:
	

Troop
~~~~~~
.. autoclass:: Troop()
	:members:
	

Hero
~~~~~

.. autoclass:: Hero()
	:members:
	

Spell
~~~~~~

.. autoclass:: Spell()
	:members:
	
	
Location
~~~~~~~~~

.. autoclass:: Location()
	:members:
	

League Objects
~~~~~~~~~~~~~~~

.. autoclass:: League()
	:members:
	:inherited-members:
	
.. autoclass:: LeagueRankedPlayer()
	:members:
	:inherited-members:
	
.. autoclass:: LegendStatistics()
	:members:
	:inherited-members:
	

Badge
~~~~~~

.. autoclass:: Badge()
	:members:
	

Timestamp
~~~~~~~~~~

.. autoclass:: Timestamp()
	:members:
	

League War Objects
~~~~~~~~~~~~~~~~~~~

.. autoclass:: LeaguePlayer()
	:members:
	:inherited-members:
	
.. autoclass:: LeagueClan()
	:members:
	:inherited-members:
	
.. autoclass:: LeagueGroup()
	:members:
	:inherited-members:
	
.. autoclass:: LeagueWar()
	:members:
	:inherited-members:
	



Exceptions
--------------------
The following exceptions are thrown by the library.

.. autoexception:: ClashOfClansException

.. autoexception:: HTTPException

.. autoexception:: InvalidArgument

.. autoexception:: InvalidToken

.. autoexception:: NotFound

.. autoexception:: Maitenance