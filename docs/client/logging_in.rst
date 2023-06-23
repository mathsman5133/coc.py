.. py:currentmodule:: coc

Logging In
==========
A coc.py client instance can be created directly by :class:`Client`. The instance can then be logged in with the methods

.. autofunction:: coc.Client.login

.. autofunction:: coc.Client.login_with_tokens


Example
~~~~~~~
.. code-block:: python3

    import coc
    import asyncio

    async def main():
        async with coc.Client(key_names="keys for my windows pc", key_count=5) as coc_client:
            await coc_client.login("email","password")
            # do stuff

    if __name__ == "__main__":
        asyncio.run(main())

.. code-block:: python3

    import coc
    import asyncio

    async def main():
        coc_client= coc.Client(key_names="keys for my windows pc", key_count=5)
        await coc_client.login("email","password")
        # do stuff
        await coc_client.close()

    if __name__ == "__main__":
        asyncio.run(main())

With the logged in instance, you can complete any of the operations detailed below. The instance can be user either
with a context manager or without as shown in the example.


Special Parameters
~~~~~~~~~~~~~~~~~~

This details special parameters passed to the :class:`Client` which may have more than 1 option (True/False).
Currently this only includes :class:`LoadGameData`, but may be expanded in the future.

LoadGameData
^^^^^^^^^^^^

.. autoclass:: LoadGameData
