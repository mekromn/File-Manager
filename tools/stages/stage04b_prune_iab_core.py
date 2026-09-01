#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil

def remove_method(path: Path, prefix: str, expected=1):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i < len(lines):
        if lines[i].startswith(prefix):
            n += 1
            while i < len(lines) and lines[i] != '.end method': i += 1
            if i < len(lines): i += 1
            while i < len(lines) and lines[i]=='': i += 1
            continue
        out.append(lines[i]); i += 1
    if n != expected: raise RuntimeError(f'{path}: {prefix}: removed {n}, expected {expected}')
    path.write_text('\n'.join(out)+'\n')

def replace_label_block(path: Path, label: str, next_label: str, return_lines):
    lines=path.read_text().splitlines()
    a=next(i for i,l in enumerate(lines) if l.strip()==label)
    b=next(i for i in range(a+1,len(lines)) if lines[i].strip()==next_label)
    lines[a:b]=[f'    {label}', *[f'    {x}' for x in return_lines], '']
    path.write_text('\n'.join(lines)+'\n')

def cut_fd_default(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final call()Ljava/lang/Object;'))
    sw=next(i for i in range(s,len(lines)) if 'packed-switch v0, :pswitch_data_0' in lines[i])
    p0=next(i for i in range(sw+1,len(lines)) if lines[i].strip()==':pswitch_0')
    lines[sw+1:p0]=['', '    # removed BillingClient default callable branch', '    const/4 v0, 0x0', '    return-object v0', '']
    path.write_text('\n'.join(lines)+'\n')

def cut_nc_billing(path: Path):
    remove_method(path,'.method public synthetic constructor <init>(Lk2/s;Ljava/lang/Object;Ljava/lang/Object;I)V')
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final run()V'))
    sw=next(i for i in range(s,len(lines)) if 'packed-switch v0, :pswitch_data_0' in lines[i])
    p0=next(i for i in range(sw+1,len(lines)) if lines[i].strip()==':pswitch_0')
    lines[sw+1:p0]=['', '    # removed billing callback default arm', '    return-void', '']
    p0=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_0')
    p1=next(i for i in range(p0+1,len(lines)) if lines[i].strip()==':pswitch_1')
    lines[p0:p1]=['    :pswitch_0','    # removed billing callback arm','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def cut_fragment_billing(path: Path):
    for label,next_label in [(':pswitch_9',':pswitch_a'),(':pswitch_a',':pswitch_b'),(':pswitch_b',':pswitch_c'),(':pswitch_d',':pswitch_e')]:
        replace_label_block(path,label,next_label,['# removed BillingClient/IAB callback arm','return-void'])

def cut_activity_billing(path: Path):
    replace_label_block(path,':pswitch_d',':pswitch_e',['# removed BillingClient connection-timeout arm','return-void'])

def cut_b6_callback(path: Path):
    remove_method(path,'.method public synthetic constructor <init>()V')
    replace_label_block(path,':pswitch_0',':pswitch_1',['# removed Billing Override binder callback arm','const/4 v2, 0x0','return v2'])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    cut_fd_default(sm/'fd/b.smali')
    cut_activity_billing(sm/'androidx/activity/i.smali')
    cut_fragment_billing(sm/'androidx/fragment/app/d.smali')
    cut_nc_billing(sm/'nc/i.smali')
    remove_method(sm/'ae/d.smali','.method public constructor <init>(Landroid/content/Context;Lnextapp/fx/iab/a;Lk2/y;)V')
    remove_method(sm/'ae/d.smali','.method public h(Z)V')
    remove_method(sm/'a7/b.smali','.method public static bridge synthetic s(Landroid/content/Context;Lk2/z;Landroid/content/IntentFilter;I)V')
    remove_method(sm/'ah/f.smali','.method public m(Ljava/lang/Throwable;)V')
    remove_method(sm/'k2/p.smali','.method public v(Lcom/google/android/gms/internal/play_billing/k5;)V')
    cut_b6_callback(sm/'b6/a.smali')
    idir=sm/'nextapp/fx/iab'
    if not idir.exists(): raise RuntimeError('IAB directory missing')
    shutil.rmtree(idir)
    for rel in ['nextapp/fx/plus/ui/a.smali','nextapp/fx/plus/ui/b.smali']:
        p=sm/rel
        if not p.exists(): raise RuntimeError(f'missing {rel}')
        p.unlink()
    dedicated=['a','j','k','l','m','n','o','q','r','s','z']
    for c in dedicated:
        p=sm/f'k2/{c}.smali'
        if not p.exists(): raise RuntimeError(f'missing dedicated k2/{c}')
        p.unlink()
    p=sm/'com/google/android/gms/internal/play_billing/p1.smali'
    if p.exists(): p.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    banned=['Lnextapp/fx/iab/','Lnextapp/fx/plus/ui/a;','Lnextapp/fx/plus/ui/b;']+[f'Lk2/{c};' for c in dedicated]
    hits=[x for x in banned if x in corpus]
    if hits: raise RuntimeError(f'dangling deleted-type refs: {hits[:20]}')
    print('stage04b IAB/BillingClient core prune complete')

if __name__=='__main__': main()
