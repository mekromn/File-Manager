# Current DW File Manager rebuild state

Updated: 2026-09-01

This is the durable handoff for the structural DW File Manager rebuild. A transient decoded tree is never treated as authoritative unless its transformation exists as a checked-in stage and its rebuild/audit is recorded under `docs/checkpoints/`.

## Immutable inputs

Accepted rebuild base:

- FX 9.1.0.8 / versionCode 9108
- SHA-256: `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- decoded smali class files: 12,079

Known-working behavioral/reference APK supplied by the user:

- FX Extended 9108006
- SHA-256: `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- reference only; never use it as a patch/build base

The reference is used only for known-working signing/package/theme/Android-inset behavior. Its retired commerce/status/state implementation must not be inherited.

## Pinned rebuild toolchains

- Apktool 3.0.3
- Apktool artifact ZIP SHA-256: `145c372cc2c9cfd3a63d8addf043b08a78aa78071ce2b467b0c3e63cadd3379d`
- smali/baksmali 3.0.10
- smali/baksmali artifact ZIP SHA-256: `6de1696514ca9c22a60a0818edfea7584232c35fa896c40c82b0aa065d09db11`

Use `tools/bootstrap_dw_rebuild.py` to verify/decode immutable inputs and `tools/audit_dw_checkpoint.py` for fast stage guards. Final acceptance remains defined by `docs/CORE_REWORK_REQUIREMENTS.md`.

## Private signing identity

The prior FX Extended signing-key bundle was recovered from the user's file library. The key is never committed to GitHub or included in documentation/artifacts. Final DW builds should reuse that signing identity so signing does not become another installation variable.

## Final identity target

- label: **DW File Manager**
- application ID: `com.mekromn.dwfilemanager`
- app-owned namespace: neutral `dw.filemanager.*`
- useful former extended modules: neutral namespace such as `dw.filemanager.ext.*`, never a legacy `plus` namespace
- compatibility target SDK: 34, preserving the known-working legacy inset/navigation behavior observed in the 9108006 reference

The external companion identifier `nextapp.fx.rk` is compatibility data only and may survive only in the single companion helper and technically required package-visibility declaration.

## Durable verified stages

### Stage 01 — identity/theme checkpoint

Files:

- `tools/stages/stage01_identity_theme.py`
- `docs/checkpoints/STAGE01_IDENTITY_THEME.md`

Verified result:

- DW package/label established;
- old sharedUserId removed;
- collision-sensitive authorities/permission changed;
- target SDK 34 compatibility metadata set;
- developer store-disable checkbox removed from XML;
- native Dark Glass + AMOLED Black Transparent theme definitions added;
- Pixel blue `#4285F4` wired into active/selection/trim/progress channels;
- top theme action-bar surfaces made opaque;
- unsigned APK SHA-256: `a1ac8f21d5778f34c8da84a086bd670523664dace788fe0c058cf0e8001f701f`.

### Stage 02 — single companion boolean / state consumer migration

Files:

- `tools/stages/stage02_companion_state.py`
- `docs/checkpoints/STAGE02_COMPANION_STATE.md`

Verified result:

- one pure `dw.filemanager.core.Companion.present(Context)` helper performs only external package lookup + SHA-256 signer comparison + boolean return;
- no cache/state/version/installer/account/timestamp/product/callback/UI/network/persistence in the helper;
- normal capability consumers call the boolean directly;
- old complex verifier and cached state/provider fields removed;
- unsigned APK SHA-256: `9045477eaf34d546eb7d2154355e55c8b124862582f871a5044a8ff38376063e`;
- rebuilt DEX independently disassembled with pinned baksmali.

### Stage 03 — trial/time-window/status structural removal

Files:

- `tools/stages/stage03a_about_tutorial.py`
- `tools/stages/stage03b_remove_update_status.py`
- `tools/stages/stage03c_remove_timewindow.py`
- `tools/stages/stage03d_prune_trial_resources.py`
- `docs/checkpoints/STAGE03_TRIAL_STATUS_REMOVAL.md`

Verified result:

- old About trial/product/status construction replaced with small native DW About surface;
- trial tutorial/check/start paths removed;
- temporary integer capability adapter deleted;
- Update/Refresh activity, home item, dedicated status classes and isolated R8 callback arms physically deleted;
- cached expiration field and time-window methods physically deleted;
- `trialPlusExpiration` and `trialexp` persistence/import/export paths physically deleted;
- temporary-state registry flag deleted;
- expired-trial constructor deleted from R8-shared `be/w` while preserving its unrelated generic-dialog uses;
- retired upgrade/tutorial extension page and marker deleted;
- 19 trial/status/upgrade-tutorial resource strings and public declarations removed;
- final Stage 03 unsigned APK SHA-256: `337692fd5b477f3bdbfa82d4a75a0162d6a126aa38ce59a39b7ee5d06f3f7832`;
- final Stage 03 `classes.dex` SHA-256: `4541f77f102632817191336de75d4881eaaca965516570930ba5c059b6fc74d2`;
- rebuilt class files: 12,065 (15 fewer than Stage 02);
- rebuilt DEX has zero references to the removed time-window/status classes/methods/tokens;
- app resources contain no trial occurrence after Stage 03.

## Structural invariants still required

The rebuild must still physically remove rather than deactivate/rename:

- app-owned store/IAB/BillingClient integration;
- SKU/product/catalog metadata used only by commerce;
- purchase/upgrade acquisition UI/resources/callbacks/broadcasts;
- telemetry/DataTransport paths with no user-initiated file-manager purpose;
- unsolicited update/promo/background network paths;
- app-owned EULA/terms acceptance flow and vendor promotional/legal surfaces.

Third-party notices that legally require redistribution remain as compact local OSS notices.

## Companion invariant

Final helper behavior remains exactly:

1. look up external `nextapp.fx.rk`;
2. missing -> false;
3. hash/check signer against expected signer;
4. return boolean.

No cache, state object, timestamps, countdown, SKU/product data, version test, installer test, broadcast listener, refresh operation, UI, network request or persistence is permitted around this compatibility gate.

## Important R8/native boundaries

- normal Media/Network/Web Access behavior is mixed with legacy-named extended-module code; migrate useful code, do not delete it;
- commerce/telemetry code is R8-mixed with unrelated utility/UI/media code in several obfuscated classes, so whole-package deletion is unsafe;
- DataTransport removal must sever mixed-class logging/scheduler/backend roots before deleting dedicated transport classes by reachability;
- four `libnative-file-access.so` ABI libraries contain JNI names tied to `nextapp.xf.shell.NativeFileAccess`; Java namespace migration must patch all four native bridges consistently.

## Theme/UI requirements still pending

The native theme resources are present, but final UI work still includes:

- drawer **body** surface/transparency must match popup-menu surface (not only drawer header);
- final adaptive DW icon replacement;
- remove all upstream/vendor iconography/branding;
- final neutral namespace migration for useful extended modules.

## Next concrete stage — Stage 04

Re-derive the call graph from the verified Stage 03 tree, then structurally remove the app-owned store/IAB/BillingClient graph:

1. inventory `nextapp.fx.iab` and public BillingClient-facing classes/methods from the Stage 03 tree;
2. delete dedicated commerce classes whose surviving incoming-reference count is zero after roots are cut;
3. remove only commerce-specific methods/switch arms from R8-shared classes;
4. remove acquisition/product/purchase resources only after their resource IDs have zero live callers;
5. rebuild with pinned Apktool;
6. independently baksmali-disassemble rebuilt DEX and verify zero dangling deleted-type references;
7. commit Stage 04 script/checkpoint before beginning DataTransport pruning.

After Stage 04: DataTransport/Google-runtime network audit and removal, neutral DW/JNI namespace migration, EULA/vendor/help cleanup, icon/drawer UI fixes, orphan pruning, signing, full structural/network audit, then device startup/settings/file/network regression testing.

No APK should be presented to the user as complete until the final file exists, is signed/verified, and passes the acceptance checklist.
