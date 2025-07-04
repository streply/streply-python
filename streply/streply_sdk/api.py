"""
Główne funkcje API dla Streply SDK
"""
import sys
import logging
import threading
import functools
import time
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Type, Union, Callable

from streply_sdk.core.client import Client
from streply_sdk.integrations.base import Integration

# Globalny klient
_client = None
_client_init_lock = threading.RLock()

# Logger
logger = logging.getLogger(__name__)

def init(
    dsn: str,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    integrations: Optional[List[Union[Integration, Type[Integration]]]] = None,
    send_default_pii: bool = True,
    traces_sample_rate: float = 1.0,
    max_breadcrumbs: int = 100,
    sample_rate: float = 1.0,
    hooks: Optional[Dict[str, Callable]] = None,
    transport=None,
    debug: bool = False,
    **options
):
    """Inicjalizuje globalny klient Streply SDK"""
    global _client
    
    with _client_init_lock:
        if _client is not None:
            logger.warning("Streply SDK already initialized")
            return
        
        _client = Client(
            dsn=dsn,
            environment=environment,
            release=release,
            integrations=integrations,
            send_default_pii=send_default_pii,
            max_breadcrumbs=max_breadcrumbs,
            sample_rate=sample_rate,
            hooks=hooks,
            transport=transport,
            debug=debug,
            traces_sample_rate=traces_sample_rate,
            **options
        )
        
        logger.debug("Streply SDK initialized")

def _ensure_client():
    """Upewnia się, że klient jest zainicjalizowany"""
    global _client
    if _client is None:
        raise RuntimeError(
            "Streply SDK not initialized. Call streply.init() before using the SDK."
        )
    return _client

def capture_exception(exc_info=None, **kwargs):
    """Przechwytuje wyjątek i wysyła do Streply"""
    return _ensure_client().capture_exception(exc_info, **kwargs)

def capture_message(message, **kwargs):
    """Przechwytuje wiadomość i wysyła do Streply"""
    return _ensure_client().capture_message(message, **kwargs)

def add_breadcrumb(category=None, message=None, level='info', data=None):
    """Dodaje breadcrumb do aktualnego kontekstu"""
    _ensure_client().context.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data
    )

@contextmanager
def configure_scope():
    """Kontekst do konfiguracji scope"""
    client = _ensure_client()
    scope = client.context.push_scope()
    try:
        yield scope
    finally:
        client.context.pop_scope()

def set_user(user):
    """Ustawia globalnego użytkownika"""
    _ensure_client().context.set_user(user)

def set_tag(key, value):
    """Ustawia globalny tag"""
    _ensure_client().context.set_tag(key, value)

def set_extra(key, value):
    """Ustawia globalną dodatkową wartość"""
    _ensure_client().context.set_extra(key, value)

def trace(func=None, name=None, op=None):
    """Dekorator do profilowania funkcji"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with trace_ctx(
                name=name or func.__name__,
                op=op or f"function.{func.__module__}.{func.__name__}"
            ):
                return func(*args, **kwargs)
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

@contextmanager
def trace_ctx(name, op=None):
    """Kontekst do profilowania fragmentu kodu"""
    client = _ensure_client()
    start_time = time.time()
    
    try:
        yield
    finally:
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # ms
        
        if client.options.get('traces_sample_rate', 0) > 0:
            client.capture_message(
                f"Performance: {name}",
                type="performance",
                params={
                    "operation": op or "code.execution",
                    "name": name,
                    "duration_ms": duration
                }
            )

def last_event_id():
    """Zwraca ID ostatniego wysłanego zdarzenia"""
    try:
        return _ensure_client().transport.last_event_id
    except Exception:
        return None