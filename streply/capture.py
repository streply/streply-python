import sys
from streply.enum.level import level

def exception(exception, params: object = {}, error_level: str = level.NORMAL):
    sys.streply.exception(exception, params, error_level)

def log(message: str, params: object = {}):
    sys.streply.log(message, params)

def error(message: str, params: object = {}, error_level: str = level.NORMAL):
    sys.streply.log(message, params, error_level)

def activity(message: str, params: object = {}):
    sys.streply.activity(message, params)

