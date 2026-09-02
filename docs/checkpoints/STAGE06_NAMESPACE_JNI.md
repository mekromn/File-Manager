# Stage 06 — neutral namespace and JNI migration

Source checkpoint: verified Stage 05 tree.

Transformations:

- `tools/stages/stage06a_namespace_migration.py`
- `tools/stages/stage06b_legacy_identifier_cleanup.py`
- `tools/stages/stage06c_jni_migration.py`

## Structural migration completed

- Migrated 549 surviving app-owned `nextapp.*` classes into neutral `dw.filemanager.*` namespaces through real smali descriptor/path changes.
- Migrated useful former `nextapp.fx.plus.*` Media/Network/Web Access implementation to `dw.filemanager.ext.*`.
- Renamed live legacy `PlusCore`, `PlusExtension`, `PlusHomeItem` and `PlusRegistry` class identifiers to neutral `Ext*` names.
- Migrated the 111 fully reachable shared shaded helpers from `com.google.android.gms.internal.play_billing` to `dw.filemanager.runtime` rather than deleting generic behavior by package name.
- Renamed app-owned package/reflection/module/preference identity strings to the DW identity.
- Removed obsolete vendor-package recognition entries from the package map; the external companion package is no longer present there.
- The external companion package remains only in the pure companion helper and manifest package-visibility query.
- Renamed useful `plusui` XML module/catalog/interaction-handler resources to `extui` while retaining their public resource IDs.
- Removed the obsolete composite product icon and its two overlay drawables/public declarations.
- Removed `plus` wording from the migrated DW runtime/resources, including generic arithmetic/tutorial prose, so no legacy token remains in DW executable code or Android resources.
- Neutralized the remaining vendor-branded Android diagnostic/help strings.

## JNI migration

`nextapp.xf.shell.NativeFileAccess` was migrated to `dw.filemanager.NativeFileAccess`.

All four ABI copies of `libnative-file-access.so` were patched in place. The new exported symbols are:

- `Java_dw_filemanager_NativeFileAccess_nativeMkfifo`
- `Java_dw_filemanager_NativeFileAccess_nativeGetLastModified`

Verified with `readelf -Ws` in the rebuilt APK for:

- arm64-v8a
- armeabi-v7a
- x86
- x86_64

No old `Java_nextapp...NativeFileAccess` symbol remains.

## Final Stage 06 checkpoint

Unsigned APK:

- size: 12,948,521 bytes
- SHA-256: `27fdb08054cf2d82a311be407f4a891a9cf0c272031aa3d889f11d6699c54f21`
- Apktool rebuild: success
- ZIP integrity: success

Independent rebuilt-DEX disassembly with pinned baksmali 3.0.10:

- total classes: 11,895
- `dw.filemanager.*` classes: 661
- `dw.filemanager.ext.*` classes: 223
- `dw.filemanager.runtime.*` classes: 111
- `nextapp.*` class files: 0
- old `com.google.android.gms.internal.play_billing` class files: 0
- old `Lnextapp/...` descriptor files: 0
- old live `Plus*` class identifier files: 0
- `plus` token files under `dw.filemanager`: 0
- Android resource `plus` hits: 0
- Android resource `nextapp` hits: 0
- manifest application class: `dw.filemanager.DWApplication`

## Explicit remaining vendor-name blockers

Stage 06 is not a final no-vendor audit yet.

Three executable/config occurrences remain deliberately visible for the next network/vendor stage:

1. `nextapp.fx.rk` in `dw.filemanager.core.Companion` — required external compatibility datum.
2. `nextapp.fx.rk` in the manifest package-visibility query — required Android visibility datum.
3. Two Box OAuth redirect string occurrences using `https://android.nextapp.com/_boxredirect` — user-initiated Box authentication currently depends on this upstream registered redirect endpoint.

The Box redirect URLs are **not accepted as final DW references**. They must be replaced by a working DW-controlled/local redirect design or Box support must be deliberately reworked before release. They were not blindly rewritten because doing so would silently break Box authentication.

App-owned EULA/privacy/help/web branding assets still contain vendor text and are handled in the next stage together with their runtime call sites.

## Next stage

Stage 07 must:

- remove the app-owned EULA/terms acceptance gate and vendor legal/privacy assets while retaining legally required third-party notices;
- remove/replace vendor help/support links and Web Access branding;
- classify remaining outbound vendor/update/support endpoints by caller;
- resolve the Box OAuth redirect blocker without silently breaking cloud authentication;
- audit the remaining Google common/Drive OAuth classes and manifest `GoogleApiActivity`/version metadata, removing Google common runtime only where no surviving user-initiated cloud path requires it;
- verify there is still no telemetry/background network initialization.

No user-test APK is produced by this checkpoint.
