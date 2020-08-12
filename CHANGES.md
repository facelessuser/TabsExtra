# TabsExtra

## 1.6.1

- **NEW**: Regression due to reference to now retired function.

## 1.6.0

- **NEW**: Features for `fallback_focus` and `spawn_view` have been removed. These features were problematic and often
  caused issues with selection of files in the sidebar.
- **NEW**: `sort_on_load_save` will only apply if the Sublime setting `preview_on_click` is disabled. This is to prevent
  issues focusing when selecting files in the sidebar.
- **NEW**: Sticky tabs will only protect a tab on bulk close. This provides consistency as we have no way to stop single
  tabs close via tab close buttons; therefore, we won't stop a tab from closing when the user explicitly calls close
  on just that tab.

## 1.5.3

- **FIX**: Fix issue where sometimes when moving, active tabs are no longer flagged with timestamps.

## 1.5.2

- **FIX**: Fix issue where override commands were not always properly getting overridden.

## 1.5.1

- **FIX**: Fix view index issue.
- **FIX**: Make upgrade message a little more clear about menu installation differences.

## 1.5.0

- **NEW**: Add documentation and settings command to the command palette.
- **NEW**: File URI path copy.

## 1.4.0

- **NEW**: New support commands.
- **NEW**: Use latest settings API when viewing settings.
- **FIX**: `window` referenced before assignment.
