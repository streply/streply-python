import os

def source(file: str, line: int, read_lines: int):
    output = {}
    file_path = os.getcwd() + '/' + file

    try:
        _file = open(file_path, 'r')
        _file_lines = _file.readlines()

        line = line-1

        for x in range(line-read_lines, line+read_lines):
            try:
                if x >= 0:
                    output[x+1] = _file_lines[x]
            except IndexError:
                pass
    except FileNotFoundError:
        pass

    return output
