#!/usr/bin/env python3
from pathlib import Path
import argparse


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    # The dynamic icon slot names are internal compatibility keys, but their images must
    # never render legacy FX artwork. Reuse the verified DW launcher artwork directly.
    iconset=root/'res/xml/iconset_dynamic_ext.xml'
    t=iconset.read_text()
    replacements={
        '@drawable/i144_dw':'@mipmap/ic_launcher_app',
        '@drawable/i288_dw':'@mipmap/ic_launcher_app',
        '@drawable/i144_dw_root':'@mipmap/ic_launcher_app',
        '@drawable/i288_dw_root':'@mipmap/ic_launcher_app',
    }
    changed=0
    for old,new in replacements.items():
        c=t.count(old)
        if c!=1: raise RuntimeError(f'expected exactly one {old} in dynamic iconset, got {c}')
        t=t.replace(old,new,1); changed+=1
    iconset.write_text(t)

    # One executable legacy display/log label escaped the earlier XML-only brand pass.
    p=root/'smali/dw/filemanager/ext/share/connect/ConnectConnection.smali'
    st=p.read_text()
    if st.count('const-string v0, "FX Connect"')!=1:
        raise RuntimeError('FX Connect literal shape changed')
    p.write_text(st.replace('const-string v0, "FX Connect"','const-string v0, "DW Connect"',1))

    # User-visible legacy FX text must be gone. Internal icon-theme ids such as
    # fx_dynamic remain compatibility identifiers only and are not rendered text.
    visible=[]
    for base in (root/'res',root/'smali/dw'):
        for q in base.rglob('*'):
            if not q.is_file() or q.suffix not in {'.xml','.smali'}: continue
            txt=q.read_text(errors='ignore')
            for needle in ('FX Connect','FX File Explorer','FX Image Viewer','FX Media Player','FX Root Installer'):
                if needle in txt: visible.append((str(q.relative_to(root)),needle))
    if visible: raise RuntimeError('visible legacy FX branding remains: '+str(visible[:20]))

    print(f'stage11a branding repair complete: {changed} legacy home/root artwork links replaced; FX Connect -> DW Connect')

if __name__=='__main__': main()
