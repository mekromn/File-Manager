# DW File Manager — LauncherEx dual feed host

## Purpose

Expose two **existing DW File Manager screens** to LauncherEx without cloning or forking their behavior:

1. DW Home
2. DW Recently Updated

This integration does not modify Android system Recents/Overview.

## Exact current runtime donor

Integration work is validated against the user's current DW runtime artifact:

- `DW-File-Manager_9.1.0.8_v9109040_SHIZUKU_FULL_FILE_IO_DYNAMIC_UI_TEST.apk`
- SHA-256 `f90b74762eed69cf6bd69960fa53b865b0e1e0dd4af185fb76974eaf6ce1b42f`
- package `com.mekromn.dwfilemanager`

The checked-in repo continues to store transformation logic/specification rather than decompiled proprietary source.

## Existing authoritative screen implementations

### Home

- manager: `dw.filemanager.ui.homecontent.HomeContentView$Manager`
- manager id/action: `home` / `action_home`
- view: `dw.filemanager.ui.homecontent.HomeContentView`

This is the screen containing Bookmarks, Files, Media, Internet and Network, Utilities and the user's customized DW Home sections/items.

### Recently Updated

- manager: `dw.filemanager.ui.search.RecentFileContentView$Manager`
- id: `recently_updated`
- catalog: current `jb.d.k`
- content instance in v9109040: current recent-file implementation (`hg.s` after R8)

This is the screen containing the All/Docs/Text/Image/Music/Video/App/Archive/Folder filter strip and date-grouped recently-updated file list.

## Host design

The feed bridge must preserve DW ownership of the screen:

- Do not duplicate Home models, Recent query logic, sorting, filters, thumbnails, menu actions or file operations inside LauncherEx.
- DW creates/owns the real page view and controller.
- LauncherEx owns only the feed-page container/lifecycle.
- Prefer public Android cross-process view embedding (`SurfaceControlViewHost` + `SurfacePackage`) so DW remains a separate installed app while its real views render interactively inside LauncherEx.
- Add a minimal exported explicit Binder service in DW restricted at runtime to the LauncherEx package/UID.
- The service exposes page creation for `home` and `recently_updated`, resize/lifecycle callbacks and cleanup.
- No generic exported file-operation IPC API is added.
- Existing DW ExplorerActivity remains independently launchable and unchanged outside feed-host mode.

If a real DW content manager requires ExplorerActivity services that cannot safely run in a pure service-hosted view, add a dedicated DW feed-host Activity/controller that reuses the same manager/content classes rather than reproducing their logic.

## State

- Both LauncherEx feed pages point to the same installed DW app and preferences/filesystem state.
- Page-local scroll/navigation state may be distinct so Home and Recently Updated can each resume where left.
- Underlying Home customization, bookmarks and filesystem changes remain shared with standalone DW.

## Security

- Feed service is explicit and accepts only LauncherEx callers after UID/package verification.
- No new network transport.
- No account or telemetry channel.
- No accessibility, root, Shizuku or overlay permission is required merely to render the feed pages.
- Existing DW Shizuku functionality remains available only through DW's own existing authorization model.

## Non-regression

- Standalone DW behavior unchanged with feed host unused.
- Existing file-open associations, Home customization, Shizuku filesystem access, picker behavior and themes remain DW-owned.
- LauncherEx feed integration must not introduce a second copy of DW's state/database.
