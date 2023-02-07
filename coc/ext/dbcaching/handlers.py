# Enables circular import for type hinting coc.Client
from __future__ import annotations

import json
from abc import abstractmethod
from datetime import datetime

import asyncpg


class BaseDBHandler:
    def __init__(self):
        self._params_loaded = False
        self.max_db_size = 100000

    @abstractmethod
    async def load_params(self):
        pass

    @abstractmethod
    async def set_params(self, *, max_db_size: int):
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


class PostgresHandler(BaseDBHandler, asyncpg.Connection):
    def __init__(self, protocol, transport, loop, addr, config, params):
        BaseDBHandler.__init__(self)
        asyncpg.Connection.__init__(self, protocol, transport, loop, addr, config, params)

    async def load_params(self):
        try:
            records = await self.fetch("SELECT name, value FROM CocPyHandlerParameters")
            params = {record["name"]: record["value"] for record in records}
            self.max_db_size = params.get("max_db_size", None) or self.max_db_size
        except asyncpg.UndefinedTableError:
            await self._create_tables()
        self._params_loaded = True

    async def set_params(self, *, max_db_size: int):
        self.max_db_size = max_db_size
        query = "INSERT INTO CocPyHandlerParameters(name, value) " \
                "VALUES ($1, $2) " \
                "ON CONFLICT (name) " \
                "DO UPDATE SET value = $2 " \
                "WHERE CocPyHandlerParameters.name = $1"
        try:
            await self.execute(query, "max_db_size", max_db_size)
        except asyncpg.UndefinedTableError:
            await self._create_tables()
            await self.execute(query, max_db_size)

    async def _create_tables(self):
        await self.execute("CREATE TABLE IF NOT EXISTS CocPyHandlerParameters("
                           "name VARCHAR(20) PRIMARY KEY, "
                           "value INTEGER NOT NULL"
                           ")")
        await self.execute("CREATE TABLE IF NOT EXISTS CocPyRaidCache("
                           "clan_tag VARCHAR(12), "
                           "end_time TIMESTAMP, "
                           "data JSONB, "
                           "PRIMARY KEY(clan_tag, end_time)"
                           ")")

    async def _ensure_db_size(self) -> None:
        await self.load_params()
        [count] = await self.fetchrow("SELECT COUNT(*) FROM CocPyRaidCache")
        while count > self.max_db_size:
            deleted = await self.execute("DELETE FROM CocPyRaidCache "
                                         "WHERE end_time = ("
                                         "SELECT MIN(end_time) FROM CocPyRaidCache)")
            count -= int("".join([char for char in deleted if char.isdigit()]))

    async def get_raid_log_entries(self, clan_tag: str, limit: int) -> list[dict[str: datetime, str: dict]]:
        try:
            records = await self.fetch("SELECT end_time, data FROM CocPyRaidCache "
                                       "WHERE clan_tag = $1 "
                                       "ORDER BY end_time DESC "
                                       "LIMIT $2",
                                       clan_tag, limit)
            return [{"end_time": record["end_time"], "data": json.loads(record["data"])} for record in records]
        except asyncpg.UndefinedTableError:
            await self._create_tables()
            return []

    async def get_raid_ended_at(self, clan_tag: str, end_time: datetime) -> dict:
        try:
            [data] = await self.fetchrow("SELECT data FROM CocPyRaidCache "
                                         "WHERE clan_tag = $1 "
                                         "AND end_time = $2",
                                         clan_tag, end_time)
            return data
        except asyncpg.UndefinedTableError:
            await self._create_tables()

    async def write_raid_log_entry(self, clan_tag: str, end_time: datetime, data: dict) -> None:
        data = json.dumps(data)
        try:
            await self.execute("INSERT INTO CocPyRaidCache(clan_tag, end_time, data) "
                               "VALUES($1, $2, $3) "
                               "ON CONFLICT DO NOTHING",
                               clan_tag, end_time, data)
            await self._ensure_db_size()
        except asyncpg.UndefinedTableError:
            await self._create_tables()
            await self.execute("INSERT INTO CocPyRaidCache(clan_tag, end_time, data) "
                               "VALUES($1, $2, $3) "
                               "ON CONFLICT DO NOTHING",
                               clan_tag, end_time, data)
            await self._ensure_db_size()
