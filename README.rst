coc.py
======

Easy to use asynchronous Clash of Clans API wrapper in Python.

Key Features
-------------
- Asynchronous code
- Entire coverage of the official Clash of Clans API
- Auto updating tokens for use with dynamic IPs

Getting Started
================

Installing
-----------
**Python 3.5 or higher is required**

.. code:: sh

    # Linux/OS X
    python3 -m pip install -U coc.py

    # Windows
    py -3 -m pip install -U coc.py

Quick Example
--------------
.. code:: py

    import coc
    import asyncio

    loop = asyncio.get_event_loop()
    client = coc.Client('token', loop)

    async def get_some_player(tag):
        player = await client.get_player(tag)

        print(player.name)
        # alternatively,
        print(str(player))

    async def get_five_clans(name):
        players = await client.search_clans(name=name, limit=5)
        for n in players:
            print(n, n.tag)

    if __name__ == '__main__':
        loop.run_until_complete(get_some_player('tag'))
        loop.run_until_complete(get_five_clans('name'))

For more examples see the examples directory

Links
------
- `coc.py Documentation <https://cocpy.readthedocs.io/en/latest/?>`_
- `Official Clash of Clans API Page <https://developer.clashofclans.com/>`_




