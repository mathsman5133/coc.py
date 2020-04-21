# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2019 mathsman5133

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import asyncio
import logging
import traceback

from collections.abc import Iterable
from typing import Union

from .cache import events_cache
from .client import Client
from .errors import Forbidden
from .utils import get

LOG = logging.getLogger(__name__)


class EventsClient(Client):
    # pylint: disable=missing-docstring
    __doc__ = Client.__doc__

    def __init__(self, **options):
        super().__init__(**options)
        self._war_retry_interval = None  # set in _setup()
        self._player_retry_interval = None  # set in _setup()
        self._clan_retry_interval = None  # set in _setup()
        self._setup()

    def _setup(self):
        self._clan_updates = []
        self._player_updates = []
        self._war_updates = []

        self._active_state_tasks = {}

        self._clan_retry_interval = 600
        self._player_retry_interval = 600
        self._war_retry_interval = 600

        self._clan_update_event = asyncio.Event(loop=self.loop)
        self._war_update_event = asyncio.Event(loop=self.loop)
        self._player_update_event = asyncio.Event(loop=self.loop)

        self._updater_tasks = {}

        self.extra_events = {}

        self._updater_tasks["clan"] = self.loop.create_task(self._clan_updater())
        self._updater_tasks["war"] = self.loop.create_task(self._war_updater())
        self._updater_tasks["player"] = self.loop.create_task(self._player_updater())
        for task in self._updater_tasks.values():
            task.add_done_callback(self._task_callback_check)

    def close(self):
        """Closes the client and all running tasks.
        """
        tasks = {t for t in asyncio.Task.all_tasks(loop=self.loop) if not t.done()}
        if not tasks:
            return
        for task in tasks:
            task.cancel()
        super().close()

    @events_cache()
    def dispatch(self, event_name: str, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        for event in self.extra_events.get(event_name, []):
            asyncio.ensure_future(self._run_event(event_name, event, *args, **kwargs), loop=self.loop)

    def event(self, function_, name=None):
        """A decorator or regular function that registers an event.

        The function **must** be a coroutine.

        Parameters
        ------------
        function_ : function
            The function to be registered (not needed if used with a decorator)
        name : str
            The name of the function to be registered. Defaults to the function name.

        Example
        --------

        .. code-block:: python3

            @client.event
            async def on_player_update(old_player, new_player):
                print('{} has updated their profile!'.format(old_player))

        Returns
        --------
        function : The function registered
        """
        if not asyncio.iscoroutinefunction(function_):
            raise TypeError("event {} must be a coroutine function".format(function_.__name__))

        name = name or function_.__name__

        if name == "on_event_error":
            setattr(self, name, function_)
            return function_

        if name in self.extra_events:
            self.extra_events[name].append(function_)
        else:
            self.extra_events[name] = [function_]

        LOG.info("Successfully registered %s event", name)
        return function_

    def add_events(self, *functions, function_dicts: dict = None):
        """Provides an alternative method to adding events.

        You can either provide functions as named args or as a dict of {name: function...} values.

        Example
        --------

        .. code-block:: python3

            client.add_events(on_member_update, on_clan_update, on_war_attack)
            # or, using a dict:
            client.add_events(function_dicts={'on_member_update': on_update,
                                              'on_clan_update': on_update_2
                                              }
                             )

        Parameters
        -----------
        functions : function
            Named args of functions to register. The name of event is dictated by function name.
        function_dicts : dict
            Dictionary of ``{'event_name': function}`` values.
        """
        for function_ in functions:
            self.event(function_)
        if function_dicts:
            for name, function_ in function_dicts.items():
                self.event(function_, name=name)

    def remove_events(self, *functions, function_dicts: dict = None):
        """Removes registered events from the client.

        Similar to :meth:`coc.add_events`, you can pass in functions as named args,
        or a list of {name: function...} values.

        Example
        --------

        .. code-block:: python3

            client.remove_events(on_member_update, on_clan_update, on_war_attack)
            # or, using a dict:
            client.remove_events(function_dicts={'on_member_update': on_update,
                                                 'on_clan_update': on_update_2
                                                }
                                )

        Parameters
        -----------
        functions : function
            Named args of functions to register. The name of event is dictated by function name.
        function_dicts : dict
            Dictionary of ``{'event_name': function}`` values.
        """
        for function_ in functions:
            try:
                self.extra_events.get(function_.__name__, []).remove(function_)
            except ValueError:
                continue
        if function_dicts:
            for name, function_ in function_dicts.items():
                try:
                    self.extra_events.get(name, []).remove(function_)
                except ValueError:
                    continue

    def run_forever(self):
        """A blocking call which runs the loop and script.

        This is useful if you have no other clients to deal
        with and just wish to run the script and receive updates indefinately.

        Roughly equivilant to:

        .. code-block:: python3

            try:
                client.loop.run_forever()
            except KeyboardInterrupt:
                client.close()
            finally:
                client.loop.close()

        """
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            LOG.info("Terminating bot and event loop.")
            self.close()

    async def _run_event(self, event_name, coro, *args, **kwargs):
        # pylint: disable=broad-except
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except (Exception, BaseException) as exception:
            try:
                await self.on_event_error(event_name, exception, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    async def on_event_error(self, event_name, exception, *args, **kwargs):
        """Event called when an event fails.

        By default this will print the traceback
        This can be overridden by either using @client.event or through subclassing EventsClient.

        Example
        --------

        .. code-block:: python3

            @client.event
            async def on_event_error(event_name, exception, *args, **kwargs):
                print('Ignoring exception in {}'.format(event_name))

            class Client(events.EventClient):
                async def on_event_error(event_name, exception, *args, **kwargs):
                    print('Ignoring exception in {}'.format(event_name))

        """
        # pylint: disable=unused-argument
        print("Ignoring exception in {}".format(event_name))
        traceback.print_exc()

    def add_clan_update(self, tags: Union[Iterable, str], retry_interval=600):
        """Subscribe clan tags to events.

        Parameters
        ------------
        tags : Union[:class:`collections.Iterable`, str]
            The clan tags to add. Could be an Iterable of tags or just a string tag.
        retry_interval : int
            In seconds, how often the client 'checks' for updates. Defaults to 600 (10min)
        """
        # pylint: disable=protected-access
        if isinstance(tags, str):
            if tags not in self._clan_updates:
                self._clan_updates.append(tags)
        else:
            self._clan_updates.extend(n for n in tags if n not in set(self._clan_updates))

        if retry_interval < 0:
            raise ValueError("retry_interval must be greater than 0 seconds")

        self._clan_retry_interval = retry_interval
        self.start_updates("clan")

    def add_war_update(self, tags: Union[Iterable, str], retry_interval=600):
        """Subscribe clan tags to war events.

        Parameters
        ------------
        tags : Union[:class:`collections.Iterable`, str]
            The clan tags to add. Could be an Iterable of tags or just a string tag.
        retry_interval : int
            In seconds, how often the client 'checks' for updates. Defaults to 600 (10min)
        """
        if isinstance(tags, str):
            if tags not in self._war_updates:
                self._war_updates.append(tags)
        else:
            self._war_updates.extend(n for n in tags if n not in set(self._war_updates))

        if retry_interval < 0:
            raise ValueError("retry_interval must be greater than 0 seconds")

        self._war_retry_interval = retry_interval
        self.start_updates("war")

    def add_player_update(self, tags: Union[Iterable, str], retry_interval=600):
        """Subscribe player tags to player update events.

        Parameters
        ------------
        tags : :class:`collections.Iterable`
            The player tags to add. Could be an Iterable of tags or just a string tag.
        retry_interval : int
            In seconds, how often the client 'checks' for updates. Defaults to 600 (10min)
        """
        if isinstance(tags, str):
            if tags not in self._player_updates:
                self._player_updates.append(tags)
        else:
            self._player_updates.extend(n for n in tags if n not in set(self._player_updates))

        if retry_interval < 0:
            raise ValueError("retry_interval must be greater than 0 seconds")

        self._player_retry_interval = retry_interval
        self.start_updates("player")

    def start_updates(self, event_group="all"):
        """Starts an, or all, events.

        .. note::

            This method **must** be called before any events are run.

        Parameters
        -----------
        event_group : str
            The event group to start updates for. Could be ``player``, ``clan``, ``war`` or ``all``.
            Defaults to 'all'

        Example
        --------
        .. code-block:: python3

            client.start_updates('clan')
            # or, for all events:
            client.start_updates('all')

        """
        lookup = {
            "clan": [self._clan_update_event, ["search_clans"]],
            "player": [self._player_update_event, ["search_players"]],
            "war": [self._war_update_event, ["current_wars", "clan_wars", "league_wars"],],  # noqa
        }
        if event_group == "all":
            events = lookup.values()
        else:
            events = [lookup[event_group]]

        for event in events:
            event[0].set()
            for cache_type in event[1]:
                self.cache.reset_event_cache(cache_type)

    def stop_updates(self, event_type="all"):
        """Stops an, or all, events.

        .. note::
            This method **must** be called in order to stop any events.

        Parameters
        -----------
        event_type : str
            See :meth:`EventsClient.start_updates` for which string corresponds to events.
            Defaults to 'all'

        Example
        --------
        .. code-block:: python3

            client.stop_updates('clan')
            # or, for all events:
            client.stop_updates('all')

        """

        lookup = {
            "clan": [self._clan_update_event, ["search_clans"]],
            "player": [self._player_update_event, ["search_players"]],
            "war": [self._war_update_event, ["current_wars", "clan_wars", "league_wars"],],  # noqa
        }
        if event_type == "all":
            events = lookup.values()
        else:
            events = [lookup[event_type]]

        for event in events:
            event[0].clear()
            for cache_type in event[1]:
                self.cache.reset_event_cache(cache_type)

    async def _dispatch_batch_updates(self, key_name):
        keys = await self.cache.keys("events")
        if not keys:
            return
        events = [n for n in keys if n.startswith(key_name)]

        self.dispatch(
            "{}_batch_updates".format(key_name), [await self.cache.pop("events", n) for n in events],
        )

    def _task_callback_check(self, result):
        if not result.done():
            return
        if result.cancelled():
            LOG.info("Task %s was cancelled", str(result))
            return

        exception = result.exception()
        if not exception:
            return

        LOG.warning(
            "Task raised an exception that was unhandled %s. Restarting the task.", exception,
        )

        lookup = {
            "clan": self._clan_updater,
            "player": self._player_updater,
            "war": self._war_updater,
        }

        for name, value in self._updater_tasks.items():
            if value != result:
                continue
            self._updater_tasks[name] = self.loop.create_task(lookup[name]())
            self._updater_tasks[name].add_done_callback(self._task_callback_check)

    async def _war_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await self._war_update_event.wait()
                await asyncio.sleep(self._war_retry_interval)
                await self._update_wars()
                await self._dispatch_batch_updates("on_war")
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_war_update", exception)
            return await self._war_updater()

    async def _clan_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await self._clan_update_event.wait()
                await asyncio.sleep(self._clan_retry_interval)
                await self._update_clans()
                await self._dispatch_batch_updates("on_clan")
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_clan_update", exception)
            return await self._clan_updater()

    async def _player_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await self._player_update_event.wait()
                await asyncio.sleep(self._player_retry_interval)
                await self._update_players()
                await self._dispatch_batch_updates("on_player")
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_player_update", exception)
            return await self._player_updater()

    async def _wait_for_state_change(self, state_to_wait_for, war):
        if state_to_wait_for == "inWar":
            to_sleep = war.start_time.seconds_until
        elif state_to_wait_for == "warEnded":
            to_sleep = war.end_time.seconds_until
        else:
            return

        await asyncio.sleep(to_sleep)

        try:
            war = await self.get_current_war(war.clan_tag)
        except Forbidden:
            return

        if war.state == state_to_wait_for:
            self.dispatch("on_war_state_change", state_to_wait_for, war)
            return

        return await self._wait_for_state_change(state_to_wait_for, war)

    def _check_state_task_status(self, clan_tag):
        try:
            states = self._active_state_tasks[clan_tag]
        except KeyError:
            return None, None

        return states.get("inWar"), states.get("warEnded")

    def _add_state_task(self, clan_tag, state, task):
        try:
            self._active_state_tasks[clan_tag][state] = task
        except KeyError:
            self._active_state_tasks[clan_tag] = {state: task}

    async def _update_wars(self):
        if not self._war_updates:
            return

        async for war in self.get_current_wars(self._war_updates, cache=False, update_cache=False):
            cached_war = await self.cache.get("current_wars", war.clan_tag)
            await self.cache.set("current_wars", war.clan_tag, war)

            if not cached_war:
                continue

            if war == cached_war:
                continue

            self._dispatch_war_differences(cached_war, war)

    def _dispatch_war_differences(self, cached_war, war):
        self.dispatch("on_war_update", cached_war, war)
        self._create_status_tasks(cached_war, war)

        if not war.opponent:
            # if there are no opponent next line will raise Attribute error..
            # we've just entered prep - this probably needs a rewrite.
            return

        if not war.iterattacks:
            # if there are no attacks next line will raise Attribute error..
            # we're not in war anymore anyway
            return

        if not cached_war.iterattacks:
            new_attacks = war.iterattacks
        else:
            new_attacks = (n for n in war.iterattacks if n not in set(cached_war.iterattacks))

        for attack in new_attacks:
            self.dispatch("on_war_attack", attack, war)

    def _create_status_tasks(self, cached_war, war):
        if cached_war.state != war.state and war.state == "preparation":
            self.dispatch("on_war_state_change", "preparation", war)

        if war.state not in ["preparation", "inWar", "warEnded"]:
            return

        in_war_task, war_ended_task = self._check_state_task_status(war.clan_tag)

        if not in_war_task or (war.start_time.time != cached_war.start_time.time):
            task = self.loop.create_task(self._wait_for_state_change("inWar", war))
            self._add_state_task(war.clan_tag, "inWar", task)

        if not war_ended_task or (war.end_time.time != cached_war.end_time.time):
            task = self.loop.create_task(self._wait_for_state_change("warEnded", war))
            self._add_state_task(war.clan_tag, "warEnded", task)

    async def _update_players(self):
        if not self._player_updates:
            return

        async for player in self.get_players(self._player_updates, cache=False, update_cache=False):
            cached_player = await self.cache.get("search_players", player.tag)
            await self.cache.set("search_players", player.tag, player)

            if not cached_player:
                continue

            if player == cached_player:
                continue

            self.dispatch("on_player_update", cached_player, player)
            self._dispatch_player_differences(cached_player, player)

    def _dispatch_player_differences(self, cached_player, player):
        # pylint: disable=too-many-branches
        # name
        if player.name != cached_player.name:
            self.dispatch("on_player_name_change", cached_player.name, player.name, player)

        # town/builder halls
        if player.town_hall != cached_player.town_hall:
            self.dispatch(
                "on_player_townhall_upgrade", cached_player.town_hall, player.town_hall, player,
            )
        if player.builder_hall != cached_player.builder_hall:
            self.dispatch(
                "on_player_builderhall_upgrade", cached_player.builder_hall, player.builder_hall, player,
            )

        # best trophies/versus/war stars
        if player.best_trophies != cached_player.best_trophies:
            self.dispatch(
                "on_player_best_trophies_change", cached_player.best_trophies, player.best_trophies, player,
            )
        if player.best_versus_trophies != cached_player.best_versus_trophies:
            self.dispatch(
                "on_player_best_versus_trophies_change",
                cached_player.best_versus_trophies,
                player.best_versus_trophies,
                player,
            )
        if player.war_stars != cached_player.war_stars:
            self.dispatch(
                "on_player_war_stars_change", cached_player.war_stars, player.war_stars, player,
            )

        # attacks win/defense/versus
        if player.attack_wins != cached_player.attack_wins:
            self.dispatch(
                "on_player_attack_wins_change", cached_player.attack_wins, player.attack_wins, player,
            )
        if player.defense_wins != cached_player.defense_wins:
            self.dispatch(
                "on_player_defense_wins_change", cached_player.defense_wins, player.defense_wins, player,
            )
        if player.versus_attack_wins != cached_player.versus_attack_wins:
            self.dispatch(
                "on_player_versus_attack_change", cached_player.versus_attack_wins, player.versus_attack_wins, player,
            )

        # trophies + league
        if player.trophies != cached_player.trophies:
            self.dispatch(
                "on_player_trophies_change", cached_player.trophies, player.trophies, player,
            )
        if player.league != cached_player.league:
            self.dispatch(
                "on_player_league_change", cached_player.league, player.league, player,
            )

        # clan stuff: role, donations, received, rank and prev. rank
        if player.role != cached_player.role:
            self.dispatch("on_player_role_change", cached_player.role, player.role, player)
        if player.donations != cached_player.donations:
            self.dispatch(
                "on_player_donations_change", cached_player.donations, player.donations, player,
            )
        if player.received != cached_player.received:
            self.dispatch(
                "on_player_received_change", cached_player.received, player.received, player,
            )

        self._dispatch_player_clan_differences(cached_player, player)

        achievement_updates = (n for n in player.achievements if n not in set(cached_player.achievements))
        troop_upgrades = (n for n in player.troops if n not in set(cached_player.troops))
        spell_upgrades = (n for n in player.spells if n not in set(cached_player.spells))
        hero_upgrades = (n for n in player.heroes if n not in set(cached_player.heroes))

        for achievement in achievement_updates:
            old_achievement = get(cached_player.achievements, name=achievement.name)
            self.dispatch("on_player_achievement_change", old_achievement, achievement, player)

        for troop in troop_upgrades:
            old_troop = get(cached_player.troops, name=troop.name)
            self.dispatch("on_player_troop_upgrade", old_troop, troop, player)

        for spell in spell_upgrades:
            old_spell = get(cached_player.spells, name=spell.name)
            self.dispatch("on_player_spell_upgrade", old_spell, spell, player)

        for hero in hero_upgrades:
            old_hero = get(cached_player.heroes, name=hero.name)
            self.dispatch("on_player_hero_upgrade", old_hero, hero, player)

    def _dispatch_player_clan_differences(self, cached_player, player):
        if player.clan_rank != cached_player.clan_rank:
            self.dispatch(
                "on_player_clan_rank_change", cached_player.clan_rank, player.clan_rank, player,
            )
        if player.clan_previous_rank != cached_player.clan_previous_rank:
            self.dispatch(
                "on_player_clan_previous_rank_change",
                cached_player.clan_previous_rank,
                player.clan_previous_rank,
                player,
            )

        # more clan stuff
        clan = player.clan
        cached_clan = cached_player.clan

        if not clan and not cached_clan:
            return
        if not clan and cached_clan:
            self.dispatch("on_player_clan_leave", cached_clan, player)
        elif not cached_clan and clan:
            self.dispatch("on_player_clan_join", clan, player)
        elif clan.tag != cached_clan.tag:
            self.dispatch("on_player_clan_leave", cached_clan, player)
            self.dispatch("on_player_clan_join", clan, player)

        if clan and cached_clan:
            if clan.tag != cached_clan.tag:
                return

            if clan.level != cached_clan.level:
                self.dispatch(
                    "on_player_clan_level_change", cached_clan.level, clan.level, clan, player,
                )

            if clan.badge != cached_clan.badge:
                self.dispatch(
                    "on_player_clan_badge_change", cached_clan.badge, clan.badge, clan, player,
                )

    async def _update_clans(self):
        if not self._clan_updates:
            return

        async for clan in self.get_clans(self._clan_updates, cache=False, update_cache=False):
            cached_clan = await self.cache.get("search_clans", clan.tag)
            await self.cache.set("search_clans", clan.tag, clan)

            if not cached_clan:
                continue

            if clan == cached_clan:
                continue

            self.dispatch("on_clan_update", cached_clan, clan)
            self._dispatch_clan_differences(cached_clan, clan)

    def _dispatch_clan_differences(self, cached_clan, clan):
        # pylint: disable=too-many-branches
        if clan.member_count != cached_clan.member_count:
            new_members = (n for n in clan.members if n.tag not in set(n.tag for n in cached_clan.members))
            for mem_join in new_members:
                self.dispatch("on_clan_member_join", mem_join, clan)

            old_members = (n for n in cached_clan.members if n.tag not in set(n.tag for n in clan.members))
            for mem_left in old_members:
                self.dispatch("on_clan_member_leave", mem_left, clan)

        if clan.members != cached_clan.members:
            self._dispatch_clan_member_differences(cached_clan, clan)

        # settings
        if clan.level != cached_clan.level:
            self.dispatch("on_clan_level_change", cached_clan.level, clan.level, clan)
        if clan.description != cached_clan.description:
            self.dispatch(
                "on_clan_description_change", cached_clan.description, clan.description, clan,
            )
        if clan.public_war_log != cached_clan.public_war_log:
            self.dispatch(
                "on_clan_public_war_log_change", cached_clan.public_war_log, clan.public_war_log, clan,
            )
        if clan.type != cached_clan.type:
            self.dispatch("on_clan_type_change", cached_clan.type, clan.type, clan)
        if clan.badge != cached_clan.badge:
            self.dispatch("on_clan_badge_change", cached_clan.badge, clan.badge, clan)
        if clan.required_trophies != cached_clan.required_trophies:
            self.dispatch(
                "on_clan_required_trophies_change", cached_clan.required_trophies, clan.required_trophies, clan,
            )
        if clan.war_frequency != cached_clan.war_frequency:
            self.dispatch(
                "on_clan_war_frequency_change", cached_clan.war_frequency, clan.war_frequency, clan,
            )

        # war win/loss/tie/streak
        if clan.war_win_streak != cached_clan.war_win_streak:
            self.dispatch(
                "on_clan_war_win_streak_change", cached_clan.war_win_streak, clan.war_win_streak, clan,
            )
        if clan.war_wins != cached_clan.war_wins:
            self.dispatch("on_clan_war_win_change", cached_clan.war_wins, clan.war_wins, clan)
        if clan.war_ties != cached_clan.war_ties:
            self.dispatch("on_clan_war_tie_change", cached_clan.war_ties, clan.war_ties, clan)
        if clan.war_losses != cached_clan.war_losses:
            self.dispatch("on_clan_war_loss_change", cached_clan.war_losses, clan.war_losses, clan)

    def _dispatch_clan_member_differences(self, cached_clan, clan):
        members = (n for n in clan.members if n != cached_clan.get_member(tag=n.tag))
        for member in members:
            cached_member = cached_clan.get_member(tag=member.tag)
            if not cached_member:
                continue

            if member.name != cached_member.name:
                self.dispatch(
                    "on_clan_member_name_change", cached_member.name, member.name, member,
                )
            if member.donations != cached_member.donations:
                self.dispatch(
                    "on_clan_member_donation", cached_member.donations, member.donations, member,
                )
            if member.received != cached_member.received:
                self.dispatch(
                    "on_clan_member_received", cached_member.received, member.received, member,
                )
            if member.trophies != cached_member.trophies:
                self.dispatch(
                    "on_clan_member_trophies_change", cached_member.trophies, member.trophies, member,
                )
            if member.versus_trophies != cached_member.versus_trophies:
                self.dispatch(
                    "on_clan_member_versus_trophies_change",
                    cached_member.versus_trophies,
                    member.versus_trophies,
                    member,
                )
            if member.role != cached_member.role:
                self.dispatch(
                    "on_clan_member_role_change", cached_member.role, member.role, member,
                )
            if member.clan_rank != cached_member.clan_rank:
                self.dispatch(
                    "on_clan_member_rank_change", cached_member.clan_rank, member.clan_rank, member,
                )
            if member.exp_level != cached_member.exp_level:
                self.dispatch(
                    "on_clan_member_level_change", cached_member.exp_level, member.exp_level, member,
                )
            if member.league != cached_member.league:
                self.dispatch(
                    "on_clan_member_league_change", cached_member.league, member.league, member,
                )
