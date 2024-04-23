""" Streply SDK """

import sys
import os
import traceback
from streply.request import request
from streply.input.dsn import dsn
from streply.input.options import options
from streply.enum.level import level
from streply.entity.entity import entity
from streply.trace import trace
from streply.utils import parseParams


class streply:
    def __init__(self, _dsn: str, _options: object):
        self._dsn = dsn(_dsn)
        self._options = options(_options)
        self._request = request(self._dsn, self._options)
        self._user = None
        sys.streply = self

    def set_option(self, name: str, value):
        self._options.set(name, value)

    def set_user(self, user_id: str, user_name: str = None, params: object = {}):
        if user_name is None:
            user_name = user_id
        self._user = {'userId': user_id, 'userName': user_name, 'params': parseParams(params)}

    def capture(self, type: str, message: str, params: object = {}, error_level: str = level.NORMAL,
                exception_name: str = None, file: str = None, line: int = None, function_name: str = None,
                exception_trace=None):
        event = entity(self._dsn, self._options, self._user)
        _trace = trace()

        event.type(type)
        event.params(params)
        event.level(error_level)
        event.message(message)
        event.exceptionName(exception_name)
        event.file(file)
        event.line(line)

        _trace.load(exception_trace)

        if len(_trace.toArray()) == 0:
            if file is not None and line is not None:
                _trace.add(file, line, function_name, None, 10)

        event.trace(_trace.toArray())

        return self._request.send(event)

    def log(self, message: str, params: object = {}):
        return self.capture('log', message, params)

    def error(self, message: str, params: object = {}, error_level: str = level.NORMAL):
        return self.capture('error', message, params, error_level)

    def activity(self, message: str, params: object = {}):
        return self.capture('activity', message, params)

    def exception(self, exception, params: object = {}, error_level: str = level.NORMAL):
        exception_code, exc_obj, exc_trace_back = sys.exc_info()
        exception_name = type(exception).__name__
        file_name = os.path.split(exc_trace_back.tb_frame.f_code.co_filename)[1]
        line = exc_trace_back.tb_lineno
        message = exception
        function_name = traceback.extract_tb(exc_trace_back, 1)[0][2]

        return self.capture('error', str(message), params, error_level,
                            exception_name, file_name, line, function_name, exc_trace_back)
