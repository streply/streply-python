"""
Integracje z różnymi frameworkami
"""
import logging
from typing import List, Type

from streply_sdk.integrations.base import Integration

logger = logging.getLogger(__name__)

def get_default_integrations():
    """
    Zwraca listę domyślnych integracji
    
    Automatycznie wykrywa dostępne integracje dla zainstalowanych frameworków
    
    Returns:
        List[Type[Integration]]: Lista klas integracji
    """
    from streply_sdk.integrations.django.integration import DjangoIntegration
    from streply_sdk.integrations.flask.integration import FlaskIntegration
    from streply_sdk.integrations.wsgi.integration import WsgiIntegration
    
    # Lista wszystkich możliwych integracji
    all_integrations = [
        DjangoIntegration,
        FlaskIntegration,
        WsgiIntegration,
    ]
    
    return all_integrations