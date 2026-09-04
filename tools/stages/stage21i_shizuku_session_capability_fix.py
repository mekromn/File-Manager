#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109032'

def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing end '+sig)
    e+=len('\n.end method')
    return s,e,text[s:e]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # Stage21h correctly put Shizuku into the actual directory list/stat code,
    # but ShellCatalog.l() created an ad-hoc root connection.  More importantly,
    # ph/i still tried to create an interactive root shell through startShell()
    # before it could mark the connection Shizuku-capable.  If that interactive
    # bootstrap failed, DW fell through to ProcessBuilder("su") and concluded it
    # had no filesystem access even though one-shot Shizuku commands worked.
    #
    # Fix the capability model at the session layer: an authorized Shizuku server
    # is sufficient to mark a ROOT_* shell session as Shizuku-backed.  We create
    # only a harmless local /system/bin/sh placeholder for the inherited stream
    # fields; every privileged command already branches on ph/i.shizuku and is
    # executed by ShizukuBridge.startCommand().  No su probe is attempted.
    ip=sm/'ph/i.smali'; t=ip.read_text()
    sig='.method public constructor <init>(Landroid/content/Context;Lph/q;)V'
    s,e,m=method(t,sig)
    old=r'''    iget-object v0, p2, Lph/q;->f:Ljava/lang/String;

    const-string v1, "su"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_0

    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuBridge;->startShell(Landroid/content/Context;)Ljava/lang/Process;

    move-result-object v2

    if-eqz v2, :cond_0

    iput-object v2, p0, Lph/i;->a:Ljava/lang/Process;

    const/4 v5, 0x1

    iput-boolean v5, p0, Lph/i;->shizuku:Z

    goto :goto_1
'''
    new=r'''    iget-object v0, p2, Lph/q;->f:Ljava/lang/String;

    const-string v1, "su"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_0

    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z

    move-result v2

    if-eqz v2, :cond_0

    :try_start_dw_shizuku_session
    invoke-static {}, Ljava/lang/Runtime;->getRuntime()Ljava/lang/Runtime;

    move-result-object v2

    const-string v3, "/system/bin/sh"

    invoke-virtual {v2, v3}, Ljava/lang/Runtime;->exec(Ljava/lang/String;)Ljava/lang/Process;

    move-result-object v2

    iput-object v2, p0, Lph/i;->a:Ljava/lang/Process;

    const/4 v5, 0x1

    iput-boolean v5, p0, Lph/i;->shizuku:Z
    :try_end_dw_shizuku_session
    .catch Ljava/io/IOException; {:try_start_dw_shizuku_session .. :try_end_dw_shizuku_session} :catch_0

    goto :goto_1
'''
    if m.count(old)!=1: raise RuntimeError('ph/i Shizuku bootstrap anchor changed: '+str(m.count(old)))
    m=m.replace(old,new,1); t=t[:s]+m+t[e:]; ip.write_text(t)

    # Restore ShellCatalog.l() to DW's normal SessionManager lifecycle.  The
    # pooled hc/f connection is now Shizuku-aware because ph/i recognizes the
    # capability above.  This avoids a parallel session model and preserves all
    # of DW's existing acquire/release semantics.
    sp=sm/'dw/filemanager/dirimpl/shell/ShellCatalog.smali'; st=sp.read_text()
    sig='.method public static l(Landroid/content/Context;)Lhc/f;'
    s,e,m=method(st,sig)
    restored=r'''.method public static l(Landroid/content/Context;)Lhc/f;
    .locals 3

    .line 1
    invoke-static {p0}, Lmb/l;->d(Landroid/content/Context;)Lmb/l;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;

    .line 6
    .line 7
    const-string v1, "rootGlobalMountNamespace"

    .line 8
    .line 9
    const/4 v2, 0x1

    .line 10
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z

    .line 11
    .line 12
    .line 13
    move-result v0

    .line 14
    if-eqz v0, :cond_0

    .line 15
    .line 16
    sget-object v0, Ldw/filemanager/dirimpl/shell/ShellCatalog;->X:Lhc/d;

    .line 17
    .line 18
    goto :goto_0

    .line 19
    :cond_0
    sget-object v0, Ldw/filemanager/dirimpl/shell/ShellCatalog;->i:Lhc/d;

    .line 20
    .line 21
    :goto_0
    invoke-static {p0, v0}, Ldw/filemanager/xf/connection/SessionManager;->a(Landroid/content/Context;Ljh/c;)Ljh/a;

    .line 22
    .line 23
    .line 24
    move-result-object p0

    .line 25
    check-cast p0, Lhc/f;

    .line 26
    .line 27
    return-object p0
.end method'''
    st=st[:s]+restored+st[e:]; sp.write_text(st)

    # Make the visible diagnostics reflect the capability that DW will actually
    # use rather than implying the failed UID-0 test means no filesystem access.
    strings=root/'res/values/strings.xml'; x=strings.read_text()
    x=x.replace('<string name="root_diag_test_result">Legacy su Root Shell Test</string>',
                '<string name="root_diag_test_result">Legacy UID-0 Root Test (Shizuku is separate)</string>')
    strings.write_text(x)

    y=root/'apktool.yml'; yt=y.read_text()
    yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    ft=ip.read_text(); fs=sp.read_text()
    for tok in ('ShizukuBridge;->isAuthorized()Z','Runtime;->exec(Ljava/lang/String;)Ljava/lang/Process;','shizuku:Z'):
        if tok not in ft: raise RuntimeError('Shizuku session capability patch missing '+tok)
    if 'SessionManager;->a(Landroid/content/Context;Ljh/c;)Ljh/a;' not in fs:
        raise RuntimeError('ShellCatalog SessionManager lifecycle not restored')
    print('stage21i: Shizuku is now a first-class ROOT_* session capability; no su probe/bootstrap required; vc='+VC)

if __name__=='__main__': main()
