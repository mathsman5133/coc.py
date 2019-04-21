.. current-module:: coc
.. _whats_new:

Changelog
===========
This page keeps a fairly detailed, human readable version
of what has changed, and whats new for each version of the lib.

v0.1.0
---------
BugFixes
~~~~~~~~~~
- Fixed bug with loops breaking when reloading the client in a discord cog.
- A more specific error, `aiohttp.ContentTypeError` is raised when parsing non-json responses.

Important
~~~~~~~~~~~
- Big thanks to Jab for some of these.

- Big one! Client now only accepts an email/password pair rather than tokens.
  This pair is what you use to login to https://developer.clashofclans.com/#/login
  and will allow the client to automatically use, create, reset and find tokens,
  making it a much more streamlined process.


- As such, the following parameters to client have been added:

    - ``key_count``: int: the number of tokens to rotate between when making API requests.
      This defaults to 1, and can be between 1 and 10

    - ``key_names``: str: The name to use when creating tokens on the developer page.
      This defaults to `Created with coc.py Client`

- Email and Password are now mandatory parameters and must be passed

- `update_tokens` parameter has been removed. The client will automatically reset bad tokens.

- In order to keep consistency with the official API docs, `token` has been renamed to `key`.
  This affects the following method/parameters:

    - ``on_token_reset(new_token)`` --> ``on_key_reset(new_key)``
    - ``HTTPClient.login()`` --> ``HTTPClient.get_keys()``

  and otherwise consistent use of `key` during internals, docs, code and examples.

- `pytz` and `python-dateutil` have both been removed as dependencies due to the ability to
  parse timestamps manually. This has been added to utils as a function: ``from_timestamp(ts)``,
  returning a utc-datetime object.

- Dataclasses have received a makeover! Many new attributes are present, these are listed below.
  Most importantly, any property beginning with an underscore (_) use and return iterator objects.
  These are **not** lists, and relevant python documentation is here:
  https://docs.python.org/3/glossary.html#term-iterator.

  These are up to 12x faster than lists, and
  as such for those who are concerned about speed, performance and memory should use these, while
  for the majority, calling the regular property should be fine (usually returning a list rather than iter).

    -   :attr:`SearchClan._members`
    -   :attr:`WarClan._members`
    -   :attr:`WarClan._attacks`
    -   :attr:`WarClan._defenses`
    -   :attr:`WarMember._attacks`
    -   :attr:`WarMember._defenses`
    -   :attr:`SearchPlayer._achievements`
    -   :attr:`CurrentWar._attacks`
    -   :attr:`CurrentWar._members`
    -   :attr:`LeagueClan._members`
    -   :attr:`LeagueGroup._clans`

- The following **new** attributes were added:

    -   :attr:`SearchClan.member_dict`
    -   :attr:`WarClan.member_dict`
    -   :attr:`WarClan.attacks`
    -   :attr:`WarClan.defenses`
    -   :attr:`WarMember.attacks`
    -   :attr:`WarMember.defenses`
    -   :attr:`SearchPlayer.achievements_dict`
    -   :attr:`SearchPlayer.troops_dict`
    -   :attr:`SearchPlayer.heroes_dict`
    -   :attr:`SearchPlayer.spells_dict`
    -   :attr:`Timestamp.time`


- The folowwing **new** methods were added:

    -   `SearchClan.get_member(tag)`
    -   `CurrentWar.get_member(tag)`

- New utility functions:

    - `utils.get(iterable, **attrs)`
        - Searches the iterable until a value with the given attribute is found.
          Unlike ``filter()``, this will return when the first value is found.
    - `utils.find(function, iterable)`
        - Searches through the iterable until a value which satisfies the function is found.

    - `from_timestamp(ts)`
        - Parses an ISO8601 timestamp as returned by the COC API into a datetime object


Documentation:
~~~~~~~~~~~~~~~~
- Many docstrings were reformatted or worded, with punctuation and other typo's fixed
- All new properties, attributes and methods have been documented.
- Update some examples, including a `clan_info` function in discord bots (Thanks, Tuba).



v0.0.6
--------
BugFixes
~~~~~~~~~
- Fix bug with always raising RuntimeError

v0.0.5
-------
BugFixes
~~~~~~~~~
- Fixed how the lib detects an invalid IP error, as SC changed how the error message works
- Fixed bug with semi-complete URL when using the API dev site
- ``email`` and ``password`` in :class:`Client` are now ``None`` by default. This was throwing
    and error before.
- str() for :class:`Achievement`, :class:`Hero`, :class:`Troop`, :class:`Spell` now all return
    respective names

Important
-----------
- Added a new exception: :exc:`Forbidden`. This is thrown when a 403 is returned, but the error is not
    one of invalid token, instead when you aren't allowed to get the resource eg. private war log.
- A :exc:`RuntimeError` will be raised if you try to pass ``update_stats`` as ``True`` but don't set
    the ``email`` or ``password``
- Added the :func:`Client.on_token_reset` which is called whenever the lib updates your token.
    By default this does nothing, however you can override it by either subclassing or
    using the decorator ``@Client.event()`` above your new ``async def on_token_reset``.
    This function can be a regular or coroutine.

Documentation
--------------
- Add examples. I will expand on these as I see fit. Feel free to let me know if you want more.
- Fix broken codeblock examples
- Update incorrect function name in the example in README.rst (``player_name`` --> ``get_some_player``

v0.0.4
-------
BugFixes
~~~~~~~~~
- Fix some problems comparing naive and aware timestamps in :class:`.Timestamp`
- Add a private ``_data`` attribute to all data classes.
  This is the json as the API returns it. It makes ``json=True`` parameters in
  requests easy to handle.
- Only cache complete clan results - ie. ``Client.search_clans`` only returned a :class:`BasicClan`,
  so in order to add some cache consistency, cached clans now only contain :class:`SearchClan`.

Important
~~~~~~~~~~
- New Class - :class:`.LeagueWarLogEntry` is similar to :class:`WarLog`, however it has it's own
  set of attributes to ensure it is easier to use and know which ones are present and not.
- This new class is utilised in ``Client.get_warlog``, which returns a ``list`` of both
  ``LeagueWarLogEntry`` and ``WarLog``, depending on the war.

Documentation
~~~~~~~~~~~~~~
- Utilise `sphinx_rtd_theme` for the RTD page
- Add this changelog
- Continue to fix typos and little errors as they are found.


v0.0.2
-------
BugFixes
~~~~~~~~~
- Fix some attributes from inherited classes not being present
- Fix some :exc:`AttributeError` from being thrown due to incomplete data from API
- When a clan is not in war, :class:`.WarClan` will not be present.
  Some errors were being thrown due to incomplete data being given from API
- Allow for text-only responses from API (ie. not json)


Important Changes
~~~~~~~~~~~~~~~~~~
- Actually specify that the package coc needs to be installed when installing with pip
- Fix incorrect spelling of both :class:`.Achievement` and :exc:`InvalidArgument`
- Update the examples in the README to work (search_players is not a thing)


v0.0.1
-------
Initial Commit!
