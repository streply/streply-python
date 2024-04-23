import logging
import sys
from logging import LogRecord
from streply.enum.level import level


class LogHandler(logging.Handler):
    def emit(self, record: LogRecord):
        file_name = record.filename
        line = record.lineno
        message = record.getMessage()
        log_level = record.levelname
        args = record.args
        event_type = 'log'
        event_level = level.NORMAL

        if log_level == 'DEBUG' or log_level == 'CRITICAL':
            event_type = 'error'

        if log_level == 'CRITICAL':
            event_level = level.CRITICAL

        sys.streply.capture(event_type, str(message), args, event_level, None, file_name, line)

