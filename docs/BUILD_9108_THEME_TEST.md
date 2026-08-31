# FX Extended 9.1.0.8 theme test build

## Baseline

The builder is locked to the exact upstream FX File Explorer 9.1.0.8 APK:

- Version code: `9108`
- Target SDK: `36`
- Expected SHA-256: `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`

The upstream APK is immutable input and must not be committed to this repository.

## Test build identity

- Application ID / manifest package: `com.mekromn.fxextended`
- Label: `FX Extended`
- Java component namespace remains `nextapp.fx.*` because those are the actual compiled class names.
- The upstream `sharedUserId="nextapp.fx"` is removed so the renamed app does not attempt to share an Android UID with official FX.
- Package-qualified provider authorities, task affinities, and the dynamic receiver permission are rewritten to `com.mekromn.fxextended.*` where isolation is required.
- Internal FX action names, module names, Java class names, the root companion query, and the existing AppAuth redirect scheme are intentionally left intact unless runtime testing proves a specific one must change.

## Added themes

Two additional native FX themes are inserted into the existing `Translucent` theme set. Existing upstream themes are not replaced.

### Dark Glass

- New XML resource ID: `0x7f130043`
- Resource key: `theme_fxext_dark_glass`
- Resource path: `res/fx_dark_glass.xml`
- Translucent charcoal surfaces with layered dark glass chrome.
- Pixel blue accent: `#4285F4`.

### AMOLED Black Transparent

- New XML resource ID: `0x7f130044`
- Resource key: `theme_fxext_amoled_black_transparent`
- Resource path: `res/fx_amoled_black_transparent.xml`
- True `#000000` content/editor backgrounds with selectively translucent black chrome.
- Pixel blue accent: `#4285F4`.

## Build

Requirements:

- Python 3
- Python package `cryptography`
- JDK tools `keytool` and `jarsigner`

Example:

```bash
FX_BASE_APK=/path/to/fx-9.1.0.8.apk \
python3 tools/build_fxextended_theme_test.py
```

The generated APK is written under `build/` by default. The test signing key is generated under `build/signing/` and is deliberately ignored by Git. Preserve the same key if subsequent builds need to install as updates over the first FX Extended test build.

The script performs the following checks before considering the APK complete:

1. Verifies the baseline SHA-256.
2. Rewrites the binary Android manifest and resource package identity.
3. Adds two new XML entries to `resources.arsc` rather than overwriting an upstream resource.
4. Adds the two native theme records to FX's theme registry.
5. Re-signs the APK with JAR/v1 signing and APK Signature Scheme v2.
6. Recomputes and verifies the v2 content digest and RSA signature.
7. Restores 4-byte alignment for every uncompressed ZIP entry after JAR signing.
8. Runs ZIP integrity checks and confirms both added theme files are present.

## Signing / compatibility note

The original NextApp private signing key is not available. A modified APK must therefore use an FX Extended signing key and cannot be an in-place signature-compatible update of the official `nextapp.fx` package. The renamed application ID is intentional so the test build can be installed separately.

Changing both package identity and signing identity can affect integrations whose credentials or entitlements are bound to the official package/certificate. In particular, Play Billing / FX Plus entitlement and some OAuth/cloud-provider callbacks must be runtime-tested. This project must not bypass upstream licensing; any integration that fails because of identity binding should be redesigned or documented rather than defeated.
