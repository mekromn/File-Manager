# Stage 02 — single companion/state migration checkpoint

Source checkpoint: Stage 01 applied to the immutable FX 9.1.0.8 baseline.

Transformation: `tools/stages/stage02_companion_state.py`.

## Applied

- added one pure `dw.filemanager.core.Companion.present(Context)` boolean helper;
- helper performs only package lookup for external compatibility package `nextapp.fx.rk`, SHA-256 signer calculation, comparison against the known upstream signer, and boolean return;
- helper has no cache, stored state, version check, installer check, account check, timestamps, countdown, product/SKU data, callback, broadcast, UI, persistence, or network operation;
- migrated 25 ordinary three-state capability consumers directly to the boolean helper;
- migrated 3 direct callers of the old complex verifier to the boolean helper;
- deleted the old complex `lh/n.l(Context)` verifier method;
- deleted the old cached/provider fields `lh/n.b`, `lh/n.c`, and `lh/n.d` and all references to them;
- removed a stale side-effect-only integer capability-state probe;
- changed the useful home-section availability path to consume the boolean directly, with its temporary/trial flag fixed absent;
- removed trial/acquisition/status work from `PlusExtension.onResume`, retaining only the legitimate network-database migration warning after a successful companion check;
- simplified the old about/status summary helper to the application name rather than rendering product/source/status text.

## Deliberately intermediate

The legacy About screen still contains two calls to `lh/n.j(Context)`. For this checkpoint only, `lh/n.j` is a compatibility adapter that maps the new boolean to `3` when present and `1` when absent. It contains no temporary/trial state and can never return the old value `2`.

This adapter is **not** part of the final architecture. Stage 03 replaces/removes the old About/trial/status implementation and then deletes `lh/n.j` completely.

Stage 02 also intentionally leaves the old trial/time-window persistence implementation in place long enough to remove it structurally in Stage 03. The remaining callers were enumerated rather than hidden:

- `jb/a.q(Context)` remains in the old About screen, settings export, and retired status screen;
- `jb/a.p(Context)` remains in TutorialActivity, the old About screen, a trial-start switch arm, and retired status screen;
- `jb/a.m(Context)` remains in the old About/status screens, settings export, and within the legacy trial helper itself;
- persistence strings `trialPlusExpiration` remain in the old trial helper/writer;
- settings archive entry `trialexp` remains in the old settings import/export paths.

Those are Stage 03 deletion targets and are not claimed as removed here.

## Structural verification

Source-tree scan after applying Stage 02:

- old `lh/n.l(Context)` verifier references: **0**;
- old `lh/n.b/c/d` state-field references: **0**;
- files calling `Companion.present(Context)`: **29**;
- files calling the temporary `lh/n.j(Context)` adapter: **1** (`AboutActivity.smali` only; two call sites);
- manifest package-visibility query for `nextapp.fx.rk`: present intentionally.

## Build verification

Rebuilt using pinned Apktool 3.0.3.

Unsigned Stage 02 APK:

- SHA-256: `9045477eaf34d546eb7d2154355e55c8b124862582f871a5044a8ff38376063e`
- size: 13,025,617 bytes
- Apktool build: success
- ZIP integrity (`unzip -t`): success

The rebuilt `classes.dex` was then independently disassembled with pinned baksmali 3.0.10:

- rebuilt `classes.dex` SHA-256: `e79614afed178bb16ec13e7227db4ae4854eab7441548550a9df9db11ca9b354`;
- disassembled class files: **12,080** (12,079 baseline classes + the new companion helper);
- `dw/filemanager/core/Companion.smali`: present;
- old complex verifier references in rebuilt DEX: **0**;
- temporary integer-adapter reference files in rebuilt DEX: **1**.

This remains an unsigned structural checkpoint, not a user-test APK or release candidate.

## Next stage

Stage 03 will structurally remove the time-window/trial/status layer rather than making it inert:

1. replace the old About implementation with a compact DW About/OSS-notices path;
2. remove trial/time-window methods and state field in `jb/a`;
3. remove `trialPlusExpiration` storage and its writer;
4. remove `trialexp` import/export branches, including their exception/control-flow metadata;
5. remove the tutorial trial-start registration/path and trial-start switch arm;
6. remove the retired status/update screen cluster and call sites;
7. delete the temporary `lh/n.j` adapter after its final caller disappears;
8. remove orphaned trial/status strings/resources and their `public.xml` declarations;
9. rebuild and independently disassemble again before advancing to commerce/BillingClient pruning.
