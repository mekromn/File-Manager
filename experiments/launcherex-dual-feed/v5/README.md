# LauncherEx × DW dual feed V5 — REJECTED

V5 removed the blocking `Process.waitFor()` from the Shizuku display-launch fallback, but the device log exposed a lower-level DEX verifier defect before the feed host could execute.

## Device result

Android 16 repeatedly rejected:

`dw.filemanager.feed.DwFeedRegistry.create(...)`

with:

`VerifyError ... [0xB3] register v9 has type Reference java.lang.Object but expected Reference: java.lang.String`

`DwFeedService.onCreate()` therefore could not initialize `DwFeedRegistry`, leaving LauncherEx on `Starting DW Home...`.

## Root cause

`create()` has nine locals, so String parameter `p0` is physical register `v9`. The activity-launch catch handler used `move-exception p0`, retyping that register as `Throwable`. On the SecurityException + successful-Shizuku path it then branches to `:launch_scheduled`, where `p0` is passed to `DwFeedRegistry$$ExternalSyntheticLambda0.<init>(String)`.

The verifier correctly merges the normal-path `String` and catch-path `Throwable` to `Object`, then rejects the constructor call because it requires `String`.

## Artifact retained for traceability

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V5_NONBLOCKING_SHIZUKU_LAUNCH.apk`

APK SHA-256: `f714c4b82a396a7210f86d83db8a704fa3b6da0302af19baa8db6e81136b68a8`

`classes2.dex` SHA-256: `0dd577791c1aea092eebcaeb25b25cd30b39bcfbe31d810392a2c399fbab0a15`

Package/version/signing identity remained correct, but **V5 is not a valid device candidate** because of this verifier failure.

The repair continues in V6 by keeping `p0/v9` as the String session id and storing the caught Throwable in local `v0` instead.