"""
Bazowa klasa integracji
"""
from abc import ABC, abstractmethod

class Integration(ABC):
    """
    Abstrakcyjna klasa bazowa dla wszystkich integracji
    
    Wszystkie integracje frameworków powinny dziedziczyć z tej klasy
    i implementować metody is_available i setup.
    """
    
    @staticmethod
    @abstractmethod
    def is_available():
        """
        Sprawdza, czy integracja jest dostępna
        
        Zwraca:
            bool: True, jeśli framework jest zainstalowany i integracja może być użyta
        """
        pass
    
    @abstractmethod
    def setup(self, client):
        """
        Konfiguruje integrację z frameworkiem
        
        Args:
            client: Klient Streply, który będzie używany przez integrację
        """
        pass