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

    import asyncio
    import coc

    async def main():
        async with coc.Client() as coc_client:
            await coc_client.login("email", "password")

        # do stuff

    asyncio.run(main())

With the returned instance, you can complete any of the operations detailed below.


Special Parameters
~~~~~~~~~~~~~~~~~~

This details special parameters passed to the :class:`Client` which may have more than 1 option (True/False).
Currently this only includes :class:`LoadGameData`, but may be expanded in the future.


LoadGameData
^^^^^^^^^^^^

.. autoclass:: LoadGameData


Basic Client Interface
----------------------

The following details all operations on the basic client instance.

.. autoclass:: Client
    :members:

Events Client
-------------

The following details all valid operations for the :class:`EventsClient`. This extends the :class:`Client` class, and
all methods from :class:`Client` are valid with the :class:`EventsClient`, too.

.. autoclass:: EventsClient
    :members:
