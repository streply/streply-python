"""
Narzędzia do czyszczenia danych wrażliwych
"""
import re
from typing import Any, Dict, List, Optional, Tuple, Union

# Lista domyślnych kluczy zawierających dane wrażliwe
DEFAULT_SENSITIVE_KEYS = [
    'password', 'passwd', 'secret', 'token', 'api_key', 'apikey', 'auth',
    'credential', 'private', 'pwd', 'ssn', 'social_security', 'credit_card',
    'card', 'cvv', 'cvc', 'expiration', 'pin', 'passphrase', 'key'
]

# Regex dla numerów kart kredytowych
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,16}\b')

# Regex dla adresów email
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

def scrub_dict(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Czyści dane wrażliwe ze słownika
    
    Args:
        data: Słownik do oczyszczenia
        sensitive_keys: Lista kluczy, które zawierają dane wrażliwe
        
    Returns:
        Dict[str, Any]: Oczyszczony słownik
    """
    if sensitive_keys is None:
        sensitive_keys = DEFAULT_SENSITIVE_KEYS
    
    result = {}
    
    for key, value in data.items():
        # Sprawdź, czy klucz zawiera wrażliwe dane
        contains_sensitive = any(sensitive_key.lower() in key.lower() for sensitive_key in sensitive_keys)
        
        if contains_sensitive:
            # Ukryj dane wrażliwe
            result[key] = '********'
        elif isinstance(value, dict):
            # Rekurencyjnie oczyść zagnieżdżone słowniki
            result[key] = scrub_dict(value, sensitive_keys)
        elif isinstance(value, list):
            # Rekurencyjnie oczyść elementy listy
            result[key] = [
                scrub_dict(item, sensitive_keys) if isinstance(item, dict) else scrub_value(item)
                for item in value
            ]
        else:
            # Sprawdź i oczyść pojedyncze wartości
            result[key] = scrub_value(value)
    
    return result

def scrub_value(value: Any) -> Any:
    """
    Czyści pojedynczą wartość z danych wrażliwych
    
    Args:
        value: Wartość do oczyszczenia
        
    Returns:
        Any: Oczyszczona wartość
    """
    if not isinstance(value, str):
        return value
    
    # Ukryj numery kart kredytowych
    value = CREDIT_CARD_PATTERN.sub('****-****-****-****', value)
    
    # Możesz dodać tutaj więcej reguł do czyszczenia innych danych wrażliwych
    
    return value

def scrub_request_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Czyści dane żądania HTTP z danych wrażliwych
    
    Args:
        request_data: Dane żądania do oczyszczenia
        
    Returns:
        Dict[str, Any]: Oczyszczone dane żądania
    """
    result = {}
    
    # Oczyść parametry GET
    if 'GET' in request_data:
        result['GET'] = scrub_dict(request_data['GET'])
    
    # Oczyść parametry POST
    if 'POST' in request_data:
        result['POST'] = scrub_dict(request_data['POST'])
    
    # Oczyść dane JSON
    if 'JSON' in request_data and request_data['JSON']:
        if isinstance(request_data['JSON'], dict):
            result['JSON'] = scrub_dict(request_data['JSON'])
        else:
            result['JSON'] = request_data['JSON']
    
    # Oczyść nagłówki
    if 'headers' in request_data:
        headers = {}
        for key, value in request_data['headers'].items():
            # Ukryj nagłówki autoryzacji
            if key.lower() in ('authorization', 'cookie', 'set-cookie', 'x-auth-token', 'x-api-key'):
                headers[key] = '********'
            else:
                headers[key] = value
        result['headers'] = headers
    
    # Kopiuj pozostałe dane
    for key, value in request_data.items():
        if key not in ('GET', 'POST', 'JSON', 'headers'):
            result[key] = value
    
    return result