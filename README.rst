coc.py
======

.. image:: https://discordapp.com/api/guilds/566451504332931073/embed.png
    :target: https://discord.gg/Eaja7gJ
    :alt: Discord Server Invite
.. image:: https://img.shields.io/pypi/v/coc.py.svg
   :target: https://pypi.python.org/pypi/coc.py
   :alt: PyPI version info
.. image:: https://img.shields.io/pypi/pyversions/discord.py.svg
   :target: https://pypi.python.org/pypi/coc.py
   :alt: PyPI supported Python versions
.. image:: https://travis-ci.org/mathsman5133/coc.py.svg?branch=master
    :target: https://travis-ci.org/mathsman5133/coc.py
    :alt: Travis CI info


Easy to use asynchronous Clash of Clans API wrapper in Python.

Key Features
-------------
- Asynchronous code
- Entire coverage of the official Clash of Clans API
- Email/password login removes the stress of managing tokens
- Optimised for speed and performance
- Completely customisable cache

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
    loop = asyncio.get_event_loop()

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

    @client.event
    async def on_clan_member_join(player, clan):
        print('{0.name} ({0.tag}) just joined {1.name} ({1.tag})!')

    client.add_clan_update('tag')

    client.run_forever()


For more examples see the examples directory

Links
------
- `coc.py Documentation <https://cocpy.readthedocs.io/en/latest/?>`_
- `Official Clash of Clans API Page <https://developer.clashofclans.com/>`_
- `Clash of Clans API Discord Server <https://discord.gg/Eaja7gJ/>`_

Disclaimer
-----------
- This content is not affiliated with, endorsed, sponsored, or specifically
  approved by Supercell and Supercell is not responsible for it.
  For more information see `Supercell's Fan Content Policy: <https://www.supercell.com/fan-content-policy.>`_



