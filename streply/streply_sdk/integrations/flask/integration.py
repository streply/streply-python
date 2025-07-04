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
        try:
            import flask
            return True
        except ImportError:
            return False
    
    def setup(self, client):
        """Konfiguruje integrację z Flask"""
        try:
            import flask
            from flask import request, g, got_request_exception
            
            # Zapisz referencję do klienta
            self.client = client
            
            # Podpięcie się pod sygnały Flask
            got_request_exception.connect(self._handle_exception)
            
            # Dodaj procesory kontekstu
            @flask.before_request
            def before_request():
                self._before_request()
            
            @flask.after_request
            def after_request(response):
                return self._after_request(response)
            
            @flask.teardown_request
            def teardown_request(exception):
                self._teardown_request(exception)
            
            logger.debug("Flask integration enabled")
        except ImportError as e:
            logger.error(f"Error setting up Flask integration: {e}")
    
    def _handle_exception(self, sender, exception):
        """Handler dla sygnału got_request_exception"""
        from flask import request
        
        try:
            # Dodaj informacje o żądaniu do kontekstu
            self._add_request_data(request)
            
            # Przechwytywanie wyjątku
            self.client.capture_exception(
                sys.exc_info(),
                request=self._get_request_data(request)
            )
        except Exception as e:
            logger.error(f"Error handling Flask exception: {e}")
    
    def _before_request(self):
        """Wykonywane przed każdym żądaniem"""
        from flask import request, g
        
        # Czyszczenie kontekstu na początku żądania
        self.client.context.clear_request_data()
        
        # Dodaj dane żądania do kontekstu
        try:
            self._add_request_data(request)
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
        # Uzyskaj dane użytkownika z Flask-Login, jeśli jest dostępny
        user_data = self._get_user_data()
        if user_data and self.client.send_default_pii:
            self.client.context.set_user(user_data)
        
        # Ustaw dane żądania w kontekście
        url = request.url
        self.client.context.set_url(url)
        
        self.client.context.set_request_data({
            'url': url,
            'method': request.method,
            'params': {
                'GET': dict(request.args),
                'POST': dict(request.form) if self.client.send_default_pii else {},
                'JSON': request.get_json(silent=True) if self.client.send_default_pii else None,
                'headers': self._get_headers(request),
            },
            'user_agent': request.user_agent.string if request.user_agent else None,
            'cookies': dict(request.cookies) if self.client.send_default_pii else {},
            'ip_address': self._get_client_ip(request) if self.client.send_default_pii else None,
        })
    
    def _get_user_data(self):
        """Wyciąga dane użytkownika z Flask-Login, jeśli jest dostępny"""
        try:
            from flask import current_app
            from flask_login import current_user
            
            if hasattr(current_app, 'login_manager') and current_user.is_authenticated:
                user_data = {
                    'userId': str(getattr(current_user, 'id', None) or ''),
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
        except (ImportError, AttributeError, RuntimeError):
            pass
        
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