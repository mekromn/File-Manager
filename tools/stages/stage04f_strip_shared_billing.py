#!/usr/bin/env python3
from pathlib import Path
import argparse, re

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
    y=sm/'k2/y.smali'; t=y.read_text()
    t,n=re.subn(r'^\.implements Lk2/w;\n','',t,count=1,flags=re.M)
    if n!=1: raise RuntimeError('k2/y billing interface missing')
    y.write_text(t)
    remove_method(y,'.method public constructor <init>(Landroid/content/Context;Lcom/google/android/gms/internal/play_billing/t4;)V')
    for prefix in (
        '.method public F(Lcom/google/android/gms/internal/play_billing/j4;)V',
        '.method public G(Lcom/google/android/gms/internal/play_billing/l4;)V',
        '.method public H(Lcom/google/android/gms/internal/play_billing/p4;)V',
        '.method public I(Lcom/google/android/gms/internal/play_billing/d5;)V',
        '.method public J(Lcom/google/android/gms/internal/play_billing/e5;)V',
    ):
        remove_method(y,prefix)
    w=sm/'k2/w.smali'
    if not w.exists(): raise RuntimeError('k2/w missing')
    w.unlink()
    remove_method(sm/'k2/e.smali','.method public a()Lk2/f;')
    remove_method(sm/'fc/d.smali','.method public static bridge synthetic w(Ljava/util/function/Consumer;Lk2/f;)V')
    k1=sm/'com/google/android/gms/internal/play_billing/k1.smali'
    remove_method(k1,'.method public static c(Landroid/content/Intent;Ljava/lang/String;)Lk2/f;')
    remove_method(k1,'.method public static h(Lk2/f;I)Landroid/os/Bundle;')
    f=sm/'k2/f.smali'
    if not f.exists(): raise RuntimeError('k2/f missing')
    f.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for tok in ('Lk2/w;','Lk2/f;'):
        if tok in corpus: raise RuntimeError(f'deleted shared billing type survives: {tok}')
    k2_corpus='\n'.join(p.read_text(errors='ignore') for p in (sm/'k2').glob('*.smali'))
    for tok in ('com.android.vending.billing.PURCHASES_UPDATED','LOCAL_BROADCAST_PURCHASES_UPDATED','ALTERNATIVE_BILLING'):
        if tok in k2_corpus: raise RuntimeError(f'billing broadcast token survives k2: {tok}')
    k2files=sorted(p.name for p in (sm/'k2').glob('*.smali'))
    if k2files != ['e.smali','p.smali','y.smali']:
        raise RuntimeError(f'unexpected remaining k2 files: {k2files}')
    print('stage04f shared R8 billing methods removed; k2 reduced to generic e/p/y')
if __name__=='__main__': main()
