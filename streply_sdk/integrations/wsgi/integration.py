import logging
from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)


class WsgiIntegration(Integration):
    #  FIXME: Requires refactoring, should check better.
    @staticmethod
    def is_available():
        return True

    def setup(self, client):
        self.client = client
        logger.debug('WSGI integration enabled')

    def middleware(self, wsgi_app):
        def wsgi_middleware(environ, start_response):
            self._setup_request_context(environ)

            try:
                return wsgi_app(environ, start_response)
            except Exception as e:
                self.client.capture_exception(
                    (type(e), e, e.__traceback__),
                    level='error',
                    request=self._get_request_data(environ)
                )

                raise
            finally:
                self.client.context.clear_request_data()

        return wsgi_middleware

    def _setup_request_context(self, environ):
        url = self._get_url_from_environ(environ)
        self.client.context.set_url(url)

        self.client.context.set_request_data({
            'url': url,
            'method': environ.get('REQUEST_METHOD'),
            'params': {
                'GET': self._get_query_params(environ),
                'headers': self._get_headers_from_environ(environ),
            },
            'user_agent': environ.get('HTTP_USER_AGENT'),
            'ip_address': self._get_client_ip_from_environ(environ) if self.client.send_default_pii else None,
        })

    def _get_url_from_environ(self, environ):
        scheme = environ.get('wsgi.url_scheme', 'http')
        host = environ.get('HTTP_HOST', environ.get('SERVER_NAME', 'localhost'))
        port = environ.get('SERVER_PORT', '')
        path = environ.get('PATH_INFO', '')
        query = environ.get('QUERY_STRING', '')

        if port and ((scheme == 'http' and port != '80') or (scheme == 'https' and port != '443')):
            host = f'{host}:{port}'

        url = f'{scheme}://{host}{path}'
        if query:
            url = f'{url}?{query}'

        return url

    def _get_query_params(self, environ):
        import urllib.parse

        query_string = environ.get('QUERY_STRING', '')
        if not query_string:
            return {}

        try:
            return dict(urllib.parse.parse_qsl(query_string))
        except Exception:
            return {}

    def _get_headers_from_environ(self, environ):
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].lower().replace('_', '-')
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.lower().replace('_', '-')
                headers[header_name] = value

        return headers

    def _get_client_ip_from_environ(self, environ):
        x_forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        else:
            return environ.get('REMOTE_ADDR')

    def _get_request_data(self, environ):
        return {
            'url': self._get_url_from_environ(environ),
            'method': environ.get('REQUEST_METHOD'),
            'GET': self._get_query_params(environ),
            'headers': self._get_headers_from_environ(environ),
        }
