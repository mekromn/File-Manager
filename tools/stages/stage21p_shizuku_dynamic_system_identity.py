#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109039'

def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing method end '+sig)
    e+=len('\n.end method')
    return s,e,text[s:e]

def replace_method(text,sig,new):
    s,e,_=method(text,sig); return text[:s]+new+text[e:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'; pkg=sm/'dw/filemanager/shizuku'; pkg.mkdir(parents=True,exist_ok=True)

    # The existing UI calls this location "System (Root)" even when the actual
    # backend is an ADB-started Shizuku server running as uid=2000 (shell).
    # Present the capability honestly: shell-mode Shizuku => System (Shizuku),
    # while actual uid=0/root (including a root-mode Shizuku server) keeps the
    # original System (Root) wording.
    helper=r'''.class public final Ldw/filemanager/shizuku/ShizukuUi;
.super Ljava/lang/Object;
.source "DWShizukuUi"

.method public static systemTitle(Landroid/content/Context;)Ljava/lang/String;
    .locals 2
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :root
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->serverUid()I
    move-result v0
    if-eqz v0, :root
    const-string v0, "System (Shizuku)"
    return-object v0
    :root
    const v1, 0x7f1003f6
    invoke-virtual {p0, v1}, Landroid/content/Context;->getString(I)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static systemTitleResources(Landroid/content/res/Resources;)Ljava/lang/String;
    .locals 2
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :root
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->serverUid()I
    move-result v0
    if-eqz v0, :root
    const-string v0, "System (Shizuku)"
    return-object v0
    :root
    const v1, 0x7f1003f6
    invoke-virtual {p0, v1}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static systemDescription(Landroid/content/Context;)Ljava/lang/String;
    .locals 2
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :root
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->serverUid()I
    move-result v0
    if-eqz v0, :root
    const-string v0, "/ (Android system, via Shizuku shell)"
    return-object v0
    :root
    const v1, 0x7f1003ee
    invoke-virtual {p0, v1}, Landroid/content/Context;->getString(I)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method
'''
    (pkg/'ShizukuUi.smali').write_text(helper)

    # Shell catalog title used in Explorer/catalog UI.
    p=sm/'dw/filemanager/dirimpl/shell/ShellCatalog.smali'; t=p.read_text()
    sig='.method public final n(Landroid/content/Context;)Ljava/lang/String;'
    new=r'''.method public final n(Landroid/content/Context;)Ljava/lang/String;
    .locals 1
    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuUi;->systemTitle(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method'''
    t=replace_method(t,sig,new); p.write_text(t)

    # Home item title uses Resources rather than Context.
    p=sm/'dw/filemanager/ui/homeimpl/RootHomeItem.smali'; t=p.read_text()
    sig='.method public final i(Landroid/content/res/Resources;Lmb/h;)Ljava/lang/String;'
    new=r'''.method public final i(Landroid/content/res/Resources;Lmb/h;)Ljava/lang/String;
    .locals 1
    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuUi;->systemTitleResources(Landroid/content/res/Resources;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method'''
    t=replace_method(t,sig,new); p.write_text(t)

    # Root-selection result label.
    p=sm/'qf/a.smali'; t=p.read_text()
    old='    invoke-virtual {v0, p1}, Landroid/content/Context;->getString(I)Ljava/lang/String;'
    new='    invoke-static {v0}, Ldw/filemanager/shizuku/ShizukuUi;->systemTitle(Landroid/content/Context;)Ljava/lang/String;'
    if t.count(old)!=1: raise RuntimeError('qf/a root title anchor count '+str(t.count(old)))
    p.write_text(t.replace(old,new,1))

    # File chooser/home root row title + description. At the description site v1
    # already contains Resources, so reacquire Context from the View.
    p=sm/'eg/c.smali'; t=p.read_text()
    old='    invoke-virtual {v1, v4}, Landroid/content/Context;->getString(I)Ljava/lang/String;'
    new='    invoke-static {v1}, Ldw/filemanager/shizuku/ShizukuUi;->systemTitle(Landroid/content/Context;)Ljava/lang/String;'
    if t.count(old)!=1: raise RuntimeError('eg/c root title anchor count '+str(t.count(old)))
    t=t.replace(old,new,1)
    old='''    const v0, 0x7f1003ee

    .line 192
    .line 193
    .line 194
    invoke-virtual {v5, v0}, Ldw/filemanager/ui/widget/f0;->setDescription(I)V'''
    new='''    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    invoke-static {v0}, Ldw/filemanager/shizuku/ShizukuUi;->systemDescription(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0

    .line 192
    .line 193
    .line 194
    invoke-virtual {v5, v0}, Ldw/filemanager/ui/widget/f0;->setDescription(Ljava/lang/CharSequence;)V'''
    if t.count(old)!=1: raise RuntimeError('eg/c root description anchor count '+str(t.count(old)))
    p.write_text(t.replace(old,new,1))

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    corpus='\n'.join((sm/x).read_text(errors='ignore') for x in ('dw/filemanager/dirimpl/shell/ShellCatalog.smali','dw/filemanager/ui/homeimpl/RootHomeItem.smali','qf/a.smali','eg/c.smali'))
    if corpus.count('ShizukuUi;->systemTitle') < 3: raise RuntimeError('dynamic System title not installed on all surfaces')
    if 'ShizukuUi;->systemDescription' not in corpus: raise RuntimeError('dynamic System description missing')
    print('stage21p: System UI dynamically identifies shell Shizuku vs actual root; vc='+VC)

if __name__=='__main__': main()
