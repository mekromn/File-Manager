# LauncherEx × DW dual feed V7 — Shizuku launch trace

## Device result driving V7

V6 fixed the DEX verifier failure. With Shizuku stopped, the device correctly reached:

`activity_launch_failed:SecurityException:...;shizuku_unavailable`

After Shizuku was started, the same Pixel 9 Pro XL / Android 16 device advanced to:

`activity_timeout`

That proves the feed service, private virtual display creation, V6 verifier repair, Shizuku Binder/permission gate, and `ShizukuBridge.startCommand()` process creation are all being reached. The remaining ambiguity is whether shell's `am start --display` fails, succeeds but targets the wrong state/display, or starts `DwFeedActivity` and the Activity fails before `onPostCreate()` reports ready.

## V7 diagnostic change

LauncherEx V2 is unchanged. V7 changes only DW `classes2.dex`.

- Preserve V6 private zero-flag `VirtualDisplay` behavior.
- Preserve the normal app `ActivityOptions.setLaunchDisplayId()` attempt and its Android 16 `SecurityException` fallback boundary.
- Execute the fallback as `/system/bin/am start -W --user current --display <id> ... 2>&1` through the already-authorized Shizuku one-shot process.
- Never wait for that shell process on DW's main looper.
- A dedicated daemon worker reads the shell output and exit code.
- Store the result on the feed Session as `shizuku_rc_<n>:<am output>`.
- If the Activity still fails to call `activityReady()` before the existing watchdog, the visible error becomes `activity_timeout:<stored Shizuku result>` instead of a generic timeout.
- Track/destroy an in-flight launch process during session cleanup.

The output is bounded so a shell diagnostic cannot grow the launcher error surface without limit.

## Exact device candidate

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V7_SHIZUKU_LAUNCH_TRACE.apk`

APK SHA-256: `b22c2f7a0f539047e890d53cc41dc9e5bc7d2719904897e6af698539abdddfe2`

`classes2.dex` SHA-256: `c33e2e0c34127c41a9277b9e031a53d59f0fabc8ef344486569ee6fa5fb0b5dc`

Signer SHA-256: `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`

Package/version remain `com.mekromn.dwfilemanager`, `versionCode 9109040`, `versionName 9.1.0.8`.

V6 → V7 entry-content audit: excluding regenerated `META-INF` signature metadata, only `classes2.dex` changes. There are no missing or extra non-signature entries. `AndroidManifest.xml`, `resources.arsc`, and the original `classes.dex` are byte-identical to V6.

The V7 DEX was assembled with smali 3.0.10, independently disassembled with baksmali 3.0.10, reassembled, and the round-trip DEX is byte-identical. The final APK is zipaligned and verifies v1/v2/v3 signatures with the permanent DW certificate.

## Device test

Keep LauncherEx V2 installed and Shizuku running/authorized. Install V7 directly over V6 without uninstalling or clearing data, then open **DW Home**. If the real page does not appear, capture the full visible `activity_timeout:shizuku_...` text; it should identify the next exact boundary without another logcat-only diagnostic build.
