""" Streply scope """

from contextlib import contextmanager
import sys

class scope:
    def __init__(self):
        self.flag = None
        self.url = None
        self.channel = None
        self.release = None
        self.environment = None
        self.global_scope = False

    def set_global_scope(self, is_global: bool):
        self.global_scope = is_global

    def set_flag(self, flag: str):
        self.flag = flag

    def set_url(self, url: str):
        self.url = url

    def set_channel(self, channel: str):
        self.channel = channel

    def set_release(self, release: str):
        self.release = release

    def set_environment(self, environment: str):
        self.environment = environment


@contextmanager
def configure_scope():
    _scope = scope()
    sys.streply.set_scope(_scope)
    yield _scope
