"""A Python SDK for Streply"""

import time
from streply.session import session

def microtime():
    return float(time.time())

__streply_version__ = '0.0.3'
__start_time__ = microtime()
__session__ = session()

from streply import *
from streply.debug import init_debug_support

init_debug_support()
del init_debug_support
