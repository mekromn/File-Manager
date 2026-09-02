# Stage 10 — final release audit + minimal app-wide companion gate

Source: immutable FX 9.1.0.8 baseline SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`, replayed through every checked-in stage on merged `main` commit `ed3c383b829b8c0d6573745934049f9268d6eaee`.

## Companion architecture

The final companion design deliberately replaces every original/per-feature companion/capability blocker with one process-wide startup gate.

Verified transformation:

- 27 distributed `Companion.present(Context)` checks removed across 26 files;
- exactly one remaining caller: `dw.filemanager.DWApplication.onCreate()`;
- exactly one `nextapp.fx.rk` literal in the packaged app, located only in `dw.filemanager.core.Companion`;
- helper performs one `PackageManager.getPackageInfo(packageName, 0)` lookup;
- success -> `true`;
- `NameNotFoundException` -> `false`;
- no signer/hash check;
- no version or installer check;
- no state/cache/persistence;
- no timer/product/account/broadcast/UI/network logic;
- no installed-app enumeration in the helper;
- no legacy `lh/n.j(Context)` / `lh/n.l(Context)` companion probes remain.

Because target SDK 34 package visibility would otherwise filter `getPackageInfo`, the manifest uses `android.permission.QUERY_ALL_PACKAGES`; the companion package name itself does not appear in the manifest. This preserves the single package-name literal and the one-operation boolean helper.

If the one startup boolean is false, `DWApplication.onCreate()` terminates before normal DW initialization. If true, the rest of the app runs without any further companion checks.

## Network allowlist

Stage 10 inventories every packaged HTTP/HTTPS literal and requires every one to be classified. Final merged replay:

- unique HTTP(S) literals: 53
- explicit user/runtime feature literals: 35
- inert XML/library/compiler/data literals: 18
- unclassified: 0
- banned NextApp/Firebase/analytics/Crashlytics/DoubleClick/vendor telemetry literals: 0

Preserved runtime URLs belong only to deliberate user-facing functions such as Google Drive browser OAuth/API, OneDrive/Microsoft Graph, Box, SugarSync, local Web Access, and the user-invoked F-Droid package page.

## Release identity

- app label: `DW File Manager`
- package: `com.mekromn.dwfilemanager`
- versionCode: `9109000`
- versionName: `9.1.0.8`
- target SDK: 34
- `.dwconfig` canonical; generated export prefix `DW_`
- Google Play Services class/manifest island: removed

## Exact merged-main replay

GitHub Actions run `33594036238` replayed merged main from the immutable base and passed:

- canonical base SHA verification: pass
- every transformation stage: pass
- strict companion invariants: pass
- network allowlist: pass
- Apktool rebuild: pass
- ZIP integrity: pass
- artifact upload: pass
- classes: `11,808`
- unsigned APK size: `12,641,243` bytes
- unsigned APK SHA-256: `b058df28be22237301444a51195e6e93d81ccf8a3ab7fa057e3417775a98e426`

## Permanent DW signer reset

The user explicitly accepted a one-time uninstall/reinstall, so the old `FX Extended Test` signing identity was retired and a permanent DW-branded signer was created.

New certificate:

- subject/issuer: `CN=DW File Manager, O=DW File Manager, OU=Mekromn`
- RSA: 4096 bit
- certificate SHA-256: `1C:FD:89:2D:8E:CA:D5:11:45:5E:36:5C:2B:FD:4A:FF:B2:4D:F2:57:60:FF:90:5B:D6:BC:10:CE:AA:3B:5C:6E`
- valid through 2054-01-18

The private recovery bundle is kept outside GitHub. This certificate is now intended to remain immutable for future DW File Manager upgrades.

## Signed Stage 10 device-test APK

Signed exact merged-main replay artifact:

- filename: `DW-File-Manager_9.1.0.8_v9109000_MINIMAL_COMPANION_FINAL_TEST.apk`
- size: `12,787,513` bytes
- SHA-256: `1b0ed70ffbad60b501b9c1d15cd4a461421a18961e5c3ed75b9a7cfcaaadaef3`
- zipalign: pass
- APK Signature Scheme v1: pass
- APK Signature Scheme v2: pass
- APK Signature Scheme v3: pass
- ZIP integrity: pass

Post-sign payload comparison against the verified unsigned artifact found:

- missing non-signature entries: 0
- extra non-signature entries: 0
- changed non-signature entries: 0
- `classes.dex` payload: byte-identical
- `AndroidManifest.xml` payload: byte-identical
- `resources.arsc` payload: byte-identical
- packaged `nextapp.fx.rk` count: exactly 1 (`classes.dex` only)
- packaged `fxconfig` count: 0
- packaged `dwconfig` count: 4
- packaged GMS descriptor/string count: 0

## Remaining runtime gates

This is the final static/device-test candidate. Runtime verification still required on Pixel 9 Pro XL / Android 16:

1. uninstall the previous FX-Extended-signed DW build once, then install this new permanent-signer build;
2. cold start with companion installed -> normal app startup;
3. optional negative test with companion absent -> app does not initialize;
4. Settings, themes, drawer/header appearance;
5. `.dwconfig` export/import and `DW_...` filename;
6. local/root/media operations;
7. SMB/SFTP/FTP/WebDAV;
8. Google Drive browser OAuth, OneDrive, Box and SugarSync;
9. Web Access including HTML5 audio;
10. verify no retired Refresh/Upgrade/trial/purchase/legal UI reappears.
