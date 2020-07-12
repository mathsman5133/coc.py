.. currentmodule:: coc

Models
======
These are the data models used by the API. All calls will return one of these

Due to the unpredictable nature of the API and what it returns, all attributes
have the possibility of being ``None``. However, as much as possible, the library tries
to return an object most appropriate to results returned.

Due to this, there are many objects for what may seem like similar things.

Clans
~~~~~~

.. autoclass:: BaseClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: PlayerClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: RankedClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanWarLeagueClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: Clan()
    :members:
    :private-members:
    :inherited-members:


Players
~~~~~~~~

.. autoclass:: BasePlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanMember()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: RankedPlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanWarLeagueClanMember()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanWarMember()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: Player()
    :members:
    :private-members:
    :inherited-members:


Wars
~~~~~

.. autoclass:: ClanWar()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanWarLogEntry()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanWarLeagueGroup()
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

.. autoclass:: LegendStatistics()
    :members:
    :private-members:
    :inherited-members:


Badge and Icons
~~~~~~~~~~~~~~~~

.. autoclass:: Badge()
    :members:
    :private-members:

.. autoclass:: Icon()
    :members:
    :private-members:


Timestamp
~~~~~~~~~~

.. autoclass:: Timestamp()
    :members:
    :private-members:

Label
~~~~~~~

.. autoclass:: Label()
    :members:
    :private-members:

War League
~~~~~~~~~~

.. autoclass:: WarLeague()
    :members:
    :private-members:
