import os
import inspect

from streply.source import source

def stacktrace(_trace):
    output = []
    path = os.getcwd() + '/'

    for frame in inspect.getinnerframes(_trace):
        file = frame.filename
        line = frame.lineno
        function = frame.function
        code_context = frame.code_context
        code_context = code_context[0].strip() if code_context else None

        file = file.replace(path, '')

        output.append({
            'file': file,
            'line': line,
            'function': function,
            'context': code_context,
        })

    return output

class trace:
    def __init__(self):
        self._trace = []

    def load(self, _trace):
        _parsed = stacktrace(_trace)

        for _row in _parsed:
            self.add(_row['file'], _row['line'], _row['function'], _row['context'], 10)

    def add(self, file: str, line: int, function_name: str, class_name: str, read_lines: int):
        self._trace.append({
            'file': file,
            'line': line,
            'function': function_name,
            'class': class_name,
            'args': [],
            'source': source(file, line, read_lines)
        })

    def toArray(self):
        return self._trace
