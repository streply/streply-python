""" Streply request """

import requests
import json

from streply.response import response
from streply.session import increaseTraceUniqueId


class request:
    def __init__(self, dsn, options):
        self._dsn = dsn
        self._options = options

    def send(self, event):
        data = event.toJson()
        headers = {
            "Content-Type": "application/json",
            'Token': self._dsn.getPublicKey(),
            'ProjectId': str(self._dsn.getProjectId()),
        }

        _response = requests.post(url=self._dsn.getApiUrl(), data=json.dumps(data), headers=headers)

        increaseTraceUniqueId()

        return response(_response)

