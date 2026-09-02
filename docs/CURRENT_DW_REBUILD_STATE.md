# Current DW File Manager rebuild state

Updated: 2026-09-01

This is the durable handoff for the structural DW File Manager rebuild. A transient decoded tree is never authoritative unless the transformation is checked into `tools/stages/` and its rebuild/audit is recorded under `docs/checkpoints/`.

## Immutable inputs

Accepted rebuild base:

- FX 9.1.0.8 / versionCode 9108
- SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- decoded classes: 12,079

Known-working reference supplied by the user:

- FX Extended 9108006
- SHA-256 `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- reference only; never a patch/build base

Pinned tools:

- Apktool 3.0.3
- smali/baksmali 3.0.10

The previous FX Extended signing-key bundle is available privately outside GitHub. Never commit it.

## Final target/invariants

- label: **DW File Manager**
- application ID: `com.mekromn.dwfilemanager`
- app-owned implementation namespace: `dw.filemanager.*`
- useful former extended modules: neutral namespace such as `dw.filemanager.ext.*`; no legacy `plus` namespace/classes/resources
- compatibility target SDK: 34, retaining the known-working legacy inset/navigation behavior from the 9108006 reference
- Dark Glass + AMOLED Black Transparent themes with exact Pixel blue `#4285F4`
- opaque top app header
- drawer body surface/transparency matched to popup-menu surface
- new DW adaptive icon and no vendor iconography
- no app-owned commerce/trial/status/product acquisition subsystem
- no analytics/telemetry/background transport/promo/update network path
- user-initiated SMB/SFTP/FTP/WebDAV/cloud/Web Access networking preserved
- app-owned EULA/terms acceptance/vendor promo/legal flow removed; legally-required third-party notices retained locally

### Companion invariant

The only compatibility gate is one pure boolean helper:

1. look up external package `nextapp.fx.rk`;
2. missing -> false;
3. verify its signer against the expected signer;
4. return boolean.

No cache, state object, timestamps, countdown, product/SKU data, version/installer test, broadcast listener, refresh operation, UI, network request or persistence is allowed around this helper.

The external package identifier is compatibility data only. It may survive only in the helper and technically required Android package-visibility declaration.

## Durable verified stages

### Stage 01 — identity/theme

Files:

- `tools/stages/stage01_identity_theme.py`
- `docs/checkpoints/STAGE01_IDENTITY_THEME.md`

Verified:

- manifest package/label moved to DW identity;
- old sharedUserId removed;
- collision-sensitive authorities/permission moved to DW package;
- target SDK metadata set to 34;
- legacy developer store checkbox removed from XML;
- Dark Glass + AMOLED theme resources registered;
- Pixel blue wired into active/selection/trim/progress channels;
- top theme action-bar surfaces opaque.

Unsigned SHA-256: `a1ac8f21d5778f34c8da84a086bd670523664dace788fe0c058cf0e8001f701f`.

### Stage 02 — single companion boolean

Files:

- `tools/stages/stage02_companion_state.py`
- `docs/checkpoints/STAGE02_COMPANION_STATE.md`

Verified:

- one pure companion-present + signer-check helper;
- normal capability consumers moved to direct boolean use;
- old complex verifier/cached provider state removed;
- no helper cache/version/installer/account/time/product/callback/UI/network/persistence.

Unsigned SHA-256: `9045477eaf34d546eb7d2154355e55c8b124862582f871a5044a8ff38376063e`.

### Stage 03 — trial/time-window/status removal

Files:

- `tools/stages/stage03a_about_tutorial.py`
- `tools/stages/stage03b_remove_update_status.py`
- `tools/stages/stage03c_remove_timewindow.py`
- `tools/stages/stage03d_prune_trial_resources.py`
- `docs/checkpoints/STAGE03_TRIAL_STATUS_REMOVAL.md`

Verified:

- native DW About surface replaces old trial/product/status construction;
- tutorial trial/start path removed;
- temporary integer capability adapter removed;
- Update/Refresh activity/home item/status classes and their isolated R8 callback arms deleted;
- expiration/time-window state, methods, persistence/import/export removed;
- expired-trial constructor removed from shared dialog class without removing unrelated uses;
- retired upgrade tutorial page/marker/resources removed;
- app resources contain no trial occurrence.

Unsigned SHA-256: `337692fd5b477f3bdbfa82d4a75a0162d6a126aa38ce59a39b7ee5d06f3f7832`.
Rebuilt classes: 12,065.

### Stage 04 — commerce/product/acquisition removal

Files:

- `tools/stages/stage04a_sever_commerce_roots.py`
- `tools/stages/stage04b_remove_iab_core.py`
- `tools/stages/stage04c_remove_acquisition_billing_api.py`
- `tools/stages/stage04d_remove_web_upgrade.py`
- `tools/stages/stage04e_remove_product_graph.py`
- `tools/stages/stage04f_strip_shared_billing_helpers.py`
- `tools/stages/stage04g_prune_commerce_resources.py`
- `tools/stages/stage04h_remove_app_commerce_residue.py`
- `tools/stages/stage04i_remove_faq_commerce.py`
- `docs/checkpoints/STAGE04_COMMERCE_REMOVAL.md`

Verified:

- app-owned IAB package physically deleted;
- public BillingClient API/proxy activities removed;
- acquisition dialog/actions/callbacks/broadcasts removed;
- dedicated product/SKU/detail graph removed;
- Web Access upgrade tab/module/remote upgrade loader removed from standalone and bundled JS;
- user-facing commerce resources removed/neutralized across locales;
- commerce FAQ text removed;
- outside the shaded generated runtime, rebuilt DEX has no commerce path.

Final Stage 04 unsigned SHA-256: `5e2f8955b82821f6d2945c4e4c5b60a33367bfab991a4452b9a33a4a52fbca4f`.
Rebuilt classes: 12,005.

### Stage 05 — telemetry/DataTransport structural removal

Files:

- `tools/stages/stage05a_sever_logging_transport.py`
- `tools/stages/stage05b_prune_unreachable_shaded.py`
- `tools/stages/stage05c_remove_transport_runtime.py`
- `tools/stages/stage05d_remove_transport_backend.py`
- `tools/stages/stage05e_strip_eventstore_bridges.py`
- `tools/stages/stage05f_strip_last_transport_mixed.py`
- `tools/stages/stage05g_prune_datatransport_graph.py`
- `docs/checkpoints/STAGE05_DATATRANSPORT_REMOVAL.md`

Verified:

- BillingLogger-to-transport send root physically removed;
- first reachability pass deleted 56 shaded classes with no surviving root;
- DataTransport discovery/scheduler Android components removed from manifest;
- scheduler/runtime/backend/event-store/CCT provider branches removed method-by-method from R8-shared classes;
- 45-class dedicated transport graph proven to have zero external roots and physically deleted;
- rebuilt DEX has no DataTransport namespace classes or CCT/event-store/database markers;
- old IAB and public BillingClient refs remain zero.

Final Stage 05 unsigned APK:

- size: 12,943,018 bytes
- SHA-256: `0ebd351fa60422c3e1ea7a670754ea8c12e8ef49c92b59d8034c5f34b1481086`
- rebuilt classes: 11,895
- ZIP integrity: clean

### Important shaded-runtime boundary after Stage 05

`com.google.android.gms.internal.play_billing` now contains 111 classes.

Fresh reachability result:

- total: 111
- external roots: 13
- reachable: 111
- unreachable: 0

These survivors include R8-shared generic callback/progress/stream/collection/backport helpers used by normal file-manager code. Do not delete them by package name. Their legacy package name is nevertheless unacceptable final DW naming and must be migrated to a neutral runtime namespace in Stage 06.

## Important native boundary

Four ABI copies of `libnative-file-access.so` contain JNI symbols tied to `nextapp.xf.shell.NativeFileAccess`. Java namespace migration must patch all four native libraries consistently with the migrated bridge name. Do not rename only the smali class.

## Current next stage — Stage 06: neutral namespace/JNI migration

Start from the verified Stage 05 tree.

1. Inventory every surviving app-owned `nextapp.*` descriptor, manifest component/action/provider/authority string, reflection/serialized class-name string and resource/module identifier.
2. Migrate ordinary app-owned `nextapp.fx.*` implementation to `dw.filemanager.*` through real smali/path changes.
3. Migrate useful former `nextapp.fx.plus.*` Media/Network/Web Access implementation to `dw.filemanager.ext.*` and rename live `Plus*` class identifiers/resources to neutral `Ext*` names.
4. Preserve external `nextapp.fx.rk` only in `Companion.present()` and the package-visibility query.
5. Migrate `nextapp.xf.shell.NativeFileAccess` to a neutral bridge and patch the JNI exported-symbol strings in all four `libnative-file-access.so` ABI libraries consistently.
6. Migrate the 111 reachable shaded generated classes from `com.google.android.gms.internal.play_billing` to a neutral DW runtime namespace without deleting their generic behavior.
7. Rebuild with Apktool; independently disassemble rebuilt DEX; verify no dangling old descriptors and no vendor/legacy `plus` implementation namespace remains except the external companion compatibility datum.
8. Checkpoint Stage 06 to GitHub before EULA/vendor/help/Google-common-network cleanup.

After Stage 06: EULA/vendor branding/help and Google common/Drive OAuth reachability audit, drawer/body UI + DW icon, resource/orphan pruning, signing, full structural/network audit, then device startup/settings/local/root/Media/network/cloud/Web Access regression testing.

No APK is complete until the final file exists, is signed/verified, and passes the acceptance checklist.
