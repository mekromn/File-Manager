# LauncherEx × DW dual feed V5

## Device result driving V5

V4 on Pixel 9 Pro XL / Android 16 passed the previous display/permission boundary but remained indefinitely on `Starting DW Home...`.

The V4 fallback executed Shizuku `am start --display` from DW's Messenger service handler and immediately called `Process.waitFor()` on that same main looper. `DwFeedActivity` belongs to the same DW process, so its lifecycle callbacks also require that main looper. This can deadlock the launch command and Activity bootstrap against each other.

## V5 correction

- Keep LauncherEx V2 unchanged.
- Keep V4 manifest/`allowEmbedded`/ACTIVITY_EMBEDDING configuration unchanged.
- Keep zero-flag private VirtualDisplay creation unchanged.
- Run the Shizuku `am start --display` process and its `waitFor()` on a dedicated daemon worker thread.
- Arm the five-second `activity_timeout` before either launch path so the UI cannot remain on `Starting...` indefinitely.
- Leave DW Home and DW Recently Updated page implementations untouched.

## Exact artifact

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V5_ASYNC_SHIZUKU_LAUNCH.apk`

SHA-256: `32b77bca72088b187c4473c22f3af532e98828cfebbe7a712bc3227bb73659d4`

V4 → V5 non-signature payload delta: `classes2.dex` only.

Signer and versionCode remain unchanged for in-place installation.
