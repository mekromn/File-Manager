# FX Extended unified test build — 9108002

Baseline: FX File Explorer 9.1.0.8 (`9108`) with SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`.

## Identity

- Application ID: `com.mekromn.fxextended`
- Label: `FX Extended`
- Version code: `9108002`
- Compatibility target: Android API 34 while retaining the 9.1.0.8 codebase, to preserve the legacy Views inset behavior on Android 15/16 and keep the storage-access action above three-button navigation.
- Signed with the existing FX Extended project key so this build updates earlier FX Extended tests.

## Unified changes

- Dark Glass theme with Pixel Blue `#4285F4`.
- AMOLED Black Transparent theme with Pixel Blue `#4285F4` and true-black content surfaces.
- Drawer/sidebar now obtains the active theme `contentBackground` rather than falling back to the legacy `windowBackground`/Material `#424242` surface. This makes the drawer follow Dark Glass/AMOLED correctly.
- Media, network/cloud, sharing, Web Access, app-management and related extended modules remain available when the user's installed official feature-key package `nextapp.fx.rk` validates.
- Renamed/re-signed application compatibility for the installed official key is retained without exposing purchase UI.
- Play in-app purchase initialization is disabled and its manifest permission/query/Proxy activities/metadata are removed.
- Legacy product-specific internal namespace and symbols are migrated to neutral `nextapp.fx.extd` / `Extd*` naming.
- The legacy paid-feature promotional tab is removed from the old add-on container; the container is retained only as a neutral Extensions surface for Themes and Developer/Root functionality.
- The legacy home-screen Upgrade item is removed from the module registry rather than hidden.
- The old Web Access lite-mode upgrade module/tab and its remote promotional iframe asset are removed.
- The obsolete in-app-purchase paragraph is removed from packaged help.
- Legacy product/purchase resource names and strings are neutralized while unrelated database-migration terminology and unrelated third-party/library `plus` symbols are left untouched.

## Binary patches (9.1.0.8 baseline only)

- Installed-key compatibility branch: `classes.dex` offset `0x35ac1a`.
- Disable Play purchase initialization: `classes.dex` offset `0x388402`.
- Drawer theme getter: `classes.dex` offset `0x3a9bdc`, `Lef/g;->w()I` → `Lef/g;->i()I`.
- Legacy promotional tab removal and tab-index correction: `UpdateActivity`/neutralized `ExtrasActivity` `onCreate` code at `0x399820`.
- Legacy promotional page refresh/click entry points are made non-executable.

## Verification performed

- Base SHA-256 guard passed.
- Package/resource identity remains `com.mekromn.fxextended` / `FX Extended`.
- Target SDK is 34; version code is 9108002.
- Both custom theme resource IDs resolve.
- Drawer patch bytes verified.
- Legacy home Upgrade module is absent from semantic `res/q6.xml` items.
- Play billing manifest permission, metadata, query intents and Proxy activities are absent.
- No FX-specific legacy `nextapp.fx.plus`, `PlusCore`, `PlusExtension`, `FX Plus`, `plus_license_key`, `UpdateActivity`, or `UpdateHomeItem` strings remain in executable DEX.
- No old Web Access Upgrade module asset or tab references remain.
- ZIP integrity passes and all stored entries are 4-byte aligned.
- JAR/v1 and APK Signature Scheme v2 structures are regenerated; v2 RSA signature and content digest verify.

Final test APK SHA-256: `dc38368a004e5ade94629fcd3e7e12fbeae3efc45fcab2e791cb044be936f847`.
