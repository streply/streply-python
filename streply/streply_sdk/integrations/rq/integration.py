import logging
import sys
import traceback
from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)


class RQIntegration(Integration):
    #  FIXME: Requires refactoring, should check better.
    @staticmethod
    def is_available():
        try:
            import rq
            return True
        except ImportError:
            return False

    def setup(self, client):
        try:
            import rq
            from rq.job import Job
            from rq.worker import Worker
            from rq.queue import Queue

            self.client = client

            original_job_init = Job.__init__
            original_job_perform = Job.perform
            original_job_handle_failure = Job._handle_failure
            original_worker_handle_exception = Worker.handle_exception

            integration = self

            def patched_job_init(job_self, *args, **kwargs):
                original_job_init(job_self, *args, **kwargs)
    
                with client.configure_scope() as scope:
                    if hasattr(job_self, 'id'):
                        scope.set_tag('rq.job_id', job_self.id)
                    if hasattr(job_self, 'func_name'):
                        scope.set_tag('rq.func_name', job_self.func_name)
                    if hasattr(job_self, 'origin'):
                        scope.set_tag('rq.queue', job_self.origin)

            def patched_job_perform(job_self):
                with client.configure_scope() as scope:
                    if hasattr(job_self, 'id'):
                        scope.set_tag('rq.job_id', job_self.id)
                    if hasattr(job_self, 'func_name'):
                        scope.set_tag('rq.func_name', job_self.func_name)
                    if hasattr(job_self, 'origin'):
                        scope.set_tag('rq.queue', job_self.origin)

                try:
                    client.add_breadcrumb(
                        category='rq',
                        message=f'Started RQ job: {job_self.func_name}',
                        level='info',
                        data={
                            'job_id': job_self.id,
                            'queue': job_self.origin
                        }
                    )

                    result = original_job_perform(job_self)

                    client.add_breadcrumb(
                        category='rq',
                        message=f'Completed RQ job: {job_self.func_name}',
                        level='info',
                        data={
                            'job_id': job_self.id,
                            'queue': job_self.origin
                        }
                    )

                    return result
                except Exception as e:
                    raise

            def patched_job_handle_failure(job_self, exc_string):
                exc_info = sys.exc_info()

                job_info = {
                    'job_id': job_self.id if hasattr(job_self, 'id') else 'unknown',
                    'func_name': job_self.func_name if hasattr(job_self, 'func_name') else 'unknown',
                    'queue': job_self.origin if hasattr(job_self, 'origin') else 'unknown',
                    'args': repr(job_self.args) if hasattr(job_self, 'args') else '[]',
                    'kwargs': repr(job_self.kwargs) if hasattr(job_self, 'kwargs') else '{}'
                }

                with client.configure_scope() as scope:
                    for key, value in job_info.items():
                        scope.set_tag(f'rq.{key}', value)

                if exc_info and exc_info[0]:
                    client.capture_exception(
                        exc_info,
                        level='error',
                        params=job_info
                    )
                else:
                    client.capture_message(
                        f'RQ job failed: {job_self.func_name}',
                        level='error',
                        params={
                            **job_info,
                            'error': exc_string
                        }
                    )

                return original_job_handle_failure(job_self, exc_string)

            def patched_worker_handle_exception(worker_self, job, *exc_info):
                worker_info = {
                    'worker_name': worker_self.name if hasattr(worker_self, 'name') else 'unknown',
                    'queues': repr(worker_self.queue_names()) if hasattr(worker_self, 'queue_names') else '[]'
                }

                job_info = {}
                if job:
                    job_info = {
                        'job_id': job.id if hasattr(job, 'id') else 'unknown',
                        'func_name': job.func_name if hasattr(job, 'func_name') else 'unknown',
                        'queue': job.origin if hasattr(job, 'origin') else 'unknown'
                    }

                params = {**worker_info, **job_info}

                with client.configure_scope() as scope:
                    for key, value in params.items():
                        scope.set_tag(f'rq.{key}', value)

                if exc_info and exc_info[0]:
                    client.capture_exception(
                        exc_info,
                        level='error',
                        params=params
                    )

                return original_worker_handle_exception(worker_self, job, *exc_info)

            Job.__init__ = patched_job_init
            Job.perform = patched_job_perform
            Job._handle_failure = patched_job_handle_failure
            Worker.handle_exception = patched_worker_handle_exception

            self._patch_existing_instances()

            logger.debug('RQ integration enabled')
        except ImportError as e:
            logger.error(f'Error setting up RQ integration: {e}')
        except Exception as e:
            logger.error(f'Unexpected error setting up RQ integration: {e}')

    def _patch_existing_instances(self):
        try:
            import rq
            import sys

            for module_name, module in list(sys.modules.items()):
                for attr_name in dir(module):
                    try:
                        attr = getattr(module, attr_name)
                        if isinstance(attr, rq.Queue):
                            logger.debug(f'Found RQ Queue in module {module_name}: {attr_name}')
                        elif isinstance(attr, rq.Worker):
                            logger.debug(f'Found RQ Worker in module {module_name}: {attr_name}')
                    except Exception:
                        pass

            logger.debug('Checked existing RQ instances')
        except Exception as e:
            logger.error(f'Error patching existing RQ instances: {e}')
