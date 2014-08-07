import sublime
from os.path import getsize, exists, basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    for v in views:
        file_name = v.file_name()
        if file_name is not None and exists(file_name):
            size = getsize(file_name)
        else:
            import re
            encoding = v.encoding()
            mapping = [
                ("with BOM", ""),
                ("Windows", "cp"),
                ("-", "_"),
                (" ", "")
            ]
            encoding = v.encoding()
            m = re.match(r'.+\((.*)\)', encoding)
            if m is not None:
                encoding = m.group(1)

            for item in mapping:
                encoding = encoding.replace(item[0], item[1])
            if encoding == "Undefined":
                encoding = "utf_8"
            size = len(v.substr(sublime.Region(0, v.size())).encode(encoding))
            if v.line_endings() == 'Windows':
                size += v.rowcol(v.size())[0]
        view_data.append(
            (
                size,
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )
