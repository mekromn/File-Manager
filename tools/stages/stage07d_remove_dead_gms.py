#!/usr/bin/env python3
from pathlib import Path
import argparse

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); sm=a.decoded/'smali'
    dead=[
        't5/g.smali',
        'com/google/android/gms/common/api/internal/LifecycleCallback.smali',
        'com/google/android/gms/common/util/DynamiteApi.smali',
        'com/google/android/gms/dynamite/DynamiteModule$DynamiteLoaderClassLoader.smali',
    ]
    descs=[]
    for rel in dead:
        p=sm/rel
        if not p.exists(): raise RuntimeError(f'missing expected dead class {rel}')
        txt=p.read_text(errors='ignore')
        cls=next((x.split()[-1] for x in txt.splitlines()[:8] if x.startswith('.class')),None)
        if cls: descs.append(cls)
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali') if str(p.relative_to(sm)) not in dead)
    bad=[d for d in descs if d in corpus]
    if bad: raise RuntimeError(f'dead GMS class gained external refs: {bad}')
    for rel in dead: (sm/rel).unlink()
    keep=[
      'com/google/android/gms/common/api/GoogleApiActivity.smali',
      'com/google/android/gms/common/api/Scope.smali',
      'com/google/android/gms/common/api/Status.smali',
      'com/google/android/gms/common/internal/a.smali',
      'com/google/android/gms/common/GooglePlayServicesMissingManifestValueException.smali',
    ]
    for rel in keep:
        if not (sm/rel).exists(): raise RuntimeError(f'required Drive GMS class missing: {rel}')
    print('stage07d removed four unreachable GMS/lifecycle remnants; Drive-required GMS retained')
if __name__=='__main__': main()
