# Stage 09g — release-candidate terminology cleanup

Source: canonical immutable FX 9.1.0.8 base replayed through all checked-in stages.

Transformation: `tools/stages/stage09g_final_wording.py`.

Stage 09g is deliberately narrow and runs after the canonical Stage 09d `.fxconfig` -> `.dwconfig` migration, Stage 09e Google Play Services/common-client removal, and Stage 09f `FX_` -> `DW_` export-prefix finalization.

## Applied

- root-enabled SharedPreferences suffix `_license` -> `_settings` because it stores ordinary root settings, not legal/entitlement state;
- stale root help no longer tells users to open the deleted Upgrade home item and instead points to Settings / Developer-Root;
- Web Access old-browser guidance says to use a modern browser rather than using the retired product word `upgrade`;
- app-owned network database strings/resources are renamed/reworded from an upgrade action to a database-format change;
- unrelated protocol/framework/third-party terms such as HTTP Upgrade, SQLite schema callbacks and legally required OSS license names are not mutated.

## Release-candidate gate

The repository exact-replay workflow must apply every checked-in stage in lexical order from the immutable 9.1.0.8 APK, rebuild successfully with pinned Apktool, pass ZIP integrity and upload the unsigned replay artifact.

After replay succeeds, the resulting exact artifact may be signed with the recovered private signing identity for device testing. Device tests remain required before calling the build final.
