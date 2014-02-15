TabsExtra
=========
<img src="https://dl.dropboxusercontent.com/u/342698/TabsExtra/tabs_extra.png" border="0"/>

Sublime Plugin with sticky tabs and more tab closing options.  ST3 is the only supported platform.

# Features

- Adds `Close Tabs to the Left` for the current group
- Adds `Close All Tabs` for the current group
- Adds `Sticky Tabs` that allows a user select certain tabs that will not close when a tab close command is issued.
- Overrides the built-in tab commands and 'close' and 'close_all' commands to work with sticky tabs (ST3 only)
- Keep active window focus on delete, or default to left or right tab (user configurable)

# Which Commands does TabsExtra Override?
TabsExtra does **not** override `close_file`, but it does override the following:

- `close_by_index`: close view from tab
- `close`: close active view from global menu
- `close_all`: close all tabs in all groups
- `close_others_by_index`: close other tabs in current group
- `close_to_right_by_index` close tabs to right in current group

# Sticky Tab Settings
By default, after any `Close` command is run, all `Sticky` tab properties are forgotten.  You can make a tab's `Stickiness` persist by enabling the following setting:

```javascript
    "persistent_sticky": false,
```

# Tab Focus After Close
By default TabsExtra keeps the current active tab focused, but if the active tab gets deleted, TabsExtra will default to either the next left or right tab (depending how the user has it set).

```javascript
    // If active window gets closed, default to (left|right)
    "fallback_focus": "right"
```

# Tab Context Menu Options
By default, the commands won't be grouped together because of the way Sublime Text menus are managed.  But you can optionally install a menu that overrides the Default Package's tab context menu for sane grouping of the commands.

# ST2 Support?
Sorry, there are no plans for ST2 support.
