#!/usr/bin/env python3
from pathlib import Path
import argparse

NEW_L = r'''.method public final l()V
    .locals 3

    invoke-virtual {p0}, Ldw/filemanager/ui/ExplorerActivity;->x()Z
    move-result v0
    if-nez v0, :return

    iget-object v0, p0, Laf/c;->Y1:Lmb/l;
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;
    const-string v1, "tutorialVersion"
    const/4 v2, -0x1
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v0
    const/4 v1, 0x4
    if-eq v0, v1, :return

    sget-object v0, Lgg/j;->b:Lhh/e;
    if-eqz v0, :return

    const/4 v0, 0x1
    invoke-static {p0, v0}, Ldw/filemanager/ui/doc/DocExtension;->a(Laf/c;Z)V

    :return
    return-void
.end method
'''

def replace_method(path:Path, sig:str, replacement:str):
    text=path.read_text(); start=text.find(sig)
    if start<0: raise RuntimeError(f'{path}: method signature missing')
    end=text.find('.end method',start)
    if end<0: raise RuntimeError(f'{path}: method end missing')
    end+=len('.end method')
    path.write_text(text[:start]+replacement.rstrip()+text[end:])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    explorer=sm/'dw/filemanager/ui/ExplorerActivity.smali'
    replace_method(explorer,'.method public final l()V',NEW_L)

    bg=sm/'bg/c.smali'; lines=bg.read_text().splitlines()
    start=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_0')
    end=next(i for i,l in enumerate(lines[start+1:],start+1) if l.strip()==':pswitch_1')
    body='\n'.join(lines[start:end])
    for tok in ('acceptedLicenseVersion','Ldw/filemanager/ui/ExplorerActivity;->l()V','Landroid/app/Activity;->finish()V'):
        if tok not in body: raise RuntimeError(f'legal dismiss branch missing expected token {tok}')
    bg.write_text('\n'.join(lines[:start]+['    :pswitch_0','    return-void','']+lines[end:])+'\n')

    wf=sm/'wf/b.smali'
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali') if p!=wf)
    if 'Lwf/b;' in corpus: raise RuntimeError('wf/b still has external caller after legal dialog removal')
    wf.unlink()

    for name in ('license.txt','privacy.txt'):
        p=root/'assets/license'/name
        if not p.exists(): raise RuntimeError(f'missing expected vendor asset {name}')
        p.unlink()
    try: (root/'assets/license').rmdir()
    except OSError: pass

    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for tok in ('acceptedLicenseVersion','license/license.txt','Lwf/b;'):
        if tok in corpus: raise RuntimeError(f'legal-gate executable residue remains: {tok}')
    if (root/'assets/license/license.txt').exists() or (root/'assets/license/privacy.txt').exists():
        raise RuntimeError('vendor legal assets remain')
    print('stage07a app-owned legal acceptance gate removed')

if __name__=='__main__': main()
