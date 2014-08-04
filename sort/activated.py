from os.path import basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    for v in views:
        view_data.append(
            (
                v.settings().get("tabs_extra_last_activated", 0),
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )
