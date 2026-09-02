#!/usr/bin/env python3
from pathlib import Path
import argparse

def remove_method(path:Path,prefix:str):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: {prefix}: count {n}')
    path.write_text('\n'.join(out)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    ref='Lhf/b1;->d(Lcom/google/android/gms/internal/play_billing/a5;)V'
    if ref in corpus: raise RuntimeError('BillingLogger send root gained a caller')
    remove_method(sm/'hf/b1.smali','.method public d(Lcom/google/android/gms/internal/play_billing/a5;)V')
    # DataTransport event encoder is called only from the deleted logger method.
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    zref='Lb2/d;->z(Lv3/a;)V'
    if zref in corpus: raise RuntimeError('transport event encoder still has caller after logger deletion')
    remove_method(sm/'b2/d.smali','.method public z(Lv3/a;)V')
    env=sm/'v3/a.smali'
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    if 'Lv3/a;' in corpus.replace(env.read_text(errors='ignore'),''):
        raise RuntimeError('billing transport envelope still has external caller')
    env.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for tok in ('Lhf/b1;->d(Lcom/google/android/gms/internal/play_billing/a5;)V','Lb2/d;->z(Lv3/a;)V','Lv3/a;'):
        if tok in corpus: raise RuntimeError(f'transport logging root survives: {tok}')
    print('stage05a BillingLogger -> DataTransport root removed')
if __name__=='__main__': main()
