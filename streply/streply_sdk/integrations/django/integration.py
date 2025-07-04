"""
Integracja z Django
"""
from streply_sdk.integrations.base import Integration
import logging
import sys
import os

logger = logging.getLogger(__name__)

class DjangoIntegration(Integration):
    """Integracja z Django zapewniająca automatyczne przechwytywanie błędów"""
    
    @staticmethod
    def is_available():
        try:
            import django
            return True
        except ImportError:
            return False
    
    def setup(self, client):
        """Konfiguruje integrację z Django"""
        try:
            from django.conf import settings
            from django.core.signals import got_request_exception, request_started, request_finished
            
            # Zapisz referencję do klienta
            self.client = client
            
            # Podpięcie się pod sygnały Django
            got_request_exception.connect(self._handle_exception)
            request_started.connect(self._handle_request_started)
            request_finished.connect(self._handle_request_finished)
            
            # Dodanie integracji z loggerem Django
            self._setup_logging()
            
            # Ustawienie zmiennych środowiskowych
            if hasattr(settings, 'ENVIRONMENT'):
                client.environment = client.environment or settings.ENVIRONMENT
            
            if hasattr(settings, 'RELEASE'):
                client.release = client.release or settings.RELEASE
            
            logger.debug("Django integration enabled")
        except ImportError as e:
            logger.error(f"Error setting up Django integration: {e}")
    
    def _handle_exception(self, sender, request=None, **kwargs):
        """Handler dla sygnału got_request_exception"""
        exc_info = sys.exc_info()
        
        # Dodaj informacje o żądaniu do kontekstu
        if request:
            self._add_request_data(request)
        
        # Przechwytywanie wyjątku
        self.client.capture_exception(
            exc_info,
            request=self._get_request_data(request) if request else None
        )
    
    def _handle_request_started(self, sender, environ=None, **kwargs):
        """Handler dla sygnału request_started"""
        # Czyszczenie kontekstu na początku żądania
        self.client.context.clear_request_data()
    
    def _handle_request_finished(self, sender, **kwargs):
        """Handler dla sygnału request_finished"""
        # Możemy tutaj dodać dodatkowe zadania po zakończeniu żądania
        pass
    
    def _add_request_data(self, request):
        """Dodaje dane żądania do kontekstu klienta"""
        user_data = self._get_user_data(request)
        if user_data and self.client.send_default_pii:
            self.client.context.set_user(user_data)
        
        # Ustaw dane żądania w kontekście
        url = request.build_absolute_uri()
        # self.client.context.set_url(url)
        request_data = {
            'url': url,
            'method': request.method,
            'params': {
                'GET': dict(request.GET),
                'POST': dict(request.POST) if self.client.send_default_pii else {},
                'headers': self._get_headers(request),
            },
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'cookies': request.COOKIES if self.client.send_default_pii else {},
            'ip_address': self._get_client_ip(request) if self.client.send_default_pii else None,
        }
        self.client.context.set_request_data(request_data)
        
        self.client.context.set_request_data({
            'url': url,
            'method': request.method,
            'params': {
                'GET': dict(request.GET),
                'POST': dict(request.POST) if self.client.send_default_pii else {},
                'headers': self._get_headers(request),
            },
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'cookies': request.COOKIES if self.client.send_default_pii else {},
            'ip_address': self._get_client_ip(request) if self.client.send_default_pii else None,
        })
    
    def _get_user_data(self, request):
        """Wyciąga dane użytkownika z żądania Django"""
        if not hasattr(request, 'user'):
            return None
        
        user = request.user
        
        if not user.is_authenticated:
            return None
        
        user_data = {
            'userId': str(user.id),
            'userName': getattr(user, user.USERNAME_FIELD, str(user.id)),
            'params': []
        }
        
        # Dodanie email, jeśli dostępny
        if hasattr(user, 'email') and user.email:
            user_data['params'].append({
                'name': 'email',
                'value': user.email
            })
        
        return user_data
    
    def _get_request_data(self, request):
        """Przekształca obiekt żądania Django na strukturę dla API"""
        return {
            'url': request.build_absolute_uri(),
            'method': request.method,
            'GET': dict(request.GET),
            'POST': dict(request.POST) if self.client.send_default_pii else {},
            'headers': self._get_headers(request),
            'cookies': request.COOKIES if self.client.send_default_pii else {},
        }
    
    def _get_headers(self, request):
        """Wyciąga nagłówki HTTP z żądania Django"""
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                name = key[5:].lower().replace('_', '-')
                headers[name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                name = key.lower().replace('_', '-')
                headers[name] = value
        return headers
    
    def _get_client_ip(self, request):
        """Wyciąga IP klienta z żądania Django"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _setup_logging(self):
        """Konfiguruje integrację z loggerem Django"""
        from streply_sdk.integrations.logging import StreplyHandler
        
        # Dodaj handler dla loggera Django
        handler = StreplyHandler(client=self.client)
        handler.setLevel(logging.ERROR)
        
        django_logger = logging.getLogger('django')
        django_logger.addHandler(handler)