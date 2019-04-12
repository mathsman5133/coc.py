.. current-module:: coc
.. _whats_new:

Changelog
===========
This page keeps a fairly detailed, human readable version
of what has changed, and whats new for each version of the lib.


v0.0.3
-------
BugFixes
~~~~~~~~~
- Fix some problems comparing naive and aware timestamps in :class:`.Timestamp`
- Add a private ``_data`` attribute to all data classes.
This is the json as the API returns it. It makes ``json=True`` parameters in
requests easy to handle.
- Only cache complete clan results - ie. `search_clans` only returned a :class:`BasicClan`,
so in order to add some cache consistency, cached clans now only contain :class:`SearchClan`.

Important
----------
- New Class - :class:`.LeagueWarLogEntry` is similar to :class:`WarLog`, however it has it's own
set of attributes to ensure it is easier to use and know which ones are present and not.
- This new class is utilised in ``Client.get_warlog``, which returns a ``list`` of both
``LeagueWarLogEntry`` and ``WarLog``, depending on the war.

Documentation
--------------
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
