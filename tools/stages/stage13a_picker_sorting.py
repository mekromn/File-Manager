#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109008'

PICKER_SORT=r'''.class public final Ldw/filemanager/ui/filechooser/PickerSort;
.super Ljava/lang/Object;
.source "DWPickerSort"

.method private static prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    .locals 1
    invoke-static {p0}, Lmb/l;->d(Landroid/content/Context;)Lmb/l;
    move-result-object v0
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;
    return-object v0
.end method

.method public static sort(Landroid/content/Context;[Lkh/j;)V
    .locals 5
    if-eqz p1, :done

    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0

    const-string v1, "dw.picker.sort_mode"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v1
    invoke-static {v1}, Lkh/o;->b(I)Lkh/o;
    move-result-object v1

    const-string v3, "dw.picker.sort_desc"
    invoke-interface {v0, v3, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v3

    const-string v4, "dw.picker.folders_first"
    const/4 v2, 0x1
    invoke-interface {v0, v4, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0

    invoke-static {p1, v1, v3, v0}, Lkh/q;->a([Lkh/j;Lkh/o;ZZ)V

    :done
    return-void
.end method

.method public static set(Landroid/content/Context;IZ)V
    .locals 2
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    const-string v1, "dw.picker.sort_mode"
    invoke-interface {v0, v1, p1}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    const-string v1, "dw.picker.sort_desc"
    invoke-interface {v0, v1, p2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    return-void
.end method

.method public static toggleFoldersFirst(Landroid/content/Context;)Z
    .locals 3
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "dw.picker.folders_first"
    const/4 v2, 0x1
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v2
    xor-int/lit8 v2, v2, 0x1
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    return v2
.end method
'''

PICKER_ACTION=r'''.class public final Ldw/filemanager/ui/filechooser/PickerSortAction;
.super Ljava/lang/Object;
.source "DWPickerSort"

.implements Lyg/b;

.field private final activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
.field private final action:I

.method public constructor <init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/ui/filechooser/PickerSortAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iput p2, p0, Ldw/filemanager/ui/filechooser/PickerSortAction;->action:I
    return-void
.end method

.method public e(Lyg/c;)V
    .locals 3
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerSortAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iget v1, p0, Ldw/filemanager/ui/filechooser/PickerSortAction;->action:I

    packed-switch v1, :pswitch_data_0
    goto :refresh

    :pswitch_0
    const/4 v1, 0x0
    const/4 v2, 0x0
    goto :set_sort

    :pswitch_1
    const/4 v1, 0x0
    const/4 v2, 0x1
    goto :set_sort

    :pswitch_2
    const/4 v1, 0x2
    const/4 v2, 0x1
    goto :set_sort

    :pswitch_3
    const/4 v1, 0x2
    const/4 v2, 0x0
    goto :set_sort

    :pswitch_4
    const/4 v1, 0x3
    const/4 v2, 0x1
    goto :set_sort

    :pswitch_5
    const/4 v1, 0x3
    const/4 v2, 0x0
    goto :set_sort

    :pswitch_6
    const/4 v1, 0x1
    const/4 v2, 0x0
    goto :set_sort

    :pswitch_7
    const/4 v1, 0x1
    const/4 v2, 0x1
    goto :set_sort

    :pswitch_8
    invoke-static {v0}, Ldw/filemanager/ui/filechooser/PickerSort;->toggleFoldersFirst(Landroid/content/Context;)Z
    goto :refresh

    :set_sort
    invoke-static {v0, v1, v2}, Ldw/filemanager/ui/filechooser/PickerSort;->set(Landroid/content/Context;IZ)V

    :refresh
    iget-object v0, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v0, :done
    invoke-virtual {v0}, Leg/g;->a()V
    :done
    return-void

    :pswitch_data_0
    .packed-switch 0x0
        :pswitch_0
        :pswitch_1
        :pswitch_2
        :pswitch_3
        :pswitch_4
        :pswitch_5
        :pswitch_6
        :pswitch_7
        :pswitch_8
    .end packed-switch
.end method
'''

MENU=r'''
    # DW Stage13: persistent picker-only sort controls.
    new-instance p1, Lyg/r;
    const-string v4, "Sort"
    const/4 v5, 0x0
    invoke-direct {p1, v4, v5}, Lyg/r;-><init>(Ljava/lang/String;Landroid/graphics/drawable/Drawable;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x0
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Name (A-Z)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x1
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Name (Z-A)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x2
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Modified (Newest first)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x3
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Modified (Oldest first)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x4
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Size (Largest first)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x5
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Size (Smallest first)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x6
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Type (A-Z)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/4 v7, 0x7
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Type (Z-A)"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    new-instance v6, Ldw/filemanager/ui/filechooser/PickerSortAction;
    const/16 v7, 0x8
    invoke-direct {v6, p0, v7}, Ldw/filemanager/ui/filechooser/PickerSortAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v2, Lyg/s;
    const-string v4, "Toggle folders first"
    invoke-direct {v2, v4, v5, v6}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v2}, Lyg/r;->d(Lyg/u;)V

    invoke-virtual {v3, p1}, Lyg/r;->d(Lyg/u;)V
'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'

    d=sm/'dw/filemanager/ui/filechooser'; d.mkdir(parents=True,exist_ok=True)
    (d/'PickerSort.smali').write_text(PICKER_SORT)
    (d/'PickerSortAction.smali').write_text(PICKER_ACTION)

    # The chooser loader historically forces NAME ascending and reads the global
    # fileViewFoldersFirst preference. Replace only that isolated sort block.
    p=sm/'be/j.smali'; t=p.read_text()
    pat=re.compile(r'''\n    sget-object v0, Lkh/o;->Z:Lkh/o;\n\n(?:    \.line .*\n)*    iget-object v3, v11, Lhf/j0;->X1:Lmb/l;\n\n(?:    \.line .*\n)*    iget-object v3, v3, Lmb/l;->b:Landroid/content/SharedPreferences;\n\n(?:    \.line .*\n)*    const-string v4, "fileViewFoldersFirst"\n\n(?:    \.line .*\n)*    invoke-interface \{v3, v4, v9\}, Landroid/content/SharedPreferences;->getBoolean\(Ljava/lang/String;Z\)Z\n\n(?:    \.line .*\n)*    move-result v3\n\n(?:    \.line .*\n)*    invoke-static \{v12, v0, v8, v3\}, Lkh/q;->a\(\[Lkh/j;Lkh/o;ZZ\)V''')
    repl='''\n    # DW Stage13: picker-only persisted sort; main browser preferences are untouched.\n    invoke-virtual {v11}, Landroid/view/View;->getContext()Landroid/content/Context;\n    move-result-object v0\n    invoke-static {v0, v12}, Ldw/filemanager/ui/filechooser/PickerSort;->sort(Landroid/content/Context;[Lkh/j;)V'''
    t,n=pat.subn(repl,t,count=1)
    if n!=1: raise RuntimeError('chooser hard-coded sort block not found')
    p.write_text(t)

    # Add Sort submenu immediately after the existing Show Hidden item.
    p=d/'ChooserActivity.smali'; t=p.read_text()
    marker='''    iput-object v2, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->m2:Lyg/s;\n\n    .line 206\n    .line 207\n    invoke-virtual {v3, v2}, Lyg/r;->d(Lyg/u;)V\n'''
    if t.count(marker)!=1: raise RuntimeError(f'ChooserActivity overflow anchor count={t.count(marker)}')
    t=t.replace(marker,marker+MENU,1)
    p.write_text(t)

    # Install over the device-confirmed v9109007 internal-association build.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    # Durable guards.
    bt=(sm/'be/j.smali').read_text(); ct=p.read_text(); ht=(d/'PickerSort.smali').read_text()
    if 'const-string v4, "fileViewFoldersFirst"' in bt and 'PickerSort;->sort' not in bt:
        raise RuntimeError('old chooser global folders-first sort path remains active')
    for tok in ('dw.picker.sort_mode','dw.picker.sort_desc','dw.picker.folders_first','Lkh/q;->a([Lkh/j;Lkh/o;ZZ)V'):
        if tok not in ht: raise RuntimeError('picker sort helper missing '+tok)
    for label in ('Sort','Name (A-Z)','Name (Z-A)','Modified (Newest first)','Modified (Oldest first)','Size (Largest first)','Size (Smallest first)','Type (A-Z)','Type (Z-A)','Toggle folders first'):
        if label not in ct: raise RuntimeError('picker menu missing '+label)
    if 'PickerSortAction' not in ct: raise RuntimeError('picker sort actions not wired')

    print('stage13a DW File Chooser sorting installed: NAME/DATE/SIZE/TYPE asc+desc, picker-only persistence, folders-first toggle; vc='+VC)

if __name__=='__main__': main()
