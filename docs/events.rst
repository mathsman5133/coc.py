.. currentmodule:: coc
Events
=======
The following section provides an overview of the Events Client, providing
an easy introduction with a wealth of examples.

Events: What they are
----------------------
The Clash of Clans API, currently, provides no reasonable way to know when
for example, someone upgrades a troop, or attacks in war, without making repeated
calls and comparing objects over time.

The coc.py events client does exactly that: making requests to the API every X seconds,
comparing the results internally and dispatching relevant "events".

Functions are called, known as "callbacks" when these events occur, and are named as such.
You must register the functions you wish to be called, in addition to telling the library which
clan and player tags you wish to "track".

A huge number of events are available, ranging from war attacks to clan description changes to troop donations.

These are enumerated below, with their appropriate group:

+----------------------------------------------+-------------------------------------+
|     Event                                    | Group                               |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_update`                        | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_level_change`                  | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_description_change`            | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_public_war_log_change`         | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_type_change`                   | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_badge_change`                  | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_required_trophies_change`      | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_war_frequency_change`          | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_war_win_streak_change`         | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_war_win_change`                | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_war_tie_change`                | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_war_loss_change`               | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_join`                   | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_leave`                  | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_name_change`            | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_donation`               | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_received`               | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_role_change`            | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_rank_change`            | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_member_level_change`           | :ref:`clan_event_group`             |
+----------------------------------------------+-------------------------------------+
| :ref:`on_war_update`                         | :ref:`war_event_group`              |
+----------------------------------------------+-------------------------------------+
| :ref:`on_war_attack`                         | :ref:`war_event_group`              |
+----------------------------------------------+-------------------------------------+
| :ref:`on_war_state_change`                   | :ref:`war_event_group`              |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_update`                      | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_name_change`                 | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_townhall_upgrade`            | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_builderhall_upgrade`         | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_best_trophies_change`        | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_best_versus_trophies_change` | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_war_stars_change`            | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_attack_wins_change`          | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_defense_wins_change`         | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_versus_attacks_change`       | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_trophies_change`             | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_league_change`               | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_role_change`                 | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_donations_change`            | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_received_change`             | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_clan_rank_change`            | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_previous_clan_rank_change`   | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_achievement_change`          | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_troop_upgrade`               | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_spell_upgrade`               | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_hero_upgrade`                | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_clan_join`                   | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_clan_leave`                  | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_player_clan_level_change`           | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+
| :ref:`on_clan_badge_change`                  | :ref:`player_event_group`           |
+----------------------------------------------+-------------------------------------+

Adding Tags and Refresh Intervals
--------------------------------------
You must provide a (list of) player or clan tags in order for the client to "listen" to them and dispatch any events required.

The most simple way of doing this is by calling one of the following functions:

1. ``add_clan_update(tags, retry_interval=600)``
2. ``add_player_update(tags, retry_interval=600)``
3. ``add_war_update(tags, retry_interval=600)``

These will listen for clan, player and/or war events respectively, for the tags passed in.

Tags can be either a string (ie ``'#clan_tag'``), or an iterable (tuple, list, generator etc.) of tags (ie. ``['tag', 'anothertag']``).
You can set the retry interval, in other words how long the process should sleep between checking for events with the kwarg ``retry_interval``.
Time is in seconds, and it defaults to 600 (10min). Please note that setting this too high may be resource intensive,
and expose your program to ratelimit trouble. Examples of registering events are below:

.. code-block:: python3

    # to register a clan with tag #clan_tag:

    import coc
    client = coc.login('email', 'password', client=coc.EventsClient)

    client.add_clan_update('#clan_tag')

.. code-block:: python3

    # to register a list of clan tags for war events, refreshing every 60 seconds:

    import coc

    tags = ['#clan_tag', '#another_tag', '#third_tag']

    client = coc.login('email', 'password', client=coc.EventsClient)
    client.add_war_update(tags, retry_interval=60)

.. code-block:: python3

    # registering a clan + all members in the clan:

    import asyncio
    import coc

    client = coc.login('email', 'password', client=coc.EventsClient)

    async def add_players():
        clan = await client.get_clan('tag')
        player_tags = [m.tag for m in clan.members]
        client.add_player_update(player_tags)

    client.add_clan_update('tag')
    asyncio.ensure_future(add_players())


Registering and Removing Events
--------------------------------
All events must be registered before callbacks will be dispatched to them. This can be done in a variety of ways:

1. Using the decorator ``@client.event`` above the function. Possibly the easiest method, this should be the go-to option.
   Please note that the event and the function must have the same name, otherwise this will not work. An example is below.

.. code-block:: python3

    import coc

    client = coc.login('email', 'password', client=coc.EventsClient)

    @client.event
    async def on_clan_member_join(member, clan):
        return

2. Calling the function ``client.event(function, name)`` where ``function`` is the method you wish to register, and ``name`` is
   the name of the event you wish to register this function to. It defaults to the name of the function. Using this method may
   be preferable where the function name is not the same as the event name. Example below.

.. code-block:: python3

    import coc

    client = coc.login('email', 'password', client=coc.EventsClient)

    async def when_a_clan_member_joins(member, clan):
        return

    client.event(when_a_clan_member_joins, 'on_clan_member_join')

3. Calling the function ``client.add_events(*events, functions_dict={})``. This is the most comprehensive and complicated of the 3
   options, however, for multiple events, this is the easiest and can make using multiple calls just 1 call.
   You should pass in the functions you wish to register with the same name as named args, and a dict containing
   ``{'event_name': function}`` values. An example is below:

.. code-block:: python3

    import coc
    client = coc.login('email', 'password', client=coc.EventsClient)

    async def on_clan_member_join(member, clan)
        return

    async def on_clan_member_received(old, new, player):
        return

    async def description_change(old, new, clan):
        return

    async def donations(old, new, player):
        return

    client.add_events(on_clan_member_join, on_clan_member_received,
                      function_dicts=
                        {
                            'on_clan_member_donation': donations,
                            'on_clan_description_change': description_change
                        }
                      )

Should the need arise, events can be removed with the method ``client.remove_events(*events, functions_dict={})``
This works in the exact same fashion as ``client.add_events``.

.. code-block:: python3

    import coc
    client = coc.login('email', 'password', client=coc.EventsClient)

    async def on_clan_member_join(member, clan)
        return

    async def on_clan_member_received(old, new, player):
        return

    async def description_change(old, new, clan):
        return

    async def donations(old, new, player):
        return

    client.remove_events(on_clan_member_join, on_clan_member_received,
                         function_dicts=
                           {
                               'on_clan_member_donation': donations,
                               'on_clan_description_change': description_change
                           }
                         )

Working With Batch Updates
---------------------------
The library provides lower-level events called "batch updates", for when doing something for every donation
is a bit too resource intense. This is called once per "group" (player, clan, war), per "refresh" and contains
all events and args dispatched that cycle.

The function ``on_clan_batch_updates(events)`` will have 1 parameter, the events, which contains data as follows:

.. code-block:: json

    [
        [
            event_name (str),
            arg1,
            arg2,
            arg3,
            arg4,
            etc.
        ]
    ]

Ie. A nested list.

An example of using the batch updates to filter all new donations that rotation is below:

.. code-block:: python3

    import coc
    client = coc.login('email', 'password', client=coc.EventsClient)

    async def on_clan_batch_update(events):
        donation_events = [n for n in events if n[0] == 'on_clan_member_donation']

        # since we know that the event `on_clan_member_donation` has 3 args, old donations, new donations and player, we can do this:

        for event in donation_events:
            old_donations, new_donations, player = event
            difference = new_donations - old_donations
            print('{0.name} ({0.tag}) just donated {1} troop space'.format(player, difference)

While that example would have been just as easily done with a regular event, the possibilities opened up with this function is huge.
If you have a resource-intensive process that you only want called once per rotation, you can use this to ensure call it only once
and know that it is being called after all other events have been dispatched.


A Basic Example
----------------
The most basic usage, running a script forever which will check for new members every 10 minutes.

.. code-block:: python3

    import coc

    client = coc.login('email', 'password', client=coc.EventsClient)

    @client.event
    async def on_clan_member_join(member, clan):
        print('{0.name} ({0.tag}) just joined clan {1.name} ({1.tag}).'.format(member, clan)

    client.add_clan_update('clan tag')
    client.run_forever()

.. code-block:: python3

    import coc

    tags = ['#tag', '#anothertag', '#thirdtag']

    client = coc.login('email', 'password', client=coc.EventsClient)

    @client.event
    async def on_clan_member_donation(old_donation, new_donations, player):
        difference = new_donations - old_donations
        print('{0.name} ({0.tag}) just donated {1} troop space'.format(member, difference)

    client.add_clan_update(tags, retry_interval=30)  # check every 30 seconds
    client.run_forever()


Compressing Multiple Events
----------------------------

The following is an example of printing whenever a player upgrades a hero, troop or spell:

.. code-block:: python3

    import coc

    tags = ['#tag', '#anothertag', '#thirdtag']

    client = coc.login('email', 'password', client=coc.EventsClient)

    async def on_upgrade(old, new, player):
        # if the player only unlocked a troop, old will be None.
        if old:
            print('{0} upgraded their {1.name} from level {2.level} to {1.level}.'.format(player, new, old)
        else:
            print('{0} unlocked {1.name}.'.format(player, new)

    client.add_events(function_dicts=
                            {
                                'on_player_troop_upgrade': on_upgrade,
                                'on_player_hero_upgrade': on_upgrade,
                                'on_player_spell_upgrade': on_upgrade
                            }
                      )  # registers all 3 events to the 1 function

    client.add_player_update(tags, retry_interval=30)  # adds the tags + tells the client to check every 30sec
    client.run_forever()

Please note that in the example above, when registering multiple events to 1 function, care must be taken
that the number of parameters for all functions is the same, otherwise some weird errors may be experienced.
Alternatively, you could create the function with *args parameter, like follows:

.. code-block:: python3

    async def on_upgrade(*args, **kwargs):
        # we only care about events with 3 arguments - old, new, player.
        if len(args) != 3:
            return

        old, new, player = args

        if old:
            print('{0} upgraded their {1.name} from level {2.level} to {1.level}.'.format(player, new, old)
        else:
            print('{0} unlocked {1.name}.'.format(player, new)


