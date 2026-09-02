# Stage 16 — Custom Home Sections and Universal Home Items

Baseline: device-confirmed DW File Manager v9109005+ runtime and association model.

## Required Home customization

- Create custom Home sections.
- Rename custom sections.
- Delete custom sections.
- Reorder sections.
- Move Home items between sections.
- Reorder items inside a section.
- Hide/remove items from Home without deleting the underlying file/app/location.
- Restore the stock/default Home layout.
- Persist the complete Home layout locally.

## First-class Home item types

One Home model must support all of these rather than separate shortcut systems:

1. `folder`
   - existing folder/bookmark behavior
   - tap navigates to the folder

2. `file`
   - any normal file can be added to Home/bookmarks just like a folder
   - preserve normal file icon/type presentation
   - tap routes through DW's normal file-open dispatcher, including exact-extension preferred-app associations
   - moved/deleted targets fail gracefully and offer stale-item cleanup

3. `app`
   - identify by package name, not install path/version
   - resolve current app label/icon dynamically
   - tap launches the app's normal launch activity
   - stale item is removable automatically after uninstall

4. `app_activity`
   - identify by package name + fully qualified Activity class (`ComponentName`)
   - resolve label/icon dynamically where available
   - allow custom Home tile name/icon override later without changing the target
   - tap launches an explicit Intent directly into the stored Activity
   - external apps: only enabled/exported Activities that Android permits DW to launch can be offered reliably
   - DW's own internal Activities may also be represented directly
   - stale targets fail gracefully and offer cleanup

## UI entry points

- Folder context menu: Add to Home / Remove from Home.
- File context menu: Add to Home / Remove from Home.
- Apps area: Add app to Home / Remove from Home.
- Apps area: Activities browser -> Add activity shortcut to Home.
- Home edit mode: Move, reorder, rename, remove, change section, and create/delete sections.

## Non-regression rules

- Existing folder bookmarks remain compatible.
- File Home items must use the same validated file association/open-with behavior as ordinary file taps.
- Adding Home customization must not alter the underlying filesystem object or installed application.
- Do not require root or accessibility for activity shortcuts.
