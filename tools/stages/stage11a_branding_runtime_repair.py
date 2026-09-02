#!/usr/bin/env python3
from pathlib import Path
import argparse

VISIBLE_REPLACEMENTS={
    'FX Connect Connection':'DW Connect Connection',
    'FX Connect permissions error.':'DW Connect permissions error.',
    'FX Connect socket timeout, retrying (':'DW Connect socket timeout, retrying (',
    'FX Connect: ':'DW Connect: ',
    'FX Connect':'DW Connect',
    'FX File Explorer':'DW File Manager',
    'FX Image Viewer':'DW Image Viewer',
    'FX Media Player':'DW Media Player',
    'FX Root Installer':'DW Root Installer',
}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    # The dynamic icon slot names are internal compatibility keys, but every reference
    # to the old FX-derived artwork must render the DW launcher artwork instead.
    iconset=root/'res/xml/iconset_dynamic_ext.xml'
    t=iconset.read_text()
    tokens=(
        'value="@drawable/i144_dw_root"',
        'value="@drawable/i288_dw_root"',
        'value="@drawable/i144_dw"',
        'value="@drawable/i288_dw"',
    )
    changed_icons=0
    for old in tokens:
        c=t.count(old)
        if c<1: raise RuntimeError(f'expected at least one exact XML token {old}, got {c}')
        t=t.replace(old,'value="@mipmap/ic_launcher_app"')
        changed_icons+=c
    if any(old in t for old in tokens):
        raise RuntimeError('legacy DW/FX-derived icon artwork link remains after replacement')
    iconset.write_text(t)

    # Replace user-facing FX wording anywhere in executable/resource text, regardless of
    # which R8/neutral namespace owns the literal.
    changed_text=0
    for base in (root/'smali',root/'res',root/'assets'):
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text()
            except Exception: continue
            oldtxt=txt
            for old,new in VISIBLE_REPLACEMENTS.items():
                txt=txt.replace(old,new)
            if txt!=oldtxt:
                changed_text+=sum(oldtxt.count(old) for old in VISIBLE_REPLACEMENTS)
                p.write_text(txt)

    visible=[]
    for base in (root/'smali',root/'res',root/'assets'):
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            for needle in VISIBLE_REPLACEMENTS:
                if needle in txt: visible.append((str(p.relative_to(root)),needle))
    if visible: raise RuntimeError('visible legacy FX branding remains: '+str(visible[:30]))

    print(f'stage11a branding repair complete: {changed_icons} legacy home/root artwork links replaced; {changed_text} visible FX text occurrence(s) migrated to DW')

if __name__=='__main__': main()
