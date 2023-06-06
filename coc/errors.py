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
from aiohttp import ClientResponse


class ClashOfClansException(Exception):
    """Base exception for coc.py
    """


class HTTPException(ClashOfClansException):
    """Base exception for when a HTTP request fails

    Attributes
    ----------
    response:
        :class:`aiohttp.ClientResponse` - The response of the failed HTTP request.

    status:
        :class:`int` - The status code of the HTTP request

    reason:
        :class:`str` - The reason provided by the API.
            This could be an empty string if nothing was given.

    message:
        :class:`str` - The more detailed message provided by the API.
            This could be an empty string if nothing was given

    """

    __slots__ = ("response", "status", "message", "reason", "_data")

    def _from_response(self, response, data):
        if isinstance(response, int):
            self.status = response
            self.response = None
        elif isinstance(response, ClientResponse):
            self.response = response
            self.status = response.status
        else:
            self.response = self.status = None

        if isinstance(data, dict):
            self.reason = data.get("reason", "Unknown")
            self.message = data.get("message")
        elif isinstance(data, str):
            self.reason = data
            self.message = None
        else:
            self.reason = "Unknown"
            self.message = None

        fmt = "{0.reason} (status code: {0.status})"
        if self.message:
            fmt += ": {0.message}"

        super().__init__(fmt.format(self))

    def __init__(self, response=None, data=None):
        if isinstance(response, (ClientResponse, int)):
            self._from_response(response, data)
        else:
            self.response = None
            self.status = 0
            self.reason = None
            self.message = response

            fmt = "Error Occurred: {0}"
            super().__init__(fmt.format(self.message))


class InvalidArgument(HTTPException):
    """
    Thrown when an error status 400 occurs.

    Client provided incorrect parameters for the request.

    Subclass of :exc:`HTTPException`
    """


class InvalidCredentials(HTTPException):
    """Thrown when an error status 403 occurs and the reason is invalid credentials.

    Special Exception thrown when missing/incorrect credentials
    were passed. This is when your email/password pair is incorrect.
    Subclass of :exc:`HTTPException`
    """
    def __init__(self, response="Invalid Credentials"):
        super().__init__(response=response)


class Forbidden(HTTPException):
    """Thrown when an error status 403 occurs.

    API token does not grant access to the requested resource.

    Subclass of :exc:`HTTPException`"""


class PrivateWarLog(Forbidden):
    """Thrown when an error status 403 occurs when trying to get a clan's war info.

    This is a special subclass of :exc:`Forbidden` for when a clan's war log is private.
    """


class NotFound(HTTPException):
    """Thrown when an error status 404 occurs.

    The resource was not found.

    Subclass of :exc:`HTTPException`
    """


class Maintenance(HTTPException):
    """Thrown when an error status 503 occurs.

    Service is temporarily unavailable because of maintenance.

    Subclass of :exc:`HTTPException`
    """


class GatewayError(HTTPException):
    """Thrown when a gateway error occurs. These are either status 502 or 504

    Error code 502: Bad Gateway
    Error code 504: The Gateway has timed-out.

    Subclass of :exc:`HTTPException`
    """
