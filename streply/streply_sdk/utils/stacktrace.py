"""
Narzędzia do pracy ze stosem wywołań
"""
import inspect
import linecache
import os
import sys
from typing import Dict, Any, List, Optional, Tuple, Union

def get_lines_from_file(filename: str, lineno: int, context: int = 5) -> Dict[int, str]:
    """
    Pobiera linie z pliku wokół określonej linii
    
    Args:
        filename: Ścieżka do pliku
        lineno: Numer linii
        context: Liczba linii kontekstu do pobrania z każdej strony
        
    Returns:
        Słownik z numerami linii jako kluczami i liniami kodu jako wartościami
    """
    start = max(1, lineno - context)
    end = lineno + context
    
    lines = {}
    for i in range(start, end + 1):
        line = linecache.getline(filename, i)
        if line:
            lines[i] = line
    
    if not lines and os.path.exists(filename):
        # Jeśli linecache nie zadziałał, spróbuj otworzyć plik bezpośrednio
        try:
            with open(filename, 'r') as f:
                all_lines = f.readlines()
                for i in range(start, min(end + 1, len(all_lines) + 1)):
                    if 0 <= i - 1 < len(all_lines):
                        lines[i] = all_lines[i - 1]
        except Exception:
            pass
    
    return lines

def get_stacktrace(tb, max_frames: int = 50) -> List[Dict[str, Any]]:
    """
    Konwertuje traceback na format stacktrace dla API Streply
    
    Args:
        tb: Obiekt traceback
        max_frames: Maksymalna liczba ramek do przetworzenia
        
    Returns:
        Lista ramek stosu w formacie API Streply
    """
    frames = []
    frame_count = 0
    
    # Użyj traceback do uzyskania ramek stosu
    if tb is not None:
        current = tb
        while current and frame_count < max_frames:
            frame = current.tb_frame
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            lineno = current.tb_lineno
            
            # Pobierz kod źródłowy wokół linii
            source = get_lines_from_file(filename, lineno, context=5)
            
            # Uzyskaj argumenty funkcji, jeśli to możliwe
            args = inspect.getargvalues(frame) if frame else None
            arg_list = []
            
            if args:
                for arg_name in args.args:
                    try:
                        arg_value = args.locals.get(arg_name, "<unavailable>")
                        arg_list.append({
                            'name': arg_name,
                            'value': repr(arg_value)
                        })
                    except Exception:
                        pass
            
            # Uzyskaj nazwę klasy, jeśli istnieje
            class_name = None
            try:
                if 'self' in frame.f_locals:
                    class_name = frame.f_locals['self'].__class__.__name__
                elif 'cls' in frame.f_locals:
                    class_name = frame.f_locals['cls'].__name__
            except Exception:
                pass
            
            # Konwertuj na względną ścieżkę, jeśli znajduje się w katalogu projektu
            try:
                cwd = os.getcwd()
                if filename.startswith(cwd):
                    filename = filename[len(cwd) + 1:]
            except Exception:
                pass
            
            # Stwórz ramkę stosu
            frame_data = {
                'file': filename,
                'line': lineno,
                'function': function,
                'class': class_name,
                'args': arg_list,
                'source': {str(k): v for k, v in source.items()}
            }
            
            frames.append(frame_data)
            
            current = current.tb_next
            frame_count += 1
    
    return frames