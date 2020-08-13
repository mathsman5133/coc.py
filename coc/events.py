"""
MIT License

Copyright (c) 2019-2020 mathsman5133

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
import json

from collections.abc import Iterable
from datetime import datetime

import asqlite

from .client import Client
from .clans import Clan
from .players import Player
from .wars import ClanWar
from .errors import Forbidden, Maintenance, PrivateWarLog
from .utils import correct_tag

LOG = logging.getLogger(__name__)
DEFAULT_SLEEP = 10


class Event:
    """Object that is created for an event. This contains runner functions, tags and type."""

    __slots__ = ("runner", "callback", "tags", "type")

    def __init__(self, runner, callback, tags, type_):
        self.runner = runner
        self.callback = callback
        self.tags = tags
        self.type = type_

    def __call__(self, cached, current):
        return self.runner(cached, current, self.callback)

    def __eq__(self, other):
        return isinstance(self, other.__class__) and self.runner == other.runner and self.callback == other.callback

    @classmethod
    def from_decorator(cls, func, runner):
        """Helper classmethod to create an event from a function"""
        return cls(runner, func, func.event_tags, func.event_type)


class _ValidateEvent:
    """Helper class to validate and register a function as an event."""

    def __init__(self, cls):
        self.cls = cls

    def __getattr__(self, item: str):
        try:
            return getattr(self.cls, item)
        except AttributeError:
            pass

        if self.cls.event_type == "client":
            return self.cls.__getattr__(self.cls, item)

        # handle member_x events:
        if "member_" in item:
            item = item.replace("member_", "")
            nested = True
        else:
            nested = False

        return self._create_event(item.replace("_change", ""), nested)

    def _create_event(self, item, nested=False):
        def pred(cached, live) -> bool:
            return getattr(cached, item) != getattr(live, item)

        def actual(tags=None, custom_class=None, retry_interval=None):
            try:
                # don't type check if it's nested... not worth the bother
                custom_class and not nested and getattr(custom_class, item)
            except AttributeError:
                raise RuntimeError("custom_class does not have expected attribute {}".format(item))

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
        """Fast route of registering an event for custom events that are manually defined."""

        def decorator(func):
            return _ValidateEvent.register_event(func, wrapped, tags, custom_class, retry_interval, event_type)

        return decorator

    @staticmethod
    def wrap_pred(pred):
        """Wraps a predicate in a coroutine that awaits the callback if the predicate is True."""

        async def wrapped(cached, live, callback):
            if pred(cached, live):
                await callback(cached, live)

        return wrapped

    @staticmethod
    def wrap_clan_member_pred(pred):
        """Wraps a predicate for a clan member (ie nested) attribute from clan objects, and calls the callback."""

        async def wrapped(cached_clan: Clan, clan: Clan, callback):
            for member in clan.members:
                cached_member = cached_clan.get_member(member.tag)
                if cached_member is not None and pred(cached_member, member) is True:
                    cached_member.clan = cached_clan
                    member.clan = clan
                    await callback(cached_member, member)

        return wrapped

    @staticmethod
    def register_event(func, runner, tags=None, cls=None, retry_interval=None, event_type=""):
        """Validates the types of all arguments and adds these as attributes to the function."""
        # pylint: disable=too-many-arguments
        if getattr(func, "is_event_listener", False) and func.event_type != event_type:
            raise RuntimeError("maximum of one event type per callback function.")

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
        try:
            func.event_runners.append(runner)
        except AttributeError:
            func.event_runners = [runner]

        return func


@_ValidateEvent
class ClanEvents:
    """Predefined clan events, or you can create your own with `@coc.ClanEvents.clan_attr_change`."""

    event_type = "clan"

    @classmethod
    def member_join(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a member has joined the clan."""

        async def wrapped(cached_clan, clan, callback):
            current_tags = set(n.tag for n in cached_clan.members)
            if not current_tags:
                return
            # we can't check the member_count first incase 1 person left and joined within the 60sec.
            members_joined = (n for n in clan.members if n.tag not in current_tags)
            for member in members_joined:
                await callback(member, clan)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, ClanEvents.event_type)

    @classmethod
    def member_leave(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a member has left the clan."""

        async def wrapped(cached_clan, clan, callback):
            # we can't check the member_count first incase 1 person left and joined within the 60sec.
            current_tags = set(n.tag for n in clan.members)
            if not current_tags:
                return
            members_left = (n for n in cached_clan.members if n.tag not in current_tags)
            for member in members_left:
                await callback(member, clan)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, ClanEvents.event_type)


@_ValidateEvent
class PlayerEvents:
    """Class that defines all valid player events."""

    event_type = "player"

    @classmethod
    def achievement_change(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player has increased the value of an achievement."""

        async def wrapped(cached_player, player, callback):
            achievement_updates = (n for n in player.achievements if n not in set(cached_player.achievements))
            for achievement in achievement_updates:
                await callback(cached_player, player, achievement)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def troop_change(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player has upgraded or unlocked a troop."""

        async def wrapped(cached_player, player, callback):
            troop_upgrades = (n for n in player.troops if n not in set(cached_player.troops))
            for troop in troop_upgrades:
                await callback(cached_player, player, troop)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def spell_change(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player has upgraded or unlocked a spell."""

        async def wrapped(cached_player, player, callback):
            spell_upgrades = (n for n in player.spells if n not in set(cached_player.spells))
            for spell in spell_upgrades:
                await callback(cached_player, player, spell)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def hero_change(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player has upgraded or unlocked a hero."""

        async def wrapped(cached_player, player, callback):
            hero_upgrades = (n for n in player.heroes if n not in set(cached_player.heroes))
            for hero in hero_upgrades:
                await callback(cached_player, player, hero)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def joined_clan(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player has joined a new clan."""

        async def wrapped(cached_player, player, callback):
            if cached_player.clan is None and player.clan is not None:
                await callback(cached_player, player)
            elif cached_player.clan is not None and player.clan is not None and cached_player.clan != player.clan:
                await callback(cached_player, player)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def left_clan(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player has joined a new clan."""

        async def wrapped(cached_player, player, callback):
            if cached_player.clan is not None and player.clan is None:
                await callback(cached_player, player)
            elif cached_player.clan and player.clan and cached_player.clan.tag != player.clan.tag:
                await callback(cached_player, player)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def clan_name(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player's clan's name has changed."""

        async def wrapped(cached_player, player, callback):
            if cached_player.clan and player.clan and cached_player.clan.name != player.clan.name:
                await callback(cached_player, player)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def clan_badge(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player's clan's badge has changed."""

        async def wrapped(cached_player, player, callback):
            if cached_player.clan and player.clan and cached_player.clan.badge != player.clan.badge:
                await callback(cached_player, player)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)

    @classmethod
    def clan_level(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a player's clan's level has changed."""

        async def wrapped(cached_player, player, callback):
            if cached_player.clan and player.clan and cached_player.clan.level != player.clan.level:
                await callback(cached_player, player)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, PlayerEvents.event_type)


@_ValidateEvent
class WarEvents:
    """Class that defines all valid war events."""

    event_type = "war"

    @classmethod
    def war_attack(cls, tags=None, custom_class=None, retry_interval=None):
        """Event for when a war player has made an attack."""

        async def wrapped(cached_war, war, callback):
            if cached_war.attacks:
                new_attacks = (a for a in war.attacks if a not in set(cached_war.attacks))
            else:
                new_attacks = war.attacks

            for attack in new_attacks:
                await callback(attack, war)

        return _ValidateEvent.shortcut_register(wrapped, tags, custom_class, retry_interval, WarEvents.event_type)


@_ValidateEvent
class ClientEvents:
    """Class that defines all valid client/misc events."""

    event_type = "client"

    def __getattr__(self, item):
        def wrapped():
            def deco(function):
                function.is_client_event = True
                function.event_name = item
                return function

            return deco

        return wrapped


class EventsClient(Client):
    # pylint: disable=missing-docstring
    __doc__ = Client.__doc__

    def __init__(self, **options):
        super().__init__(**options)
        self._setup()

        self._in_maintenance_event = asyncio.Event()
        self._keys_ready = asyncio.Event()

        self.clan_retry_interval = 0
        self.player_retry_interval = 0
        self.war_retry_interval = 0

        self.clan_cls = Clan
        self.player_cls = Player
        self.war_cls = ClanWar

        self.clan_loops_run = 0
        self.player_loops_run = 0
        self.war_loops_run = 0

        self.is_cwl_active = options.pop("cwl_active", True)
        self.sqlite_path = options.pop("sqlite_path", "coc-events.db")
        self.events_batch_limit = options.pop("events_batch_limit", None)
        self._conn = None  # set in create_schema
        self._transaction_lock = asyncio.Lock()

    def _setup(self):
        self._updater_tasks = {
            "clan": self.loop.create_task(self._clan_updater()),
            "player": self.loop.create_task(self._player_updater()),
            "war": self.loop.create_task(self._war_updater()),
            "maintenance": self.loop.create_task(self._maintenance_poller()),
        }

        for task in self._updater_tasks.values():
            task.add_done_callback(self._task_callback_check)

        self._clan_updates = set()
        self._player_updates = set()
        self._war_updates = set()

        self._listeners = {"clan": [], "player": [], "war": [], "client": {}}

        self._clans = {}
        self._players = {}
        self._wars = {}

    async def login(self, email: str, password: str):
        await super().login(email, password)
        await self._create_schema()

    def add_clan_updates(self, *tags):
        """Add clan tags to receive updates for.

        Parameters
        ------------
        \\*tags : str
            The clan tags to add. If you wish to pass in an iterable, you must unpack it with \\*.

        Example
        -------
        .. code-block:: python3

            client.add_clan_updates("#tag1", "#tag2", "#tag3")

            tags = ["#tag4", "#tag5", "#tag6"]
            client.add_clan_updates(*tags)
        """
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("clan tag must be of type str not {0!r}".format(tag))
            self._clan_updates.add(correct_tag(tag))

    def remove_clan_updates(self, *tags):
        """Remove clan tags that you receive events updates for.

        Parameters
        ------------
        \\*tags : str
            The clan tags to remove. If you wish to pass in an iterable, you must unpack it with \\*.

        Example
        -------
        .. code-block:: python3

            client.remove_clan_updates("#tag1", "#tag2", "#tag3")

            tags = ["#tag4", "#tag5", "#tag6"]
            client.remove_clan_updates(*tags)
        """
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("clan tag must be of type str not {0!r}".format(tag))
            try:
                self._clan_updates.remove(correct_tag(tag))
            except KeyError:
                pass  # tag didn't exist to start with

    def add_player_updates(self, *tags):
        r"""Add player tags to receive events for.

        Parameters
        ------------
        \\*tags : str
            The player tags to add. If you wish to pass in an iterable, you must unpack it with \*\.

        Example
        -------
        .. code-block:: python3

            client.add_player_updates("#tag1", "#tag2", "#tag3")

            tags = ["#tag4", "#tag5", "#tag6"]
            client.add_player_updates(*tags)

        """
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("player tag must be of type str not {0!r}".format(tag))
            self._player_updates.add(correct_tag(tag))

    def remove_player_updates(self, *tags):
        r"""Remove player tags that you receive events updates for.

        Parameters
        ------------
        \\*tags : str
            The player tags to remove. If you wish to pass in an iterable, you must unpack it with \*\.

        Example
        -------
        .. code-block:: python3

            client.remove_player_updates("#tag1", "#tag2", "#tag3")

            tags = ["#tag4", "#tag5", "#tag6"]
            client.remove_player_updates(*tags)

        """
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("player tag must be of type str not {0!r}".format(tag))
            try:
                self._player_updates.remove(correct_tag(tag))
            except KeyError:
                pass  # the tag was never added

    def add_war_updates(self, *tags):
        r"""Add clan tags to receive war events for.

        Parameters
        ------------
        \\*tags : str
            The clan tags to add that will receive war events.
            If you wish to pass in an iterable, you must unpack it with \*\.

        Example
        -------
        .. code-block:: python3

            client.add_war_updates("#tag1", "#tag2", "#tag3")

            tags = ["#tag4", "#tag5", "#tag6"]
            client.add_war_updates(*tags)
        """
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("clan war tags must be of type str not {0!r}".format(tag))
            self._war_updates.add(correct_tag(tag))

    def remove_war_updates(self, *tags):
        r"""Remove player tags that you receive events updates for.

        Parameters
        ------------
        \\*tags : str
            The clan tags to remove that will receive war events.
            If you wish to pass in an iterable, you must unpack it with \*\.

        Example
        -------
        .. code-block:: python3

            client.remove_war_updates("#tag1", "#tag2", "#tag3")

            tags = ["#tag4", "#tag5", "#tag6"]
            client.remove_war_updates(*tags)
        """
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("clan war tags must be of type str not {0!r}".format(tag))
            try:
                self._war_updates.remove(correct_tag(tag))
            except KeyError:
                pass  # tag didn't exist to start with

    def _get_cached_clan(self, clan_tag):
        try:
            return self._clans[clan_tag]
        except KeyError:
            return None

    def _get_cached_player(self, player_tag):
        try:
            return self._players[player_tag]
        except KeyError:
            return None

    def _get_cached_war(self, key):
        try:
            return self._wars[key]
        except KeyError:
            return None

    def event(self, function):
        """A decorator or regular function that registers an event.

        The function **may be** be a coroutine.

        Parameters
        ------------
        function : function
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

        .. code-block:: python3

            import coc

            client = coc.login(...)

            @client.event
            @coc.ClientEvents.maintenance_start()
            async def maintenance_has_started():
                print('maintenance has started!')

        .. note::

            The order of decorators is important - the ``@client.event`` one must lay **above**

        Returns
        --------
        function : The function registered
        """
        if getattr(function, "is_client_event", False):
            try:
                self._listeners["client"][function.event_name].append(function)
            except KeyError:
                self._listeners["client"][function.event_name] = [function]
            return function

        if not getattr(function, "is_event_listener", None):
            raise ValueError("no events found to register to this callback")

        events = [Event.from_decorator(function, runner) for runner in function.event_runners]

        retry_interval = getattr(function, "event_retry_interval")
        cls = getattr(function, "event_cls")
        tags = getattr(function, "event_tags")
        event_type = events[0].type

        self._listeners[event_type].extend(events)

        if event_type == "clan":
            self.clan_cls = cls or self.clan_cls
            self.clan_retry_interval = retry_interval or self.clan_retry_interval
            self.add_clan_updates(*tags)
        elif event_type == "player":
            self.player_cls = cls or self.player_cls
            self.player_retry_interval = retry_interval or self.player_retry_interval
            self.add_player_updates(*tags)
        elif event_type == "war":
            self.war_cls = cls or self.war_cls
            self.war_retry_interval = retry_interval or self.war_retry_interval
            self.add_war_updates(*tags)

        LOG.info("Successfully registered %s event", function)
        return function

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
        for function in events:
            for runner in function.event_runners:
                event = Event.from_decorator(function, runner)
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
        """Closes the client and all running tasks."""
        tasks = {t for t in asyncio.Task.all_tasks(loop=self.loop) if not t.done()}
        for task in tasks:
            task.cancel()
        super().close()

    def dispatch(self, event_name: str, *args, **kwargs):
        # pylint: disable=broad-except
        registered = self._listeners["client"].get(event_name)
        if registered is None:
            if event_name == "event_error":
                LOG.exception("Ignoring exception in event task.")
                print("Ignoring exception in event task.")
                traceback.print_exc()

        else:
            for event in registered:
                try:
                    asyncio.ensure_future(event(*args, **kwargs))
                except (BaseException, Exception):
                    LOG.exception("Ignoring exception in %s.", event_name)

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
            "maintenance": self._maintenance_poller,
        }

        for name, value in self._updater_tasks.items():
            if value != result:
                continue
            self._updater_tasks[name] = self.loop.create_task(lookup[name]())
            self._updater_tasks[name].add_done_callback(self._task_callback_check)

    async def _maintenance_poller(self):
        # pylint: disable=broad-except
        maintenance_start = None
        try:
            while self.loop.is_running():
                await self._in_maintenance_event.wait()
                if maintenance_start is None:
                    maintenance_start = datetime.utcnow()
                    for event in self._listeners["client"].get("maintenance_start", []):
                        try:
                            asyncio.ensure_future(event())
                        except (BaseException, Exception) as exc:
                            self.dispatch("event_error", exc)
                try:
                    # just need to remove the cache layer
                    try:
                        del self.http.cache["https://api.clashofclans.com/v1/clans/%23G88CYQP"]
                    except KeyError:
                        pass
                    await self.get_clan("#G88CYQP")  # my clan
                except (Maintenance, Exception):
                    await asyncio.sleep(5)
                else:
                    self._in_maintenance_event.clear()
                    for event in self._listeners["client"].get("maintenance_completion", []):
                        try:
                            asyncio.ensure_future(event(maintenance_start))
                        except (BaseException, Exception) as exc:
                            self.dispatch("event_error", exc)
                    maintenance_start = None

        except asyncio.CancelledError:
            pass
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._maintenance_poller()

    async def _create_schema(self):
        self._conn = await asqlite.connect(self.sqlite_path, loop=self.loop)

        queries = (
            "CREATE TABLE IF NOT EXISTS war (tag text PRIMARY KEY, data text NOT NULL, cache_expires integer);",
            "CREATE INDEX IF NOT EXISTS war_cache_expires_idx ON war(cache_expires);",
            "CREATE TABLE IF NOT EXISTS clan (tag text PRIMARY KEY, data text, cache_expires integer default 0);",
            "CREATE INDEX IF NOT EXISTS clan_cache_expires_idx ON clan(cache_expires);",
            "CREATE TABLE IF NOT EXISTS player (tag text PRIMARY KEY, data text, cache_expires integer default 0);",
            "CREATE INDEX IF NOT EXISTS player_cache_expires_idx ON player(cache_expires);",
        )
        for query in queries:
            await self._conn.execute(query)

    async def _load_from_db(self, loop_type):
        lookup = {"player": self._player_updates, "war": self._war_updates, "clan": self._clan_updates}
        updates = lookup[loop_type]

        # loop_type can only be war, clan or player.
        results = await self._conn.fetchall(f"SELECT tag FROM {loop_type}")
        if len(results) != len(updates):
            new_tags = set(n for n in updates if n not in results)
            old_tags = set(n for n in results if n not in updates)
            query = f"INSERT INTO {loop_type} (tag, cache_expires) VALUES (?, strftime('%s', 'now'))"
            async with self._transaction_lock, self._conn.transaction():
                for tag in new_tags:
                    await self._conn.execute(query, tag)
                for tag in old_tags:
                    await self._conn.execute(f"DELETE FROM {loop_type} WHERE tag = ?", tag)

        query = f"SELECT tag, data FROM {loop_type} WHERE strftime('%s', 'now') > cache_expires LIMIT ?"
        results = await self._conn.fetchall(query, self.events_batch_limit or len(updates))
        return {tag: data and json.loads(data) for tag, data in results}

    async def _update_db(self, loop_type, cache):
        # loop_type can only be war, clan or player.
        query = f"REPLACE INTO {loop_type} (tag, data, cache_expires) VALUES (?, ?, strftime('%s','now') + ?)"
        async with self._transaction_lock, self._conn.transaction():
            for tag, data in cache.items():
                cache_expires = data.pop("_response_retry")
                await self._conn.execute(query, tag, json.dumps(data), cache_expires)

    async def _war_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await asyncio.sleep(DEFAULT_SLEEP)
                if self._in_maintenance_event.is_set():
                    continue  # don't run if we're hitting maintenance errors.

                self._wars = await self._load_from_db("war")

                self.dispatch("war_loop_start", list(self._wars.keys()))
                tasks = [
                    self.loop.create_task(self._run_war_update(tag)) for index, tag in enumerate(self._wars.keys())
                ]
                await asyncio.gather(*tasks)
                await self._update_db("war", self._wars)
                self.dispatch("war_loop_finish", list(self._wars.keys()))

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._war_updater()

    async def _clan_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await asyncio.sleep(DEFAULT_SLEEP)
                if self._in_maintenance_event.is_set():
                    continue  # don't run if we're hitting maintenance errors.

                self._clans = await self._load_from_db("clan")

                self.dispatch("clan_loop_start", list(self._clans.keys()))
                tasks = [
                    self.loop.create_task(self._run_clan_update(tag)) for index, tag in enumerate(self._clans.keys())
                ]
                await asyncio.gather(*tasks)
                await self._update_db("clan", self._clans)
                self.dispatch("clan_loop_finish", self.clan_loops_run)

                self.clan_loops_run += 1

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._clan_updater()

    async def _player_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await asyncio.sleep(DEFAULT_SLEEP)
                if self._in_maintenance_event.is_set():
                    continue  # don't run if we're hitting maintenance errors.

                self._players = await self._load_from_db("player")

                self.dispatch("player_loop_start", list(self._players.keys()))
                tasks = [
                    self.loop.create_task(self._run_player_update(tag))
                    for index, tag in enumerate(self._players.keys())
                ]
                await asyncio.gather(*tasks)
                await self._update_db("player", self._players)
                self.dispatch("player_loop_finish", self.player_loops_run)
                self.player_loops_run += 1

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._player_updater()

    async def _run_player_update(self, player_tag):
        # pylint: disable=protected-access, broad-except
        try:
            data = await self.http.get_player(player_tag)
        except Maintenance:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return

        cached_data = self._get_cached_player(player_tag)
        self._players[data["tag"]] = data

        data.pop("_response_retry")  # need to remove to properly __eq__

        if data is None or cached_data is None or cached_data == data:
            return

        cached_player = self.player_cls(data=cached_data, client=self)
        player = self.player_cls(data=data, client=self)
        for listener in self._listeners["player"]:
            if listener.tags and player_tag not in listener.tags:
                continue
            await listener(cached_player, player)

    async def _run_clan_update(self, clan_tag):
        # pylint: disable=protected-access, broad-except
        try:
            data = await self.http.get_clan(clan_tag)
        except Maintenance:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return

        cached_data = self._get_cached_clan(clan_tag)
        self._clans[data["tag"]] = data

        data.pop("_response_retry")  # need to remove to properly __eq__

        if data is None or cached_data is None or cached_data == data:
            return

        cached_clan = self.clan_cls(data=cached_data, client=self)
        clan = self.clan_cls(data=data, client=self)

        for listener in self._listeners["clan"]:
            if listener.tags and clan_tag not in listener.tags:
                continue
            await listener(cached_clan, clan)

    async def _run_war_update(self, clan_tag):
        # pylint: disable=protected-access, broad-except
        try:
            # to-do: make this more efficient
            if self.is_cwl_active:
                war = await self.get_current_war(clan_tag, cls=self.war_cls)
                if war.is_cwl:
                    data = await self.http.get_cwl_wars(war.war_tag)
                else:
                    data = await self.http.get_clan_current_war(clan_tag)
            else:
                data = await self.http.get_clan_current_war(clan_tag)
                war = self.war_cls(data=data, client=self, clan_tag=clan_tag)
        except (Maintenance, PrivateWarLog, Forbidden):
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return

        cached_data = self._get_cached_war(clan_tag)
        self._wars[clan_tag] = data

        data.pop("_response_retry")  # need to remove to properly __eq__

        if data is None or cached_data is None or cached_data == data:
            return

        cached_war = self.war_cls(data=cached_data, client=self)

        for listener in self._listeners["war"]:
            if listener.tags and clan_tag not in listener.tags:
                continue
            await listener(cached_war, war)
