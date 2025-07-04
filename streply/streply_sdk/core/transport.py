"""
System transportu dla Streply SDK
"""
import json
import logging
import threading
import time
import urllib.parse
from typing import Dict, Any, Optional, List, Callable

import requests

logger = logging.getLogger(__name__)

class Transport:
    """Bazowa klasa transportu"""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.last_event_id = None
    
    def send(self, event: Dict[str, Any]) -> Optional[str]:
        """Wysyła zdarzenie do API"""
        raise NotImplementedError("Transport.send musi być zaimplementowane")


class HttpTransport(Transport):
    """Transport HTTP do wysyłania zdarzeń"""
    
    def __init__(
        self, 
        dsn: str,
        timeout: float = 2.0,
        buffer_size: int = 100,
        retry_max: int = 3,
        retry_delay: float = 0.5
    ):
        super().__init__(dsn)
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.retry_max = retry_max
        self.retry_delay = retry_delay
        
        # Parsowanie DSN
        parsed = urllib.parse.urlparse(dsn)
        self.public_key = parsed.username
        self.project_id = parsed.path.strip("/")
        self.api_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Buforowanie zdarzeń
        self._buffer = []
        self._buffer_lock = threading.RLock()
        self._worker = None
        self._worker_thread = None
        self._running = False
        
        # Uruchomienie worker thread
        self._start_worker()
    
    def _start_worker(self):
        """Uruchamia worker thread do asynchronicznego wysyłania zdarzeń"""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="streply-worker",
            daemon=True
        )
        self._worker_thread.start()
    
    def _worker_loop(self):
        """Główna pętla workera"""
        while self._running:
            if not self._buffer:
                # Jeśli bufor jest pusty, poczekaj chwilę
                time.sleep(0.1)
                continue
            
            # Pobierz zdarzenia z bufora
            with self._buffer_lock:
                events = self._buffer[:self.buffer_size]
                self._buffer = self._buffer[self.buffer_size:]
            
            # Wyślij zdarzenia
            for event in events:
                self._send_event(event)
    
    def _send_event(self, event: Dict[str, Any]) -> Optional[str]:
        """Wysyła pojedyncze zdarzenie do API"""
        headers = {
            "Content-Type": "application/json",
            "Token": self.public_key,
            "ProjectId": self.project_id
        }
        
        data = json.dumps(event)
        
        for attempt in range(self.retry_max):
            try:
                response = requests.post(
                    url=self.api_url,
                    data=data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    # Zapisz ID zdarzenia i zwróć
                    try:
                        response_data = response.json()
                        event_id = response_data.get("id")
                        self.last_event_id = event_id
                        return event_id
                    except Exception as e:
                        logger.error(f"Error parsing response: {e}")
                        return None
                elif response.status_code == 429:
                    # Rate limiting, poczekaj dłużej
                    time.sleep(self.retry_delay * (attempt + 1) * 2)
                else:
                    logger.warning(
                        f"Error sending event to Streply (attempt {attempt+1}/{self.retry_max}): "
                        f"HTTP {response.status_code}"
                    )
                    
                    if attempt < self.retry_max - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(
                    f"Error sending event to Streply (attempt {attempt+1}/{self.retry_max}): {e}"
                )
                
                if attempt < self.retry_max - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def send(self, event: Dict[str, Any]) -> Optional[str]:
        """Dodaje zdarzenie do bufora do asynchronicznego wysłania"""
        with self._buffer_lock:
            self._buffer.append(event)
        
        # Jeśli worker thread nie działa, uruchom go
        if not self._running or not self._worker_thread.is_alive():
            self._start_worker()
        
        return None