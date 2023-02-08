# Enables circular import for type hinting
from __future__ import annotations

import json
from abc import abstractmethod
from datetime import datetime

import asyncpg


class BaseDBHandler:
    """Abstract class to inherit all database handler classes from
    """
    def __init__(self):
        self._params_loaded = False
        self.max_db_size = None

    @abstractmethod
    async def load_params(self):
        """Method to load parameters from the database
        """
        pass

    @abstractmethod
    async def set_params(self, *, max_db_size: int):
        """Method to set parameters and write them to the database so other handlers can read them.

        Args:
            max_db_size:
                :class:`int`: The maximum amount of raids that shall be stored in the database.
                This limits the growth of the database. The size of one raid depends on various
                factors, but should lie in the order of magnitude of a kilobyte.
                This should only be set through this function.
        """
        pass

    @abstractmethod
    async def _ensure_db_size(self) -> None:
        """Method to ensure the database does not surpass `self.max_db_size` by deleting the least significant entries.
        """
        pass

    @abstractmethod
    async def get_raid_log_entries(self, clan_tag: str, limit: int) -> list[dict[str: datetime, str: dict]]:
        """Method to fetch the latest `limit` raid log entries for a specific clan

        Args:
            clan_tag: :class:`str`: The tag of the clan to fetch raid log entries for
            limit: :class:`int`: The amount of raid log entries that shall be fetched

        Returns:
            A :class:`list` of :class:`dict`, each containing the end time and the data of one raid log entry

        """
        pass

    @abstractmethod
    async def get_raid_ended_at(self, clan_tag: str, end_time: datetime) -> dict:
        """Method to get one specific raid log entry

        Args:
            clan_tag: :class:`str`: The tag of the clan to fetch raid log entries for
            end_time: :class:`datetime`: The time the raid ended at

        Returns:
            Optional[:class:`dict`]: the data of the raid log entry

        """
        pass

    @abstractmethod
    async def write_raid_log_entry(self, clan_tag: str, end_time: datetime, data: dict) -> None:
        """Method to write a new raid log entry to the database. This is expected to ignore existing ones
        and ensure the max database size.

        Args:
            clan_tag: :class:`str`: The tag of the clan to fetch raid log entries for
            end_time: :class:`datetime`: The time the raid ended at
            data: :class:`dict`: The data for the raid log entry as returned from the API

        """
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
            await self.execute(query, "max_db_size", max_db_size)

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
        if not self._params_loaded:
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
