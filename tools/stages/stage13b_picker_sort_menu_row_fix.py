#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109009'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    p=root/'smali/dw/filemanager/ui/filechooser/ChooserActivity.smali'
    t=p.read_text()
    start=t.find('# DW Stage13: persistent picker-only sort controls.')
    if start < 0: raise RuntimeError('Stage13 picker sort menu marker missing')
    end=t.find('    invoke-virtual {v3, p1}, Lyg/r;->d(Lyg/u;)V', start)
    if end < 0: raise RuntimeError('Stage13 picker sort menu end missing')
    end += len('    invoke-virtual {v3, p1}, Lyg/r;->d(Lyg/u;)V')
    block=t[start:end]
    n_new=block.count('new-instance v2, Lyg/s;')
    n_ctor=block.count('Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V')
    if n_new != 9 or n_ctor != 9:
        raise RuntimeError(f'expected 9 Stage13 sort Lyg/s rows, got new={n_new} ctor={n_ctor}')
    block=block.replace('new-instance v2, Lyg/s;','new-instance v2, Lyg/p;')
    block=block.replace('Lyg/s;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V','Lyg/p;-><init>(Ljava/lang/CharSequence;Landroid/graphics/drawable/Drawable;Lyg/b;)V')
    t=t[:start]+block+t[end:]
    p.write_text(t)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    final=p.read_text()
    repaired=final[start:final.find('    invoke-virtual {v3, p1}, Lyg/r;->d(Lyg/u;)V',start)+len('    invoke-virtual {v3, p1}, Lyg/r;->d(Lyg/u;)V')]
    if 'Lyg/s;-><init>' in repaired: raise RuntimeError('special/toggle row remains inside Stage13 Sort submenu')
    if repaired.count('Lyg/p;-><init>') != 9: raise RuntimeError('expected nine normal picker sort action rows')
    print('stage13b picker Sort submenu repaired: nine normal yg/p action rows; vc='+VC)

if __name__=='__main__': main()
