"""
Integracja z systemem logowania Pythona
"""
import logging
import sys
from typing import Optional, Dict, Any

class StreplyHandler(logging.Handler):
    """
    Handler dla standardowego loggera Pythona wysyłający logi do Streply
    
    Przykład użycia:
    
    ```python
    import logging
    from streply.integrations.logging import StreplyHandler
    
    logger = logging.getLogger(__name__)
    handler = StreplyHandler()
    handler.setLevel(logging.ERROR)  # Wysyłaj tylko logi o poziomie ERROR i wyższym
    logger.addHandler(handler)
    
    # Teraz logi będą wysyłane do Streply
    try:
        1 / 0
    except Exception:
        logger.exception("Wystąpił błąd")
    ```
    """
    
    def __init__(self, client=None, level=logging.NOTSET):
        """
        Inicjalizuje handler loggera
        
        Args:
            client: Klient Streply do użycia (opcjonalny, domyślnie używa globalnego klienta)
            level: Minimalny poziom logów do przechwytywania
        """
        super().__init__(level)
        self.client = client
    
    def _get_client(self):
        """Pobiera klienta Streply"""
        if self.client:
            return self.client
        
        # Użyj globalnego klienta, jeśli nie podano lokalnego
        try:
            import streply_sdk
            return streply_sdk._ensure_client()
        except (ImportError, RuntimeError):
            return None
    
    def emit(self, record):
        """
        Wysyła rekord logu do Streply
        
        Args:
            record: Rekord logu
        """
        client = self._get_client()
        if not client:
            return
        
        # Określ typ zdarzenia na podstawie poziomu logu
        event_type = 'log'
        level = 'normal'
        
        if record.levelno >= logging.ERROR:
            event_type = 'error'
            level = 'normal'
        
        if record.levelno >= logging.CRITICAL:
            level = 'critical'
        
        # Pobierz szczegóły wyjątku, jeśli są dostępne
        exc_info = record.exc_info
        
        # Dodatkowe parametry
        params = {
            'logger': record.name,
            'level_name': record.levelname,
            'path': record.pathname,
        }
        
        # Dodaj dane z rekordu, jeśli są
        if hasattr(record, 'request'):
            params['request'] = record.request
        
        # Jeśli mamy informacje o wyjątku, użyj ich
        if exc_info and exc_info != (None, None, None):
            client.capture_exception(
                exc_info,
                message=self.format(record),
                params=params,
                level=level,
                file=record.pathname,
                line=record.lineno
            )
        else:
            # W przeciwnym razie wyślij jako zwykły log
            client.capture_message(
                self.format(record),
                type=event_type,
                level=level,
                params=params,
                file=record.pathname,
                line=record.lineno
            )