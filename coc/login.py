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

import typing

from .async_client import AsyncClient
from .sync_client import SyncClient
from .events import EventsClient


def login(
    email: str, password: str, client: typing.Type[typing.Union[AsyncClient, EventsClient, SyncClient]] = AsyncClient, **kwargs
) -> typing.Union[AsyncClient, EventsClient, SyncClient]:
    r"""Eases logging into the coc.py Client.

    This function makes logging into the client easy, returning the created client.

    Parameters
    -----------
    email : str
        Your password email from https://developer.clashofclans.com
        This is used when updating keys automatically if your IP changes
    password : str
        Your password login from https://developer.clashofclans.com
        This is used when updating keys automatically if your IP changes
    client
        The type of coc.py client to use. This could either be a
        :class:`Client` or :class:`EventsClient`, depending on which you wish
        to use.
    **kwargs
        Any kwargs you wish to pass into the Client object.
    """
    instance = client(**kwargs)
    if isinstance(instance, AsyncClient):
        instance.loop.run_until_complete(instance.login(email, password))
    else:
        instance.login(email, password)

    return instance


login_with_email = login


def login_with_keys(
        *keys: typing.List[str], client: typing.Type[typing.Union[AsyncClient, EventsClient, SyncClient]] = AsyncClient, **kwargs
) -> typing.Union[AsyncClient, EventsClient, SyncClient]:
    instance = client(**kwargs)
    instance.login_with_keys(keys)
    return instance
