# LauncherEx × DW dual feed V10 — display input + never-black recovery

## Device failures driving V10

DW V9 was visually usable, but device testing exposed two related correctness failures:

1. Popup/menu taps could pass through the visible menu and activate the file underneath it.
2. Finishing internal viewers (image, binary, text, etc.) could leave the feed SurfaceView black after Back.

Both are consequences of treating the feed as only a root `ExplorerActivity` rather than a complete Android display/task/window stack.

## V10 correction

### Display-level input routing

V9 forwarded each Messenger MotionEvent directly to the root `ExplorerActivity.dispatchTouchEvent()`. That bypasses Android's window input dispatcher, so a PopupWindow, Dialog, or child viewer can be visually topmost while the root activity still receives the tap underneath it.

V10 removes that fallback entirely. A Shizuku UserService runs as shell UID and injects the original MotionEvent at the feed virtual-display level through `InputManagerGlobal` in asynchronous mode. The event display id is rewritten to the session VirtualDisplay id before injection. Android then performs ordinary hit testing/window focus routing and sends the event to the actual topmost DW window.

If the privileged input bridge is not ready, V10 drops the sample and requests a rebind. It never falls back to root-Activity dispatch, because a lost sample is safer than a click-through.

The initial feed READY message is delayed until the input UserService binder is alive; a failure becomes a visible `input_bridge_timeout` rather than a partially interactive feed.

### Never-black task recovery

V10 registers an Application `ActivityLifecycleCallbacks` tracker for activities on each feed display. The currently resumed top DW activity is stored per feed Session.

When a finishing/destroyed viewer pauses, V10 schedules a 16 ms recovery check. If the feed display no longer has a resumed DW activity, it asks Shizuku to bring the existing root `DwFeedActivity` task forward on that same display with:

`NEW_TASK | CLEAR_TOP | SINGLE_TOP | NO_ANIMATION`

This preserves the existing root when it is alive and recreates it only when necessary. Recovery retries are bounded. If the display still cannot recover, the session sends `activity_recovery_failed` and tears down cleanly so LauncherEx can show a visible host error instead of leaving a silent black SurfaceView.

## Isolation

LauncherEx is not changed by DW V10. It is intended to pair with LauncherEx V7 (which keeps the V6/V3 SurfaceView + gesture architecture and adds Home-layer restoration).

V9 -> V10 payload-content audit, excluding regenerated APK signature metadata: **only `classes2.dex` changes**. Manifest, resources, primary DEX, native libraries, package, version and signing identity are unchanged.

Exact candidate:

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V10_DISPLAY_INPUT_NEVER_BLACK.apk`

APK SHA-256: `555be82378b7d215891a7edb688b82d9d82842ab853e6ca24e7c6c87e18f36f0`

`classes2.dex` SHA-256: `916d3d194125ab0e24a72cbfcf6105f64ce85f6f939e0efdc5b03eedb2601d85`

Package/version remain `com.mekromn.dwfilemanager`, `versionCode 9109040`, `versionName 9.1.0.8`.

Signer SHA-256 remains `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`; v1/v2/v3 verification passes.

The rebuilt classes2 DEX has valid DEX SHA-1/Adler32 headers and survives a byte-identical baksmali/smali 3.0.10 round trip.

## Device acceptance

- Popup/menu items receive the tap; the file underneath never activates.
- Dialogs and internal viewers receive input normally.
- Image/binary/text viewer -> Back always returns to a live DW feed.
- Repeated viewer open/back cycles never leave a black feed.
- Root Back cannot strand the VirtualDisplay with no foreground DW window.
- Vertical scroll/fling and ordinary taps remain responsive.
- Shizuku interruption produces a visible/recoverable feed error rather than unsafe root click-through.
