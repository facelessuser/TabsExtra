"""
Sort by file modified time.

Copyright (c) 2014 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import time
from os.path import exists, getmtime, basename
from TabsExtra import tab_sort_helper as tsh


def run(views, view_data):
    """Prep data for sort."""

    for v in views:
        file_name = v.file_name()
        modified = -1
        dirty = v.is_dirty()
        if file_name is not None and exists(file_name):
            if not dirty:
                try:
                    modified = getmtime(file_name)
                except Exception:
                    dirty = True
        else:
            dirty = True

        view_data.append(
            (
                int(dirty), modified,
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )

    # Wait till all times are acquired and then insert a time later
    # than the latest time for dirty files
    current_time = time.time()
    count = 0
    for item in view_data:
        if item[1] == -1:
            view_data[count] = (item[0], current_time, item[2], item[3])
        count += 1
