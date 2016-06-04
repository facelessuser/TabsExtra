"""
Sort by file type.

Copyright (c) 2014 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
from os.path import splitext, basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    """Prep data for sort."""

    for v in views:
        view_data.append(
            (
                tsh.numeric_sort((splitext(v.file_name())[1] if v.file_name() else '').lower()),
                tsh.numeric_sort((splitext(basename(v.file_name()))[0] if v.file_name() else '').lower()),
                v
            )
        )
