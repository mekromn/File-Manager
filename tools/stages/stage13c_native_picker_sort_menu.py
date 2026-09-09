#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109010'

PICKER_CALLBACK=r'''.class public final Ldw/filemanager/ui/filechooser/PickerSortCallback;
.super Ljava/lang/Object;
.source "DWPickerSort"

.implements Laf/j;

.field private final activity:Ldw/filemanager/ui/filechooser/ChooserActivity;

.method public constructor <init>(Ldw/filemanager/ui/filechooser/ChooserActivity;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/ui/filechooser/PickerSortCallback;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    return-void
.end method

.method public a(Ljava/lang/Object;ZZ)V
    .locals 2
    instance-of p3, p1, Lkh/o;
    if-eqz p3, :done
    check-cast p1, Lkh/o;
    invoke-virtual {p1}, Ljava/lang/Enum;->ordinal()I
    move-result p1
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerSortCallback;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    invoke-static {v0, p1, p2}, Ldw/filemanager/ui/filechooser/PickerSort;->set(Landroid/content/Context;IZ)V
    iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v1, :done
    invoke-virtual {v1}, Leg/g;->a()V
    :done
    return-void
.end method
'''

FOLDERS_ACTION=r'''.class public final Ldw/filemanager/ui/filechooser/PickerFoldersFirstAction;
.super Ljava/lang/Object;
.source "DWPickerSort"

.implements Lyg/b;

.field private final activity:Ldw/filemanager/ui/filechooser/ChooserActivity;

.method public constructor <init>(Ldw/filemanager/ui/filechooser/ChooserActivity;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/ui/filechooser/PickerFoldersFirstAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    return-void
.end method

.method public e(Lyg/c;)V
    .locals 2
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerFoldersFirstAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    invoke-static {v0}, Ldw/filemanager/ui/filechooser/PickerSort;->toggleFoldersFirst(Landroid/content/Context;)Z
    iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v1, :done
    invoke-virtual {v1}, Leg/g;->a()V
    :done
    return-void
.end method
'''

PICKER_MENU=r'''.class public final Ldw/filemanager/ui/filechooser/PickerSortMenu;
.super Ljava/lang/Object;
.source "DWPickerSort"

.method public static add(Ldw/filemanager/ui/filechooser/ChooserActivity;Lyg/r;)V
    .locals 12

    # Same native section-heading model used by DW's main overflow menu.
    new-instance v0, Lyg/q;
    const-string v1, "SORT BY"
    invoke-direct {v0, v1}, Lyg/q;-><init>(Ljava/lang/String;)V
    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V

    new-instance v9, Ldw/filemanager/ui/filechooser/PickerSortCallback;
    invoke-direct {v9, p0}, Ldw/filemanager/ui/filechooser/PickerSortCallback;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;)V

    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->mode(Landroid/content/Context;)Lkh/o;
    move-result-object v10
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->descending(Landroid/content/Context;)Z
    move-result v11

    # NAME — exactly the same af/k sort tile used by the main DW menu.
    new-instance v0, Laf/k;
    move-object v1, p0
    const-string v2, "Name"
    const-string v3, "action_sort_name"
    sget-object v4, Lkh/o;->Z:Lkh/o;
    const/4 v5, 0x1
    move-object v6, v9
    move-object v7, v10
    move v8, v11
    invoke-direct/range {v0 .. v8}, Laf/k;-><init>(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;ILaf/j;Ljava/lang/Object;Z)V
    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V

    # DATE — default direction newest first, matching DW's native main menu behavior.
    new-instance v0, Laf/k;
    move-object v1, p0
    const-string v2, "Date"
    const-string v3, "action_calendar"
    sget-object v4, Lkh/o;->Y1:Lkh/o;
    const/4 v5, 0x3
    move-object v6, v9
    move-object v7, v10
    move v8, v11
    invoke-direct/range {v0 .. v8}, Laf/k;-><init>(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;ILaf/j;Ljava/lang/Object;Z)V
    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V

    # KIND.
    new-instance v0, Laf/k;
    move-object v1, p0
    const-string v2, "Kind"
    const-string v3, "action_kind"
    sget-object v4, Lkh/o;->X1:Lkh/o;
    const/4 v5, 0x1
    move-object v6, v9
    move-object v7, v10
    move v8, v11
    invoke-direct/range {v0 .. v8}, Laf/k;-><init>(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;ILaf/j;Ljava/lang/Object;Z)V
    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V

    # SIZE — default direction largest first, matching DW's native main menu behavior.
    new-instance v0, Laf/k;
    move-object v1, p0
    const-string v2, "Size"
    const-string v3, "action_size"
    sget-object v4, Lkh/o;->Z1:Lkh/o;
    const/4 v5, 0x3
    move-object v6, v9
    move-object v7, v10
    move v8, v11
    invoke-direct/range {v0 .. v8}, Laf/k;-><init>(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;ILaf/j;Ljava/lang/Object;Z)V
    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V

    # Native divider, then picker-only folders-first control.
    new-instance v0, Lyg/y;
    invoke-direct {v0}, Ljava/lang/Object;-><init>()V
    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V

    new-instance v0, Ldw/filemanager/ui/filechooser/PickerFoldersFirstAction;
    invoke-direct {v0, p0}, Ldw/filemanager/ui/filechooser/PickerFoldersFirstAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;)V
    new-instance v1, Lyg/p;
    const-string v2, "Folders First"
    const/4 v3, 0x0
    invoke-direct {v1, v2, v3, v0}, Lyg/p;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V

    return-void
.end method
'''

PICKER_EXTRA_METHODS=r'''
.method public static mode(Landroid/content/Context;)Lkh/o;
    .locals 3
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "dw.picker.sort_mode"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v0
    invoke-static {v0}, Lkh/o;->b(I)Lkh/o;
    move-result-object v0
    return-object v0
.end method

.method public static descending(Landroid/content/Context;)Z
    .locals 3
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "dw.picker.sort_desc"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    return v0
.end method
'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    d=sm/'dw/filemanager/ui/filechooser'

    # Extend the picker-only preference helper with native-menu state getters.
    ps=d/'PickerSort.smali'; t=ps.read_text()
    if 'mode(Landroid/content/Context;)Lkh/o;' not in t:
        t=t.rstrip()+"\n"+PICKER_EXTRA_METHODS+"\n"
    ps.write_text(t)

    (d/'PickerSortCallback.smali').write_text(PICKER_CALLBACK)
    (d/'PickerFoldersFirstAction.smali').write_text(FOLDERS_ACTION)
    (d/'PickerSortMenu.smali').write_text(PICKER_MENU)

    # Remove the custom nested Sort submenu entirely and inject the same native
    # inline sort controls used by DW's main overflow menu.
    chooser=d/'ChooserActivity.smali'; t=chooser.read_text()
    pat=re.compile(r'\n    # DW Stage13: persistent picker-only sort controls\..*?\n    invoke-virtual \{v3, p1\}, Lyg/r;->d\(Lyg/u;\)V\n', re.S)
    repl='''\n    # DW Stage13c: native inline SORT BY controls, matching the main DW overflow menu.\n    invoke-static {p0, v3}, Ldw/filemanager/ui/filechooser/PickerSortMenu;->add(Ldw/filemanager/ui/filechooser/ChooserActivity;Lyg/r;)V\n'''
    t,n=pat.subn(repl,t,count=1)
    if n!=1: raise RuntimeError(f'custom picker Sort submenu block not found: {n}')
    chooser.write_text(t)

    # The old custom action class is no longer referenced after removing the submenu.
    old=d/'PickerSortAction.smali'
    if old.exists(): old.unlink()

    # Install over 9109009.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    # Durable guards: no nested Sort model remains; native DW af/k sort tiles do.
    ct=chooser.read_text(); mt=(d/'PickerSortMenu.smali').read_text()
    if 'const-string v4, "Sort"' in ct: raise RuntimeError('legacy nested picker Sort submenu survived')
    if 'PickerSortAction' in ct or old.exists(): raise RuntimeError('legacy picker submenu action survived')
    for tok in ('new-instance v0, Laf/k;','const-string v1, "SORT BY"','action_sort_name','action_calendar','action_kind','action_size'):
        if tok not in mt: raise RuntimeError('native picker sort UI missing '+tok)
    if 'invoke-static {p0, v3}, Ldw/filemanager/ui/filechooser/PickerSortMenu;->add' not in ct:
        raise RuntimeError('ChooserActivity native sort menu hook missing')

    print('stage13c replaced crashing nested picker Sort submenu with native inline DW SORT BY controls; vc='+VC)

if __name__=='__main__': main()
