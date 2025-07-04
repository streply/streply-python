import logging
import sys
import os
from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)


class FlaskIntegration(Integration):
    #  FIXME: Requires refactoring, should check better.
    @staticmethod
    def is_available():
        try:
            import flask
            return True
        except ImportError:
            return False

    def setup(self, client):
        try:
            import flask

            self.client = client

            original_flask_app_init = flask.Flask.__init__

            def patched_flask_app_init(app_self, *args, **kwargs):
                original_flask_app_init(app_self, *args, **kwargs)

                app_self.errorhandler(Exception)(self._make_error_handler())
                app_self.before_request(self._make_before_request())
                app_self.after_request(self._make_after_request())
                app_self.teardown_request(self._make_teardown_request())

                logger.debug(f'Streply Flask integration setup for app: {app_self.name}')

            flask.Flask.__init__ = patched_flask_app_init

            self._patch_existing_apps()

            logger.debug('Flask integration enabled')
        except Exception as e:
            logger.error(f'Unexpected error setting up Flask integration: {e}')

    def _patch_existing_apps(self):
        try:
            import flask

            try:
                app = flask.current_app._get_current_object()
                self._patch_app(app)
            except RuntimeError:
                pass

            for module_name, module in list(sys.modules.items()):
                if hasattr(module, 'app') and isinstance(module.app, flask.Flask):
                    self._patch_app(module.app)

                if hasattr(module, 'app') and module_name.startswith('connexion'):
                    if hasattr(module.app, 'app') and isinstance(module.app.app, flask.Flask):
                        self._patch_app(module.app.app)
        except Exception as e:
            logger.error(f'Error patching existing Flask apps: {e}')

    def _patch_app(self, app):
        try:
            app.errorhandler(Exception)(self._make_error_handler())
            app.before_request(self._make_before_request())
            app.after_request(self._make_after_request())
            app.teardown_request(self._make_teardown_request())

            logger.debug(f'Patched existing Flask app: {app.name}')
        except Exception as e:
            logger.error(f'Error patching Flask app: {e}')
    
    def _make_error_handler(self):
        client = self.client

        def error_handler(e):
            try:
                import flask

                client.capture_exception(
                    sys.exc_info(),
                    params={'endpoint': flask.request.endpoint} if hasattr(flask, 'request') else {}
                )
            except Exception as handler_error:
                logger.error(f'Error in Flask error handler: {handler_error}')

            raise e

        return error_handler

    def _make_before_request(self):
        client = self.client

        def before_request():
            try:
                import flask

                client.context.clear_request_data()

                request = flask.request
                
                with client.configure_scope() as scope:
                    scope.set_tag('url', request.url)
                    scope.set_tag('method', request.method)
                    if hasattr(request, 'endpoint') and request.endpoint:
                        scope.set_tag('endpoint', request.endpoint)

                request_data = {
                    'url': request.url,
                    'method': request.method,
                    'params': {
                        'GET': dict(request.args),
                        'POST': dict(request.form) if client.send_default_pii else {},
                        'JSON': request.get_json(silent=True) if client.send_default_pii else None,
                        'headers': dict(request.headers),
                    },
                    'user_agent': request.headers.get('User-Agent'),
                    'cookies': dict(request.cookies) if client.send_default_pii else {},
                    'ip_address': request.remote_addr if client.send_default_pii else None,
                }

                client.context.set_request_data(request_data)
            except Exception as e:
                logger.error(f'Error in Flask before_request: {e}')

        return before_request

    def _make_after_request(self):
        def after_request(response):
            return response

        return after_request
    
    def _make_teardown_request(self):
        client = self.client

        def teardown_request(exception):
            if exception:
                try:
                    client.capture_exception(
                        (type(exception), exception, exception.__traceback__),
                        level='error'
                    )
                except Exception as e:
                    logger.error(f'Error in Flask teardown_request: {e}')

        return teardown_request
