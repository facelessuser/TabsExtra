"""
Sort by path.

Copyright (c) 2014 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
from os.path import dirname, basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    """Prep data for sort."""

    for v in views:
        view_data.append(
            (
                tsh.numeric_sort(dirname(v.file_name() if v.file_name() else '').lower()),
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )
