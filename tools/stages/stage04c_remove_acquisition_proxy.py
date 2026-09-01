#!/usr/bin/env python3
from pathlib import Path
import argparse, re, shutil

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
    if n!=expected: raise RuntimeError(f'{path}: {prefix} removed {n}, expected {expected}')
    path.write_text('\n'.join(out)+'\n')

def cut_default_before_pswitch0(path: Path, method_prefix: str, ret_lines):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith(method_prefix))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    sw=next(i for i in range(s,e) if 'packed-switch' in lines[i])
    p0=next(i for i in range(sw+1,e) if lines[i].strip()==':pswitch_0')
    lines[sw+1:p0]=['', *[f'    {x}' for x in ret_lines], '']
    path.write_text('\n'.join(lines)+'\n')

def cut_hg_acquisition(path: Path):
    lines=path.read_text().splitlines()
    a=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_6')
    b=next(i for i in range(a+1,len(lines)) if lines[i].strip()==':pswitch_7')
    lines[a:b]=['    :pswitch_6','    check-cast v7, Lbe/w;','    invoke-virtual {v7}, Lnextapp/fx/ui/widget/n;->dismiss()V','    # retired acquisition dialog removed','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def remove_manifest_lines(path: Path):
    lines=path.read_text().splitlines(); removed=0
    needles=['android:name="com.google.android.play.billingclient.version"','android:name="com.android.billingclient.api.ProxyBillingActivity"','android:name="com.android.billingclient.api.ProxyBillingActivityV2"']
    out=[]
    for l in lines:
        if any(n in l for n in needles): removed+=1; continue
        out.append(l)
    if removed!=3: raise RuntimeError(f'expected 3 billing manifest lines, removed {removed}')
    path.write_text('\n'.join(out)+'\n')

def remove_public(path: Path, typ: str, name: str):
    t=path.read_text(); pat=rf'^\s*<public type="{re.escape(typ)}" name="{re.escape(name)}" id="0x[0-9a-fA-F]+" />\n?'
    t,n=re.subn(pat,'',t,count=1,flags=re.M)
    if n!=1: raise RuntimeError(f'public declaration missing {typ}/{name}')
    path.write_text(t)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    cut_hg_acquisition(sm/'hg/a.smali')
    remove_method(sm/'hf/g.smali','.method public constructor <init>(Lyd/c;Landroid/content/Context;Lhf/n;)V')
    cut_default_before_pswitch0(sm/'hf/g.smali','.method public final g()V',['# retired acquisition dialog dismiss arm removed','return-void'])
    for rel in ('yd/b.smali','yd/c.smali'):
        p=sm/rel
        if not p.exists(): raise RuntimeError(f'missing acquisition class {rel}')
        p.unlink()
    cut_default_before_pswitch0(sm/'r5/g.smali','.method public g(Ljava/lang/Object;)V',['# removed ProxyBillingActivityV2 callback default arm','return-void'])
    cut_default_before_pswitch0(sm/'b9/b.smali','.method public g(Ljava/lang/Object;)V',['# removed ProxyBillingActivityV2 callback default arm','return-void'])
    remove_method(sm/'com/google/android/gms/internal/play_billing/k1.smali','.method public static i(Ljava/lang/String;Ljava/lang/String;)Lcom/android/billingclient/api/Purchase;')
    api=sm/'com/android/billingclient/api'
    for name in ('ProxyBillingActivity.smali','ProxyBillingActivityV2.smali','Purchase.smali'):
        p=api/name
        if not p.exists(): raise RuntimeError(f'missing public billing API class {name}')
        p.unlink()
    if api.exists() and not any(api.iterdir()): api.rmdir()
    remove_manifest_lines(root/'AndroidManifest.xml')
    for rel in ('res/raw/com_android_billingclient_heterodyne_info','res/raw/com_android_billingclient_registration_info.binarypb','res/xml/com_android_billingclient_phenotype.xml','unknown/billing.properties'):
        p=root/rel
        if p.exists(): p.unlink()
    pub=root/'res/values/public.xml'
    remove_public(pub,'raw','com_android_billingclient_heterodyne_info')
    remove_public(pub,'raw','com_android_billingclient_registration_info')
    remove_public(pub,'xml','com_android_billingclient_phenotype')
    y=root/'apktool.yml'; txt=y.read_text()
    txt=txt.replace('- res/raw/com_android_billingclient_heterodyne_info\n','').replace('- res/raw/com_android_billingclient_registration_info.binarypb\n','')
    y.write_text(txt)
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    banned=['Lyd/b;','Lyd/c;','Lcom/android/billingclient/api/ProxyBillingActivity;','Lcom/android/billingclient/api/ProxyBillingActivityV2;','Lcom/android/billingclient/api/Purchase;','LICENSE_REQUEST_PURCHASE_PLUS']
    hits=[x for x in banned if x in corpus]
    if hits: raise RuntimeError(f'acquisition/proxy refs survive: {hits}')
    manifest=(root/'AndroidManifest.xml').read_text()
    for tok in ('com.google.android.play.billingclient.version','com.android.billingclient.api.ProxyBillingActivity'):
        if tok in manifest: raise RuntimeError(f'billing manifest token survives: {tok}')
    print('stage04c acquisition/proxy billing surfaces removed')

if __name__=='__main__': main()
