.. currentmodule:: coc

API Reference
=============

Logging In
----------
Log in with the exact same syntax as the regular coc.py client.

.. autofunction:: coc.ext.discordlinks.login

Example
~~~~~~~
.. code-block:: python3

    from coc.ext import discordlinks

    client = discordlinks.login("username", "password")

With the returned instance, you can complete any of the operations detailed below.


Discord Link Client
-------------------

The following is a quick and simple overview of all methods available with the links API.

.. autoclass:: coc.ext.discordlinks.DiscordLinkClient
    :members:
