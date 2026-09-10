# LauncherEx × DW dual feed V9 — native session / no companion

## Device evidence driving V9

V8 finally renders the real DW Home surface on the Pixel 9 Pro XL / Android 16. The remaining device defects are behavioral rather than display bootstrap failures:

- vertical scrolling in the feed is not native/smooth;
- opening some DW content can leave the feed surface black;
- the old standalone companion APK requirement is obsolete for the diverged DW build and no longer provides retained functionality.

## V9 changes

### 1. Remove the obsolete companion requirement physically

The Stage10 architecture had already removed 27 distributed feature-level companion decisions and reduced the old product dependency to one process-wide startup check. V9 removes that last check rather than forcing it true:

- remove `DWApplication.onCreate()` → `Companion.present(Context)`;
- remove the missing-companion `System.exit(0)` path;
- delete `dw.filemanager.core.Companion`;
- require zero packaged `nextapp.fx.rk` literals and zero `Companion.present` call sites.

`QUERY_ALL_PACKAGES` is intentionally not removed here because DW's own Apps/package browsing can use package visibility independently of the deleted companion gate.

### 2. Keep DW child navigation on the feed display

V8's `DwFeedActivity` overrode both `startActivity(...)` overloads and forced every child launch to `Display.DEFAULT_DISPLAY`. That can move a DW-owned viewer/child Activity off the private feed display and leave LauncherEx looking at a valid but empty/black surface.

V9 removes those overrides completely. The feed Activity now uses normal Activity launch semantics, so same-task DW navigation can inherit its current display/task instead of being forcibly ejected to display 0.

### 3. Reduce per-touch latency

The Launcher → DW Messenger boundary still carries one MotionEvent per input event, but V9 removes a redundant second copy and an extra main-looper queue hop inside DW:

- `DwFeedService` already receives Messenger messages on DW's main looper;
- `DwFeedRegistry.input()` therefore dispatches the received MotionEvent directly to `ExplorerActivity.dispatchTouchEvent(...)`;
- recycle the received MotionEvent immediately afterward;
- delete the now-unused input-dispatch synthetic Runnable class.

This preserves the exact DW view/controller touch path while reducing allocation and scheduling overhead on every scroll/fling event.

### 4. Preserve V8 native page routing

- DW Home: fresh `ExplorerActivity` remains on its native Home surface; do not call `A("home")`.
- DW Recently Updated: continue using the exact `jb.d.k` / `SearchRecentFileCatalog` route used by DW itself.

## Exact device candidate

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V9_NATIVE_SESSION_NO_COMPANION.apk`

APK SHA-256: `ff88073a4ab50afb0e42898786fcdcbdbf422f81e6ed6f4a218846e65352efa7`

DEX SHA-256:

- `classes.dex`: `30d4ad67289d15f644930124302380dfabc5836a396157f9812e8c93ebcd5249`
- `classes2.dex`: `5aaa624ac59abfbfa494214ca6c712b18a6d0b052fb4a4c205c7a026d6153a84`

Permanent DW signer SHA-256: `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`

Package/version stay frozen at `com.mekromn.dwfilemanager`, `versionCode 9109040`, `versionName 9.1.0.8`.

V8 → V9 non-signature payload audit:

- changed: `classes.dex`, `classes2.dex` only;
- added: none;
- removed: none;
- `AndroidManifest.xml`: byte-identical;
- `resources.arsc`: byte-identical.

Both V9 DEX files have valid SHA-1/Adler32 headers and independently disassemble/reassemble byte-identically with baksmali/smali 3.0.10. The final APK verifies ZIP alignment and v1/v2/v3 signatures with the permanent DW certificate.

## Device gate

Use with LauncherEx dual-feed V3. Keep Shizuku running/authorized. Install both in place without uninstalling or clearing data.

Required acceptance:

1. slow and fast DW Home vertical scrolling/fling is smooth and does not get stolen by the launcher;
2. open folders, files, viewers, dialogs and context actions without the feed becoming black;
3. Back navigation behaves as DW normally does;
4. Recently Updated and its filters remain functional;
5. swipe away from the feed and back without losing DW state during ordinary attached page transitions;
6. standalone DW still works normally;
7. DW launches even when the old companion APK is absent.

V9 remains device-test-required until these behaviors are confirmed on the Pixel.
