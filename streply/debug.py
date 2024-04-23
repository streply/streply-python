import os
import sys
import logging
from streply.handler.log_handler import LogHandler
from streply.utils import logger
from streply.enum.level import level

def configure_logger():
    logger.addHandler(LogHandler())
    logger.setLevel(logging.DEBUG)

def except_handler(exception, message, trace_back):
    exception_name = exception.__name__
    file_name = os.path.split(trace_back.tb_frame.f_code.co_filename)[1]
    line = trace_back.tb_lineno

    sys.streply.capture('error', str(message), {}, level.NORMAL, exception_name, file_name, line, None, trace_back)


def configure_debugger():
    sys.excepthook = except_handler


def init_debug_support():
    if not logger.handlers:
        configure_logger()
    configure_debugger()

