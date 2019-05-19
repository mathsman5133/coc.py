import asyncio
import logging
import traceback

from itertools import chain
from collections import Iterable

from coc.utils import get
from coc.errors import Forbidden, HTTPException, ClashOfClansException
from coc.client import Client
from coc.cache import Cache
from coc.nest_asyncio import apply

cache_search_clans = Cache()
cache_war_clans = Cache()

cache_search_players = Cache()
cache_war_players = Cache()

cache_current_wars = Cache()
cache_war_logs = Cache()

cache_league_groups = Cache()
cache_league_wars = Cache()

cache_locations = Cache()

cache_leagues = Cache()
cache_seasons = Cache()

log = logging.getLogger(__name__)


def login(email, password, **kwargs):
    client = EventsClient(**kwargs)
    client.loop.run_until_complete(client.login(email, password))
    return client


class EventsClient(Client):
    def __init__(self, **options):
        super().__init__(**options)

        self.loop.set_debug(enabled=True)
        apply(self.loop)

        self._clan_updates = None
        self._player_updates = None
        self._war_updates = None

        self._active_state_tasks = {}

        self._clan_retry_interval = 600
        self._player_retry_interval = 600
        self._war_retry_interval = 600

        self.extra_events = {}

        self.updater_tasks = {}
        self.ran = 0

    def dispatch(self, event_name: str, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            asyncio.ensure_future(self._run_event(ev, event, *args, **kwargs), loop=self.loop)

    def event(self, fctn, name=None):
        if not asyncio.iscoroutinefunction(fctn):
            raise TypeError('event must be a coroutine function')

        name = name or fctn.__name__

        if name in self.extra_events:
            self.extra_events[name].append(fctn)
        else:
            self.extra_events[name] = [fctn]

        return fctn

    async def _run_event(self, event_name, coro, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_event_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    async def on_event_error(self, event_name, *args, **kwargs):
        print('Ignoring exception in {}'.format(event_name))
        traceback.print_exc()

    async def add_clan_update(self, tags: Iterable, *, member_updates=False, retry_interval=600):
        if not self._clan_updates:
            self._clan_updates = tags
        else:
            self._clan_updates = chain(self._clan_updates, tags)

        if member_updates:
            async for clan in self.get_clans(tags):
                await self.add_player_update((n.tag for n in clan._members), retry_interval=retry_interval)
            self._player_retry_interval = retry_interval

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._clan_retry_interval = retry_interval

    async def add_war_update(self, tags: Iterable, *, retry_interval=600):
        if not self._war_updates:
            self._war_updates = tags
        else:
            self._war_updates = chain(self._war_updates, tags)

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._war_retry_interval = retry_interval

    async def add_player_update(self, tags: Iterable, retry_interval=600):
        if not self._player_updates:
            self._player_updates = tags
        else:
            self._player_updates = chain(self._player_updates, tags)

        if retry_interval < 0:
            raise ValueError('retry_interval must be greater than 0 seconds')

        self._player_retry_interval = retry_interval

    async def start_updates(self):
        if not self.updater_tasks.get('war'):
            self.updater_tasks['war'] = self.loop.create_task(self._war_updater())
        else:
            self.updater_tasks['war'].cancel()
            self.updater_tasks['war'] = self.loop.create_task(self._war_updater())

        if not self.updater_tasks.get('clan'):
            self.updater_tasks['clan'] = self.loop.create_task(self._clan_updater())
        else:
            self.updater_tasks['clan'].cancel()
            self.updater_tasks['clan'] = self.loop.create_task(self._clan_updater())

        if not self.updater_tasks.get('player'):
            self.updater_tasks['player'] = self.loop.create_task(self._player_updater())
        else:
            self.updater_tasks['player'].cancel()
            self.updater_tasks['player'] = self.loop.create_task(self._player_updater())

    async def _war_updater(self):
        try:
            while self.loop.is_running():
                self.ran += 1
                await self._update_wars()
                await asyncio.sleep(self._war_retry_interval)
        except (
            OSError,
            asyncio.CancelledError,
            HTTPException,
            ClashOfClansException
        ):

            self.dispatch('event_error')
            return await self._war_updater()

    async def _clan_updater(self):
        try:
            while self.loop.is_running():
                self.ran += 1
                await self._update_clans()
                await asyncio.sleep(self._player_retry_interval)
        except (
            OSError,
            asyncio.CancelledError,
            HTTPException,
            ClashOfClansException
        ):
            self.dispatch('event_error')
            return await self._clan_updater()

    async def _player_updater(self):
        try:
            while self.loop.is_running():
                self.ran += 1
                await self._update_players()
                await asyncio.sleep(self._clan_retry_interval)
        except (
            OSError,
            asyncio.CancelledError,
            HTTPException,
            ClashOfClansException
        ):
            self.dispatch('event_error')
            return await self._player_updater()

    async def _check_member_count(self, cached_clan, new_clan):
        differences = [n for n in new_clan._members if n not in set(n.tag for n in cached_clan._members)]

        for tag in differences:
            new_member = get(new_clan._members, tag=tag)
            if new_member:
                self.dispatch('clan_member_join', new_member)
                continue

            member_left = get(cached_clan._members, tag=tag)
            if member_left:
                self.dispatch('clan_member_leave', member_left)
                continue

        return

    async def _update_clans(self):
        if not self._clan_updates:
            return

        async for clan in self.get_clans(self._clan_updates, update_cache=False):
            cached_clan = cache_search_clans.get(clan.tag)
            if not cached_clan:
                cache_search_clans.add(clan.tag, clan)
                continue

            if clan == cached_clan:
                log.warning('first equality')
                cache_search_clans.add(clan.tag, clan)
                continue

            self.dispatch('clan_update', cached_clan, clan)

            if clan.member_count != cached_clan:
                await self._check_member_count(cached_clan, clan)
                cached_clan._data['memberCount'] = clan.member_count  # hack for next line

            if clan._data == cached_clan._data:
                cache_search_clans.add(clan.tag, clan)
                continue

            self.dispatch('clan_settings_update', cached_clan, clan)
            cache_search_clans.add(clan.tag, clan)

    async def _wait_for_state_change(self, state_to_wait_for, war):
        if state_to_wait_for == 'inWar':
            to_sleep = war.start_time.seconds_until
        elif state_to_wait_for == 'warEnded':
            to_sleep = war.end_time.seconds_until
        else:
            return

        await asyncio.sleep(to_sleep)

        try:
            war = await self.get_current_war(war.clan_tag)
        except Forbidden:
            return

        if war.state == state_to_wait_for:
            self.dispatch('war_state_change', state_to_wait_for, war)
            return

        return await self._wait_for_state_change(state_to_wait_for, war)

    def _check_state_task_status(self, clan_tag):
        try:
            states = self._active_state_tasks[clan_tag]
        except KeyError:
            return

        return states.get('inWar'), states.get('warEnded')

    def _add_state_task(self, clan_tag, state, task):
        self._active_state_tasks[clan_tag][state] = task

    def _create_status_tasks(self, cached_war, war):
        if war.state == cached_war.state:
            return

        if war.state not in ['preparation', 'inWar', 'warEnded']:
            return

        in_war_task, war_ended_task = self._check_state_task_status(war.clan_tag)

        if not in_war_task or (war.start_time.time != cached_war.start_time.time):
            task = self.loop.create_task(self._wait_for_state_change('inWar', war))
            self._add_state_task(war.clan_tag, 'inWar', task)

        if not war_ended_task or (war.end_time.time != cached_war.end_time.time):
            task = self.loop.create_task(self._wait_for_state_change('inWar', war))
            self._add_state_task(war.clan_tag, 'warEnded', task)

    async def _update_wars(self):
        if not self._war_updates:
            return

        async for war in self.get_current_wars(self._war_updates, update_cache=False):
            cached_war = cache_current_wars.get(war.clan_tag)
            if not cached_war:
                cache_current_wars.add(war.clan_tag, war)
                continue

            if war == cached_war:
                cache_current_wars.add(war.clan_tag, war)
                continue

            self.dispatch('war_update', cached_war, war)

            await self._create_status_tasks(cached_war, war)

            if len(war._attacks) != len(cached_war._attacks):
                new_attacks = [n for n in war._attacks if n not in set(cached_war._attacks)]
                for attack in new_attacks:
                    self.dispatch('war_attack', attack)

            cache_current_wars.add(war.clan_tag, war)

    async def _update_players(self):
        if not self._player_updates:
            return

        async for player in self.get_players(self._player_updates, update_cache=False):
            cached_player = cache_search_players.get(player.tag)
            self.dispatch('player_update', cached_player, player)

            if not cached_player:
                cache_search_players.add(player.tag, player)
                continue

            if player == cached_player:
                continue

            if player.name != cached_player.name:
                self.dispatch('player_name_change', cached_player.name, player.name, player)
                cached_player._data['name'] = player.name

            if player.town_hall != cached_player.town_hall:
                self.dispatch('player_townhall_upgrade', cached_player.town_hall, player.town_hall, player)
                cached_player._data['townHallLevel'] = player.town_hall

            if player.builder_hall != cached_player.builder_hall:
                self.dispatch('player_builderhall_upgrade',
                                     cached_player.builder_hall, player.builder_hall, player)
                cached_player._data['builderHallLevel'] = player.town_hall

            if player == cached_player:
                cache_search_players.add(player.tag, player)
                continue

            achievement_updates = [n for n in player._achievements if n not in set(cached_player._achievements)]
            troop_upgrades = [n for n in player.troops if n not in set(cached_player.troops)]
            spell_upgrades = [n for n in player.spells if n not in set(cached_player.spells)]
            hero_upgrades = [n for n in player.heroes if n not in set(cached_player.heroes)]

            for achievement in achievement_updates:
                old_achievement = get(cached_player._achievements, name=achievement.name)
                self.dispatch('player_achievement_update', old_achievement, achievement)
                cached_player._data['achievements'][achievement.name] = achievement._data

            for troop in troop_upgrades:
                old_troop = get(cached_player.troops, name=troop.name)
                self.dispatch('player_achievement_update', old_troop, troop)
                cached_player._data['troops'][troop.name] = troop._data

            for spell in spell_upgrades:
                old_spell = get(cached_player.spells, name=spell.name)
                self.dispatch('player_achievement_update', old_spell, spell)
                cached_player._data['spells'][spell.name] = spell._data

            for hero in hero_upgrades:
                old_hero = get(cached_player.heroes, name=hero.name)
                self.dispatch('player_achievement_update', old_hero, hero)
                cached_player._data['heroes'][hero.name] = hero._data

            if cached_player == player:
                cache_search_players.add(player.tag, player)
                continue

            self.dispatch('player_other_update', cached_player, player)
