.. currentmodule:: coc
.. _migrating_to_v2_0:

Migrating to coc.py v2.0
========================

Most of the outward facing library is the same, with a few changes detailed below. One significant change is the
introduction of game data into Troop, Spell, Hero and Pet objects. You can read more about that here: :ref:`game_data`.

Logging in with keys
---------------------
A popular request was made to be able to use the client without the automatic key management. You can now initiate coc.py
with a list of keys (or tokens), using the :meth:`coc.login_with_keys` method.

Parsing and creating army links
-------------------------------
The June update brought about the ability to share and create army links. v2 brings the ability to do this within the client,
using the methods :meth:`Client.parse_army_link` and :meth:`Client.create_army_link`. These work best when paired with
the game data mentioned above, as you will receive (semi)complete Troop and Spell objects with stats for all troops and spells.

Thanks to Anub, Sco and others for helping to implement this.


Additional methods / attributes for models
------------------------------------------
A popular feature request was to be able to know "is this troop the max for the player's TH level". Before, this would
require you to keep a static list of troop levels and do a lookup. This has been integrated into coc.py, and many models
have this attribute now:

- :attr:`Troop.is_max_for_townhall`

- :attr:`Spell.is_max_for_townhall`

- :attr:`Hero.is_max_for_townhall`

- :attr:`Pet.is_max_for_townhall`

Similarly, you can use `Troop.get_max_level_for_townhall` to do the opposite - get the max troop level for a specific townhall.
More on that in the :ref:`game_data` section, however.


- :attr:`WarClan.average_attack_duration` is now a valid property, thanks to doluk for implementing this.

- :attr:`Player.war_opted_in` was added, to reflect the September update in the API.

- :attr:`ClanWar.attacks_per_member` was added, which details the number of attacks each member has in the war, also in the September update.

- :attr:`Player.clan_previous_rank` was fixed, it didn't point to the correct API field before.


Miscellaneous
-------------
- ``ujson`` has been added to the requirements and will be used where possible,
as a faster method of deserialising json payloads from the API.

- Internal handling of keys has been written to make it more stable.

- Flame Flinger, Super Bowler and Super Dragon were all added to coc.py.
