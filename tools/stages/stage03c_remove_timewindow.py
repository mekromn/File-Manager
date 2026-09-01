#!/usr/bin/env python3
from pathlib import Path
import argparse, re

def remove_method(path: Path, prefix: str):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: expected 1 {prefix}, got {n}')
    path.write_text('\n'.join(out)+'\n')

def strip_export_trial(path: Path):
    lines=path.read_text().splitlines()
    a=next(i for i,l in enumerate(lines) if l.strip()==':cond_29')
    b=next(i for i in range(a+1,len(lines)) if lines[i].strip()==':cond_2a')
    seg='\n'.join(lines[a:b])
    if 'trialexp' not in seg or 'Ljb/a;->q' not in seg: raise RuntimeError('unexpected export trial block')
    lines[a:b]=['    :cond_29','    # retired trial-expiration archive entry removed','']
    path.write_text('\n'.join(lines)+'\n')

def strip_import_trial(path: Path):
    lines=path.read_text().splitlines()
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final b()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if 'new-instance v14, Ljava/io/File;' in lines[i])
    g=next(i for i in range(a,e) if lines[i].strip()==':goto_2')
    seg='\n'.join(lines[a:g])
    if 'trialexp' not in seg or ':catchall_0' not in seg: raise RuntimeError('unexpected import trial parse block')
    repl=['    :try_end_2','    .catchall {:try_start_2 .. :try_end_2} :catchall_0','','    goto :goto_2','', '    :catchall_0','    move-exception v0','    goto/16 :goto_3','']
    lines[a:g]=repl
    s=next(i for i,l in enumerate(lines) if l.startswith('.method public final b()V'))
    e=next(i for i in range(s+1,len(lines)) if lines[i]=='.end method')
    a=next(i for i in range(s,e) if 'cmp-long v0, v14, v16' in lines[i])
    b=next(i for i in range(a,e) if lines[i].strip()==':cond_4')
    lines[a:b+1]=['    # retired trial-expiration persistence removed']
    path.write_text('\n'.join(lines)+'\n')

def remove_field_i(path: Path):
    t=path.read_text()
    nt,n=re.subn(r'^\.field public static i:J = -0x8000000000000000L\n\n?', '', t, count=1, flags=re.M)
    if n!=1: raise RuntimeError('trial expiration field not found')
    path.write_text(nt)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; sm=root/'smali'
    strip_export_trial(sm/'sf/a.smali')
    strip_import_trial(sm/'mb/c.smali')
    jba=sm/'jb/a.smali'
    for prefix in ('.method public static m(Landroid/content/Context;)J','.method public static p(Landroid/content/Context;)Z','.method public static q(Landroid/content/Context;)Z'):
        remove_method(jba,prefix)
    remove_field_i(jba)
    remove_method(sm/'mb/l.smali','.method public final G(J)V')
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    banned=['Ljb/a;->m(Landroid/content/Context;)J','Ljb/a;->p(Landroid/content/Context;)Z','Ljb/a;->q(Landroid/content/Context;)Z','Ljb/a;->i:J','Lmb/l;->G(J)V','trialPlusExpiration','trialexp']
    hits=[x for x in banned if x in corpus]
    if hits: raise RuntimeError(f'remaining trial/time-window executable refs: {hits}')
    print('stage03c time-window persistence removed')

if __name__=='__main__': main()
