# Current DW File Manager rebuild state

Updated: 2026-09-02

This file is the durable handoff for the DW File Manager structural rebuild. The authoritative implementation is the checked-in stage scripts under `tools/stages/` plus verification records under `docs/checkpoints/`. A transient decoded tree is never treated as authoritative by itself.

## Immutable inputs

- accepted base: FX 9.1.0.8 / versionCode 9108 / SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- known-working reference only: FX Extended 9108006 / SHA-256 `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- Apktool 3.0.3
- smali/baksmali 3.0.10
- recovered signing identity remains private outside GitHub

Use `.github/workflows/export-rebuild-state.yml` to export the checked-in rebuild state as a GitHub Actions artifact after interruptions.

## Final target/invariants

- **DW File Manager** / `com.mekromn.dwfilemanager`
- app-owned namespace `dw.filemanager.*`
- useful extended modules `dw.filemanager.ext.*`
- neutral R8-shared runtime `dw.filemanager.runtime.*`
- target SDK 34 compatibility behavior
- Dark Glass + AMOLED Black Transparent with exact Pixel blue `#4285F4`
- opaque top header and drawer body matching popup-menu surface
- new DW adaptive icon; no upstream vendor artwork/visible branding
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
- four unreachable GMS/lifecycle/Dynamite remnants deleted while the 9-class Drive-auth GMS path is retained;
- SoundManager2/Flash fallback replaced with a 1,181-byte HTML5 Audio-only compatibility shim;
- startup/background component audit shows no telemetry/update/promo network path.

### Stage 08 — UI branding, drawer surface, DW artwork

Files:

- `tools/stages/stage08a_drawer_menu_surface.py`
- `tools/stages/stage08b_rebrand_android_icon.py`
- `assets/dw-icons/*`
- `.github/workflows/generate-dw-icon-assets.yml`
- `docs/checkpoints/STAGE08_UI_BRANDING.md`

Verified:

- actual drawer-body `bg/f` no longer uses `windowBackground`; it calls `ef/g.dwMenuBackground()` which resolves `menuBackground` with `windowBackground` fallback;
- Android UI/resources/locales contain zero uppercase `FX` / `NextApp` branding hits;
- FX-branded resource IDs and files migrated to DW identifiers at the same public numeric IDs;
- old FX artwork physically replaced by dark DW folder/monogram artwork with Pixel blue `#4285F4`;
- adaptive foreground/background, legacy launcher icons, splash, root and TextEdit variants are generated and committed;
- `.fxconfig` is deliberately retained as a configuration-file compatibility extension, not branding;
- rebuilt classes: `11,890`;
- final Stage 08 unsigned APK size: `12,891,720` bytes;
- final Stage 08 unsigned SHA-256: `185a69ec5828a0809aeea24a57f09e9673918d64ec1ed76d69f0a433860bc4ae`;
- `classes.dex` SHA-256: `68b0397a0e177247da8b0853d59b575ae63343d89d3706b1523324f1841d4ba4`.

## Explicit unresolved Box OAuth blocker

Two executable references to `https://android.nextapp.com/_boxredirect` remain solely in Box OAuth. The upstream Box OAuth client is server-registered against that callback, so blindly changing it would break Box authentication.

Final resolution must be one of:

- a DW-controlled/configurable Box OAuth client + neutral callback;
- a proven compatible redirect-omission/generic callback path validated by a real Box login;
- remove Box support if absolute zero vendor references takes priority.

Do not hide/encode the old URI and call it removed.

## Current next stage — Stage 09: lean finalization + Box decision + signing readiness

Start from verified Stage 08.

1. Run safe orphan/dead resource and class pruning after all removed subsystems/branding.
2. Re-audit every surviving HTTP/HTTPS endpoint and classify it by explicit user-facing network feature.
3. Resolve or explicitly gate the Box OAuth blocker without silently breaking cloud behavior.
4. Set final version code/name and verify package/manifest/provider/action identity.
5. Sign with the recovered private DW/FX-Extended signing identity.
6. Verify v1/v2 signatures, DEX/resource/ZIP integrity and alignment.
7. Generate final before/after class/resource/network report and banned-term audit.
8. Produce an actually existing downloadable APK only after all static acceptance checks pass.
9. Device regression test: startup, Settings, local browsing, root, Media, SMB/SFTP/FTP/WebDAV, cloud providers and Web Access.

No APK is complete until the final file exists, is signed/verified, and passes the acceptance checklist.
