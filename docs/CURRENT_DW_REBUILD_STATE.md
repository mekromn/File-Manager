# Current DW File Manager rebuild state

Updated: 2026-09-02

This file is the durable handoff for the DW File Manager structural rebuild. The authoritative implementation is the checked-in stage scripts under `tools/stages/` plus verification records under `docs/checkpoints/`. A transient decoded tree is never treated as authoritative by itself.

## Immutable inputs

- accepted base: FX 9.1.0.8 / versionCode 9108 / SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- known-working reference only: FX Extended 9108006 / SHA-256 `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- Apktool 3.0.3
- smali/baksmali 3.0.10
- recovered signing identity remains private outside GitHub

Use `.github/workflows/export-rebuild-state.yml` to export the checked-in rebuild state after interruptions. Use `.github/workflows/replay-dw-rebuild.yml` for a full exact-hash replay from the immutable base.

## Final target/invariants

- **DW File Manager** / `com.mekromn.dwfilemanager`
- app-owned namespace `dw.filemanager.*`
- useful extended modules `dw.filemanager.ext.*`
- neutral R8-shared runtime `dw.filemanager.runtime.*`
- target SDK 34 compatibility behavior
- Dark Glass + AMOLED Black Transparent with exact Pixel blue `#4285F4`
- opaque top header and drawer body matching popup-menu surface
- new DW adaptive icon; no upstream vendor artwork/visible branding
- DW configuration extension `.dwconfig`; legacy `.fxconfig` is not retained
- no app-owned commerce/trial/status/product acquisition subsystem
- no telemetry/DataTransport/background promo/update path
- app-owned EULA/terms acceptance removed; third-party notices retained
- user-initiated SMB/SFTP/FTP/WebDAV/cloud/Web Access functionality preserved

## Companion invariant

Only `dw.filemanager.core.Companion.present(Context)` evaluates the external package:

1. lookup `nextapp.fx.rk`;
2. missing -> false;
3. signer verification;
4. boolean return.

No cache, state object, time/product/version/installer checks, broadcasts, UI, network request, refresh path or persistence is permitted. The external package literal exists only in this helper and the Android package-visibility query.

## Durable verified stages

### Stage 01 — identity/theme
`stage01_identity_theme.py` / `STAGE01_IDENTITY_THEME.md`

DW package/label, target SDK 34, collision-safe authorities, developer store checkbox removal, Dark Glass/AMOLED theme registration and Pixel-blue active channels.

### Stage 02 — companion boolean
`stage02_companion_state.py` / `STAGE02_COMPANION_STATE.md`

One signer-verified boolean helper; normal capability consumers migrated away from the old state provider.

### Stage 03 — trial/time-window/status removal
`stage03a`–`stage03d` / `STAGE03_TRIAL_STATUS_REMOVAL.md`

Update/Refresh/status UI, trial tutorial, time-window state/persistence/import/export and trial/status resources physically removed.

### Stage 04 — commerce/product/acquisition removal
`stage04a`–`stage04i` / `STAGE04_COMMERCE_REMOVAL.md`

App-owned IAB, public BillingClient proxy/API surface, acquisition/product/SKU graph, Web Access upgrade module and commerce resources/help removed.

### Stage 05 — telemetry/DataTransport removal
`stage05a`–`stage05g` / `STAGE05_DATATRANSPORT_REMOVAL.md`

BillingLogger transport root, unreachable shaded code, scheduler/backend/event-store/CCT graph and Android DataTransport components removed by method-level cuts and proven reachability.

### Stage 06 — neutral namespace + JNI
`stage06a`–`stage06c` / `STAGE06_NAMESPACE_JNI.md`

- app-owned `nextapp.*` implementation migrated to `dw.filemanager.*`;
- useful former legacy module code moved to `dw.filemanager.ext.*`;
- 111 genuinely shared shaded helpers moved to `dw.filemanager.runtime.*`;
- old `play_billing` and live `Plus*` implementation identifiers removed;
- all four `libnative-file-access.so` JNI exports migrated to `Java_dw_filemanager_NativeFileAccess_*`.

### Stage 07 — legal/vendor/background-network cleanup
`stage07a`–`stage07e` / `STAGE07_LEGAL_NETWORK.md`

- app-owned first-run EULA/license gate and obsolete privacy settings surface removed;
- vendor support/help/Web Access branding and links removed from packaged assets;
- four unreachable GMS/lifecycle/Dynamite remnants deleted while the Drive-auth GMS path is retained;
- SoundManager2/Flash fallback replaced with a 1,181-byte HTML5 Audio-only compatibility shim;
- startup/background component audit shows no telemetry/update/promo network path.

### Stage 08 — UI branding, drawer surface, DW artwork
`stage08a`–`stage08b` / `STAGE08_UI_BRANDING.md`

- drawer body resolves `menuBackground` with `windowBackground` only as fallback;
- Android UI/resources/locales contain zero uppercase FX/NextApp branding hits at this checkpoint;
- FX-branded resource IDs/files migrated to DW identifiers at the same public numeric IDs;
- old artwork replaced by DW adaptive/legacy/splash/root/TextEdit artwork with Pixel blue `#4285F4`;
- Stage 08 historically retained `.fxconfig`; Stage 09d intentionally supersedes that compatibility decision.

Stage 08 unsigned reference: 11,890 classes, 12,891,720 bytes, SHA-256 `185a69ec5828a0809aeea24a57f09e9673918d64ec1ed76d69f0a433860bc4ae`.

### Stage 09 — lean finalization / Box neutralization / `.dwconfig`
`stage09a`–`stage09d` / `STAGE09_FINALIZATION.md`

- 12 graph-proven orphan resources removed;
- hard-coded `https://android.nextapp.com/_boxredirect` removed from Box OAuth; callback acceptance uses matching OAuth `state` plus non-null `code`;
- remaining app-owned commerce/trial/state residue and stale terms removed;
- `.fxconfig` migrated to `.dwconfig` everywhere app-owned.

Exact-hash GitHub Actions replay run `33591589290` passed from the immutable 9.1.0.8 APK through every checked-in stage 01→09d. Stage 09d found and replaced exactly four `fxconfig` content occurrences:

- 2 in `res/values/strings.xml`;
- 1 in `smali/rf/a.smali`;
- 1 in `smali/ab/k.smali`;
- 0 path renames were required.

Verified Stage 09d unsigned replay:

- rebuilt classes: `11,889`
- APK size: `12,829,902` bytes
- APK SHA-256: `ce1dff557cf399e722caa3a1abc15a9045ed895b7b52ce5a6edad113e2c46e76`
- ZIP integrity: clean
- canonical base SHA verification: passed
- full stage replay: passed

PR #1 (`Stage 09d: migrate .fxconfig to .dwconfig`) was squash-merged to `main` as commit `da7b92404e6f98a9ac03b786ee9219e122f66c01`.

## Remaining release gates

1. Re-audit every surviving HTTP/HTTPS endpoint against explicit user-facing file-manager features.
2. Set/freeze final versionCode/versionName and verify package/manifest/provider/action identity.
3. Sign with the recovered private DW/FX-Extended signing identity.
4. Verify v1/v2 signatures, ZIP alignment, DEX/resources/ZIP integrity, and signer fingerprint.
5. Generate final before/after class/resource/network/banned-term report.
6. Produce an actually existing downloadable **signed** APK only after static acceptance checks pass.
7. Device regression test: startup, Settings, themes/drawer, `.dwconfig` export/import, local browsing, root, Media, SMB/SFTP/FTP/WebDAV, cloud providers including real Box login, and Web Access.

The Box vendor redirect literal is statically removed, but Box server compatibility is not claimed until a real device login succeeds.

No APK is final until the signed file exists and the release/device gates pass.
