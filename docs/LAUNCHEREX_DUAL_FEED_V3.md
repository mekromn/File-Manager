# LauncherEx dual feed V3 — Android 16 phase isolation

## Device evidence from V2

On Pixel 9 Pro XL / Android 16, the LauncherEx feed page reached the DW host and displayed:

`DW Home unavailable`  
`create_failed:SecurityException`

V2's `create_failed` catch covered both `DisplayManager.createVirtualDisplay(...)` and `startActivity(...setLaunchDisplayId(...))`, so that result did not distinguish the rejected operation.

## V3 change

V3 deliberately changes **DW only**. LauncherEx V2 remains the exact client/pager/settings build.

- virtual-display flags changed from `OWN_CONTENT_ONLY | PRESENTATION` to `0`;
- display creation has its own catch and reports `display_create_failed:<type>:<message>`;
- Activity launch onto that display has its own catch and reports `activity_launch_failed:<type>:<message>`;
- timeout remains `activity_timeout`;
- DW catalog navigation reports `navigate_failed:<type>:<message>`;
- exception messages are sanitized/truncated before being sent to the visible feed diagnostic.

A zero-flag virtual display is intentionally the least-privileged private configuration. This removes optional flag-policy ambiguity before we test whether Android 16 separately rejects launching a normal Activity onto an app-created display.

## Exact device candidate

- filename: `DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V3_DIAGNOSTIC.apk`
- SHA-256: `c2c73191c6b0c56697990cfc244a72d1e52c58e8a82758c2217f3f84c98ac99f`
- package: `com.mekromn.dwfilemanager`
- versionCode: `9109040`
- signer SHA-256: `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`

## Binary isolation

Compared with the delivered V2 DW feed APK, the only non-signature entry that changes is `classes2.dex`.

- V2 classes2: `3c773ce8f62b6111a1195d657fcfeb86aa8b0f9dc24cfae962101522478c832c`
- V3 classes2: `daa0d6cab92c4d9c276830f20d2f29ac373b980db4f69ab11b6e192e8377c6e6`

`AndroidManifest.xml`, `resources.arsc`, and `classes.dex` remain byte-identical to V2.

## Test interpretation

- real DW Home appears: display + activity placement are accepted; continue to Recently Updated.
- `display_create_failed:...`: Android rejects the virtual display itself.
- `activity_launch_failed:...`: virtual display exists, Android rejects launching the DW Activity onto it.
- `activity_timeout`: launch returned but `DwFeedActivity` did not become ready.
- `navigate_failed:...`: Activity is alive but DW's page navigation path failed.
