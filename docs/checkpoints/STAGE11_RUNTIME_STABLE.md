# Stage 11 — Runtime Stable Baseline

Status: **ON-DEVICE PASS**

Validated on: Pixel 9 Pro XL / Android 16

Merged code commit: `e16750106f3fc228ee796735f651e015346f1a5c`

Device-test build:

- App: DW File Manager
- package: `com.mekromn.dwfilemanager`
- versionName: `9.1.0.8`
- versionCode: `9109004`
- signed APK SHA-256: `9ee50172b1fea09a86f7f70e36b72b90a71c66f7f369d1aacc9d8f011933e2a1`
- permanent signer SHA-256: `1C:FD:89:2D:8E:CA:D5:11:45:5E:36:5C:2B:FD:4A:FF:B2:4D:F2:57:60:FF:90:5B:D6:BC:10:CE:AA:3B:5C:6E`

## Device-confirmed working paths

The user confirmed the v9109004 build works after testing the paths that had previously crashed:

- Settings
- Images
- Videos
- Recent
- Apps submenus
- Cleaning Tools

## Runtime fixes that define this baseline

### 1. Companion architecture

All former distributed companion-controlled feature branches now execute their ordinary/default paths directly. There is exactly one app-wide startup package-presence check for `nextapp.fx.rk`.

### 2. Settings ART VerifyError

Stage 07b previously removed the Privacy preference by deleting a raw smali block from `ph/m.smali`. That block also initialized `v8` to integer `2`, while surviving code later used `v8` for `new-array`, causing ART to reject `ph.m` with an undefined-register `VerifyError`.

The fix removes the Privacy UI while preserving the original shared `const/4 v8, 0x2` initialization and adds a regression guard.

### 3. AppDetailsActivity explicit target

The migrated class is `dw.filemanager.ext.ui.app.AppDetailsActivity`, but `gf/c.smali` still used `setClassName()` with stale target `dw.filemanager.ui.app.AppDetailsActivity`.

The explicit class-name string is now migrated to the real class.

### 4. JNI bridge — critical invariant

The old Stage 06c implementation changed JNI symbol strings inside the existing ELF libraries in-place. Although tools could display the renamed symbols, the ELF dynamic hash metadata was not rebuilt, so Android could not resolve them at runtime and threw `UnsatisfiedLinkError` for:

- `NativeFileAccess.nativeGetLastModified()`
- `NativeFileAccess.nativeMkfifo()`

Stage 06c now **rebuilds `libnative-file-access.so` from source using the Android NDK** for all four ABIs:

- arm64-v8a
- armeabi-v7a
- x86
- x86_64

Required exported JNI symbols:

- `Java_dw_filemanager_NativeFileAccess_nativeMkfifo`
- `Java_dw_filemanager_NativeFileAccess_nativeGetLastModified`

The build verifies the dynamic symbol table and requires a valid ELF `.gnu.hash` or `.hash` section. **Do not revert to in-place JNI symbol string patching.**

## Release policy

Treat v9109004 / Stage 11 as the current known-good runtime baseline. Any subsequent cleanup or optimization must preserve these on-device working paths and the rebuilt JNI bridge behavior.
