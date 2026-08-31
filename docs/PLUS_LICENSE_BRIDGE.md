# FX Plus license-key bridge

FX 9.1.0.8 contains the Plus implementation in the main APK, but legitimately enables it through the separately installed **FX File Explorer: Plus License** package, `nextapp.fx.rk`.

## Why a renamed build loses Media and Internet/Network

Upstream method `lh.n.l(Context): boolean` loads `nextapp.fx.rk`, loads the current application package, and compares their signing certificates. This works for official FX because both packages are signed by NextApp. FX Extended is intentionally renamed to `com.mekromn.fxextended` and must use a different project signing key, so the upstream comparison always fails even when the user owns and has installed the official Plus key.

That failed entitlement state produces the base/free home screen: **Media** and **Internet and Network** are absent and **Upgrade** is shown.

## FX Extended behavior

`tools/build_fxextended_plus_key_bridge.py` preserves the paid-key requirement but adapts the signature check for the renamed build:

- `nextapp.fx.rk` must still be installed and visible to PackageManager.
- If the key package is missing, upstream's existing failure/exception path leaves Plus disabled.
- The renamed APK is not treated as the signing reference because it cannot possess NextApp's private signing key.
- Google Play in-app BillingClient initialization is forced onto FX's existing disabled path.
- The standalone `nextapp.fx.rk` license-key route remains the supported entitlement mechanism.

## Guarded binary locations for FX 9.1.0.8

The builder is SHA-256 guarded against the canonical 9.1.0.8 base and verifies exact pre-patch bytes before modifying either location.

- Plus license comparison rewrite: DEX file offset `0x35AC1A` (`lh.n.l(Context)`, instruction `0x59`).
- Google IAB disable: DEX file offset `0x388402` (`PlusExtension.onCreate`, instruction `0x13`).

After changes, the builder regenerates the DEX SHA-1 signature and Adler-32 checksum, then performs the normal APK rebuild/alignment/v1+v2 signing verification.
