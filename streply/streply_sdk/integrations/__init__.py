"""
Integracje z różnymi frameworkami
"""
import logging
import sys
from typing import List, Type

from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)

def get_default_integrations():
    """
    Zwraca listę domyślnych integracji
    
    Automatycznie wykrywa dostępne integracje dla zainstalowanych i aktywnych frameworków
    
    Returns:
        List[Type[Integration]]: Lista klas integracji
    """
    integrations = []
    
    # Sprawdź Django
    try:
        from streply_sdk.integrations.django.integration import DjangoIntegration
        if DjangoIntegration.is_available():
            integrations.append(DjangoIntegration)
            logger.debug("Detected Django framework, adding DjangoIntegration")
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Error checking Django availability: {e}")
    
    # Sprawdź Flask
    try:
        from streply_sdk.integrations.flask.integration import FlaskIntegration
        if FlaskIntegration.is_available():
            integrations.append(FlaskIntegration)
            logger.debug("Detected Flask framework, adding FlaskIntegration")
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Error checking Flask availability: {e}")
    
    # Zawsze dostępne integracje
    from streply_sdk.integrations.wsgi.integration import WsgiIntegration
    integrations.append(WsgiIntegration)
    logger.debug("Adding WsgiIntegration")
    
    return integrations