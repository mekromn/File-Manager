# LauncherEx × DW dual feed V8 — native Home / Recent routing

## Device result driving V8

V7 successfully launches the real DW `ExplorerActivity` on the feed display. The device shows the actual DW Home UI and then DW itself presents:

`Unable to start requested module for:home (dw.filemanager.xf.IdCatalog)`

This proves the LauncherEx feed surface, private virtual display, Android 16 Shizuku activity launch, and `DwFeedActivity.onPostCreate()` path are all working. The remaining failure is our page-selection call inside DW.

## Root cause

`ExplorerActivity.A(String)` is not a generic page-name API. It constructs a new `dw.filemanager.xf.IdCatalog` from the supplied string and routes that catalog through DW's content system. Passing protocol label `home` therefore asks DW to open an IdCatalog literally named `home`, producing the device error dialog.

A fresh `ExplorerActivity` is already on the native Home surface; the V7 screenshot visibly shows that complete Home UI behind the dialog. Home therefore requires no catalog navigation at all.

DW's own `RecentHomeItem` exposes:

- UI key: `recently_updated`
- native catalog: `jb.d.k`
- catalog value: `dw.filemanager.search.SearchRecentFileCatalog`

Its native navigation object is the same `IdCatalog` used by `RecentFileContentView.Manager`.

## V8 correction

LauncherEx V2 is unchanged. V8 changes only DW `classes2.dex`.

- `PAGE_HOME`: leave the freshly-started `ExplorerActivity` on its already-rendered Home surface; do **not** call `ExplorerActivity.A("home")`.
- `PAGE_RECENT`: obtain DW's exact existing Recent catalog from `jb.d.k`, read its canonical string, and pass that to `ExplorerActivity.A(...)`.
- Retain V7's Shizuku `am start -W` tracing as a fallback diagnostic.
- Keep the 120 ms ready-post used by the existing feed host.

No DW Home/Recent implementation is cloned or reimplemented. V8 now uses the same semantics DW itself uses.

## Exact device candidate

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V8_NATIVE_HOME_RECENT_ROUTE.apk`

APK SHA-256: `7ca18f427cdd96a5fd42e840c24c9c6585b58896897d4606e676dcdfde91f75c`

`classes2.dex` SHA-256: `1f3c43fc56214b0fbab838fe2e26bf7d74ef908b03f595cb349f13c6eadf6959`

Signer SHA-256: `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`

Package/version remain `com.mekromn.dwfilemanager`, `versionCode 9109040`, `versionName 9.1.0.8`.

V7 → V8 entry-content audit: excluding regenerated `META-INF` signature metadata, only `classes2.dex` changes. There are no missing or extra non-signature entries. `AndroidManifest.xml`, `resources.arsc`, and primary `classes.dex` are byte-identical to V7.

The V8 DEX was assembled with smali 3.0.10, disassembled with baksmali 3.0.10, then reassembled byte-identically. The final APK is zipaligned and verifies v1/v2/v3 signatures with the permanent DW certificate.

## Device test

Keep Shizuku running and authorized. Keep LauncherEx V2 installed. Install V8 directly over V7 without uninstalling or clearing data.

Test **DW Home** first. The exact Home UI that V7 already reached should remain visible without the `IdCatalog home` dialog. Then test **DW Recently Updated**; V8 should route to DW's native `SearchRecentFileCatalog` page.