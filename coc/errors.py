# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2019 mathsman5133

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


class ClashOfClansException(Exception):
    pass


class HTTPException(ClashOfClansException):
    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        try:
            self.reason = message.get('reason', '')
            self.message = message.get('message', '')

        except Exception:
            self.reason = 'Unknown'
            self.message = ''

        fmt = '{0.reason} (status code: {0.status})'
        if len(self.message):
            fmt = fmt + ' :{1}'

        super().__init__(fmt.format(self.response, self.message))


class Forbidden(HTTPException):
    pass


class NotFound(HTTPException):
    pass


class InvalidArguement(ClashOfClansException):
    pass


class InvalidToken(HTTPException):
    pass


class Maitenance(HTTPException):
    pass

