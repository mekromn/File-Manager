#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109011'

PICKER_SORT_METHODS={
'sort':r'''.method public static sort(Landroid/content/Context;[Lkh/j;)V
    .locals 5
    if-eqz p1, :done

    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->mode(Landroid/content/Context;)Lkh/o;
    move-result-object v0
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->descending(Landroid/content/Context;)Z
    move-result v1

    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v2
    const-string v3, "dw.picker.folders_first"
    const/4 v4, 0x1
    invoke-interface {v2, v3, v4}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v2

    invoke-static {p1, v0, v1, v2}, Lkh/q;->a([Lkh/j;Lkh/o;ZZ)V
    :done
    return-void
.end method''',
'set':r'''.method public static set(Landroid/content/Context;IZ)V
    .locals 6
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1

    # Selecting a new sort leaves any previous per-folder override so the new
    # selection takes effect immediately and can be saved again explicitly.
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->folderBase(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v2
    if-eqz v2, :global
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v4, ".mode"
    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v3
    invoke-interface {v1, v3}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v4, ".desc"
    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-interface {v1, v2}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v1

    :global
    const-string v2, "dw.picker.sort_mode"
    invoke-interface {v1, v2, p1}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    const-string v2, "dw.picker.sort_desc"
    invoke-interface {v1, v2, p2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->apply()V
    return-void
.end method''',
'mode':r'''.method public static mode(Landroid/content/Context;)Lkh/o;
    .locals 6
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->folderBase(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v1
    if-eqz v1, :global
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v3, ".mode"
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-interface {v0, v2}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z
    move-result v3
    if-eqz v3, :global
    const/4 v3, 0x0
    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v0
    goto :decode
    :global
    const-string v1, "dw.picker.sort_mode"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v0
    :decode
    invoke-static {v0}, Lkh/o;->b(I)Lkh/o;
    move-result-object v0
    return-object v0
.end method''',
'descending':r'''.method public static descending(Landroid/content/Context;)Z
    .locals 6
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->folderBase(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v1
    if-eqz v1, :global
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v3, ".desc"
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-interface {v0, v2}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z
    move-result v3
    if-eqz v3, :global
    const/4 v3, 0x0
    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    return v0
    :global
    const-string v1, "dw.picker.sort_desc"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    return v0
.end method'''
}

PICKER_SORT_EXTRA=r'''
.method private static folderBase(Landroid/content/Context;)Ljava/lang/String;
    .locals 4
    instance-of v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
    if-eqz v0, :none
    check-cast p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v0, :none
    invoke-virtual {v0}, Leg/g;->getPath()Lhh/f;
    move-result-object v0
    if-eqz v0, :none
    invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;
    move-result-object v0
    new-instance v1, Ljava/lang/StringBuilder;
    const-string v2, "dw.picker.folder_sort."
    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
    :none
    const/4 v0, 0x0
    return-object v0
.end method

.method public static isSavedForFolder(Landroid/content/Context;)Z
    .locals 4
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->folderBase(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :no
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1, v0}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v2, ".mode"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v1
    invoke-interface {v1, v0}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z
    move-result v0
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static saveForFolder(Landroid/content/Context;)Z
    .locals 8
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->folderBase(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :fail
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerSort;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v1

    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2, v0}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v3, ".mode"
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3, v0}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    const-string v0, ".desc"
    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v3

    invoke-interface {v1, v2}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z
    move-result v0
    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    if-eqz v0, :save
    invoke-interface {v4, v2}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    invoke-interface {v4, v3}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    invoke-interface {v4}, Landroid/content/SharedPreferences$Editor;->apply()V
    const/4 v0, 0x0
    return v0

    :save
    const-string v0, "dw.picker.sort_mode"
    const/4 v5, 0x0
    invoke-interface {v1, v0, v5}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v0
    const-string v6, "dw.picker.sort_desc"
    invoke-interface {v1, v6, v5}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v1
    invoke-interface {v4, v2, v0}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0, v3, v1}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    const/4 v0, 0x1
    return v0
    :fail
    const/4 v0, 0x0
    return v0
.end method
'''

PICKER_PANEL=r'''.class public final Ldw/filemanager/ui/filechooser/PickerPanel;
.super Ljava/lang/Object;
.source "DWPickerPanel"

.method private static prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    .locals 1
    invoke-static {p0}, Lmb/l;->d(Landroid/content/Context;)Lmb/l;
    move-result-object v0
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;
    return-object v0
.end method

.method public static viewMode(Landroid/content/Context;)Lmb/m;
    .locals 3
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "dw.picker.view_mode"
    const/4 v2, 0x5
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v0
    sget-object v1, Lmb/m;->Z:Lmb/m;
    invoke-static {v0, v1}, Lmb/m;->a(ILmb/m;)Lmb/m;
    move-result-object v0
    return-object v0
.end method

.method public static setViewMode(Ldw/filemanager/ui/filechooser/ChooserActivity;Lmb/m;)V
    .locals 3
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    const-string v1, "dw.picker.view_mode"
    iget v2, p1, Lmb/m;->f:I
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v0, :done
    invoke-virtual {v0}, Leg/g;->a()V
    :done
    return-void
.end method

.method public static applyViewMode(Landroid/content/Context;Lhf/g0;)V
    .locals 1
    if-eqz p1, :done
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->viewMode(Landroid/content/Context;)Lmb/m;
    move-result-object v0
    invoke-virtual {p1, v0}, Lhf/g0;->setViewMode(Lmb/m;)V
    :done
    return-void
.end method

.method public static hidden(Landroid/content/Context;)Z
    .locals 3
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "dw.picker.show_hidden"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    return v0
.end method

.method public static setHidden(Landroid/content/Context;Z)V
    .locals 2
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    const-string v1, "dw.picker.show_hidden"
    invoke-interface {v0, v1, p1}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    return-void
.end method

.method public static toggleFilter(Ldw/filemanager/ui/filechooser/ChooserActivity;)V
    .locals 7
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->p2:Lhf/l0;
    if-eqz v0, :create
    invoke-virtual {v0}, Landroid/view/View;->getVisibility()I
    move-result v1
    if-eqz v1, :hide
    goto :show

    :create
    new-instance v0, Lhf/l0;
    move-object v1, p0
    invoke-direct {v0, v1}, Lhf/l0;-><init>(Laf/c;)V
    new-instance v1, Ldw/filemanager/ui/filechooser/PickerFilterListener;
    invoke-direct {v1, p0}, Ldw/filemanager/ui/filechooser/PickerFilterListener;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;)V
    invoke-virtual {v0, v1}, Lhf/l0;->setOnFilterUpdateListener(Lhf/k0;)V
    const/4 v2, 0x1
    const/4 v3, 0x0
    invoke-static {v2, v3}, Lhf/p0;->m(ZZ)Landroid/widget/LinearLayout$LayoutParams;
    move-result-object v2
    invoke-virtual {v0, v2}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V
    iget-object v2, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    invoke-virtual {v2}, Landroid/view/View;->getParent()Landroid/view/ViewParent;
    move-result-object v2
    instance-of v3, v2, Landroid/view/ViewGroup;
    if-eqz v3, :done
    check-cast v2, Landroid/view/ViewGroup;
    const/4 v3, 0x0
    invoke-virtual {v2, v0, v3}, Landroid/view/ViewGroup;->addView(Landroid/view/View;I)V
    iput-object v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->p2:Lhf/l0;

    :show
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V
    iget-object v1, v0, Lhf/l0;->X1:Landroid/widget/EditText;
    invoke-virtual {v1}, Landroid/view/View;->requestFocus()Z
    iget-object v2, v0, Lhf/l0;->a2:Landroid/view/inputmethod/InputMethodManager;
    const/4 v3, 0x0
    invoke-virtual {v2, v1, v3}, Landroid/view/inputmethod/InputMethodManager;->showSoftInput(Landroid/view/View;I)Z
    return-void

    :hide
    iget-object v1, v0, Lhf/l0;->c2:Lhf/k0;
    instance-of v2, v1, Ldw/filemanager/ui/filechooser/PickerFilterListener;
    if-eqz v2, :simple_hide
    check-cast v1, Ldw/filemanager/ui/filechooser/PickerFilterListener;
    invoke-virtual {v1}, Ldw/filemanager/ui/filechooser/PickerFilterListener;->close()V
    return-void
    :simple_hide
    const/16 v1, 0x8
    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V
    :done
    return-void
.end method
'''

PICKER_FILTER_LISTENER=r'''.class public final Ldw/filemanager/ui/filechooser/PickerFilterListener;
.super Ljava/lang/Object;
.source "DWPickerPanel"

.implements Lhf/k0;

.field private final activity:Ldw/filemanager/ui/filechooser/ChooserActivity;

.method public constructor <init>(Ldw/filemanager/ui/filechooser/ChooserActivity;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/ui/filechooser/PickerFilterListener;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    return-void
.end method

.method public update(Ljava/lang/String;Lhf/n;)V
    .locals 3
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerFilterListener;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iget-object v0, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v0, :done
    iget-object v1, v0, Leg/g;->Z1:Lhf/j0;
    if-eqz v1, :done
    iget-object v1, v1, Lhf/j0;->f:Lhf/g0;
    invoke-virtual {v1, p1, p2}, Lhf/g0;->j(Ljava/lang/String;Lhf/n;)V
    :done
    return-void
.end method

.method public close()V
    .locals 5
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerFilterListener;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iget-object v0, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->p2:Lhf/l0;
    if-eqz v0, :done
    iget-object v1, v0, Lhf/l0;->X1:Landroid/widget/EditText;
    const-string v2, ""
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    iget-object v2, v0, Lhf/l0;->a2:Landroid/view/inputmethod/InputMethodManager;
    invoke-virtual {v0}, Landroid/view/View;->getWindowToken()Landroid/os/IBinder;
    move-result-object v3
    const/4 v4, 0x0
    invoke-virtual {v2, v3, v4}, Landroid/view/inputmethod/InputMethodManager;->hideSoftInputFromWindow(Landroid/os/IBinder;I)Z
    const/16 v2, 0x8
    invoke-virtual {v0, v2}, Landroid/view/View;->setVisibility(I)V
    :done
    return-void
.end method
'''

PICKER_DISPLAY_ACTION=r'''.class public final Ldw/filemanager/ui/filechooser/PickerDisplayAction;
.super Ljava/lang/Object;
.source "DWPickerPanel"

.implements Lyg/b;

.field private final activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
.field private final mode:Lmb/m;

.method public constructor <init>(Ldw/filemanager/ui/filechooser/ChooserActivity;Lmb/m;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/ui/filechooser/PickerDisplayAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iput-object p2, p0, Ldw/filemanager/ui/filechooser/PickerDisplayAction;->mode:Lmb/m;
    return-void
.end method

.method public e(Lyg/c;)V
    .locals 2
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerDisplayAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iget-object v1, p0, Ldw/filemanager/ui/filechooser/PickerDisplayAction;->mode:Lmb/m;
    invoke-static {v0, v1}, Ldw/filemanager/ui/filechooser/PickerPanel;->setViewMode(Ldw/filemanager/ui/filechooser/ChooserActivity;Lmb/m;)V
    return-void
.end method
'''

PICKER_PANEL_ACTION=r'''.class public final Ldw/filemanager/ui/filechooser/PickerPanelAction;
.super Ljava/lang/Object;
.source "DWPickerPanel"

.implements Lyg/b;

.field private final activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
.field private final action:I

.method public constructor <init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/ui/filechooser/PickerPanelAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iput p2, p0, Ldw/filemanager/ui/filechooser/PickerPanelAction;->action:I
    return-void
.end method

.method public e(Lyg/c;)V
    .locals 6
    iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerPanelAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
    iget v1, p0, Ldw/filemanager/ui/filechooser/PickerPanelAction;->action:I
    packed-switch v1, :pswitch_data_0
    return-void

    :pswitch_0
    iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v1, :done
    invoke-virtual {v1}, Leg/g;->a()V
    goto :done

    :pswitch_1
    invoke-static {v0}, Ldw/filemanager/ui/filechooser/PickerSort;->saveForFolder(Landroid/content/Context;)Z
    iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v1, :done
    invoke-virtual {v1}, Leg/g;->a()V
    goto :done

    :pswitch_2
    iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v1, :search_unavailable
    invoke-virtual {v1}, Leg/g;->getCollection()Lkh/d;
    move-result-object v2
    if-eqz v2, :search_unavailable
    invoke-interface {v2}, Lkh/j;->e()Ldw/filemanager/xf/dir/DirectoryCatalog;
    move-result-object v2
    instance-of v3, v2, Lnh/a;
    if-eqz v3, :search_unavailable
    invoke-virtual {v1}, Leg/g;->getPath()Lhh/f;
    move-result-object v2
    if-eqz v2, :search_unavailable
    new-instance v3, Lhh/f;
    const/4 v4, 0x1
    new-array v4, v4, [Ljava/lang/Object;
    sget-object v5, Ljb/d;->p:Ldw/filemanager/xf/IdCatalog;
    const/4 p1, 0x0
    aput-object v5, v4, p1
    invoke-direct {v3, v2, v4}, Lhh/f;-><init>(Lhh/f;[Ljava/lang/Object;)V
    invoke-virtual {v1, v3}, Leg/g;->setPath(Lhh/f;)V
    goto :done

    :search_unavailable
    const-string v1, "Search is not available in this location."
    const/4 v2, 0x0
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    goto :done

    :pswitch_3
    invoke-static {v0}, Ldw/filemanager/ui/filechooser/PickerPanel;->toggleFilter(Ldw/filemanager/ui/filechooser/ChooserActivity;)V

    :done
    return-void

    :pswitch_data_0
    .packed-switch 0x0
        :pswitch_0
        :pswitch_1
        :pswitch_2
        :pswitch_3
    .end packed-switch
.end method
'''

PICKER_PANEL_MENU=r'''.class public final Ldw/filemanager/ui/filechooser/PickerPanelMenu;
.super Ljava/lang/Object;
.source "DWPickerPanel"

.method private static displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;
    .locals 6
    iget-object v0, p0, Laf/c;->Z:Lef/g;
    iget-boolean v0, v0, Lef/g;->j:Z
    invoke-static {p1, p4, v0}, Ldw/filemanager/ui/res/ActionIcons;->b(Landroid/content/res/Resources;Ljava/lang/String;I)Lsa/h;
    move-result-object v0
    invoke-virtual {p1, p3}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v1
    new-instance v2, Ldw/filemanager/ui/filechooser/PickerDisplayAction;
    invoke-direct {v2, p0, p2}, Ldw/filemanager/ui/filechooser/PickerDisplayAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;Lmb/m;)V
    new-instance v3, Lyg/s;
    invoke-direct {v3, v1, v0, v2}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    const/4 v0, 0x1
    iput-boolean v0, v3, Lyg/s;->l:Z
    const-string v1, "displayMode"
    iput-object v1, v3, Lyg/s;->m:Ljava/lang/String;
    if-ne p2, p5, :not_selected
    goto :selected_done
    :not_selected
    const/4 v0, 0x0
    :selected_done
    iput-boolean v0, v3, Lyg/s;->k:Z
    return-object v3
.end method

.method public static add(Ldw/filemanager/ui/filechooser/ChooserActivity;Lyg/r;)V
    .locals 10
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v0

    # Refresh is useful everywhere in a chooser.
    new-instance v1, Ldw/filemanager/ui/filechooser/PickerPanelAction;
    const/4 v2, 0x0
    invoke-direct {v1, p0, v2}, Ldw/filemanager/ui/filechooser/PickerPanelAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    iget-object v2, p0, Laf/c;->Z:Lef/g;
    iget-boolean v2, v2, Lef/g;->j:Z
    const-string v3, "action_refresh"
    invoke-static {v0, v3, v2}, Ldw/filemanager/ui/res/ActionIcons;->b(Landroid/content/res/Resources;Ljava/lang/String;I)Lsa/h;
    move-result-object v2
    new-instance v3, Lyg/p;
    const-string v4, "Refresh"
    invoke-direct {v3, v4, v2, v1}, Lyg/p;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v3}, Lyg/r;->d(Lyg/u;)V

    # DISPLAY AS — same native tile model and icon family as the main DW panel.
    new-instance v1, Lyg/q;
    const v2, 0x7f1000ea
    invoke-virtual {v0, v2}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v2
    invoke-direct {v1, v2}, Lyg/q;-><init>(Ljava/lang/String;)V
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->viewMode(Landroid/content/Context;)Lmb/m;
    move-result-object v9

    sget-object v2, Lmb/m;->Z:Lmb/m;
    const v3, 0x7f100063
    const-string v4, "action_view_icon"
    move-object v1, p0
    move-object v5, v9
    invoke-static/range {v1 .. v5}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;
    move-result-object v1
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V
    new-instance v1, Lyg/v;
    invoke-direct {v1}, Ljava/lang/Object;-><init>()V
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V

    sget-object v2, Lmb/m;->Y:Lmb/m;
    const v3, 0x7f100061
    const-string v4, "action_view_grid"
    move-object v1, p0
    move-object v5, v9
    invoke-static/range {v1 .. v5}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;
    move-result-object v1
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V

    sget-object v2, Lmb/m;->X:Lmb/m;
    const v3, 0x7f100064
    const-string v4, "action_view_list"
    move-object v1, p0
    move-object v5, v9
    invoke-static/range {v1 .. v5}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;
    move-result-object v1
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V
    new-instance v1, Lyg/v;
    invoke-direct {v1}, Ljava/lang/Object;-><init>()V
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V

    sget-object v2, Lmb/m;->X1:Lmb/m;
    const v3, 0x7f100067
    const-string v4, "action_pie"
    move-object v1, p0
    move-object v5, v9
    invoke-static/range {v1 .. v5}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;
    move-result-object v1
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V

    # Native SORT BY tiles plus folders-first control.
    invoke-static {p0, p1}, Ldw/filemanager/ui/filechooser/PickerSortMenu;->add(Ldw/filemanager/ui/filechooser/ChooserActivity;Lyg/r;)V

    # Save/clear the picker-only sort override for the current folder.
    new-instance v1, Ldw/filemanager/ui/filechooser/PickerPanelAction;
    const/4 v2, 0x1
    invoke-direct {v1, p0, v2}, Ldw/filemanager/ui/filechooser/PickerPanelAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    iget-object v2, p0, Laf/c;->Z:Lef/g;
    iget-boolean v2, v2, Lef/g;->j:Z
    const-string v3, "action_check"
    invoke-static {v0, v3, v2}, Ldw/filemanager/ui/res/ActionIcons;->b(Landroid/content/res/Resources;Ljava/lang/String;I)Lsa/h;
    move-result-object v2
    const v3, 0x7f10007b
    invoke-virtual {v0, v3}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v3
    new-instance v4, Lyg/p;
    invoke-direct {v4, v3, v2, v1}, Lyg/p;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v4}, Lyg/r;->d(Lyg/u;)V

    new-instance v1, Lyg/q;
    const/4 v2, 0x0
    invoke-direct {v1, v2}, Lyg/q;-><init>(Ljava/lang/String;)V
    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V

    # Persisted picker-only Show Hidden control.
    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->hidden(Landroid/content/Context;)Z
    move-result v5
    iget-object v1, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
    if-eqz v1, :hidden_menu
    invoke-virtual {v1, v5}, Leg/g;->setDisplayHidden(Z)V
    :hidden_menu
    const v1, 0x7f100083
    invoke-virtual {v0, v1}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v1
    iget-object v2, p0, Laf/c;->Z:Lef/g;
    iget-boolean v2, v2, Lef/g;->j:Z
    const-string v3, "action_show_hidden"
    invoke-static {v0, v3, v2}, Ldw/filemanager/ui/res/ActionIcons;->b(Landroid/content/res/Resources;Ljava/lang/String;I)Lsa/h;
    move-result-object v2
    new-instance v3, Lnf/a;
    const/4 v4, 0x2
    invoke-direct {v3, p0, v4}, Lnf/a;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    new-instance v4, Lyg/s;
    invoke-direct {v4, v1, v2, v3}, Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    const/4 v1, 0x1
    iput-boolean v1, v4, Lyg/s;->l:Z
    iput-boolean v5, v4, Lyg/s;->k:Z
    iput-object v4, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->m2:Lyg/s;
    invoke-virtual {p1, v4}, Lyg/r;->d(Lyg/u;)V

    # Search — uses DW's own searchable-catalog path when supported.
    new-instance v1, Ldw/filemanager/ui/filechooser/PickerPanelAction;
    const/4 v2, 0x2
    invoke-direct {v1, p0, v2}, Ldw/filemanager/ui/filechooser/PickerPanelAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    iget-object v2, p0, Laf/c;->Z:Lef/g;
    iget-boolean v2, v2, Lef/g;->j:Z
    const-string v3, "action_search"
    invoke-static {v0, v3, v2}, Ldw/filemanager/ui/res/ActionIcons;->b(Landroid/content/res/Resources;Ljava/lang/String;I)Lsa/h;
    move-result-object v2
    const v3, 0x7f1000be
    invoke-virtual {v0, v3}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v3
    new-instance v4, Lyg/p;
    invoke-direct {v4, v3, v2, v1}, Lyg/p;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v4}, Lyg/r;->d(Lyg/u;)V

    # Filter — reuses DW's native hf/l0 filter bar and hf/g0 filter engine.
    new-instance v1, Ldw/filemanager/ui/filechooser/PickerPanelAction;
    const/4 v2, 0x3
    invoke-direct {v1, p0, v2}, Ldw/filemanager/ui/filechooser/PickerPanelAction;-><init>(Ldw/filemanager/ui/filechooser/ChooserActivity;I)V
    iget-object v2, p0, Laf/c;->Z:Lef/g;
    iget-boolean v2, v2, Lef/g;->j:Z
    const-string v3, "action_filter"
    invoke-static {v0, v3, v2}, Ldw/filemanager/ui/res/ActionIcons;->b(Landroid/content/res/Resources;Ljava/lang/String;I)Lsa/h;
    move-result-object v2
    const v3, 0x7f100078
    invoke-virtual {v0, v3}, Landroid/content/res/Resources;->getString(I)Ljava/lang/String;
    move-result-object v3
    new-instance v4, Lyg/p;
    invoke-direct {v4, v3, v2, v1}, Lyg/p;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V
    invoke-virtual {p1, v4}, Lyg/r;->d(Lyg/u;)V
    return-void
.end method
'''

def replace_method(text, signature_prefix, replacement):
    pat=re.compile(r'\.method '+re.escape(signature_prefix)+r'.*?\.end method',re.S)
    text,n=pat.subn(replacement,text,count=1)
    if n!=1: raise RuntimeError('method not found: '+signature_prefix)
    return text

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'; d=sm/'dw/filemanager/ui/filechooser'

    # Upgrade picker sort persistence with a picker-only per-folder override.
    ps=d/'PickerSort.smali'; t=ps.read_text()
    t=replace_method(t,'public static sort(Landroid/content/Context;[Lkh/j;)V',PICKER_SORT_METHODS['sort'])
    t=replace_method(t,'public static set(Landroid/content/Context;IZ)V',PICKER_SORT_METHODS['set'])
    t=replace_method(t,'public static mode(Landroid/content/Context;)Lkh/o;',PICKER_SORT_METHODS['mode'])
    t=replace_method(t,'public static descending(Landroid/content/Context;)Z',PICKER_SORT_METHODS['descending'])
    if 'folderBase(Landroid/content/Context;)Ljava/lang/String;' not in t:
        t=t.rstrip()+"\n"+PICKER_SORT_EXTRA+"\n"
    ps.write_text(t)

    (d/'PickerPanel.smali').write_text(PICKER_PANEL)
    (d/'PickerFilterListener.smali').write_text(PICKER_FILTER_LISTENER)
    (d/'PickerDisplayAction.smali').write_text(PICKER_DISPLAY_ACTION)
    (d/'PickerPanelAction.smali').write_text(PICKER_PANEL_ACTION)
    (d/'PickerPanelMenu.smali').write_text(PICKER_PANEL_MENU)

    # ChooserActivity: add filter-bar field and replace the old Show Hidden + sort-only
    # block with the full native panel builder.
    chooser=d/'ChooserActivity.smali'; ct=chooser.read_text()
    if '.field public p2:Lhf/l0;' not in ct:
        ct=ct.replace('.field public m2:Lyg/s;\n','.field public m2:Lyg/s;\n\n.field public p2:Lhf/l0;\n',1)
    marker='invoke-static {p0, v3}, Ldw/filemanager/ui/filechooser/PickerSortMenu;->add(Ldw/filemanager/ui/filechooser/ChooserActivity;Lyg/r;)V'
    mi=ct.find(marker)
    if mi<0: raise RuntimeError('Stage13c sort menu hook missing')
    hidden_const=ct.rfind('    const v4, 0x7f100083',0,mi)
    if hidden_const<0: raise RuntimeError('Chooser Show Hidden block missing')
    start=ct.rfind('    new-instance v2, Lyg/s;',0,hidden_const)
    if start<0: raise RuntimeError('Chooser Show Hidden block start missing')
    end=ct.find('\n',mi+len(marker))
    if end<0: end=len(ct)
    replacement='    # DW Stage13d: full native picker overflow panel.\n    invoke-static {p0, v3}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->add(Ldw/filemanager/ui/filechooser/ChooserActivity;Lyg/r;)V'
    ct=ct[:start]+replacement+ct[end:]
    chooser.write_text(ct)

    # Apply picker-only display mode every time the chooser loader is refreshed.
    eg=sm/'eg/g.smali'; et=eg.read_text()
    anchor='''    iget-object v0, p0, Leg/g;->Z1:Lhf/j0;\n\n    .line 105\n    .line 106\n    iget-object v1, p0, Leg/g;->k2:Ljava/util/Set;\n\n    .line 107\n    .line 108\n    invoke-virtual {v0, v1}, Lhf/j0;->setDisplayMediaTypes(Ljava/util/Collection;)V'''
    inject=anchor+'''\n\n    # DW Stage13d: restore picker-only display mode.\n    iget-object v0, p0, Leg/g;->Z1:Lhf/j0;\n    iget-object v1, v0, Lhf/j0;->f:Lhf/g0;\n    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;\n    move-result-object v0\n    invoke-static {v0, v1}, Ldw/filemanager/ui/filechooser/PickerPanel;->applyViewMode(Landroid/content/Context;Lhf/g0;)V'''
    if et.count(anchor)!=1: raise RuntimeError(f'eg/g display hook anchor count={et.count(anchor)}')
    et=et.replace(anchor,inject,1); eg.write_text(et)

    # Persist the existing chooser Show Hidden toggle.
    nf=sm/'nf/a.smali'; nt=nf.read_text()
    hidden_anchor='    invoke-virtual {p1, v1}, Leg/g;->setDisplayHidden(Z)V'
    hidden_new=hidden_anchor+'\n\n    invoke-static {v0, v1}, Ldw/filemanager/ui/filechooser/PickerPanel;->setHidden(Landroid/content/Context;Z)V'
    if nt.count(hidden_anchor)!=1: raise RuntimeError(f'nf/a hidden anchor count={nt.count(hidden_anchor)}')
    nt=nt.replace(hidden_anchor,hidden_new,1); nf.write_text(nt)

    # Reuse DW's native filter bar in ChooserActivity by adding a Laf/c overload. The
    # original body only requires Context + Laf/c APIs, so this is type-correct.
    l0=sm/'hf/l0.smali'; lt=l0.read_text()
    if '.method public constructor <init>(Laf/c;)V' not in lt:
        pat=re.compile(r'(\.method public constructor <init>\(Ldw/filemanager/ui/content/k;\)V.*?\.end method)',re.S)
        m=pat.search(lt)
        if not m: raise RuntimeError('hf/l0 original constructor missing')
        clone=m.group(1).replace('.method public constructor <init>(Ldw/filemanager/ui/content/k;)V','.method public constructor <init>(Laf/c;)V',1)
        lt=lt[:m.end()]+"\n\n"+clone+lt[m.end():]
    l0.write_text(lt)

    # hf/l0's shared TextWatcher historically hard-casts its marker listener to lf/g.
    # Add a narrow branch for the picker listener; preserve the original path unchanged.
    ba=sm/'be/a0.smali'; bt=ba.read_text()
    old='''    iget-object p1, p2, Lhf/l0;->c2:Lhf/k0;\n\n    .line 38\n    .line 39\n    iget-object p2, p2, Lhf/l0;->f:Lhf/n;\n\n    .line 40\n    .line 41\n    check-cast p1, Llf/g;\n\n    .line 42\n    .line 43\n    iget-object p1, p1, Llf/g;->a:Llf/s;\n\n    .line 44\n    .line 45\n    invoke-virtual {p1, p3, p2}, Llf/s;->W0(Ljava/lang/String;Lhf/n;)V'''
    new='''    iget-object p1, p2, Lhf/l0;->c2:Lhf/k0;\n\n    .line 38\n    .line 39\n    iget-object p2, p2, Lhf/l0;->f:Lhf/n;\n\n    instance-of p4, p1, Ldw/filemanager/ui/filechooser/PickerFilterListener;\n    if-eqz p4, :dw_filter_original_listener\n    check-cast p1, Ldw/filemanager/ui/filechooser/PickerFilterListener;\n    invoke-virtual {p1, p3, p2}, Ldw/filemanager/ui/filechooser/PickerFilterListener;->update(Ljava/lang/String;Lhf/n;)V\n    goto :cond_2\n\n    :dw_filter_original_listener\n    .line 40\n    .line 41\n    check-cast p1, Llf/g;\n\n    .line 42\n    .line 43\n    iget-object p1, p1, Llf/g;->a:Llf/s;\n\n    .line 44\n    .line 45\n    invoke-virtual {p1, p3, p2}, Llf/s;->W0(Ljava/lang/String;Lhf/n;)V'''
    if bt.count(old)!=1: raise RuntimeError(f'be/a0 filter listener anchor count={bt.count(old)}')
    bt=bt.replace(old,new,1); ba.write_text(bt)

    ag=sm/'af/g.smali'; at=ag.read_text()
    old='''    if-eqz v0, :cond_b\n\n    .line 341\n    .line 342\n    check-cast v0, Llf/g;\n\n    .line 343\n    .line 344\n    iget-object v0, v0, Llf/g;->a:Llf/s;\n\n    .line 345\n    .line 346\n    invoke-virtual {v0}, Llf/s;->V0()V'''
    new='''    if-eqz v0, :cond_b\n\n    instance-of v2, v0, Ldw/filemanager/ui/filechooser/PickerFilterListener;\n    if-eqz v2, :dw_filter_close_original\n    check-cast v0, Ldw/filemanager/ui/filechooser/PickerFilterListener;\n    invoke-virtual {v0}, Ldw/filemanager/ui/filechooser/PickerFilterListener;->close()V\n    return-void\n\n    :dw_filter_close_original\n    .line 341\n    .line 342\n    check-cast v0, Llf/g;\n\n    .line 343\n    .line 344\n    iget-object v0, v0, Llf/g;->a:Llf/s;\n\n    .line 345\n    .line 346\n    invoke-virtual {v0}, Llf/s;->V0()V'''
    if at.count(old)!=1: raise RuntimeError(f'af/g filter close anchor count={at.count(old)}')
    at=at.replace(old,new,1); ag.write_text(at)

    # Install over the user's current 9109009 build; 9109010 was an undelivered intermediate.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    # Durable guards.
    final=chooser.read_text(); menu=(d/'PickerPanelMenu.smali').read_text(); pst=ps.read_text()
    if 'PickerPanelMenu;->add' not in final: raise RuntimeError('full picker panel hook missing')
    if 'PickerSortMenu;->add' in final: raise RuntimeError('old direct sort-only hook survived')
    for tok in ('DISPLAY AS','PickerSortMenu;->add','action_view_icon','action_view_grid','action_view_list','action_pie','action_check','action_show_hidden','action_search','action_filter','Refresh'):
        if tok not in menu: raise RuntimeError('full picker panel missing '+tok)
    for tok in ('dw.picker.folder_sort.','saveForFolder(Landroid/content/Context;)Z','isSavedForFolder(Landroid/content/Context;)Z'):
        if tok not in pst: raise RuntimeError('picker folder sort persistence missing '+tok)
    if 'applyViewMode(Landroid/content/Context;Lhf/g0;)V' not in eg.read_text(): raise RuntimeError('picker display mode apply hook missing')
    if '<init>(Laf/c;)V' not in l0.read_text(): raise RuntimeError('native filter bar Laf/c overload missing')
    if 'PickerFilterListener' not in ba.read_text() or 'PickerFilterListener' not in ag.read_text(): raise RuntimeError('native filter listener bridge missing')

    print('stage13d full native DW picker panel installed: Refresh, Display As, Sort By, Save for Folder, Folders First, Show Hidden, Search, Filter; vc='+VC)

if __name__=='__main__': main()
