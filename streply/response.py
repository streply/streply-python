""" Streply response """

import json


class response:
    def __init__(self, _response):
        is_success = True

        try:
            self._data = json.loads(_response.text)
        except ValueError as e:
            is_success = False

        if is_success:
            self._status_code = _response.status_code
            self._status = self._data['status']
        else:
            self._status_code = 500
            self._status = 'error'

    def statusCode(self):
        return self._status_code

    def isSuccess(self):
        if self._status == 'success':
            return True
        return False

    def getOutput(self):
        return self._data

