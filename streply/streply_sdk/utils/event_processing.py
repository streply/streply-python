"""
Narzędzia do przetwarzania zdarzeń
"""
import re
import os
import sys
from typing import Dict, Any, List, Optional, Callable

from streply_sdk.utils.data_scrubbing import scrub_request_data, scrub_dict

def before_send_hook(event: Dict[str, Any], hint: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Hook wywoływany przed wysłaniem zdarzenia
    
    Args:
        event: Zdarzenie do przetworzenia
        hint: Dodatkowe wskazówki
        
    Returns:
        Optional[Dict[str, Any]]: Przetworzone zdarzenie lub None, aby pominąć wysyłanie
    """
    if hint is None:
        hint = {}
    
    # Czyść dane wrażliwe
    if 'params' in event and isinstance(event['params'], list):
        # Przeparsuj parametry z formatu API na słownik
        params_dict = {}
        for param in event['params']:
            if 'name' in param and 'value' in param:
                params_dict[param['name']] = param['value']
        
        # Oczyść słownik
        cleaned_params_dict = scrub_dict(params_dict)
        
        # Przekonwertuj z powrotem na format API
        event['params'] = [
            {'name': key, 'value': value}
            for key, value in cleaned_params_dict.items()
        ]
    
    # Czyść dane żądania
    if 'requestParams' in event and isinstance(event['requestParams'], dict):
        event['requestParams'] = scrub_request_data(event['requestParams'])
    
    # Czyść dane użytkownika
    if 'user' in event and isinstance(event['user'], dict) and 'params' in event['user']:
        if isinstance(event['user']['params'], list):
            # Przeparsuj parametry z formatu API na słownik
            user_params_dict = {}
            for param in event['user']['params']:
                if 'name' in param and 'value' in param:
                    user_params_dict[param['name']] = param['value']
            
            # Oczyść słownik
            cleaned_user_params_dict = scrub_dict(user_params_dict)
            
            # Przekonwertuj z powrotem na format API
            event['user']['params'] = [
                {'name': key, 'value': value}
                for key, value in cleaned_user_params_dict.items()
            ]
    
    return event

def add_environment_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dodaje dane o środowisku do zdarzenia
    
    Args:
        event: Zdarzenie do uzupełnienia
        
    Returns:
        Dict[str, Any]: Uzupełnione zdarzenie
    """
    # Dodaj informacje o środowisku
    if 'params' not in event:
        event['params'] = []
    
    # Dodaj informacje o systemie operacyjnym
    import platform
    event['params'].append({
        'name': 'os',
        'value': platform.platform()
    })
    
    # Dodaj informacje o Pythonie
    event['params'].append({
        'name': 'python',
        'value': platform.python_version()
    })
    
    # Dodaj informacje o interpreterze
    event['params'].append({
        'name': 'interpreter',
        'value': sys.executable
    })
    
    return event