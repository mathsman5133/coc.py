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
**Python 3.7 or higher is required**

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U coc.py

    # Windows
    py -3 -m pip install -U coc.py

    # to install the development version:
    python3 -m pip install -U git+https://github.com/mathsman5133/coc.py


Quick Example
--------------
This is the basic usage of the library.
This example will get a player with a certain tag, and search for 5 clans with a name.

.. code:: py

    import asyncio
    import coc


    async def main():
        async with coc.Client() as coc_client:
            try:
                await coc_client.login("email", "password")
            except coc.invalidcredentials as error:
                exit(error)

            player = await coc_client.get_player("tag")
            print(f"{player.name} has {player.trophies} trophies!")

            clans = await coc_client.search_clans(name="best clan ever", limit=5)
            for clan in clans:
                print(f"{clan.name} ({clan.tag}) has {clan.member_count} members")

            try:
                war = await coc_client.get_current_war("#clantag")
                print(f"{war.clan_tag} is currently in {war.state} state.")
            except coc.privatewarlog:
                print("uh oh, they have a private war log!")

    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pass

Basic Events Example
---------------------
This script will run forever, printing to the terminal
whenever someone joins the clan or a member of the clan donates troops.

.. code:: py

    import asyncio
    import logging

    import coc


    @coc.ClanEvents.member_join()
    async def foo(player, clan):
        print(f"{player.name} ({player.tag}) just joined {clan.name} ({clan.tag})")


    @coc.ClanEvents.member_donations()
    async def bar(old_member, member):
        troops_donated = member.donations - old_member.donations
        print(f"{member.name} just donated {troops_donated} troops!")


    async def main():
        coc_client = coc.EVentsClient()
        try:
            await coc.login("email", "password")
        except coc.InvalidCredentials as error:
            exit(error)

        # Register all the clans you want to monitor
        list_of_clan_tags = ["tag1", "tag2", "tag3"]
        coc_client.add_clan_updates(*list_of_clan_tags)

        # Register the callbacks for each of the events you are monitoring
        coc_client.add_events(
            foo,
            bar
        )


    if __name__ == "__main__":
        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger()

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main())
            loop.run_forever()
        except KeyboardInterrupt:
            pass

For more examples see the examples directory

Contributing
--------------
Contributing is fantastic and much welcomed! If you have an issue, feel free to open an issue and start working on it.

If you wish to run, setup or work on documentation, you will need to install ``sphinx`` and a few related dependencies.
These can be installed with:

.. code:: sh

    pip install -r doc_requirements.txt
    cd docs
    make html

If you wish to run linting, pylint, black and flake8 have been setup and can be run with:

.. code:: sh

    python setup.py lint

Links
------
- `coc.py Documentation <https://cocpy.readthedocs.io/en/latest/?>`_
- `Official Clash of Clans API Page <https://developer.clashofclans.com/>`_
- `Clash of Clans API Discord Server <https://discord.gg/Eaja7gJ>`_

Disclaimer
-----------
This content is not affiliated with, endorsed, sponsored, or specifically
approved by Supercell and Supercell is not responsible for it.
For more information see `Supercell's Fan Content Policy. <https://www.supercell.com/fan-content-policy.>`_



