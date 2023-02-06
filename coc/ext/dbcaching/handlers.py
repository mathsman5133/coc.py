# Enables circular import for type hinting coc.Client
from __future__ import annotations

import json
from abc import abstractmethod
from datetime import datetime

import asyncpg


class BaseDBHandler:
    def __init__(self, *, max_db_size: int):
        self.max_db_size = max_db_size

    @abstractmethod
    async def __aenter__(self) -> BaseDBHandler:
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def _ensure_db_size(self) -> None:
        pass

    @abstractmethod
    async def get_raid_log_entries(self, clan_tag: str, limit: int) -> list[dict[str: datetime, str: dict]]:
        pass

    @abstractmethod
    async def get_raid_ended_at(self, clan_tag: str, end_time: datetime) -> dict:
        pass

    @abstractmethod
    async def write_raid_log_entry(self, clan_tag: str, end_time: datetime, data: dict) -> None:
        pass


class PostgresHandler(BaseDBHandler):
    def __init__(self, *, max_db_size: int, pool: asyncpg.Pool):
        self._pool = pool
        self._conn = None
        super().__init__(max_db_size=max_db_size)

    async def __aenter__(self) -> PostgresHandler:
        self._conn = await self._pool.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._conn.close()

    async def _create_table(self):
        await self._conn.execute('CREATE TABLE IF NOT EXISTS CocPyRaidCache('
                                 'clan_tag VARCHAR(12), '
                                 'end_time TIMESTAMP, '
                                 'data JSONB, '
                                 'PRIMARY KEY(clan_tag, end_time)'
                                 ')')

    async def _ensure_db_size(self) -> None:
        [count] = await self._conn.fetchrow('SELECT COUNT(*) FROM CocPyRaidCache')
        while count > self.max_db_size:
            deleted = await self._conn.execute('DELETE FROM CocPyRaidCache '
                                               'WHERE end_time = ('
                                               'SELECT MIN(end_time) FROM CocPyRaidCache)')
            count -= int(''.join([char for char in deleted if char.isdigit()]))

    async def get_raid_log_entries(self, clan_tag: str, limit: int) -> list[dict[str: datetime, str: dict]]:
        try:
            records = await self._conn.fetch('SELECT end_time, data FROM CocPyRaidCache '
                                             'WHERE clan_tag = $1 '
                                             'ORDER BY end_time DESC '
                                             'LIMIT $2',
                                             clan_tag, limit)
            return [{'end_time': record['end_time'], 'data': json.loads(record['data'])} for record in records]
        except asyncpg.UndefinedTableError:
            await self._create_table()
            return []

    async def get_raid_ended_at(self, clan_tag: str, end_time: datetime) -> dict:
        try:
            [data] = await self._conn.fetchrow('SELECT data FROM CocPyRaidCache '
                                               'WHERE clan_tag = $1 '
                                               'AND end_time = $2',
                                               clan_tag, end_time)
            return data
        except asyncpg.UndefinedTableError:
            await self._create_table()

    async def write_raid_log_entry(self, clan_tag: str, end_time: datetime, data: dict) -> None:
        data = json.dumps(data)
        try:
            await self._conn.execute('INSERT INTO CocPyRaidCache(clan_tag, end_time, data) '
                                     'VALUES($1, $2, $3) '
                                     'ON CONFLICT DO NOTHING',
                                     clan_tag, end_time, data)
            await self._ensure_db_size()
        except asyncpg.UndefinedTableError:
            await self._create_table()
            await self._conn.execute('INSERT INTO CocPyRaidCache(clan_tag, end_time, data) '
                                     'VALUES($1, $2, $3) '
                                     'ON CONFLICT DO NOTHING',
                                     clan_tag, end_time, data)
            await self._ensure_db_size()
