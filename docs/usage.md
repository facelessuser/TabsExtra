# Usage
Using TabsExtra is very straight forward once the menu is created.  TabsExtra will update the right click context menu of tabs with various useful features.  It also a couple of Sublime's commands to allow for various improvements in relation to tab focus when closing files, tab postion when opening files, and making available new useful close commands.

## Install/Upgrade Menu
When first installing TabsExtra, you need to Install the new menu; this does not happen automatically.  Go to `Preferences->Package Settings->TabsExtra` and Install/Upgrade either the **basic** tab menu or the **override** menu. The **basic** menu's commands won't be grouped together with the built-in options because of the way Sublime Text's menus are managed.  But the **override** menu overrides the **Default** Package's tab context menu for sane, clean grouping of the commands.

## Which Commands does TabsExtra Override?
TabsExtra does **not** override `close_file`, but it does override the following:

- `close_by_index`: close view from tab
- `close`: close active view from global menu
- `close_all`: close all tabs in all groups
- `close_others_by_index`: close other tabs in current group
- `close_to_right_by_index` close tabs to right in current group

## What TabsExtra Cannot Do
TabsExtra **cannot** override the tab close button.  But it should be able to predict when it is pressed, and focus the appropriate window after the close.

## Sticky Tab Settings
By default, after any `Close` command is run, all `Sticky` tab properties are forgotten.  You can make a tab's `Stickiness` persist by enabling the following setting:

```javascript
    "persistent_sticky": false,
```

## Tab Focus After Close
By default TabsExtra keeps the current active tab focused, but if the active tab gets deleted, TabsExtra will default to either the left, right, or last active tab (depending how the user has it set).

```javascript
    // If active window gets closed, default to (left|right|last_active)
    "fallback_focus": "right"
```

## Tab Spawn Position
TabsExtra can control where a new window is opened with the `spawn_view` settings option.

```js
    // Experimental: When opening a view, where should it be spawned at (none|left|active_left|active_right|right)
    "spawn_view": "none",
```

## Tab Sort
TabsExtra adds various sort options to the tab context menu.  You can control which sort options appear and even configure a specific sort command to run when a file is saved in the settings file.  You can also adjust how numbers in strings are sorted.

```js
    // Define sort layout.  Each entry contains:
    //    "module": plugin that defines what view meta data is used to sort
    //    "caption": menu name for entry
    //    "reverse": (optional) sort tabs in the reverse (true|false)
    "sort_layout": [
        {"module": "TabsExtra.sort.name", "caption": "Name"},
        {"module": "TabsExtra.sort.path", "caption": "Path"},
        {"module": "TabsExtra.sort.modified", "caption": "Modified"},
        {"module": "TabsExtra.sort.created", "caption": "Created"},
        {"module": "TabsExtra.sort.type", "caption": "Extension"},
        {"module": "TabsExtra.sort.size", "caption": "Size"},
        {"module": "TabsExtra.sort.activated", "caption": "Last Activated"},
        {"module": "TabsExtra.sort.syntax", "caption": "Syntax"},
        {"module": "TabsExtra.sort.reverse", "caption": "Reverse Order"}
    ],
    // When sorting, normal strings will be sorted numerically.
    //
    // Example (non-numerical sort):
    //   test12 test2 test1 => test1 test12 test2
    //
    // Example (numerical sort):
    //   test12 test2 test1 => test1 test2 test12
    "numeric_sort": false,

    // Sort tabs when a file is opened or saved
    "sort_on_load_save": false,

    // Sort module to use when sorting on load and save
    //    "module": plugin that defines what view meta data is used to sort
    //    "reverse": (optional) sort tabs in the reverse (true|false)
    "sort_on_load_save_command": {"module": "TabsExtra.sort.name"}
```

Sort options are actually provided by small sort modules.  As seen above, sort modules are specified in the settings file like you are importing a python module.  The package folder would be the root of the module and would then be followed by the subfolders and the actual module name; all would be separated with dots.  As shown above, TabsExtra comes with 9 different sort modules: name, path, modified, created, type, size, activated, syntax, reverse.  If these modules do not suit your needs, you can right your own.

Within a sort module, there must be a run method as shown above below:

def run(views, view_data)
: 
    This function takes a list of `views` and an empty list to append sort data to.  The `view_data` is populated by the `run` function with arrays of formatted info that will be used to sort the tabs.  Info with the most importance should be appended first.

    If you are dealing with strings that have numbers, and you wish to sort them numerically, you can import the numeric helper with the following import: `#!python from TabsExtra import tab_sort_helper as tsh`.  Once imported you can simply run your data through the `tab_sort_helper`: `#!python tsh.numeric_sort(dirname(v.file_name() if v.file_name() else '')`.

    **Parameters**:

    | Parameter | Description |
    |-----------|-------------|
    | views     | List of Sublime view objects. |
    | view_data | An empty list that should be populated by the function with relevant sort data. |

    Example module:

    ```
    from os.path import dirname, basename
    from TabsExtra import tab_sort_helper as tsh


    def run(views, view_data):
        for v in views:
            view_data.append(
                (
                    tsh.numeric_sort(dirname(v.file_name() if v.file_name() else '').lower()),
                    tsh.numeric_sort(basename(v.file_name() if v.file_name() else '').lower()),
                    v
                )
            )
    ```

# Additional Menu Helper Commands
TabsExtra also adds a number of other miscellaneous useful tab context commands that can open recently tabs, delete tabs from the disk, rename the current file, reveal the the tab's file in the sidebar or file manager, retrieve the file path, and revert unsaved changes.

# Customize Tab Context Menu
The tab menu adds a number of times.  Each item group can be re-ordered, or excluded if desired via the settings file.

```javascript
    // Menu layout include or exclude, in whatever order you desire, the following options:
    // ["close", "sticky", "open", "clone", "save", "delete", "rename", "reveal", "path", "revert", "sort"]
    // When done, go to Preferences->Package Settings->TabsExtra and Install/Upgrade either
    // the default TabsMenu or the Override Menu which overrides the "Default" package's menu.
    "menu_layout": ["close", "sticky", "open", "clone", "save", "delete", "rename", "reveal", "path", "revert", "sort"],
```
