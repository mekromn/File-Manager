#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    public=(root/'res/values/public.xml').read_text(errors='ignore')
    defined={int(x,16) for x in re.findall(r'id="(0x7f[0-9a-fA-F]{6})"',public)}
    refs={}
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            txt=p.read_text(errors='ignore')
            for m in re.finditer(r'(?<![0-9A-Fa-f])0x7f[0-9A-Fa-f]{6}(?![0-9A-Fa-f])',txt):
                rid=int(m.group(0),16)
                refs.setdefault(rid,set()).add(str(p.relative_to(root)))
    missing={rid:sorted(paths) for rid,paths in refs.items() if rid not in defined}
    print(f'defined_public_ids={len(defined)} referenced_app_ids={len(refs)} missing_referenced_ids={len(missing)}')
    for rid,paths in sorted(missing.items()):
        print(f'MISSING 0x{rid:08x} :: '+', '.join(paths[:20]))
    # Crash-path subset for prioritization.
    needles=('fxsystem','Recent','viewer/image','ext/ui/image','ext/ui/video','tabactivity','ui/content')
    crash=[]
    for rid,paths in missing.items():
        selected=[x for x in paths if any(n in x for n in needles)]
        if selected: crash.append((rid,selected))
    print(f'crash_path_missing_ids={len(crash)}')
    for rid,paths in sorted(crash): print(f'CRASH_PATH_MISSING 0x{rid:08x} :: '+', '.join(paths[:20]))

if __name__=='__main__': main()
