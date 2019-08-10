coc.py
======

Easy to use asynchronous Clash of Clans API wrapper in Python.

Key Features
-------------
- Asynchronous code
- Entire coverage of the official Clash of Clans API
- Email/password login removes the stress of managing tokens
- Optimised for speed and performance

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

    # to install the development version:
    python3 -m pip install -U git+https://github.com/mathsman5133/coc.py --upgrade


Quick Example
--------------
This is the basic usage of the library.
This example will get a player with a certain tag, and search for 5 clans with a name.

.. code:: py

    import coc
    import asyncio

    client = coc.login('email', 'password')
    loop = asyncio.get_event_loop

    player = loop.run_until_complete(client.get_player('tag'))
    print(player.name)

    async def get_five_clans(name):
        players = await client.search_clans(name=name, limit=5)
        for n in players:
            print(n, n.tag)

    if __name__ == '__main__':
        loop.run_until_complete(get_five_clans('name'))
        loop.run_until_complete(client.close())

Basic Events Example
---------------------
This script will run forever, printing to the terminal whenever someone joins the clan.

.. code:: py

    import coc
    import asyncio

    client = coc.login('email', 'password', client=coc.EventsClient)
    loop = asyncio.get_event_loop()

    @client.event
    async def on_clan_member_join(player, clan):
        print('{0.name} ({0.tag}) just joined {1.name} ({1.tag})!')

    loop.run_until_complete(client.add_clan_update('tag'))
    client.start_events('clan')

    client.run_forever()


For more examples see the examples directory

Links
------
- `coc.py Documentation <https://cocpy.readthedocs.io/en/latest/?>`_
- `Official Clash of Clans API Page <https://developer.clashofclans.com/>`_




