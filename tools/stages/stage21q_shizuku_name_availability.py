#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109040'

def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing method end '+sig)
    e+=len('\n.end method')
    return s,e,text[s:e]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; p=root/'smali/hc/e.smali'; t=p.read_text()
    sig='.method public final j0(Landroid/content/Context;Ljava/lang/CharSequence;)Z'
    s,e,m=method(t,sig)
    marker='''    move-result-object v0

    .line 16
    invoke-static {p1}, Ldw/filemanager/dirimpl/shell/ShellCatalog;->l(Landroid/content/Context;)Lhc/f;'''
    repl='''    move-result-object v0

    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v1
    if-eqz v1, :dw_legacy_name_available

    :try_start_dw_name_available
    invoke-static {p1, v0}, Ldw/filemanager/shizuku/DwShizukuFsClient;->stat(Landroid/content/Context;Ljava/lang/String;)Lph/e;
    :try_end_dw_name_available
    .catch Lph/o; {:try_start_dw_name_available .. :try_end_dw_name_available} :dw_name_not_found

    # stat succeeded: the candidate already exists, so the name is unavailable.
    const/4 v0, 0x0
    return v0

    :dw_name_not_found
    # If the candidate cannot be stat-ed, let the real mkdir/rename/create call
    # decide. This avoids falling back into the legacy root shell merely to run
    # `test -e`, while still rejecting every path that the Shizuku backend can
    # positively prove already exists.
    const/4 v0, 0x1
    return v0

    :dw_legacy_name_available
    .line 16
    invoke-static {p1}, Ldw/filemanager/dirimpl/shell/ShellCatalog;->l(Landroid/content/Context;)Lhc/f;'''
    if m.count(marker)!=1: raise RuntimeError('hc/e.j0 Shizuku availability anchor count '+str(m.count(marker)))
    m=m.replace(marker,repl,1); p.write_text(t[:s]+m+t[e:])

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    out=p.read_text();
    if 'dw_legacy_name_available' not in out or 'DwShizukuFsClient;->stat' not in out: raise RuntimeError('Shizuku name availability path missing')
    print('stage21q: create/rename name-availability checks use Shizuku stat instead of legacy root shell; vc='+VC)

if __name__=='__main__': main()
