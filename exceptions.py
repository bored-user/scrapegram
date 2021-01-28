class InvalidUsernameError(Exception):
    def __init__(self):
        self.message = 'invalid username handle'
        super().__init__(self.message)

class PrivateAccountError(Exception):
    def __init__(self):
        self.message = 'account cannot be private'
        super().__init__(self.message)

class MediaRetrievalError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
