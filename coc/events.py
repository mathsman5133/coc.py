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

from collections.abc import Iterable
from datetime import datetime, timedelta

import coc.raid
from .client import Client
from .clans import Clan
from .enums import WarRound
from .players import Player
from .wars import ClanWar
from .errors import Maintenance, PrivateWarLog
from .utils import correct_tag, get_season_end, get_clan_games_start, get_clan_games_end

LOG = logging.getLogger(__name__)
DEFAULT_SLEEP = 10


class Event:
    """
    Object that is created for an event. This contains runner functions,
    tags and type.
    """

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
        if "member_" in item and item != "member_count":
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
                    func, wrap(pred), tags, custom_class, retry_interval, self.cls.event_type, item
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
    def register_event(func, runner, tags=None, cls=None, retry_interval=None, event_type="", event_name=""):
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
        func.event_name = event_name
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

    @classmethod
    def new_war(cls, tags=None, custom_class=None, retry_interval=None):
        """Alias for the preparation start time changes, which is equal to a new war started"""

        async def wrapped(cached_war: ClanWar, war: ClanWar, callback):
            if cached_war.preparation_start_time and war.preparation_start_time \
                    and cached_war.preparation_start_time.time != war.preparation_start_time.time:
                await callback(war)
            elif war.preparation_start_time and not cached_war.preparation_start_time:
                # no war on endpoint, so new war is for sure new
                await callback(war)
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
        self._in_maintenance_event.set()  # only block when maintenance is on

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
        self.check_cwl_prep = options.pop("check_cwl_prep", False)

        self._locks = {}

    def _setup(self):
        self._updater_tasks = {
            "clan": self.loop.create_task(self._clan_updater()),
            "player": self.loop.create_task(self._player_updater()),
            "war": self.loop.create_task(self._war_updater()),
            "maintenance": self.loop.create_task(self._maintenance_poller()),
            "season": self.loop.create_task(self._end_of_season_poller()),
            "raid_weekend": self.loop.create_task(self._raid_poller()),
            "clan_games": self.loop.create_task(self._clan_games_poller())
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

    def add_clan_updates(self, *tags):
        """Add clan tags to receive updates for.

        Parameters
        ----------
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
        ----------
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
        ----------
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
        ----------
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
        ----------
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
        ----------
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

    def event(self, function):
        """A decorator or regular function that registers an event.

        The function **may be** be a coroutine.

        Parameters
        ----------
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
            if function.event_name == "members":
                self.check_cwl_prep = True  # we need to check cwl clans in prep for this one.

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
            "season": self._end_of_season_poller
        }

        for name, value in self._updater_tasks.items():
            if value != result:
                continue
            self._updater_tasks[name] = self.loop.create_task(lookup[name]())
            self._updater_tasks[name].add_done_callback(self._task_callback_check)

    async def _raid_poller(self):
        # pylint: disable=broad-except, protected-access
        try:
            age = 0
            while self.loop.is_running():
                try:
                    [raid_log_entry] = await self.get_raid_log("#2PP", limit=1)
                    raid_log_entry: coc.raid.RaidLogEntry
                except Maintenance:
                    await asyncio.sleep(15)
                except Exception:
                    await asyncio.sleep(DEFAULT_SLEEP)
                else:
                    if raid_log_entry.start_time.seconds_until + age > 0 and raid_log_entry.end_time.seconds_until > 0:
                        # raid started
                        self.dispatch("raid_weekend_start")
                    elif raid_log_entry.end_time.seconds_until + age > 0 > raid_log_entry.end_time.seconds_until:
                        # raid ended
                        self.dispatch("raid_weekend_end")
                    # sleep for response_retry + 1
                    age = raid_log_entry._response_retry + 1
                    await asyncio.sleep(age)
        except asyncio.CancelledError:
            pass
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._raid_poller()

    async def _end_of_season_poller(self):
        try:
            while self.loop.is_running():
                end_of_season = get_season_end()
                now = datetime.utcnow()
                await asyncio.sleep((end_of_season - now).total_seconds())
                self.dispatch("new_season_start")
        except asyncio.CancelledError:
            pass
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._end_of_season_poller()

    async def _clan_games_poller(self):
        try:
            while self.loop.is_running():
                clan_games_start = get_clan_games_start()
                clan_games_end = get_clan_games_end()
                now = datetime.utcnow()
                if now < clan_games_start:
                    event = "clan_games_start"
                    mute_time = clan_games_start - now
                else:
                    event = "clan_games_end"
                    mute_time = clan_games_end - now
                await asyncio.sleep(mute_time.total_seconds())
                self.dispatch(event)
        except asyncio.CancelledError:
            pass
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._end_of_season_poller()

    async def _maintenance_poller(self):
        # pylint: disable=broad-except, protected-access
        maintenance_start = None
        try:
            while self.loop.is_running():
                try:
                    player = await self.get_player("#JY9J2Y99")
                    await asyncio.sleep(player._response_retry + 1)
                except Maintenance:
                    if maintenance_start is None:
                        self._in_maintenance_event.clear()
                        maintenance_start = datetime.utcnow()
                        self.dispatch("maintenance_start")

                    await asyncio.sleep(15)
                except Exception:
                    await asyncio.sleep(DEFAULT_SLEEP)
                else:
                    if maintenance_start is not None:
                        self._in_maintenance_event.set()
                        self.dispatch("maintenance_completion", maintenance_start)
                        maintenance_start = None

        except asyncio.CancelledError:
            pass
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            return await self._maintenance_poller()

    async def _war_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await asyncio.sleep(DEFAULT_SLEEP)
                await self._in_maintenance_event.wait()  # don't run if we're hitting maintenance errors.

                self.dispatch("war_loop_start", self.war_loops_run)

                if self.is_cwl_active and self.check_cwl_prep:
                    options = (WarRound.current_war, WarRound.current_preparation)
                else:
                    options = (WarRound.current_war, )

                tasks = [
                    self.loop.create_task(self._run_war_update(tag, option))
                    for tag in self._war_updates for option in options
                ]
                await asyncio.gather(*tasks)
                self.dispatch("war_loop_finish", self.war_loops_run)
                self.war_loops_run += 1

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)

            for lock in (v for k, v in self._locks.items() if "war" in k):
                self._safe_unlock(lock)

            return await self._war_updater()

    async def _clan_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await asyncio.sleep(DEFAULT_SLEEP)
                await self._in_maintenance_event.wait()  # don't run if we're hitting maintenance errors.

                self.dispatch("clan_loop_start", self.clan_loops_run)
                tasks = [
                    self.loop.create_task(self._run_clan_update(index, tag))
                    for index, tag in enumerate(self._clan_updates)
                ]
                await asyncio.gather(*tasks)
                self.dispatch("clan_loop_finish", self.clan_loops_run)
                self.clan_loops_run += 1

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)

            for lock in (v for k, v in self._locks.items() if "clan" in k):
                self._safe_unlock(lock)

            return await self._clan_updater()

    async def _player_updater(self):
        # pylint: disable=broad-except
        try:
            while self.loop.is_running():
                await asyncio.sleep(DEFAULT_SLEEP)
                await self._in_maintenance_event.wait()  # don't run if we're hitting maintenance errors.

                self.dispatch("player_loop_start", self.player_loops_run)
                tasks = [
                    self.loop.create_task(self._run_player_update(index, tag))
                    for index, tag in enumerate(self._player_updates)
                ]
                await asyncio.gather(*tasks)
                self.dispatch("player_loop_finish", self.player_loops_run)
                self.player_loops_run += 1

        except asyncio.CancelledError:
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)

            for lock in (v for k, v in self._locks.items() if "player" in k):
                self._safe_unlock(lock)

            return await self._player_updater()

    @staticmethod
    def _safe_unlock(lock):
        try:
            lock.release()
        except RuntimeError:
            pass

    async def _run_player_update(self, index, player_tag):
        # pylint: disable=protected-access, broad-except
        await asyncio.sleep(0.005 * index)

        key = "player:{}".format(player_tag)
        try:
            lock = self._locks[key]
        except KeyError:
            self._locks[key] = lock = asyncio.Lock()

        if lock.locked():
            # fast return to speed up events
            return
        await lock.acquire()

        try:
            player = await self.get_player(
                player_tag, cls=self.player_cls, load_game_data=True if self.load_game_data.always else False
            )
        except Maintenance:
            self._safe_unlock(lock)
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            self._safe_unlock(lock)
            return

        # sleep for either
        seconds = max(player._response_retry, self.player_retry_interval)
        self.loop.call_later(seconds, self._safe_unlock, lock)

        cached_player = self._get_cached_player(player_tag)
        self._update_player(player)

        if cached_player is None:
            self._safe_unlock(lock)
            return

        for listener in self._listeners["player"]:
            if listener.tags and player_tag not in listener.tags:
                continue
            await listener(cached_player, player)

    async def _run_clan_update(self, index, clan_tag):
        # pylint: disable=protected-access, broad-except
        await asyncio.sleep(0.005 * index)

        key = "clan:{}".format(clan_tag)
        try:
            lock = self._locks[key]
        except KeyError:
            self._locks[key] = lock = asyncio.Lock()

        if lock.locked():
            # fast return to speed up events
            return
        await lock.acquire()

        try:
            clan = await self.get_clan(clan_tag, cls=self.clan_cls)
        except Maintenance:
            self._safe_unlock(lock)
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            self._safe_unlock(lock)
            return

        # sleep for either the global retry or whenever a new player object is available, whichever is smaller.
        self.loop.call_later(max(clan._response_retry, self.clan_retry_interval), self._safe_unlock, lock)

        cached_clan = self._get_cached_clan(clan_tag)
        self._update_clan(clan)

        if not cached_clan:
            self._safe_unlock(lock)
            return

        for listener in self._listeners["clan"]:
            if listener.tags and clan_tag not in listener.tags:
                continue
            await listener(cached_clan, clan)

    async def _run_war_update(self, clan_tag, cwl_round=None):
        # pylint: disable=protected-access, broad-except
        key = "war:{}:{}".format(cwl_round, clan_tag)
        try:
            lock = self._locks[key]
        except KeyError:
            self._locks[key] = lock = asyncio.Lock()

        if lock.locked():
            # fast return to speed up events
            return
        await lock.acquire()

        if self.is_cwl_active:
            meth = self.get_current_war
        else:
            meth = self.get_clan_war

        try:
            war = await meth(clan_tag, cls=self.war_cls, round=cwl_round)
        except (Maintenance, PrivateWarLog):
            self._safe_unlock(lock)
            return
        except (Exception, BaseException) as exception:
            self.dispatch("event_error", exception)
            self._safe_unlock(lock)
            return

        if war is None:
            self._safe_unlock(lock)
            return

        # sleep for either the global retry or whenever a new war object is available, whichever is smaller.
        self.loop.call_later(max(war._response_retry, self.war_retry_interval), self._safe_unlock, lock)

        cached_war = self._get_cached_war(clan_tag)
        self._update_war(clan_tag, war)

        if not cached_war:
            self._safe_unlock(lock)
            return

        for listener in self._listeners["war"]:
            if listener.tags and clan_tag not in listener.tags:
                continue
            await listener(cached_war, war)
