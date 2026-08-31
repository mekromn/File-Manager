# FX Extended

FX Extended is an experimental extension project built from the latest upstream **FX File Explorer** APK while preserving FX's fast, information-dense file-manager design and privacy-first character.

## Upstream baseline

The canonical baseline for this project is:

- App: FX File Explorer
- Package: `nextapp.fx`
- Version: `9.1.0.8`
- Version code: `9108`
- Minimum SDK: `21`
- Target SDK: `36`
- Compile SDK: `36`
- SHA-256: `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`
- Upstream signing certificate SHA-256: `02:F7:97:30:22:3F:45:4C:CD:10:84:14:EC:06:36:18:B7:62:A4:76:8A:ED:FB:64:46:2D:84:16:F4:17:C6:77`

The original upstream APK is treated as **immutable input**. Generated/decompiled files and modified builds must never replace the canonical baseline.

## Initial direction

The first development phase focuses on improving FX as a file manager rather than replacing its design:

1. Reproducible decode / patch / rebuild / sign / verify pipeline.
2. Android 16 behavior audit and compatibility testing.
3. Safe file operations: verification, transactional moves, recovery, operation history, and optional trash/undo.
4. Advanced search and saved smart-folder queries.
5. APK power tools: inspect, extract, compare, share, and split-package support.
6. Optional Shizuku-backed privileged file access, explicitly user-authorized.
7. Modern image/media handling, including HDR-aware image inspection.
8. Native media-stack modernization after compatibility tests.

See `docs/BASELINE.md` and `docs/ROADMAP.md` as the project develops.

## Important signing note

Any modified APK must be signed with a project-controlled signing key because the upstream NextApp private signing key is not available. This means modified builds will not be signature-compatible updates over the official `nextapp.fx` installation. The build/patch system must make this fact explicit and must regression-test features that may depend on the original signing identity.

## Status

Baseline selected and audited. Repository bootstrap in progress.
