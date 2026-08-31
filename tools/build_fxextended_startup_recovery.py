#!/usr/bin/env python3
"""Startup-safe FX Extended recovery build.

This intentionally preserves all live upstream class descriptors.  A previous
experimental unified build renamed the live `nextapp.fx.plus.*` implementation
namespace; that can break reflection and persisted state when updating an
existing FX Extended install.  This recovery builder keeps the working binary
implementation names and applies only independently verified changes:

* side-by-side FX Extended package/theme build from build_fxextended_theme_test
* targetSdk 34 compatibility window behavior for the legacy Views UI
* versionCode 9108003
* official installed `nextapp.fx.rk` key compatibility after re-signing
* Google in-app billing initialization disabled
* drawer/sidebar uses active theme contentBackground
* obsolete UpdateHomeItem module node removed from the home registry

Do not reintroduce live DEX class/package renaming without a state migration and
reflection audit.
"""
import hashlib
import struct
import zipfile
import zlib

import build_fxextended_theme_test as base

VERSION_CODE = 9108003
TARGET_SDK = 34
base.OUT_FINAL = base.OUT_ROOT / 'FX-Extended_9.1.0.8_RECOVERY_Android16_UI_COMPAT_SIDEBAR_DarkGlass_AMOLED_PixelBlue_TEST.apk'

_original_patch_manifest = base.patch_manifest


def patch_manifest_compat(axml: bytes) -> bytes:
    out = bytearray(_original_patch_manifest(axml))
    strings = base.get_axml_string_list(out)
    _, root_h, _ = base.chunk_hdr(out, 0)
    o = root_h
    while o < len(out):
        t, h, s = base.chunk_hdr(out, o)
        if t == 0x0102:
            ext = o + 16
            tag = strings[base.u32(out, ext + 4)]
            ast, asz, ac, *_ = struct.unpack_from('<HHHHHH', out, ext + 8)
            aoff = ext + ast
            for i in range(ac):
                x = aoff + i * asz
                name = strings[base.u32(out, x + 4)]
                if tag == 'manifest' and name == 'versionCode':
                    struct.pack_into('<I', out, x + 8, 0xFFFFFFFF)
                    out[x + 15] = 0x10
                    struct.pack_into('<I', out, x + 16, VERSION_CODE)
                elif tag == 'uses-sdk' and name == 'targetSdkVersion':
                    struct.pack_into('<I', out, x + 8, 0xFFFFFFFF)
                    out[x + 15] = 0x10
                    struct.pack_into('<I', out, x + 16, TARGET_SDK)
        o += s
    return bytes(out)


def patch_runtime_dex(dex: bytes) -> bytes:
    out = bytearray(dex)

    # Preserve legitimate standalone license-key recognition after package re-sign.
    off = 0x35AC1A
    old = bytes.fromhex('6e 10 db 06 0b 00 0c 0b')
    new = bytes.fromhex('1a 0b 4f a3 00 00 00 00')  # nextapp.fx.rk
    if out[off:off + len(old)] != old:
        raise AssertionError('license-key target mismatch')
    out[off:off + len(old)] = new

    # Disable Google IAB initialization through the existing upstream branch.
    iab_off = 0x388402
    if out[iab_off:iab_off + 2] != bytes.fromhex('0a 00'):
        raise AssertionError('IAB target mismatch')
    out[iab_off:iab_off + 2] = bytes.fromhex('12 10')

    # Sidebar: use active-theme contentBackground rather than windowBackground.
    drawer_off = 0x3A9BDC
    old_drawer = bytes.fromhex('6e 10 5a 36 02 00')
    new_drawer = bytes.fromhex('6e 10 4c 36 02 00')
    if out[drawer_off:drawer_off + 6] != old_drawer:
        raise AssertionError('drawer target mismatch')
    out[drawer_off:drawer_off + 6] = new_drawer

    out[12:32] = hashlib.sha1(out[32:]).digest()
    struct.pack_into('<I', out, 8, zlib.adler32(out[12:]) & 0xFFFFFFFF)
    return bytes(out)


def remove_axml_item_named(axml: bytes, target_name: str) -> bytes:
    strings = base.get_axml_string_list(axml)
    _, root_h, _ = base.chunk_hdr(axml, 0)
    o = root_h
    out = bytearray(axml[:root_h])
    skip = 0
    removed = False
    while o < len(axml):
        t, h, s = base.chunk_hdr(axml, o)
        ch = axml[o:o + s]
        if skip:
            if t == 0x0102:
                skip += 1
            elif t == 0x0103:
                skip -= 1
            o += s
            continue
        if t == 0x0102:
            ext = o + 16
            tag = strings[base.u32(axml, ext + 4)]
            ast, asz, ac, *_ = struct.unpack_from('<HHHHHH', axml, ext + 8)
            aoff = ext + ast
            attrs = {}
            for i in range(ac):
                x = aoff + i * asz
                name = strings[base.u32(axml, x + 4)]
                raw = base.u32(axml, x + 8)
                data_type = axml[x + 15]
                data = base.u32(axml, x + 16)
                value = strings[raw] if raw != 0xFFFFFFFF and raw < len(strings) else (strings[data] if data_type == 3 and data < len(strings) else None)
                attrs[name] = value
            if tag == 'item' and attrs.get('name') == target_name:
                skip = 1
                removed = True
                o += s
                continue
        out += ch
        o += s
    if not removed or skip:
        raise AssertionError('home module removal failed')
    struct.pack_into('<I', out, 4, len(out))
    return bytes(out)


def build_unsigned_recovery(manifest, arsc, registry, dark, amoled):
    base.WORK.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(base.BASE, 'r') as zin:
        dex = patch_runtime_dex(zin.read('classes.dex'))

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
            if name == 'res/q6.xml':
                data = remove_axml_item_named(data, 'nextapp.fx.plus.ui.UpdateHomeItem')
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


base.patch_manifest = patch_manifest_compat
base.build_unsigned = build_unsigned_recovery

if __name__ == '__main__':
    base.main()
    with zipfile.ZipFile(base.OUT_FINAL, 'r') as z:
        dex = z.read('classes.dex')
        assert dex[0x35AC1A:0x35AC22] == bytes.fromhex('1a 0b 4f a3 00 00 00 00')
        assert dex[0x388402:0x388404] == bytes.fromhex('12 10')
        assert dex[0x3A9BDC:0x3A9BE2] == bytes.fromhex('6e 10 4c 36 02 00')
        # Critical startup invariant: live implementation descriptors are NOT renamed.
        assert b'nextapp/fx/plus' in dex
        assert b'nextapp/fx/extd' not in dex
    print('STARTUP RECOVERY: live implementation descriptors preserved')
    print(f'TARGET SDK: {TARGET_SDK}; VERSION CODE: {VERSION_CODE}')
