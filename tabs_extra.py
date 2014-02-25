"""
TabsExtra

Copyright (c) 2014 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime_plugin
import sublime
import time
from . import tab_menu

SETTINGS = "tabs_extra.sublime-settings"

LEFT = 0
RIGHT = 1
LAST = 2

OVERRIDE_CONFIRM = '''TabsExtra will overwrite the entire "Tab Context.sublime-menu" file in "Packages/Default" with a new one.  ST3 keeps an unmodified copy in the archive.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''

RESTORE_CONFIRM = '''In ST3 TabsExtra will simply delete the override "Tab Context.sublime-menu" from "Packages/Default" to allow the archived menu to take effect.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''


def is_persistent():
    """
    Check if sticky tabs should be persistent.
    """

    return sublime.load_settings(SETTINGS).get("persistent_sticky", False)


def get_fallback_direction():
    """
    Get the focused tab fallback direction.
    """

    mode = LEFT
    value = sublime.load_settings(SETTINGS).get("fallback_focus", "left")
    if value == "last_active":
        mode = LAST
    elif value == "right":
        mode = RIGHT
    return mode


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

        # Setup active index and group
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

        # Compile a list of existing tabs with their timestamps
        self.last_activated = []
        for v in self.views:
            last_activated = v.settings().get("tabs_extra_last_activated", None)
            if last_activated is not None:
                self.last_activated.append((last_activated, v))

        # Determine targeted views to close and views to cleanup
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

    def select_left(self, fallback=True):
        """
        Select tab to the left if the current active tab was closed.
        """

        selected = False
        for x in reversed(range(0, self.active_index)):
            if self.window.get_view_index(self.views[x])[1] != -1:
                self.window.focus_view(self.views[x])
                selected = True
                break
        if fallback and not selected:
            # Fallback to other direction
            selected = self.select_left(False)
        return selected

    def select_right(self, fallback=True):
        """
        Select tab to the right if the current active tab was closed.
        """

        selected = False
        for x in range(self.active_index + 1, len(self.views)):
            if self.window.get_view_index(self.views[x])[1] != -1:
                self.window.focus_view(self.views[x])
                selected = True
                break
        if fallback and not selected:
            # Fallback to other direction
            selected = self.select_right(False)
        return selected


    def select_last(self, fallback=True):
        """
        Select last activated tab if available.
        """

        selected = False
        self.last_activated.sort()

        if len(self.last_activated):
            # Get most recent activated tab
            for v in reversed(self.last_activated):
                if self.window.get_view_index(v[1])[1] != -1:
                    self.window.focus_view(v[1])
                    selected = True
                    break

        if fallback and not selected:
            # Fallback left
            selected = self.select_left(False)
        if fallback and not selected:
            # Fallback right
            selected = self.select_right(False)
        return selected

    def select_view(self):
        """
        Select active tab, if available, or fallback to the left or right.
        """

        selected = False
        if self.active_index is not None:
            fallback_mode = get_fallback_direction()
            if self.window.get_view_index(self.views[self.active_index])[1] != -1:
                self.window.focus_view(self.views[self.active_index])
                selected = True
            elif fallback_mode == LAST:
                self.select_last()
            elif fallback_mode == RIGHT:
                self.select_right()
            else:
                self.select_left()

    def run(
        self, group=-1, index=-1,
        close_type="single", unsaved_prompt=True, close_unsaved=True
    ):
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
                    if not v.is_dirty() or close_unsaved:
                        if v.is_dirty() and not unsaved_prompt:
                            v.set_scratch(True)
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

    def on_activated(self, view):
        """
        Timestamp each view when activated.
        """

        view.settings().set('tabs_extra_last_activated', time.time())


class TabsExtraViewWrapperCommand(sublime_plugin.WindowCommand):
    def run(self, command, group=-1, index=-1, args={}):
        """
        Wrap command in order to ensure view gets focused first.
        """

        if group >= 0 or index >= 0:
            self.window.focus_view(self.window.views_in_group(int(group))[index])
            self.window.run_command(command, args)


class TabsExtraRevertCommand(TabsExtraViewWrapperCommand):
    def is_visible(self, command, group=-1, index=-1, args={}):
        """
        Determine if command should be visible in menu.
        """

        enabled = False
        if group >= 0 or index >= 0:
            view = self.window.views_in_group(int(group))[index]
            if view.file_name() is not None:
                enabled = view.is_dirty()
        return enabled


class TabsExtraFileCommand(TabsExtraViewWrapperCommand):
    def is_enabled(self, command, group=-1, index=-1, args={}):
        """
        Determine if command should be enabled.
        """

        enabled = False
        if group >= 0 or index >= 0:
            view = self.window.views_in_group(int(group))[index]
            enabled = view.file_name() is not None
        return enabled


class TabsExtraInstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        """
        Install/upgrade the override tab menu.
        """

        msg = OVERRIDE_CONFIRM
        if sublime.ok_cancel_dialog(msg):
            tab_menu.upgrade_override_menu()

class TabsExtraUninstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        """
        Uninstall the override tab menu.
        """

        msg = RESTORE_CONFIRM
        if sublime.ok_cancel_dialog(msg):
            tab_menu.uninstall_override_menu()


class TabsExtraInstallMenuCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        """
        Install/upgrade the standard tab menu.
        """

        tab_menu.upgrade_default_menu()
