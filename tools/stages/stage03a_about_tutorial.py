#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil, re

ABOUT = r'''.class public Lnextapp/fx/ui/about/AboutActivity;
.super Landroid/app/Activity;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method public onCreate(Landroid/os/Bundle;)V
    .locals 4
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    new-instance v0, Landroid/widget/TextView;
    invoke-direct {v0, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    const-string v1, "DW File Manager\n\nVersion 9.1.0.8\n\nPrivacy-first file management."
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    const/high16 v1, 0x41a00000    # 20.0f
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextSize(F)V

    const/16 v1, 0x30
    const/16 v2, 0x30
    const/16 v3, 0x30
    invoke-virtual {v0, v1, v2, v3, v2}, Landroid/view/View;->setPadding(IIII)V

    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V
    return-void
.end method
'''

TUTORIAL_L = r'''.method public final l()V
    .locals 4
    invoke-static {p0}, Lmb/l;->d(Landroid/content/Context;)Lmb/l;
    move-result-object v0
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    const-string v1, "tutorialVersion"
    const/4 v2, 0x4
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    const-string v1, "_lastUpdate"
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J
    move-result-wide v2
    invoke-interface {v0, v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putLong(Ljava/lang/String;J)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->commit()Z
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V
    return-void
.end method'''

def replace_method(path: Path, signature_prefix: str, body: str):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(signature_prefix):
            n+=1; out.extend(body.splitlines()); out.append('')
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: expected 1 {signature_prefix}, got {n}')
    path.write_text('\n'.join(out)+'\n')

def remove_method(path: Path, signature_prefix: str):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(signature_prefix):
            n+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: expected 1 {signature_prefix}, got {n}')
    path.write_text('\n'.join(out)+'\n')

def strip_tutorial_g_loop(path: Path):
    lines=path.read_text().splitlines()
    # only within F(), remove collection loop from first s2 load through :cond_1 label.
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final F('))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if 'Lnextapp/fx/ui/doc/TutorialActivity;->s2:La2/n;' in lines[i])
    b=next(i for i in range(a,e) if lines[i].strip()==':cond_1')
    lines[a:b+1]=['    # removed retired trial-option extension loop']
    path.write_text('\n'.join(lines)+'\n')

def strip_onback_trial_loop(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final onBackPressed()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if 'Lnextapp/fx/ui/doc/TutorialActivity;->s2:La2/n;' in lines[i])
    b=next(i for i in range(a,e) if lines[i].strip()==':cond_1')
    lines[a:b+1]=['    # removed retired trial-option extension loop']
    path.write_text('\n'.join(lines)+'\n')

def strip_plus_extension_trial_registration(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method static constructor <clinit>()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if 'new-instance v0, Lnextapp/fx/plus/ui/k;' in lines[i])
    # stop before next useful tutorial extension registration (plus/ui/g)
    b=next(i for i in range(a,e) if 'new-instance v0, Lnextapp/fx/plus/ui/g;' in lines[i])
    lines[a:b]=['    # removed retired trial tutorial registration']
    path.write_text('\n'.join(lines)+'\n')

def neutralize_be_arm(path: Path):
    lines=path.read_text().splitlines()
    # pswitch_3 is the dedicated checked-change arm for plus/ui/k in this baseline.
    a=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_3')
    b=next(i for i in range(a+1,len(lines)) if lines[i].strip()==':pswitch_4')
    lines[a:b]=['    :pswitch_3','    # retired trial checkbox callback','    return-void','']
    path.write_text('\n'.join(lines)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded', type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    (sm/'nextapp/fx/ui/about/AboutActivity.smali').write_text(ABOUT)

    tut=sm/'nextapp/fx/ui/doc/TutorialActivity.smali'
    replace_method(tut,'.method public final l()V',TUTORIAL_L)
    strip_onback_trial_loop(tut)

    strip_tutorial_g_loop(sm/'nextapp/fx/ui/doc/TutorialActivity$g.smali')
    neutralize_be_arm(sm/'be/a.smali')
    strip_plus_extension_trial_registration(sm/'nextapp/fx/plus/ui/PlusExtension.smali')

    k=sm/'nextapp/fx/plus/ui/k.smali'
    if k.exists(): k.unlink()

    # About was the final Stage02 consumer of the temporary integer adapter.
    remove_method(sm/'lh/n.smali','.method public static j(Landroid/content/Context;)I')

    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    assert 'Lnextapp/fx/plus/ui/k;' not in corpus
    assert 'Llh/n;->j(Landroid/content/Context;)I' not in corpus
    assert not k.exists()
    assert 'trialPlusExpiration' in corpus  # next cut removes persistence; do not overclaim yet
    print('stage03a about/tutorial cut complete')

if __name__=='__main__': main()
