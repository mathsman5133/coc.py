from typing import Type

from coc import Client, RaidLogEntry, Forbidden, PrivateWarLog
from coc.ext.dbcaching import CachedRaidLog, BaseDBHandler
from coc.utils import correct_tag


async def get_raidlog(
        client: Client,
        clan_tag: str,
        cls: Type[RaidLogEntry] = RaidLogEntry,
        handler: BaseDBHandler = None,
        limit: int = 0,
) -> CachedRaidLog:
    """
    Retrieve cached raid logs from a database where possible and fetch them from the API
    otherwise.


    Parameters
    -----------
    client:
        class:`Client` to use to fetch missing raid logs from the API

    cls:
        Target class to use to model that data returned

    clan_tag:
        class:`str`: The clan tag to search for.

    handler:
        Subclass of class:`BaseDBHandler`: Handler to use for database interactions.
        The default of `None` results in the class:`SQLiteHandler` being used. If you
        want to use a different database, choose another handler or make your own by subclassing
        class:`BaseDBHandler`.

    limit:
        class:`int`: Number of logs to retrieve

    Raises
    ------
    TypeError
        The ``cls`` parameter must be a subclass of :class:`RaidLogEntry`.

    NotFound
        No clan was found with the supplied tag.

    PrivateWarLog
        The clan's warlog is private.

    Maintenance
        The API is currently in maintenance.

    GatewayError
        The API hit an unexpected gateway exception.


    Returns
    --------
    :class:`CachedRaidLog`:
        Entries in the capital raid seasons of the requested clan.
    """

    if limit < 0:
        raise ValueError("Limit cannot be negative")

    if not issubclass(cls, RaidLogEntry):
        raise TypeError("cls must be a subclass of RaidLogEntry.")

    if client.correct_tags:
        clan_tag = correct_tag(clan_tag)

    try:
        return await CachedRaidLog.init_cls(client=client,
                                            clan_tag=clan_tag,
                                            limit=limit,
                                            db_handler=handler,
                                            model=cls)
    except Forbidden as exception:
        raise PrivateWarLog(exception.response,
                            exception.reason) from exception
