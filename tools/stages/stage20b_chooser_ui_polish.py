#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109021'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # 1. Theme: chooser content uses same CONTENT surface as the Explorer content.
    p=sm/'dw/filemanager/ui/filechooser/ChooserActivity.smali'
    t=p.read_text()
    old='sget-object v3, Lef/f;->X1:Lef/f;'
    assert t.count(old)==1, t.count(old)
    t=t.replace(old,'sget-object v3, Lef/f;->f:Lef/f;',1)
    p.write_text(t)

    # 2. Sort orientation: insert native column breaks after Name and Kind.
    p=sm/'dw/filemanager/ui/filechooser/PickerSortMenu.smali'
    t=p.read_text()
    # target the addView immediately before Date and Size constructor blocks
    for marker in [
    '''    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V\n\n    new-instance v0, Laf/k;\n\n    move-object v1, p0\n\n    const-string v2, "Date"''',
    '''    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V\n\n    new-instance v0, Laf/k;\n\n    move-object v1, p0\n\n    const-string v2, "Size"''']:
        assert t.count(marker)==1, (marker[-20:],t.count(marker))
        replacement=marker.split('\n\n    new-instance v0, Laf/k;')[0]+'''\n\n    new-instance v0, Lyg/v;\n\n    invoke-direct {v0}, Ljava/lang/Object;-><init>()V\n\n    invoke-virtual {p1, v0}, Lyg/r;->d(Lyg/u;)V\n\n    new-instance v0, Laf/k;'''+marker.split('\n\n    new-instance v0, Laf/k;',1)[1]
        t=t.replace(marker,replacement,1)
    p.write_text(t)

    # 3. PickerPanel: separate HOME display mode, default Card, and root detection.
    p=sm/'dw/filemanager/ui/filechooser/PickerPanel.smali'
    t=p.read_text()
    # remove toggleFilter method completely
    pat=re.compile(r'\n\.method public static toggleFilter\(Ldw/filemanager/ui/filechooser/ChooserActivity;\)V\n.*?\n\.end method\n',re.S)
    t,n=pat.subn('\n',t,count=1); assert n==1
    # add isHome before viewMode
    is_home=r'''
    .method public static isHome(Landroid/content/Context;)Z
        .locals 3
        instance-of v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
        if-eqz v0, :no
        check-cast p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
        iget-object v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
        if-eqz v0, :no
        invoke-virtual {v0}, Leg/g;->getPath()Lhh/f;
        move-result-object v0
        if-eqz v0, :no
        iget-object v0, v0, Lhh/f;->f:[Ljava/lang/Object;
        array-length v0, v0
        if-nez v0, :no
        const/4 v0, 0x1
        return v0
        :no
        const/4 v0, 0x0
        return v0
    .end method
    '''
    idx=t.index('.method public static viewMode')
    t=t[:idx]+is_home+'\n'+t[idx:]
    # replace setViewMode method
    pat=re.compile(r'\.method public static setViewMode\(Ldw/filemanager/ui/filechooser/ChooserActivity;Lmb/m;\)V\n.*?\.end method',re.S)
    new_set=r'''.method public static setViewMode(Ldw/filemanager/ui/filechooser/ChooserActivity;Lmb/m;)V
        .locals 4
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
        move-result-object v0
        invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
        move-result-object v0
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->isHome(Landroid/content/Context;)Z
        move-result v1
        if-eqz v1, :normal
        const-string v1, "dw.picker.home_view_mode"
        goto :key
        :normal
        const-string v1, "dw.picker.view_mode"
        :key
        iget v2, p1, Lmb/m;->f:I
        invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
        move-result-object v0
        invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V
        iget-object v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
        if-eqz v0, :done
        invoke-virtual {v0}, Leg/g;->a()V
        :done
        return-void
    .end method'''
    t,n=pat.subn(new_set,t,count=1); assert n==1
    # replace viewMode
    pat=re.compile(r'\.method public static viewMode\(Landroid/content/Context;\)Lmb/m;\n.*?\.end method',re.S)
    new_view=r'''.method public static viewMode(Landroid/content/Context;)Lmb/m;
        .locals 4
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->prefs(Landroid/content/Context;)Landroid/content/SharedPreferences;
        move-result-object v0
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->isHome(Landroid/content/Context;)Z
        move-result v1
        if-eqz v1, :normal
        const-string v1, "dw.picker.home_view_mode"
        const/4 v2, 0x4
        goto :read
        :normal
        const-string v1, "dw.picker.view_mode"
        const/4 v2, 0x5
        :read
        invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
        move-result v0
        sget-object v1, Lmb/m;->Z:Lmb/m;
        invoke-static {v0, v1}, Lmb/m;->a(ILmb/m;)Lmb/m;
        move-result-object v0
        return-object v0
    .end method'''
    t,n=pat.subn(new_view,t,count=1); assert n==1
    p.write_text(t)

    # 4. Menu: home stops after DISPLAY AS; remove Search and Filter entirely.
    p=sm/'dw/filemanager/ui/filechooser/PickerPanelMenu.smali'
    t=p.read_text()
    # remove block Search through Filter by anchor after hidden add, before return
    start=t.index('    new-instance v1, Ldw/filemanager/ui/filechooser/PickerPanelAction;\n\n    const/4 v2, 0x2', t.index('iput-object v4, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;->m2:Lyg/s;'))
    end=t.index('    return-void\n.end method', start)
    t=t[:start]+t[end:]
    # insert home early return after final DISPLAY AS Usage item add, before PickerSortMenu call
    needle='''    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V\n\n    invoke-static {p0, p1}, Ldw/filemanager/ui/filechooser/PickerSortMenu;->add'''
    assert t.count(needle)==1
    repl='''    invoke-virtual {p1, v1}, Lyg/r;->d(Lyg/u;)V\n\n    invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->isHome(Landroid/content/Context;)Z\n    move-result v1\n    if-eqz v1, :not_home\n    return-void\n    :not_home\n\n    invoke-static {p0, p1}, Ldw/filemanager/ui/filechooser/PickerSortMenu;->add'''
    t=t.replace(needle,repl,1)
    p.write_text(t)

    # 5. PickerPanelAction only Refresh + SaveForFolder; remove search/filter switches.
    p=sm/'dw/filemanager/ui/filechooser/PickerPanelAction.smali'
    t=p.read_text()
    pat=re.compile(r'\.method public e\(Lyg/c;\)V\n.*?\.end method',re.S)
    new_action=r'''.method public e(Lyg/c;)V
        .locals 2
        iget-object v0, p0, Ldw/filemanager/ui/filechooser/PickerPanelAction;->activity:Ldw/filemanager/ui/filechooser/ChooserActivity;
        iget v1, p0, Ldw/filemanager/ui/filechooser/PickerPanelAction;->action:I
        if-nez v1, :save
        iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
        if-eqz v1, :done
        invoke-virtual {v1}, Leg/g;->a()V
        goto :done
        :save
        const/4 p1, 0x1
        if-ne v1, p1, :done
        invoke-static {v0}, Ldw/filemanager/ui/filechooser/PickerSort;->saveForFolder(Landroid/content/Context;)Z
        iget-object v1, v0, Ldw/filemanager/ui/filechooser/ChooserActivity;->l2:Leg/g;
        if-eqz v1, :done
        invoke-virtual {v1}, Leg/g;->a()V
        :done
        return-void
    .end method'''
    t,n=pat.subn(new_action,t,count=1); assert n==1
    p.write_text(t)
    # delete dead picker filter listener class; stale base bridges remain unreachable but no listener code is bundled
    fp=sm/'dw/filemanager/ui/filechooser/PickerFilterListener.smali'
    if fp.exists(): fp.unlink()

    # 6. HOME styler helper.
    helper=r'''.class public final Ldw/filemanager/ui/filechooser/PickerHomeStyler;
    .super Ljava/lang/Object;
    .source "DWPickerHome"

    .method public static itemType(Landroid/content/Context;)I
        .locals 2
        instance-of v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
        if-eqz v0, :list
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->viewMode(Landroid/content/Context;)Lmb/m;
        move-result-object v0
        sget-object v1, Lmb/m;->Z:Lmb/m;
        if-ne v0, v1, :list
        const/4 v0, 0x2
        return v0
        :list
        const/4 v0, 0x1
        return v0
    .end method

    .method public static usageEnabled(Landroid/content/Context;Z)Z
        .locals 2
        instance-of v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
        if-eqz v0, :default
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->viewMode(Landroid/content/Context;)Lmb/m;
        move-result-object v0
        sget-object v1, Lmb/m;->X1:Lmb/m;
        if-ne v0, v1, :default
        const/4 v0, 0x1
        return v0
        :default
        return p1
    .end method

    .method private static heading(Landroid/content/Context;Ljava/lang/String;)Landroid/widget/TextView;
        .locals 4
        new-instance v0, Landroid/widget/TextView;
        invoke-direct {v0, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
        invoke-virtual {v0, p1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
        const/high16 v1, 0x41a00000
        invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextSize(F)V
        const v1, 0x3f333333
        invoke-virtual {v0, v1}, Landroid/view/View;->setAlpha(F)V
        const/16 v1, 0x10
        invoke-static {p0, v1}, Lhf/p0;->d(Landroid/content/Context;I)I
        move-result v1
        const/16 v2, 0xc
        invoke-static {p0, v2}, Lhf/p0;->d(Landroid/content/Context;I)I
        move-result v2
        const/4 v3, 0x0
        invoke-virtual {v0, v1, v2, v1, v2}, Landroid/view/View;->setPadding(IIII)V
        return-object v0
    .end method

    .method private static addGroup(Landroid/content/Context;Landroid/widget/LinearLayout;Ljava/util/ArrayList;I)V
        .locals 10
        invoke-virtual {p2}, Ljava/util/ArrayList;->size()I
        move-result v0
        if-lez v0, :done
        const/4 v1, 0x1
        if-gt p3, v1, :grid
        const/4 v2, 0x0
        :list_loop
        if-ge v2, v0, :done
        invoke-virtual {p2, v2}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;
        move-result-object v3
        check-cast v3, Landroid/view/View;
        new-instance v4, Landroid/widget/LinearLayout$LayoutParams;
        const/4 v5, -0x1
        const/4 v6, -0x2
        invoke-direct {v4, v5, v6}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V
        invoke-virtual {v3, v4}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V
        invoke-virtual {p1, v3}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
        add-int/lit8 v2, v2, 0x1
        goto :list_loop

        :grid
        const/4 v2, 0x0
        :row_loop
        if-ge v2, v0, :done
        new-instance v3, Landroid/widget/LinearLayout;
        invoke-direct {v3, p0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V
        const/4 v4, 0x0
        invoke-virtual {v3, v4}, Landroid/widget/LinearLayout;->setOrientation(I)V
        int-to-float v5, p3
        invoke-virtual {v3, v5}, Landroid/widget/LinearLayout;->setWeightSum(F)V
        new-instance v5, Landroid/widget/LinearLayout$LayoutParams;
        const/4 v6, -0x1
        const/4 v7, -0x2
        invoke-direct {v5, v6, v7}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V
        invoke-virtual {p1, v3, v5}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
        const/4 v5, 0x0
        :cell_loop
        if-ge v5, p3, :row_loop
        if-ge v2, v0, :empty_cell
        invoke-virtual {p2, v2}, Ljava/util/ArrayList;->get(I)Ljava/lang/Object;
        move-result-object v6
        check-cast v6, Landroid/view/View;
        goto :have_cell
        :empty_cell
        new-instance v6, Landroid/view/Space;
        invoke-direct {v6, p0}, Landroid/view/Space;-><init>(Landroid/content/Context;)V
        :have_cell
        new-instance v7, Landroid/widget/LinearLayout$LayoutParams;
        const/4 v8, 0x0
        const/4 v9, -0x2
        const/high16 v1, 0x3f800000
        invoke-direct {v7, v8, v9, v1}, Landroid/widget/LinearLayout$LayoutParams;-><init>(IIF)V
        invoke-virtual {v6, v7}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V
        invoke-virtual {v3, v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
        if-ge v2, v0, :no_inc
        add-int/lit8 v2, v2, 0x1
        :no_inc
        add-int/lit8 v5, v5, 0x1
        goto :cell_loop
        :done
        return-void
    .end method

    .method public static apply(Landroid/content/Context;Landroid/widget/LinearLayout;)V
        .locals 9
        instance-of v0, p0, Ldw/filemanager/ui/filechooser/ChooserActivity;
        if-eqz v0, :done
        invoke-virtual {p1}, Landroid/view/ViewGroup;->getChildCount()I
        move-result v0
        if-lez v0, :done
        new-instance v1, Ljava/util/ArrayList;
        invoke-direct {v1}, Ljava/util/ArrayList;-><init>()V
        new-instance v2, Ljava/util/ArrayList;
        invoke-direct {v2}, Ljava/util/ArrayList;-><init>()V
        const/4 v3, 0x0
        :scan
        if-ge v3, v0, :scanned
        invoke-virtual {p1, v3}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;
        move-result-object v4
        instance-of v5, v4, Lff/q;
        if-eqz v5, :file
        invoke-virtual {v1, v4}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z
        goto :next
        :file
        invoke-virtual {v2, v4}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z
        :next
        add-int/lit8 v3, v3, 0x1
        goto :scan
        :scanned
        invoke-virtual {p1}, Landroid/view/ViewGroup;->removeAllViews()V
        invoke-static {p0}, Ldw/filemanager/ui/filechooser/PickerPanel;->viewMode(Landroid/content/Context;)Lmb/m;
        move-result-object v3
        const/4 v4, 0x2
        sget-object v5, Lmb/m;->X:Lmb/m;
        if-ne v3, v5, :not_list
        const/4 v4, 0x1
        goto :cols
        :not_list
        sget-object v5, Lmb/m;->Z:Lmb/m;
        if-ne v3, v5, :cols
        const/4 v4, 0x3
        :cols
        invoke-virtual {v1}, Ljava/util/ArrayList;->isEmpty()Z
        move-result v5
        if-nez v5, :files
        const-string v5, "BOOKMARKS"
        invoke-static {p0, v5}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->heading(Landroid/content/Context;Ljava/lang/String;)Landroid/widget/TextView;
        move-result-object v5
        invoke-virtual {p1, v5}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
        invoke-static {p0, p1, v1, v4}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->addGroup(Landroid/content/Context;Landroid/widget/LinearLayout;Ljava/util/ArrayList;I)V
        :files
        invoke-virtual {v2}, Ljava/util/ArrayList;->isEmpty()Z
        move-result v5
        if-nez v5, :done
        const-string v5, "FILES"
        invoke-static {p0, v5}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->heading(Landroid/content/Context;Ljava/lang/String;)Landroid/widget/TextView;
        move-result-object v5
        invoke-virtual {p1, v5}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V
        invoke-static {p0, p1, v2, v4}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->addGroup(Landroid/content/Context;Landroid/widget/LinearLayout;Ljava/util/ArrayList;I)V
        :done
        return-void
    .end method
    '''
    (sm/'dw/filemanager/ui/filechooser/PickerHomeStyler.smali').write_text(helper)

    # 7. Hook root/home construction and per-item geometry in Leg/c.
    p=sm/'eg/c.smali'; t=p.read_text()
    t=t.replace('.method public final onMeasure(II)V\n    .locals 10','.method public final onMeasure(II)V\n    .locals 11',1)
    old='''    iget-boolean v8, p0, Leg/c;->Z1:Z\n\n    .line 84\n    .line 85\n    invoke-direct {v7, v1, v6, v4, v8}, Lff/q;-><init>(Landroid/content/Context;Lff/d;IZ)V'''
    new='''    iget-boolean v8, p0, Leg/c;->Z1:Z\n\n    invoke-static {v1}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->itemType(Landroid/content/Context;)I\n    move-result v10\n\n    .line 84\n    .line 85\n    invoke-direct {v7, v1, v6, v10, v8}, Lff/q;-><init>(Landroid/content/Context;Lff/d;IZ)V'''
    assert t.count(old)==1;t=t.replace(old,new,1)
    old='''    move-result v8\n\n    .line 132\n    iget-boolean v9, p0, Leg/c;->Z1:Z'''
    new='''    move-result v8\n\n    invoke-static {v1, v8}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->usageEnabled(Landroid/content/Context;Z)Z\n    move-result v8\n\n    .line 132\n    iget-boolean v9, p0, Leg/c;->Z1:Z'''
    assert t.count(old)==1;t=t.replace(old,new,1)
    old='''    new-instance v5, Lxf/c;\n\n    .line 159\n    .line 160\n    invoke-direct {v5, v1, v4}, Lxf/c;-><init>(Landroid/content/Context;I)V'''
    new='''    new-instance v5, Lxf/c;\n\n    invoke-static {v1}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->itemType(Landroid/content/Context;)I\n    move-result v10\n\n    .line 159\n    .line 160\n    invoke-direct {v5, v1, v10}, Lxf/c;-><init>(Landroid/content/Context;I)V'''
    assert t.count(old)==1;t=t.replace(old,new,1)
    needle='''    :cond_3\n    invoke-super {p0, p1, p2}, Landroid/widget/ScrollView;->onMeasure(II)V'''
    repl='''    :cond_3\n    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;\n    move-result-object v0\n    iget-object v2, p0, Leg/c;->i:Landroid/widget/LinearLayout;\n    invoke-static {v0, v2}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->apply(Landroid/content/Context;Landroid/widget/LinearLayout;)V\n\n    invoke-super {p0, p1, p2}, Landroid/widget/ScrollView;->onMeasure(II)V'''
    assert t.count(needle)==1;t=t.replace(needle,repl,1)
    p.write_text(t)

    # 8. local catalog tile constructor uses Icon tile geometry on chooser HOME Icon mode.
    p=sm/'hf/o0.smali'; t=p.read_text()
    old='''    const/4 v0, 0x1\n\n    .line 2\n    invoke-direct {p0, p1, v0}, Lxf/c;-><init>(Landroid/content/Context;I)V'''
    new='''    const/4 v0, 0x1\n\n    instance-of v1, p1, Ldw/filemanager/ui/filechooser/ChooserActivity;\n    if-eqz v1, :dw_type_ready\n    invoke-static {p1}, Ldw/filemanager/ui/filechooser/PickerHomeStyler;->itemType(Landroid/content/Context;)I\n    move-result v0\n    :dw_type_ready\n\n    .line 2\n    invoke-direct {p0, p1, v0}, Lxf/c;-><init>(Landroid/content/Context;I)V'''
    assert t.count(old)==1;t=t.replace(old,new,1)
    p.write_text(t)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>9109021',yt,count=1); assert n==1; y.write_text(yt)

    assert 'action_search' not in (sm/'dw/filemanager/ui/filechooser/PickerPanelMenu.smali').read_text()
    assert 'action_filter' not in (sm/'dw/filemanager/ui/filechooser/PickerPanelMenu.smali').read_text()
    assert (sm/'dw/filemanager/ui/filechooser/PickerSortMenu.smali').read_text().count('new-instance v0, Lyg/v;')==2
    print('stage20b polished chooser theme/home/menu; removed broken search/filter; vc=9109021')

if __name__=='__main__': main()
