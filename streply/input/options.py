""" Streply Options """

class options:
    def __init__(self, _options: object):
        self._options = _options

    def set(self, name: str, value):
        self._options[name] = value

    def get(self, name: str):
        return self._options.get(name)

    def environment(self):
        return self.get('environment')

    def release(self):
        return self.get('release')
