"""
Sort by file creation time.

Copyright (c) 2014 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sys
import time
from os.path import basename, exists
from TabsExtra import tab_sort_helper as tsh

if sys.platform.startswith('win'):
    _PLATFORM = "windows"
elif sys.platform == "darwin":
    _PLATFORM = "osx"
else:
    _PLATFORM = "linux"


if _PLATFORM == "osx":
    import ctypes

    # http://stackoverflow.com/questions/946967/get-file-creation-time-with-python-on-mac
    class StructTimespec(ctypes.Structure):

        """Timespec structure."""

        _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]

    class StructStat64(ctypes.Structure):

        """Stat64 structure."""

        _fields_ = [
            ('st_dev', ctypes.c_int32),
            ('st_mode', ctypes.c_uint16),
            ('st_nlink', ctypes.c_uint16),
            ('st_ino', ctypes.c_uint64),
            ('st_uid', ctypes.c_uint32),
            ('st_gid', ctypes.c_uint32),
            ('st_rdev', ctypes.c_int32),
            ('st_atimespec', StructTimespec),
            ('st_mtimespec', StructTimespec),
            ('st_ctimespec', StructTimespec),
            ('st_birthtimespec', StructTimespec),
            ('dont_care', ctypes.c_uint64 * 8)
        ]

    libc = ctypes.CDLL('libc.dylib')
    stat64 = libc.stat64
    stat64.argtypes = [ctypes.c_char_p, ctypes.POINTER(StructStat64)]

    def getctime(pth):
        """Get the appropriate creation time on OSX."""

        buf = StructStat64()
        rv = stat64(pth.encode("utf-8"), ctypes.pointer(buf))
        if rv != 0:
            raise OSError("Couldn't stat file %r" % pth)
        return float("%d.%d" % (buf.st_birthtimespec.tv_sec, buf.st_birthtimespec.tv_nsec))

else:
    from os.path import getctime as get_creation_time

    def getctime(pth):
        """Get the creation time for everyone else."""

        return get_creation_time(pth)


def run(views, view_data):
    """Prep data for sort."""

    for v in views:
        file_name = v.file_name()
        created = -1
        if file_name is not None and exists(file_name):
            try:
                created = getctime(file_name)
            except Exception:
                pass

        view_data.append(
            (
                created,
                tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                v
            )
        )

    # Wait till all times are acquired and then insert a time later
    # than the latest time for created files.
    current_time = time.time()
    count = 0
    for item in view_data:
        if item[1] == -1:
            view_data[count] = (current_time, item[1], item[2])
        count += 1
