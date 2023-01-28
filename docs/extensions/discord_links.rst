.. py:currentmodule:: coc

.. _links_extension:

Discord Links Extension
=======================

Overview
--------

Discord has become the de facto standard for clan communication. One of the challenges in working with Discord bots and Clash of Clans is linking a Clash of Clans village to a Discord account.  Thanks to a new API created by ReverendMike, this problem is now solved.  coc.py leverages this API to allow bot developers easy access to linked accounts.


The coc.py extension for Discord links allows you to do the following:

- Link a Discord account to one or more player tags
- Update existing links
- Remove links
- Get player tag(s) based on a Discord ID
- Get a Discord ID based on a player tag
- Get a list of Discord IDs based on an iterable of player tags

In order to use the Discord Links API, you will need a username and password.
Please contact ReverendMike#6969 on Discord if you are interested.

API Reference
-------------

Logging In
~~~~~~~~~~
Log in with the exact same syntax as the regular coc.py client.

.. autofunction:: coc.ext.discordlinks.login

Example
^^^^^^^
.. code-block:: python3

    from coc.ext import discordlinks

    client = discordlinks.login("username", "password")

With the returned instance, you can complete any of the operations detailed below.


Discord Link Client
~~~~~~~~~~~~~~~~~~~

The following is a quick and simple overview of all methods available with the links API.

.. autoclass:: coc.ext.discordlinks.DiscordLinkClient
    :members:


Examples
--------

This is an example of using the discord links extension.

.. literalinclude:: ../../examples/discord_links.py
   :language: py
   :linenos:
