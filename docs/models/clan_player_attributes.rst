.. py:currentmodule:: coc

Clan and Player Attributes
==========================

Achievement
~~~~~~~~~~~
.. autoclass:: Achievement()
    :members:
    :private-members:
    :show-inheritance:

Capital District
~~~~~~~~~~~~~~~~
.. autoclass:: CapitalDistrict()
    :members:
    :private-members:
    :show-inheritance:

Label
~~~~~
.. autoclass:: Label()
    :members:
    :private-members:
    :show-inheritance:

Base League
~~~~~~~~~~~
.. autoclass:: BaseLeague()
    :members:
    :private-members:
    :show-inheritance:

League
~~~~~~
.. autoclass:: League()
    :members:
    :private-members:
    :inherited-members:
    :show-inheritance:

Legend Statistics
~~~~~~~~~~~~~~~~~
.. autoclass:: LegendStatistics()
    :members:
    :private-members:
    :inherited-members:
    :show-inheritance:

PlayerHouseElement
~~~~~~~~~~~~~~~~~~
.. autoclass:: PlayerHouseElement()
    :members:
    :private-members:
    :show-inheritance:

PlayerHouseElementType
~~~~~~~~~~~~~~~~~~~~~~
.. class:: PlayerHouseElementType()

    An Enumeration with all the types of player house elements

    .. py:attribute:: ground

    .. py:attribute:: roof

    .. py:attribute:: foot

    .. py:attribute:: deco

    .. py:attribute:: walls

Role
~~~~
Returns a string that is rendered as the role appears in-game, ie ``Co-Leader`` or ``Elder``.
``str(member.role)`` will also return this.

.. note::

    The in-game role ``Elder`` is named ``admin`` in the API responses.

.. class:: Role

    .. py:attribute:: in_game_name
