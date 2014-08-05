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
    from ctypes import *

    # http://stackoverflow.com/questions/946967/get-file-creation-time-with-python-on-mac
    class struct_timespec(Structure):
        _fields_ = [('tv_sec', c_long), ('tv_nsec', c_long)]

    class struct_stat64(Structure):
        _fields_ = [
            ('st_dev', c_int32),
            ('st_mode', c_uint16),
            ('st_nlink', c_uint16),
            ('st_ino', c_uint64),
            ('st_uid', c_uint32),
            ('st_gid', c_uint32),
            ('st_rdev', c_int32),
            ('st_atimespec', struct_timespec),
            ('st_mtimespec', struct_timespec),
            ('st_ctimespec', struct_timespec),
            ('st_birthtimespec', struct_timespec),
            ('dont_care', c_uint64 * 8)
        ]

    libc = CDLL('libc.dylib')
    stat64 = libc.stat64
    stat64.argtypes = [c_char_p, POINTER(struct_stat64)]

    def getctime(pth):
        """
        Get the appropriate creation time on OSX
        """

        buf = struct_stat64()
        rv = stat64(pth.encode("utf-8"), pointer(buf))
        if rv != 0:
            raise OSError("Couldn't stat file %r" % pth)
        return float("%d.%d" % (buf.st_birthtimespec.tv_sec, buf.st_birthtimespec.tv_nsec))

else:
    from os.path import getctime as get_creation_time

    def getctime(pth):
        """
        Get the creation time for everyone else
        """

        return get_creation_time(pth)


def run(views, view_data):
    for v in views:
        file_name = v.file_name()
        created = -1
        if file_name is not None and exists(file_name):
            try:
                created = getctime(file_name)
            except:
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
