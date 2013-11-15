
class CustomError(Exception):
    def __init__(self, errortype, message, parenterror=None):
        self.errortype = errortype
        self.message = message
        if parenterror:
            template = "{0}:\n{1!r}"
            errmsg = template.format(type(parenterror).__name__, parenterror.args)
            self.upstack = errmsg
        else:
            self.upstack = ""

    def __str__(self):
        if self.upstack:
            return "%s: %s FROM %s" % (self.errortype, self.message, self.upstack)
        else:
            return self.errortype + ': ' + self.message

    def errortype(self):
        return self.errortype

    def message(self):
        return self.message

    def upstack(self):
        return self.upstack