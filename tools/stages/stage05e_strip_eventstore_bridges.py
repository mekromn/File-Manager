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

def drop_interface(path:Path,desc:str):
    t=path.read_text(); nt=t.replace(f'.implements {desc}\n','')
    if nt==t: raise RuntimeError(f'{path}: missing interface {desc}')
    path.write_text(nt)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); sm=a.decoded/'smali'
    remove_method(sm/'ce/b.smali','.method public apply(Ljava/lang/Object;)Ljava/lang/Object;'); drop_interface(sm/'ce/b.smali','Lf4/d;')
    remove_method(sm/'af/d.smali','.method public apply(Ljava/lang/Object;)Ljava/lang/Object;'); drop_interface(sm/'af/d.smali','Lf4/d;')
    remove_method(sm/'af/d.smali','.method public c()Ljava/lang/Object;'); drop_interface(sm/'af/d.smali','Lg4/b;')
    for rel in ['b2/d.smali','a2/n.smali','b2/i.smali','r5/g.smali','u5/g.smali']:
        p=sm/rel; remove_method(p,'.method public get()Ljava/lang/Object;'); drop_interface(p,'La4/b;')
    remove_method(sm/'b2/d.smali','.method public A(Ljava/lang/String;)V')
    remove_method(sm/'b2/d.smali','.method public n()Ly3/i;')
    remove_method(sm/'t8/c.smali','.method public constructor <init>(Ljava/util/concurrent/Executor;Lf4/f;Lb9/e;Lf4/f;)V')
    p=sm/'ae/c.smali'; lines=p.read_text().splitlines(); start=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_b'); end=next(i for i,l in enumerate(lines[start+1:],start+1) if l.strip()==':pswitch_c'); body='\n'.join(lines[start:end])
    for tok in ('Lt8/c;','Lf4/f;','La8/a;'):
        if tok not in body: raise RuntimeError(f'ae/c transport branch missing {tok}')
    p.write_text('\n'.join(lines[:start]+['    :pswitch_b','    return-void','']+lines[end:])+'\n')
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for tok in ('Lb2/d;->A(Ljava/lang/String;)V','Lb2/d;->n()Ly3/i;'):
        if tok in corpus: raise RuntimeError(f'transport bridge remains {tok}')
    print('stage05e transport/event-store provider bridges removed')
if __name__=='__main__': main()
