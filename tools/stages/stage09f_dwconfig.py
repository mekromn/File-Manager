#!/usr/bin/env python3
from pathlib import Path
import argparse

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    # Stage 09d owns the actual .fxconfig -> .dwconfig migration. 09f only
    # finishes the exported filename prefix so the durable replay chain has a
    # single source of truth for the extension migration.
    p=root/'smali/ab/k.smali'; t=p.read_text()
    if t.count('const-string v6, "dwconfig"')!=1:
        raise RuntimeError('Stage 09d dwconfig MIME extension mapping missing or duplicated')
    if 'fxconfig' in t.lower():
        raise RuntimeError('legacy fxconfig token returned in MIME mapping')

    p=root/'smali/rf/a.smali'; t=p.read_text()
    if t.count('const-string v3, "FX_"')!=1 or t.count('const-string v0, ".dwconfig"')!=1:
        raise RuntimeError('post-Stage09d config filename generation shape changed')
    p.write_text(t.replace('const-string v3, "FX_"','const-string v3, "DW_"',1))

    hits=[]
    for base in [root/'smali',root/'res',root/'assets']:
        if not base.exists(): continue
        for f in base.rglob('*'):
            if not f.is_file(): continue
            try: txt=f.read_text(errors='ignore')
            except Exception: continue
            if 'fxconfig' in txt.lower(): hits.append(str(f.relative_to(root)))
    if hits: raise RuntimeError('old fxconfig naming remains: '+str(hits[:20]))
    if '"FX_"' in (root/'smali/rf/a.smali').read_text():
        raise RuntimeError('old FX_ export prefix remains')
    if '"DW_"' not in (root/'smali/rf/a.smali').read_text():
        raise RuntimeError('DW_ export prefix missing')
    print('stage09f finalized config export prefix DW_; Stage09d remains sole dwconfig migration')

if __name__=='__main__': main()
