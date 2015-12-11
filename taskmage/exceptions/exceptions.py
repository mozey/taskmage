class CommandNotFound(Exception):
    def __init__(self):
        self.message = "Command not found"

        super(CommandNotFound, self).__init__(self.message)

class CommandAmbiguous(Exception):
    def __init__(self):
        self.message = "Command abbreviation ambiguous"

        super(CommandAmbiguous, self).__init__(self.message)

class FilterInvalid(Exception):
    def __init__(self, arg):
        self.message = "Unsupported filter {}".format(arg)

        super(FilterInvalid, self).__init__(self.message)

class FilterRequired(Exception):
    def __init__(self, arg):
        self.message = "{} filter is required".format(arg)

        super(FilterRequired, self).__init__(self.message)

class ModNotFound(Exception):
    def __init__(self):
        self.message = "Mod not found"

        super(ModNotFound, self).__init__(self.message)

class ModAmbiguous(Exception):
    def __init__(self):
        self.message = "Mod abbreviation ambiguous"

        super(ModAmbiguous, self).__init__(self.message)

class NotImplemented(Exception):
    def __init__(self):
        self.message = "Not implemented"

        super(NotImplemented, self).__init__(self.message)

class TaskNotFound(Exception):
    def __init__(self):
        self.message = "Task not found"

        super(TaskNotFound, self).__init__(self.message)

class TaskNotStarted(Exception):
    def __init__(self):
        self.message = "Task not started"

        super(TaskNotStarted, self).__init__(self.message)


