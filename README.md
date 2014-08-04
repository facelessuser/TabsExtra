TabsExtra
=========
<img src="https://dl.dropboxusercontent.com/u/342698/TabsExtra/Menu.png" border="0"/>

Sublime Plugin with sticky tabs, more tab closing options, tab sorting, and tab access to cloning, deleting, renaming etc.  ST3 is the only supported platform.

# Features

- Adds `Close Tabs to the Left` for the current group
- Adds `Close All Tabs` for the current group
- Adds `Sticky Tabs` that allows a user select certain tabs that will not close when a tab close command is issued.
- Adds variants of the close commands to skip unsaved files, or to dismiss saved files with no prompt
- Overrides the built-in tab commands and 'close' and 'close_all' commands to work with sticky tabs (ST3 only)
- Keep active window focus on delete, or default to the last active, left, or right tab (user configurable)
- Add open last tab, reveal in sidebar or finder, copy file path, save options, and revert
- Adds tab sorting options (based loosely on @bizoo's [SortTabs](https://github.com/bizoo/SortTabs) plugin)
- Access clone, delete, rename, save, reveal, copy file path, revert, etc.

# Which Commands does TabsExtra Override?
TabsExtra does **not** override `close_file`, but it does override the following:

- `close_by_index`: close view from tab
- `close`: close active view from global menu
- `close_all`: close all tabs in all groups
- `close_others_by_index`: close other tabs in current group
- `close_to_right_by_index` close tabs to right in current group

# What TabsExtra Cannot Do
TabsExtra **cannot** override the tab close button.  But it should be able to predict when it is pressed, and focus the appropriate window after the close.

# Sticky Tab Settings
By default, after any `Close` command is run, all `Sticky` tab properties are forgotten.  You can make a tab's `Stickiness` persist by enabling the following setting:

```javascript
    "persistent_sticky": false,
```

# Tab Focus After Close
By default TabsExtra keeps the current active tab focused, but if the active tab gets deleted, TabsExtra will default to either the left, right, or last active tab (depending how the user has it set).

```javascript
    // If active window gets closed, default to (left|right|last_active)
    "fallback_focus": "right"
```

# Customize Tab Context Menu
The tab menu adds a number of times.  Each item group can be re-ordered, or excluded if desired via the settings file.

```javascript
    // Menu layout include or exclude, in whatever order you desire, the following options:
    // ["close", "sticky", "open", "clone", "save", "delete", "rename", "reveal", "path", "revert", "sort"]
    // When done, go to Preferences->Package Settings->TabsExtra and Install/Upgrade either
    // the default TabsMenu or the Override Menu which overrides the "Default" package's menu.
    "menu_layout": ["close", "sticky", "open", "clone", "save", "delete", "rename", "reveal", "path", "revert", "sort"],
```

Sort options are also configurable:

```javascript
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
    "numeric_sort": false
```

# Tab Context Menu Options
By default, the commands won't be grouped together with the built-in options because of the way Sublime Text menus are managed.  But you can optionally install a menu that overrides the Default Package's tab context menu for sane grouping of the commands.

# ST2 Support?
Sorry, there are no plans for ST2 support.

# License

TabsExtra is released under the MIT license.

Copyright (c) 2014 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
