.. currentmodule:: coc
API Reference
==============

The following section outlines the API Reference of coc.py

Logging in and client creation
-------------------------------
.. autofunction:: login

Clients
--------

Basic Client
~~~~~~~~~~~~~~
.. autoclass:: Client
    :members:

Events Client
~~~~~~~~~~~~~~
.. autoclass:: EventsClient
    :members:
    :inherited-members:

Custom Cache
-------------

Cache Class
~~~~~~~~~~~~~
.. autoclass:: Cache
    :members:
    :inherited-members:

Max Size Cache
~~~~~~~~~~~~~~~
.. autoclass:: MaxSizeCache

Time To Live Cache
~~~~~~~~~~~~~~~~~~~
.. autoclass:: TimeToLiveCache

Default Cache
~~~~~~~~~~~~~~~
.. autoclass:: DefaultCache

Event Reference
----------------

Events are called when using the :class:`EventsClient` client, clans/players/wars
have been registered, and have been started.

Events need to be registered in order to be called by the client. You can register events by
using either :meth:`EventsClient.event`, or :meth:`EventsClient.add_events`.

All events the client will dispatch are listed below.

.. _on_event_error:

Event Error
~~~~~~~~~~~~~~~
.. py:function:: on_event_error(event_name, \*args, \*\*kwargs)

    This event is called when another event raises an exception and fails.
    By default, it will print the traceback to stderr and the exception will
    be ignored.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to ``sys.exc_info()``.

    :param event_name: The event which caused the error
    :param args: The positional args for the event which raised the error
    :param kwargs: The keyword-args for the event which raised the error

.. _clan_event_group:

Clan Events
~~~~~~~~~~~~~

These events are all related to clan changes and changes to players within the clan. Clans can be added by
registering clan tags and relevant events.

.. _on_clan_update:

Clan Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. py:function:: on_clan_update(old_clan, new_clan)

    This event is called when a clan has been updated.
    This could be a member join/leave, settings or other update.
    This is called before, and regardless whether, any other events are called,
    ie. :func:`on_clan_member_join`

    :param old_clan: The clan object before the change
    :type old_clan: :class:`SearchClan`
    :param new_clan: The clan object after the change
    :type new_clan: :class:`SearchClan`

.. _on_clan_level_change:

Clan Level Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. py:function:: on_clan_level_change(old_level, new_level, clan)

    This event is called when the clan level changes.

    :param old_level: The old clan level
    :type old_level: int
    :param new_level: The new clan level
    :type new_level: int
    :param clan: The clan who's level changed
    :type clan: :class:`SearchClan`

.. _on_clan_description_change:

Clan Description Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_description_change(old_description, new_description, clan)

    This event is called when the clan description changes.

    :param old_description: The old clan's description
    :type old_description: str
    :param new_description: The new clan description
    :type new_description: str
    :param clan: The clan who's description changed
    :type clan: :class:`SearchClan`

.. _on_clan_public_war_log_change:

Clan Public WarLog Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_public_war_log_change(old_toggle, new_toggle, clan)

    This event is called when the clan's toggle changes.

    :param old_toggle: The old clan toggle
    :type old_toggle: bool
    :param new_toggle: The new clan toggle
    :type new_toggle: bool
    :param clan: The clan who's toggle changed
    :type clan: :class:`SearchClan`

.. _on_clan_type_change:

Clan Type Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_type_change(old_type, new_type, clan)

    This event is called when the clan's type changes.

    :param old_type: The old clan type
    :type old_type: str
    :param new_type: The new clan type
    :type new_type: str
    :param clan: The clan who's type changed
    :type clan: :class:`SearchClan`

.. _on_clan_badge_change:

Clan Badge Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_badge_change(old_badge, new_badge, clan)

    This event is called when the clan's badge changes.

    :param old_badge: The old clan badge
    :type old_badge: :class:`Badge`
    :param new_badge: The new clan badge
    :type new_badge: :class:`Badge`
    :param clan: The clan who's badge changed
    :type clan: :class:`SearchClan`

.. _on_clan_required_trophies_change:

Clan Required Trophies Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_required_trophies_change(old_requirement, new_requirement, clan)

    This event is called when the clan's trophy requirement changes.

    :param old_requirement: The old clan requirement
    :type old_requirement: int
    :param new_requirement: The new clan requirement
    :type new_requirement: int
    :param clan: The clan who's requirement changed
    :type clan: :class:`SearchClan`

.. _on_clan_war_frequency_change:

Clan War Frequency Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_war_frequency_change(old_frequency, new_frequency, clan)

    This event is called when the clan's war frequency changes.

    :param old_frequency: The old clan war frequency
    :type old_frequency: str
    :param new_frequency: The new clan war frequency
    :type new_frequency: str
    :param clan: The clan who's war frequency changed
    :type clan: :class:`SearchClan`

.. _on_clan_war_win_streak_change:

Clan War Win Streak Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_war_win_streak_change(old_streak, new_streak, clan)

    This event is called when the clan's war win streak changes.

    :param old_streak: The old clan streak
    :type old_streak: int
    :param new_streak: The new clan streak
    :type new_streak: int
    :param clan: The clan who's streak changed
    :type clan: :class:`SearchClan`

.. _on_clan_war_win_change:

Clan War Wins Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_war_win_change(old_wins, new_wins, clan)

    This event is called when the clan's war wins change.

    :param old_wins: The old clan wins
    :type old_wins: int
    :param new_wins: The new clan wins
    :type new_wins: int
    :param clan: The clan who's wins changed
    :type clan: :class:`SearchClan`

.. _on_clan_war_tie_change:

Clan War Ties Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_war_tie_change(old_ties, new_ties, clan)

    This event is called when the clan's war ties change.

    :param old_ties: The old clan ties
    :type old_ties: int
    :param new_ties: The new clan ties
    :type new_ties: int
    :param clan: The clan who's ties changed
    :type clan: :class:`SearchClan`

.. _on_clan_war_loss_change:

Clan War Losses Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_war_loss_change(old_losses, new_losses, clan)

    This event is called when the clan's war losses change.

    :param old_losses: The old clan losses
    :type old_losses: int
    :param new_losses: The new clan losses
    :type new_losses: int
    :param clan: The clan who's losses changed
    :type clan: :class:`SearchClan`

.. _on_clan_member_join:

Clan Member Join
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_join(member, clan)

    This event is called when a member joins a clan.

    :param member: The member who joined.
    :type member: :class:`BasicPlayer`
    :param clan: The clan the member joined.
    :type clan: :class:`SearchClan`

.. _on_clan_member_leave:

Clan Member Leave
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_leave(member, clan)

    This event is called when a member leaves a clan.

    :param member: The member who left.
    :type member: :class:`BasicPlayer`
    :param clan: The clan the member left.
    :type clan: :class:`SearchClan`

.. _on_clan_member_name_change:

Clan Member Name Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_name_change(old_name, new_name, player)

    This event is called when a clan member's name changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_name: The player's old name
    :type old_name: str
    :param new_name: The player's new name
    :type new_name: str
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_donation:

Clan Member Donations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_donation(old_donations, new_donations, player)

    This event is called when a clan member's donations changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_donations: The player's old donations
    :type old_donations: int
    :param new_donations: The player's new donations
    :type new_donations: int
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_received:

Clan Member Received
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_received(old_received, new_received, player)

    This event is called when a clan member's donations received changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_received: The player's old received
    :type old_received: int
    :param new_received: The player's new received
    :type new_received: int
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_trophy_change

Clan Member Trophy Count Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_trophy_change(old_trophies, new_trophies, player)

    This event is called when a clan member's trophy count has changed.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_received: The player's old trophy count
    :type old_received: int
    :param new_received: The player's new trophy count
    :type new_received: int
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_versus_trophy_change

Clan Member Versus Trophy Count Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_versus_trophy_change(old_trophies, new_trophies, player)

    This event is called when a clan member's versus trophy count has changed.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_received: The player's old versus trophy count
    :type old_received: int
    :param new_received: The player's new versus trophy count
    :type new_received: int
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`


.. _on_clan_member_role_change:

Clan Member Role Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_role_change(old_role, new_role, player)

    This event is called when a clan member's role changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_role: The player's old role
    :type old_role: str
    :param new_role: The player's new role
    :type new_role: str
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_rank_change:

Clan Member Rank Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_rank_change(old_rank, new_rank, player)

    This event is called when a clan member's rank changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_rank: The player's old rank
    :type old_rank: int
    :param new_rank: The player's new rank
    :type new_rank: int
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_level_change:

Clan Member Level Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_level_change(old_level, new_level, player)

    This event is called when a clan member's level changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_level: The player's old level
    :type old_level: str
    :param new_level: The player's new level
    :type new_level: str
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`

.. _on_clan_member_league_change:

Clan Member League Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_clan_member_league_change(old_league, new_league, player, clan)

    This event is called when a clan member's league changes.
    The player's clan can be accessed through :attr:`BasicPlayer.clan` and is of type :class:`SearchClan`

    :param old_level: The player's old league
    :type old_level: :class:`League`
    :param new_level: The player's new league
    :type new_level: :class:`League`
    :param player: The player object which changed
    :type player: :class:`BasicPlayer`
    :param clan: The player's clan
    :type clan: :class:`SearchClan`

.. _war_event_group:

War Events
~~~~~~~~~~~~

These events are all related to war changes, such as war attacks and state changes. Clans can be added by
registering clan tags and relevant events.

.. _on_war_update:

War Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_war_update(old_war, new_war)

    This event is called when a war update occurs, regardless of it's nature.
    This could be an attack, state change or other.

    :param old_war: The war object before the change
    :type old_war: :class:`War`
    :param new_war: The war object after the change
    :type new_war: :class:`War`

.. _on_war_attack:

New War Attack
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_war_attack(attack, war)

    This event is called when a new war attack has been made.
    This could be an offensive or defensive attack.
    This will be called once per new attack, even if multiple
    new attacks are found.

    :param attack: The new attack.
    :type attack: :class:`WarAttack`
    :param war: The war this attack belongs to.
    :type war: :class:`War`

.. _on_war_state_change:

War State Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_war_state_change(current_state, war)

    This event is called when a change of war state occurs.
    This will not necessarily be called when the client checks
    for a change, as a task will be created at the last update to
    wait for new state changes.

    :param current_state: The current war state it has changed to.
    :type current_state: :class:`str`
    :param war: The war that has changed state
    :type war: :class:`War`

.. _player_event_group:

Player Events
~~~~~~~~~~~~~~~

These events are all related to player changes and changes to clans within the player. Clans can be added by
registering clan tags and relevant events.

.. _on_player_update:

Player Update
^^^^^^^^^^^^^^^^

.. py:function:: on_player_update(old_player, new_player)

    This event is called when a player changes.
    This event will be called regardless of the update that follows.
    This could be a name or level change, or a troop/spell upgrade.

    :param old_war: The player object before the change
    :type old_war: :class:`SearchPlayer`
    :param new_war: The player object after the change
    :type new_war: :class:`SearchPlayer`

.. _on_player_name_change:

Player Name Change
^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_name_change(old_name, new_name, player)

    This event is called when a player's name has changed.

    :param old_name: The player's old name
    :type old_name: :class:`str`
    :param new_name: The player's new name
    :type new_name: :class:`str`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. _on_player_townhall_upgrade:

Player Town Hall Change
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_townhall_upgrade(old_townhall, new_townhall, player)

    This event is called when a player's townhall has been upgraded.

    :param old_townhall: The player's old townhall level
    :type old_townhall: :class:`int`
    :param new_townhall: The player's new townhall level
    :type new_townhall: :class:`int`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. _on_player_builderhall_upgrade:

Player Builder Hall Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_builderhall_upgrade(old_builderhall, new_builderhall, player)

    This event is called when a player's builder hall has been upgraded.

    :param old_builderhall: The player's old builder hall level
    :type old_builderhall: :class:`int`
    :param new_builderhall: The player's new builder hall level
    :type new_builderhall: :class:`int`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. _on_player_best_trophies_change:

Player Best Trophies Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_best_trophies_change(old_best, new_best, player)

    This event is called when a player's best trophy count changes.

    :param old_best: The player's old best trophy count
    :type old_best: int
    :param new_best: The player's new best trophy count
    :type new_best: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_best_versus_trophies_change:

Player Best Versus Trophies Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_best_versus_trophies_change(old_best, new_best, player)

    This event is called when a player's best versus trophy count changes.

    :param old_best: The player's old best versus trophy count
    :type old_best: int
    :param new_best: The player's new best versus trophy count
    :type new_best: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_war_stars_change:

Player War Stars Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_war_stars_change(old_stars, new_stars, player)

    This event is called when a player's war stars changes.

    :param old_stars: The player's old war stars
    :type old_stars: int
    :param new_stars: The player's new war stars
    :type new_stars: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_attack_wins_change:

Player Attack Wins Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_attack_wins_change(old_attacks, new_attacks, player)

    This event is called when a player's attacks count changes.

    :param old_attacks: The player's old attacks count
    :type old_attacks: int
    :param new_attacks: The player's new attacks count
    :type new_attacks: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_defense_wins_change:

Player Defense Wins Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_defense_wins_change(old_defenses, new_defenses, player)

    This event is called when a player's defenses trophy count changes.

    :param old_defenses: The player's old defenses count
    :type old_defenses: int
    :param new_defenses: The player's new defenses count
    :type new_defenses: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_versus_attacks_change:

Player Versus Attacks Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_versus_attacks_change(old_attacks, new_attacks, player)

    This event is called when a player's versus attacks count changes.

    :param old_attacks: The player's old versus attacks count
    :type old_attacks: int
    :param new_attacks: The player's new versus attacks count
    :type new_attacks: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_trophies_change:

Player Trophies Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_trophies_change(old_trophies, new_trophies, player)

    This event is called when a player's trophy count changes.

    :param old_trophies: The player's old trophy count
    :type old_trophies: int
    :param new_trophies: The player's new trophy count
    :type new_trophies: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_league_change:

Player League Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_league_change(old_league, new_league, player)

    This event is called when a player's league changes.

    :param old_league: The player's old league
    :type old_league: :class:`League`
    :param new_league: The player's new league
    :type new_league: :class:`League`
    :param player: The player in question
    :type player: :class:`SearchPlayer`

.. _on_player_role_change:

Player Role Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_role_change(old_role, new_role, player)

    This event is called when a player's clan role.

    :param old_role: The player's old role
    :type old_role: str
    :param new_role: The player's new role
    :type new_role: str
    :param player: The player in question
    :type player: :class:`SearchPlayer`


.. _on_player_donations_change:

Player Donations Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_donations_change(old_donations, new_donations, player)

    This event is called when a player's donation count changes.

    :param old_donations: The player's old donation count
    :type old_donations: int
    :param new_donations: The player's new donation count
    :type new_donations: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`


.. _on_player_received_change:

Player Received Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_received_change(old_received, new_received, player)

    This event is called when a player's donations received count changes.

    :param old_received: The player's old received count
    :type old_received: int
    :param new_received: The player's new received count
    :type new_received: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`


.. _on_player_clan_rank_change:

Player's Clan Rank Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_clan_rank_change(old_rank, new_rank, player)

    This event is called when a player's clan rank changes.

    :param old_rank: The player's old rank
    :type old_rank: int
    :param new_rank: The player's new rank
    :type new_rank: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`


.. _on_player_previous_clan_rank_change:

Player's Previous Clan Rank Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_previous_clan_rank_change(old_rank, new_rank, player)

    This event is called when a player's previous clan rank changes.
    This would typically be at the end of the season.

    :param old_rank: The player's old previous rank
    :type old_rank: int
    :param new_rank: The player's new previous rank
    :type new_rank: int
    :param player: The player in question
    :type player: :class:`SearchPlayer`


.. _on_player_achievement_change:

Player Achievement Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_achievement_change(old_achievement, new_achievement, player)

    This event is called when a player's achievement has changed.

    :param old_achievement: The player's old achievement.
    :type old_achievement: :class:`Achievement`
    :param new_achievement: The player's new achievement.
    :type new_achievement: :class:`Achievement`
    :param player: The new player object
    :type player: :class:`SearchPlayer`


.. _on_player_troop_upgrade:

Player Troop Upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_troop_upgrade(old_troop, new_troop, player)

    This event is called when a player's troop has been upgraded.

    :param old_troop: The player's old troop.
    :type old_troop: :class:`Troop`
    :param new_troop: The player's new troop.
    :type new_troop: :class:`Troop`
    :param player: The new player object
    :type player: :class:`SearchPlayer`


.. _on_player_spell_upgrade:

Player Spell Upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_spell_upgrade(old_spell, new_spell, player)

    This event is called when a player's spell has been upgraded.

    :param old_spell: The player's old spell.
    :type old_spell: :class:`Spell`
    :param new_spell: The player's new spell.
    :type new_spell: :class:`Spell`
    :param player: The new player object
    :type player: :class:`SearchPlayer`


.. _on_player_hero_upgrade:

Player Hero Upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_hero_upgrade(old_hero, new_hero, player)

    This event is called when a player's hero has been upgraded.

    :param old_hero: The player's old hero.
    :type old_hero: :class:`Hero`
    :param new_hero: The player's new hero.
    :type new_hero: :class:`Hero`
    :param player: The new player object
    :type player: :class:`SearchPlayer`

.. _on_player_clan_join:

Player Clan Join
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_clan_join(player, clan)

    This event is called when a player joins a clan.

    :param member: The player who joined.
    :type member: :class:`SearchPlayer`
    :param clan: The clan the player joined.
    :type clan: :class:`Clan`


.. _on_player_clan_leave:

Player Clan Leave
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_clan_leave(player, clan)

    This event is called when a player leaves a clan.

    :param member: The member who left.
    :type member: :class:`SearchPlayer`
    :param clan: The clan the member left.
    :type clan: :class:`Clan`



.. _on_player_clan_level_change:

Player's Clan Level Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_clan_level_change(old_level, new_level, clan, player)

    This event is called when a player's clan's level changes.

    :param old_level: The old clan level
    :type old_level: int
    :param new_level: The new clan level
    :type new_level: int
    :param clan: The clan who's level changed
    :type clan: :class:`Clan`
    :param player: The player who's clan's level changed.
    :type player: :class:`SearchPlayer`


.. _on_player_clan_badge_change:

Player's Clan Badge Change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:function:: on_player_clan_badge_change(old_badge, new_badge, clan, player)

    This event is called when the clan's badge changes.

    :param old_badge: The old clan badge
    :type old_badge: :class:`Badge`
    :param new_badge: The new clan badge
    :type new_badge: :class:`Badge`
    :param clan: The clan who's badge changed
    :type clan: :class:`Clan`
    :param player: The player who's clan's badge changed.
    :type player: :class:`SearchPlayer`


Data Models
-------------------------
These are the data models used by the API. All calls will return one of these

Due to the unpredictable nature of the API and what Supercell returns, all attributes
have the possibility of being `None`. However, as much as possible, the library tries
to return an object most appropriate to results returned.

Due to this, there are many objects for what may seem like similar things.

Note: If a :class:`SearchPlayer` inherits :class:`BasicPlayer`, it will inherit all
attributes of both :class:`Player` and :class:`BasicPlayer`, however it will **not necessarily**
inherit :class:`WarMember`

Clans
~~~~~~

.. autoclass:: Clan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: BasicClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: SearchClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarClan()
    :members:
    :private-members:
    :inherited-members:


Players
~~~~~~~~

.. autoclass:: Player()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: BasicPlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarMember()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: SearchPlayer()
    :members:
    :private-members:
    :inherited-members:


Wars
~~~~~

.. autoclass:: BaseWar()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: WarLog()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: ClanWar()
    :members:
    :private-members:
    :inherited-members:


WarAttack
~~~~~~~~~~

.. autoclass:: WarAttack()
    :members:
    :private-members:


Achievement
~~~~~~~~~~~~

.. autoclass:: Achievement()
    :members:
    :private-members:


Troop
~~~~~~
.. autoclass:: Troop()
    :members:
    :private-members:


Hero
~~~~~

.. autoclass:: Hero()
    :members:
    :private-members:


Spell
~~~~~~

.. autoclass:: Spell()
    :members:
    :private-members:


Location
~~~~~~~~~

.. autoclass:: Location()
    :members:
    :private-members:


League Objects
~~~~~~~~~~~~~~~

.. autoclass:: League()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueRankedPlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LegendStatistics()
    :members:
    :private-members:
    :inherited-members:


Badge
~~~~~~

.. autoclass:: Badge()
    :members:
    :private-members:


Timestamp
~~~~~~~~~~

.. autoclass:: Timestamp()
    :members:
    :private-members:


League War Objects
~~~~~~~~~~~~~~~~~~~

.. autoclass:: LeaguePlayer()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueClan()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueGroup()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueWar()
    :members:
    :private-members:
    :inherited-members:

.. autoclass:: LeagueWarLogEntry()
    :members:
    :private-members:


Exceptions
--------------------
The following exceptions are thrown by the library.

.. autoexception:: ClashOfClansException

.. autoexception:: HTTPException

.. autoexception:: InvalidArgument

.. autoexception:: InvalidCredentials

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: Maitenance

.. autoexception:: GatewayError

.. autoexception:: PrivateWarLog
