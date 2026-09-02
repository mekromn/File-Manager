#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109006'

INTERNAL_METHODS=r'''
.method private static internalTarget(Ljava/lang/String;)Ljava/lang/String;
    .locals 2
    if-eqz p0, :none
    new-instance v0, Ljava/lang/StringBuilder;
    const-string v1, "internal:"
    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
    :none
    const/4 v0, 0x0
    return-object v0
.end method

.method public static matchesInternal(Ljava/lang/String;Ljava/lang/String;)Z
    .locals 1
    if-eqz p0, :no
    invoke-static {p1}, Ldw/filemanager/open/FileAssociations;->internalTarget(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :no
    invoke-virtual {p0, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    return v0
    :no
    const/4 v0, 0x0
    return v0
.end method

.method public static toggleInternal(Landroid/content/Context;Lkh/e;Ljava/lang/String;)Z
    .locals 5
    invoke-static {p2}, Ldw/filemanager/open/FileAssociations;->internalTarget(Ljava/lang/String;)Ljava/lang/String;
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

LONGCLICK=r'''.method public onLongClick(Landroid/view/View;)Z
    .locals 7

    invoke-virtual {p1}, Landroid/view/View;->getTag()Ljava/lang/Object;
    move-result-object v0

    iget-object v1, p0, Ldw/filemanager/open/AssociationLongClick;->dialog:Lhf/y0;
    invoke-virtual {v1}, Landroid/app/Dialog;->getContext()Landroid/content/Context;
    move-result-object v2
    iget-object v3, v1, Lhf/y0;->X:Lkh/e;

    instance-of v4, v0, Lqe/b;
    if-eqz v4, :check_internal
    check-cast v0, Lqe/b;
    iget-object v0, v0, Lqe/b;->a:Landroid/content/pm/ResolveInfo;
    if-eqz v0, :no
    invoke-static {v2, v3, v0}, Ldw/filemanager/open/FileAssociations;->toggle(Landroid/content/Context;Lkh/e;Landroid/content/pm/ResolveInfo;)Z
    move-result v0
    goto :toast_result

    :check_internal
    instance-of v4, v0, Lhf/u0;
    if-eqz v4, :no
    check-cast v0, Lhf/u0;
    iget-object v0, v0, Lhf/u0;->i:Ljava/lang/String;
    if-eqz v0, :no
    invoke-static {v2, v3, v0}, Ldw/filemanager/open/FileAssociations;->toggleInternal(Landroid/content/Context;Lkh/e;Ljava/lang/String;)Z
    move-result v0

    :toast_result
    if-eqz v0, :cleared
    const-string v5, "Preferred option saved for this file type."
    goto :toast

    :cleared
    const-string v5, "Preferred option cleared for this file type."

    :toast
    const/4 v6, 0x0
    invoke-static {v2, v5, v6}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v2
    invoke-virtual {v2}, Landroid/widget/Toast;->show()V
    const/4 v0, 0x1
    return v0

    :no
    const/4 v0, 0x0
    return v0
.end method'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'

    fa=sm/'dw/filemanager/open/FileAssociations.smali'
    t=fa.read_text()
    if 'matchesInternal(Ljava/lang/String;Ljava/lang/String;)Z' not in t:
        t=t.rstrip()+"\n"+INTERNAL_METHODS+"\n"
    fa.write_text(t)

    lc=sm/'dw/filemanager/open/AssociationLongClick.smali'
    t=lc.read_text()
    t,n=re.subn(r'\.method public onLongClick\(Landroid/view/View;\)Z.*?\.end method',LONGCLICK,t,count=1,flags=re.S)
    if n!=1: raise RuntimeError('AssociationLongClick.onLongClick not found')
    lc.write_text(t)

    y0=sm/'hf/y0.smali'; t=y0.read_text()

    # Internal rows previously had a null tag. Tag them with their hf/u0 click action so
    # the same long-press listener can recover the internal target Activity class.
    old='    invoke-virtual {v1, p3}, Landroid/view/View;->setTag(Ljava/lang/Object;)V'
    new='''    if-nez p3, :dw_assoc_external_tag\n    invoke-virtual {v1, p4}, Landroid/view/View;->setTag(Ljava/lang/Object;)V\n    goto :dw_assoc_tag_done\n    :dw_assoc_external_tag\n    invoke-virtual {v1, p3}, Landroid/view/View;->setTag(Ljava/lang/Object;)V\n    :dw_assoc_tag_done'''
    if t.count(old)!=1: raise RuntimeError(f'hf/y0 setTag anchor count={t.count(old)}')
    t=t.replace(old,new,1)

    # Auto-select a saved DW-internal row using the same existing click action that an
    # explicit tap would execute. This keeps retrieve/stream/details flags unchanged.
    anchor='''    invoke-direct/range {v1 .. v6}, Lhf/u0;-><init>(Lhf/y0;Ljava/lang/String;ILandroid/graphics/drawable/Drawable;I)V\n\n    .line 15\n    .line 16\n    .line 17\n    const/4 p1, 0x0'''
    repl='''    invoke-direct/range {v1 .. v6}, Lhf/u0;-><init>(Lhf/y0;Ljava/lang/String;ILandroid/graphics/drawable/Drawable;I)V\n\n    # DW Stage12d: saved internal Open With target.\n    iget-object v2, p0, Lhf/y0;->j2:Ljava/lang/String;\n    if-eqz v2, :dw_internal_assoc_continue\n    iget-boolean v3, p0, Lhf/y0;->k2:Z\n    if-nez v3, :dw_internal_assoc_continue\n    invoke-static {v2, p1}, Ldw/filemanager/open/FileAssociations;->matchesInternal(Ljava/lang/String;Ljava/lang/String;)Z\n    move-result v2\n    if-eqz v2, :dw_internal_assoc_continue\n    const/4 v2, 0x1\n    iput-boolean v2, p0, Lhf/y0;->k2:Z\n    const/4 v2, 0x0\n    invoke-virtual {v1, v2}, Lhf/u0;->onClick(Landroid/view/View;)V\n    return-void\n\n    :dw_internal_assoc_continue\n    .line 15\n    .line 16\n    .line 17\n    const/4 p1, 0x0'''
    if t.count(anchor)!=1: raise RuntimeError(f'hf/y0 internal c() anchor count={t.count(anchor)}')
    t=t.replace(anchor,repl,1)
    y0.write_text(t)

    strings=root/'res/values/strings.xml'; st=strings.read_text()
    st=st.replace('Long-press an application to set it as the preferred app for this file type; long-press the preferred app again to clear it.',
                  'Long-press any option to set it as the preferred choice for this file type; long-press the preferred choice again to clear it.')
    strings.write_text(st)

    # Install over device-confirmed v9109005.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    # Regression guards: all four user-reported internal options must still be present
    # somewhere in the Open With population graph, while the generic mechanism lives in y0.
    final=y0.read_text(); ftxt=fa.read_text(); ltxt=lc.read_text()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for cls in ('dw.filemanager.ui.viewer.TextViewerActivity','dw.filemanager.ui.textedit.EditorActivity','dw.filemanager.ui.viewer.BinaryViewerActivity','dw.filemanager.ui.details.DetailsActivity'):
        if cls not in corpus: raise RuntimeError('expected internal Open With target missing: '+cls)
    for tok in ('matchesInternal(Ljava/lang/String;Ljava/lang/String;)Z','toggleInternal(Landroid/content/Context;Lkh/e;Ljava/lang/String;)Z','const-string v1, "internal:"'):
        if tok not in ftxt: raise RuntimeError('internal association helper missing '+tok)
    if 'instance-of v4, v0, Lhf/u0;' not in ltxt: raise RuntimeError('internal long-press path missing')
    if 'invoke-virtual {v1, v2}, Lhf/u0;->onClick(Landroid/view/View;)V' not in final: raise RuntimeError('internal auto-open path missing')

    print('stage12d internal Open With associations installed for all DW internal rows; vc='+VC)

if __name__=='__main__': main()
