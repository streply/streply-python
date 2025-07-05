import logging
import sys
import os
import inspect
from streply.integrations.base import Integration

logger = logging.getLogger(__name__)


class FastAPIIntegration(Integration):
    #  FIXME: Requires refactoring, should check better.    
    @staticmethod
    def is_available():
        try:
            import fastapi
            return True
        except ImportError:
            return False

    def setup(self, client):
        try:
            import fastapi
            import starlette

            self.client = client

            original_fastapi_init = fastapi.FastAPI.__init__

            integration = self

            def patched_fastapi_init(app_self, *args, **kwargs):
                original_fastapi_init(app_self, *args, **kwargs)

                integration._add_exception_middleware(app_self)
                integration._add_exception_handlers(app_self)
                integration._add_request_middleware(app_self)

                logger.debug(f'Patched FastAPI app')

            fastapi.FastAPI.__init__ = patched_fastapi_init

            self._patch_existing_apps()

            logger.debug('FastAPI integration enabled')
        except ImportError as e:
            logger.error(f'Error setting up FastAPI integration: {e}')
        except Exception as e:
            logger.error(f'Unexpected error setting up FastAPI integration: {e}')

    def _add_exception_middleware(self, app):
        try:
            from starlette.middleware.base import BaseHTTPMiddleware

            integration = self

            class StreplyExceptionMiddleware(BaseHTTPMiddleware):
                async def dispatch(self, request, call_next):
                    try:
                        response = await call_next(request)
                        return response
                    except Exception as exc:
                        integration._capture_exception(request, exc)
                        raise

            app.add_middleware(StreplyExceptionMiddleware)

            logger.debug('Added FastAPI exception middleware')
        except Exception as e:
            logger.error(f'Error adding FastAPI exception middleware: {e}')
    
    def _add_exception_handlers(self, app):
        try:
            integration = self

            @app.exception_handler(Exception)
            async def streply_exception_handler(request, exc):
                integration._capture_exception(request, exc)
                raise exc

            logger.debug('Added FastAPI exception handlers')
        except Exception as e:
            logger.error(f'Error adding FastAPI exception handlers: {e}')

    def _add_request_middleware(self, app):
        try:
            from starlette.middleware.base import BaseHTTPMiddleware

            integration = self

            class StreplyRequestMiddleware(BaseHTTPMiddleware):
                async def dispatch(self, request, call_next):
                    try:
                        integration._setup_request_context(request)
                    except Exception as e:
                        logger.error(f'Error setting up FastAPI request context: {e}')

                    response = await call_next(request)
                    return response

            app.add_middleware(StreplyRequestMiddleware)
            logger.debug('Added FastAPI request middleware')
        except Exception as e:
            logger.error(f'Error adding FastAPI request middleware: {e}')

    def _patch_existing_apps(self):
        try:
            import fastapi

            for module_name, module in list(sys.modules.items()):
                if hasattr(module, 'app') and isinstance(module.app, fastapi.FastAPI):
                    self._patch_fastapi_app(module.app)

                for attr_name in dir(module):
                    try:
                        attr = getattr(module, attr_name)
                        if isinstance(attr, fastapi.FastAPI):
                            self._patch_fastapi_app(attr)
                    except Exception:
                        pass

            logger.debug('Patched existing FastAPI apps')
        except Exception as e:
            logger.error(f'Error patching existing FastAPI apps: {e}')

    def _patch_fastapi_app(self, app):
        try:
            self._add_exception_middleware(app)
            self._add_exception_handlers(app)
            self._add_request_middleware(app)

            logger.debug(f'Patched existing FastAPI app')
        except Exception as e:
            logger.error(f'Error patching FastAPI app: {e}')

    def _capture_exception(self, request, exception):
        try:
            _, _, tb = sys.exc_info()

            with self.client.configure_scope() as scope:
                scope.set_tag('url', str(request.url))
                scope.set_tag('method', request.method)
                scope.set_tag('path', request.url.path)

                if hasattr(request, 'path_params'):
                    for key, value in request.path_params.items():
                        scope.set_tag(f'path_param.{key}', str(value))

                if hasattr(request, 'client') and request.client:
                    scope.set_tag('client_host', request.client.host)
                    scope.set_tag('client_port', str(request.client.port))

            self.client.capture_exception(
                (type(exception), exception, tb),
                params={
                    'fastapi_path': request.url.path,
                    'fastapi_method': request.method,
                    'fastapi_exception': str(exception)
                }
            )
        except Exception as e:
            logger.error(f'Error capturing FastAPI exception: {e}')
    
    def _setup_request_context(self, request):
        try:
            url = str(request.url)

            with self.client.configure_scope() as scope:
                scope.set_tag('url', url)
                scope.set_tag('method', request.method)
                scope.set_tag('path', request.url.path)

                if hasattr(request, 'path_params'):
                    for key, value in request.path_params.items():
                        scope.set_tag(f'path_param.{key}', str(value))

            query_params = {}
            if hasattr(request, 'query_params'):
                for key, value in request.query_params.items():
                    query_params[key] = value

            headers = {}
            if hasattr(request, 'headers'):
                for key, value in request.headers.items():
                    headers[key] = value

            cookies = {}
            if hasattr(request, 'cookies'):
                cookies = dict(request.cookies)

            client_ip = None
            if self.client.send_default_pii:
                client_ip = self._get_client_ip(request)

            request_data = {
                'url': url,
                'method': request.method,
                'params': {
                    'GET': query_params,
                    'headers': headers,
                },
                'user_agent': headers.get('user-agent'),
                'cookies': cookies if self.client.send_default_pii else {},
                'ip_address': client_ip,
            }

            self.client.context.set_request_data(request_data)
        except Exception as e:
            logger.error(f'Error setting up FastAPI request context: {e}')

    def _get_client_ip(self, request):
        try:
            if 'x-forwarded-for' in request.headers:
                return request.headers['x-forwarded-for'].split(',')[0].strip()
            elif hasattr(request, 'client') and hasattr(request.client, 'host'):
                return request.client.host
            return None
        except Exception:
            return None
