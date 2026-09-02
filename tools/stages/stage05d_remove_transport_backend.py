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
    if n!=1: raise RuntimeError(f'{path}: {prefix} count={n}')
    path.write_text('\n'.join(out).rstrip()+'\n')

def drop_interface(path:Path,desc:str):
    txt=path.read_text(); before=txt
    txt=txt.replace(f'.implements {desc}\n','')
    if txt==before: raise RuntimeError(f'{path}: interface {desc} missing')
    path.write_text(txt)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    remove_method(sm/'t4/j.smali','.method public get()Ljava/lang/Object;')
    remove_method(sm/'t4/j.smali','.method public s(Ljava/lang/String;)Lcom/google/android/datatransport/cct/CctBackendFactory;')
    drop_interface(sm/'t4/j.smali','La4/b;')
    remove_method(sm/'l/f3.smali','.method public get()Ljava/lang/Object;'); drop_interface(sm/'l/f3.smali','La4/b;')
    remove_method(sm/'d4/b.smali','.method public get()Ljava/lang/Object;'); drop_interface(sm/'d4/b.smali','La4/b;')
    remove_method(sm/'ca/f.smali','.method public constructor <init>(Landroid/content/Context;Lz3/d;Lf4/f;Lb9/e;Ljava/util/concurrent/Executor;Lf4/f;Le9/b;Le9/b;Lf4/f;)V')
    remove_method(sm/'af/f.smali','.method public synthetic constructor <init>(Ld4/a;Ly3/i;Lw7/y0;Ly3/h;)V')
    p=sm/'af/f.smali'; lines=p.read_text().splitlines(); start=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_17'); end=next(i for i,l in enumerate(lines[start+1:],start+1) if l.strip()==':pswitch_18'); body='\n'.join(lines[start:end])
    for tok in ('Ld4/a;','Lz3/d;','Transport backend'):
        if tok not in body: raise RuntimeError(f'af/f transport arm missing {tok}')
    p.write_text('\n'.join(lines[:start]+['    :pswitch_17','    return-void','']+lines[end:])+'\n')
    for rel in ['d4/a.smali','z3/d.smali','com/google/android/datatransport/cct/CctBackendFactory.smali','com/google/android/datatransport/runtime/backends/TransportBackendDiscovery.smali']:
        q=sm/rel
        if not q.exists(): raise RuntimeError(f'missing {rel}')
        q.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    forbidden=['Ld4/a;','Lz3/d;','CctBackendFactory','TransportBackendDiscovery']
    bad=[x for x in forbidden if x in corpus]
    if bad: raise RuntimeError(f'stage05d backend refs remain: {bad}')
    print('stage05d DataTransport backend registry/discovery roots removed')
if __name__=='__main__': main()
