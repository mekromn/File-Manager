# Stage 09e — Google Play Services/common-client removal

Source: canonical Stage 09d/09f DW chain replayed from the immutable FX 9.1.0.8 base.

Transformation: `tools/stages/stage09e_remove_google_services.py`.

## Purpose

Remove the remaining Google Play Services common/client island without sacrificing Google Drive. Drive authentication is implemented through the surviving AppAuth/browser flow and does not require the old `com.google.android.gms` common-client island.

## Structural changes

Stage 09e:

- removes isolated GMS-only methods/interfaces from R8-shared classes while preserving their unrelated file-manager/media/network behavior;
- removes the pure Google common/client class island and GoogleApiActivity/version manifest metadata;
- removes orphaned `common_google_play_services_*` strings, Google sign-in button/version resources and related public resource declarations;
- removes the separate Google Play Store app-market enum/integration (`GOOGLE_PLAY`, `com.android.vending`, `app_market_google`) while preserving Amazon, F-Droid and Samsung market handling;
- preserves the AppAuth/Google Drive implementation and its dedicated `btn_google_signin_dark` UI resources.

## Hard acceptance assertions

A replayed tree after Stage 09e must contain:

- zero `Lcom/google/android/gms/` descriptors;
- zero `com.google.android.gms` implementation/manifest strings;
- zero Google Play Store market integration (`GOOGLE_PLAY` / `com.android.vending`);
- zero orphaned common-GMS sign-in artwork;
- the normal AppAuth/Google Drive classes/resources must remain buildable.

Stage 09e is accepted only after the repository's exact replay workflow applies every checked-in stage in lexical order from the immutable 9.1.0.8 base, rebuilds the unsigned APK successfully, and passes ZIP integrity.

Device regression testing of Google Drive sign-in remains a release gate even after static replay succeeds.
