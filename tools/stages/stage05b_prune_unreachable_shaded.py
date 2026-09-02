#!/usr/bin/env python3
from pathlib import Path
import argparse,re,collections
PAT=re.compile(r'Lcom/google/android/gms/internal/play_billing/([A-Za-z0-9_$]+);')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'; pkg=sm/'com/google/android/gms/internal/play_billing'
    files={p.stem:p for p in pkg.glob('*.smali')}
    external=collections.defaultdict(set)
    for p in sm.rglob('*.smali'):
        if pkg in p.parents: continue
        for c in PAT.findall(p.read_text(errors='ignore')):
            if c in files: external[c].add(str(p.relative_to(sm)))
    graph={c:set() for c in files}
    for c,p in files.items():
        for d in PAT.findall(p.read_text(errors='ignore')):
            if d in files and d!=c: graph[c].add(d)
    roots=set(external); reach=set(roots); q=list(roots)
    while q:
        c=q.pop()
        for d in graph.get(c,()):
            if d not in reach: reach.add(d); q.append(d)
    dead=set(files)-reach
    if len(files)!=167 or len(roots)!=13 or len(dead)!=56:
        raise RuntimeError(f'unexpected shaded graph total={len(files)} roots={len(roots)} dead={len(dead)}')
    for c in sorted(dead): files[c].unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    dangling=[c for c in dead if f'Lcom/google/android/gms/internal/play_billing/{c};' in corpus]
    if dangling: raise RuntimeError(f'dangling deleted shaded refs: {sorted(dangling)}')
    remain=list(pkg.glob('*.smali'))
    if len(remain)!=111: raise RuntimeError(f'expected 111 shaded survivors, got {len(remain)}')
    print('stage05b graph prune complete: deleted 56 unreachable shaded classes; 111 remain')

if __name__=='__main__': main()
