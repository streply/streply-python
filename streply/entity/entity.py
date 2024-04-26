""" Streply entity """

from streply import __streply_version__
from streply import __start_time__
from streply import __session__
from streply import microtime
from streply.enum.level import level
from streply.utils import parseParams
import platform
import datetime
import socket
import os
import sys


class entity:
    def __init__(self, dsn, options, user):
        self._dsn = dsn
        self._options = options
        self._type = 'log'
        self._message = None
        self._params = {}
        self._level = level.NORMAL
        self._user = user
        self._exception_name = None
        self._file = None
        self._line = None
        self._trace = {}

    def message(self, message: str):
        self._message = message

    def type(self, type: str):
        self._type = type

    def params(self, params: object):
        self._params = params

    def level(self, level: str):
        self._level = level

    def exceptionName(self, exception_name: str):
        self._exception_name = exception_name

    def file(self, file: str):
        self._file = file

    def line(self, line: int):
        self._line = line

    def trace(self, trace: object):
        self._trace = trace

    def toJson(self):
        if self._message is None:
            raise Exception('Message cannot be empty')

        _time = microtime()
        _loadTime = _time - __start_time__
        _scope = sys.streply.scope()
        _flag = None
        _url = None
        _channel = None
        _environment = self._options.environment()
        _release = self._options.release()

        if _scope is not None:
            _flag = _scope.flag
            _url = _scope.url
            _channel = _scope.channel

            if _scope.environment is not None:
                _environment = _scope.environment

            if _scope.release is not None:
                _release = _scope.release

            if not _scope.global_scope:
                sys.streply.set_scope(None)

        return {
            'eventType': 'event',
            'traceId': __session__.traceId(),
            'traceUniqueId': __session__.traceUniqueId(),
            'sessionId': __session__.sessionId(),
            'userId': __session__.userId(),
            'status': 0,
            'dateTimeZone': str(datetime.datetime.now().astimezone().tzname()),
            'date': str(datetime.datetime.now()),
            'startTime': __start_time__,
            'time': _time,
            'loadTime': _loadTime,
            'technology': 'python',
            'technologyVersion': platform.python_version(),
            'environment': _environment,
            'release': _release,
            'projectId': self._dsn.getProjectId(),
            'httpStatusCode': 200,
            'apiClientVersion': __streply_version__,
            'type': self._type,
            'level': self._level,
            'params': parseParams(self._params),
            'message': self._message,
            'requestUserAgent': socket.gethostname(),
            'requestParams': sys.argv,
            'dir': os.getcwd(),
            'user': self._user,
            'url': _url,
            'flag': _flag,
            'file': self._file,
            'line': self._line,
            'exceptionName': self._exception_name,
            'trace': self._trace,
            'channel': _channel,
        }
