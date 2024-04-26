import sys
from streply.enum.level import level

def exception(exception, params: object = {}, error_level: str = level.NORMAL):
    return sys.streply.exception(exception, params, error_level)

def log(message: str, params: object = {}):
    return sys.streply.log(message, params)

def error(message: str, params: object = {}, error_level: str = level.NORMAL):
    return sys.streply.log(message, params, error_level)

def activity(message: str, params: object = {}):
    return sys.streply.activity(message, params)
