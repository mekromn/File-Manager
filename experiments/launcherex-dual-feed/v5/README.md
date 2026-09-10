# LauncherEx × DW dual feed V5

## Device result driving V5

V4 on Pixel 9 Pro XL / Android 16 passed the previous display/permission boundary but remained indefinitely on `Starting DW Home...`.

The V4 fallback executed Shizuku `am start --display` from DW's Messenger service handler and immediately called `Process.waitFor()` on that same main looper. `DwFeedActivity` belongs to the same DW process, so its lifecycle callbacks also require that main looper. This can deadlock the launch command and Activity bootstrap against each other.

## V5 correction

- Keep LauncherEx V2 unchanged.
- Keep V4 manifest/`allowEmbedded`/`ACTIVITY_EMBEDDING` configuration unchanged.
- Keep zero-flag private `VirtualDisplay` creation unchanged.
- Keep the existing normal `ActivityOptions.setLaunchDisplayId()` attempt unchanged.
- When that path throws `SecurityException`, start Shizuku `am start --display` but **do not call `Process.waitFor()` on DW's main looper**.
- The existing five-second `activity_timeout` therefore becomes live immediately after the Shizuku process is started; the feed can no longer remain indefinitely on `Starting...` because the main looper is blocked in `waitFor()`.
- Leave DW Home and DW Recently Updated page implementations untouched.

This is intentionally smaller than the earlier worker-thread draft: the one-shot shell command is already asynchronous once DW stops waiting for its process. That lets the exact V4 DEX be patched in place with six code units, preserving method size, catch ranges, and downstream offsets.

## Exact built artifact

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V5_NONBLOCKING_SHIZUKU_LAUNCH.apk`

SHA-256: `f714c4b82a396a7210f86d83db8a704fa3b6da0302af19baa8db6e81136b68a8`

`classes2.dex` SHA-256: `0dd577791c1aea092eebcaeb25b25cd30b39bcfbe31d810392a2c399fbab0a15`

V4 → V5 ZIP entry-content audit: excluding regenerated v1 signature metadata under `META-INF`, `classes2.dex` is the only payload entry whose content changed. `AndroidManifest.xml` and `classes.dex` remain byte-identical.

The DEX SHA-1 signature and Adler32 checksum were recalculated and verified. The final APK verifies with v1/v2/v3 signatures, zipalign verification, and the permanent DW certificate SHA-256 `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`.

Package identity remains unchanged for in-place installation:

- package: `com.mekromn.dwfilemanager`
- versionCode: `9109040`
- versionName: `9.1.0.8`

## Device test

Keep LauncherEx V2 installed. Install V5 directly over V4 without uninstalling or clearing data, then test **DW Home** first. The expected result is either the real DW Home page becoming ready, or a precise timeout/error after about five seconds—not an indefinite `Starting DW Home...` state.
