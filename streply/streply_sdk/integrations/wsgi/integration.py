"""
Integracja z WSGI
"""
import logging
import sys
import os
from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)

class WsgiIntegration(Integration):
    """Integracja z WSGI zapewniająca middleware do przechwytywania błędów"""
    
    @staticmethod
    def is_available():
        # WSGI jest zawsze dostępne w Pythonie
        return True
    
    def setup(self, client):
        """Konfiguruje integrację z WSGI"""
        # Zapisz referencję do klienta
        self.client = client
        logger.debug("WSGI integration enabled")
    
    def middleware(self, wsgi_app):
        """
        Zwraca middleware WSGI do przechwytywania błędów
        
        Args:
            wsgi_app: Aplikacja WSGI do opakowania
            
        Returns:
            callable: Middleware WSGI
        """
        def wsgi_middleware(environ, start_response):
            # Skonfiguruj kontekst żądania
            self._setup_request_context(environ)
            
            try:
                # Wykonaj aplikację WSGI
                return wsgi_app(environ, start_response)
            except Exception as e:
                # Przechwytuj wyjątki
                self.client.capture_exception(
                    (type(e), e, e.__traceback__),
                    level="error",
                    request=self._get_request_data(environ)
                )
                # Propaguj wyjątek dalej
                raise
            finally:
                # Wyczyść kontekst żądania
                self.client.context.clear_request_data()
        
        return wsgi_middleware
    
    def _setup_request_context(self, environ):
        """Ustawia kontekst żądania na podstawie środowiska WSGI"""
        # Ustaw URL
        url = self._get_url_from_environ(environ)
        self.client.context.set_url(url)
        
        # Ustaw dane żądania
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
        """Tworzy URL na podstawie środowiska WSGI"""
        scheme = environ.get('wsgi.url_scheme', 'http')
        host = environ.get('HTTP_HOST', environ.get('SERVER_NAME', 'localhost'))
        port = environ.get('SERVER_PORT', '')
        path = environ.get('PATH_INFO', '')
        query = environ.get('QUERY_STRING', '')
        
        # Dodaj port do hosta, jeśli nie jest standardowy
        if port and ((scheme == 'http' and port != '80') or (scheme == 'https' and port != '443')):
            host = f"{host}:{port}"
        
        # Połącz elementy URL
        url = f"{scheme}://{host}{path}"
        if query:
            url = f"{url}?{query}"
        
        return url
    
    def _get_query_params(self, environ):
        """Przetwarza parametry zapytania z QUERY_STRING"""
        import urllib.parse
        
        query_string = environ.get('QUERY_STRING', '')
        if not query_string:
            return {}
        
        # Parsuj parametry zapytania
        try:
            return dict(urllib.parse.parse_qsl(query_string))
        except Exception:
            return {}
    
    def _get_headers_from_environ(self, environ):
        """Wyciąga nagłówki HTTP ze środowiska WSGI"""
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
        """Wyciąga IP klienta ze środowiska WSGI"""
        x_forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        else:
            return environ.get('REMOTE_ADDR')
    
    def _get_request_data(self, environ):
        """Konwertuje środowisko WSGI na strukturę dla API"""
        return {
            'url': self._get_url_from_environ(environ),
            'method': environ.get('REQUEST_METHOD'),
            'GET': self._get_query_params(environ),
            'headers': self._get_headers_from_environ(environ),
        }