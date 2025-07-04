"""
Integracja z Flask
"""
import logging
import sys
import os
from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)

class FlaskIntegration(Integration):
    """Integracja z Flask zapewniająca automatyczne przechwytywanie błędów"""
    
    @staticmethod
    def is_available():
        """
        Sprawdza, czy Flask jest zainstalowany i aktywny
        
        Returns:
            bool: True jeśli Flask jest dostępny i aktywny
        """
        try:
            # Sprawdź, czy Flask jest zainstalowany
            import flask
            
            # Sprawdź, czy Flask jest aktywny - musi mieć zdefiniowane kluczowe funkcje
            if not hasattr(flask, 'request') or not hasattr(flask, 'current_app'):
                return False
                
            # Sprawdź, czy Flask jest faktycznie używany w projekcie
            return 'flask.app' in sys.modules
        except ImportError:
            return False
        except Exception:
            # W przypadku innych błędów, zakładamy że Flask nie jest poprawnie skonfigurowany
            return False
    
    def setup(self, client):
        """Konfiguruje integrację z Flask"""
        try:
            import flask
            
            # Sprawdź, czy faktycznie mamy dostęp do funkcji, których potrzebujemy
            if not hasattr(flask, 'request') or not hasattr(flask, 'current_app'):
                logger.error("Flask is installed but not properly configured")
                return
                
            # Zapisz referencję do klienta
            self.client = client
            
            # Rejestruj obsługę wyjątków w aktualnej aplikacji Flask
            self._register_error_handler()
            
            # Rejestruj procesory kontekstu
            self._register_request_processors()
            
            logger.debug("Flask integration enabled")
        except ImportError as e:
            logger.error(f"Error setting up Flask integration: {e}")
        except Exception as e:
            logger.error(f"Unexpected error setting up Flask integration: {e}")
    
    def _register_error_handler(self):
        """Rejestruje obsługę wyjątków w Flask"""
        try:
            import flask
            
            # Uzyskaj aktualną aplikację Flask
            app = flask.current_app._get_current_object()
            
            # Zarejestruj handler dla wszystkich wyjątków
            @app.errorhandler(Exception)
            def handle_exception(e):
                self._handle_exception(None, e)
                # Pozwól na standardową obsługę wyjątku
                raise e
                
            logger.debug("Registered Flask error handler")
        except Exception as e:
            logger.error(f"Failed to register Flask error handler: {e}")
    
    def _register_request_processors(self):
        """Rejestruje procesory kontekstu w Flask"""
        try:
            import flask
            
            # Uzyskaj aktualną aplikację Flask
            app = flask.current_app._get_current_object()
            
            # Dodaj procesory kontekstu
            @app.before_request
            def before_request():
                self._before_request()
            
            @app.after_request
            def after_request(response):
                return self._after_request(response)
            
            @app.teardown_request
            def teardown_request(exception):
                self._teardown_request(exception)
                
            logger.debug("Registered Flask request processors")
        except Exception as e:
            logger.error(f"Failed to register Flask request processors: {e}")
    
    def _handle_exception(self, sender, exception):
        """Handler dla wyjątków Flask"""
        try:
            import flask
            
            # Dodaj informacje o żądaniu do kontekstu
            self._add_request_data(flask.request)
            
            # Przechwytywanie wyjątku
            self.client.capture_exception(
                sys.exc_info(),
                request=self._get_request_data(flask.request)
            )
        except Exception as e:
            logger.error(f"Error handling Flask exception: {e}")
    
    def _before_request(self):
        """Wykonywane przed każdym żądaniem"""
        try:
            import flask
            
            # Czyszczenie kontekstu na początku żądania
            self.client.context.clear_request_data()
            
            # Dodaj dane żądania do kontekstu
            self._add_request_data(flask.request)
        except Exception as e:
            logger.error(f"Error processing Flask request data: {e}")
    
    def _after_request(self, response):
        """Wykonywane po każdym żądaniu"""
        # Możemy dodać dodatkowe informacje o odpowiedzi
        return response
    
    def _teardown_request(self, exception):
        """Wykonywane przy zamykaniu żądania"""
        if exception:
            try:
                # Jeśli jest wyjątek, przechwytujemy go
                self.client.capture_exception(
                    (type(exception), exception, exception.__traceback__),
                    level="error"
                )
            except Exception as e:
                logger.error(f"Error in Flask teardown: {e}")
    
    def _add_request_data(self, request):
        """Dodaje dane żądania do kontekstu klienta"""
        try:
            # Uzyskaj dane użytkownika z Flask-Login, jeśli jest dostępny
            user_data = self._get_user_data()
            if user_data and self.client.send_default_pii:
                self.client.context.set_user(user_data)
            
            # Ustaw dane żądania w kontekście
            url = request.url
            
            # Używanie kontekstu
            with self.client.configure_scope() as scope:
                scope.set_tag("url", url)
                scope.set_tag("method", request.method)
                scope.set_tag("endpoint", request.endpoint)
            
            # Ustaw dane żądania
            request_data = {
                'url': url,
                'method': request.method,
                'params': {
                    'GET': dict(request.args),
                    'POST': dict(request.form) if self.client.send_default_pii else {},
                    'JSON': request.get_json(silent=True) if self.client.send_default_pii else None,
                    'headers': self._get_headers(request),
                },
                'user_agent': request.user_agent.string if hasattr(request, 'user_agent') else None,
                'cookies': dict(request.cookies) if self.client.send_default_pii else {},
                'ip_address': self._get_client_ip(request) if self.client.send_default_pii else None,
            }
            
            self.client.context.set_request_data(request_data)
        except Exception as e:
            logger.error(f"Error adding request data: {e}")
    
    def _get_user_data(self):
        """Wyciąga dane użytkownika z Flask-Login, jeśli jest dostępny"""
        try:
            # Sprawdź, czy Flask-Login jest dostępny
            try:
                from flask_login import current_user
                from flask import current_app
            except ImportError:
                return None
            
            # Sprawdź, czy użytkownik jest zalogowany
            if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
                return None
            
            user_data = {
                'userId': str(getattr(current_user, 'id', '') or ''),
                'userName': str(getattr(current_user, 'username', None) or getattr(current_user, 'id', None) or ''),
                'params': []
            }
            
            # Dodanie email, jeśli dostępny
            if hasattr(current_user, 'email') and current_user.email:
                user_data['params'].append({
                    'name': 'email',
                    'value': current_user.email
                })
            
            return user_data
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None
    
    def _get_request_data(self, request):
        """Przekształca obiekt żądania Flask na strukturę dla API"""
        return {
            'url': request.url,
            'method': request.method,
            'GET': dict(request.args),
            'POST': dict(request.form) if self.client.send_default_pii else {},
            'JSON': request.get_json(silent=True) if self.client.send_default_pii else None,
            'headers': self._get_headers(request),
            'cookies': dict(request.cookies) if self.client.send_default_pii else {},
        }
    
    def _get_headers(self, request):
        """Wyciąga nagłówki HTTP z żądania Flask"""
        headers = {}
        for key, value in request.headers:
            headers[key.lower()] = value
        return headers
    
    def _get_client_ip(self, request):
        """Wyciąga IP klienta z żądania Flask"""
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
        else:
            ip = request.remote_addr
        return ip