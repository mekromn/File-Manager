#!/usr/bin/env python3
from pathlib import Path
import argparse,re,collections

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    paths=[]
    for pkg in ['y3','z3','f4','v3','b4','g4','i4']:
        d=sm/pkg
        if d.exists(): paths.extend(d.glob('*.smali'))
    paths += [sm/f'e4/{n}.smali' for n in ['b','c','d','f','h','i','j'] if (sm/f'e4/{n}.smali').exists()]
    paths += [p for p in (sm/'w3/a.smali', sm/'w3/c.smali') if p.exists()]
    classes={}
    for p in paths:
        m=re.search(r'^\.class[^\n]* (L[^;]+;)',p.read_text(errors='ignore'),re.M)
        if not m: raise RuntimeError(f'no class descriptor {p}')
        classes[m.group(1)]=p
    if len(classes)!=45: raise RuntimeError(f'expected 45 transport-only classes, got {len(classes)}')
    external=collections.defaultdict(set)
    for p in sm.rglob('*.smali'):
        if p in classes.values(): continue
        txt=p.read_text(errors='ignore')
        for desc in classes:
            if desc in txt: external[desc].add(str(p.relative_to(sm)))
    if external: raise RuntimeError('transport set gained external roots: '+repr({k:sorted(v) for k,v in external.items()}))
    for p in classes.values(): p.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    dangling=[d for d in classes if d in corpus]
    if dangling: raise RuntimeError(f'dangling transport descriptors: {dangling[:10]}')
    markers=['SQLiteEventStore','transport_contexts','log_event_dropped','CctTransportBackend','datatransport/3.1.8 android/','com.google.android.datatransport.events']
    hits=[m for m in markers if m in corpus]
    if hits: raise RuntimeError(f'DataTransport markers remain after graph prune: {hits}')
    print('stage05g graph prune complete: 45 DataTransport-only classes deleted; zero external roots')
if __name__=='__main__': main()
