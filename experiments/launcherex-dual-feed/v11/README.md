# LauncherEx × DW dual feed V11 — transition-aware never-black recovery

## Device failure driving V11

On the Pixel 9 Pro XL / Android 16 device, DW V10 could restart the feed when opening an APK or another target that legitimately leaves DW for a child/external activity.

V10 inferred a blank feed from DW-process lifecycle callbacks. That cannot see Package Installer or another activity owned by a different process/package, so an internal DW trampoline could finish, V10 would briefly see no resumed DW activity, and the watchdog could relaunch `DwFeedActivity` while a legitimate handoff was still in progress.

## V11 correction

V11 keeps V10's display-level MotionEvent injection and no-click-through policy, but makes task recovery display-aware.

The Shizuku UserService version is bumped to 2 and adds two privileged ActivityTaskManager operations:

- `displayState(displayId)` uses `getAllRootTaskInfosOnDisplay()` and reports:
  - `2`: a visible task already occupies the feed display;
  - `1`: tasks exist on the display but none is currently visible;
  - `0`: the display has no task;
  - `-1`: probe unavailable/error.
- `focusTopTask(displayId)` focuses the existing top task without recreating `DwFeedActivity`.

Recovery rules:

1. The first two recovery checks are grace probes, allowing legitimate transitions such as APK -> Package Installer to settle.
2. If state is `2`, recovery never steals focus or relaunches DW. The session is re-probed periodically so recovery remains available after the external activity leaves.
3. If state is `1`, V11 focuses the existing task rather than restarting the feed root, preserving DW navigation/viewer state.
4. If state is `-1`, V11 rebinds/retries; unknown state is never treated as permission to restart.
5. Root relaunch is allowed only when state is `0` and there is no surviving non-finishing root `ExplorerActivity`.

This separates **never black** from **always force DW to the foreground**.

## Recommended launcher pairing

While DW reliability is being finalized, pair V11 with the known partially usable LauncherEx V3 SurfaceView baseline rather than V7. V7/V10 device testing still showed intermittent wallpaper-only/iconless Home states, so the launcher-side experiment remains rejected for now.

## Exact candidate

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V11_TRANSITION_AWARE_NEVER_BLACK.apk`

APK SHA-256: `ed6d2502f3fd28a15e6660855105eebf6b28ea2a7d5d978f25e424ee3df11c14`

`classes2.dex` SHA-256: `48864d58c0e43e524b03239df4c0fb2c92aa26d084e51fdb912fc528edf7498b`

Signer SHA-256: `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`

Package/version remain `com.mekromn.dwfilemanager`, `versionCode 9109040`, `versionName 9.1.0.8`.

V10 -> V11 non-signature payload audit: only `classes2.dex` changes. `AndroidManifest.xml`, primary `classes.dex`, resources, native libraries, package/version and signing identity are unchanged. The rebuilt DEX survives a byte-identical baksmali/smali 3.0.10 round trip; the final APK passes zip alignment and v1/v2/v3 signature verification.

## Device acceptance

- Opening an APK reaches Package Installer instead of restarting DW Home.
- Opening external/internal viewers does not reset the feed root.
- Back from a viewer/installer returns to the same live DW state when Android would normally do so.
- A truly empty feed display still recovers instead of remaining black.
- Popup/dialog/viewer input continues to use V10 display-level injection; no root-activity click-through fallback is reintroduced.
