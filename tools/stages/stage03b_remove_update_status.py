#!/usr/bin/env python3
from pathlib import Path
import argparse, re

HH_B = r'''.method public b(Lnextapp/fx/ui/fxsystem/MainPrefActivity;Landroid/preference/PreferenceGroup;)V
    .locals 13
    const-string v0, "security"
    invoke-static {p1, p2, v0}, Ltf/c;->c(Landroid/content/Context;Landroid/preference/PreferenceGroup;Ljava/lang/String;)V
    const-string v0, "network"
    invoke-static {p1, p2, v0}, Ltf/c;->c(Landroid/content/Context;Landroid/preference/PreferenceGroup;Ljava/lang/String;)V

    const v5, 0x7f0801fc
    const-string v6, "nextapp.fx.plus.ui.share.WebAccessPrefActivity"
    const v3, 0x7f100678
    const v4, 0x7f100677
    move-object v1, p1
    move-object v2, p2
    invoke-static/range {v1 .. v6}, Ltf/c;->b(Landroid/content/Context;Landroid/preference/PreferenceGroup;IIILjava/lang/String;)V

    move-object v7, v1
    move-object v8, v2
    const v11, 0x7f0801ed
    const-string v12, "nextapp.fx.plus.ui.share.ConnectPrefActivity"
    const v9, 0x7f100585
    const v10, 0x7f100584
    invoke-static/range {v7 .. v12}, Ltf/c;->b(Landroid/content/Context;Landroid/preference/PreferenceGroup;IIILjava/lang/String;)V
    return-void
.end method'''

def replace_method(path: Path, prefix: str, body: str):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1; out.extend(body.splitlines()); out.append('')
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: {prefix} count {n}')
    path.write_text('\n'.join(out)+'\n')

def cut_label_block(path: Path, label: str, end_label: str, comment: str):
    lines=path.read_text().splitlines()
    a=next(i for i,l in enumerate(lines) if l.strip()==label)
    b=next(i for i in range(a+1,len(lines)) if lines[i].strip()==end_label)
    lines[a:b]=[f'    {label}',f'    # {comment}','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def neutralize_hf_f_trial_arm(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final h()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if lines[i].strip()==':pswitch_3')
    b=next(i for i in range(a+1,e) if lines[i].strip()==':pswitch_4')
    lines[a:b]=['    :pswitch_3','    # removed retired trial/update action','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def neutralize_hf_n_h(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public h(Z)V'))
    sw=next(i for i in range(s,len(lines)) if 'packed-switch v0, :pswitch_data_0' in lines[i])
    b=next(i for i in range(sw+1,len(lines)) if lines[i].strip()==':pswitch_0')
    lines[sw+1:b]=['','    # removed retired update/status callback','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def prune_plus_j(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method static constructor <clinit>()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if 'sget-object v0, Lnextapp/fx/ui/homeimpl/e;->a:' in lines[i])
    b=next(i for i in range(a+1,e) if 'new-instance v0, Ltf/b;' in lines[i])
    del lines[a:b]
    for val in ('0x17','0x16'):
        idx=next(i for i in range(s,len(lines)) if f'const/16 v3, {val}' in lines[i])
        a=idx
        while a>s and 'new-instance v0, Ltf/b;' not in lines[a]: a-=1
        if 'new-instance v0, Ltf/b;' not in lines[a]: raise RuntimeError(f'start block {val} not found')
        b=idx
        while b<len(lines) and 'invoke-static {v0}, Ltf/d;->b(Ltf/b;)V' not in lines[b]: b+=1
        if b>=len(lines): raise RuntimeError(f'end block {val} not found')
        del lines[a:b+1]
    path.write_text('\n'.join(lines)+'\n')

def remove_manifest_activity(path: Path):
    lines=path.read_text().splitlines(); old=len(lines)
    lines=[l for l in lines if 'android:name="nextapp.fx.plus.ui.update.UpdateActivity"' not in l]
    if len(lines)!=old-1: raise RuntimeError('UpdateActivity manifest entry count unexpected')
    path.write_text('\n'.join(lines)+'\n')

def remove_xml_item(path: Path):
    lines=path.read_text().splitlines(); old=len(lines)
    lines=[l for l in lines if 'nextapp.fx.plus.ui.UpdateHomeItem' not in l]
    if len(lines)!=old-1: raise RuntimeError('UpdateHomeItem module entry count unexpected')
    path.write_text('\n'.join(lines)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    remove_manifest_activity(root/'AndroidManifest.xml')
    remove_xml_item(root/'res/xml/module_plusui.xml')
    prune_plus_j(sm/'nextapp/fx/plus/ui/j.smali')
    replace_method(sm/'hh/e.smali','.method public b(Lnextapp/fx/ui/fxsystem/MainPrefActivity;Landroid/preference/PreferenceGroup;)V',HH_B)
    replace_method(sm/'hf/n.smali','.method public d(Z)V','.method public d(Z)V\n    .locals 0\n    # retired update/status callback\n    return-void\n.end method')
    neutralize_hf_n_h(sm/'hf/n.smali')
    neutralize_hf_f_trial_arm(sm/'hf/f.smali')
    cut_label_block(sm/'androidx/activity/i.smali',':pswitch_9',':pswitch_a','removed retired update notification arm')
    cut_label_block(sm/'me/j.smali',':pswitch_16',':pswitch_data_0','removed retired update/theme-launch arm')
    remove=['nextapp/fx/plus/ui/UpdateHomeItem.smali','nextapp/fx/plus/ui/update/UpdateActivity.smali','me/a.smali','me/c.smali','me/d.smali','me/e.smali','me/f.smali','me/g.smali','me/i.smali','me/k.smali','me/l.smali','me/m.smali']
    for rel in remove:
        p=sm/rel
        if not p.exists(): raise RuntimeError(f'missing expected class {rel}')
        p.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    banned=['Lnextapp/fx/plus/ui/UpdateHomeItem;','Lnextapp/fx/plus/ui/update/UpdateActivity;','Lme/f;','Lme/l;','Lme/c;','Lme/d;','Lme/e;','Lme/g;','Lme/i;','Lme/m;','Lme/a;','Lme/k;']
    hits=[x for x in banned if x in corpus]
    if hits: raise RuntimeError(f'dangling removed-class refs: {hits}')
    assert 'nextapp.fx.plus.ui.update.UpdateActivity' not in (root/'AndroidManifest.xml').read_text()
    assert 'nextapp.fx.plus.ui.UpdateHomeItem' not in (root/'res/xml/module_plusui.xml').read_text()
    print('stage03b update/status root cut complete')

if __name__=='__main__': main()
