import uuid
import datetime
import platform
import sys
import os
import time
from typing import Dict, Any


class Event:
    def __init__(self, client, type='log', message='', level='normal', exception_name=None, params=None):
        self.client = client
        self.type = type
        self.message = message
        self.level = level
        self.exception_name = exception_name
        self.params = params or {}
        self.trace = []
        self.file = None
        self.line = None

        self.trace_unique_id = f'{client.trace_id}_{client.trace_counter}'

        self.time = datetime.datetime.now()
        self.start_time = client.start_time
        self.load_time = time.time() - client.start_time

        self.context_data = {}

    def add_trace(self, trace):
        self.trace = trace

    def set_file_line(self, file, line):
        self.file = file
        self.line = line

    def update_from_context(self, context):
        self.context_data = context.get_event_data()

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'eventType': 'event',
            'traceId': self.client.trace_id,
            'traceUniqueId': self.trace_unique_id,
            'sessionId': self.client.session_id,
            'userId': self.client.context.user.get('userId') if self.client.context.user else uuid.uuid4().hex,
            'status': 0,
            'dateTimeZone': str(self.time.astimezone().tzname()),
            'date': str(self.time),
            'startTime': self.start_time,
            'time': time.time(),
            'loadTime': self.load_time,
            'technology': 'python',
            'technologyVersion': platform.python_version(),
            'environment': self.client.environment,
            'release': self.client.release,
            'projectId': self.client._extract_project_id(self.client.dsn),
            'httpStatusCode': 200,
            'apiClientVersion': __import__('streply').__version__,
            'type': self.type,
            'level': self.level,
            'params': self._format_params(self.params),
            'message': self.message,
            'requestUserAgent': self.client.context.request.get('user_agent') if hasattr(self.client.context, 'request') else None,
            'requestParams': self.client.context.request.get('params') if hasattr(self.client.context, 'request') else sys.argv,
            'dir': self.client.context.get('dir', os.getcwd()),
            'user': self.client.context.user,
            'url': self.client.context.request.get('url') if hasattr(self.client.context, 'request') else None,
            'flag': self.client.context.get('flag', None),
            'file': self.file,
            'line': self.line,
            'exceptionName': self.exception_name,
            'trace': self.trace,
            'channel': self.client.context.get('channel', None),
        }

        data.update(self.context_data)

        return data

    def _format_params(self, params):
        formatted_params = []

        for key, value in params.items():
            formatted_params.append({
                'name': key,
                'value': value
            })

        return formatted_params
