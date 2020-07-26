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
- Optimised for speed, memory and performance

Getting Started
================

Installing
-----------
**Python 3.5 or higher is required**

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U git+https://github.com/mathsman5133/coc.py@rewrite

    # Windows
    py -3 -m pip install -U git+https://github.com/mathsman5133/coc.py@rewrite


Quick Example
--------------
This is the basic usage of the library.
This example will get a player with a certain tag, and search for 5 clans with a name.

.. code:: py

    import coc
    import asyncio

    client = coc.login('email', 'password')

    player = loop.run_until_complete(client.get_player('tag'))
    print(player.name)

    async def main():
        player = await client.get_player("tag")
        print("{0.name} has {0.trophies} trophies!".format(player))

        clans = await client.search_clans(name="Best Clan Ever", limit=5)
        for clan in clans:
            print("{0.name} ({0.tag}) has {0.member_count} members".format(clan))

        try:
            war = await client.get_current_war("clan tag")
            print(f"{0.clan_tag} is currently in {0.state} state.".format(war))
        except coc.PrivateWarLog:
            print("Uh oh, they have a private war log!")

    if __name__ == '__main__':
        asyncio.get_event_loop().run_until_complete(main())

Basic Events Example
---------------------
This script will run forever, printing to the terminal
whenever someone joins the clan or a member of the clan donates troops.

.. code:: py

    import coc

    client = coc.login('email', 'password', client=coc.EventsClient)

    @client.event
    @coc.ClanEvents.member_join("clan tag")
    async def foo(player, clan):
        print("{0.name} ({0.tag}) just joined {1.name} ({1.tag})!".format(player, clan))

    @client.event
    @coc.ClanEvents.member_donations("clan tag")
    async def bar(old_member, member):
        troops_donated = old_member.donations - member.donations
        print("{0} just donated {1} troops!".format(member.name, troops_donated))

    client.run_forever()


For more examples see the examples directory

Contributing
--------------
Contributing is fantastic and much welcomed! If you have an issue, feel free to open an issue and start working on it.
A few things to bear in mind:

Installing the dev requirements:

.. code:: sh

    pip install -r dev-requirements.txt

This will install all the dev requirements, such as pylint, sphinx and pre-commit. These are handy!

**Setting up a git pre-commit hook**

Code quality is important - the repo has automatic linting and CI implemented.

In order to keep the git history
clean, a pre-commit hook will automatically lint your code according to the repo's standard before you push.

You can install this pre-commit hook with:

.. code:: sh

    pre-commit install

In your local terminal. The ``pre-commit`` module should have already been installed
if you installed the dev-requirements

You can run all linting that will be run in CI with:

.. code:: sh

    python setup.py lint
    // or
    pre-commit run --all-files

Links
------
- `coc.py Documentation <https://cocpy.readthedocs.io/en/latest/?>`_
- `Official Clash of Clans API Page <https://developer.clashofclans.com/>`_
- `Clash of Clans API Discord Server <https://discord.gg/Eaja7gJ>`_

Disclaimer
-----------
- This content is not affiliated with, endorsed, sponsored, or specifically
  approved by Supercell and Supercell is not responsible for it.
  For more information see `Supercell's Fan Content Policy: <https://www.supercell.com/fan-content-policy.>`_



