"""
TabsExtra.

Copyright (c) 2014 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime_plugin
import sublime
import time
import sys
from TabsExtra import tab_menu
import os
import functools
from operator import itemgetter
import sublime_api

from urllib.parse import urljoin
from urllib.request import pathname2url

SETTINGS = "tabs_extra.sublime-settings"
PREFS = "Preferences.sublime-settings"

LEFT = 0
RIGHT = 1
LAST = 2

LAST_ACTIVE = None

OVERRIDE_CONFIRM = '''TabsExtra will overwrite the entire "Tab Context.sublime-menu" file in "Packages/Default" with a new one.  ST3 keeps an unmodified copy in the archive.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''  # noqa

RESTORE_CONFIRM = '''In ST3 TabsExtra will simply delete the override "Tab Context.sublime-menu" from "Packages/Default" to allow the archived menu to take effect.

You do this at your own risk.  If something goes wrong, you may need to manually fix the menu.

Are you sure you want to continue?
'''  # noqa


###############################
# Helpers
###############################
def log(msg, status=False):
    """Log message."""

    string = str(msg)
    print("TabsExtra: %s" % string)
    if status:
        sublime.status_message(string)


def debug(s):
    """Debug message."""

    if sublime.load_settings(SETTINGS).get("debug", False):
        log(s)


def sublime_format_path(pth):
    """Format path for sublime."""

    import re
    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m is not None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


def is_persistent():
    """Check if sticky tabs should be persistent."""

    return sublime.load_settings(SETTINGS).get("persistent_sticky", False)


def sort_on_load_save():
    """Sort on save."""
    return (
        sublime.load_settings(SETTINGS).get("sort_on_load_save", False) and
        not sublime.load_settings(PREFS).get("preview_on_click")
    )


def timestamp_view(window, sheet):
    """Timestamp view."""

    global LAST_ACTIVE
    view = window.active_view()
    if view is None:
        return

    # Detect if this focus is due to the last active tab being moved
    if (
        LAST_ACTIVE is not None and
        not LAST_ACTIVE.settings().get("tabs_extra_is_closed", False) and
        LAST_ACTIVE.window() is None
    ):
        # Flag last active tab as being moved
        window = view.window()
        active_group, active_index = window.get_sheet_index(sheet)
        LAST_ACTIVE.settings().set("tabs_extra_moving", [window.id(), active_group])
        # Skip if moving a tab
        LAST_ACTIVE = None
        allow = False
    else:
        allow = True

    if allow:
        window = view.window()
        active_group, active_index = window.get_sheet_index(sheet)
        # Add time stamp of last activation
        view.settings().set('tabs_extra_last_activated', time.time())
        # Track the tabs last position to help with focusing after a tab is moved
        view.settings().set('tabs_extra_last_activated_sheet_index', active_index)
        LAST_ACTIVE = view
        debug("activated - %s" % view.file_name())
    else:
        debug("skipping - %s" % view.file_name())


def get_group_view(window, group, index):
    """Get the view at the given index in the given group."""

    sheets = window.sheets_in_group(int(group))
    sheet = sheets[index] if -1 < index < len(sheets) else None
    view = sheet.view() if sheet is not None else None

    return view


class Focus(object):
    """View focus handler."""

    win = None
    obj = None

    @classmethod
    def cancel(cls):
        """Cancel focus."""

        cls.win = None
        cls.obj = None

    @classmethod
    def defer(cls, win, obj):
        """Defer focus."""

        if cls.win is None and cls.obj is None:
            cls.win = win
            cls.obj = obj
            sublime.set_timeout(cls.on_focus, 100)
        else:
            cls.win = win
            cls.obj = obj

    @classmethod
    def on_focus(cls):
        """On focus event."""

        cls._focus()

    @classmethod
    def focus(cls, win, obj):
        """Set the win and obj before calling focus."""

        cls.win = win
        cls.obj = obj
        cls._focus()

    @classmethod
    def _focus(cls):
        """Perform view focus."""

        try:
            if cls.win is not None and cls.obj is not None:
                if isinstance(cls.obj, sublime.View):
                    cls.win.focus_view(cls.obj)
                    timestamp_view(cls.win, cls.obj)
                elif isinstance(cls.obj, sublime.Sheet):
                    cls.win.focus_sheet(cls.obj)
                    timestamp_view(cls.win, cls.obj)
        except Exception:
            pass
        cls.cancel()


###############################
# Sticky Tabs
###############################
class TabsExtraClearAllStickyCommand(sublime_plugin.WindowCommand):
    """Clear all sticky tabs."""

    def run(self, group=-1, force=False):
        """Clear all tab sticky states of current active group."""

        if group == -1:
            group = self.window.active_group()

        if group >= 0:
            persistent = is_persistent()
            views = self.window.views_in_group(int(group))
            if not persistent or force:
                for v in views:
                    v.settings().erase("tabs_extra_sticky")

    def is_visible(self, group=-1, force=False):
        """Show command if any tabs in active group are sticky."""

        if group == -1:
            group = self.window.active_group()

        marked = False
        views = self.window.views_in_group(int(group))
        for v in views:
            if v.settings().get("tabs_extra_sticky", False):
                marked = True
                break
        return marked


class TabsExtraToggleStickyCommand(sublime_plugin.WindowCommand):
    """Toggle sticky state for tab."""

    def run(self, group=-1, index=-1):
        """Toggle a tabs sticky state."""

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                if not view.settings().get("tabs_extra_sticky", False):
                    view.settings().set("tabs_extra_sticky", True)
                else:
                    view.settings().erase("tabs_extra_sticky")

    def is_checked(self, group=-1, index=-1):
        """Show in menu whether the tab is sticky."""

        checked = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                checked = view.settings().get("tabs_extra_sticky", False)
        return checked


class TabsExtraSetStickyCommand(sublime_plugin.TextCommand):
    """Set sticky value for the tab."""

    def run(self, edit, value):
        """Set the sticky command to the specific value."""

        if self.is_enabled(value):
            self.view.settings().set("tabs_extra_sticky", bool(value))

    def is_enabled(self, value):
        """Check if sticky value is already set to desired value."""

        enabled = False
        if self.view is not None:
            current_value = self.view.settings().get("tabs_extra_sticky", False)
            if current_value != value:
                enabled = True
        return enabled


###############################
# Close
###############################
class TabsExtraCloseMenuCommand(sublime_plugin.WindowCommand):
    """Close tabs via a quick panel menu."""

    close_types = [
        ("Close", "single"),
        ("Close Other Tabs", "other"),
        ("Close Tabs to Right", "right"),
        ("Close Tabs to Left", "left"),
        ("Close All Tabs", "all")
    ]

    def run(self, mode="normal", close_type=None):
        """Run command."""

        self.mode = mode
        self.group = -1
        self.index = -1
        sheet = self.window.active_sheet()
        if sheet is not None:
            self.group, self.index = self.window.get_sheet_index(sheet)
        if self.group != -1 and self.index != -1:
            value = None
            if close_type is not None:
                index = 0
                for ct in self.close_types:
                    if ct[1] == close_type:
                        value = index
                    index += 1
            if value is None:
                self.window.show_quick_panel(
                    [x[0] for x in self.close_types],
                    self.check_selection
                )
            else:
                self.check_selection(value)

    def check_selection(self, value):
        """Check the user's selection."""

        if value != -1:
            close_unsaved = True
            unsaved_prompt = True
            if self.mode == "skip_unsaved":
                close_unsaved = False
            if self.mode == "dismiss_unsaved":
                unsaved_prompt = False
            close_type = self.close_types[value][1]
            self.window.run_command(
                "tabs_extra_close",
                {
                    "group": int(self.group),
                    "index": int(self.index),
                    "close_type": close_type,
                    "unsaved_prompt": unsaved_prompt,
                    "close_unsaved": close_unsaved
                }
            )

    def is_enabled(self, mode="normal"):
        """Check if command is enabled."""

        group = -1
        index = -1
        sheet = self.window.active_sheet()
        if sheet is not None:
            group, index = self.window.get_sheet_index(sheet)
        return group != -1 and index != -1 and mode in ["normal", "skip_unsaved", "dismiss_unsaved"]


class TabsExtraCloseAllCommand(sublime_plugin.WindowCommand):
    """Close all tabs in the whole window."""

    def run(self):
        """Close all tabs in window; not just the tabs in the active group."""

        for group in range(0, self.window.num_groups()):
            sheet = self.window.active_sheet_in_group(group)
            if sheet is not None:
                index = self.window.get_sheet_index(sheet)[1]
                self.window.run_command("tabs_extra_close", {"close_type": "all", "group": group, "index": index})


class TabsExtraCloseCommand(sublime_plugin.WindowCommand):
    """Close tab command."""

    def init(self, close_type, group, index):
        """
        Determine which views will be targeted by close command.

        Also determine which tab states need to be cleaned up.
        """

        self.persistent = is_persistent()
        self.sheets = self.window.sheets_in_group(int(group))
        assert(close_type in ["single", "left", "right", "other", "all"])

        # Setup active index and group
        active_sheet = self.window.active_sheet()
        active_index = None
        self.active_index = index
        self.active_group = None
        if active_sheet is not None:
            active_group, active_index = self.window.get_sheet_index(active_sheet)
            if group != active_group:
                active_index = None
        if active_index is not None:
            self.active_index = active_index

        # Determine targeted sheets to close and sheets to cleanup
        if close_type == "single":
            self.targets = [self.sheets[index]]
            self.cleanup = bool(len(self.sheets[:index] + self.sheets[index + 1:]))
        elif close_type == "left":
            self.targets = self.sheets[:index]
            self.cleanup = bool(len(self.sheets[index:]))
        elif close_type == "right":
            self.targets = self.sheets[index + 1:]
            self.cleanup = bool(len(self.sheets[:index + 1]))
        elif close_type == "other":
            self.targets = self.sheets[:index] + self.sheets[index + 1:]
            self.cleanup = True
        elif close_type == "all":
            self.targets = self.sheets[:]
            self.cleanup = False

    def can_close(self, is_sticky, is_single):
        """Prompt user in certain scenarios if okay to close."""

        is_okay = True
        if is_sticky:
            if not is_single:
                is_okay = False
        return is_okay

    def run(
        self, group=-1, index=-1,
        close_type="single", unsaved_prompt=True, close_unsaved=True
    ):
        """Close the specified tabs and cleanup sticky states."""

        TabsExtraListener.extra_command_call = True

        try:
            if group >= 0 and index >= 0:
                self.init(close_type, group, index)

                if (
                    len(self.targets) and
                    not unsaved_prompt and
                    not all(not target.view().is_dirty() for target in self.targets) and
                    not sublime.ok_cancel_dialog(
                        "Are you sure you want to dismiss all targeted unsaved buffers?"
                    )
                ):
                    TabsExtraListener.extra_command_call = False
                    return

                for s in self.targets:
                    v = s.view()
                    if v is not None:
                        if self.can_close(v.settings().get("tabs_extra_sticky", False), close_type == "single"):
                            if not self.persistent:
                                v.settings().erase("tabs_extra_sticky")
                            self.window.focus_view(v)
                            if not v.is_dirty() or close_unsaved:
                                if not unsaved_prompt:
                                    v.set_scratch(True)
                                sublime_api.window_close_file(self.window.id(), v.id())
                        elif not self.persistent:
                            v.settings().erase("tabs_extra_sticky")
                    else:
                        self.window.focus_sheet(s)
                        self.window.run_command('close_file')

                if not self.persistent and self.cleanup:
                    self.window.run_command("tabs_extra_clear_all_sticky", {"group": group})
        except Exception:
            pass

        TabsExtraListener.extra_command_call = False


###############################
# Listener
###############################
class TabsExtraListener(sublime_plugin.EventListener):
    """Listener command to handle tab focus, closing, moving events."""

    extra_command_call = False

    def on_window_command(self, window, command_name, args):
        """Intercept and override specific close tab commands."""

        extra_command_call = TabsExtraListener.extra_command_call

        cmd = None
        if args is None:
            view = window.active_view()
            if view is None:
                return cmd
            # Mark all actual file closes done from TabsExtra
            # This helps us know when file close was called outside of TabsExtra commands
            if extra_command_call and command_name == "close_file":
                view.settings().set("tabs_extra_closing", True)
                return cmd
            group, index = window.get_view_index(view)
            args = {"group": group, "index": index}
        if command_name in ["close_by_index", "close"]:
            command_name = "tabs_extra_close"
            args["close_type"] = "single"
            cmd = (command_name, args)
        elif command_name == "close_all":
            command_name = "tabs_extra_close_all"
            args = {}
            cmd = (command_name, args)
        elif command_name == "close_others_by_index":
            command_name = "tabs_extra_close"
            args["close_type"] = "other"
            cmd = (command_name, args)
        elif command_name == "close_to_right_by_index":
            command_name = "tabs_extra_close"
            args["close_type"] = "right"
            cmd = (command_name, args)
        return cmd

    def on_load(self, view):
        """Mange sorting."""

        Focus.cancel()

        if sort_on_load_save():
            if not self.on_sort(view):
                view.settings().set('tabsextra_to_sort', True)

    def on_post_save(self, view):
        """On save sorting."""

        if sort_on_load_save():
            self.on_sort(view)

    def on_sort(self, view):
        """Sort views."""

        sorted_views = False
        window = view.window()
        if window and window.get_view_index(view)[1] != -1:
            cmd = sublime.load_settings(SETTINGS).get("sort_on_load_save_command", {})
            module = str(cmd.get("module", ""))
            reverse = bool(cmd.get("reverse", False))
            if module != "":
                window.run_command(
                    "tabs_extra_sort",
                    {"sort_by": module, "reverse": reverse}
                )
            sorted_views = True
        return sorted_views

    def on_pre_close(self, view):
        """
        If a view is closing without being marked, we know it was done outside of TabsExtra.

        Attach view and window info so we can focus the right view after close.
        """

        Focus.cancel()

        view.settings().set("tabs_extra_is_closed", True)
        if not view.settings().get("tabs_extra_closing", False):
            TabsExtraListener.extra_command_call = True
            window = view.window()
            if window is not None:
                view.settings().set("tabs_extra_view_info", view.window().get_view_index(view))
                view.settings().set("tabs_extra_window_info", view.window().id())
            else:
                TabsExtraListener.extra_command_call = False

    def on_close(self, view):
        """
        Handle focusing the correct view in window group.

        Close command was initiated outside of TabsExtra, so a focus is required.
        """

        view_info = view.settings().get("tabs_extra_view_info", None)
        window_info = view.settings().get("tabs_extra_window_info", None)
        if view_info is not None and window_info is not None:
            TabsExtraListener.extra_command_call = False

    def on_activated(self, view):
        """
        Timestamp each view when activated.

        Detect if on_move event should be executed.
        """

        if not TabsExtraListener.extra_command_call:
            window = view.window()
            if window is None:
                return
            s = window.active_sheet()
            timestamp_view(window, s)

        # Detect if tab was moved to a new group
        # Run on_move event if it has.
        moving = view.settings().get("tabs_extra_moving", None)
        if moving is not None:
            win_id, group_id = moving
            window = view.window()
            if window is None:
                return
            active_group = window.get_view_index(view)[0]
            if window.id() != win_id or int(group_id) != int(active_group):
                view.settings().erase("tabs_extra_moving")
        elif sort_on_load_save() and view.settings().get('tabsextra_to_sort'):
            view.settings().erase('tabsextra_to_sort')
            self.on_sort(view)


###############################
# Wrappers
###############################
class TabsExtraViewWrapperCommand(sublime_plugin.WindowCommand):
    """Wrapper for for executing certain commands from the tab context menu."""

    def run(self, command, group=-1, index=-1, args=None):
        """Wrap command in order to ensure view gets focused first."""

        if args is None:
            args = {}

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                self.window.focus_view(view)
                self.window.run_command(command, args)


###############################
# File Management Commands
###############################
class TabsExtraDeleteCommand(sublime_plugin.WindowCommand):
    """Delete the file."""

    def run(self, group=-1, index=-1):
        """Delete the tab's file."""

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                file_name = view.file_name()
                if file_name is not None and os.path.exists(file_name):
                    if sublime.ok_cancel_dialog("Delete %s?" % file_name, "Delete"):
                        if not view.close():
                            return
                        import Default.send2trash as send2trash  # noqa: N813
                        send2trash.send2trash(file_name)

    def is_visible(self, group=-1, index=-1):
        """Check if command should be visible."""

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None and view.file_name() is not None and os.path.exists(view.file_name()):
                enabled = True
        return enabled


class TabsExtraDuplicateCommand(sublime_plugin.WindowCommand):
    """Duplicate tab."""

    def run(self, group=-1, index=-1):
        """Rename the given tab."""

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                file_name = view.file_name()
                if file_name is not None and os.path.exists(file_name):
                    v = self.window.show_input_panel(
                        "Duplicate:", file_name,
                        lambda x: self.on_done(file_name, x),
                        None, None
                    )
                    file_path_len = len(file_name)
                    file_name_len = len(os.path.basename(file_name))
                    v.sel().clear()
                    v.sel().add(
                        sublime.Region(
                            file_path_len - file_name_len,
                            file_path_len
                        )
                    )

    def on_done(self, old, new):
        """Handle the tab duplication when the user is done with the input panel."""

        new_path = os.path.dirname(new)
        if os.path.exists(new_path) and os.path.isdir(new_path):
            if not os.path.exists(new) or sublime.ok_cancel_dialog("Overwrite %s?" % new, "Replace"):
                try:
                    with open(old, 'rb') as f:
                        text = f.read()

                    with open(new, 'wb') as f:
                        f.write(text)

                    self.window.open_file(new)
                except Exception:
                    sublime.status_message("Unable to duplicate")

    def is_visible(self, group=-1, index=-1):
        """Check if the command is visible."""

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None and view.file_name() is not None and os.path.exists(view.file_name()):
                enabled = True
        return enabled


class TabsExtraRenameCommand(sublime_plugin.WindowCommand):
    """Rename the tab's file."""

    def run(self, group=-1, index=-1):
        """Rename the given tab."""

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                file_name = view.file_name()
                if file_name is not None and os.path.exists(file_name):
                    branch, leaf = os.path.split(file_name)
                    v = self.window.show_input_panel(
                        "New Name:", leaf,
                        functools.partial(self.on_done, file_name, branch),
                        None, None
                    )
                    name = os.path.splitext(leaf)[0]
                    v.sel().clear()
                    v.sel().add(sublime.Region(0, len(name)))

    def on_done(self, old, branch, leaf):
        """Handle the renaming when user is done with the input panel."""

        new = os.path.join(branch, leaf)

        try:
            os.rename(old, new)

            v = self.window.find_open_file(old)
            if v:
                v.retarget(new)
        except Exception:
            sublime.status_message("Unable to rename")

    def is_visible(self, group=-1, index=-1):
        """Check if the command is visible."""

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None and view.file_name() is not None and os.path.exists(view.file_name()):
                enabled = True
        return enabled


class TabsExtraMoveCommand(sublime_plugin.WindowCommand):
    """Move the tab's file."""

    def run(self, group=-1, index=-1):
        """Move the file in the given tab."""

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                file_name = view.file_name()
                if file_name is not None and os.path.exists(file_name):
                    v = self.window.show_input_panel(
                        "New Location:", file_name,
                        functools.partial(self.on_done, file_name),
                        None, None
                    )
                    file_path_len = len(file_name)
                    file_name_len = len(os.path.basename(file_name))
                    v.sel().clear()
                    v.sel().add(
                        sublime.Region(
                            file_path_len - file_name_len,
                            file_path_len
                        )
                    )

    def on_done(self, old, new):
        """Handle the moving when user is done with the input panel."""

        try:
            directory = os.path.dirname(new)
            if not os.path.exists(directory):
                os.makedirs(directory)

            os.rename(old, new)

            v = self.window.find_open_file(old)
            if v:
                v.retarget(new)
        except Exception:
            sublime.status_message("Unable to move")

    def is_visible(self, group=-1, index=-1):
        """Check if the command is visible."""

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None and view.file_name() is not None and os.path.exists(view.file_name()):
                enabled = True
        return enabled


class TabsExtraRevertCommand(TabsExtraViewWrapperCommand):
    """Revert changes in file."""

    def is_visible(self, command, group=-1, index=-1, args=None):
        """Determine if command should be visible in menu."""

        if args is None:
            args = {}

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None and view.file_name() is not None:
                enabled = view.is_dirty()
        return enabled


class TabsExtraFileCommand(TabsExtraViewWrapperCommand):
    """Wrapper for file commands."""

    def is_enabled(self, command, group=-1, index=-1, args=None):
        """Determine if command should be enabled."""

        if args is None:
            args = {}

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                enabled = view.file_name() is not None
        return enabled


class TabsExtraFilePathCommand(sublime_plugin.WindowCommand):
    """Get file paths."""

    def run(self, group=-1, index=-1, path_type='path'):
        """Run the command."""

        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                self.window.focus_view(view)
                view.run_command('copy_path')
                pth = sublime.get_clipboard()
                if path_type == 'name':
                    pth = os.path.basename(pth)
                elif path_type == 'path_uri':
                    pth = urljoin('file:', pathname2url(pth))
                sublime.set_clipboard(pth)

    def is_enabled(self, group=-1, index=-1, path_type='path'):
        """Determine if command should be enabled."""

        enabled = False
        if group >= 0 and index >= 0:
            view = get_group_view(self.window, group, index)
            if view is not None:
                enabled = view.file_name() is not None
        return enabled


###############################
# Sort
###############################
class TabsExtraSortMenuCommand(sublime_plugin.WindowCommand):
    """Sort tabs."""

    def run(self):
        """Using "sort_layout" setting, construct a quick panel sort menu."""

        sort_layout = sublime.load_settings(SETTINGS).get("sort_layout", [])
        if len(sort_layout):
            self.sort_commands = []
            sort_menu = []
            for sort_entry in sort_layout:
                caption = str(sort_entry.get("caption", ""))
                module = str(sort_entry.get("module", ""))
                reverse = bool(sort_entry.get("reverse", False))
                if module != "":
                    self.sort_commands.append((module, reverse))
                    sort_menu.append(caption)
            if len(sort_menu):
                self.window.show_quick_panel(sort_menu, self.check_selection)

    def check_selection(self, value):
        """Launch the selected sort command."""

        if value != -1:
            command = self.sort_commands[value]
            self.window.run_command("tabs_extra_sort", {"sort_by": command[0], "reverse": command[1]})


class TabsExtraSortCommand(sublime_plugin.WindowCommand):
    """Sort tabs."""

    def run(self, group=-1, sort_by=None, reverse=False):
        """Sort Tabs."""

        if sort_by is not None:
            if group == -1:
                group = self.window.active_group()
            self.group = group
            self.reverse = reverse
            views = self.window.views_in_group(int(group))
            if len(views):
                sort_module = self.get_sort_module(sort_by)
                if sort_module is not None:
                    view_data = []
                    sort_module.run(views, view_data)
                    self.sort(view_data)
                    self.window.focus_view(self.window.active_view())

    def sort(self, view_data):
        """Sort the views."""

        indexes = tuple([x for x in range(0, len(view_data[0]) - 1)])
        sorted_views = sorted(view_data, key=itemgetter(*indexes))
        if self.reverse:
            sorted_views = sorted_views[::-1]
        if sorted_views != view_data:
            for index in range(0, len(sorted_views)):
                self.window.set_view_index(sorted_views[index][-1], self.group, index)

    def get_sort_module(self, module_name):
        """Import the sort_by module."""

        import imp
        path_name = os.path.join("Packages", os.path.normpath(module_name.replace('.', '/')))
        path_name += ".py"
        module = imp.new_module(module_name)
        sys.modules[module_name] = module
        exec(
            compile(
                sublime.load_resource(sublime_format_path(path_name)),
                module_name, 'exec'
            ),
            sys.modules[module_name].__dict__
        )
        return module


###############################
# Menu Installation
###############################
class TabsExtraInstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    """Install TabsExtra menu overriding the default tab context menu."""

    def run(self):
        """Install/upgrade the override tab menu."""

        msg = OVERRIDE_CONFIRM
        if sublime.ok_cancel_dialog(msg):
            tab_menu.upgrade_override_menu()


class TabsExtraUninstallOverrideMenuCommand(sublime_plugin.ApplicationCommand):
    """Uninstall the TabsExtra override menu."""

    def run(self):
        """Uninstall the override tab menu."""

        msg = RESTORE_CONFIRM
        if sublime.ok_cancel_dialog(msg):
            tab_menu.uninstall_override_menu()


class TabsExtraInstallMenuCommand(sublime_plugin.ApplicationCommand):
    """Install the TabsExtra menu by appending it to the existing tab context menu."""

    def run(self):
        """Install/upgrade the standard tab menu."""

        tab_menu.upgrade_default_menu()


###############################
# Plugin Loading
###############################
def plugin_loaded():
    """Handle plugin setup."""

    win = sublime.active_window()
    if win is not None:
        sheet = win.active_sheet()
        if sheet is not None:
            timestamp_view(win, sheet)
