#!/usr/bin/env python3
from pathlib import Path
import argparse,re

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
    if n!=1: raise RuntimeError(f'{path}: {prefix} count {n}')
    path.write_text('\n'.join(out)+'\n')

def cut_fragment_timeout(path:Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final run()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if lines[i].strip()==':pswitch_c')
    b=next(i for i in range(a+1,e) if lines[i].strip()==':pswitch_d')
    seg='\n'.join(lines[a:b])
    if 'BillingClient' not in seg or 'Async task is taking too long' not in seg:
        raise RuntimeError('fragment pswitch_c no longer matches billing timeout arm')
    lines[a:b]=['    :pswitch_c','    # removed unreachable BillingClient timeout arm','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    qref='Lmb/d;->q(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Z'
    if qref in corpus: raise RuntimeError('purchase verification helper gained a caller')
    aref='Landroidx/emoji2/text/g;->a()Z'
    if aref in corpus: raise RuntimeError('billing override metadata helper gained a caller')
    remove_method(sm/'mb/d.smali','.method public static q(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Z')
    remove_method(sm/'androidx/emoji2/text/g.smali','.method public a()Z')
    cut_fragment_timeout(sm/'androidx/fragment/app/d.smali')
    share=sm/'nextapp/fx/plus/share/service/SharingService$1.smali'
    t=share.read_text(); t,n=t.replace('const-string p1, "nextapp.fx"','const-string p1, "DWFileManager"',1),t.count('const-string p1, "nextapp.fx"')
    if n!=1: raise RuntimeError(f'sharing log tag count {n}')
    old='Cannot start sharing service due to unavailable FX Plus license key.'
    if t.count(old)!=1: raise RuntimeError('sharing legacy message count unexpected')
    t=t.replace(old,'Cannot start sharing service: companion app unavailable.')
    share.write_text(t)
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    banned=['Purchase verification failed: missing data.','com.google.android.play.billingclient.enableBillingOverridesTesting','Unable to retrieve metadata value for enableBillingOverridesTesting.','Async task is taking too long, cancel it!','Cannot start sharing service due to unavailable FX Plus license key.']
    hits=[x for x in banned if x in corpus]
    if hits: raise RuntimeError(f'residual app-owned commerce tokens: {hits}')
    print('stage04h residual app-owned commerce methods removed')

if __name__=='__main__': main()
