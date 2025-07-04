import logging

logger = logging.getLogger(__name__)


def get_default_integrations():
    integrations = []

    try:
        from streply_sdk.integrations.django.integration import DjangoIntegration
        if DjangoIntegration.is_available():
            integrations.append(DjangoIntegration)
            logger.debug('Detected Django framework, adding DjangoIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking Django availability: {e}')

    try:
        from streply_sdk.integrations.flask.integration import FlaskIntegration
        if FlaskIntegration.is_available():
            integrations.append(FlaskIntegration)
            logger.debug('Detected Flask framework, adding FlaskIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking Flask availability: {e}')

    try:
        from streply_sdk.integrations.fastapi.integration import FastAPIIntegration
        if FastAPIIntegration.is_available():
            integrations.append(FastAPIIntegration)
            logger.debug('Detected FastAPI framework, adding FastAPIIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking FastAPI availability: {e}')

    try:
        from streply_sdk.integrations.celery.integration import CeleryIntegration
        if CeleryIntegration.is_available():
            integrations.append(CeleryIntegration)
            logger.debug('Detected Celery, adding CeleryIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking Celery availability: {e}')

    try:
        from streply_sdk.integrations.bottle.integration import BottleIntegration
        if BottleIntegration.is_available():
            integrations.append(BottleIntegration)
            logger.debug('Detected Bottle, adding BottleIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking Bottle availability: {e}')

    try:
        from streply_sdk.integrations.celery.integration import CeleryIntegration
        if CeleryIntegration.is_available():
            integrations.append(CeleryIntegration)
            logger.debug('Detected Celery, adding CeleryIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking Celery availability: {e}')

    try:
        from streply_sdk.integrations.rq.integration import RQIntegration
        if RQIntegration.is_available():
            integrations.append(RQIntegration)
            logger.debug('Detected RQ, adding RQIntegration')
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f'Error checking RQ availability: {e}')

    from streply_sdk.integrations.wsgi.integration import WsgiIntegration
    integrations.append(WsgiIntegration)
    logger.debug('Adding WsgiIntegration')

    return integrations
