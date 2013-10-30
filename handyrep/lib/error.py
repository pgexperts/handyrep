
class CustomError(Exception):
    def __init__(self, errortype, message):
        self.errortype = errortype
        self.message = message

    def __str__(self):
        return self.errortype + ': ' + self.message

    def errortype(self):
        return self.errortype

    def message(self):
        return self.message