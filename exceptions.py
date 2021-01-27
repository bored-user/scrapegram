class InvalidUsernameError(Exception):
    def __init__(self):
        self.message = 'invalid username handle'
        super().__init__(self.message)

class PrivateAccountError(Exception):
    def __init__(self):
        self.message = 'account cannot be private'
        super().__init__(self.message)