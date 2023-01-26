.. py:currentmodule:: coc

Models
======
These are the data models used by the API. All calls will return one of these

Due to the unpredictable nature of the API and what it returns, all attributes
have the possibility of being ``None``. However, as much as possible, the library tries
to return an object most appropriate to results returned.

Due to this, there are many objects for what may seem like similar things.

Clans
~~~~~~

Base Clan
^^^^^^^^^
.. autoclass:: BaseClan()
    :members:
    :private-members:
    :inherited-members:

Player Clan
^^^^^^^^^^^
.. autoclass:: PlayerClan()
    :members:
    :private-members:
    :inherited-members:

Ranked Clan
^^^^^^^^^^^
.. autoclass:: RankedClan()
    :members:
    :private-members:
    :inherited-members:

War Clan
^^^^^^^^
.. autoclass:: WarClan()
    :members:
    :private-members:
    :inherited-members:

Clan War League Clan
^^^^^^^^^^^^^^^^^^^^
.. autoclass:: ClanWarLeagueClan()
    :members:
    :private-members:
    :inherited-members:

Raid Clan
^^^^^^^^^
.. autoclass:: RaidClan()
    :members:
    :private-members:
    :inherited-members:

Clan
^^^^
.. autoclass:: Clan()
    :members:
    :private-members:
    :inherited-members:

Players
~~~~~~~~

Base Player
^^^^^^^^^^^
.. autoclass:: BasePlayer()
    :members:
    :private-members:
    :inherited-members:

Clan Member
^^^^^^^^^^^
.. autoclass:: ClanMember()
    :members:
    :private-members:
    :inherited-members:

Ranked Player
^^^^^^^^^^^^^
.. autoclass:: RankedPlayer()
    :members:
    :private-members:
    :inherited-members:

Clan War League Clan Member
^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: ClanWarLeagueClanMember()
    :members:
    :private-members:
    :inherited-members:

Raid Member
^^^^^^^^^^^
.. autoclass:: RaidMember()
    :members:
    :private-members:
    :inherited-members:

Clan War Member
^^^^^^^^^^^^^^^
.. autoclass:: ClanWarMember()
    :members:
    :private-members:
    :inherited-members:

Player
^^^^^^
.. autoclass:: Player()
    :members:
    :private-members:
    :inherited-members:

Wars
~~~~~

Clan War
^^^^^^^^
.. autoclass:: ClanWar()
    :members:
    :private-members:
    :inherited-members:

Clan War Log Entry
^^^^^^^^^^^^^^^^^^
.. autoclass:: ClanWarLogEntry()
    :members:
    :private-members:
    :inherited-members:

Clan War League Group
^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: ClanWarLeagueGroup()
    :members:
    :private-members:
    :inherited-members:

WarAttack
^^^^^^^^^^
.. autoclass:: WarAttack()
    :members:
    :private-members:

War League
^^^^^^^^^^
.. autoclass:: WarLeague()
    :members:
    :private-members:


Raids
~~~~~

Raid Log Entry
^^^^^^^^^^^^^^
.. autoclass:: RaidLogEntry()
    :members:
    :private-members:

Raid District
^^^^^^^^^^^^^
.. autoclass:: RaidDistrict()
    :members:
    :private-members:

Raid Attack
^^^^^^^^^^^
.. autoclass:: RaidAttack()
    :members:
    :private-members:

Game Objects
~~~~~~~~~~~~

Troop
^^^^^
.. autoclass:: Troop()
    :members:
    :private-members:


Hero
^^^^
.. autoclass:: Hero()
    :members:
    :private-members:

Pet
^^^
.. autoclass:: Pet()
    :members:
    :private-members:


Spell
^^^^^
.. autoclass:: Spell()
    :members:
    :private-members:

Player Attributes
~~~~~~~~~~~~~~~~~

Achievement
^^^^^^^^^^^
.. autoclass:: Achievement()
    :members:
    :private-members:


League
^^^^^^
.. autoclass:: League()
    :members:
    :private-members:
    :inherited-members:

Legend Statistics
^^^^^^^^^^^^^^^^^
.. autoclass:: LegendStatistics()
    :members:
    :private-members:
    :inherited-members:

Label
^^^^^
.. autoclass:: Label()
    :members:
    :private-members:

Graphics
~~~~~~~~

Badge
^^^^^
.. autoclass:: Badge()
    :members:
    :private-members:

Icon
^^^^
.. autoclass:: Icon()
    :members:
    :private-members:

Time
~~~~

Timestamp
^^^^^^^^^
.. autoclass:: Timestamp()
    :members:
    :private-members:


TimeDelta
^^^^^^^^^
.. autoclass:: TimeDelta()
    :members:
    :private-members:

Location
~~~~~~~~
.. autoclass:: Location()
    :members:
    :private-members:

Enumerations
~~~~~~~~~~~~

The library provides some enumerations for certain types of strings, as well as orders for troops, spells and
achievements that are used internally.

Corresponds to a member's in-game role in the clan.

.. class:: Role

    Returns a string that is rendered as the role appears in-game, ie ``Co-Leader`` or ``Elder``.
    ``str(member.role)`` will also return this.

    .. py:attribute:: in_game_name


.. class:: WarRound

    Corresponds to the previous war day in Clan-War League (ie the war most recently finished)

    .. py:attribute:: previous_war

    Corresponds to the current war day in Clan-War Leagues.

    .. py:attribute:: current_war

    Corresponds to the current preparation day in Clan-War Leagues.

    .. py:attribute:: current_preparation


.. class:: Resource

    Corresponds to resources found in-game

    .. py:attribute:: gold
    .. py:attribute:: elixir
    .. py:attribute:: dark_elixir
    .. py:attribute:: builder_elixir


All elixir troops, ordered as they appear in-game.

.. data:: coc.ELIXIR_TROOP_ORDER


All dark elixir troops, ordered as they appear in-game.

.. data:: coc.DARK_ELIXIR_TROOP_ORDER


All siege machines, ordered as they appear in-game.

.. data:: coc.SIEGE_MACHINE_ORDER


All super troops, ordered as they appear in-game.

.. data:: coc.SUPER_TROOP_ORDER


All home troops, ordered as they appear in-game. This is a combination of elixir, dark elixir and siege machine troops.
This does not contain super troops.

.. data:: coc.HOME_TROOP_ORDER


All builder troops, ordered as they appear in-game.

.. data:: coc.BUILDER_TROOPS_ORDER


All elixir spells, ordered as they appear in-game.

.. data:: coc.ELIXIR_SPELL_ORDER


All dark elixir spells, ordered as they appear in-game.

.. data:: coc.DARK_ELIXIR_SPELL_ORDER


All spells, ordered as they appear in-game.

.. data:: coc.SPELL_ORDER


All heroes, ordered as they appear in-game.

.. data:: coc.HERO_ORDER


All achievements, ordered as they appear in-game.

.. data:: coc.ACHIEVEMENT_ORDER


All of the above contain a list of strings, corresponding to the name given in-game and in the API.
