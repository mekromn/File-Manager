# Stage 19 — Original DW Folder Palette Expansion

Base: device-confirmed v9109007 (`ba8e08f58685bdd2db29a05e86e668b7f34470b5`).

## User-visible target

Expose the expanded folder palette in both existing UI surfaces:

1. Theme → Icons → Dynamic Material.
2. The Select Icon dialog used by bookmarks/Home items.

Both surfaces should consume the same underlying palette definition so future additions/removals cannot drift.

## Palette direction

The public `msikma/osx-folder-icons` repository was used only as inspiration for the breadth of color choices. Its README states that the icon artwork itself is derived from Apple's macOS High Sierra folder icon and remains © Apple; therefore DW must NOT bundle or copy those pixels.

DW will instead generate original variants from DW File Manager's existing folder geometry/artwork. Existing Blue, Copper, Khaki, Green, and Plain remain. Add genuinely distinct DW-original variants inspired by the useful color categories found upstream: Aqua, Dark Blue, Gray, Orange, Pink, Red, Violet, White, and Yellow. Generic is already represented by Plain. Blue/Green are already represented. `Syft` is project-specific upstream and is not automatically imported.

## Invariants

- No Apple-derived artwork or upstream PNG/ICNS/PSD assets are bundled.
- Preserve the existing folder geometry, overlays, shape selector, and icon rendering behavior.
- New colors must work with all existing folder overlays/special-folder glyphs, not only the plain folder.
- Theme palette and Select Icon palette must stay synchronized.
- Do not regress v9109007 runtime behavior, file associations, JNI bridge, branding, privacy/telemetry removals, or signing identity.
