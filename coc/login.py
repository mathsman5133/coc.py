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

from typing import Type, Union

from .client import Client
from .events import EventsClient


def login(
    email: str, password: str, client: Type[Union[Client, EventsClient]] = Client, **kwargs
) -> Union[Client, EventsClient]:
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
    instance.loop.run_until_complete(instance.login(email, password))
    return instance


def login_with_keys(*keys: str, client: Type[Union[Client, EventsClient]] = Client, **kwargs) -> Union[Client, EventsClient]:
    r"""Logs into the coc.py Client using premade keys from the developer site.

    Unlike :meth:`coc.login`, this login method **will not** automatically update and manage your keys, including when
    your IP address changes. It is recommended that you use the :meth:`coc.login` method.

    .. code-block:: python3

        client = coc.login_with_keys("eabfcd.adk.token1", "eacjuth.haetg.token2", throttle_limit=20)


    Parameters
    -----------
    *keys: str
        Keys or tokens as found from https://developer.clashofclans.com.
    client
        The type of coc.py client to use. This could either be a
        :class:`Client` or :class:`EventsClient`, depending on which you wish
        to use.
    **kwargs
        Any kwargs you wish to pass into the Client object.
    """
    instance = client(**kwargs)
    instance.login_with_keys(*keys)
    return instance
