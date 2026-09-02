#!/usr/bin/env python3
from pathlib import Path
import argparse,re,xml.etree.ElementTree as ET

VC='9109005'

HELPER=r'''.class public final Ldw/filemanager/open/FileAssociations;
.super Ljava/lang/Object;
.source "DWFileAssociations"

.method private static key(Lkh/e;)Ljava/lang/String;
    .locals 5

    invoke-interface {p0}, Lkh/j;->getName()Ljava/lang/String;
    move-result-object v0

    const-string v1, "dw.fileassoc.__no_extension__"
    if-eqz v0, :ret_none

    const/16 v2, 0x2e
    invoke-virtual {v0, v2}, Ljava/lang/String;->lastIndexOf(I)I
    move-result v2
    if-lez v2, :ret_none

    invoke-virtual {v0}, Ljava/lang/String;->length()I
    move-result v3
    add-int/lit8 v4, v2, 0x1
    if-ge v4, v3, :ret_none

    invoke-virtual {v0, v4}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object v0
    sget-object v2, Ljava/util/Locale;->ROOT:Ljava/util/Locale;
    invoke-virtual {v0, v2}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;
    move-result-object v0

    new-instance v2, Ljava/lang/StringBuilder;
    const-string v3, "dw.fileassoc."
    invoke-direct {v2, v3}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v1

    :ret_none
    return-object v1
.end method

.method private static prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    .locals 1
    invoke-static {p0}, Lmb/l;->d(Landroid/content/Context;)Lmb/l;
    move-result-object v0
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;
    return-object v0
.end method

.method private static component(Landroid/content/pm/ResolveInfo;)Ljava/lang/String;
    .locals 3
    if-eqz p0, :none
    iget-object v0, p0, Landroid/content/pm/ResolveInfo;->activityInfo:Landroid/content/pm/ActivityInfo;
    if-eqz v0, :none
    iget-object v1, v0, Landroid/content/pm/ActivityInfo;->packageName:Ljava/lang/String;
    iget-object v0, v0, Landroid/content/pm/ActivityInfo;->name:Ljava/lang/String;
    if-eqz v1, :none
    if-eqz v0, :none
    new-instance v2, Landroid/content/ComponentName;
    invoke-direct {v2, v1, v0}, Landroid/content/ComponentName;-><init>(Ljava/lang/String;Ljava/lang/String;)V
    invoke-virtual {v2}, Landroid/content/ComponentName;->flattenToString()Ljava/lang/String;
    move-result-object v0
    return-object v0
    :none
    const/4 v0, 0x0
    return-object v0
.end method

.method public static get(Landroid/content/Context;Lkh/e;)Ljava/lang/String;
    .locals 3
    invoke-static {p0}, Ldw/filemanager/open/FileAssociations;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0
    invoke-static {p1}, Ldw/filemanager/open/FileAssociations;->key(Lkh/e;)Ljava/lang/String;
    move-result-object v1
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static has(Landroid/content/Context;Lkh/e;)Z
    .locals 1
    invoke-static {p0, p1}, Ldw/filemanager/open/FileAssociations;->get(Landroid/content/Context;Lkh/e;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :no
    const/4 v0, 0x1
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static matches(Ljava/lang/String;Landroid/content/pm/ResolveInfo;)Z
    .locals 1
    if-eqz p0, :no
    invoke-static {p1}, Ldw/filemanager/open/FileAssociations;->component(Landroid/content/pm/ResolveInfo;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :no
    invoke-virtual {p0, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static toggle(Landroid/content/Context;Lkh/e;Landroid/content/pm/ResolveInfo;)Z
    .locals 5
    invoke-static {p2}, Ldw/filemanager/open/FileAssociations;->component(Landroid/content/pm/ResolveInfo;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :fail

    invoke-static {p1}, Ldw/filemanager/open/FileAssociations;->key(Lkh/e;)Ljava/lang/String;
    move-result-object v1
    invoke-static {p0}, Ldw/filemanager/open/FileAssociations;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v2
    const/4 v3, 0x0
    invoke-interface {v2, v1, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3

    if-eqz v3, :save
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v4
    if-eqz v4, :save

    invoke-interface {v2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0, v1}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    const/4 v0, 0x0
    return v0

    :save
    invoke-interface {v2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v2
    invoke-interface {v2, v1, v0}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
    const/4 v0, 0x1
    return v0

    :fail
    const/4 v0, 0x0
    return v0
.end method
'''

LONGCLICK=r'''.class public final Ldw/filemanager/open/AssociationLongClick;
.super Ljava/lang/Object;
.source "DWFileAssociations"

.implements Landroid/view/View$OnLongClickListener;

.field private final dialog:Lhf/y0;

.method public constructor <init>(Lhf/y0;)V
    .locals 0
    iput-object p1, p0, Ldw/filemanager/open/AssociationLongClick;->dialog:Lhf/y0;
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public onLongClick(Landroid/view/View;)Z
    .locals 6

    invoke-virtual {p1}, Landroid/view/View;->getTag()Ljava/lang/Object;
    move-result-object v0
    instance-of v1, v0, Lqe/b;
    if-eqz v1, :no
    check-cast v0, Lqe/b;
    iget-object v0, v0, Lqe/b;->a:Landroid/content/pm/ResolveInfo;
    if-eqz v0, :no

    iget-object v1, p0, Ldw/filemanager/open/AssociationLongClick;->dialog:Lhf/y0;
    invoke-virtual {v1}, Landroid/app/Dialog;->getContext()Landroid/content/Context;
    move-result-object v2
    iget-object v3, v1, Lhf/y0;->X:Lkh/e;
    invoke-static {v2, v3, v0}, Ldw/filemanager/open/FileAssociations;->toggle(Landroid/content/Context;Lkh/e;Landroid/content/pm/ResolveInfo;)Z
    move-result v0

    if-eqz v0, :cleared
    const-string v4, "Preferred app saved for this file type."
    goto :toast

    :cleared
    const-string v4, "Preferred app cleared for this file type."

    :toast
    const/4 v5, 0x0
    invoke-static {v2, v4, v5}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v2
    invoke-virtual {v2}, Landroid/widget/Toast;->show()V
    const/4 v0, 0x1
    return v0

    :no
    const/4 v0, 0x0
    return v0
.end method
'''

def patch_once(text, old, new, label):
    n=text.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected exactly one match, got {n}')
    return text.replace(old,new,1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    sm=root/'smali'

    # New association logic: exact lower-case extension -> explicit Android component.
    d=sm/'dw/filemanager/open'; d.mkdir(parents=True,exist_ok=True)
    (d/'FileAssociations.smali').write_text(HELPER)
    (d/'AssociationLongClick.smali').write_text(LONGCLICK)

    # Intercept normal file opening before any built-in viewer route. With no saved
    # association this is a single fast SharedPreferences lookup and original behavior continues.
    p=sm/'hf/b0.smali'; t=p.read_text()
    marker='''    iget-object v6, v6, Lmb/l;->b:Landroid/content/SharedPreferences;\n\n    .line 20\n    .line 21\n    instance-of v7, v1, Lkh/m0;'''
    repl='''    iget-object v6, v6, Lmb/l;->b:Landroid/content/SharedPreferences;\n\n    # DW Stage12: exact-extension preferred app override before internal routing.\n    invoke-static {v0, v1}, Ldw/filemanager/open/FileAssociations;->has(Landroid/content/Context;Lkh/e;)Z\n    move-result v7\n    if-eqz v7, :dw_fileassoc_continue\n    invoke-static {v0, v1, p2}, Lhf/y0;->k(Landroid/content/Context;Lkh/e;Llf/b;)V\n    return-void\n\n    :dw_fileassoc_continue\n    .line 20\n    .line 21\n    instance-of v7, v1, Lkh/m0;'''
    t=patch_once(t,marker,repl,'hf/b0 normal-open hook'); p.write_text(t)

    # Extend the existing Open With dialog rather than creating a second chooser.
    p=sm/'hf/y0.smali'; t=p.read_text()
    field_marker='.field public final i2:Lhf/x0;\n'
    fields='.field public final i2:Lhf/x0;\n\n# Stage12 preferred-app auto-open state. Null for explicit Open With dialogs.\n.field public j2:Ljava/lang/String;\n\n.field public k2:Z\n'
    t=patch_once(t,field_marker,fields,'hf/y0 fields')

    # New auto-association entry point. Existing j() remains the explicit chooser and never auto-opens.
    j_end='''.method public static j(Landroid/content/Context;Lkh/e;Llf/b;)V\n    .locals 2\n\n    .line 1\n    new-instance v0, Lhf/y0;\n\n    .line 2\n    .line 3\n    const/4 v1, 0x1\n\n    .line 4\n    invoke-direct {v0, p0, v1, p1, p2}, Lhf/y0;-><init>(Landroid/content/Context;ILkh/e;Llf/b;)V\n\n    .line 5\n    .line 6\n    .line 7\n    new-instance p0, Lhf/s0;\n\n    .line 8\n    .line 9\n    const/4 p1, 0x0\n\n    .line 10\n    invoke-direct {p0, v0, p1}, Lhf/s0;-><init>(Lhf/y0;I)V\n\n    .line 11\n    .line 12\n    .line 13\n    const-wide/16 p1, 0x64\n\n    .line 14\n    .line 15\n    iget-object v0, v0, Lhf/y0;->Y1:Landroid/os/Handler;\n\n    .line 16\n    .line 17\n    invoke-virtual {v0, p0, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z\n\n    .line 18\n    .line 19\n    .line 20\n    return-void\n.end method\n'''
    auto=j_end+'''\n.method public static k(Landroid/content/Context;Lkh/e;Llf/b;)V\n    .locals 4\n\n    new-instance v0, Lhf/y0;\n    const/4 v1, 0x1\n    invoke-direct {v0, p0, v1, p1, p2}, Lhf/y0;-><init>(Landroid/content/Context;ILkh/e;Llf/b;)V\n\n    invoke-static {p0, p1}, Ldw/filemanager/open/FileAssociations;->get(Landroid/content/Context;Lkh/e;)Ljava/lang/String;\n    move-result-object v1\n    iput-object v1, v0, Lhf/y0;->j2:Ljava/lang/String;\n\n    new-instance v1, Lhf/s0;\n    const/4 p1, 0x0\n    invoke-direct {v1, v0, p1}, Lhf/s0;-><init>(Lhf/y0;I)V\n    const-wide/16 v2, 0x64\n    iget-object p0, v0, Lhf/y0;->Y1:Landroid/os/Handler;\n    invoke-virtual {p0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z\n    return-void\n.end method\n'''
    t=patch_once(t,j_end,auto,'hf/y0 auto-open entry')

    click='''    invoke-virtual {v1, p3}, Landroid/view/View;->setTag(Ljava/lang/Object;)V\n\n    .line 69\n    .line 70\n    .line 71\n    invoke-virtual {v1, p4}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V\n\n    .line 72\n    .line 73\n    .line 74\n    iget-object p1, p0, Lhf/y0;->d2:Lgh/g;\n\n    .line 75\n    .line 76\n    invoke-virtual {p1, v1}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V\n\n    .line 77\n    .line 78\n    .line 79\n    return-void'''
    click_new='''    invoke-virtual {v1, p3}, Landroid/view/View;->setTag(Ljava/lang/Object;)V\n\n    .line 69\n    .line 70\n    .line 71\n    invoke-virtual {v1, p4}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V\n\n    # External application rows: long-press toggles preferred app for this exact extension.\n    if-eqz p3, :dw_assoc_no_long_press\n    new-instance v2, Ldw/filemanager/open/AssociationLongClick;\n    invoke-direct {v2, p0}, Ldw/filemanager/open/AssociationLongClick;-><init>(Lhf/y0;)V\n    invoke-virtual {v1, v2}, Landroid/view/View;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V\n    :dw_assoc_no_long_press\n\n    .line 72\n    .line 73\n    .line 74\n    iget-object p1, p0, Lhf/y0;->d2:Lgh/g;\n\n    .line 75\n    .line 76\n    invoke-virtual {p1, v1}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V\n\n    # Auto-open only when invoked through k(); explicit Open With j() leaves j2 null.\n    if-eqz p3, :dw_assoc_row_done\n    iget-object v2, p0, Lhf/y0;->j2:Ljava/lang/String;\n    if-eqz v2, :dw_assoc_row_done\n    iget-object v3, p3, Lqe/b;->a:Landroid/content/pm/ResolveInfo;\n    invoke-static {v2, v3}, Ldw/filemanager/open/FileAssociations;->matches(Ljava/lang/String;Landroid/content/pm/ResolveInfo;)Z\n    move-result v2\n    if-eqz v2, :dw_assoc_row_done\n    const/4 v2, 0x1\n    iput-boolean v2, p0, Lhf/y0;->k2:Z\n    const/4 v2, 0x0\n    iput-object v2, p0, Lhf/y0;->j2:Ljava/lang/String;\n    invoke-interface {p4, v1}, Landroid/view/View$OnClickListener;->onClick(Landroid/view/View;)V\n\n    :dw_assoc_row_done\n    .line 77\n    .line 78\n    .line 79\n    return-void'''
    t=patch_once(t,click,click_new,'hf/y0 row association behavior')
    p.write_text(t)

    # Suppress the delayed chooser show if a preferred row was resolved within the 100ms grace period.
    p=sm/'hf/s0.smali'; t=p.read_text()
    show='''    :pswitch_0\n    iget-object v0, p0, Lhf/s0;->i:Lhf/y0;\n\n    .line 41\n    .line 42\n    invoke-virtual {v0}, Ldw/filemanager/ui/widget/g0;->show()V\n\n    .line 43\n    .line 44\n    .line 45\n    return-void'''
    show_new='''    :pswitch_0\n    iget-object v0, p0, Lhf/s0;->i:Lhf/y0;\n\n    # A resolved preferred app should be genuinely one-tap with no chooser flash.\n    iget-boolean v1, v0, Lhf/y0;->k2:Z\n    if-nez v1, :dw_assoc_skip_show\n\n    .line 41\n    .line 42\n    invoke-virtual {v0}, Ldw/filemanager/ui/widget/g0;->show()V\n\n    :dw_assoc_skip_show\n    .line 43\n    .line 44\n    .line 45\n    return-void'''
    t=patch_once(t,show,show_new,'hf/s0 chooser suppression'); p.write_text(t)

    # Explain the control in the existing Open With dialog. Default locale is sufficient fallback.
    strings=root/'res/values/strings.xml'; tree=ET.parse(strings); rr=tree.getroot(); found=False
    for e in rr:
        if e.tag=='string' and e.attrib.get('name')=='open_with_dialog_desc':
            e.text='Select an option to open the file "%s". Long-press an application to set it as the preferred app for this file type; long-press the preferred app again to clear it.'
            found=True; break
    if not found: raise RuntimeError('open_with_dialog_desc not found')
    ET.indent(tree,space='    '); tree.write(strings,encoding='utf-8',xml_declaration=True)

    # Install over the confirmed-working Stage11 v9109004 baseline.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found'); y.write_text(yt)

    # Durable invariants.
    if 'Ldw/filemanager/open/FileAssociations;->has' not in (sm/'hf/b0.smali').read_text(): raise RuntimeError('normal-open association hook missing')
    yy=(sm/'hf/y0.smali').read_text()
    for token in ('Lhf/y0;->k(Landroid/content/Context;Lkh/e;Llf/b;)V','AssociationLongClick','->matches(Ljava/lang/String;Landroid/content/pm/ResolveInfo;)Z','->k2:Z'):
        if token not in yy and token not in (sm/'hf/b0.smali').read_text(): raise RuntimeError('association integration missing '+token)
    if '->toggle(Landroid/content/Context;Lkh/e;Landroid/content/pm/ResolveInfo;)Z' not in (d/'AssociationLongClick.smali').read_text(): raise RuntimeError('association long-press toggle missing')
    if 'dw.fileassoc.' not in (d/'FileAssociations.smali').read_text(): raise RuntimeError('association preference namespace missing')

    print('stage12a file type associations installed: exact extension preferred app, one-tap auto-open, explicit Open With override, long-press set/clear; vc='+VC)

if __name__=='__main__': main()
