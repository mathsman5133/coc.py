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

