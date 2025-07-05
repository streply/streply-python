import logging


class StreplyHandler(logging.Handler):
    def __init__(self, client=None, level=logging.NOTSET):
        super().__init__(level)
        self.client = client

    def _get_client(self):
        if self.client:
            return self.client

        try:
            import streply_sdk
            return streply_sdk._ensure_client()
        except (ImportError, RuntimeError):
            return None

    def emit(self, record):
        client = self._get_client()
        if not client:
            return

        event_type = 'log'
        level = 'normal'

        if record.levelno >= logging.ERROR:
            event_type = 'error'
            level = 'normal'

        if record.levelno >= logging.CRITICAL:
            level = 'critical'

        exc_info = record.exc_info

        params = {
            'logger': record.name,
            'level_name': record.levelname,
            'path': record.pathname,
        }

        if hasattr(record, 'request'):
            params['request'] = record.request

        if exc_info and exc_info != (None, None, None):
            client.capture_exception(
                exc_info,
                message=self.format(record),
                params=params,
                level=level,
                file=record.pathname,
                line=record.lineno
            )
        else:
            client.capture_message(
                self.format(record),
                type=event_type,
                level=level,
                params=params,
                file=record.pathname,
                line=record.lineno
            )
