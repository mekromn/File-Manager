#!/usr/bin/env python3
"""Build FX Extended with the standalone FX Plus License key bridge.

This layers on top of build_fxextended_theme_test.py. It keeps FX Plus gated by
an installed `nextapp.fx.rk` license-key package, while fixing the upstream
signature comparison that cannot succeed after FX Extended is re-signed.
Google Play in-app billing initialization is disabled; the standalone Plus key
is the entitlement path.
"""
import hashlib
import struct
import zipfile
import zlib
from pathlib import Path

import build_fxextended_theme_test as base

base.OUT_FINAL = base.OUT_ROOT / 'FX-Extended_9.1.0.8_FULL_PLUS_KEY_DarkGlass_AMOLED_PixelBlue_TEST.apk'


def patch_plus_license_key_bridge(dex: bytes) -> bytes:
    # lh.n.l(Context), guarded FX 9.1.0.8 baseline.
    # Upstream compares nextapp.fx.rk's signature to Context.getPackageName().
    # FX Extended has a new signature, so substitute nextapp.fx.rk for the
    # current-package lookup. The key package must still exist or upstream's
    # existing NameNotFoundException path leaves Plus disabled.
    off = 0x35AC1A
    old = bytes.fromhex('6e 10 db 06 0b 00 0c 0b')
    new = bytes.fromhex('1a 0b 4f a3 00 00 00 00')  # const-string v11, string@0xa34f = nextapp.fx.rk
    if dex[off:off + len(old)] != old:
        raise AssertionError('Plus-license bridge target does not match guarded FX 9.1.0.8 baseline')
    out = bytearray(dex)
    out[off:off + len(old)] = new

    # PlusExtension.onCreate: force upstream's googleIabDisable branch true.
    # The standalone nextapp.fx.rk key remains available through the existing
    # non-IAB path.
    iab_off = 0x388402
    if out[iab_off:iab_off + 2] != bytes.fromhex('0a 00'):  # move-result v0
        raise AssertionError('IAB-disable target does not match guarded FX 9.1.0.8 baseline')
    out[iab_off:iab_off + 2] = bytes.fromhex('12 10')        # const/4 v0, #1

    # Repair DEX header integrity after code edits.
    out[12:32] = hashlib.sha1(out[32:]).digest()
    struct.pack_into('<I', out, 8, zlib.adler32(out[12:]) & 0xFFFFFFFF)
    return bytes(out)


def build_unsigned_with_plus_bridge(manifest, arsc, registry, dark, amoled):
    base.WORK.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(base.BASE, 'r') as zin:
        dex = patch_plus_license_key_bridge(zin.read('classes.dex'))

    replacements = {
        'AndroidManifest.xml': manifest,
        'resources.arsc': arsc,
        'res/ox.xml': registry,
        'res/fx_dark_glass.xml': dark,
        'res/fx_amoled_black_transparent.xml': amoled,
        'classes.dex': dex,
    }

    with zipfile.ZipFile(base.BASE, 'r') as zin, zipfile.ZipFile(base.OUT_UNSIGNED, 'w', allowZip64=True) as zout:
        existing = set()
        for zi in zin.infolist():
            name = zi.filename
            if base.is_old_signature(name):
                continue
            data = replacements.get(name, zin.read(name))
            existing.add(name)
            nzi = base.copy_zipinfo(zi)
            if name == 'resources.arsc':
                nzi.compress_type = zipfile.ZIP_STORED
                nzi.extra = base.make_alignment_extra(zout.fp.tell(), name, 4)
            else:
                nzi.extra = b''
            zout.writestr(nzi, data)

        for name in ('res/fx_dark_glass.xml', 'res/fx_amoled_black_transparent.xml'):
            if name not in existing:
                zi = zipfile.ZipInfo(name, (1981, 1, 1, 1, 1, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                zout.writestr(zi, replacements[name])
    return base.OUT_UNSIGNED


base.build_unsigned = build_unsigned_with_plus_bridge

if __name__ == '__main__':
    base.main()
    with zipfile.ZipFile(base.OUT_FINAL, 'r') as z:
        dex = z.read('classes.dex')
        assert dex[0x35AC1A:0x35AC22] == bytes.fromhex('1a 0b 4f a3 00 00 00 00')
        assert dex[0x388402:0x388404] == bytes.fromhex('12 10')
    print('PLUS LICENSE: requires installed nextapp.fx.rk')
    print('GOOGLE IAB: disabled')
