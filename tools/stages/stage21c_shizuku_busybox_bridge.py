#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109026'
TARGET='/data/local/tmp/dw-filemanager-busybox'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # The root/ShellCatalog parser uses DW's bundled BusyBox for exact ls output.
    # A Shizuku process runs as Android's shell UID and cannot normally traverse
    # DW's private /data/user/0 package directory to execute that binary. Stage a
    # byte-identical copy into /data/local/tmp, created by the Shizuku shell, then
    # retain the existing parser and command protocol unchanged.
    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'
    if not bp.exists(): raise RuntimeError('Stage21a ShizukuBridge missing')
    t=bp.read_text()
    field='.field private static volatile busyboxReady:Z\n'
    if 'busyboxReady:Z' not in t:
        anchor='.source "DWShizukuBridge"\n'
        if t.count(anchor)!=1: raise RuntimeError('ShizukuBridge source anchor changed')
        t=t.replace(anchor,anchor+'\n'+field,1)

    extra=r'''
.method public static isAuthorized()Z
    .locals 2
    :try_start
    invoke-static {}, Lrikka/shizuku/Shizuku;->pingBinder()Z
    move-result v0
    if-eqz v0, :no
    invoke-static {}, Lrikka/shizuku/Shizuku;->checkSelfPermission()I
    move-result v0
    if-nez v0, :no
    const/4 v0, 0x1
    return v0
    :no
    const/4 v0, 0x0
    return v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :fail
    :fail
    const/4 v0, 0x0
    return v0
.end method

.method public static busyboxPath(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    .locals 12
    if-eqz p1, :original
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :original

    sget-boolean v0, Ldw/filemanager/shizuku/ShizukuBridge;->busyboxReady:Z
    if-eqz v0, :stage
    const-string v0, "/data/local/tmp/dw-filemanager-busybox"
    return-object v0

    :stage
    :try_start
    const/4 v0, 0x3
    new-array v1, v0, [Ljava/lang/String;
    const/4 v2, 0x0
    const-string v3, "sh"
    aput-object v3, v1, v2
    const/4 v2, 0x1
    const-string v3, "-c"
    aput-object v3, v1, v2
    const/4 v2, 0x2
    const-string v3, "cat > /data/local/tmp/dw-filemanager-busybox && chmod 700 /data/local/tmp/dw-filemanager-busybox"
    aput-object v3, v1, v2
    const/4 v2, 0x0
    invoke-static {v1, v2, v2}, Lrikka/shizuku/Shizuku;->newProcess([Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Lrikka/shizuku/ShizukuRemoteProcess;
    move-result-object v4
    if-eqz v4, :original

    new-instance v5, Ljava/io/FileInputStream;
    invoke-direct {v5, p1}, Ljava/io/FileInputStream;-><init>(Ljava/lang/String;)V
    invoke-virtual {v4}, Ljava/lang/Process;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v6
    const/16 v7, 0x4000
    new-array v7, v7, [B

    :copy
    invoke-virtual {v5, v7}, Ljava/io/FileInputStream;->read([B)I
    move-result v8
    if-ltz v8, :copied
    const/4 v9, 0x0
    invoke-virtual {v6, v7, v9, v8}, Ljava/io/OutputStream;->write([BII)V
    goto :copy

    :copied
    invoke-virtual {v5}, Ljava/io/FileInputStream;->close()V
    invoke-virtual {v6}, Ljava/io/OutputStream;->flush()V
    invoke-virtual {v6}, Ljava/io/OutputStream;->close()V
    invoke-virtual {v4}, Ljava/lang/Process;->waitFor()I
    move-result v8
    if-nez v8, :original

    const/4 v8, 0x1
    sput-boolean v8, Ldw/filemanager/shizuku/ShizukuBridge;->busyboxReady:Z
    const-string v0, "/data/local/tmp/dw-filemanager-busybox"
    return-object v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :original

    :original
    return-object p1
.end method
'''
    if 'busyboxPath(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;' not in t:
        t=t.rstrip()+'\n'+extra+'\n'
    bp.write_text(t)

    # Make the existing te/a BusyBox resolver transparently return the shell-owned
    # staged path only while Shizuku is active+authorized. With no Shizuku grant,
    # the original private BusyBox path remains untouched for genuine su/root.
    tp=sm/'te/a.smali'; tt=tp.read_text()
    pat=re.compile(r'\.method public final i\(\)Ljava/lang/String;\n.*?\n\.end method',re.S)
    new_i=r'''.method public final i()Ljava/lang/String;
    .locals 3
    iget-object v0, p0, Lte/a;->h:Lmb/l;
    iget-object v0, v0, Lmb/l;->b:Landroid/content/SharedPreferences;
    const-string v1, "busyboxPath9"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-nez v0, :have
    iget-object v0, p0, Lte/a;->i:Landroid/content/Context;
    invoke-static {v0}, Lph/r;->q(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0
    :have
    iget-object v1, p0, Lte/a;->i:Landroid/content/Context;
    invoke-static {v1, v0}, Ldw/filemanager/shizuku/ShizukuBridge;->busyboxPath(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method'''
    tt,n=pat.subn(new_i,tt,count=1)
    if n!=1: raise RuntimeError('te/a BusyBox resolver method changed')
    tp.write_text(tt)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    bt=bp.read_text(); et=tp.read_text()
    for tok in ('busyboxReady:Z','isAuthorized()Z','busyboxPath(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;',
                'cat > /data/local/tmp/dw-filemanager-busybox','chmod 700 /data/local/tmp/dw-filemanager-busybox','FileInputStream','waitFor()I'):
        if tok not in bt: raise RuntimeError('Shizuku BusyBox bridge missing '+tok)
    if 'ShizukuBridge;->busyboxPath' not in et: raise RuntimeError('te/a does not use Shizuku BusyBox bridge')
    print('stage21c stages DW BusyBox into shell-owned /data/local/tmp for Shizuku directory listing; vc='+VC)

if __name__=='__main__': main()
