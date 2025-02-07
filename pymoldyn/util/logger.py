import inspect
import os
from datetime import datetime

__all__ = ["Logger"]


class Logger(object):

    EMERG = 0
    ALERT = 1
    CRIT = 2
    ERR = 3
    ERROR = 3
    WARNING = 4
    WARN = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7

    severities = [
        "Emergency",
        "Alert",
        "Critical",
        "Error",
        "Warning",
        "Notice",
        "Informational",
        "Debug",
    ]

    def __init__(self, identifier):
        self.identifier = identifier
        self.streams = dict()
        self.format = "{time} {severity} from {identifier} in {function} ({file}:{line}): "
        self.logs = []

    def setstream(self, ident, stream, severity):
        if severity is None or stream == -1:
            if ident in self.streams:
                del self.streams[ident]
        else:
            self.streams[ident] = (stream, severity)

    def log(self, severtiy, message, tag=None):
        self._log(severtiy, message, tag)

    def emerg(self, message):
        self._log(self.EMERG, message)

    def alert(self, message):
        self._log(self.ALERT, message)

    def crit(self, message):
        self._log(self.CRIT, message)

    def err(self, message):
        self._log(self.ERR, message)

    def error(self, message):
        self._log(self.ERR, message)

    def warn(self, message):
        self._log(self.WARN, message)

    def notice(self, message):
        self._log(self.NOTICE, message)

    def info(self, message):
        self._log(self.INFO, message)

    def debug(self, message):
        self._log(self.DEBUG, message)

    def _log(self, severity, message, tag=None):
        st = inspect.stack()
        info = {
            "identifier": self.identifier,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "severity": self.severities[severity].upper(),
            "function": st[2][3],
            "file": os.path.relpath(st[2][1]),
            "line": st[2][2],
        }
        line = self.format.format(**info) + message
        self._logline(severity, line)
        if tag is not None:
            self.logs.append(tag)

    def _logline(self, severity, line):
        for stream, maxseverity in self.streams.values():
            if severity <= maxseverity:
                if isinstance(stream, Logger):
                    stream._logline(severity, line)
                else:
                    print(line, file=stream)
