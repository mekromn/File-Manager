# Stage 01 — identity/theme checkpoint

Source: immutable FX 9.1.0.8 baseline, SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`.

Transformation: `tools/stages/stage01_identity_theme.py`.

## Applied

- application package changed to `com.mekromn.dwfilemanager`;
- old `sharedUserId` removed;
- collision-sensitive dynamic-receiver permission and provider authorities changed to the DW package;
- external compatibility query for `nextapp.fx.rk` deliberately preserved;
- app label changed to **DW File Manager**;
- target SDK metadata changed from 36 to 34 to preserve the known-working legacy inset/navigation compatibility behavior seen in the 9108006 reference;
- stage versionCode set to `9109000` by default;
- legacy `googleIabDisable` developer checkbox removed from `pref_developer.xml` rather than hidden;
- native **Dark Glass** and **AMOLED Black Transparent** themes added using the known-working 9108006 theme model;
- top action-bar surfaces corrected to opaque values;
- Pixel blue `#4285F4` retained in active/selection/trim/progress channels;
- drawer-header surface is matched to the popup-menu surface in the theme definitions. The separate drawer-body lookup hook is handled in a later structural UI stage.

## Build verification

The script was applied to a fresh copy of the canonical decoded baseline and rebuilt with pinned Apktool 3.0.3.

Resulting unsigned checkpoint:

- SHA-256: `a1ac8f21d5778f34c8da84a086bd670523664dace788fe0c058cf0e8001f701f`
- Apktool build: success
- ZIP integrity (`unzip -t`): success

This is an intermediate unsigned structural checkpoint, not a user-test APK and not a release candidate.

## Deliberately not claimed yet

Stage 01 does **not** claim completion of:

- Java/smali namespace migration;
- old state/trial/product/store subsystem deletion;
- single companion-helper implementation;
- EULA/legal-flow cleanup;
- DataTransport/telemetry deletion;
- Google runtime reachability cleanup;
- drawer-body theme hook;
- adaptive icon replacement;
- resource orphan pruning;
- signing or device launch testing.

Those are later stages and must each rebuild successfully before final release verification.
