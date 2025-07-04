"""
Narzędzia do kodowania i dekodowania danych
"""
import json
import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

class StreamlyJSONEncoder(json.JSONEncoder):
    """
    Enkoder JSON rozszerzony o obsługę typów Pythona
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        
        # Próba konwersji na dict
        try:
            return dict(obj)
        except (TypeError, ValueError):
            pass
        
        # Próba konwersji na string
        try:
            return str(obj)
        except (TypeError, ValueError):
            return repr(obj)

def to_json(data: Any) -> str:
    """
    Konwertuje dane na format JSON
    
    Args:
        data: Dane do konwersji
        
    Returns:
        str: Dane w formacie JSON
    """
    return json.dumps(data, cls=StreamlyJSONEncoder)

def from_json(data: str) -> Any:
    """
    Konwertuje dane w formacie JSON na obiekty Pythona
    
    Args:
        data: Dane w formacie JSON
        
    Returns:
        Any: Dane przekonwertowane na obiekty Pythona
    """
    return json.loads(data)

def scrub_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Czyści dane wrażliwe z obiektu
    
    Args:
        data: Dane do oczyszczenia
        sensitive_keys: Lista kluczy, które zawierają dane wrażliwe
        
    Returns:
        Dict[str, Any]: Oczyszczone dane
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'secret', 'token', 'api_key', 'apikey', 'auth']
    
    result = {}
    
    for key, value in data.items():
        # Sprawdź, czy klucz zawiera wrażliwe dane
        contains_sensitive = False
        for sensitive_key in sensitive_keys:
            if sensitive_key.lower() in key.lower():
                contains_sensitive = True
                break
        
        if contains_sensitive:
            # Ukryj dane wrażliwe
            result[key] = '********'
        elif isinstance(value, dict):
            # Rekurencyjnie oczyść zagnieżdżone słowniki
            result[key] = scrub_sensitive_data(value, sensitive_keys)
        elif isinstance(value, list):
            # Rekurencyjnie oczyść elementy listy
            result[key] = [
                scrub_sensitive_data(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Zachowaj pozostałe dane bez zmian
            result[key] = value
    
    return result