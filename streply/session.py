import uuid


def increaseTraceUniqueId():
    session.uniqueTraceId += 1


class session:
    uniqueTraceId = 0

    def __init__(self):
        self._traceId = uuid.uuid4().hex
        self._sessionId = uuid.uuid4().hex
        self._userId = uuid.uuid4().hex

    def traceId(self):
        return self._traceId

    def traceUniqueId(self):
        return self._traceId + '_' + str(self.uniqueTraceId)

    def sessionId(self):
        return self._sessionId

    def userId(self):
        return self._userId
