# Stage 03 — trial/time-window/status structural removal

Source checkpoint: Stage 02 applied to the immutable FX 9.1.0.8 baseline.

Sequential transformations:

1. `tools/stages/stage03a_about_tutorial.py`
2. `tools/stages/stage03b_remove_update_status.py`
3. `tools/stages/stage03c_remove_timewindow.py`
4. `tools/stages/stage03d_prune_trial_resources.py`

This stage physically removes the temporary/evaluation/time-window/status UI and persistence layer. It is not a constant-return or hidden-UI patch.

## Stage 03a — About/tutorial state surface

- replaced the old 2,000+ line About implementation with a small native DW File Manager About activity;
- removed the tutorial trial-option collection loops and trial-start path;
- removed the trial checkbox callback arm;
- removed the trial tutorial registration;
- deleted `nextapp/fx/plus/ui/k.smali`;
- deleted the final temporary integer compatibility adapter `lh/n.j(Context)` after its last caller disappeared.

## Stage 03b — retired Update/Refresh/status screen

- removed `nextapp.fx.plus.ui.update.UpdateActivity` from the manifest;
- removed `UpdateHomeItem` from the home module XML and runtime registration;
- removed the two obsolete settings registrations that existed only for the retired update/status screen while retaining the useful network/Web Access settings registration;
- removed update/status-only switch arms from R8-shared classes at method/branch granularity;
- deleted the dedicated update/status implementation classes:
  - `nextapp/fx/plus/ui/UpdateHomeItem`;
  - `nextapp/fx/plus/ui/update/UpdateActivity`;
  - `me/a`, `me/c`, `me/d`, `me/e`, `me/f`, `me/g`, `me/i`, `me/k`, `me/l`, `me/m`.

The surviving `me/b`, `me/h`, and `me/j` classes are R8-shared and retain unrelated normal functionality.

## Stage 03c — time-window persistence engine

Physically removed:

- `jb/a.i:J` cached expiration field;
- `jb/a.m(Context)J`;
- `jb/a.p(Context)Z`;
- `jb/a.q(Context)Z`;
- `mb/l.G(J)V` persistence writer;
- `trialPlusExpiration` SharedPreferences key usage;
- `trialexp` settings export archive entry;
- `trialexp` settings import/parse/persistence path.

The import/export exception-handler/control-flow metadata was repaired rather than leaving stale labels or dead catch ranges.

## Stage 03d — remaining temporary-state UI/resources

- removed the obsolete `j.b` temporary-state flag itself and all reads/writes;
- removed trial-only home asterisk/trailing-note behavior;
- removed the unused `be/w(Context)` expired-trial constructor while preserving `be/w` itself because R8 shares the class as a generic dialog subtype in normal UI;
- deleted the dedicated upgrade/tutorial extension marker and page (`plus/ui/g`, `plus/ui/l`) and their TutorialActivity registration/loop;
- removed 19 trial/status/upgrade-tutorial string resources and matching `public.xml` declarations, including the old 7-day-trial copy and the stale warning that themes require the old upgrade/trial system.

## Full Stage 03 rebuild verification

Applied the four scripts sequentially to a fresh copy of the Stage 02 decoded tree, then rebuilt with pinned Apktool 3.0.3.

Unsigned Stage 03 checkpoint APK:

- SHA-256: `337692fd5b477f3bdbfa82d4a75a0162d6a126aa38ce59a39b7ee5d06f3f7832`
- size: 13,014,819 bytes
- Apktool build: success
- ZIP integrity (`unzip -t`): success

Independent pinned baksmali 3.0.10 disassembly of the rebuilt `classes.dex`:

- `classes.dex` SHA-256: `4541f77f102632817191336de75d4881eaaca965516570930ba5c059b6fc74d2`
- class files: **12,065**
- Stage 02 class files: 12,080
- net class-definition reduction in Stage 03: **15**

Rebuilt-DEX reference counts for the removed model are all zero:

- `lh/n.j(Context)`: 0
- `jb/a.m(Context)`: 0
- `jb/a.p(Context)`: 0
- `jb/a.q(Context)`: 0
- `mb/l.G(J)`: 0
- `trialPlusExpiration`: 0
- `trialexp`: 0
- `UpdateActivity`: 0
- `UpdateHomeItem`: 0
- `plus/ui/k`: 0
- retired tutorial `plus/ui/g`: 0
- retired tutorial `plus/ui/l`: 0
- `j.b` temporary-state flag: 0

A case-insensitive `trial` scan of the rebuilt executable smali produces no app-specific trial occurrence; the only raw substring matches before filtering were the unrelated words `Industrial` and `Techno-Industrial`. A case-insensitive resource scan produces no `trial` occurrence after Stage 03.

## Important scope boundary

Stage 03 does **not** claim that the complete old commerce/store subsystem is gone yet.

The useful Media/Network/Web Access implementation still lives under legacy `plus`-named packages pending neutral namespace migration, and the old app-owned store/IAB/BillingClient graph plus associated purchase/upgrade resources still has to be structurally removed. Those are the next stages.

Likewise, Google DataTransport/telemetry reachability, broader Google runtime cleanup, EULA/vendor asset consolidation, full DW namespace/JNI migration, adaptive icon replacement, drawer-body theme hook, resource-orphan pruning, final signing, and device launch/regression testing remain pending.

This is an unsigned structural checkpoint, not a user-test APK or release candidate.

## Next stage

Stage 04 will re-derive the current call graph from this exact Stage 03 tree and remove the app-owned store/IAB/BillingClient graph without deleting R8-shared utility/media/network code. Dedicated commerce classes will be deleted by reachability; mixed R8 classes will lose only the commerce-specific methods/switch arms. The APK must rebuild and independently disassemble before telemetry/DataTransport pruning begins.
