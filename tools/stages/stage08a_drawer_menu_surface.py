#!/usr/bin/env python3
from pathlib import Path
import argparse

METHOD = r'''
.method public final dwMenuBackground()I
    .locals 3

    sget-object v0, Lfg/n;->f:Lfg/n;
    iget-object v1, p0, Lef/g;->d:Lfg/q;
    iget-object v2, p0, Lef/g;->b:Landroid/content/res/Resources;
    invoke-virtual {v1, v2, v0}, Lfg/q;->a(Landroid/content/res/Resources;Lfg/n;)I
    move-result v0
    if-nez v0, :cond_dw_menu
    invoke-virtual {p0}, Lef/g;->w()I
    move-result v0
    :cond_dw_menu
    return v0
.end method

'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    theme=root/'smali/ef/g.smali'; text=theme.read_text()
    if '.method public final dwMenuBackground()I' in text: raise SystemExit('dwMenuBackground already exists')
    marker='.method public final w()I\n'
    if text.count(marker)!=1: raise RuntimeError(f'w method marker count={text.count(marker)}')
    theme.write_text(text.replace(marker,METHOD+marker,1))
    drawer=root/'smali/bg/f.smali'; d=drawer.read_text()
    old='    invoke-virtual {v4}, Lef/g;->w()I\n'; new='    invoke-virtual {v4}, Lef/g;->dwMenuBackground()I\n'
    if d.count(old)!=1: raise RuntimeError(f'drawer w call count={d.count(old)}')
    drawer.write_text(d.replace(old,new,1))
    assert 'Lef/g;->dwMenuBackground()I' in drawer.read_text()
    assert 'sget-object v0, Lfg/n;->f:Lfg/n;' in theme.read_text()
    print('stage08a drawer body now resolves menuBackground with windowBackground fallback')

if __name__=='__main__': main()
