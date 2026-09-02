# Stage 07 — app legal/vendor surfaces and network-minimization checkpoint

Source checkpoint: verified Stage 06 tree.

Transformations committed for this checkpoint:

- `tools/stages/stage07a_remove_legal_gate.py`
- `tools/stages/stage07b_remove_privacy_surface.py`
- `tools/stages/stage07c_rebrand_help_web.py`
- `tools/stages/stage07d_remove_dead_gms.py`
- `tools/stages/stage07e_html5_audio.py`

## App-owned legal/privacy removal

- Physically removed the first-run EULA/license acceptance path from `ExplorerActivity` rather than auto-accepting it.
- Removed `acceptedLicenseVersion` state and the dedicated accept/reject listener.
- Removed the legal-dismiss branch from the R8-shared dialog listener while preserving its unrelated branches.
- Deleted the app-owned `assets/license/license.txt` and `assets/license/privacy.txt` files.
- Removed the obsolete Privacy Information settings row and its click branch.
- Retained third-party/open-source notices and generic file/details metadata that use legal/license terminology for unrelated purposes.

## Vendor help/Web Access cleanup

- Removed NextApp support e-mail addresses and external vendor documentation actions.
- Rebranded local help pages to DW File Manager naming.
- Rebranded Web Access source and bundled JavaScript together.
- Deleted the four packaged vendor branding PNGs.
- Removed all standalone `FX` / NextApp branding from packaged assets at this checkpoint.
- External vendor documentation/promo URLs no longer have executable Web Access actions.

## Google runtime reachability

Stage 06 had 12 `com.google.android.gms` classes.

A transitive class-graph traversal rooted at:

- `dw.filemanager.ext.ui.net.cloud.GoogleDriveAuthActivity`
- `dw.filemanager.ext.ui.net.cloud.GoogleDriveAuthTokenActivity`

proved 9 GMS classes reachable from the actual user-invoked Google Drive authentication path. These include `GoogleApiActivity`, `Scope`, `Status`, common manifest-value checks and the common internal helper. Their manifest activity/version metadata is therefore retained to preserve Google Drive authentication.

Four dead files were physically removed:

- R8 helper `t5/g`
- `com.google.android.gms.common.api.internal.LifecycleCallback`
- `com.google.android.gms.common.util.DynamiteApi`
- `com.google.android.gms.dynamite.DynamiteModule$DynamiteLoaderClassLoader`

The resulting Stage 07d APK rebuilt successfully with exactly 9 GMS class files remaining.

## Web Access audio/network lean-up

The bundled 2017 SoundManager2 library was 37,878 bytes and included a complete Flash/SWF/plugin fallback with Macromedia download/plugin URLs, even though Web Access configured `preferFlash:false`.

DW Web Access uses only:

- `soundManager.createSound()`
- `soundManager.destroySound()`
- sound `play/pause/resume/setPosition/setVolume`
- `duration`, `position`, `paused`

The legacy library was replaced by a 1,181-byte HTML5 `Audio` compatibility shim implementing exactly that contract.

Verified after replacement:

- no Flash/SWF/Macromedia/plugin fallback strings in Web Access;
- Web Access APK rebuild succeeds;
- ZIP integrity succeeds.

Stage 07e unsigned checkpoint:

- size: 12,891,901 bytes
- SHA-256: `262444c8ab906d04c840cab148f862e80c3fe832e6cef18015a03f127f090782`

## Network endpoint classification

A full static HTTP/HTTPS string inventory after the cleanup finds no vendor update/theme/support/promo/telemetry endpoint.

Surviving functional endpoints are tied to deliberate user actions:

- Google OAuth + Google Drive API/upload endpoints;
- Microsoft OAuth + Graph/OneDrive endpoints;
- Box OAuth/API/upload endpoints;
- SugarSync authorization/API endpoints;
- local Web Access loopback (`127.0.0.1`);
- an F-Droid package-page URL in the user-invoked app-market/open-package path.

Non-network-runtime strings also remain where they are data/spec/documentation, for example Android/W3 XML namespaces, Adobe XMP namespace, SLF4J/Commons documentation messages and compiler/source URLs embedded inside bundled BusyBox binaries.

## Startup/background network audit

`DWApplication.onCreate()` performs device/UI/local initialization only:

- resource sanity check;
- Bluetooth adapter initialization;
- screen-state receiver registration;
- Wi-Fi state receiver registration;
- target/display/device feature detection;
- module registration;
- local thumbnail/cache cleanup;
- local file-manager initialization.

The startup async thread is thumbnail/cache maintenance and contains no HTTP/network request.

`dw.filemanager.ext.ui.ExtExtension.onCreate()` is empty after the retired commerce lifecycle removal.

Remaining manifest services are:

- Sharing/Web Access service and Quick Settings tile — user initiated;
- local media server/index scan services;
- file operation service.

No telemetry, analytics, update, promo or DataTransport service/receiver remains.

AndroidX Startup initializes Emoji, process lifecycle, profile installer and OkHttp platform configuration; it does not itself create an outbound request.

## Explicit Box OAuth blocker

Two executable vendor-domain references remain in the Box OAuth path:

- the authorization request's registered redirect URI;
- the WebView callback interception check.

The URI is `https://android.nextapp.com/_boxredirect`.

Current Box OAuth documentation states that redirect URIs are exact-match application configuration. `redirect_uri` may be omitted only in compatible single-redirect configurations; applications with multiple configured redirect URIs require it and otherwise return `redirect_uri_missing` after authorization.

The current embedded Box OAuth client is an upstream credential registration that DW cannot modify from APK code. Blindly changing the redirect URI would therefore break Box authentication.

The source has deliberately **not** hidden/encoded this vendor redirect and called it removed. It remains an explicit final-release blocker.

Clean long-term solutions are:

1. replace the Box OAuth client with DW-controlled/configurable Box application credentials and a neutral HTTPS/loopback redirect; or
2. remove Box support if a zero-vendor-reference build is prioritized over Box compatibility.

A potential compatibility experiment is to omit `redirect_uri` and validate `state`/authorization code generically in the WebView, but it cannot be accepted without a real Box login test because the upstream Box app may have multiple registered redirects.

## Pending after Stage 07

- resolve Box OAuth vendor redirect blocker;
- broader Android resource-key/internal visible branding sweep (`fx`-named resource IDs that no longer display FX text);
- final drawer-body popup-surface theme hook;
- new DW adaptive icon and any remaining vendor artwork cleanup;
- orphan/dead resource pruning;
- signing with the recovered private signing identity;
- full final structural/network audit;
- device startup/settings/local/root/Media/network/cloud/Web Access regression testing.

No user-test APK is produced by this checkpoint.
