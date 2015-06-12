"""
Reverse sort.

Copyright (c) 2014 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""


def run(views, view_data):
    """Prep data for sort."""

    count = len(views)
    for v in views:
        view_data.append((count, v))
        count -= 1
