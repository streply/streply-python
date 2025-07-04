import inspect
import linecache
import os
from typing import Dict, Any, List


def get_lines_from_file(filename: str, lineno: int, context: int = 5) -> Dict[int, str]:
    start = max(1, lineno - context)
    end = lineno + context

    lines = {}
    for i in range(start, end + 1):
        line = linecache.getline(filename, i)
        if line:
            lines[i] = line

    if not lines and os.path.exists(filename):
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
    frames = []
    frame_count = 0

    if tb is not None:
        current = tb
        while current and frame_count < max_frames:
            frame = current.tb_frame
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            lineno = current.tb_lineno

            source = get_lines_from_file(filename, lineno, context=5)

            args = inspect.getargvalues(frame) if frame else None
            arg_list = []

            if args:
                for arg_name in args.args:
                    try:
                        arg_value = args.locals.get(arg_name, '<unavailable>')
                        arg_list.append({
                            'name': arg_name,
                            'value': repr(arg_value)
                        })
                    except Exception:
                        pass

            class_name = None
            try:
                if 'self' in frame.f_locals:
                    class_name = frame.f_locals['self'].__class__.__name__
                elif 'cls' in frame.f_locals:
                    class_name = frame.f_locals['cls'].__name__
            except Exception:
                pass

            try:
                cwd = os.getcwd()
                if filename.startswith(cwd):
                    filename = filename[len(cwd) + 1:]
            except Exception:
                pass

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
