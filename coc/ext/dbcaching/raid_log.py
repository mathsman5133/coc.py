# Enables circular import for type hinting coc.Client
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Type

from coc import Client, utils, Timestamp, RaidLogEntry
from coc.entry_logs import RaidLog
from coc.ext.dbcaching import BaseDBHandler


class CachedRaidLog(RaidLog):
    """Represents a Generator for a cached RaidLog"""

    def __init__(self, **kwargs):
        super().__init__(page=False, **kwargs)

    @classmethod
    async def init_cls(cls,
                       client: Client,
                       clan_tag: str,
                       model: Type[RaidLogEntry],
                       limit: int,
                       db_handler: BaseDBHandler = None,
                       ) -> CachedRaidLog:
        json_resp = await cls._fetch_database(client, clan_tag, limit, db_handler)
        return CachedRaidLog(client=client, clan_tag=clan_tag, limit=limit,
                             json_resp=json_resp, model=model)

    @classmethod
    async def _fetch_database(cls,
                              client: Client,
                              clan_tag: str,
                              limit: int,
                              db_handler: BaseDBHandler,
                              ) -> dict:
        """Class method to get cached raids from the database where possible and fetch the rest from the API"""
        # The limit will be zero if not specified and in that case we want all the entries
        raid_log_entries = await db_handler.get_raid_log_entries(clan_tag, limit if limit else db_handler.max_db_size)
        if raid_log_entries:
            # calculate how many newer raid logs there are that might be uncached
            limit_to_fetch = (utils.get_raid_weekend_end(datetime.utcnow() - timedelta(weeks=1))
                              - raid_log_entries[0]["end_time"]).days // 7
        else:  # nothing cached, so we need to request all the raid logs we want
            limit_to_fetch = limit
        if datetime.utcnow() > utils.get_raid_weekend_start():
            # there is a raid currently running, so we need to fetch it to get live data
            limit_to_fetch += 1
        if not limit or limit_to_fetch + len(raid_log_entries) < limit:
            # if we want more raids than there are stored plus the ones after that, just fetch them all
            args = {"limit": limit} if limit else {}
            json_resp = await cls._fetch_endpoint(client, clan_tag, **args)
        else:
            if limit_to_fetch:  # request the raids after the latest cached one
                args = {"limit": limit_to_fetch}
                json_resp = await cls._fetch_endpoint(client, clan_tag, **args)
            else:  # everything is cached, no need to make an API call
                json_resp = {}
        items = json_resp.get("items", [])
        # store finished raids in db
        for item in items:
            if item["state"] == "ended":
                await db_handler.write_raid_log_entry(clan_tag, Timestamp(data=item["endTime"]).time, item)
        for entry in raid_log_entries:
            items.append(entry["data"])
        # If not specified, the limit will be 0, so we don't want to slice the items in that case
        items = items[:limit] if limit else items
        json_resp["items"] = items
        return json_resp
