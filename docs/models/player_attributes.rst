.. py:currentmodule:: coc

Player Attributes
=================

Achievement
~~~~~~~~~~~
.. autoclass:: Achievement()
    :members:
    :private-members:


League
~~~~~~
.. autoclass:: League()
    :members:
    :private-members:
    :inherited-members:

Legend Statistics
~~~~~~~~~~~~~~~~~
.. autoclass:: LegendStatistics()
    :members:
    :private-members:
    :inherited-members:

Role
~~~~
Returns a string that is rendered as the role appears in-game, ie ``Co-Leader`` or ``Elder``.
``str(member.role)`` will also return this.

.. note::

    The in-game role ``Elder`` is named ``admin`` in the API responses.

.. class:: Role

    .. py:attribute:: in_game_name


Label
~~~~~
.. autoclass:: Label()
    :members:
    :private-members:

