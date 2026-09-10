# LauncherEx × DW dual feed V4 — Android 16 display launch

## Device evidence from V3

On the Pixel 9 Pro XL / Android 16, V3 returned:

`activity_launch_failed:SecurityException:Permission Denial ... dw.filemanager.feed.DwFeedActivity`

Because V3 reports display creation separately, this proves the zero-flag private virtual display was created successfully and Android denied the subsequent ordinary app launch of `DwFeedActivity` onto that non-default display. Neither DW Home nor DW Recently Updated had been navigated yet.

## V4

LauncherEx V2 is unchanged. Only DW changes.

1. DW still creates the private virtual display with `flags = 0`.
2. DW first attempts the normal `ActivityOptions.setLaunchDisplayId(...)` path.
3. If and only if that launch throws `SecurityException`, V4 uses DW's already-authorized Shizuku shell bridge to run `am start --display <displayId>` for DW's own `DwFeedActivity`.
4. `DwFeedActivity` declares `android:allowEmbedded="true"` so it is eligible for an untrusted/private virtual display.
5. `DwFeedActivity` is exported only behind `android.permission.ACTIVITY_EMBEDDING`; this is not a generic exported DW entry point.
6. After launch, the existing V2/V3 registry still navigates the real `ExplorerActivity` to `home` or `recently_updated`, and all browser/file behavior remains DW-owned.

If Shizuku is not authorized, the feed fails closed with `shizuku_unavailable` rather than changing launcher state.

## Artifact

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V4_ANDROID16_SHIZUKU_DISPLAY_LAUNCH.apk`

SHA-256: `97c14cfc5a89e3dc3115f02257f24f0401dc98a9edee5b343aabfa08f33c6cb0`

Package/version remain `com.mekromn.dwfilemanager` / `9109040`, signed with the permanent DW File Manager certificate.

Relative to V3, the only non-signature payload entries changed are `AndroidManifest.xml` and `classes2.dex`. `classes.dex` and `resources.arsc` are byte-identical.
