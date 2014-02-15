import sublime_plugin
import sublime
from os.path import join, exists
from os import makedirs, remove, rename
import json
from .lib.file_strip.json import sanitize_json

PACKAGE_NAME = "TabsExtra"
DEFAULT_PACKAGE = "Default"
TAB_MENU = "Tab Context.sublime-menu"
SETTINGS = "tabs_extra.sublime-settings"
VERSION_FILE = "version.json"

LEFT = 0
RIGHT = 1

__format__ = "1.0.0"

CHANGES = '''
- Check menu formats
'''

FORMAT_VERSION = {
    "version": __format__,
    "override": False
}


DEFAULT_MENU = '''[
    { "caption": "-", "id": "tabs_extra_sticky" },
    { "command": "tabs_extra_toggle_sticky", "args": { "group": -1, "index": -1 }, "caption": "Sticky Tab" },
    { "command": "tabs_extra_clear_all_sticky", "args": { "group": -1, "force": true }, "caption": "Clear All Sticky Tabs" },
    { "caption": "-", "id": "tabs_extra" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "all"}, "caption": "Close All Tabs" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "left" }, "caption": "Close Tabs to the Left" }
]
'''

OVERRIDE_MENU = '''
[
    // { "caption": "-", "id": "tabs_extra" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "single" }, "caption": "Close" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "all"}, "caption": "Close All Tabs" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "other" }, "caption": "Close Other Tabs" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "right" }, "caption": "Close Tabs to the Right" },
    { "command": "tabs_extra", "args": { "group": -1, "index": -1, "close_type": "left" }, "caption": "Close Tabs to the Left" },
    { "caption": "-" },
    { "command": "tabs_extra_toggle_sticky", "args": { "group": -1, "index": -1 }, "caption": "Sticky Tab" },
    { "command": "tabs_extra_clear_all_sticky", "args": { "group": -1, "force": true }, "caption": "Clear All Sticky Tabs" },
    { "caption": "-" },
    { "command": "new_file", "caption": "New File" },
    { "command": "prompt_open_file", "caption": "Open File" }
]
'''

BACKUP_MENU = '''[
    { "command": "close_by_index", "args": { "group": -1, "index": -1 }, "caption": "Close" },
    { "command": "close_others_by_index", "args": { "group": -1, "index": -1 }, "caption": "Close others" },
    { "command": "close_to_right_by_index", "args": { "group": -1, "index": -1 }, "caption": "Close tabs to the right" },
    { "caption": "-" },
    { "command": "new_file" },
    { "command": "prompt_open_file", "caption": "Open file" }
]
'''

OVERRIDE_CONFIRM = '''TabsExtra will overwrite the entire "Tab Context.sublime-menu" file in "Packages/Default" with a new one.  ST3 keeps an unmodified copy in the archive.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''

OVERRIDE_CONFIRM2 = '''TabsExtra will overwrite the entire "Tab Context.sublime-menu" file in "Packages/Default" with a new one.  In ST2, TabsExtra will backup the current menu, but updates may wipe out the override menu and may require you to re-install the override menu.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''

RESTORE_CONFIRM = '''In ST3 TabsExtra will simply delete the override "Tab Context.sublime-menu" from "Packages/Default" to allow the archived menu to take effect.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''

UPGRADE_MSG = '''
 /$$$$$$$$        /$$                 /$$$$$$$$             /$$
|__  $$__/       | $$                | $$_____/            | $$
   | $$  /$$$$$$ | $$$$$$$   /$$$$$$$| $$       /$$   /$$ /$$$$$$    /$$$$$$  /$$$$$$
   | $$ |____  $$| $$__  $$ /$$_____/| $$$$$   |  $$ /$$/|_  $$_/   /$$__  $$|____  $$
   | $$  /$$$$$$$| $$  \ $$|  $$$$$$ | $$__/    \  $$$$/   | $$    | $$  \__/ /$$$$$$$
   | $$ /$$__  $$| $$  | $$ \____  $$| $$        >$$  $$   | $$ /$$| $$      /$$__  $$
   | $$|  $$$$$$$| $$$$$$$/ /$$$$$$$/| $$$$$$$$ /$$/\  $$  |  $$$$/| $$     |  $$$$$$$
   |__/ \_______/|_______/ |_______/ |________/|__/  \__/   \___/  |__/      \_______/


======================================================================================

Menu format upgraded to version (%(format)s). To pick up these changes, do one of the following:

1. If using the override menu, select "Preferences->Package Settings->TabsExtra->Install/Upgrade Default Override Menu" from Sublime's menu.

2. If using the default menu, select "Preferences->Package Settings->TabsExtra->Install/Upgrade TabsExtra Menu" from the menu" from Sublime's menu.

======================================================================================

Changes:
%(changes)s''' % {"format": __format__, "changes": CHANGES}


def is_persistent():
    """
    Check if sticky tabs should be persistent.
    """

    return sublime.load_settings(SETTINGS).get("persistent_sticky", False)


def get_fallback_direction():
    """
    Get the focused tab fallback direction.
    """

    return LEFT if sublime.load_settings(SETTINGS).get("fallback_focus", "left") == "left" else RIGHT


class TabsExtraClearAllStickyCommand(sublime_plugin.WindowCommand):
    def run(self, group=-1, force=False):
        """
        Clear all tab sticky states of current active group.
        """

        if group >= 0:
            persistent = is_persistent()
            views = self.window.views_in_group(int(group))
            if not persistent or force:
                for v in views:
                    v.settings().erase("tabs_extra_sticky")

    def is_visible(self, group=-1, force=False):
        """
        Show command if any tabs in active group are sticky.
        """

        marked = False
        views = self.window.views_in_group(int(group))
        for v in views:
            if v.settings().get("tabs_extra_sticky", False):
                marked = True
                break
        return marked


class TabsExtraToggleStickyCommand(sublime_plugin.WindowCommand):
    def run(self, group=-1, index=-1):
        """
        Toggle a tabs sticky state.
        """

        if group >= 0 or index >= 0:
            view = self.window.views_in_group(int(group))[index]
            if not view.settings().get("tabs_extra_sticky", False):
                view.settings().set("tabs_extra_sticky", True)
            else:
                view.settings().erase("tabs_extra_sticky")

    def is_checked(self, group=-1, index=-1):
        """
        Show in menu whether the tab is sticky.
        """

        checked = False
        if group >= 0 or index >= 0:
            checked = self.window.views_in_group(int(group))[index].settings().get("tabs_extra_sticky", False)
        return checked


class TabsExtraAllCommand(sublime_plugin.WindowCommand):
    def run(self):
        """
        Close all tabs in window; not just the tabs in the active group.
        """

        for group in range(0, self.window.num_groups()):
            view = self.window.active_view_in_group(group)
            if view is not None:
                index = self.window.get_view_index(view)[1]
                self.window.run_command("tabs_extra", {"close_type": "all", "group": group, "index": index})


class TabsExtraCommand(sublime_plugin.WindowCommand):
    def init(self, close_type, group, index):
        """
        Determine which views will be targeted by close command.
        Also determine which tab states need to be cleaned up.
        """

        self.persistent = is_persistent()
        self.views = self.window.views_in_group(int(group))
        assert(close_type in ["single", "left", "right", "other", "all"])

        active_view = self.window.active_view()
        active_index = None
        self.active_index = index
        self.active_group = None
        if active_view is not None:
            active_group, active_index = self.window.get_view_index(active_view)
            if group != active_group:
                active_index = None

        if active_index is not None:
            self.active_index = active_index

        if close_type == "single":
            self.targets = [self.views[index]]
            self.cleanup = bool(len(self.views[:index] + self.views[index + 1:]))
        elif close_type == "left":
            self.targets = self.views[:index]
            self.cleanup = bool(len(self.views[index:]))
        elif close_type == "right":
            self.targets = self.views[index + 1:]
            self.cleanup = bool(len(self.views[:index + 1]))
        elif close_type == "other":
            self.targets = self.views[:index] + self.views[index + 1:]
            self.cleanup = True
        elif close_type == "all":
            self.targets = self.views[:]
            self.cleanup = False

    def select_left(self):
        """
        Select tab to the left if the current active tab was closed.
        """

        selected = False
        for x in reversed(range(0, self.active_index)):
            if self.window.get_view_index(self.views[x])[1] != -1:
                self.window.focus_view(self.views[x])
                selected = True
                break
        return selected

    def select_right(self):
        """
        Select tab to the right if the current active tab was closed.
        """

        selected = False
        for x in range(self.active_index + 1, len(self.views)):
            if self.window.get_view_index(self.views[x])[1] != -1:
                self.window.focus_view(self.views[x])
                selected = True
                break
        return selected

    def select_view(self):
        """
        Select active tab, if available, or fallback to the left or right.
        """

        selected = False
        if self.active_index is not None:
            if self.window.get_view_index(self.views[self.active_index])[1] != -1:
                self.window.focus_view(self.views[self.active_index])
                selected = True
            elif get_fallback_direction() == LEFT:
                selected = self.select_left()
                if not selected:
                    self.select_right()
            else:
                selected = self.select_right()
                if not selected:
                    self.select_left()

    def run(self, group=-1, index=-1, close_type="single"):
        """
        Close the specified tabs and cleanup sticky states.
        """

        if group >= 0 or index >= 0:
            self.init(close_type, group, index)

            for v in self.targets:
                if not v.settings().get("tabs_extra_sticky", False):
                    if not self.persistent:
                        v.settings().erase("tabs_extra_sticky")
                    self.window.focus_view(v)
                    self.window.run_command("close_file")
                elif not self.persistent:
                    v.settings().erase("tabs_extra_sticky")

            if not self.persistent and self.cleanup:
                self.window.run_command("tabs_extra_clear_all_sticky", {"group": group})

            self.select_view()


class TabsExtraListener(sublime_plugin.EventListener):
    def on_window_command(self, window, command_name, args):
        """
        Intercept and override specific close tab commands.
        """

        cmd = None
        if args is None:
            view = window.active_view()
            if view is None:
                return cmd
            group, index = window.get_view_index(view)
            args = {"group": group, "index": index}
        if command_name in ["close_by_index", "close"]:
            command_name = "tabs_extra"
            args["close_type"] = "single"
            cmd = (command_name, args)
        elif command_name == "close_all":
            command_name = "tabs_extra_all"
            args = {}
            cmd = (command_name, args)
        elif command_name == "close_others_by_index":
            command_name = "tabs_extra"
            args["close_type"] = "other"
            cmd = (command_name, args)
        elif command_name == "close_to_right_by_index":
            command_name = "tabs_extra"
            args["close_type"] = "right"
            cmd = (command_name, args)
        return cmd


class TabsExtraInstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        """
        Install/upgrade the override tab menu.
        """

        msg = OVERRIDE_CONFIRM
        if sublime.ok_cancel_dialog(msg):
            menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
            version_file = join(menu_path, VERSION_FILE)
            if not exists(menu_path):
                makedirs(menu_path)
            menu = join(menu_path, TAB_MENU)
            if exists(menu):
                remove(menu)
            default_path = join(sublime.packages_path(), "Default")
            if not exists(default_path):
                makedirs(default_path)
            default_menu = join(default_path, TAB_MENU)
            with open(default_menu, "w") as f:
                f.write(OVERRIDE_MENU)
            with open(version_file, "w") as f:
                FORMAT_VERSION["override"] = True
                f.write(json.dumps(FORMAT_VERSION, sort_keys=True, indent=4, separators=(',', ': ')))

class TabsExtraUninstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        """
        Uninstall the override tab menu.
        """

        msg = RESTORE_CONFIRM
        if sublime.ok_cancel_dialog(msg):
            default_path = join(sublime.packages_path(), "Default")
            default_menu = join(default_path, TAB_MENU)
            if exists(default_menu):
                remove(default_menu)
            upgrade_default_menu()


class TabsExtraInstallMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        """
        Install/upgrade the standard tab menu.
        """

        upgrade_default_menu()



class TabsExtraMessageCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        """
        Display upgrade message.
        """

        self.view.set_scratch(True)
        self.view.settings().set("word_wrap", True)
        self.view.set_syntax_file("Packages/Text/Plain text.tmLanguage")
        self.view.settings().set("font_face", "Courier New")
        self.view.insert(edit, 0, UPGRADE_MSG)


def upgrade_default_menu():
    """
    Install/upgrade the standard tab menu.
    """
    menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
    menu = join(menu_path, TAB_MENU)
    version_file = join(menu_path, VERSION_FILE)
    if not exists(menu_path):
        makedirs(menu_path)
    with open(menu, "w") as f:
        f.write(DEFAULT_MENU)
    FORMAT_VERSION["override"] = False
    with open(version_file, "w") as f:
        f.write(json.dumps(FORMAT_VERSION, sort_keys=True, indent=4, separators=(',', ': ')))


def plugin_loaded():
    """
    Install menu if nothing can be found. Alert the user to a menu upgrade if one is found.
    """

    menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
    if not exists(menu_path):
        makedirs(menu_path)
        upgrade_default_menu()
        return
    menu = join(menu_path, TAB_MENU)
    version_file = join(menu_path, VERSION_FILE)
    upgrade = False
    if not exists(version_file):
        upgrade = True
    else:
        v_old = {}
        try:
            with open(version_file, "r") as f:
                v_old = json.loads(sanitize_json(f.read(), preserve_lines=True))
        except Exception as e:
            print(e)
            pass

        if FORMAT_VERSION["version"] != v_old.get("version", ""):
            upgrade = True

    if upgrade:
        win = sublime.active_window()
        if win is not None:
            view = win.new_file()
            if view is not None:
                view.set_name("TabsExtra Message")
                view.run_command("tabs_extra_message")
