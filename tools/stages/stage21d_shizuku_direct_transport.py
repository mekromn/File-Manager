#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109027'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # Shizuku runs commands as Android's shell UID.  DW's original root command
    # transport redirects each command into FIFO nodes under Context.getDir("Pipe"),
    # which lives below the app-private /data/user/0 directory and is not writable
    # by uid=shell.  Do not try to relax permissions on that private directory.
    # Instead, keep the exact legacy FIFO transport for genuine su/root and use a
    # one-shot Shizuku process whose Binder-backed stdout/stderr streams are read
    # directly by the app process.

    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'
    bt=bp.read_text()
    extra=r'''
.method public static startCommand(Ljava/lang/String;)Ljava/lang/Process;
    .locals 5
    :try_start
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :none
    const/4 v0, 0x3
    new-array v1, v0, [Ljava/lang/String;
    const/4 v2, 0x0
    const-string v3, "sh"
    aput-object v3, v1, v2
    const/4 v2, 0x1
    const-string v3, "-c"
    aput-object v3, v1, v2
    const/4 v2, 0x2
    aput-object p0, v1, v2
    const/4 v2, 0x0
    invoke-static {v1, v2, v2}, Lrikka/shizuku/Shizuku;->newProcess([Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Lrikka/shizuku/ShizukuRemoteProcess;
    move-result-object v0
    return-object v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :none
    :none
    const/4 v0, 0x0
    return-object v0
.end method

.method public static copyCommandToFile(Ljava/lang/String;Ljava/lang/String;)V
    .locals 10
    invoke-static {p0}, Ldw/filemanager/shizuku/ShizukuBridge;->startCommand(Ljava/lang/String;)Ljava/lang/Process;
    move-result-object v0
    if-nez v0, :started
    new-instance v1, Ljava/io/IOException;
    const-string v2, "Unable to start Shizuku command"
    invoke-direct {v1, v2}, Ljava/io/IOException;-><init>(Ljava/lang/String;)V
    throw v1

    :started
    new-instance v1, Ljava/lang/StringBuffer;
    invoke-direct {v1}, Ljava/lang/StringBuffer;-><init>()V
    invoke-virtual {v0}, Ljava/lang/Process;->getErrorStream()Ljava/io/InputStream;
    move-result-object v2
    new-instance v3, Ldw/filemanager/shizuku/ShizukuErrorDrainer;
    invoke-direct {v3, v2, v1}, Ldw/filemanager/shizuku/ShizukuErrorDrainer;-><init>(Ljava/io/InputStream;Ljava/lang/StringBuffer;)V
    new-instance v4, Ljava/lang/Thread;
    invoke-direct {v4, v3}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V
    invoke-virtual {v4}, Ljava/lang/Thread;->start()V

    invoke-virtual {v0}, Ljava/lang/Process;->getInputStream()Ljava/io/InputStream;
    move-result-object v5
    new-instance v6, Ljava/io/FileOutputStream;
    invoke-direct {v6, p1}, Ljava/io/FileOutputStream;-><init>(Ljava/lang/String;)V
    const/16 v7, 0x4000
    new-array v7, v7, [B
    :copy
    invoke-virtual {v5, v7}, Ljava/io/InputStream;->read([B)I
    move-result v8
    if-ltz v8, :copied
    const/4 v9, 0x0
    invoke-virtual {v6, v7, v9, v8}, Ljava/io/OutputStream;->write([BII)V
    goto :copy
    :copied
    invoke-virtual {v6}, Ljava/io/OutputStream;->flush()V
    invoke-virtual {v6}, Ljava/io/OutputStream;->close()V
    invoke-virtual {v5}, Ljava/io/InputStream;->close()V
    :try_wait
    invoke-virtual {v0}, Ljava/lang/Process;->waitFor()I
    move-result v8
    invoke-virtual {v4}, Ljava/lang/Thread;->join()V
    :try_wait_end
    .catch Ljava/lang/InterruptedException; {:try_wait .. :try_wait_end} :interrupted
    goto :check
    :interrupted
    invoke-virtual {v0}, Ljava/lang/Process;->destroy()V
    new-instance v2, Ljava/io/IOException;
    const-string v3, "Interrupted waiting for Shizuku command"
    invoke-direct {v2, v3}, Ljava/io/IOException;-><init>(Ljava/lang/String;)V
    throw v2

    :check
    invoke-virtual {v1}, Ljava/lang/StringBuffer;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v2}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object v3
    invoke-virtual {v3}, Ljava/lang/String;->isEmpty()Z
    move-result v4
    if-nez v4, :exit
    new-instance v4, Ljava/io/IOException;
    invoke-direct {v4, v2}, Ljava/io/IOException;-><init>(Ljava/lang/String;)V
    throw v4
    :exit
    if-eqz v8, :ok
    new-instance v2, Ljava/io/IOException;
    const-string v3, "Shizuku shell command failed"
    invoke-direct {v2, v3}, Ljava/io/IOException;-><init>(Ljava/lang/String;)V
    throw v2
    :ok
    return-void
.end method
'''
    if 'startCommand(Ljava/lang/String;)Ljava/lang/Process;' not in bt:
        bt=bt.rstrip()+'\n'+extra+'\n'
    bp.write_text(bt)

    drainer=r'''.class public final Ldw/filemanager/shizuku/ShizukuErrorDrainer;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.source "DWShizukuErrorDrainer"

.field private final in:Ljava/io/InputStream;
.field private final out:Ljava/lang/StringBuffer;

.method public constructor <init>(Ljava/io/InputStream;Ljava/lang/StringBuffer;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/shizuku/ShizukuErrorDrainer;->in:Ljava/io/InputStream;
    iput-object p2, p0, Ldw/filemanager/shizuku/ShizukuErrorDrainer;->out:Ljava/lang/StringBuffer;
    return-void
.end method

.method public run()V
    .locals 5
    :try_start
    new-instance v0, Ljava/io/BufferedReader;
    new-instance v1, Ljava/io/InputStreamReader;
    iget-object v2, p0, Ldw/filemanager/shizuku/ShizukuErrorDrainer;->in:Ljava/io/InputStream;
    sget-object v3, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;
    invoke-direct {v1, v2, v3}, Ljava/io/InputStreamReader;-><init>(Ljava/io/InputStream;Ljava/nio/charset/Charset;)V
    invoke-direct {v0, v1}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V
    const/4 v4, 0x1
    :loop
    invoke-virtual {v0}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v1
    if-eqz v1, :done
    if-nez v4, :first
    iget-object v2, p0, Ldw/filemanager/shizuku/ShizukuErrorDrainer;->out:Ljava/lang/StringBuffer;
    const/16 v3, 0xa
    invoke-virtual {v2, v3}, Ljava/lang/StringBuffer;->append(C)Ljava/lang/StringBuffer;
    :first
    const/4 v4, 0x0
    iget-object v2, p0, Ldw/filemanager/shizuku/ShizukuErrorDrainer;->out:Ljava/lang/StringBuffer;
    invoke-virtual {v2, v1}, Ljava/lang/StringBuffer;->append(Ljava/lang/String;)Ljava/lang/StringBuffer;
    goto :loop
    :done
    invoke-virtual {v0}, Ljava/io/BufferedReader;->close()V
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :ignore
    :ignore
    return-void
.end method
'''
    dp=sm/'dw/filemanager/shizuku/ShizukuErrorDrainer.smali'; dp.parent.mkdir(parents=True,exist_ok=True); dp.write_text(drainer)

    # Mark only root-mode ph/i instances that actually obtained a Shizuku process.
    ip=sm/'ph/i.smali'; it=ip.read_text()
    if '.field public shizuku:Z' not in it:
        anchor='.field public f:Z\n'
        if it.count(anchor)!=1: raise RuntimeError('ph/i field anchor changed')
        it=it.replace(anchor,anchor+'\n.field public shizuku:Z\n',1)
    init='''    iput-boolean v0, p0, Lph/i;->f:Z\n    iput-object p1, p0, Lph/i;->d:Landroid/content/Context;'''
    init2='''    iput-boolean v0, p0, Lph/i;->f:Z\n    iput-boolean v0, p0, Lph/i;->shizuku:Z\n    iput-object p1, p0, Lph/i;->d:Landroid/content/Context;'''
    if it.count(init)==1: it=it.replace(init,init2,1)
    elif 'iput-boolean v0, p0, Lph/i;->shizuku:Z' not in it: raise RuntimeError('ph/i shizuku init anchor changed')
    got='''    iput-object v2, p0, Lph/i;->a:Ljava/lang/Process;\n    goto :streams'''
    got2='''    iput-object v2, p0, Lph/i;->a:Ljava/lang/Process;\n    const/4 v5, 0x1\n    iput-boolean v5, p0, Lph/i;->shizuku:Z\n    goto :streams'''
    if it.count(got)==1: it=it.replace(got,got2,1)
    elif 'iput-boolean v5, p0, Lph/i;->shizuku:Z' not in it: raise RuntimeError('ph/i Shizuku process anchor changed')

    # Direct Shizuku streaming branch for b(); legacy root and user shells retain
    # the original PipeFactory implementation byte-for-byte below this gate.
    bhead='''.method public final b(Ljava/lang/String;Lph/s;)Lph/g;\n    .locals 10\n\n    .line 1\n    iget-object v0, p0, Lph/i;->b:Ljava/io/BufferedWriter;'''
    bnew='''.method public final b(Ljava/lang/String;Lph/s;)Lph/g;\n    .locals 10\n\n    iget-boolean v0, p0, Lph/i;->shizuku:Z\n    if-eqz v0, :dw_fifo_transport\n    iget-boolean v0, p0, Lph/i;->f:Z\n    if-nez v0, :dw_shizuku_closed\n    iget-boolean v0, p0, Lph/i;->e:Z\n    if-nez v0, :dw_shizuku_busy\n\n    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuBridge;->startCommand(Ljava/lang/String;)Ljava/lang/Process;\n    move-result-object v8\n    if-nez v8, :dw_shizuku_started\n    new-instance v0, Lph/h;\n    invoke-direct {v0}, Lph/h;-><init>()V\n    throw v0\n\n    :dw_shizuku_started\n    new-instance v7, Ljava/lang/StringBuffer;\n    invoke-direct {v7}, Ljava/lang/StringBuffer;-><init>()V\n    invoke-virtual {v8}, Ljava/lang/Process;->getErrorStream()Ljava/io/InputStream;\n    move-result-object v0\n    new-instance v1, Ldw/filemanager/shizuku/ShizukuErrorDrainer;\n    invoke-direct {v1, v0, v7}, Ldw/filemanager/shizuku/ShizukuErrorDrainer;-><init>(Ljava/io/InputStream;Ljava/lang/StringBuffer;)V\n    new-instance v5, Ljava/lang/Thread;\n    invoke-direct {v5, v1}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V\n    invoke-virtual {v5}, Ljava/lang/Thread;->start()V\n    invoke-virtual {v8}, Ljava/lang/Process;->getInputStream()Ljava/io/InputStream;\n    move-result-object v4\n    const/4 v0, 0x1\n    iput-boolean v0, p0, Lph/i;->e:Z\n    new-instance v2, Lph/g;\n    move-object v3, p0\n    move-object v6, p2\n    invoke-direct/range {v2 .. v8}, Lph/g;-><init>(Lph/i;Ljava/io/InputStream;Ljava/lang/Thread;Lph/s;Ljava/lang/StringBuffer;Ljava/lang/Process;)V\n    return-object v2\n\n    :dw_shizuku_busy\n    const-string v0, "STDOUT InputStream from previous command execution was not closed prior to current command execution attempt."\n    invoke-static {v0}, Lhh/e;->q(Ljava/lang/String;)V\n    const/4 v0, 0x0\n    return-object v0\n\n    :dw_shizuku_closed\n    const-string v0, "InteractiveShell closed."\n    invoke-static {v0}, Lhh/e;->q(Ljava/lang/String;)V\n    const/4 v0, 0x0\n    return-object v0\n\n    :dw_fifo_transport\n    .line 1\n    iget-object v0, p0, Lph/i;->b:Ljava/io/BufferedWriter;'''
    if it.count(bhead)!=1: raise RuntimeError('ph/i b() head changed: '+str(it.count(bhead)))
    it=it.replace(bhead,bnew,1)

    # f(command, appLocalOutput) previously redirected the Shizuku shell directly
    # to an app-private pathname, which uid=shell also cannot create.  Stream the
    # remote stdout back through Binder and let the app process create its own file.
    fhead='''.method public final f(Ljava/lang/String;Ljava/lang/String;)V\n    .locals 3\n\n    .line 1\n    iget-object v0, p0, Lph/i;->b:Ljava/io/BufferedWriter;'''
    fnew='''.method public final f(Ljava/lang/String;Ljava/lang/String;)V\n    .locals 3\n\n    iget-boolean v0, p0, Lph/i;->shizuku:Z\n    if-eqz v0, :dw_f_fifo\n    invoke-static {p1, p2}, Ldw/filemanager/shizuku/ShizukuBridge;->copyCommandToFile(Ljava/lang/String;Ljava/lang/String;)V\n    return-void\n\n    :dw_f_fifo\n    .line 1\n    iget-object v0, p0, Lph/i;->b:Ljava/io/BufferedWriter;'''
    if it.count(fhead)!=1: raise RuntimeError('ph/i f() head changed: '+str(it.count(fhead)))
    it=it.replace(fhead,fnew,1)
    ip.write_text(it)

    # Extend ph/g with a direct-process mode.  It preserves the original close()
    # cleanup for FIFO-backed streams and performs process/error cleanup when the
    # stream came directly from Shizuku.
    gp=sm/'ph/g.smali'; gt=gp.read_text()
    if '.field public shizukuMode:Z' not in gt:
        anchor='.field public final synthetic i:Lph/s;\n'
        if gt.count(anchor)!=1: raise RuntimeError('ph/g field anchor changed')
        gt=gt.replace(anchor,anchor+'\n.field public shizukuMode:Z\n.field public shizukuProcess:Ljava/lang/Process;\n',1)
    alt=r'''
.method public constructor <init>(Lph/i;Ljava/io/InputStream;Ljava/lang/Thread;Lph/s;Ljava/lang/StringBuffer;Ljava/lang/Process;)V
    .locals 1
    iput-object p1, p0, Lph/g;->X1:Lph/i;
    iput-object p3, p0, Lph/g;->f:Ljava/lang/Thread;
    iput-object p4, p0, Lph/g;->i:Lph/s;
    iput-object p5, p0, Lph/g;->X:Ljava/lang/StringBuffer;
    const/4 v0, 0x0
    iput-object v0, p0, Lph/g;->Y:Ljava/io/File;
    iput-object v0, p0, Lph/g;->Z:Ljava/io/File;
    iput-object p6, p0, Lph/g;->shizukuProcess:Ljava/lang/Process;
    const/4 v0, 0x1
    iput-boolean v0, p0, Lph/g;->shizukuMode:Z
    invoke-direct {p0, p2}, Ljava/io/FilterInputStream;-><init>(Ljava/io/InputStream;)V
    return-void
.end method
'''
    if '<init>(Lph/i;Ljava/io/InputStream;Ljava/lang/Thread;Lph/s;Ljava/lang/StringBuffer;Ljava/lang/Process;)V' not in gt:
        pos=gt.index('\n\n# virtual methods')
        gt=gt[:pos]+'\n'+alt+gt[pos:]
    chead='''.method public final close()V\n    .locals 5\n\n    .line 1\n    iget-object v0, p0, Lph/g;->Z:Ljava/io/File;'''
    cnew='''.method public final close()V\n    .locals 5\n\n    iget-boolean v0, p0, Lph/g;->shizukuMode:Z\n    if-eqz v0, :dw_fifo_close\n    :try_start_dw\n    invoke-super {p0}, Ljava/io/FilterInputStream;->close()V\n    iget-object v0, p0, Lph/g;->shizukuProcess:Ljava/lang/Process;\n    if-eqz v0, :dw_no_process\n    invoke-virtual {v0}, Ljava/lang/Process;->waitFor()I\n    :dw_no_process\n    iget-object v0, p0, Lph/g;->f:Ljava/lang/Thread;\n    if-eqz v0, :dw_no_thread\n    invoke-virtual {v0}, Ljava/lang/Thread;->join()V\n    :dw_no_thread\n    iget-object v0, p0, Lph/g;->X1:Lph/i;\n    const/4 v1, 0x0\n    iput-boolean v1, v0, Lph/i;->e:Z\n    iget-object v0, p0, Lph/g;->X:Ljava/lang/StringBuffer;\n    invoke-virtual {v0}, Ljava/lang/StringBuffer;->toString()Ljava/lang/String;\n    move-result-object v1\n    invoke-virtual {v1}, Ljava/lang/String;->trim()Ljava/lang/String;\n    move-result-object v2\n    invoke-virtual {v2}, Ljava/lang/String;->isEmpty()Z\n    move-result v2\n    if-nez v2, :dw_direct_done\n    iget-object v2, p0, Lph/g;->i:Lph/s;\n    invoke-interface {v2, v1}, Lph/s;->q(Ljava/lang/String;)V\n    :dw_direct_done\n    return-void\n    :try_end_dw\n    .catchall {:try_start_dw .. :try_end_dw} :dw_direct_fail\n    :dw_direct_fail\n    move-exception v0\n    iget-object v1, p0, Lph/g;->X1:Lph/i;\n    const/4 v2, 0x0\n    iput-boolean v2, v1, Lph/i;->e:Z\n    iget-object v1, p0, Lph/g;->shizukuProcess:Ljava/lang/Process;\n    if-eqz v1, :dw_throw\n    invoke-virtual {v1}, Ljava/lang/Process;->destroy()V\n    :dw_throw\n    throw v0\n\n    :dw_fifo_close\n    .line 1\n    iget-object v0, p0, Lph/g;->Z:Ljava/io/File;'''
    if gt.count(chead)!=1: raise RuntimeError('ph/g close head changed: '+str(gt.count(chead)))
    gt=gt.replace(chead,cnew,1)
    gp.write_text(gt)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    final_i=ip.read_text(); final_g=gp.read_text(); final_b=bp.read_text()
    for tok in ('shizuku:Z','startCommand(Ljava/lang/String;)','copyCommandToFile','dw_fifo_transport'):
        if tok not in final_i+final_b: raise RuntimeError('direct Shizuku transport missing '+tok)
    for tok in ('shizukuMode:Z','shizukuProcess:Ljava/lang/Process;','dw_fifo_close'):
        if tok not in final_g: raise RuntimeError('ph/g Shizuku stream mode missing '+tok)
    print('stage21d replaced app-private FIFO transport with direct Binder streams for Shizuku only; real su/root transport preserved; vc='+VC)

if __name__=='__main__': main()
