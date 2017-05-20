"""Support command."""
import sublime
import sublime_plugin
import textwrap

__version__ = "1.3.0"
__pc_name__ = 'TabsExtra'


def list2string(obj):
    """Convert list to string."""

    return '.'.join([str(x) for x in obj])


def format_version(module, attr, call=False):
    """Format the version."""

    try:
        if call:
            version = getattr(module, attr)()
        else:
            version = getattr(module, attr)
    except Exception as e:
        print(e)
        version = 'Version could not be acquired!'

    if not isinstance(version, str):
        version = list2string(version)
    return version


def is_installed_by_package_control():
    """Check if installed by package control."""

    settings = sublime.load_settings('Package Control.sublime-settings')
    return str(__pc_name__ in set(settings.get('installed_packages', [])))


class TabsExtraSupportInfoCommand(sublime_plugin.ApplicationCommand):
    """Support info."""

    def run(self):
        """Run command."""

        info = {}

        info["platform"] = sublime.platform()
        info["st_version"] = sublime.version()
        info["arch"] = sublime.arch()
        info["version"] = __version__
        info["pc_install"] = is_installed_by_package_control()

        msg = textwrap.dedent(
            """\
            - ST ver.:        %(st_version)s
            - Platform:       %(platform)s
            - Arch:           %(arch)s
            - Plugin ver.:    %(version)s
            - Install via PC: %(pc_install)s
            """ % info
        )

        sublime.message_dialog(msg + '\nInfo has been copied to the clipboard.')
        sublime.set_clipboard(msg)