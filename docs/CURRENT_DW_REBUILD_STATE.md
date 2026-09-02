# Current DW File Manager rebuild state

Updated: 2026-09-02

This is the durable handoff for the DW File Manager structural rebuild. The authoritative implementation is the checked-in stage scripts under `tools/stages/` plus verification records under `docs/checkpoints/`. A transient decoded tree is never authoritative by itself.

## Immutable base

- canonical base: FX 9.1.0.8 / versionCode 9108
- canonical SHA-256: `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- known-working historical reference only: FX Extended 9108006 / SHA-256 `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- Apktool 3.0.3
- smali/baksmali 3.0.10

Use `.github/workflows/replay-dw-rebuild.yml` for exact immutable-base replay. It now gates both pull requests and changes merged to `main`.

## Final identity

- app: **DW File Manager**
- package: `com.mekromn.dwfilemanager`
- versionCode: `9109000`
- versionName: `9.1.0.8`
- target SDK: 34
- app-owned namespace: `dw.filemanager.*`
- useful extension namespace: `dw.filemanager.ext.*`
- neutral shared runtime: `dw.filemanager.runtime.*`
- configuration extension: `.dwconfig`
- generated config filename prefix: `DW_`
- Dark Glass + AMOLED Black Transparent with Pixel blue `#4285F4`
- DW adaptive/legacy/splash/root/TextEdit artwork

## Final companion invariant — Stage 10

The old distributed companion/capability system is retired.

There is exactly **one app-wide companion decision**:

1. `DWApplication.onCreate()` calls `dw.filemanager.core.Companion.present(Context)` once.
2. The helper contains the only `nextapp.fx.rk` literal in the packaged APK.
3. It performs exactly one `PackageManager.getPackageInfo(packageName, 0)` lookup.
4. Package found -> `true`.
5. `NameNotFoundException` -> `false`.
6. If false, DW exits before normal initialization.
7. If true, normal DW code runs with no further companion checks.

No signer/hash check, version check, installer check, account, product, trial, timer, cache, persistence, broadcast, UI, network, or installed-app enumeration exists in the companion helper.

Stage 10 removed 27 distributed companion checks across 26 files. The final package contains exactly one `nextapp.fx.rk` literal total and exactly one caller of `Companion.present(Context)`.

Target-SDK package visibility is provided without duplicating the companion package literal. The manifest contains `android.permission.QUERY_ALL_PACKAGES`; it contains no `nextapp.fx.rk` value.

## Structural removals completed

- trial/time-window/status system: removed
- Update/Refresh/status UI: removed
- app-owned IAB/BillingClient/product/SKU/acquisition system: removed
- Google Play Store integration/surface: removed
- DataTransport/telemetry upload graph: removed
- Google Play Services/common-client class/manifest island: removed
- app-owned EULA/terms acceptance: removed
- obsolete privacy settings surface: removed
- vendor support/help/promo branding: removed
- hard-coded NextApp Box redirect: removed
- `.fxconfig`: removed / migrated to `.dwconfig`
- stale Upgrade/license wording: removed while required OSS/protocol license terminology remains

User-initiated SMB/SFTP/FTP/WebDAV/cloud/Web Access functionality remains intentionally preserved.

## Network release gate

Stage 10 classifies every packaged HTTP/HTTPS literal:

- unique literals: 53
- explicit runtime/user-feature literals: 35
- inert XML/library/compiler/data literals: 18
- unclassified: 0
- banned NextApp/Firebase/analytics/Crashlytics/DoubleClick/telemetry domains: 0

Preserved runtime endpoints are tied to deliberate user-facing features such as Google Drive browser OAuth/API, Microsoft/OneDrive Graph, Box, SugarSync, local Web Access, and the user-invoked F-Droid package page.

## Exact merged-main Stage 10 replay

Merged Stage 10 code commit: `ed3c383b829b8c0d6573745934049f9268d6eaee`.

GitHub Actions run `33594036238` replayed that exact `main` commit from the immutable base and passed:

- base SHA verification: pass
- every transformation stage: pass
- network allowlist: pass
- one-companion-literal invariant: pass
- one-companion-caller invariant: pass
- one `getPackageInfo(name, 0)` helper lookup invariant: pass
- Apktool rebuild: pass
- ZIP integrity: pass
- artifact upload: pass
- classes: `11,808`
- unsigned size: `12,641,243` bytes
- unsigned SHA-256: `b058df28be22237301444a51195e6e93d81ccf8a3ab7fa057e3417775a98e426`

See `docs/checkpoints/STAGE10_RELEASE_AUDIT.md`.

## Permanent DW File Manager signer

The user accepted a one-time uninstall/reinstall so the historical `FX Extended Test` certificate could be retired.

Permanent new certificate identity:

- subject/issuer: `CN=DW File Manager, O=DW File Manager, OU=Mekromn`
- RSA 4096
- certificate SHA-256: `1C:FD:89:2D:8E:CA:D5:11:45:5E:36:5C:2B:FD:4A:FF:B2:4D:F2:57:60:FF:90:5B:D6:BC:10:CE:AA:3B:5C:6E`
- validity: through 2054-01-18

The private recovery bundle is deliberately kept outside GitHub and has been saved to the user's Library as `DW-File-Manager_SIGNING_KEY_KEEP_PRIVATE.zip`. This signer is now a hard invariant for all future DW File Manager builds.

## Current signed Stage 10 device-test candidate

`DW-File-Manager_9.1.0.8_v9109000_MINIMAL_COMPANION_FINAL_TEST.apk`

- signed size: `12,787,513` bytes
- signed SHA-256: `1b0ed70ffbad60b501b9c1d15cd4a461421a18961e5c3ed75b9a7cfcaaadaef3`
- zipalign verification: pass
- APK Signature Scheme v1: pass
- APK Signature Scheme v2: pass
- APK Signature Scheme v3: pass
- signer identity/fingerprint: pass
- ZIP integrity: pass

Post-sign comparison against the exact verified unsigned merged-main artifact:

- missing non-signature entries: 0
- extra non-signature entries: 0
- changed non-signature entries: 0
- `classes.dex`: byte-identical
- `AndroidManifest.xml`: byte-identical
- `resources.arsc`: byte-identical
- `nextapp.fx.rk`: exactly 1 occurrence, in `classes.dex` only
- `fxconfig`: 0
- `dwconfig`: 4
- GMS descriptor/string hits: 0

## Remaining device validation

The static/rebuild/signing gates are complete. Runtime testing remains:

1. uninstall the previous FX-Extended-signed build once, then install the new DW-signed APK;
2. cold start with companion installed;
3. optional negative test with companion absent -> DW should exit before initialization;
4. Settings; Dark Glass/AMOLED; drawer/header appearance;
5. `.dwconfig` export/import and `DW_...` generated filename;
6. local browsing/copy/move/delete/search and root mode;
7. Media section;
8. SMB/SFTP/FTP/WebDAV;
9. Google Drive browser OAuth, OneDrive, Box and SugarSync;
10. Web Access including HTML5 audio;
11. confirm retired Refresh/Upgrade/trial/purchase/legal UI never reappears.

The signed APK is the current device-test candidate. Device results determine whether any runtime fixes are still required.
