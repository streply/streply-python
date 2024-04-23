""" Streply DSN """

from urllib.parse import urlparse


class dsn:
    def __init__(self, dsn: str):
        self._dsn = urlparse(dsn)

    def getScheme(self):
        return self._dsn.scheme

    def getServer(self):
        return self._dsn.hostname

    def getPort(self):
        if self._dsn.port is None:
            if self.getScheme() == 'https':
                return 443
            else:
                return 80

        return self._dsn.port

    def getPublicKey(self):
        return self._dsn.username

    def getProjectId(self):
        return int(self._dsn.path[1:])

    def getApiUrl(self):
        api_url = self.getScheme() + "://" + self.getServer()

        if self.getPort() != 443 and self.getPort() != 80:
            api_url += ":" + str(self.getPort())

        return api_url
