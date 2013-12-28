TabsExtra
=========

Sublime Plugin with sticky tabs and more tab closing options.  ST3 is the only **officially** supported platform.

# Features

- Adds `Close Tabs to the Left`
- Adds `Close All Tabs`
- Adds `Sticky Tabs` that allows a user select certain tabs that will not close when a tab close command is issued.
- Overrides the built-in tab commands to work with sticky tabs (ST3 only)

# Sticky Tab Settings
By default, after any `Close` command is run, all `Sticky` tab properties are forgotten.  You can make a tab's `Stickiness` persist by enabling the following setting:

```javascript
    "persistent_sticky": false,
```

# Tab Context Menu Options
By default, the commands won't be grouped together because of the way Sublime Text menus are managed.  But you can optionally install a menu that overrides the Default Package's tab context menu for sane grouping of the commands.

# ST2 Support?
ST2 support is not officially complete.  For best functionality, it is recommended to install the override menu for the Default tab context menu.

Sublime Text 2 will pop up a warning reminding you that ST2 support is not final.  You can disable it in the settings file by adding this setting:

```javascript
    "st2_warning_enabled": false
```
