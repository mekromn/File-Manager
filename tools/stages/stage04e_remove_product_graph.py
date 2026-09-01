#!/usr/bin/env python3
from pathlib import Path
import argparse

def remove_method(path: Path, prefix: str, expected=1):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=expected: raise RuntimeError(f'{path}: {prefix}: removed {n}, expected {expected}')
    path.write_text('\n'.join(out)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    fc=sm/'fc/d.smali'
    for prefix in (
        '.method public static bridge synthetic A(Ljava/util/stream/Stream;Lcom/google/android/gms/internal/play_billing/a;)Z',
        '.method public static bridge synthetic n(Ljava/util/stream/Stream;Lcom/google/android/gms/internal/play_billing/a;)Ljava/util/stream/Stream;',
        '.method public static bridge synthetic o(Ljava/util/stream/Stream;Lcom/google/android/gms/internal/play_billing/t;)Ljava/util/stream/Stream;',
        '.method public static bridge synthetic v(Ljava/util/ArrayList;Lk2/u;)V',
    ):
        remove_method(fc,prefix)
    product=['b','c','d','g','h','i','t','u','v','x']
    for c in product:
        p=sm/f'k2/{c}.smali'
        if not p.exists(): raise RuntimeError(f'missing expected product class k2/{c}')
        p.unlink()
    for c in ('a','t'):
        p=sm/f'com/google/android/gms/internal/play_billing/{c}.smali'
        if not p.exists(): raise RuntimeError(f'missing product predicate/mapper {c}')
        p.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    banned=[f'Lk2/{c};' for c in product]+['Lcom/google/android/gms/internal/play_billing/a;','Lcom/google/android/gms/internal/play_billing/t;']
    hits=[x for x in banned if x in corpus]
    if hits: raise RuntimeError(f'product graph refs survive: {hits}')
    k2='\n'.join(p.read_text(errors='ignore') for p in (sm/'k2').glob('*.smali'))
    for tok in ('productId','ProductDetails','skuDetailsToken','SKU type','list of SKUs'):
        if tok.lower() in k2.lower(): raise RuntimeError(f'product token survives k2: {tok}')
    print('stage04e product/SKU graph removed')
if __name__=='__main__': main()
