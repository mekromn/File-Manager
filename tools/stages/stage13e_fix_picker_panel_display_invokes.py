#!/usr/bin/env python3
from pathlib import Path
import argparse

CASES=[
('Z','0x7f100063','action_view_icon'),
('Y','0x7f100061','action_view_grid'),
('X','0x7f100064','action_view_list'),
('X1','0x7f100067','action_pie'),
]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    p=root/'smali/dw/filemanager/ui/filechooser/PickerPanelMenu.smali'
    t=p.read_text()
    for enum,rid,icon in CASES:
        old=f'''    sget-object v2, Lmb/m;->{enum}:Lmb/m;\n    const v3, {rid}\n    const-string v4, "{icon}"\n    move-object v1, p0\n    move-object v5, v9\n    invoke-static/range {{v1 .. v5}}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;'''
        new=f'''    move-object v1, p0\n    move-object v2, v0\n    sget-object v3, Lmb/m;->{enum}:Lmb/m;\n    const v4, {rid}\n    const-string v5, "{icon}"\n    move-object v6, v9\n    invoke-static/range {{v1 .. v6}}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem(Ldw/filemanager/ui/filechooser/ChooserActivity;Landroid/content/res/Resources;Lmb/m;ILjava/lang/String;Lmb/m;)Lyg/s;'''
        if t.count(old)!=1: raise RuntimeError(f'display invoke block not found for {enum}: {t.count(old)}')
        t=t.replace(old,new,1)
    p.write_text(t)
    if t.count('invoke-static/range {v1 .. v6}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem')!=4:
        raise RuntimeError('expected four corrected six-register display invokes')
    if 'invoke-static/range {v1 .. v5}, Ldw/filemanager/ui/filechooser/PickerPanelMenu;->displayItem' in t:
        raise RuntimeError('old five-register display invoke remains')
    print('stage13e corrected all four full-panel Display As invoke/range register layouts')

if __name__=='__main__': main()
