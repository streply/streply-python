import logging
import sys
import traceback
from streply.integrations.base import Integration

logger = logging.getLogger(__name__)


class BottleIntegration(Integration):
    #  FIXME: Requires refactoring, should check better.    
    @staticmethod
    def is_available():
        try:
            import bottle
            return 'bottle' in sys.modules
        except ImportError:
            return False

    def setup(self, client):
        try:
            import bottle

            self.client = client

            original_error_handler = bottle.default_app().error_handler

            def streply_error_handler(error):
                try:
                    self._capture_exception(error)
                except Exception as e:
                    logger.error(f'Error capturing Bottle exception: {e}')

                return original_error_handler(error)

            bottle.default_app().error_handler = streply_error_handler

            @bottle.hook('before_request')
            def before_request():
                try:
                    self._setup_request_context()
                except Exception as e:
                    logger.error(f'Error setting up Bottle request context: {e}')

            logger.debug('Bottle integration enabled')
        except ImportError as e:
            logger.error(f'Error setting up Bottle integration: {e}')
        except Exception as e:
            logger.error(f'Unexpected error setting up Bottle integration: {e}')

    def _capture_exception(self, error):
        try:
            import bottle

            exc_type, exc_value, tb = sys.exc_info()
            
            if exc_type is None:
                exc_type = type(error)
                exc_value = error
                tb = getattr(error, 'traceback', None)

            request = bottle.request

            with self.client.configure_scope() as scope:
                scope.set_tag('url', request.url)
                scope.set_tag('method', request.method)
                scope.set_tag('route', request.route.rule if request.route else 'unknown')

            self.client.capture_exception(
                (exc_type, exc_value, tb),
                params={
                    'bottle_route': request.route.rule if request.route else 'unknown',
                    'bottle_method': request.method,
                    'bottle_path': request.path
                }
            )
        except Exception as e:
            logger.error(f'Error capturing Bottle exception: {e}')

    def _setup_request_context(self):
        try:
            import bottle

            request = bottle.request

            with self.client.configure_scope() as scope:
                scope.set_tag('url', request.url)
                scope.set_tag('method', request.method)
                if request.route:
                    scope.set_tag('route', request.route.rule)

            request_data = {
                'url': request.url,
                'method': request.method,
                'params': {
                    'GET': dict(request.query),
                    'POST': dict(request.forms) if self.client.send_default_pii else {},
                    'headers': dict(request.headers),
                },
                'user_agent': request.headers.get('User-Agent'),
                'cookies': dict(request.cookies) if self.client.send_default_pii else {},
                'ip_address': request.remote_addr if self.client.send_default_pii else None,
            }

            self.client.context.set_request_data(request_data)
        except Exception as e:
            logger.error(f'Error setting up Bottle request context: {e}')
