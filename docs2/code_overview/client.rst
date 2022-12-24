.. py:currentmodule:: coc

Clients and Logging In
======================

Logging In
----------
A coc.py client instance can be created through the utility function, :meth:`coc.login`:

.. autofunction:: login

.. autofunction:: login_with_keys


Example
~~~~~~~
.. code-block:: python3

    import coc

    client = coc.login("email", "password", key_names="keys for my windows pc", key_count=5)

With the returned instance, you can complete any of the operations detailed below.


Special Parameters
~~~~~~~~~~~~~~~~~~

This details special parameters passed to the :class:`Client` which may have more than 1 option (True/False).
Currently this only includes :class:`LoadGameData`, but may be expanded in the future.

LoadGameData
^^^^^^^^^^^^

.. autoclass:: LoadGameData