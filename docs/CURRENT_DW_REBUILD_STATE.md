# Current DW File Manager rebuild state

Updated: 2026-09-01

This file is the durable handoff/checkpoint for the structural DW File Manager rebuild. It exists so a chat/container interruption cannot silently turn an in-memory edit tree into an assumed build state.

## Immutable inputs

The accepted rebuild always starts from the untouched upstream APK:

- FX 9.1.0.8 / versionCode 9108
- SHA-256: `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- decoded smali class files: 12,079

Known-working behavioral/reference APK supplied by the user:

- FX Extended 9108006
- SHA-256: `0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c`
- decoded smali class files: 12,079
- reference only: do **not** use it as a patch/build base

The reference is useful for recovering known-working signing/package/theme/Android-inset behavior. Retired commerce/status/state implementation from it must not be inherited.

## Pinned rebuild toolchains

GitHub Actions artifacts are pinned and hash-checked:

- Apktool artifact ZIP SHA-256: `145c372cc2c9cfd3a63d8addf043b08a78aa78071ce2b467b0c3e63cadd3379d`
- smali/baksmali artifact ZIP SHA-256: `6de1696514ca9c22a60a0818edfea7584232c35fa896c40c82b0aa065d09db11`
- Apktool: 3.0.3
- smali/baksmali: 3.0.10

Use `tools/bootstrap_dw_rebuild.py` to verify and decode both APKs side-by-side. Use `tools/audit_dw_checkpoint.py` as a fast source-tree guard between structural stages. The final acceptance audit remains the stricter process in `docs/CORE_REWORK_REQUIREMENTS.md`.

## Signing identity

The previous FX Extended signing-key bundle was recovered from the user's file library and remains private. Its bytes/hash must never be committed to GitHub. The repository may document that the same signing identity is required, but the key itself stays outside version control.

## Important status boundary

A prior transient container session progressed through a series of structural experiments commonly referred to in chat as Stage 8/9/11. Those runs produced useful verified findings, but the edited source tree itself did not survive the process/container interruption.

Therefore:

- those historical results are **not** a current build input;
- their structural findings may be reproduced;
- every modification must be reapplied through checked-in scripts/patches and reverified from the immutable 9.1.0.8 base;
- no APK may be presented based only on a remembered transient checkpoint.

## Rebuild target

Final identity:

- label: `DW File Manager`
- application ID: `com.mekromn.dwfilemanager`
- app-owned implementation namespace: neutral `dw.filemanager.*`
- useful former extended modules should use a neutral namespace such as `dw.filemanager.ext.*`, not a legacy `plus` namespace
- target SDK compatibility behavior should preserve the known-working Android navigation/inset behavior recovered from the 9108006 reference

## Structural invariants to reproduce

The rebuild must physically remove, rather than deactivate or rename, the retired app-owned subsystem for:

- store/IAB bridge and public BillingClient-facing integration;
- update/status/refresh acquisition screen and home item;
- trial/evaluation/time-window state and persistence;
- SKU/product/catalog metadata used only by that subsystem;
- old commerce broadcasts/callbacks/dialogs;
- developer store-disable preference and its key/read/write logic;
- app-owned EULA/terms acceptance flow and vendor promotional/legal surfaces;
- telemetry/DataTransport paths that have no user-initiated file-manager purpose;
- unsolicited update/promo/background network paths.

Third-party notices that legally require redistribution remain as compact local OSS notices.

## Companion invariant

The only surviving compatibility gate is one pure boolean helper:

1. look up external package `nextapp.fx.rk`;
2. if missing, return false;
3. hash/check its signer against the known expected signer;
4. return the boolean result.

No cache, state object, timestamps, countdown, SKU/product information, version test, installer test, broadcast listener, refresh operation, UI, network request or persistence belongs in this path.

The external package identifier is compatibility data, not DW branding. It should appear only where technically required by the helper/package visibility mechanism.

## Historical structural findings to reproduce and reverify

The previous transient teardown established several important boundaries that should guide the scripted rebuild, but each must be re-proven after reapplication:

- useful Media/Network/Web Access implementation was mixed with legacy-named extended-module code; useful behavior must be migrated, not deleted;
- the old integer capability state represented unavailable / temporary-evaluation / companion-authorized states; temporary/evaluation state can be removed entirely once all consumers use the single boolean companion helper;
- `UpdateActivity` / `UpdateHomeItem` and related refresh/status/dialog call sites are retired and should have no dangling references;
- billing/telemetry code is R8-mixed with unrelated utility/UI/media code in several obfuscated classes, so whole-package deletion is unsafe;
- a concrete BillingLogger -> DataTransport upload root existed inside a heavily shared helper; method/branch-level removal is required before deleting transport classes by reachability;
- Android DataTransport scheduler/backend components can be removed only after their mixed-class provider/scheduler branches are severed;
- the native file-access JNI bridge contains vendor-qualified Java symbol names in four ABI libraries and must be migrated consistently if the Java bridge namespace moves.

## Theme/reference requirements

Recover the known-working native theme registration mechanics from 9108006, while applying the later corrections:

- Dark Glass;
- AMOLED Black Transparent;
- Pixel blue `#4285F4` wired to actual active/selected/focused/highlight channels;
- opaque top application header;
- navigation drawer surface/transparency matching the popup-menu surface;
- no upstream/vendor iconography in the final adaptive icon.

## Next concrete stage

1. Bootstrap a fresh decoded workspace from the immutable base + reference using the checked-in tool.
2. Check in the first transformation script/patch rather than editing the decoded tree only.
3. Reproduce identity/manifest/theme/developer-setting cleanup and rebuild.
4. Reproduce the single companion helper and remove the three-state/time-window model.
5. Remove the app-owned store/status/product graph and re-run reachability.
6. Sever DataTransport telemetry scheduler/backend branches and physically delete the now-unreachable transport graph.
7. Perform full neutral namespace/JNI migration.
8. Prune orphaned resources/help/assets.
9. Sign with the recovered private signing identity.
10. Generate before/after structural and network audits and run the full acceptance checklist.
11. Confirm the final APK file actually exists before presenting a download link.
