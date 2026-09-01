#!/usr/bin/env python3
from __future__ import annotations
import argparse, re
from pathlib import Path

TRIAL_STRINGS = {
    'about_header_trial_plus','about_item_trial_expires','about_item_trial_status','about_value_trial_recently_expired','action_trial_start','home_note_asterisk_plus_trial','home_section_trailing_text_plus_trial','state_trial_active','state_trial_expired','update_trial_plus_dialog_message_expired','update_trial_plus_dialog_message_start','update_trial_plus_dialog_title','tutorial_start_plus_check','tutorial_tab_title_upgrade','tutorial_upgrade_description','tutorial_upgrade_plus','tutorial_upgrade_root','tutorial_upgrade_title','update_warning_theme_plus_required',
}
TRIAL_IDS = {
    '0x7f10001d','0x7f100024','0x7f100025','0x7f10003d','0x7f1000d9','0x7f100382','0x7f100387','0x7f10079d','0x7f10079e','0x7f1008d5','0x7f1008d6','0x7f1008d7','0x7f1008a9','0x7f1008b2','0x7f1008b4','0x7f1008b5','0x7f1008b6','0x7f1008b7','0x7f1008d8',
}

def replace_method(path: Path, method_prefix: str, body: str) -> None:
    lines=path.read_text().splitlines(); out=[]; i=0; count=0
    while i<len(lines):
        if lines[i].startswith(method_prefix):
            count+=1; out.extend(body.strip('\n').splitlines())
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            out.append(''); continue
        out.append(lines[i]); i+=1
    if count!=1: raise RuntimeError(f'{path}: expected one {method_prefix!r}, got {count}')
    path.write_text('\n'.join(out)+'\n')

def remove_method(path: Path, method_prefix: str) -> None:
    lines=path.read_text().splitlines(); out=[]; i=0; count=0
    while i<len(lines):
        if lines[i].startswith(method_prefix):
            count+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if count!=1: raise RuntimeError(f'{path}: expected one {method_prefix!r}, got {count}')
    path.write_text('\n'.join(out)+'\n')

def remove_string_name_from_xml(path: Path, name: str) -> int:
    if not path.exists(): return 0
    text=path.read_text(); pat=re.compile(r'\n?\s*<string\s+name="'+re.escape(name)+r'"(?:\s+[^>]*)?>.*?</string>',re.S)
    text2,n=pat.subn('',text)
    if n: path.write_text(text2)
    return n

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); args=ap.parse_args(); root=args.decoded; smali=root/'smali'
    j=smali/'nextapp/fx/plus/ui/j.smali'; t=j.read_text(); t,n=re.subn(r'^\.field public static b:Z\n\n?','',t,count=1,flags=re.M)
    if n!=1: raise RuntimeError('registry trial flag field not found exactly once')
    j.write_text(t)
    replace_method(smali/'nextapp/fx/plus/ui/PlusRegistry$1.smali','.method public final a(Landroid/content/Context;Lmb/h;)Ljava/lang/String;','''.method public final a(Landroid/content/Context;Lmb/h;)Ljava/lang/String;
    .locals 1
    const/4 v0, 0x0
    return-object v0
.end method''')
    hs=smali/'nextapp/fx/plus/ui/PlusRegistry$PlusHomeSection.smali'
    replace_method(hs,'.method public final d(Landroid/content/res/Resources;)Ljava/lang/String;','''.method public final d(Landroid/content/res/Resources;)Ljava/lang/String;
    .locals 1
    const/4 v0, 0x0
    return-object v0
.end method''')
    t=hs.read_text(); t=re.sub(r'\n\s*const/4 v0, 0x0\n\s*sput-boolean v0, Lnextapp/fx/plus/ui/j;->b:Z','',t); hs.write_text(t)
    replace_method(smali/'nextapp/fx/plus/ui/PlusHomeItem.smali','.method public final i(Landroid/content/res/Resources;Lmb/h;)Ljava/lang/String;','''.method public final i(Landroid/content/res/Resources;Lmb/h;)Ljava/lang/String;
    .locals 1
    invoke-virtual {p0, p1}, Lnextapp/fx/plus/ui/PlusHomeItem;->k(Landroid/content/res/Resources;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method''')
    corpus='\n'.join(p.read_text(errors='ignore') for p in smali.rglob('*.smali'))
    ctor='Lbe/w;-><init>(Landroid/content/Context;)V'
    if ctor in corpus: raise RuntimeError('be/w trial constructor still has a caller; refusing to delete it')
    remove_method(smali/'be/w.smali','.method public constructor <init>(Landroid/content/Context;)V')
    ext=smali/'nextapp/fx/plus/ui/PlusExtension.smali'; lines=ext.read_text().splitlines()
    a=next(i for i,l in enumerate(lines) if 'new-instance v0, Lnextapp/fx/plus/ui/g;' in l)
    b=next(i for i in range(a+1,len(lines)) if 'invoke-virtual {v1, v2, v0}, La2/n;->W(Ljava/lang/Object;Ljava/lang/Object;)V' in lines[i])
    del lines[a:b+1]; ext.write_text('\n'.join(lines)+'\n')
    tut=smali/'nextapp/fx/ui/doc/TutorialActivity.smali'; lines=tut.read_text().splitlines()
    a=next(i for i,l in enumerate(lines) if 'sget-object v0, Lnextapp/fx/ui/doc/TutorialActivity;->t2:La2/n;' in l)
    b=next(i for i in range(a+1,len(lines)) if lines[i].strip()==':cond_0')
    del lines[a:b]; tut.write_text('\n'.join(lines)+'\n')
    for rel in ('nextapp/fx/plus/ui/g.smali','nextapp/fx/plus/ui/l.smali'):
        q=smali/rel
        if not q.exists(): raise RuntimeError(f'missing retired tutorial class {rel}')
        q.unlink()
    removed=0
    for values in root.glob('res/values*'):
        sp=values/'strings.xml'
        for name in TRIAL_STRINGS: removed+=remove_string_name_from_xml(sp,name)
    pub=root/'res/values/public.xml'; pt=pub.read_text()
    for name in TRIAL_STRINGS:
        pt,n=re.subn(r'^\s*<public type="string" name="'+re.escape(name)+r'" id="0x[0-9a-fA-F]+" />\n?','',pt,flags=re.M)
        if n!=1: raise RuntimeError(f'expected one public declaration for {name}, got {n}')
    pub.write_text(pt)
    corpus='\n'.join(p.read_text(errors='ignore') for p in smali.rglob('*.smali'))
    if 'Lnextapp/fx/plus/ui/j;->b:Z' in corpus: raise RuntimeError('temporary-state flag reference survives')
    for tok in ('Lnextapp/fx/plus/ui/g;','Lnextapp/fx/plus/ui/l;'):
        if tok in corpus: raise RuntimeError(f'retired tutorial class reference survives: {tok}')
    for rid in TRIAL_IDS:
        if rid in corpus: raise RuntimeError(f'trial-only resource id still referenced: {rid}')
    for token in ('trialPlusExpiration','trialexp','Llh/n;->j(Landroid/content/Context;)I','Ljb/a;->m(Landroid/content/Context;)J','Ljb/a;->p(Landroid/content/Context;)Z','Ljb/a;->q(Landroid/content/Context;)Z','Lmb/l;->G(J)V'):
        if token in corpus: raise RuntimeError(f'retired time-window token survives: {token}')
    strings='\n'.join(p.read_text(errors='ignore') for p in root.glob('res/values*/strings.xml') if p.exists())
    for name in TRIAL_STRINGS:
        if f'name="{name}"' in strings: raise RuntimeError(f'trial resource name survives: {name}')
    print(f'stage03d resource/state pruning complete; removed {removed} localized string elements')

if __name__=='__main__': main()
