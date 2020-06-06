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
import functools
import logging
import traceback


from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Union

from .client import Client
from .clans import Clan
from .players import Player, ClanMember
from .wars import ClanWar
from .errors import Forbidden
from .iterators import EventIterator
from .utils import get, maybe_coroutine

LOG = logging.getLogger(__name__)
DEFAULT_RETRY_SLEEP = 30


class TagMetadata:
    __slots__ = (
        "tag",
        "retry_interval",
        "events",
        "obj_cls",
        "_last_run",
        "_next_run",
    )

    def __init__(self, tag, retry_interval, events, obj_cls):
        self.tag = tag
        self.retry_interval = retry_interval
        self.events = events or []
        self.obj_cls = obj_cls
        self._last_run = None
        self._next_run = None

    def __eq__(self, other):
        return isinstance(other, TagMetadata) and self.tag == other.tag

    def add_event(self, event):
        self.events.append(event)

    def get_events(self, type):
        return (event for event in self.events if event.type_ == type)

    @property
    def last_run(self):
        return self._last_run

    @last_run.setter
    def last_run(self, value):
        self._last_run = value

    @property
    def next_run(self):
        set_next = self._next_run
        if set_next:
            return set_next  # handle default retry intervals

        last_run = self.last_run
        if last_run is None:
            return datetime.utcnow()  # handle first time runs

        return self.last_run + timedelta(seconds=self.retry_interval)

    @next_run.setter
    def next_run(self, value):
        if not self.retry_interval:
            self._next_run = datetime.utcnow() + timedelta(seconds=value)

    @property
    def can_run(self):
        return datetime.utcnow() >= self.next_run


class Event:
    __slots__ = ("runner", "callback", "tag", "type_")

    def __init__(self, runner, callback, tag, type_):
        self.runner = runner
        self.callback = callback
        self.tag = tag
        self.type_ = type_

    def __call__(self, cached, current):
        return self.runner(cached, current, self.callback)

    @classmethod
    def from_decorator(cls, func):
        return cls(func.__event_runner, func, func.__event_tags, func.__event_type)


def register_event(func, runner, tags, cls, retry_interval, event_type):
    if getattr(func, "__is_event_listener", False):
        raise RuntimeError("maximum of one event per callback function.")

    if not asyncio.iscoroutinefunction(func):
        raise TypeError("callback function must be of type coroutine.")

    if not tags:
        tags = ()
    elif isinstance(tags, str):
        tags = (tags,)
    elif isinstance(tags, Iterable):
        tags = tuple(tags)
    else:
        raise TypeError("tags must be of type str, or iterable not {0!r}".format(tags))

    if retry_interval is not None and not isinstance(retry_interval, int):
        raise TypeError("retry_interval must be of type int not {0!r}".format(retry_interval))

    func.__event_type = event_type
    func.__event_tags = tags
    func.__is_event_listener = True
    func.__event_cls = cls
    func.__event_retry_interval = retry_interval

    if not asyncio.iscoroutinefunction(runner):
        raise TypeError("runner function must be of type coroutine")

    func.__event_runner = runner

    return func


def prepare_player_events(pred, tags, player_cls, retry_interval):
    if not issubclass(player_cls, Player):
        raise TypeError("player_cls must be of type Player not {0!r}".format(player_cls))

    def decorator(func):
        return register_event(func, pred, tags, player_cls, retry_interval, "player")

    return decorator


def wrap_pred(pred):
    async def wrapped(cached, live, callback):
        if pred(cached, live):
            return await callback(cached, live)

    return wrapped


class ClanEvents:
    event_type = "clan"

    @classmethod
    def prepare(cls, pred, tags, clan_cls, retry_interval):
        if not issubclass(clan_cls, Clan):
            raise TypeError("clan_cls must be of type Clan not {0!r}".format(clan_cls))

        def decorator(func):
            return register_event(func, pred, tags, clan_cls, retry_interval, "clan")

        return decorator

    @classmethod
    def wrap_member_pred(cls, pred):
        async def wrapped(cached_clan, clan, callback):
            LOG.critical("running cache check")
            for member in clan.members:
                cached_member = cached_clan.get_member(member.tag)
                if cached_member and pred(cached_member, member):
                    await callback(cached_member, member)

        return wrapped

    @classmethod
    def level_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan, clan):
            return cached_clan.level == clan.level

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def description_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan, clan):
            return cached_clan.description == clan.description

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def public_warlog_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan, clan):
            return cached_clan.description == clan.description

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def type_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan, clan):
            return cached_clan.type == clan.type

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def badge_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan, clan):
            return cached_clan.badge == clan.badge

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def required_trophies_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan, clan):
            return cached_clan.required_trophies == clan.required_trophies

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def war_frequency_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan: Clan, clan: Clan):
            return cached_clan.war_frequency == clan.war_frequency

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def war_win_streak_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan: Clan, clan: Clan):
            return cached_clan.war_win_streak == clan.war_win_streak

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def war_wins_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan: Clan, clan: Clan):
            return cached_clan.war_wins == clan.war_wins

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def war_ties_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan: Clan, clan: Clan):
            return cached_clan.war_ties == clan.war_ties

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def war_losses_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan: Clan, clan: Clan):
            return cached_clan.war_losses == clan.war_losses

        return ClanEvents.prepare(wrap_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_name_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.name == clan_member.name

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_role_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.role == clan_member.role

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_exp_level_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.exp_level == clan_member.exp_level

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_league_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.league == clan_member.league

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_trophies_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.trophies == clan_member.trophies

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_versus_trophies_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.versus_trophies == clan_member.versus_trophies

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_clan_rank_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.clan_rank == clan_member.clan_rank

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_previous_clan_rank_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.previous_clan_rank == clan_member.previous_clan_rank

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_donations_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.donations == clan_member.donations

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_received_change(cls, tags=None, clan_cls=Clan, retry_interval=None):
        def pred(cached_clan_member, clan_member):
            return cached_clan_member.received == clan_member.received

        return ClanEvents.prepare(ClanEvents.wrap_member_pred(pred), tags, clan_cls, retry_interval)

    @classmethod
    def member_join(cls, tags=None, clan_cls=Clan, retry_interval=None):
        async def wrapped(cached_clan, clan, callback):
            # we can't check the member_count first incase 1 person left and joined within the 60sec.
            members_joined = (n for n in clan.members if n.tag not in set(n.tag for n in cached_clan.members))
            for member in members_joined:
                await callback(member)

        return ClanEvents.prepare(wrapped, tags, clan_cls, retry_interval)

    @classmethod
    def member_leave(cls, tags=None, clan_cls=Clan, retry_interval=None):
        async def wrapped(cached_clan, clan, callback):
            # we can't check the member_count first incase 1 person left and joined within the 60sec.
            members_left = (n for n in cached_clan.members if n.tag not in set(n.tag for n in clan.members))
            for member in members_left:
                await callback(member)

        return ClanEvents.prepare(wrapped, tags, clan_cls, retry_interval)


class PlayerEvents:
    event_type = "player"

    @classmethod
    def name_change(cls, tags=None, player_cls=Player, retry_interval=None):
        def pred(cached_player, player):
            return cached_player.name == player.name

        return prepare_player_events(wrap_pred(pred), tags, player_cls, retry_interval)

    @classmethod
    def donations_change(cls, tags=None, player_cls=Player, retry_interval=None):
        def pred(cached_player, player):
            return cached_player.donations == player.donations

        return prepare_player_events(wrap_pred(pred), tags, player_cls, retry_interval)

    @classmethod
    def received_change(cls, tags=None, player_cls=Player, retry_interval=None):
        def pred(cached_player, player):
            return cached_player.received == player.received

        return prepare_player_events(wrap_pred(pred), tags, player_cls, retry_interval)

    @classmethod
    def trophies_change(cls, tags=None, player_cls=Player, retry_interval=None):
        def pred(cached_player, player):
            return cached_player.trophies == player.trophies

        return prepare_player_events(wrap_pred(pred), tags, player_cls, retry_interval)

    @classmethod
    def versus_trophies_change(cls, tags=None, player_cls=Player, retry_interval=None):
        def pred(cached_player, player):
            return cached_player.versus_trophies == player.versus_trophies

        return prepare_player_events(pred, tags, player_cls, retry_interval)


class WarEvents:
    event_type = "war"

    @classmethod
    def war_attack(cls, tags=None, war_cls=ClanWar, retry_interval=None):
        async def wrapped(cached_war, war, callback):
            if cached_war.attacks:
                new_attacks = (a for a in war.attacks if a not in set(cached_war.attacks))
            else:
                new_attacks = war.attacks

            for attack in new_attacks:
                await callback(attack, war)

        return prepare_war_events(wrapped, tags, war_cls, retry_interval)


class EventsClient(Client):
    # pylint: disable=missing-docstring
    __doc__ = Client.__doc__

    def __init__(self, **options):
        super().__init__(**options)
        self._setup()

        self._setup_via_decorators = None

        self._clan_retry_interval = 60
        self._player_retry_interval = 60
        self._war_retry_interval = 60

        self._clan_cls = Clan
        self._player_cls = Player
        self._war_cls = ClanWar

        self._clan_tags = set()
        self._player_tags = set()
        self._war_tags = set()

    def _setup(self):
        self._updater_tasks = {
            "clan": self.loop.create_task(self._clan_updater()),
            "player": self.loop.create_task(self._player_updater()),
            "war": self.loop.create_task(self._war_updater()),
        }

        for task in self._updater_tasks.values():
            task.add_done_callback(self._task_callback_check)

        self._tag_metadata = {"clan": {}, "player": {}, "war": {}}

        self._listeners = {"clan": [], "player": [], "war": []}

        self._clans = {}
        self._players = {}

    @property
    def clan_retry_interval(self):
        return self._clan_retry_interval

    @clan_retry_interval.setter
    def clan_retry_interval(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif value is None:
            self._clan_retry_interval = None
        elif not isinstance(value, int):
            raise TypeError("retry_interval must be of type int or None not {0!r}".format(value))
        elif value < 0:
            raise ValueError("retry_interval must be greater than 0 seconds")
        else:
            self._clan_retry_interval = value
            self._setup_via_decorators = False

    @property
    def player_retry_interval(self):
        return self._clan_retry_interval

    @player_retry_interval.setter
    def player_retry_interval(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif value is None:
            self._player_retry_interval = None
        elif not isinstance(value, int):
            raise TypeError("retry_interval must be of type int or None not {0!r}".format(value))
        elif value < 0:
            raise ValueError("retry_interval must be greater than 0 seconds")
        else:
            self._player_retry_interval = value
            self._setup_via_decorators = False

    @property
    def war_retry_interval(self):
        return self._clan_retry_interval

    @war_retry_interval.setter
    def war_retry_interval(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif value is None:
            self._war_retry_interval = None  # default value
        elif not isinstance(value, int):
            raise TypeError("retry_interval must be of type int or None not {0!r}".format(value))
        elif value < 0:
            raise ValueError("retry_interval must be greater than 0 seconds")
        else:
            self._war_retry_interval = value
            self._setup_via_decorators = False

    @property
    def clan_cls(self):
        return self._clan_cls

    @clan_cls.setter
    def clan_cls(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif not isinstance(value, Clan):
            raise TypeError("clan_cls must be of type Clan not {0!r}".format(value))
        else:
            self._clan_cls = value
            self._setup_via_decorators = False

    @property
    def player_cls(self):
        return self._player_cls

    @player_cls.setter
    def player_cls(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif not isinstance(value, Player):
            raise TypeError("player_cls must be of type Player not {0!r}".format(value))
        else:
            self._player_cls = value
            self._setup_via_decorators = False

    @property
    def war_cls(self):
        return self._war_cls

    @war_cls.setter
    def war_cls(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif not isinstance(value, ClanWar):
            raise TypeError("war_cls must be of type ClanWar not {0!r}".format(value))
        else:
            self._war_cls = value
            self._setup_via_decorators = False

    @property
    def clan_tags(self):
        return self._clan_tags

    @clan_tags.setter
    def clan_tags(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif not isinstance(value, Iterable):
            raise TypeError("clan_tags must be of type Iterable not {0!r}".format(value))
        else:
            self._clan_tags.update(*value)
            self._setup_via_decorators = False

    @property
    def player_tags(self):
        return self._player_tags

    @player_tags.setter
    def player_tags(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif not isinstance(value, Iterable):
            raise TypeError("player_tags must be of type Iterable not {0!r}".format(value))
        else:
            self._player_tags.update(*value)
            self._setup_via_decorators = False

    @property
    def war_tags(self):
        return self._war_tags

    @war_tags.setter
    def war_tags(self, value):
        if self._setup_via_decorators is True:
            raise RuntimeError("you cannot setup via both decorators and properties.")
        elif not isinstance(value, Iterable):
            raise TypeError("war_tags must be of type Iterable not {0!r}".format(value))
        else:
            self._war_tags.update(*value)
            self._setup_via_decorators = False

    def _get_tag_metadata(self, event_type, tag):
        try:
            return self._tag_metadata[event_type][tag]
        except KeyError:
            return None

    def _get_cached_clan(self, clan_tag):
        try:
            return self._clans[clan_tag]
        except KeyError:
            return None

    def _update_clan(self, clan):
        self._players[clan.tag] = clan

    def _get_cached_player(self, player_tag):
        try:
            return self._players[player_tag]
        except KeyError:
            return None

    def _update_player(self, player):
        self._players[player.tag] = player

    def event(self, func):
        """A decorator or regular function that registers an event.

        The function **may be** be a coroutine.

        Parameters
        ------------
        function_ : function
            The function to be registered (not needed if used with a decorator)

        Example
        --------

        .. code-block:: python3

            import coc

            client = coc.login(...)

            @client.event
            @coc.ClanEvents.description_change
            async def player_donated_troops(old_player, new_player):
                print('{} has donated troops!'.format(new_player))

        .. note::

            The order of decorators is important - the ``@client.event`` one must lay **above**

        Returns
        --------
        function : The function registered
        """
        if not getattr(func, "__is_event_listener"):
            raise ValueError("no events found to register to this callback")

        event = Event.from_decorator(func)

        retry_interval = getattr(func, "__event_retry_interval")
        cls = getattr(func, "__event_cls")
        tags = getattr(func, "__event_tags")

        if (retry_interval or cls or tags) and self._setup_via_decorators is False:
            raise RuntimeError("retry_interval, cls or tags arguments are incompatible with manual setup of events.")
        elif self._setup_via_decorators is False or not (retry_interval or cls or tags):
            # basically check if they do @coc.ClanEvents.level_change() or have done client.edit_clan_metadata somewhere
            # since the 2 ways of setting up events are incompatible.
            self._listeners[event.type_].append(event)
            return

        for tag in tags:
            existing = self._get_tag_metadata(event.type_, tag)
            if existing is not None:
                if existing.retry_interval != retry_interval:
                    raise ValueError("retry_interval must be the same for all events for tag {}".format(tag))
                elif existing.obj_cls != cls:
                    raise ValueError("cls must be the same for all events added to tag {}".format(tag))
                else:
                    existing.add_event(event)
            else:
                self._tag_metadata[event.type_][tag] = TagMetadata(tag, retry_interval, [event], cls)

        self._setup_via_decorators = True

        LOG.info("Successfully registered %s event", func)
        return func

    def add_events(self, *events):
        r"""Shortcut to add many events at once.

        This method just iterates over :meth:`EventsClient.listener`.

        Parameters
        -----------
        \*\listeners: :class:`function`
            The listener functions to add.
        """
        for event in events:
            self.event(event)

    def remove_events(self, *events):
        r"""Shortcut to remove many events at once.

        Parameters
        -----------
        \*\listeners: :class:`function`
            The listener functions to remove.
        """
        for listener in events:
            event = Event.from_decorator(listener)
            self._listeners[event.tag].remove(event)

            try:
                del self._tag_metadata[event.tag][event.type_]
            except KeyError:
                pass

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
            self.close()

    def close(self):
        """Closes the client and all running tasks.
        """
        tasks = {t for t in asyncio.Task.all_tasks(loop=self.loop) if not t.done()}
        for task in tasks:
            task.cancel()
        super().close()

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
        LOG.exception("test")
        print("Ignoring exception in {}".format(event_name))
        traceback.print_exc()

    def _task_callback_check(self, result):
        if not result.done():
            return
        if result.cancelled():
            LOG.info("Task %s was cancelled", str(result))
            return

        exception = result.exception()
        if not exception:
            return

        LOG.exception("Task raised an exception that was unhandled. Restarting the task.", exc_info=exception)

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
                await asyncio.sleep(self._war_retry_interval or DEFAULT_RETRY_SLEEP)
                await self._in_maintenance_event.wait()
                await self._update_wars()
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_war_update", exception)
            return await self._war_updater()

    async def _clan_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                LOG.info("running")
                await asyncio.sleep(self._clan_retry_interval or DEFAULT_RETRY_SLEEP)
                await self._in_maintenance_event.wait()
                await self._update_clans()
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_clan_update", exception)
            return await self._clan_updater()

    async def _player_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                LOG.info("running")
                await asyncio.sleep(self._player_retry_interval or DEFAULT_RETRY_SLEEP)
                await self._in_maintenance_event.wait()
                await self._update_players()
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_player_update", exception)
            return await self._player_updater()

    async def _update_players(self):
        LOG.info("running to report")
        LOG.info(str(self._tag_metadata))
        LOG.info(str(self._listeners))

        tag_metadata = self._tag_metadata["player"].values()
        if not tag_metadata:
            LOG.info("nothing to report")
            return

        set_via_decorator = self._setup_via_decorators
        default_retry = self.player_retry_interval == 0

        if set_via_decorator is True:
            LOG.info("set via deco")
            filtered = (m for m in tag_metadata if m.can_run)
            iterator = EventIterator(self, filtered, self.get_player)
        else:
            filtered = (m.tag for m in tag_metadata if m.can_run)
            iterator = self.get_players(filtered, cls=self.player_cls)

        LOG.info(f"iterator is {iterator} and tags are {filtered}")
        async for player in iterator:
            LOG.info(str(player))
            cached_player = self._get_cached_player(player.tag)
            self._update_player(player)

            if not cached_player:
                continue

            if set_via_decorator or default_retry:
                metadata = self._get_tag_metadata("player", player.tag)
                metadata.next_run = player._response_retry

            if set_via_decorator:
                for listener in metadata.get_events(type="player"):
                    await listener(cached_player, player)
            else:
                for listener in self._listeners["player"]:
                    await listener(cached_player, player)

    async def _update_clans(self):
        tag_metadata = self._tag_metadata["clan"].values()
        if not tag_metadata:
            return

        set_via_decorator = self._setup_via_decorators

        if set_via_decorator:
            filtered = (m for m in tag_metadata if m.can_run)
            iterator = EventIterator(self, filtered, self.get_clan)
        else:
            filtered = (m.tag for m in tag_metadata if m.can_run)
            iterator = self.get_clans(filtered, cls=self.clan_cls)

        async for clan in iterator:
            cached_clan = self._get_cached_clan(clan.tag)
            self._update_clan(clan)

            if not cached_clan:
                continue

            metadata = self._get_tag_metadata("clan", clan.tag)
            if self.player_retry_interval == 0:
                metadata.next_run = clan._response_retry

            if set_via_decorator:
                for listener in metadata.events:
                    await listener(cached_clan, clan)
            else:
                for listener in self._listeners["clans"]:
                    await listener(cached_clan, clan)

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

        if not war.state == cached_war.state:
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
        if war.state == "preparation":
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
