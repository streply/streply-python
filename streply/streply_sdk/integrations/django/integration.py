from streply_sdk.integrations.base import Integration
import logging
import sys
import os

logger = logging.getLogger(__name__)


class DjangoIntegration(Integration):
    @staticmethod
    def is_available():
        try:
            import django

            import sys
            if 'manage.py' in sys.argv[0]:
                return True

            if 'DJANGO_SETTINGS_MODULE' in os.environ:
                return True

            try:
                from django.conf import settings
                return True
            except (ImportError, AttributeError):
                pass

            import inspect
            stack = inspect.stack()
            for frame in stack:
                if 'django' in frame.filename:
                    return True
   
            django_modules = ['django.http', 'django.urls', 'django.views', 
                             'django.middleware', 'django.template']
            for module in django_modules:
                if module in sys.modules:
                    return True

            return False
        except ImportError:
            return False
        except Exception as e:
            import logging
            logging.getLogger('streply').debug(f'Error in Django.is_available(): {e}')
            return False
    
    def setup(self, client):
        try:
            from django.conf import settings
            from django.core.signals import got_request_exception, request_started, request_finished

            self.client = client

            got_request_exception.connect(self._handle_exception)
            request_started.connect(self._handle_request_started)
            request_finished.connect(self._handle_request_finished)

            self._setup_logging()

            if hasattr(settings, 'ENVIRONMENT'):
                client.environment = client.environment or settings.ENVIRONMENT

            if hasattr(settings, 'RELEASE'):
                client.release = client.release or settings.RELEASE

            logger.debug('Django integration enabled')
        except ImportError as e:
            logger.error(f'Error setting up Django integration: {e}')
        except Exception as e:
            logger.error(f'Unexpected error setting up Django integration: {e}')

    def _handle_exception(self, sender, request=None, **kwargs):
        exc_info = sys.exc_info()

        if request:
            self._add_request_data(request)

        try:
            self.client.capture_exception(
                exc_info,
                request=self._get_request_data(request) if request else None
            )
        except Exception as e:
            logger.error(f'Error capturing Django exception: {e}')

    def _handle_request_started(self, sender, environ=None, **kwargs):
        try:
            self.client.context.clear_request_data()
        except Exception as e:
            logger.error(f'Error handling request_started: {e}')

    def _handle_request_finished(self, sender, **kwargs):
        pass

    def _add_request_data(self, request):
        try:
            user_data = self._get_user_data(request)
            if user_data and self.client.send_default_pii:
                self.client.context.set_user(user_data)

            url = request.build_absolute_uri()

            with self.client.configure_scope() as scope:
                scope.set_tag('url', url)
                scope.set_tag('method', request.method)

                if hasattr(request, 'resolver_match') and request.resolver_match:
                    scope.set_tag('view', request.resolver_match.view_name)

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
        except Exception as e:
            logger.error(f'Error adding request data: {e}')

    def _get_user_data(self, request):
        if not hasattr(request, 'user'):
            return None

        user = request.user

        if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return None

        try:
            user_data = {
                'userId': str(user.id),
                'userName': getattr(user, user.USERNAME_FIELD, str(user.id)),
                'params': []
            }

            if hasattr(user, 'email') and user.email:
                user_data['params'].append({
                    'name': 'email',
                    'value': user.email
                })

            return user_data
        except Exception as e:
            logger.error(f'Error getting user data: {e}')
            return None

    def _get_request_data(self, request):
        return {
            'url': request.build_absolute_uri(),
            'method': request.method,
            'GET': dict(request.GET),
            'POST': dict(request.POST) if self.client.send_default_pii else {},
            'headers': self._get_headers(request),
            'cookies': request.COOKIES if self.client.send_default_pii else {},
        }

    def _get_headers(self, request):
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
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _setup_logging(self):
        try:
            from streply_sdk.integrations.logging import StreplyHandler

            handler = StreplyHandler(client=self.client)
            handler.setLevel(logging.ERROR)

            django_logger = logging.getLogger('django')
            django_logger.addHandler(handler)
        except Exception as e:
            logger.error(f'Error setting up Django logging: {e}')
