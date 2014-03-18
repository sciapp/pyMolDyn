

class ProhibitedError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)


def prohibited(f):
    raise ProhibitedError('Function call is prohibited.')
