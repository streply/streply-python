"""
Klasa Event do reprezentacji zdarzeń Streply
"""
import uuid
import datetime
import platform
import sys
import os
from typing import Dict, Any, Optional, List

class Event:
    """Reprezentacja zdarzenia Streply"""
    
    def __init__(self, client, type='log', message='', level='normal', exception_name=None, params=None):
        """
        Inicjalizuje zdarzenie
        
        Args:
            client: Klient Streply
            type: Typ zdarzenia (log, error, activity)
            message: Wiadomość zdarzenia
            level: Poziom zdarzenia (normal, critical, high, low)
            exception_name: Nazwa wyjątku (dla typu error)
            params: Dodatkowe parametry
        """
        self.client = client
        self.type = type
        self.message = message
        self.level = level
        self.exception_name = exception_name
        self.params = params or {}
        self.trace = []
        self.file = None
        self.line = None
        
        # Generowanie identyfikatorów
        self.trace_unique_id = f"{client.trace_id}_{client.trace_counter}"
        
        # Czas
        self.time = datetime.datetime.now()
        self.start_time = client.start_time
        self.load_time = time.time() - client.start_time
        
        # Kontekst
        self.context_data = {}
    
    def add_trace(self, trace):
        """Dodaje informacje o stacktrace"""
        self.trace = trace
    
    def set_file_line(self, file, line):
        """Ustawia informacje o pliku i linii"""
        self.file = file
        self.line = line
    
    def update_from_context(self, context):
        """Aktualizuje zdarzenie danymi z kontekstu"""
        self.context_data = context.get_event_data()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje zdarzenie na słownik gotowy do wysłania do API"""
        data = {
            'eventType': 'event',
            'traceId': self.client.trace_id,
            'traceUniqueId': self.trace_unique_id,
            'sessionId': self.client.session_id,
            'userId': self.client.context.user.get('userId') if self.client.context.user else uuid.uuid4().hex,
            'status': 0,
            'dateTimeZone': str(self.time.astimezone().tzname()),
            'date': str(self.time),
            'startTime': self.start_time,
            'time': time.time(),
            'loadTime': self.load_time,
            'technology': 'python',
            'technologyVersion': platform.python_version(),
            'environment': self.client.environment,
            'release': self.client.release,
            'projectId': self.client._extract_project_id(self.client.dsn),
            'httpStatusCode': 200,
            'apiClientVersion': __import__('streply').__version__,
            'type': self.type,
            'level': self.level,
            'params': self._format_params(self.params),
            'message': self.message,
            'requestUserAgent': self.client.context.request.get('user_agent') if hasattr(self.client.context, 'request') else None,
            'requestParams': self.client.context.request.get('params') if hasattr(self.client.context, 'request') else sys.argv,
            'dir': self.client.context.get('dir', os.getcwd()),
            'user': self.client.context.user,
            'url': self.client.context.request.get('url') if hasattr(self.client.context, 'request') else None,
            'flag': self.client.context.get('flag', None),
            'file': self.file,
            'line': self.line,
            'exceptionName': self.exception_name,
            'trace': self.trace,
            'channel': self.client.context.get('channel', None),
        }
        
        # Dodaj dane z kontekstu
        data.update(self.context_data)
        
        return data
    
    def _format_params(self, params):
        """Formatuje parametry w formacie wymaganym przez API"""
        formatted_params = []
        
        for key, value in params.items():
            formatted_params.append({
                'name': key,
                'value': value
            })
        
        return formatted_params