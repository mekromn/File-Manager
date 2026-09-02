#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VERSION_CODE='9109001'

CRASH_LOG=r'''.class public final Ldw/filemanager/core/CrashLog;
.super Ljava/lang/Object;
.implements Ljava/lang/Thread$UncaughtExceptionHandler;

.field private final previous:Ljava/lang/Thread$UncaughtExceptionHandler;

.method private constructor <init>(Ljava/lang/Thread$UncaughtExceptionHandler;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Ldw/filemanager/core/CrashLog;->previous:Ljava/lang/Thread$UncaughtExceptionHandler;
    return-void
.end method

.method public static install(Landroid/content/Context;)V
    .locals 2
    invoke-static {}, Ljava/lang/Thread;->getDefaultUncaughtExceptionHandler()Ljava/lang/Thread$UncaughtExceptionHandler;
    move-result-object v0
    new-instance v1, Ldw/filemanager/core/CrashLog;
    invoke-direct {v1, v0}, Ldw/filemanager/core/CrashLog;-><init>(Ljava/lang/Thread$UncaughtExceptionHandler;)V
    invoke-static {v1}, Ljava/lang/Thread;->setDefaultUncaughtExceptionHandler(Ljava/lang/Thread$UncaughtExceptionHandler;)V
    return-void
.end method

.method public uncaughtException(Ljava/lang/Thread;Ljava/lang/Throwable;)V
    .locals 4

    const-string v0, "DWFileManager"
    const-string v1, "Uncaught exception"
    invoke-static {v0, v1, p2}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    :try_start_0
    new-instance v0, Ljava/io/FileWriter;
    const-string v1, "/storage/emulated/0/Download/DW-File-Manager-crash.txt"
    const/4 v2, 0x1
    invoke-direct {v0, v1, v2}, Ljava/io/FileWriter;-><init>(Ljava/lang/String;Z)V

    new-instance v1, Ljava/io/PrintWriter;
    invoke-direct {v1, v0}, Ljava/io/PrintWriter;-><init>(Ljava/io/Writer;)V

    const-string v2, "===== DW File Manager uncaught exception ====="
    invoke-virtual {v1, v2}, Ljava/io/PrintWriter;->println(Ljava/lang/String;)V
    invoke-virtual {p1}, Ljava/lang/Thread;->getName()Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v1, v2}, Ljava/io/PrintWriter;->println(Ljava/lang/String;)V
    invoke-virtual {p2, v1}, Ljava/lang/Throwable;->printStackTrace(Ljava/io/PrintWriter;)V
    invoke-virtual {v1}, Ljava/io/PrintWriter;->flush()V
    invoke-virtual {v1}, Ljava/io/PrintWriter;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :delegate

    :catch_0
    move-exception v0

    :delegate
    iget-object v0, p0, Ldw/filemanager/core/CrashLog;->previous:Ljava/lang/Thread$UncaughtExceptionHandler;
    if-eqz v0, :done
    invoke-interface {v0, p1, p2}, Ljava/lang/Thread$UncaughtExceptionHandler;->uncaughtException(Ljava/lang/Thread;Ljava/lang/Throwable;)V

    :done
    return-void
.end method
'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    # Higher version code so this repair candidate updates the installed 9109000 build.
    yml=root/'apktool.yml'; t=yml.read_text()
    t,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VERSION_CODE,t,count=1)
    if n!=1: raise RuntimeError('versionCode field not found for Stage11 diagnostic bump')
    yml.write_text(t)

    # Install a local-only uncaught-exception recorder after the sole companion startup gate.
    app=root/'smali/dw/filemanager/DWApplication.smali'; t=app.read_text()
    marker='    :dw_companion_ok\n'
    if t.count(marker)!=1: raise RuntimeError('sole startup companion gate marker missing/duplicated')
    install='    invoke-static {p0}, Ldw/filemanager/core/CrashLog;->install(Landroid/content/Context;)V\n\n'
    t=t.replace(marker,marker+install,1)
    app.write_text(t)

    crash=root/'smali/dw/filemanager/core/CrashLog.smali'
    crash.parent.mkdir(parents=True,exist_ok=True)
    crash.write_text(CRASH_LOG+'\n')

    # This diagnostic is explicitly local-only: no URL/socket/network APIs.
    h=crash.read_text()
    for banned in ('http://','https://','Ljava/net/','Lokhttp','Firebase','DataTransport'):
        if banned in h: raise RuntimeError('network/telemetry token in local crash recorder: '+banned)
    if h.count('/storage/emulated/0/Download/DW-File-Manager-crash.txt')!=1:
        raise RuntimeError('crash log path missing/duplicated')
    if app.read_text().count('CrashLog;->install')!=1:
        raise RuntimeError('CrashLog install must occur exactly once')

    print(f'stage11b local runtime diagnostic installed; repair candidate versionCode={VERSION_CODE}')

if __name__=='__main__': main()
