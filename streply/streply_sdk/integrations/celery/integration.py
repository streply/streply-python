import logging
import sys
from streply.integrations.base import Integration

logger = logging.getLogger(__name__)


class CeleryIntegration(Integration):
    #  FIXME: Requires refactoring, should check better.    
    @staticmethod
    def is_available():
        try:
            import celery
            return True
        except ImportError:
            return False
    
    def setup(self, client):
        try:
            import celery
            
            self.client = client
            self._connect_signals()
            self._patch_celery()

            logger.debug('Celery integration enabled')
        except ImportError as e:
            logger.error(f'Error setting up Celery integration: {e}')
        except Exception as e:
            logger.error(f'Unexpected error setting up Celery integration: {e}')
    
    def _connect_signals(self):
        try:
            from celery.signals import (
                task_failure, task_success, task_retry, task_revoked, 
                before_task_publish, after_task_publish
            )

            task_failure.connect(self._handle_task_failure)
            task_success.connect(self._handle_task_success)
            task_retry.connect(self._handle_task_retry)
            task_revoked.connect(self._handle_task_revoked)
            before_task_publish.connect(self._handle_before_task_publish)
            after_task_publish.connect(self._handle_after_task_publish)

            logger.debug('Connected to Celery signals')
        except Exception as e:
            logger.error(f'Error connecting to Celery signals: {e}')

    def _patch_celery(self):
        try:
            import celery

            original_celery_init = celery.Celery.__init__

            integration = self

            def patched_init(app_self, *args, **kwargs):
                original_celery_init(app_self, *args, **kwargs)

                if hasattr(app_self, 'Task'):
                    original_task_on_failure = app_self.Task.on_failure
                    
                    def patched_on_failure(task_self, exc, task_id, args, kwargs, einfo=None, **options):
                        try:
                            integration._handle_task_failure(
                                sender=task_self,
                                task_id=task_id,
                                exception=exc,
                                args=args,
                                kwargs=kwargs,
                                einfo=einfo
                            )
                        except Exception as e:
                            logger.error(f'Error in patched on_failure: {e}')

                        return original_task_on_failure(task_self, exc, task_id, args, kwargs, einfo, **options)

                    app_self.Task.on_failure = patched_on_failure

                logger.debug(f'Patched Celery app: {app_self}')

            celery.Celery.__init__ = patched_init

            self._patch_existing_apps()

            logger.debug('Patched Celery.__init__')
        except Exception as e:
            logger.error(f'Error patching Celery: {e}')

    def _patch_existing_apps(self):
        try:
            import celery

            try:
                app = celery.current_app
                if app:
                    self._patch_celery_app(app)
            except (AttributeError, ImportError):
                pass

            for module_name, module in list(sys.modules.items()):
                if hasattr(module, 'app') and isinstance(module.app, celery.Celery):
                    self._patch_celery_app(module.app)
        except Exception as e:
            logger.error(f'Error patching existing Celery apps: {e}')

    def _patch_celery_app(self, app):
        try:
            if hasattr(app, 'Task'):
                original_task_on_failure = app.Task.on_failure

                integration = self

                def patched_on_failure(task_self, exc, task_id, args, kwargs, einfo=None, **options):
                    try:
                        integration._handle_task_failure(
                            sender=task_self,
                            task_id=task_id,
                            exception=exc,
                            args=args,
                            kwargs=kwargs,
                            einfo=einfo
                        )
                    except Exception as e:
                        logger.error(f'Error in patched on_failure: {e}')

                    return original_task_on_failure(task_self, exc, task_id, args, kwargs, einfo, **options)

                app.Task.on_failure = patched_on_failure

                logger.debug(f'Patched existing Celery app: {app}')
        except Exception as e:
            logger.error(f'Error patching Celery app: {e}')

    def _handle_task_failure(self, sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
        try:
            with self.client.configure_scope() as scope:
                scope.set_tag('celery.task_id', task_id)
                scope.set_tag('celery.task_name', sender.name if sender else 'unknown')

                if args:
                    scope.set_extra('celery.args', self._safe_repr(args))
                if kwargs:
                    scope.set_extra('celery.kwargs', self._safe_repr(kwargs))

            if exception and einfo:
                self.client.capture_exception(
                    (type(exception), exception, traceback),
                    level='error',
                    params={
                        'celery_task_id': task_id,
                        'celery_task_name': sender.name if sender else 'unknown'
                    }
                )
            else:
                self.client.capture_message(
                    f'Celery task failed: {sender.name if sender else 'unknown'}',
                    level='error',
                    params={
                        'celery_task_id': task_id,
                        'celery_task_name': sender.name if sender else 'unknown'
                    }
                )
        except Exception as e:
            logger.error(f'Error handling Celery task failure: {e}')

    def _safe_repr(self, obj):
        try:
            return repr(obj)
        except Exception:
            return '<non-representable>'

    def _handle_task_success(self, sender=None, **kwargs):
        pass

    def _handle_task_retry(self, sender=None, request=None, reason=None, einfo=None, **kwargs):
        try:
            self.client.capture_message(
                f'Celery task retry: {sender.name if sender else 'unknown'}',
                level='warning',
                params={
                    'celery_task_id': request.id if request else 'unknown',
                    'celery_task_name': sender.name if sender else 'unknown',
                    'retry_reason': str(reason) if reason else 'unknown'
                }
            )
        except Exception as e:
            logger.error(f'Error handling Celery task retry: {e}')
    
    def _handle_task_revoked(self, sender=None, request=None, **kwargs):
        pass

    def _handle_before_task_publish(self, sender=None, body=None, **kwargs):
        pass

    def _handle_after_task_publish(self, sender=None, body=None, **kwargs):
        pass
