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
import time
import weakref

from collections.abc import Iterable
from datetime import datetime

from .client import Client
from .clans import Clan
from .players import Player
from .wars import ClanWar
from .errors import Maintenance, PrivateWarLog
from .utils import correct_tag

LOG = logging.getLogger(__name__)
DEFAULT_SLEEP = 10


class Event:
    __slots__ = ("runner", "callback", "tags", "type")

    def __init__(self, runner, callback, tags, type):
        self.runner = runner
        self.callback = callback
        self.tags = tags
        self.type = type

    def __call__(self, cached, current):
        return self.runner(cached, current, self.callback)

    @classmethod
    def from_decorator(cls, func):
        return cls(func.event_runner, func, func.event_tags, func.event_type)


class _ValidateEvent:
    def __init__(self, cls):
        self.cls = cls

    def __getattr__(self, item):
        try:
            return getattr(self.cls, item)
        except AttributeError:
            pass

        print(item)
        # this is only called if the attr/func is not found the normal way.
        if "change" not in item:
            return

        # handle member_x events:
        if "member_" in item:
            item = item.strip("member_")
            nested = True
        else:
            nested = False

        return self._create_event(item.strip("_change"), nested)

    def _create_event(self, item, nested: bool = False):
        def pred(cached, live):
            return getattr(cached, item) != getattr(live, item)

        def actual(tags=None, custom_class=None, retry_interval=None):
            # custom_class = custom_class or lookup.get(self.cls.event_type)
            try:
                custom_class and not nested and getattr(
                    custom_class, item
                )  # don't type check if it's nested... not worth the bother
            except AttributeError:
                raise RuntimeError("custom_class does not have expected attribute %s", item)

            def decorator(func):
                if nested:
                    wrap = _ValidateEvent.wrap_clan_member_pred
                else:
                    wrap = _ValidateEvent.wrap_pred
                return _ValidateEvent.register_event(
                    func, wrap(pred), tags, custom_class, retry_interval, self.cls.event_type
                )

            return decorator

        return actual

    @staticmethod
    def shortcut_register(wrapped, tags, custom_class, retry_interval, event_type):
        def decorator(func):
            return _ValidateEvent.register_event(func, wrapped, tags, custom_class, retry_interval, event_type)

        return decorator

    @staticmethod
    def wrap_pred(pred):
        async def wrapped(cached, live, callback):
            if pred(cached, live):
                return await callback(cached, live)

        return wrapped

    @staticmethod
    def wrap_clan_member_pred(pred):
        async def wrapped(cached_clan, clan, callback):
            for member in clan.members:
                cached_member = cached_clan.get_member(member.tag)
                if cached_member is not None and pred(cached_member, member) is True:
                    await callback(cached_member, member)

        return wrapped

    @staticmethod
    def register_event(func, runner, tags=None, cls=None, retry_interval=None, event_type=""):
        if getattr(func, "is_event_listener", False):
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

        if not asyncio.iscoroutinefunction(runner):
            raise TypeError("runner function must be of type coroutine")

        func.event_type = event_type
        func.event_tags = tags
        func.is_event_listener = True
        func.event_cls = cls
        func.event_retry_interval = retry_interval
        func.event_runner = runner
        return func


@_ValidateEvent
class ClanEvents:
    event_type = "clan"

    @classmethod
    def member_join(cls, tags=None, custom_class=Clan, retry_interval=None):
        async def wrapped(cached_clan, clan, callback):
            # we can't check the member_count first incase 1 person left and joined within the 60sec.
            members_joined = (n for n in clan.members if n.tag not in set(n.tag for n in cached_clan.members))
            for member in members_joined:
                await callback(member)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, ClanEvents.event_type)

    @classmethod
    def member_leave(cls, tags=None, custom_class=Clan, retry_interval=None):
        async def wrapped(cached_clan, clan, callback):
            # we can't check the member_count first incase 1 person left and joined within the 60sec.
            members_left = (n for n in cached_clan.members if n.tag not in set(n.tag for n in clan.members))
            for member in members_left:
                await callback(member)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, ClanEvents.event_type)


@_ValidateEvent
class PlayerEvents:
    event_type = "player"

    @classmethod
    def achievement_change(cls, tags=None, custom_class=Player, retry_interval=None):
        async def wrapped(cached_player, player, callback):
            achievement_updates = (n for n in player.achievements if n not in set(cached_player.achievements))
            for achievement in achievement_updates:
                await callback(cached_player, player, achievement)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def troop_change(cls, tags=None, custom_class=Player, retry_interval=None):
        async def wrapped(cached_player, player, callback):
            troop_upgrades = (n for n in player.troops if n not in set(cached_player.troops))
            for troop in troop_upgrades:
                await callback(cached_player, player, troop)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def spell_change(cls, tags=None, custom_class=Player, retry_interval=None):
        async def wrapped(cached_player, player, callback):
            spell_upgrades = (n for n in player.spells if n not in set(cached_player.spells))
            for spell in spell_upgrades:
                await callback(cached_player, player, spell)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def hero_change(cls, tags=None, custom_class=Player, retry_interval=None):
        async def wrapped(cached_player, player, callback):
            hero_upgrades = (n for n in player.heroes if n not in set(cached_player.heroes))
            for hero in hero_upgrades:
                await callback(cached_player, player, hero)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)


@_ValidateEvent
class WarEvents:
    event_type = "war"

    @classmethod
    def war_attack(cls, tags=None, custom_class=ClanWar, retry_interval=None):
        async def wrapped(cached_war, war, callback):
            if cached_war.attacks:
                new_attacks = (a for a in war.attacks if a not in set(cached_war.attacks))
            else:
                new_attacks = war.attacks

            for attack in new_attacks:
                await callback(attack, war)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, WarEvents.event_type)


class EventsLocker:
    def __init__(self, lock):
        self.lock = lock
        self.unlock = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.unlock:
            self.lock.release()


class EventsClient(Client):
    # pylint: disable=missing-docstring
    __doc__ = Client.__doc__

    def __init__(self, **options):
        super().__init__(**options)
        self._setup()

        self._in_maintenance_event = asyncio.Event()
        self._keys_ready = asyncio.Event()

        self.clan_retry_interval = 10
        self.player_retry_interval = 10
        self.war_retry_interval = 10

        self.clan_cls = Clan
        self.player_cls = Player
        self.war_cls = ClanWar

        self.is_cwl_active = options.pop("cwl_active", True)

        self._locks = {}

    def _setup(self):
        self._updater_tasks = {
            "clan": self.loop.create_task(self._clan_updater()),
            "player": self.loop.create_task(self._player_updater()),
            "war": self.loop.create_task(self._war_updater()),
        }

        for task in self._updater_tasks.values():
            task.add_done_callback(self._task_callback_check)

        self._clan_updates = set()
        self._player_updates = set()
        self._war_updates = set()

        self._listeners = {"clan": [], "player": [], "war": []}

        self._clans = {}
        self._players = {}
        self._wars = {}

    async def login(self, email: str, password: str):
        await super().login(email, password)
        self.loop.create_task(self.maintenance_poller())

    def add_clan_updates(self, value):
        if isinstance(value, str):
            if self.correct_tags:
                self._clan_updates.add(correct_tag(value))
            else:
                self._clan_updates.add(value)

        elif isinstance(value, Iterable):
            if self.correct_tags:
                self._clan_updates.update(correct_tag(tag) for tag in value)
            else:
                self._clan_updates.update(value)

        else:
            raise TypeError("clan tags must be of type str or Iterable not {0!r}".format(value))

    def add_player_updates(self, value):
        if isinstance(value, str):
            if self.correct_tags:
                self._player_updates.add(correct_tag(value))
            else:
                self._player_updates.add(value)

        elif isinstance(value, Iterable):
            if self.correct_tags:
                self._player_updates.update(correct_tag(tag) for tag in value)
            else:
                self._player_updates.update(value)

        else:
            raise TypeError("player tags must be of type str or Iterable not {0!r}".format(value))

    def add_war_updates(self, value):
        if isinstance(value, str):
            if self.correct_tags:
                self._war_updates.add(correct_tag(value))
            else:
                self._war_updates.add(value)

        elif isinstance(value, Iterable):
            if self.correct_tags:
                self._war_updates.update(correct_tag(tag) for tag in value)
            else:
                self._war_updates.update(value)

        else:
            raise TypeError("clan war tags must be of type str or Iterable not {0!r}".format(value))

    def _get_cached_clan(self, clan_tag):
        try:
            return self._clans[clan_tag]
        except KeyError:
            return None

    def _update_clan(self, clan):
        self._clans[clan.tag] = clan

    def _get_cached_player(self, player_tag):
        try:
            return self._players[player_tag]
        except KeyError:
            return None

    def _update_player(self, player):
        self._players[player.tag] = player

    def _get_cached_war(self, key):
        try:
            return self._wars[key]
        except KeyError:
            return None

    def _update_war(self, key, war):
        self._wars[key] = war

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
            @coc.ClanEvents.description_change()
            async def player_donated_troops(old_player, new_player):
                print('{} has donated troops!'.format(new_player))

        .. note::

            The order of decorators is important - the ``@client.event`` one must lay **above**

        Returns
        --------
        function : The function registered
        """
        if not getattr(func, "is_event_listener", None):
            raise ValueError("no events found to register to this callback")

        event = Event.from_decorator(func)

        retry_interval = getattr(func, "event_retry_interval")
        cls = getattr(func, "event_cls")
        tags = getattr(func, "event_tags")
        event_type = event.type

        self._listeners[event_type].append(event)

        if event_type == "clan":
            self.clan_cls = cls or self.clan_cls
            self.clan_retry_interval = retry_interval or self.clan_retry_interval
            self.add_clan_updates(tags)
        elif event_type == "player":
            self.player_cls = cls or self.player_cls
            self.player_retry_interval = retry_interval or self.player_retry_interval
            self.add_player_updates(tags)
        elif event_type == "war":
            self.war_cls = cls or self.war_cls
            self.war_retry_interval = retry_interval or self.war_retry_interval
            self.add_war_updates(tags)

        LOG.info("Successfully registered %s event", func)
        return func

    def add_events(self, *events):
        r"""Shortcut to add many events at once.

        This method just iterates over :meth:`EventsClient.listener`.

        Parameters
        -----------
        \*\events: :class:`function`
            The event listener functions to add.
        """
        for event in events:
            self.event(event)

    def remove_events(self, *events):
        r"""Shortcut to remove many events at once.

        Parameters
        -----------
        \*\events: :class:`function`
            The event listener functions to remove.
        """
        for e in events:
            event = Event.from_decorator(e)
            self._listeners[event.type].remove(event)

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

    async def maintenance_poller(self):
        maintenance_start = None
        try:
            while True:
                await self._in_maintenance_event.wait()
                if maintenance_start is None:
                    maintenance_start = datetime.utcnow()
                    self.dispatch("maintenance")
                try:
                    await self.get_clan("#G88CYQP")  # my clan
                except Maintenance:
                    await asyncio.sleep(5)
                else:
                    self._in_maintenance_event.clear()
                    self.dispatch("maintenance_completion", maintenance_start)
                    maintenance_start = None

        except asyncio.CancelledError:
            pass
        except:
            LOG.exception("maintenance poller exitted. restarting.")
            return await self.maintenance_poller()

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
                if self._in_maintenance_event.is_set():
                    continue  # don't run if we're hitting maintenance errors.
                await asyncio.sleep(DEFAULT_SLEEP)

                s = time.perf_counter()
                tasks = [asyncio.ensure_future(self._run_war_update(tag)) for tag in self._war_updates]
                await asyncio.gather(*tasks)
                print(f"war updater took {(time.perf_counter() - s)*1000}ms")
                LOG.info(f"war updater took {(time.perf_counter() - s)*1000}ms")

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_war_update", exception)
            return await self._war_updater()

    async def _clan_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                self.loop.create_future()
                if self._in_maintenance_event.is_set():
                    continue  # don't run if we're hitting maintenance errors.
                await asyncio.sleep(DEFAULT_SLEEP)

                s = time.perf_counter()
                tasks = [self.loop.create_task(self._run_clan_update(tag)) for tag in self._clan_updates]
                await asyncio.gather(*tasks)
                LOG.info(f"clan updater took {(time.perf_counter() - s)*1000}ms")
        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_clan_update", exception)
            return await self._clan_updater()

    async def _player_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                if self._in_maintenance_event.is_set():
                    continue  # don't run if we're hitting maintenance errors.
                await asyncio.sleep(DEFAULT_SLEEP)
                LOG.info(self._players)

                s = time.perf_counter()
                # for tag in self._update_tags["player"]:
                #     await self._run_player_update(tag)
                tasks = [self.loop.create_task(self._run_player_update(tag)) for tag in self._player_updates]
                await asyncio.gather(*tasks)
                print(self._player_updates)
                print(f"player updater took {(time.perf_counter() - s)*1000}ms")

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            await self.on_event_error("on_player_update", exception)
            return await self._player_updater()

    async def _run_player_update(self, player_tag):
        key = "player:{}".format(player_tag)
        lock = self._locks.get(key)
        if lock is None:
            self._locks[key] = lock = asyncio.Lock()

        await lock.acquire()
        player = await self.get_player(player_tag, cls=self.player_cls)
        # sleep for either
        self.loop.call_later(max(player._response_retry, self.player_retry_interval), lock.release)

        cached_player = self._get_cached_player(player_tag)
        self._update_player(player)

        if cached_player is None:
            return

        for listener in self._listeners["player"]:
            if listener.tags and player_tag not in listener.tags:
                LOG.info("no listener")
                continue
            await listener(cached_player, player)

    async def _run_clan_update(self, clan_tag):
        key = "clan:{}".format(clan_tag)
        lock = self._locks.get(key)
        if lock is None:
            self._locks[key] = lock = asyncio.Lock()

        await lock.acquire()
        clan = await self.get_clan(clan_tag, cls=self.clan_cls)
        # sleep for either the global retry or whenever a new player object is available, whichever is smaller.
        self.loop.call_later(max(clan._response_retry, self.player_retry_interval), lock.release)

        cached_clan = self._get_cached_clan(clan_tag)
        self._update_clan(clan)

        if not cached_clan:
            return

        for listener in self._listeners["clan"]:
            if listener.tags and clan_tag not in listener.tags:
                LOG.info("no listener")
                continue
            await listener(cached_clan, clan)

    async def _run_war_update(self, clan_tag):
        key = "war:{}".format(clan_tag)
        lock = self._locks.get(key)
        if lock is None:
            self._locks[key] = lock = asyncio.Lock()

        await lock.acquire()

        if self.is_cwl_active:
            meth = self.get_current_war
        else:
            meth = self.get_clan_war
        try:
            war = await meth(clan_tag, cls=self.war_cls)
        except PrivateWarLog:
            return

        # sleep for either the global retry or whenever a new player object is available, whichever is smaller.
        self.loop.call_later(max(war._response_retry, self.player_retry_interval), lock.release)

        cached_war = self._get_cached_war(clan_tag)
        self._update_war(clan_tag, war)

        if not cached_war:
            return

        for listener in self._listeners["war"]:
            if listener.tags and clan_tag not in listener.tags:
                LOG.info("no listener")
                continue
            await listener(cached_war, war)
