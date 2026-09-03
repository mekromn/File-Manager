#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109007'

OLD='''    # External application rows: long-press toggles preferred app for this exact extension.\n    if-eqz p3, :dw_assoc_no_long_press\n    new-instance v2, Ldw/filemanager/open/AssociationLongClick;\n    invoke-direct {v2, p0}, Ldw/filemanager/open/AssociationLongClick;-><init>(Lhf/y0;)V\n    invoke-virtual {v1, v2}, Landroid/view/View;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V\n    :dw_assoc_no_long_press\n'''

NEW='''    # DW Stage12e: every Open With tile is persistable. Stage12d tags internal\n    # rows with their hf/u0 action and external rows with qe/b ResolveInfo, so the\n    # same listener can safely handle both kinds.\n    new-instance v2, Ldw/filemanager/open/AssociationLongClick;\n    invoke-direct {v2, p0}, Ldw/filemanager/open/AssociationLongClick;-><init>(Lhf/y0;)V\n    invoke-virtual {v1, v2}, Landroid/view/View;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V\n'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    y0=root/'smali/hf/y0.smali'
    t=y0.read_text()
    n=t.count(OLD)
    if n!=1: raise RuntimeError(f'conditional external-only long-press block count={n}')
    t=t.replace(OLD,NEW,1)
    y0.write_text(t)

    # Install over the failed-on-device v9109006 candidate.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    final=y0.read_text()
    if 'if-eqz p3, :dw_assoc_no_long_press' in final:
        raise RuntimeError('external-only long-press gate still present')
    if final.count('Ldw/filemanager/open/AssociationLongClick;-><init>(Lhf/y0;)V')!=1:
        raise RuntimeError('expected one universal association long-press listener')
    if 'invoke-virtual {v1, v2}, Landroid/view/View;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V' not in final:
        raise RuntimeError('universal Open With long-press listener missing')

    print('stage12e fixed internal Open With long-press listener attachment; all internal/external rows persistable; vc='+VC)

if __name__=='__main__': main()
