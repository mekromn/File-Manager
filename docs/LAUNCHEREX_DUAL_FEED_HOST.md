# DW File Manager — LauncherEx dual feed host

## Purpose

Expose two **existing DW File Manager screens** to LauncherEx without cloning or forking their behavior:

1. DW Home (`home`)
2. DW Recently Updated (`recently_updated`)

This integration does not modify Android system Recents/Overview.

## Current runtime donor

- `DW-File-Manager_9.1.0.8_v9109040_SHIZUKU_FULL_FILE_IO_DYNAMIC_UI_TEST.apk`
- package `com.mekromn.dwfilemanager`
- versionCode `9109040`

## Authoritative screens

### Home

- manager: `dw.filemanager.ui.homecontent.HomeContentView$Manager`
- manager id/action: `home` / `action_home`
- view: `dw.filemanager.ui.homecontent.HomeContentView`

### Recently Updated

- manager: `dw.filemanager.ui.search.RecentFileContentView$Manager`
- id: `recently_updated`
- catalog: `jb.d.k`
- current recent content implementation remains DW-owned

## V1 device result — rejected transport

The first device candidate successfully exposed LauncherEx's two feed toggles and page surface, but the user's 2026-09-09 screen recording showed both DW Home and DW Recently Updated as black pages.

V1's fragile seam was cross-display view-tree re-parenting: a real `ExplorerActivity` was launched on a private virtual display, then its root view was detached and placed into `SurfaceControlViewHost` for LauncherEx.

Because both independent DW page IDs failed identically, the page implementations are not redesigned in V2. The shared render transport is replaced.

## V2 host design — direct virtual-display output

V2 keeps the **real ExplorerActivity/window/view hierarchy intact**.

1. LauncherEx creates a normal `SurfaceView` for each enabled DW feed page.
2. LauncherEx binds explicitly to `dw.filemanager.feed.DwFeedService` and sends that Surface plus size/density and page ID.
3. DW creates a private `VirtualDisplay` with `VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY | VIRTUAL_DISPLAY_FLAG_PRESENTATION` and uses the LauncherEx Surface directly as the display output.
4. DW starts `DwFeedActivity extends ExplorerActivity` on that display.
5. Once the real ExplorerActivity is ready, DW calls its existing navigation method with `home` or `recently_updated`.
6. No DW view is detached or re-parented. The Activity draws normally into its own Window, and Android composites that display straight into LauncherEx's SurfaceView.
7. LauncherEx forwards `MotionEvent` copies through the explicit Messenger service; DW dispatches them to the actual ExplorerActivity.
8. Child Activities intentionally launch on the physical default display so opening a document/editor/settings surface behaves like normal DW instead of remaining trapped on the feed display.

## Diagnostics

The V2 protocol returns explicit failure phases to LauncherEx. The feed page displays these strings instead of an unexplained black surface, including:

- `bad_request`
- `create_failed:<Exception>`
- `activity_timeout`
- `activity_ready_failed:<Exception>`
- `navigate_failed:<Exception>`
- `ready_failed:<Exception>`

This makes the next Pixel/Android 16 test actionable without requiring logcat for the first failure boundary.

## Security

- The service is explicit.
- Every incoming Message validates `Message.sendingUid` and requires the UID's package list to contain `dev.launcherex`.
- IPC is limited to feed session creation/close, a client Surface, page selection, dimensions and touch events.
- No generic exported file-operation API is added.
- No network transport, accessibility or overlay permission is introduced by the feed host.
- Existing DW Shizuku functionality remains under DW's existing authorization model.

## V2 artifact

- `DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V2.apk`
- SHA-256 `c0d87c58905dc37ff66881b69a34e55aca569fa764374f54167355867696f431`
- versionCode `9109040`
- signer SHA-256 `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`
- `classes.dex` is unchanged from the current DW runtime; V2 host code is isolated to `classes2.dex`.

## Source

Original integration code is kept under:

`experiments/launcherex-dual-feed/v2/dw/filemanager/feed/`

Standalone DW behavior remains authoritative and independently launchable.
