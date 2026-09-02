# Stage 08 — drawer/theme surface + DW branding/icon checkpoint

Source: verified Stage 07e tree reconstructed from the immutable FX 9.1.0.8 baseline through checked-in stages 01–07e.

Transformations:

- `tools/stages/stage08a_drawer_menu_surface.py`
- `tools/stages/stage08b_rebrand_android_icon.py`
- generated binary artwork under `assets/dw-icons/`

## Stage 08a — drawer body uses popup-menu surface

The actual slide-out drawer body is created in `bg/f` and previously called `ef/g.w()`, which resolves the active theme's `windowBackground`.

Stage 08a adds `ef/g.dwMenuBackground()` which resolves `fg/n.f` (`menuBackground`) and falls back to `windowBackground` only if the theme does not define a menu surface. Only the drawer-body call is changed to this helper; other windows retain their existing background behavior.

This implements the requirement that Dark Glass / AMOLED drawer-body transparency match popup menus exactly rather than using a separate flat/opaque window surface.

## Stage 08b — full Android DW branding/resource migration

Applied across Android resources/locales:

- visible `FX` branding replaced with DW naming;
- `FX Connect` -> `DW Connect`;
- `FX TextEdit` -> `DW TextEdit`;
- viewer/chooser/executor/archive/media/root/helper labels changed to DW equivalents;
- `item_about_fx`, `item_fx_connect`, `item_fx_textedit` migrated to neutral DW resource names while preserving their public numeric IDs;
- branded drawable/mipmap identifiers migrated at their existing public IDs (`i144/i288`, root/TextEdit variants, splash and logo);
- no resource filename containing an FX/NextApp brand token remains;
- at the historical Stage 08 checkpoint, `.fxconfig` was intentionally left unchanged for compatibility. This is superseded by Stage 09d, which migrates the format token/extension to `.dwconfig` at the user's request.

## New DW icon family

The old FX artwork is physically replaced.

Generated artwork is committed under `assets/dw-icons/` and is copied into the rebuilt app by Stage 08b. The icon system uses:

- dark file/folder treatment;
- Pixel blue `#4285F4` accent;
- white `DW` monogram;
- separate root and TextEdit variants;
- adaptive launcher background + foreground;
- legacy xxhdpi/xxxhdpi launcher PNGs;
- DW splash mark.

The icon assets are generated deterministically by `.github/workflows/generate-dw-icon-assets.yml` and committed as normal repository assets, so Stage 08b itself has no Pillow/font runtime dependency.

## Verification

Rebuilt with pinned Apktool 3.0.3 and independently disassembled with pinned baksmali 3.0.10.

Final Stage 08 unsigned APK:

- size: `12,891,720` bytes
- SHA-256: `185a69ec5828a0809aeea24a57f09e9673918d64ec1ed76d69f0a433860bc4ae`
- `classes.dex` SHA-256: `68b0397a0e177247da8b0853d59b575ae63343d89d3706b1523324f1841d4ba4`
- rebuilt classes: `11,890`
- ZIP integrity: clean

Structural/UI assertions:

- exactly one drawer-body call to `ef/g.dwMenuBackground()`;
- helper resolves `menuBackground` with `windowBackground` fallback;
- zero uppercase `FX` / `NextApp` branding hits in Android resources or packaged assets;
- zero legacy FX/NextApp-branded Android resource filenames;
- zero old `nextapp.*` Java class descriptors;
- zero legacy `play_billing` namespace;
- zero `plus` token in the migrated DW implementation namespace;
- exactly two `nextapp.fx.rk` occurrences remain: the pure companion helper and Android package-visibility query;
- four JNI bridge libraries remain migrated to `Java_dw_filemanager_NativeFileAccess_*`.

## Explicit unresolved boundary at Stage 08

Two executable literals for `https://android.nextapp.com/_boxredirect` remained in the legacy Box OAuth flow at this checkpoint. Stage 09b later removes this vendor redirect literal and switches callback acceptance to validated `state` + `code`; real-device Box sign-in remains a regression-test requirement.

Stage 08 does not claim final signing, final orphan pruning, or device regression testing.
