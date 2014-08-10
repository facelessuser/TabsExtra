"""
TabsExtra

Copyright (c) 2014 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import sublime_plugin
from os.path import join, exists
from os import makedirs, remove
import json
from .lib.file_strip.json import sanitize_json
import codecs

__format__ = "1.4.0"
__changes__ = [
    "Fix indexing for when image preview tabs are open.",
    "Rename TabExtra and TabExtraAll to TabExtraClose and TabExtraCloseAll"
]

PACKAGE_NAME = "TabsExtra"
DEFAULT_PACKAGE = "Default"
SETTINGS = "tabs_extra.sublime-settings"
TAB_MENU = "Tab Context.sublime-menu"
VERSION_FILE = "version.json"
FORMAT_VERSION = {
    "version": __format__,
    "override": False
}

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
%(changes)s
''' % {"format": __format__, "changes": '\n'.join(["- %s" % change for change in __changes__])}

###############################
# Menu Options
###############################
CLOSE_OPTIONS = '''    { "caption": "-"},
%(override)s
    { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "left" }, "caption": "Close Tabs to the Left" },
    { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "all" }, "caption": "Close All Tabs" },
    {
        "caption": "Close Tabs(s) - Skip Unsaved",
        "children":
        [
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "single", "close_unsaved": false }, "caption": "Close" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "other", "close_unsaved": false }, "caption": "Close Other Tabs" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "right", "close_unsaved": false }, "caption": "Close Tabs to the Right" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "left", "close_unsaved": false }, "caption": "Close Tabs to the Left" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "all", "close_unsaved": false }, "caption": "Close All Tabs" }
        ]
    },
    {
        "caption": "Close Tabs(s) - Dismiss Unsaved",
        "children":
        [
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "single", "unsaved_prompt": false }, "caption": "Close" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "other", "unsaved_prompt": false }, "caption": "Close Other Tabs" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "right", "unsaved_prompt": false }, "caption": "Close Tabs to the Right" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "left", "unsaved_prompt": false }, "caption": "Close Tabs to the Left" },
            { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "all", "unsaved_prompt": false }, "caption": "Close All Tabs" }
        ]
    }'''

STICKY_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_toggle_sticky", "args": { "group": -1, "index": -1 }, "caption": "Sticky Tab" },
    { "command": "tabs_extra_clear_all_sticky", "args": { "group": -1, "force": true }, "caption": "Clear All Sticky Tabs" }'''

SAVE_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_view_wrapper", "args": {"group": -1, "index": -1, "command": "save"}, "caption": "Save" },
    { "command": "tabs_extra_view_wrapper", "args": {"group": -1, "index": -1, "command": "prompt_save_as"}, "caption": "Save As…" },
    { "command": "save_all", "caption": "Save All" }'''

CLONE_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_view_wrapper", "args": {"group": -1, "index": -1, "command": "clone_file"}, "caption": "Clone" }'''

OPEN_OPTIONS = '''    { "caption": "-" },
%(override)s
    { "command": "reopen_last_file", "caption": "Reopen Last Tab" }'''

REVEAL_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_file", "args": {"group": -1, "index": -1, "command": "open_dir", "args": {"dir": "$file_path", "file": "$file_name"}}, "caption": "Open Containing Folder…" },
    { "command": "tabs_extra_file", "args": {"group": -1, "index": -1, "command": "reveal_in_side_bar"}, "caption": "Reveal in Side Bar" }'''

PATH_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_file", "args": {"group": -1, "index": -1, "command": "copy_path"}, "caption": "Copy File Path" }'''

REVERT_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_revert", "args": {"group": -1, "index": -1, "command": "revert"}, "caption": "Revert File" }'''

DELETE_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_delete", "args": {"group": -1, "index": -1}, "caption": "Delete File" }'''

RENAME_OPTIONS = '''    { "caption": "-" },
    { "command": "tabs_extra_rename", "args": {"group": -1, "index": -1}, "caption": "Rename…" }'''

SORT_OPTIONS = '''    { "caption": "-" },
    {
        "caption": "Sort Tabs By…",
        "children":
        [
%(entries)s
        ]
    }'''

SORT_ENTRY = '            { "command": "tabs_extra_sort", "args": {"group": -1, "sort_by": "%(sort_by)s", "reverse": %(reverse)s}, "caption": "%(caption)s" }'

###############################
# Override Menu Options
###############################
OVERRIDE_CLOSE_OPTIONS = '''    { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "single" }, "caption": "Close" },
    { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "other" }, "caption": "Close Other Tabs" },
    { "command": "tabs_extra_close", "args": { "group": -1, "index": -1, "close_type": "right" }, "caption": "Close Tabs to the Right" },'''

OVERRIDE_OPEN_OPTIONS = '''    { "command": "new_file", "caption": "New File" },
    { "command": "prompt_open_file", "caption": "Open File" },'''


MENU_MAP = {
    "clone": CLONE_OPTIONS,
    "close": CLOSE_OPTIONS,
    "delete": DELETE_OPTIONS,
    "open": OPEN_OPTIONS,
    "path": PATH_OPTIONS,
    "rename": RENAME_OPTIONS,
    "reveal": REVEAL_OPTIONS,
    "revert": REVERT_OPTIONS,
    "save": SAVE_OPTIONS,
    "sort": SORT_OPTIONS,
    "sticky": STICKY_OPTIONS
}

OVERRIDE_MAP = {
    "close": OVERRIDE_CLOSE_OPTIONS,
    "open": OVERRIDE_OPEN_OPTIONS
}


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


def get_menu(override=False):
    """
    Return the formatted tab menu.
    """

    default_layout = ["close", "sticky", "open", "clone", "save", "delete", "rename", "reveal", "path", "revert", "sort"]
    layout = sublime.load_settings(SETTINGS).get("menu_layout", default_layout)
    entries = []
    for entry in layout:
        if entry in MENU_MAP:
            if entry in OVERRIDE_MAP:
                entries.append(MENU_MAP[entry] % {"override": OVERRIDE_MAP[entry] if override else ''})
                continue
            if entry == "sort":
                sort_layout = sublime.load_settings(SETTINGS).get("sort_layout", [])
                if len(sort_layout):
                    sort_entries = []
                    for sort_entry in sort_layout:
                        sort_entries.append(
                            SORT_ENTRY % {
                                "sort_by": sort_entry.get("module", ""),
                                "caption": sort_entry.get("caption", ""),
                                "reverse": str(bool(sort_entry.get("reverse", False))).lower()
                            }
                        )
                    item = MENU_MAP[entry] % {"entries": ',\n'.join(sort_entries)}
            else:
                item = MENU_MAP[entry]
            entries.append(item)

    return "[\n%s\n]\n" % (',\n'.join(entries))


def upgrade_override_menu():
    """
    Install/Upgrade the override menu.
    """

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
    with codecs.open(default_menu, "w", "utf-8") as f:
        f.write(get_menu(override=True))
    with open(version_file, "w") as f:
        FORMAT_VERSION["override"] = True
        f.write(json.dumps(FORMAT_VERSION, sort_keys=True, indent=4, separators=(',', ': ')))


def uninstall_override_menu():
    """
    Uninstall the override menu.  Re-install the default TabsExtra menu.
    """

    default_path = join(sublime.packages_path(), "Default")
    default_menu = join(default_path, TAB_MENU)
    if exists(default_menu):
        remove(default_menu)
    upgrade_default_menu()


def upgrade_default_menu():
    """
    Install/upgrade the standard tab menu.
    """

    menu_path = join(sublime.packages_path(), "User", PACKAGE_NAME)
    menu = join(menu_path, TAB_MENU)
    version_file = join(menu_path, VERSION_FILE)
    if not exists(menu_path):
        makedirs(menu_path)
    with codecs.open(menu, "w", "utf-8") as f:
        f.write(get_menu())
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
