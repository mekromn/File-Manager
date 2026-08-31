# FX 9.1.0.8 Theme-System Research

Baseline APK SHA-256: `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`

This file records concrete reverse-engineering findings from the canonical FX 9.1.0.8 APK so later work does not need to rediscover the obfuscated resource layout.

## Native theme subsystem

Relevant code/string evidence in `classes.dex` includes:

- `nextapp.fx.ui.fxsystem.theme.ThemeActivity`
- `http://android.nextapp.com/fx/themes.xml`
- `nextapp.fx.intent.extra.GET_THEMES`
- `nextapp.fx.theme.THEME`
- `nextapp.fx.theme.THEME_ICON`
- `theme-set`
- `theme`
- `icon-theme-set`
- `icon-theme`
- `isTranslucent`
- `setTranslucent`
- `updateTranslucentState`

FX therefore has a real theme-module parser and should be extended through that mechanism rather than by a global UI-overlay hack.

## Master internal registry

The internal theme module registry is stored in the obfuscated binary XML resource:

- APK path: `res/ox.xml`

It defines these built-in theme sets:

- `material_light`
- `material_dark`
- `translucent`

The existing translucent entries are:

- `translucent_light` → resource ID `0x7f130041`
- `translucent_dark` → resource ID `0x7f130040`

Do **not** overwrite either one for FX Extended. Dark Glass and AMOLED Black Transparent are additions, not replacements.

## XML resource-id mapping

Resource type `0x13` contains the theme XML resources. Important mappings from the 9.1.0.8 resource table:

- `0x7f130040` = `theme_translucent_dark` = APK file `res/rI.xml`
- `0x7f130041` = `theme_translucent_light` = APK file `res/LQ.xml`
- `0x7f13003e` = `theme_materiald_midnight` = APK file `res/QN.xml`
- `0x7f13003c` = `theme_materiald_gray` = APK file `res/4b.xml`
- `0x7f130039` = `theme_materiald_blue_gray` = APK file `res/2N.xml`
- `0x7f13003a` = `theme_materiald_blue_gray_sp` = APK file `res/OK.xml`

There are currently 67 XML entries (`0x00` through `0x42`) and no unused slot in this resource type, so two genuinely new internal theme XML resources require proper resource-table growth/rebuild. Reusing an unrelated existing resource ID is intentionally rejected as fragile.

## Existing Translucent Dark structure

`res/rI.xml` parses as a native FX `<theme>` and sets:

- `light=false`
- `translucent=true`
- `actionBarBackground`
- `actionBarBackgroundOpaque`
- `drawerHeaderBackground`
- `menuBackground`
- `windowBackground`
- `contentBackground`
- `headerForeground`
- `headerBackground`
- `headerBackgroundInactive`
- `headerLowContrastIcons`
- `headerBackgroundLight`
- `specialTextColor`
- `defaultTrimBase`
- `defaultTrimAccent`
- `progressComplete`
- `progressRemaining`
- `boxBackground`
- `boxPressedBackground`
- `boxEffectOnlyPressedBackground`
- `boxFlatPressedBackground`
- `selectionBackground`
- `selectionPressedBackground`
- `editorBackground`
- `editorText`
- `editorIndex`
- `editorHex`

This is the template to follow for the two FX Extended translucent themes.

## Existing translucent palette values

Useful baseline colors from resource type `color` (`0x06`):

- `theme_trans_box_base` = `#1FFFFFFF`
- `theme_trans_box_pressed_base` = `#3FFFFFFF`
- `theme_trans_dark_drawer_header_bg` = `#7F546E7A`
- `theme_trans_dark_header_bg` = `#00000000`
- `theme_trans_dark_header_fg` = `#FFFFFFFF`
- `theme_trans_dark_header_inactive_bg` = `#278F8F8F`
- `theme_trans_dark_window_bg` = `#D737474F`
- `theme_trans_selection_background` = `#2FFFFFFF`
- `theme_trans_selection_pressed_background` = `#3FFFFFFF`

These values explain the current translucent appearance but are **not** the target FX Extended palettes.

## FX Extended target integration

Preferred implementation:

1. Keep all upstream entries intact.
2. Add two new native FX theme XML resources.
3. Add both entries to the theme registry, preferably grouped adjacent to the existing `translucent` set unless a clean new theme-set title resource is added at the same time.
4. Use `#4285F4` as the common accent/selection/focus color.
5. Set `translucent=true` for both.
6. Dark Glass uses layered translucent charcoal surfaces.
7. AMOLED Black Transparent uses true `#000000` for large content regions and selective black translucency for chrome/overlays.
8. Rebuild resources normally rather than binary-patching resource IDs in place.
9. Regression-test launch/theme persistence, dual-pane, dialogs, viewers/editors, operations UI, status/navigation bars, rotation, and split-screen.

See `docs/THEMES.md` for the visual palette/behavior specification.
