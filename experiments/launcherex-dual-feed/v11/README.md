# LauncherEx × DW dual feed V11 — external-safe never-black recovery

## Device failure driving V11

DW V10 fixed root-Activity click-through by moving feed input to Android's display-level dispatcher, and added proactive recovery for black states. Device testing then exposed a regression: opening an APK could appear to restart the feed because the recovery watchdog could pull the DW root task forward during a legitimate external transition.

## V11 correction

V11 keeps V10's display-level input injection and removes the destructive assumption that every temporarily blank DW lifecycle state means the feed is broken.

### Host-active recovery gate

LauncherEx V9 reports its host window focus to each feed session. Recovery is suppressed while LauncherEx is not active, such as while Package Installer or another main-display external activity is in front.

### Actual virtual-display task probe

Host focus alone is not enough because an external activity can legitimately run **on the feed VirtualDisplay** while LauncherEx remains focused on the physical display. Before recovery, the Shizuku shell UserService synchronously asks `IActivityTaskManager.getTasks(..., displayId)` for the top task on that exact display.

Probe states:

- no top task -> recovery may proceed;
- DW top task -> normal DW lifecycle/recovery rules apply;
- foreign top task -> recovery backs off and polls gently without consuming attempts or changing task order;
- probe unavailable -> the bridge is rebound/retried briefly, then falls back to the host-aware local recovery path so probe failure itself cannot produce a permanent black feed.

This specifically allows Package Installer, choosers and other external targets to remain in front instead of DW immediately yanking itself back.

### Preserve the existing root task

When recovery is actually necessary and the original root `DwFeedActivity` is still alive, V11 first uses the shell UserService to `moveTaskToFront` on its existing task id. That preserves directory, scroll and navigation state. Root recreation through `am start --display` is retained only as a last resort when the original root Activity is genuinely finishing/destroyed.

### Topmost-window input remains

V10's display-level input architecture remains. The root `ExplorerActivity.dispatchTouchEvent()` fallback stays removed. MotionEvents are injected at the VirtualDisplay through the Shizuku UserService so Android routes them to the actual topmost menu/dialog/viewer window.

MOVE samples use asynchronous injection for throughput. Structural events (DOWN/UP/etc.) wait for dispatcher acceptance inside the UserService Binder thread; the LauncherEx -> DW Messenger path itself remains nonblocking. This is intended to make popup/menu acceptance deterministic without slowing scroll/fling MOVE traffic.

## Exact candidate

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V11_EXTERNAL_SAFE_NEVER_BLACK.apk`

APK SHA-256: `d5161873a3ac90712a6b0209e29bbb7617c6c547c07ed8a57cc6c1dc1b147c37`

`classes2.dex` SHA-256: `e51cd9673fc908f916a7fdd144e630b5731a08a9bbfa24aab2b7da633be5d768`

Package/version remain `com.mekromn.dwfilemanager`, versionCode `9109040`, versionName `9.1.0.8`.

Signer SHA-256 remains `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`; v1/v2/v3 verification passes.

V10 -> V11 payload-content audit, excluding regenerated signature metadata: **only `classes2.dex` changes**. The rebuilt DEX survives a byte-identical baksmali/smali 3.0.10 round trip.

## Device acceptance

- Open APK -> Package Installer/chooser remains usable; DW does not restart or steal focus.
- Back from the external target returns to the same feed state.
- Repeated image/text/binary viewer -> Back cycles never leave black.
- Popup/display-mode taps hit only the visible menu; no file underneath activates.
- Legitimate foreign activities on the VirtualDisplay are never displaced by recovery.
- Genuine blank feed state recovers the existing task first and only recreates the root if it is truly dead.
- Shizuku/input bridge trouble becomes bounded/recoverable instead of unsafe click-through or permanent black.
