# Current DW File Manager rebuild state

Updated: 2026-09-02

This is the durable handoff for the DW File Manager structural rebuild. The authoritative implementation is the checked-in stage scripts under `tools/stages/` plus verification records under `docs/checkpoints/`. A transient decoded tree is never authoritative by itself.

## Immutable inputs

- canonical base: FX 9.1.0.8 / versionCode 9108 / SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- known-working reference only: FX Extended 9108006 / SHA-256 `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- Apktool 3.0.3
- smali/baksmali 3.0.10
- recovered signing identity remains private outside GitHub

Use `.github/workflows/replay-dw-rebuild.yml` for immutable-base replay and `.github/workflows/export-rebuild-state.yml` for durable state export.

## Final identity/invariants

- app: **DW File Manager**
- package: `com.mekromn.dwfilemanager`
- versionCode: `9109000`
- upstream versionName retained: `9.1.0.8`
- target SDK: 34
- app-owned namespace: `dw.filemanager.*`
- useful extended modules: `dw.filemanager.ext.*`
- neutral R8-shared runtime: `dw.filemanager.runtime.*`
- Dark Glass + AMOLED Black Transparent; Pixel blue `#4285F4`
- opaque top header; drawer body uses popup-menu surface
- DW icon family; no visible upstream FX/NextApp artwork
- configuration extension: `.dwconfig`; exported filenames use `DW_...`
- no app-owned trial/status/product/acquisition/IAB/BillingClient/Google Play Services/DataTransport subsystem
- no telemetry/background promo/update path
- app-owned EULA/terms acceptance removed; required third-party notices retained
- user-initiated SMB/SFTP/FTP/WebDAV/cloud/Web Access preserved

## Companion invariant

Only `dw.filemanager.core.Companion.present(Context)` evaluates `nextapp.fx.rk`: package lookup -> signer verification -> boolean. The literal exists only in that helper and the required package-visibility query. No cache/state/time/product/version/installer/broadcast/UI/network/persistence surrounds it.

## Durable stages

### 01 — identity/theme
DW package/label, SDK 34 compatibility, collision-safe authorities, developer store checkbox removal, Dark Glass/AMOLED registration and Pixel-blue active channels.

### 02 — companion boolean
Single signer-verified companion helper; normal capability consumers migrated off the legacy state provider.

### 03 — trial/time-window/status removal
Update/Refresh/status UI, trial tutorial, time-window state/persistence/import/export and trial/status resources physically removed.

### 04 — commerce/product/acquisition removal
App-owned IAB, public BillingClient API/proxies, product/SKU/acquisition graph, Web Access upgrade module and commerce resources/help removed.

### 05 — telemetry/DataTransport removal
BillingLogger transport root, scheduler/backend/event-store/CCT graph and Android DataTransport components removed by method-level cuts and proven reachability.

### 06 — neutral namespace + JNI
App-owned implementation -> `dw.filemanager.*`; useful module code -> `dw.filemanager.ext.*`; shared shaded runtime -> `dw.filemanager.runtime.*`; old `play_billing`/live `Plus*` implementation names removed; four ABI JNI exports migrated to `Java_dw_filemanager_NativeFileAccess_*`.

### 07 — legal/vendor/background-network cleanup
First-run app-owned EULA/legal gate and obsolete privacy surface removed; vendor support/help/Web Access branding removed; SoundManager Flash fallback replaced with HTML5 Audio-only shim; no telemetry/update/promo startup/background network path.

### 08 — UI branding/drawer/DW artwork
Drawer body resolves `menuBackground`; Android UI/resources/locales rebranded; FX-branded resource IDs/files migrated at stable numeric IDs; DW adaptive/legacy/splash/root/TextEdit artwork installed.

### 09a–09d — lean finalization / Box / banned residue / `.dwconfig`
- graph-proven orphan resource pruning;
- hard-coded NextApp Box redirect removed; callback validates OAuth `state` + `code` generically;
- remaining app-owned trial/commerce/state residue stripped;
- `.fxconfig` -> `.dwconfig` migrated everywhere app-owned.

### 09e — Google Play Services/common-client removal
`tools/stages/stage09e_remove_google_services.py` physically removes the remaining Google common/client island, GoogleApiActivity/version metadata, orphaned common-GMS UI resources and the separate Google Play Store market enum/integration. Google Drive's AppAuth/browser OAuth implementation remains. Static exact replay passed; real Drive sign-in remains a device test.

### 09f — DW config filename prefix
Stage 09d remains the sole extension migration. Stage 09f changes the generated config filename prefix from `FX_...` to `DW_...` and asserts `.dwconfig` is already canonical.

### 09g — final app-owned terminology cleanup
`tools/stages/stage09g_final_wording.py` changes the root-settings `_license` SharedPreferences suffix to `_settings`, removes the stale root-help reference to the deleted Upgrade home item, rewords Web Access old-browser guidance, and renames/rewords the app-owned network-database upgrade UI as a format change. Unrelated protocol/framework terms and required OSS license names remain intact.

## Final exact replay gate

PR #4 / GitHub Actions run `33592839294` replayed every checked-in stage from the immutable 9.1.0.8 base and passed:

- canonical base SHA verification: pass
- all stage transformations: pass
- Apktool rebuild: pass
- ZIP integrity: pass
- artifact upload: pass
- rebuilt classes: `11,808`
- unsigned size: `12,641,290` bytes
- unsigned SHA-256: `d2599e878450e9af5a80a16c291cbb79fcd523aed987e65dd2f3613818e4e2fb`

The verification record was squash-merged as commit `efe768211ed57e3373e3b5465103c5a47dea0e63`.

## Signed Stage 09g device-test candidate

The exact replay artifact was signed outside GitHub with the recovered private signing identity.

- signed size: `12,785,738` bytes
- signed SHA-256: `0ee09f6f299bc0f70114d95dcac4af435b8de7eeb5f45ba2cb19b5a5bee32193`
- signer certificate SHA-256: `15:1E:70:F8:73:68:3F:66:1B:FD:9A:52:42:4B:E7:3E:C5:54:C4:A4:01:21:C6:4F:FD:42:8E:CA:ED:9D:42:21`
- JAR/v1 signature verification: pass
- APK Signature Scheme v2 RSA/SHA-256 signature verification: pass
- v2 whole-file content digest verification: pass
- ZIP integrity: pass

The v2 verifier was cross-validated against the known-working signed 9108006 reference before signing this candidate.

## Signed-APK static audit

Decoding the signed candidate itself produced 11,808 classes and verified:

- package `com.mekromn.dwfilemanager`: pass
- app label `DW File Manager`: pass
- versionCode `9109000`: pass
- target SDK 34: pass
- GMS descriptors / manifest entries: zero
- `play_billing`: zero
- NextApp network endpoints: zero
- `fxconfig`: zero
- `.dwconfig`: present
- whole-word trial: zero
- whole-word billing: zero
- purchase/purchased/purchases: zero
- IAP: zero
- paid: zero
- `state_trial`: zero
- `time remaining`: zero
- Google Play wording/integration: zero
- companion external package: exactly one smali helper occurrence + one manifest query
- root `_license` preference suffix: zero
- stale root-help `Upgrade`: zero

## Remaining gates

The current APK is a **device-test candidate**, not yet declared final. Remaining runtime validation:

1. install + cold startup on the Pixel 9 Pro XL / Android 16;
2. Settings opens; Dark Glass/AMOLED themes and drawer/header appearance;
3. `.dwconfig` export/import and `DW_...` generated filename;
4. local browsing/copy/move/delete/search and root mode;
5. Media section;
6. SMB/SFTP/FTP/WebDAV;
7. cloud providers, especially Google Drive login after GMS removal and real Box login after neutral callback handling;
8. Web Access including HTML5 audio playback;
9. verify no obsolete Refresh/Upgrade/trial/purchase/legal UI reappears.

The signed file exists and is statically verified. Runtime/device acceptance is now the main blocker to calling it final.
