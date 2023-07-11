# Enables circular import for type hinting coc.Client
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Type, Union

from .raid import RaidLogEntry
from .wars import ClanWarLogEntry

if TYPE_CHECKING:
    from .client import Client


class LogPaginator(ABC):
    @abstractmethod
    def __init__(self, client: Client,
                 clan_tag: str,
                 limit: int,
                 page: bool,
                 json_resp: dict,
                 model: Union[Type[ClanWarLogEntry], Type[RaidLogEntry]]):

        self._clan_tag = clan_tag
        self._limit = limit
        self._page = page

        self._init_data = json_resp  # Initial data; this is const
        self._init_logs = json_resp.get("items", [])
        self._response_retry = json_resp.get("_response_retry", 0)
        self._client = client
        self._model = model

    def __len__(self) -> int:
        return len(self._init_logs)

    def __iter__(self):
        """Initialize the iter object and reset the iter index to 0"""
        self._sync_index = 0
        return self

    def __next__(self) -> Union[ClanWarLogEntry, RaidLogEntry]:
        """Fetch the next item in the iter object and return the entry"""
        if self._sync_index == len(self._init_logs):
            raise StopIteration
        ret = self._model(data=self._init_logs[self._sync_index],
                          client=self._client, response_retry=self._response_retry, clan_tag=self._clan_tag)
        self._sync_index += 1
        return ret

    def __getitem__(self, index: int) -> Union[ClanWarLogEntry, RaidLogEntry]:
        """Support indexing the object. This will not fetch any addition
        items from the endpoint"""
        try:
            return self._model(data=self._init_logs[index],
                               client=self._client, response_retry=self._response_retry, clan_tag=self._clan_tag)
        except Exception:
            raise

    def __aiter__(self):
        # These values are used to simulate the caller having a single list
        # of items. In reality, the list is populated on demand.
        self._max_index = len(self._init_logs)
        self._min_index = 0
        self._async_index = 0

        # Make copies of the init data since they will change.
        self._logs = self._init_logs[:]
        self._page_data = self._init_data.copy()
        return self

    async def __anext__(self) -> Union[ClanWarLogEntry, RaidLogEntry]:
        """
        This class supports async for loops. If the `page` bool is set to
        True then the async for loop will fetch all items from the endpoint
        until there are not more items in the endpoint. This is done without
        increasing the memory footprint by only caching `limit` number
        of logs at all times.

        When `limit` is set to 10, `self._logs` will only store 10 log items.
        When the last item in `self._logs` is reached when iterating,
        the array will be replaced by the next `limit` number of items. All
        this is abstracted from the user, they will just think they are
        iterating over the array. Keep in mind that if `limit` is set to 10
        and there are 200 total logs, then this API will make 20 get
        requests to the endpoint making it quite slow. Consider tuning
        this method with the `limit` value.
        """
        # If paging is not enabled, do not fetch  any more items only
        # iterate over the items in the self._war_logs
        if not self._page:
            if self._async_index == len(self._logs):
                raise StopAsyncIteration
            ret = self._model(data=self._logs[self._async_index],
                              client=self._client, response_retry=self._response_retry, clan_tag=self._clan_tag)
            self._async_index += 1
            return ret

        # If paging is enabled, update self._war_logs if the end of the
        # array is reached
        ret: Union[ClanWarLogEntry, RaidLogEntry]

        # If index request is within range of the war_logs, return item
        if self._min_index <= self._async_index < self._max_index:
            ret = self._logs[self._async_index - self._min_index]

        # Iteration has reached the end of the array, fetch the next
        # set of logs from the endpoint
        elif self._next_page:
            await self._paginate()
            self._min_index = self._max_index
            self._max_index = self._max_index + len(self._logs)
            ret = self._logs[self._async_index - self._min_index]
        else:
            raise StopAsyncIteration

        self._async_index += 1
        return self._model(data=ret, client=self._client, response_retry=self._response_retry, clan_tag=self._clan_tag)

    async def _paginate(self) -> None:
        """
        Request data from the endpoint and update the iter variables with
        the new data. `self._fetch_endpoint` is a child defined method.
        """
        self._page_data = await self._fetch_endpoint(self._client,
                                                     self._clan_tag,
                                                     **self.options)
        self._logs = self._page_data.get("items", [])
        self._response_retry = self._page_data.get("_response_retry", 0)

    @property
    def options(self) -> dict:
        """Generate the header for the endpint request"""
        options = {"limit": self._limit}
        if self._next_page:
            options["after"] = self._next_page
        return options

    @property
    def _next_page(self) -> Optional[str]:
        """Determine if there is a next page for the endpoint query"""
        try:
            return self._page_data.get("paging").get("cursors").get("after")
        except KeyError:
            return None

    @staticmethod
    @abstractmethod
    async def _fetch_endpoint(client: Client,
                              clan_tag: str,
                              fut: Optional[asyncio.Future] = None,
                              **options) -> dict:
        """Function to fetch data from the endpoint"""
        pass

    @classmethod
    @abstractmethod
    async def init_cls(cls,
                       client: Client,
                       clan_tag: str,
                       model: Type[ClanWarLogEntry],
                       limit: int,
                       paginate: bool = True,
                       ) -> Union[ClanWarLog, RaidLog]:
        """Class method to return an instantiated object"""
        pass


class ClanWarLog(LogPaginator, ABC):
    """Represents a Generator for a ClanWarLog"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    async def init_cls(cls,
                       client: Client,
                       clan_tag: str,
                       model: Type[ClanWarLogEntry],
                       limit: int,
                       page: bool = True,
                       after: str = None,
                       before: str = None
                       ) -> ClanWarLog:

        # Add the limit if specified
        args = {"limit": limit} if limit else {}
        if after:
            args["after"] = after
        if before:
            args["before"] = before

        json_resp = await cls._fetch_endpoint(client, clan_tag, **args)
        return ClanWarLog(client=client, clan_tag=clan_tag, limit=limit,
                          page=page, json_resp=json_resp, model=model)

    @staticmethod
    async def _fetch_endpoint(client: Client, clan_tag: str,
                              fut: Optional[asyncio.Future] = None,
                              **options) -> dict:
        result = await client.http.get_clan_war_log(clan_tag, **options, ignore_cache=True)
        if fut:
            fut.set_result(result)
        return result


class RaidLog(LogPaginator, ABC):
    """Represents a Generator for a RaidLog"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    async def init_cls(cls,
                       client: Client,
                       clan_tag: str,
                       model: Type[RaidLogEntry],
                       limit: int,
                       page: bool = True,
                       after: str = None,
                       before: str = None
                       ) -> RaidLog:

        # Add the limit if specified
        args = {"limit": limit} if limit else {}
        if after:
            args["after"] = after
        if before:
            args["before"] = before

        json_resp = await cls._fetch_endpoint(client, clan_tag, **args)
        return RaidLog(client=client, clan_tag=clan_tag, limit=limit,
                       page=page, json_resp=json_resp, model=model)

    @staticmethod
    async def _fetch_endpoint(client: Client, clan_tag: str,
                              fut: Optional[asyncio.Future] = None,
                              **options) -> dict:
        result = await client.http.get_clan_raid_log(clan_tag, **options)
        if fut:
            fut.set_result(result)
        return result
