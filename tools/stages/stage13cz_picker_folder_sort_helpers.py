#!/usr/bin/env python3
from pathlib import Path
import argparse

EXTRA=r'''
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

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    p=a.decoded/'smali/dw/filemanager/ui/filechooser/PickerSort.smali'
    if not p.exists(): raise RuntimeError('PickerSort.smali missing before folder helper stage')
    t=p.read_text()
    if '.method private static folderBase(Landroid/content/Context;)Ljava/lang/String;' not in t:
        t=t.rstrip()+"\n"+EXTRA+"\n"
        p.write_text(t)
    t=p.read_text()
    for token in ('.method private static folderBase(Landroid/content/Context;)Ljava/lang/String;','dw.picker.folder_sort.','.method public static saveForFolder(Landroid/content/Context;)Z','.method public static isSavedForFolder(Landroid/content/Context;)Z'):
        if token not in t: raise RuntimeError('picker folder helper missing: '+token)
    print('stage13cz installed picker-only per-folder sort persistence helpers before full panel stage')

if __name__=='__main__': main()
