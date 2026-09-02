#!/usr/bin/env python3
from pathlib import Path
import argparse

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    p=root/'smali/ab/k.smali'; t=p.read_text()
    if t.count('const-string v6, "fxconfig"')!=1: raise RuntimeError('fxconfig MIME extension mapping shape changed')
    p.write_text(t.replace('const-string v6, "fxconfig"','const-string v6, "dwconfig"',1))

    p=root/'smali/rf/a.smali'; t=p.read_text()
    if t.count('const-string v3, "FX_"')!=1 or t.count('const-string v0, ".fxconfig"')!=1:
        raise RuntimeError('config filename generation shape changed')
    t=t.replace('const-string v3, "FX_"','const-string v3, "DW_"',1)
    t=t.replace('const-string v0, ".fxconfig"','const-string v0, ".dwconfig"',1)
    p.write_text(t)

    for p in (root/'res').glob('values*/strings.xml'):
        t=p.read_text(); p.write_text(t.replace('.fxconfig','.dwconfig').replace('fxconfig','dwconfig'))

    hits=[]
    for base in [root/'smali',root/'res',root/'assets']:
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: t=p.read_text(errors='ignore')
            except Exception: continue
            if 'fxconfig' in t.lower(): hits.append(str(p.relative_to(root)))
    if hits: raise RuntimeError('old fxconfig naming remains: '+str(hits[:20]))
    if '"FX_"' in (root/'smali/rf/a.smali').read_text(): raise RuntimeError('old FX_ export prefix remains')
    print('stage09f migrated config extension to .dwconfig and export prefix to DW_')

if __name__=='__main__': main()
