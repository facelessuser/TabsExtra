import sublime_plugin
import sublime
from os.path import join, exists
from os import makedirs, remove, rename

ST3 = int(sublime.version()) >= 3000

PACKAGE_NAME = "TabsExtra"
DEFAULT_PACKAGE = "Default"
TAB_MENU = "Tab Context.sublime-menu"
SETTINGS = "tabs_extra.sublime-settings"

EMPTY_MENU = '''[
]
'''

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

RESTORE_CONFIRM2 = '''In ST2, TabsExtra will try to restore the "Tab Context.sublime-menu" menu from a previous backup.  If the restore fails, TabsExtra will generate a new one which should match the shipped version.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''

ST2_WARN_MSG = '''TabsExtra:
ST2 support is not officially complete.  For best functionality, it is recommended to install the override menu for the Default tab context menu.
'''


def is_persistent():
    return sublime.load_settings(SETTINGS).get("persistent_sticky", False)


class TabsExtraClearAllStickyCommand(sublime_plugin.WindowCommand):
    def run(self, group=-1, force=False):
        if group == -1:
            return
        persistent = is_persistent()
        views = self.window.views_in_group(int(group))
        if not persistent or force:
            for v in views:
                v.settings().erase("tabs_extra_sticky")

    def is_visible(self, group=-1, force=False):
        marked = False
        views = self.window.views_in_group(int(group))
        for v in views:
            if v.settings().get("tabs_extra_sticky", False):
                marked = True
                break
        return marked


class TabsExtraToggleStickyCommand(sublime_plugin.WindowCommand):
    def run(self, group=-1, index=-1):
        if group == -1 or index == -1:
            return False
        view = self.window.views_in_group(int(group))[index]
        if not view.settings().get("tabs_extra_sticky", False):
            view.settings().set("tabs_extra_sticky", True)
        else:
            view.settings().erase("tabs_extra_sticky")

    def is_checked(self, group=-1, index=-1):
        if group == -1 or index == -1:
            return False
        return self.window.views_in_group(int(group))[index].settings().get("tabs_extra_sticky", False)


class TabsExtraCommand(sublime_plugin.WindowCommand):
    def init(self, close_type, group, index):
        self.persistent = is_persistent()
        views = self.window.views_in_group(int(group))
        assert(close_type in ["single", "left", "right", "other", "all"])

        if close_type == "single":
            self.targets = [views.pop(index)]
            self.cleanup = bool(len(views[:index] + views[index + 1:]))
        elif close_type == "left":
            self.targets = views[:index]
            self.cleanup = bool(len(views[index:]))
        elif close_type == "right":
            self.targets = views[index + 1:]
            self.cleanup = bool(len(views[:index + 1]))
        elif close_type == "other":
            self.targets = views[:index] + views[index + 1:]
            self.cleanup = True
        elif close_type == "all":
            self.targets = views[:]
            self.cleanup = False

    def run(self, group=-1, index=-1, close_type="single"):
        if group == -1 or index == -1:
            return
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


class TabsExtraListener(sublime_plugin.EventListener):
    def on_window_command(self, window, command_name, args):
        if command_name == "close_by_index":
            command_name = "tabs_extra"
            args["close_type"] = "single"
            return (command_name, args)
        elif command_name == "close_others_by_index":
            command_name = "tabs_extra"
            args["close_type"] = "other"
            return (command_name, args)
        elif command_name == "close_to_right_by_index":
            command_name = "tabs_extra"
            args["close_type"] = "right"
            return (command_name, args)
        return None


class TabsExtraInstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        msg = OVERRIDE_CONFIRM if ST3 else OVERRIDE_CONFIRM2
        if sublime.ok_cancel_dialog(msg):
            menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
            if not exists(menu_path):
                makedirs(menu_path)
            menu = join(menu_path, TAB_MENU)
            with open(menu, "w") as f:
                f.write(EMPTY_MENU)
            default_path = join(sublime.packages_path(), "Default")
            if not exists(default_path):
                makedirs(default_path)
            default_menu = join(default_path, TAB_MENU)
            if not ST3:
                if exists(default_menu) and not exists(default_menu + ".tabs_extra"):
                    rename(default_menu, default_menu + ".tabs_extra")
            with open(default_menu, "w") as f:
                f.write(OVERRIDE_MENU)


class TabsExtraUninstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        msg = RESTORE_CONFIRM if ST3 else RESTORE_CONFIRM2
        if sublime.ok_cancel_dialog(msg):
            menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
            if not exists(menu_path):
                makedirs(menu_path)
            menu = join(menu_path, TAB_MENU)
            with open(menu, "w") as f:
                f.write(DEFAULT_MENU)
            default_path = join(sublime.packages_path(), "Default")
            default_menu = join(default_path, TAB_MENU)
            if exists(default_menu):
                remove(default_menu)
            if not ST3:
                if exists(default_menu + ".tabs_extra"):
                    rename(default_menu + ".tabs_extra", default_menu)
                else:
                    with open(default_menu) as f:
                        f.write(BACKUP_MENU)


def plugin_loaded():
    menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
    if not exists(menu_path):
        makedirs(menu_path)
    menu = join(menu_path, TAB_MENU)
    if not exists(menu):
        with open(menu, "w") as f:
            f.write(DEFAULT_MENU)


def St2Warn():
    sublime.error_message(ST2_WARN_MSG)


if not ST3:
    if sublime.load_settings(SETTINGS).get("st2_warning_enabled", True):
        sublime.set_timeout(St2Warn, 3000)
    plugin_loaded()
