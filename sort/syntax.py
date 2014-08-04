from os.path import basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    for v in views:
        view_data.append(
            (
                tsh.numberic_sort(v.settings().get('syntax', '')),
                tsh.numberic_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )
