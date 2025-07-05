import time
import uuid
import sys
import platform
import datetime
import logging
import random
from typing import Dict, Optional, List, Type, Union

from streply_sdk.core.transport import Transport, HttpTransport
from streply_sdk.core.context import Context
from streply_sdk.utils.stacktrace import get_stacktrace
from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        dsn: str,
        environment: Optional[str] = None,
        release: Optional[str] = None,
        integrations: Optional[List[Union[Integration, Type[Integration]]]] = None,
        send_default_pii: bool = True,
        max_breadcrumbs: int = 100,
        sample_rate: float = 1.0,
        hooks: Optional[Dict[str, callable]] = None,
        transport: Optional[Transport] = None,
        debug: bool = False,
        **options
    ):
        self.dsn = dsn
        self.environment = environment
        self.release = release
        self.send_default_pii = send_default_pii
        self.max_breadcrumbs = max_breadcrumbs
        self.sample_rate = sample_rate
        self.hooks = hooks or {}
        self.options = options
        self.debug = debug

        self.transport = transport or HttpTransport(dsn)

        self.context = Context()

        self.session_id = uuid.uuid4().hex
        self.trace_id = uuid.uuid4().hex
        self.trace_counter = 0
        self.start_time = time.time()

        self._integrations = {}
        self._load_integrations(integrations)

        self._install_global_excepthook()

    def _load_integrations(self, integrations):
        from streply_sdk.integrations import get_default_integrations

        available_integrations = get_default_integrations()

        if integrations is None:
            for integration_cls in available_integrations:
                if integration_cls.is_available():
                    self._setup_integration(integration_cls())
        else:
            for integration in integrations:
                if isinstance(integration, type):
                    integration = integration()
                self._setup_integration(integration)

    def _setup_integration(self, integration):
        integration_name = integration.__class__.__name__

        if integration_name in self._integrations:
            logger.warning(f'Integration {integration_name} is already enabled')
            return

        self._integrations[integration_name] = integration

        try:
            integration.setup(self)
            logger.debug(f'Enabled integration: {integration_name}')
        except Exception as e:
            logger.error(f'Error setting up integration {integration_name}: {e}')

    def _install_global_excepthook(self):
        old_excepthook = sys.excepthook

        def excepthook(type_, value, traceback):
            self.capture_exception((type_, value, traceback))
            return old_excepthook(type_, value, traceback)

        sys.excepthook = excepthook

    def capture_exception(self, exc_info=None, **kwargs):
        if exc_info is None:
            exc_info = sys.exc_info()

        if exc_info == (None, None, None):
            return

        type_, value, traceback = exc_info

        if type_ is None:
            return

        event = self._create_event(
            type='error',
            message=str(value),
            level=kwargs.pop('level', 'normal'),
            exception_name=type_.__name__,
            params=kwargs.pop('params', {}),
            **kwargs
        )

        event['trace'] = get_stacktrace(traceback)

        file_line_info = self._get_file_line_from_traceback(traceback)
        if file_line_info:
            event['file'] = file_line_info.get('file')
            event['line'] = file_line_info.get('line')

        return self._capture_event(event)

    def capture_message(self, message, **kwargs):
        event = self._create_event(
            type=kwargs.pop('type', 'log'),
            message=message,
            level=kwargs.pop('level', 'normal'),
            params=kwargs.pop('params', {}),
            **kwargs
        )

        return self._capture_event(event)

    def _create_event(self, **kwargs):
        self.trace_counter += 1
        trace_unique_id = f'{self.trace_id}_{self.trace_counter}'

        current_time = time.time()

        event = {
            'eventType': 'event',
            'traceId': self.trace_id,
            'traceUniqueId': trace_unique_id,
            'sessionId': self.session_id,
            'userId': self.context.user.get('userId') if self.context.user else uuid.uuid4().hex,
            'status': 0,
            'dateTimeZone': str(datetime.datetime.now().astimezone().tzname()),
            'date': str(datetime.datetime.now()),
            'startTime': self.start_time,
            'time': current_time,
            'loadTime': current_time - self.start_time,
            'technology': 'python',
            'technologyVersion': platform.python_version(),
            'environment': self.environment,
            'release': self.release,
            'projectId': self._extract_project_id(self.dsn),
            'httpStatusCode': 200,
            'apiClientVersion': '',  # __import__('streply_sdk').__version__,
            'type': kwargs.get('type', 'log'),
            'level': kwargs.get('level', 'normal'),
            'params': self._format_params(kwargs.get('params', {})),
            'message': kwargs.get('message', ''),
            'requestUserAgent': self.context.request.get('user_agent') if hasattr(self.context, 'request') else None,
            'requestParams': self.context.request.get('params') if hasattr(self.context, 'request') else sys.argv,
            'dir': '',  # TODO self.context.get('dir', None),
            'user': self.context.user,
            'url': self.context.request.get('url') if hasattr(self.context, 'request') else None,
            'flag': '',  # TODO self.context.get('flag', None),
            'file': kwargs.get('file'),
            'line': kwargs.get('line'),
            'exceptionName': kwargs.get('exception_name'),
            'trace': kwargs.get('trace', []),
            'channel': '',  # TODO self.context.get('channel', None),
        }

        event.update(self.context.get_event_data())

        return event

    def _capture_event(self, event):
        if self.sample_rate < 1.0 and random.random() > self.sample_rate:
            return

        if 'before_send' in self.hooks:
            event = self.hooks['before_send'](event, {})

            if event is None:
                return

        return self.transport.send(event)

    def _format_params(self, params):
        formatted_params = []

        for key, value in params.items():
            formatted_params.append({
                'name': key,
                'value': value
            })

        return formatted_params

    def _extract_project_id(self, dsn):
        try:
            parts = dsn.split('/')
            return parts[-1]
        except Exception:
            return '0'

    def _get_file_line_from_traceback(self, traceback):
        if not traceback:
            return None

        try:
            frame = traceback.tb_frame
            filename = frame.f_code.co_filename
            lineno = traceback.tb_lineno
            return {
                'file': filename,
                'line': lineno
            }
        except Exception:
            return None
