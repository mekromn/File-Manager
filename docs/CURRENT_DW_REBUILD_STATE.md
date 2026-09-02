# Current DW File Manager rebuild state

Updated: 2026-09-01

This is the durable handoff for the structural DW File Manager rebuild. A transient decoded tree is never authoritative unless the transformation is checked into `tools/stages/` and its rebuild/audit is recorded under `docs/checkpoints/`.

## Immutable inputs

- accepted base: FX 9.1.0.8 / versionCode 9108 / SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- known-working reference only: FX Extended 9108006 / SHA-256 `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- Apktool 3.0.3
- smali/baksmali 3.0.10
- private recovered FX Extended signing identity remains outside GitHub

## Final target

- label: **DW File Manager**
- application ID: `com.mekromn.dwfilemanager`
- neutral app-owned namespace: `dw.filemanager.*`
- useful extended modules: `dw.filemanager.ext.*`
- compatibility target SDK: 34
- Dark Glass + AMOLED Black Transparent, Pixel blue `#4285F4`
- opaque top header; drawer body matches popup-menu surface
- new DW adaptive icon; no upstream vendor artwork/branding
- no app-owned commerce/trial/status/product acquisition system
- no telemetry/DataTransport/background promo/update network path
- deliberate SMB/SFTP/FTP/WebDAV/cloud/Web Access networking preserved
- app-owned EULA/terms acceptance removed; third-party notices retained

## Companion invariant

Only `dw.filemanager.core.Companion.present(Context)` may evaluate the external companion:

1. package `nextapp.fx.rk` lookup;
2. missing -> false;
3. signer verification;
4. boolean return.

No cache/state/version/installer/account/time/product/broadcast/UI/network/persistence is permitted. The external package literal may survive only in the helper and the required Android package-visibility query.

## Durable verified stages

### Stage 01 — identity/theme
`tools/stages/stage01_identity_theme.py` / `docs/checkpoints/STAGE01_IDENTITY_THEME.md`

Unsigned SHA-256 `a1ac8f21d5778f34c8da84a086bd670523664dace788fe0c058cf0e8001f701f`.

### Stage 02 — single companion boolean
`tools/stages/stage02_companion_state.py` / `docs/checkpoints/STAGE02_COMPANION_STATE.md`

Unsigned SHA-256 `9045477eaf34d546eb7d2154355e55c8b124862582f871a5044a8ff38376063e`.

### Stage 03 — trial/time-window/status removal
`stage03a` through `stage03d` / `docs/checkpoints/STAGE03_TRIAL_STATUS_REMOVAL.md`

- Update/Refresh/status UI and trial tutorial removed;
- time-window state/persistence/import/export removed;
- trial/status resources removed.

Unsigned SHA-256 `337692fd5b477f3bdbfa82d4a75a0162d6a126aa38ce59a39b7ee5d06f3f7832`; rebuilt classes 12,065.

### Stage 04 — commerce/product/acquisition removal
`stage04a` through `stage04i` / `docs/checkpoints/STAGE04_COMMERCE_REMOVAL.md`

- app-owned IAB package removed;
- public BillingClient API/proxies removed;
- acquisition/product/SKU graph removed;
- Web Access upgrade module/remote loader removed;
- commerce Android/help resources removed or neutralized.

Unsigned SHA-256 `5e2f8955b82821f6d2945c4e4c5b60a33367bfab991a4452b9a33a4a52fbca4f`; rebuilt classes 12,005.

### Stage 05 — telemetry/DataTransport removal
`stage05a` through `stage05g` / `docs/checkpoints/STAGE05_DATATRANSPORT_REMOVAL.md`

- BillingLogger transport root removed;
- 56 unreachable shaded classes pruned;
- DataTransport scheduler/backend/event-store/CCT graph removed method-by-method and by proven reachability;
- zero DataTransport/CCT/event-store markers in rebuilt DEX.

Unsigned SHA-256 `0ebd351fa60422c3e1ea7a670754ea8c12e8ef49c92b59d8034c5f34b1481086`; rebuilt classes 11,895.

### Stage 06 — neutral namespace + JNI
`stage06a` through `stage06c` / `docs/checkpoints/STAGE06_NAMESPACE_JNI.md`

- 549 app-owned `nextapp.*` classes migrated to `dw.filemanager.*`;
- useful legacy extended modules migrated to `dw.filemanager.ext.*`;
- 111 reachable R8-shared generated helpers migrated to `dw.filemanager.runtime.*`;
- old `play_billing` namespace and live `Plus*` identifiers removed;
- four ABI JNI bridges migrated to `Java_dw_filemanager_NativeFileAccess_*`;
- zero old `Lnextapp/...` descriptors and zero `plus` tokens in DW executable/resources.

Unsigned SHA-256 `27fdb08054cf2d82a311be407f4a891a9cf0c272031aa3d889f11d6699c54f21`; rebuilt classes 11,895.

### Stage 07 — legal/vendor/background-network cleanup
Scripts:

- `tools/stages/stage07a_remove_legal_gate.py`
- `tools/stages/stage07b_remove_privacy_surface.py`
- `tools/stages/stage07c_rebrand_help_web.py`
- `tools/stages/stage07d_remove_dead_gms.py`
- `tools/stages/stage07e_html5_audio.py`
- `docs/checkpoints/STAGE07_LEGAL_NETWORK.md`

Verified:

- first-run app-owned EULA/license acceptance flow and state physically removed;
- vendor-owned legal/privacy assets removed while third-party notices remain;
- obsolete Privacy Information settings row/click branch removed;
- help/Web Access vendor support links and NextApp/standalone FX branding removed from packaged assets;
- four vendor branding PNGs deleted;
- Google Drive reachability graph proves 9 GMS classes required by user-initiated Drive auth; four unreachable GMS/lifecycle/Dynamite files deleted;
- Web Access SoundManager2/Flash fallback replaced with 1,181-byte HTML5 Audio-only shim;
- no vendor update/theme/support/promo/telemetry endpoint remains;
- startup path contains local/device/module/cache initialization only; no outbound request;
- no telemetry/update/promo background service/receiver remains.

Current Stage 07e unsigned checkpoint:

- size 12,891,901 bytes
- SHA-256 `262444c8ab906d04c840cab148f862e80c3fe832e6cef18015a03f127f090782`

### Explicit Box OAuth release blocker

Two executable references to `https://android.nextapp.com/_boxredirect` remain solely in the Box OAuth flow. Box currently exact-matches configured OAuth redirects. The embedded upstream Box client registration cannot be changed from APK code. Do not hide/encode this string and call it removed.

Resolution must be one of:

- DW-controlled/configurable Box OAuth credentials + neutral HTTPS/loopback redirect; or
- remove Box support if zero vendor references takes priority.

An experimental redirect-omission path is possible only if the upstream Box application has a compatible single registered redirect and requires a real login test before acceptance.

## Current next stage — Stage 08: UI/resource branding and icon

Start from verified Stage 07e tree.

1. Inventory remaining `fx`-named app-owned Android resource IDs/visible values and migrate branding-specific identifiers without changing generic technical meanings accidentally.
2. Implement the drawer **body** theme hook so drawer surface/transparency equals the popup-menu surface for the new themes.
3. Create and install a new DW File Manager adaptive icon; remove all remaining upstream app icon/logo resources.
4. Rebuild and independently inspect resources/DEX for vendor-visible branding.
5. Run orphan resource/dead asset pruning that is safe after Stages 03–07.
6. Checkpoint Stage 08 to GitHub.

After Stage 08: resolve Box blocker, final versioning/signing, full structural/network audit, then device startup/settings/local/root/Media/network/cloud/Web Access regression testing.

No APK is complete until the final file exists, is signed/verified, and passes the acceptance checklist.
