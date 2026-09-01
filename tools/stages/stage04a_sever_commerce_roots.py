#!/usr/bin/env python3
from __future__ import annotations
import argparse,re
from pathlib import Path

NOOP_CTOR='''.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method'''
NOOP_CREATE='''.method public onCreate(Lnextapp/fx/ui/content/k;)V
    .locals 0
    return-void
.end method'''
NOOP_DESTROY='''.method public onDestroy(Lnextapp/fx/ui/content/k;)V
    .locals 0
    return-void
.end method'''

def replace_method(path:Path,prefix:str,body:str):
    lines=path.read_text().splitlines(); out=[];i=0;n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1; out.extend(body.splitlines()); out.append('')
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: expected one {prefix}, got {n}')
    path.write_text('\n'.join(out)+'\n')

def remove_method(path:Path,prefix:str):
    lines=path.read_text().splitlines(); out=[];i=0;n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: expected one {prefix}, got {n}')
    path.write_text('\n'.join(out)+'\n')

def cut_be_n_commerce_receiver(path:Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final onReceive('))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if lines[i].strip()==':pswitch_c')
    b=next(i for i in range(a+1,e) if lines[i].strip()==':pswitch_11')
    seg='\n'.join(lines[a:b])
    if 'LICENSE_REQUEST_PURCHASE_PLUS' not in seg or 'PlusExtension;->b(' not in seg:
        raise RuntimeError('be/n discriminator-3 commerce receiver arm did not match expected baseline')
    lines[a:b]=['    :pswitch_c','    # retired commerce receiver discriminator removed','    return-void','']
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final onReceive('))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    d=next(i for i in range(s,e) if lines[i].strip()==':sswitch_data_1')
    del lines[d:e]
    path.write_text('\n'.join(lines)+'\n')

def remove_manifest_intent_for_action(lines:list[str],action:str):
    hit=next((i for i,l in enumerate(lines) if f'android:name="{action}"' in l),None)
    if hit is None: raise RuntimeError(f'manifest query action missing: {action}')
    a=hit
    while a>=0 and '<intent>' not in lines[a]: a-=1
    b=hit
    while b<len(lines) and '</intent>' not in lines[b]: b+=1
    if a<0 or b>=len(lines): raise RuntimeError(f'manifest intent bounds failed: {action}')
    del lines[a:b+1]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    pe=sm/'nextapp/fx/plus/ui/PlusExtension.smali'
    t=pe.read_text()
    for pat in (
        r'^\.field private static plusWelcomeShown:Z = false\n\n?',
        r'^\.field private contentActivity:Lnextapp/fx/ui/content/k;\n\n?',
        r'^\.field private iab:Lnextapp/fx/plus/ui/a;\n\n?',
        r'^\.field private final licenseUpdateReceiver:Landroid/content/BroadcastReceiver;\n\n?',
    ):
        t,n=re.subn(pat,'',t,count=1,flags=re.M)
        if n!=1: raise RuntimeError(f'PlusExtension field not found: {pat}')
    pe.write_text(t)
    replace_method(pe,'.method public constructor <init>()V',NOOP_CTOR)
    for prefix in (
        '.method public static bridge synthetic a(Lnextapp/fx/plus/ui/PlusExtension;)',
        '.method public static bridge synthetic b(Lnextapp/fx/plus/ui/PlusExtension;',
        '.method public static bridge synthetic c(Lnextapp/fx/plus/ui/PlusExtension;',
        '.method public static bridge synthetic d(Lnextapp/fx/plus/ui/PlusExtension;',
        '.method private doUpgradePlus(Landroid/content/Context;)V',
        '.method private doUpgradeWelcome(Landroid/content/Context;)V',
        '.method private updateLicenseState(Landroid/content/Context;)V',
    ):
        remove_method(pe,prefix)
    replace_method(pe,'.method public onCreate(Lnextapp/fx/ui/content/k;)V',NOOP_CREATE)
    replace_method(pe,'.method public onDestroy(Lnextapp/fx/ui/content/k;)V',NOOP_DESTROY)
    cut_be_n_commerce_receiver(sm/'be/n.smali')
    mp=root/'AndroidManifest.xml'; lines=mp.read_text().splitlines()
    old=len(lines); lines=[l for l in lines if 'android:name="nextapp.fx.module/iab"' not in l]
    if len(lines)!=old-1: raise RuntimeError('IAB module manifest metadata count unexpected')
    old=len(lines); lines=[l for l in lines if 'android:name="com.android.vending.BILLING"' not in l]
    if len(lines)!=old-1: raise RuntimeError('billing permission count unexpected')
    for action in ('com.android.vending.billing.InAppBillingService.BIND','com.google.android.apps.play.billingtestcompanion.BillingOverrideService.BIND'):
        remove_manifest_intent_for_action(lines,action)
    mp.write_text('\n'.join(lines)+'\n')
    q=root/'res/xml/module_iab.xml'
    if not q.exists(): raise RuntimeError('module_iab.xml missing')
    q.unlink()
    pub=root/'res/values/public.xml'; pt=pub.read_text()
    pt,n=re.subn(r'^\s*<public type="xml" name="module_iab" id="0x[0-9a-fA-F]+" />\n?','',pt,count=1,flags=re.M)
    if n!=1: raise RuntimeError('module_iab public declaration missing')
    pub.write_text(pt)
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for tok in ('PlusExtension;->a(Lnextapp/fx/plus/ui/PlusExtension;','PlusExtension;->b(Lnextapp/fx/plus/ui/PlusExtension;','PlusExtension;->c(Lnextapp/fx/plus/ui/PlusExtension;','PlusExtension;->d(Lnextapp/fx/plus/ui/PlusExtension;'):
        if tok in corpus: raise RuntimeError(f'commerce bridge token survives Stage04a: {tok}')
    pe_text=pe.read_text(); be_text=(sm/'be/n.smali').read_text()
    for tok in ('LICENSE_REQUEST_PURCHASE_PLUS','LICENSE_PURCHASE_COMPLETE','LICENSE_PURCHASE_ERROR','IAB internal error','Purchase not available'):
        if tok in pe_text or tok in be_text: raise RuntimeError(f'commerce root token survives active extension/receiver: {tok}')
    manifest=mp.read_text()
    for tok in ('nextapp.fx.module/iab','com.android.vending.BILLING','InAppBillingService.BIND','BillingOverrideService.BIND'):
        if tok in manifest: raise RuntimeError(f'manifest commerce root survives: {tok}')
    print('stage04a commerce roots severed')

if __name__=='__main__': main()
