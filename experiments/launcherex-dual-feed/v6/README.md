# LauncherEx × DW dual feed V6 — Android verifier repair

## Device evidence

The V5 device log repeatedly rejects `dw.filemanager.feed.DwFeedRegistry.create(...)` before `DwFeedService` can initialize:

`VerifyError ... [0xB3] register v9 has type Reference java.lang.Object but expected Reference: java.lang.String`

That is a DEX verifier/type-flow bug in the feed host, not a new virtual-display or Shizuku policy failure.

## Exact root cause

`create()` has 9 locals and 7 parameters, so Java parameter `p0` is physical register `v9` and is the String feed session id. The activity-launch catch handler used `move-exception p0`, changing that same physical register to `Throwable`. On the SecurityException + successful-Shizuku path, execution branches back to `:launch_scheduled`, where `p0` is passed to `DwFeedRegistry$$ExternalSyntheticLambda0.<init>(String)`.

At that join Android correctly merges the normal-path String and catch-path Throwable to Object, then rejects the constructor call because it requires String.

## V6 repair

V6 keeps the session-id parameter untouched. The catch Throwable is stored in local `v0`, and only the catch handler's `instance-of` and two `describe(Throwable)` calls are redirected to `v0`.

Only four non-header bytes in `classes2.dex` change. No instruction width, branch target, catch range, method size, manifest entry, primary DEX, DW page implementation, LauncherEx code, virtual-display policy or Shizuku transport logic changes.

## Artifact

`DW-File-Manager_9.1.0.8_v9109040_LAUNCHEREX_DUAL_FEED_V6_VERIFIER_FIX.apk`

APK SHA-256: `5f29fe239c88e4677ac54629d46b675c00be614fd94f722f69f3efb5bca3cddd`

`classes2.dex` SHA-256: `f050568b6d3267b8b1ca25a10167676a48fda7e6f746ef495cf4665bb60b0372`

Signer SHA-256: `a66c6e2f8cdca4dba6bcde92230bf91a162d767df217f09bbbab8194185afdbf`

Package/version remain `com.mekromn.dwfilemanager`, `versionCode 9109040`, `versionName 9.1.0.8`.

V5 → V6 payload-entry audit: excluding regenerated `META-INF` v1 signature metadata, only `classes2.dex` changes. `AndroidManifest.xml` and `classes.dex` are byte-identical.

## Device test

Keep LauncherEx V2 installed. Install V6 directly over V5 without uninstalling or clearing data, then open **DW Home**. This build specifically removes the V5 verifier blocker so the next result can reach the actual display/activity launch path.