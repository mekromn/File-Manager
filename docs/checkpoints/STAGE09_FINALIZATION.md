# Stage 09 — lean finalization checkpoint

Source: verified Stage 08 tree reconstructed from the immutable FX 9.1.0.8 baseline through checked-in stages 01–08b.

Transformations:

- `tools/stages/stage09a_prune_removed_orphans.py`
- `tools/stages/stage09b_box_redirect_neutral.py`
- `tools/stages/stage09c_strip_banned_residue.py`
- `tools/stages/stage09d_dwconfig_extension.py`

## Stage 09a — graph-proven orphan resource pruning

Removes 12 resources left orphaned by the physically removed update/license paths. The stage first proves that every public resource ID and symbolic resource reference is unreachable from surviving smali/resources, then removes the localized strings, public declarations, and obsolete update overlay artwork.

## Stage 09b — neutral Box OAuth callback handling

Removes the hard-coded `https://android.nextapp.com/_boxredirect` literal from the Box authorization request and changes the WebView callback path to accept a callback only when the returned OAuth `state` matches the per-request state and a non-null authorization `code` is present.

Static acceptance requires zero `nextapp.com` endpoint literals after this stage. A real-device Box sign-in remains a regression-test requirement; this stage does not claim server-side Box compatibility until that succeeds on-device.

## Stage 09c — final commerce/state residue teardown

Removes the final app-owned billing/trial/state remnants that survived earlier shared-R8 pruning, including the obsolete billing enum arm, purchase/BILLING permission metadata, time-remaining/payment resources, and stale commerce/trial comments/identifiers. The stage asserts the banned billing/trial terms are absent from surviving implementation/resources.

## Stage 09d — `.fxconfig` -> `.dwconfig`

At the user's request, the historical FX configuration extension/token is no longer preserved for compatibility.

Stage 09d performs a tree-wide, case-insensitive ASCII migration of `fxconfig` -> `dwconfig` across every app-owned decoded file. The replacement is intentionally equal length (8 bytes -> 8 bytes), so it is safe for smali/resources/assets and any embedded ASCII occurrence without changing binary layout. Any app-owned path name containing `fxconfig` is renamed as well.

Hard assertions:

- the stage must find at least one legacy token/path when replayed from verified Stage 09c;
- no app-owned `fxconfig` token remains afterward;
- no app-owned filename/directory containing `fxconfig` remains;
- the resulting `dwconfig` occurrence count is at least the number of replaced content occurrences.

This intentionally means new DW builds use `.dwconfig`; legacy `.fxconfig` compatibility is not retained.

## Reproducible replay gate

`.github/workflows/replay-dw-rebuild.yml` downloads the immutable 9.1.0.8 APK, verifies SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`, decodes with pinned Apktool 3.0.3, replays every checked-in stage in lexical order, rebuilds an unsigned APK, checks ZIP integrity, records class/size/hash metrics, and uploads the replay evidence as a short-lived artifact.

Stage 09d is not considered verified until that replay gate passes. Signing and device regression testing remain later gates.
