from os.path import dirname, basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    for v in views:
        view_data.append(
            (
                tsh.numeric_sort(dirname(v.file_name() if v.file_name() else '').lower()),
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )
