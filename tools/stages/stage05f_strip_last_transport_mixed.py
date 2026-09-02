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
    if n!=1: raise RuntimeError(f'{path}: {prefix}: count={n}')
    path.write_text('\n'.join(out).rstrip()+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); sm=a.decoded/'smali'
    remove_method(sm/'w3/b.smali','.method public a(Lb2/d;)Lb5/k;')
    remove_method(sm/'ei/a.smali','.method public c()Ly3/h;')
    remove_method(sm/'b9/e.smali','.method public k(Lb4/a;Ljava/io/ByteArrayOutputStream;)V')
    p=sm/'l6/e.smali'; lines=p.read_text().splitlines(); start=next(i for i,l in enumerate(lines) if l.strip()==':cond_f'); end=next(i for i,l in enumerate(lines[start+1:],start+1) if l.strip()==':cond_10'); body='\n'.join(lines[start:end])
    if 'Lb4/c;' not in body: raise RuntimeError('l6/e b4/c branch not found')
    p.write_text('\n'.join(lines[:start]+['    :cond_f']+lines[end:])+'\n')
    mixed='\n'.join((sm/r).read_text(errors='ignore') for r in ('w3/b.smali','ei/a.smali','b9/e.smali','l6/e.smali'))
    for tok in ('CctTransportBackend','datatransport/3.1.8 android/','com.google.android.datatransport.events','Lb4/c;'):
        if tok in mixed: raise RuntimeError(f'mixed transport marker remains: {tok}')
    print('stage05f last mixed DataTransport bridges removed')
if __name__=='__main__': main()
