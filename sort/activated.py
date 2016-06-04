"""
Sort by tab activation.

Copyright (c) 2014 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
from os.path import basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    """Prep data for sort."""

    for v in views:
        view_data.append(
            (
                v.settings().get("tabs_extra_last_activated", 0),
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )
