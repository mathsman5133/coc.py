from abc import abstractmethod
from datetime import datetime

import asyncpg


class BaseDBHandler:
    def __init__(self, max_db_size: int):
        self.max_db_size = max_db_size

    @abstractmethod
    async def _ensure_db_size(self) -> None:
        pass

    @abstractmethod
    async def get_raid_log_entries(self, clan_tag: str, limit: int) -> list[dict[str: datetime, str: dict]]:
        pass

    @abstractmethod
    async def write_raid_log_entry(self, clan_tag: str, end_time: datetime, data: dict) -> None:
        pass


class PostgresHandler(BaseDBHandler):
    def __init__(self, max_db_size: int, conn: asyncpg.Connection):
        self._conn = conn
        super().__init__(max_db_size)

    async def _create_table(self):
        await self._conn.execute('CREATE TABLE CocPyRaidCache('
                                 'clan_tag VARCHAR(12), '
                                 'end_time TIMESTAMP, '
                                 'data JSONB, '
                                 'PRIMARY KEY(clan_tag, end_time)'
                                 ') ON CONFLICT DO NOTHING')

    async def _ensure_db_size(self) -> None:
        count = await self._conn.fetchrow('SELECT COUNT(*) FROM CocPyRaidCache')
        while count > self.max_db_size:
            deleted = await self._conn.execute('DELETE FROM CocPyRaidCache '
                                               'WHERE end_time = ('
                                               'SELECT MIN(end_time) FROM CocPyRaidCache)')
            count -= deleted

    async def get_raid_log_entries(self, clan_tag: str, limit: int) -> list[dict[str: datetime, str: dict]]:
        try:
            records = await self._conn.fetch('SELECT end_time, data FROM CocPyRaidCache '
                                             'WHERE clan_tag = $1 '
                                             'ORDER BY end_time DESC '
                                             'LIMIT $2',
                                             clan_tag, limit)
            return [{'end_time': record['end_time'], 'data': record['data']} for record in records]
        except asyncpg.UndefinedTableError:
            await self._create_table()
            return []

    async def write_raid_log_entry(self, clan_tag: str, end_time: datetime, data: dict) -> None:
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
