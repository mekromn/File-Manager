# FX Extended Theme Specification

FX Extended adds first-class themes to the existing FX appearance system. These themes must remain optional and must not remove or alter upstream theme choices.

## Shared accent

Both FX Extended themes use **Pixel blue** as the primary accent:

- Accent / primary: `#4285F4`
- Selected/icon emphasis: `#4285F4`
- Focus/pressed accent should be derived from the same hue rather than changing to FX's upstream accent color.
- Text and destructive/error colors remain semantic and are not forced to blue.

## 1. Dark Glass

Purpose: a dark translucent theme with a layered glass appearance while retaining FX's information density and excellent readability.

### Surface targets

- Root/window background: very dark translucent charcoal, approximately `#D9121418` where alpha is supported.
- Main browser/file-list surface: dark translucent charcoal; do not make file text translucent.
- Toolbar/action bar: darker glass surface, approximately `#D9181B20`.
- Navigation surfaces / side panels: approximately `#CC101216`.
- Dialog/popup/card surfaces: approximately `#E61A1D22` so text remains easy to read.
- Dividers: low-contrast translucent white.
- Primary text: near-white.
- Secondary text: high-legibility light gray.
- Disabled text: visibly muted but still readable.
- Selection: Pixel blue tint; selection text/icon contrast must remain accessible.

### Behavior

- Transparency applies to backgrounds and chrome, never to foreground text or critical icons.
- Preserve translucency where FX supports it natively.
- Use system/background content showing through the app to provide the glass effect; do not fake glass with static wallpapers.
- Where platform blur is safely available, blur may be added later as an optional enhancement. The theme must remain correct without blur.
- Status/navigation bars should visually integrate with the glass chrome and continue to meet Android 16 edge-to-edge contrast requirements.

## 2. AMOLED Black Transparent

Purpose: true-black AMOLED surfaces combined with selective transparency in chrome and overlays.

### Surface targets

- File-list/root background: `#000000` (true black) wherever transparency is not useful.
- Toolbar/action bar: near-black translucent surface, approximately `#E6000000`.
- Navigation surfaces: approximately `#D9000000`.
- Dialog/popup/card surfaces: approximately `#F20A0A0A`.
- Secondary raised surfaces: `#080808` to `#101010` only where separation is required.
- Primary text: near-white.
- Secondary text: light gray.
- Dividers: very subtle gray/translucent white.
- Selection and focus: Pixel blue `#4285F4`.

### Behavior

- Maximize true-black pixels in large content regions for OLED displays.
- Do not convert text, icons, thumbnails, media, or previews to reduced-opacity content.
- Transparency is primarily for toolbars, dialogs, navigation chrome, overlays, and transient UI.
- Avoid gray backgrounds unless required to distinguish elevated surfaces.

## Theme-system integration requirements

The APK exposes an internal FX theme subsystem (`nextapp.fx.ui.fxsystem.theme.ThemeActivity`) and theme parsing concepts including `theme-set`, `theme`, `icon-theme-set`, `isTranslucent`, action-bar/background-light flags, and a theme intent (`nextapp.fx.theme.THEME`). FX Extended should extend this native mechanism rather than implement a global overlay hack.

Implementation requirements:

1. Add **Dark Glass** and **AMOLED Black Transparent** as normal selectable entries in FX Appearance/Themes.
2. Preserve every existing upstream theme and icon-theme option.
3. Persist theme selection using FX's existing preference mechanism.
4. Apply the selected theme before activity inflation to avoid light/dark flashing during launch.
5. Apply theme consistently to browser windows, settings, dialogs, file operations, viewers/editors, search, archive UI, and Web Access configuration screens where they use Android UI resources.
6. Ensure text contrast stays readable across transparent surfaces.
7. Keep semantic colors (errors, warnings, destructive actions) semantically distinct from the Pixel blue accent.
8. Verify Android 16 status/navigation bar icon contrast and edge-to-edge behavior.
9. Verify both portrait and landscape layouts and dual-pane/multi-window modes.
10. Add screenshot/regression checks for the Home screen, a file browser, Settings/Appearance, a confirmation dialog, an operation progress view, and dual-pane mode.

## Initial validation matrix

- Pixel 9 Pro XL / Android 16
- Light wallpaper behind Dark Glass
- Dark wallpaper behind Dark Glass
- AMOLED Black with a folder containing mixed thumbnails/icons
- File selection / multi-select
- Rename/delete/copy dialogs
- Settings and nested settings pages
- Text editor/viewer
- Image viewer chrome
- Archive browser
- SMB/SFTP/cloud connection screens
- Dual-pane mode
- Rotation and split-screen

## Non-goals

- No forced Material redesign.
- No reduction of FX's information density.
- No replacement of existing iconography merely for stylistic conformity.
- No globally transparent text or controls.
- No removal of upstream themes.
