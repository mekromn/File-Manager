#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109037'

def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing method end '+sig)
    e+=len('\n.end method')
    return s,e,text[s:e]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'; svc=sm/'dw/filemanager/shizuku/DwShizukuFsService.smali'
    t=svc.read_text()

    # Shizuku running from wireless debugging is UID 2000 (shell), not UID 0.
    # Android deliberately denies readdir() on some parents such as /data even
    # though shell may traverse them and stat/open specific descendants. The
    # device diagnostics proved exactly this: / and /data/local/tmp enumerate,
    # while /data itself returns EACCES. Do not misclassify that as a broken
    # Shizuku backend. For a small set of Android framework parents, provide a
    # best-effort candidate list and let the existing row()/lstat loop retain
    # only children that actually exist and are stat-able under the Shizuku UID.
    # This preserves security boundaries and never fabricates a successful file.
    helper=r'''
.method private static knownProtectedChildren(Ljava/lang/String;)[Ljava/lang/String;
    .locals 4

    const-string v0, "/data"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :data
    const-string v1, "/data/"
    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :local_check

    :data
    const/16 v0, 0x20
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "app"
    aput-object v2, v0, v1
    const/4 v1, 0x1
    const-string v2, "data"
    aput-object v2, v0, v1
    const/4 v1, 0x2
    const-string v2, "user"
    aput-object v2, v0, v1
    const/4 v1, 0x3
    const-string v2, "user_de"
    aput-object v2, v0, v1
    const/4 v1, 0x4
    const-string v2, "system"
    aput-object v2, v0, v1
    const/4 v1, 0x5
    const-string v2, "system_ce"
    aput-object v2, v0, v1
    const/4 v1, 0x6
    const-string v2, "system_de"
    aput-object v2, v0, v1
    const/4 v1, 0x7
    const-string v2, "local"
    aput-object v2, v0, v1
    const/16 v1, 0x8
    const-string v2, "media"
    aput-object v2, v0, v1
    const/16 v1, 0x9
    const-string v2, "app-lib"
    aput-object v2, v0, v1
    const/16 v1, 0xa
    const-string v2, "app-asec"
    aput-object v2, v0, v1
    const/16 v1, 0xb
    const-string v2, "app-private"
    aput-object v2, v0, v1
    const/16 v1, 0xc
    const-string v2, "anr"
    aput-object v2, v0, v1
    const/16 v1, 0xd
    const-string v2, "misc"
    aput-object v2, v0, v1
    const/16 v1, 0xe
    const-string v2, "misc_ce"
    aput-object v2, v0, v1
    const/16 v1, 0xf
    const-string v2, "misc_de"
    aput-object v2, v0, v1
    const/16 v1, 0x10
    const-string v2, "vendor"
    aput-object v2, v0, v1
    const/16 v1, 0x11
    const-string v2, "property"
    aput-object v2, v0, v1
    const/16 v1, 0x12
    const-string v2, "tombstones"
    aput-object v2, v0, v1
    const/16 v1, 0x13
    const-string v2, "resource-cache"
    aput-object v2, v0, v1
    const/16 v1, 0x14
    const-string v2, "backup"
    aput-object v2, v0, v1
    const/16 v1, 0x15
    const-string v2, "cache"
    aput-object v2, v0, v1
    const/16 v1, 0x16
    const-string v2, "dalvik-cache"
    aput-object v2, v0, v1
    const/16 v1, 0x17
    const-string v2, "ss"
    aput-object v2, v0, v1
    const/16 v1, 0x18
    const-string v2, "apex"
    aput-object v2, v0, v1
    const/16 v1, 0x19
    const-string v2, "nativetest"
    aput-object v2, v0, v1
    const/16 v1, 0x1a
    const-string v2, "nativetest64"
    aput-object v2, v0, v1
    const/16 v1, 0x1b
    const-string v2, "preloads"
    aput-object v2, v0, v1
    const/16 v1, 0x1c
    const-string v2, "rollback"
    aput-object v2, v0, v1
    const/16 v1, 0x1d
    const-string v2, "adb"
    aput-object v2, v0, v1
    const/16 v1, 0x1e
    const-string v2, "bootchart"
    aput-object v2, v0, v1
    const/16 v1, 0x1f
    const-string v2, "per_boot"
    aput-object v2, v0, v1
    return-object v0

    :local_check
    const-string v0, "/data/local"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :local
    const-string v1, "/data/local/"
    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :user_check
    :local
    const/4 v0, 0x3
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "tmp"
    aput-object v2, v0, v1
    const/4 v1, 0x1
    const-string v2, "tests"
    aput-object v2, v0, v1
    const/4 v1, 0x2
    const-string v2, "traces"
    aput-object v2, v0, v1
    return-object v0

    :user_check
    const-string v0, "/data/user"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :user0
    const-string v0, "/data/user/"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :user0
    const-string v0, "/data/user_de"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :user0
    const-string v0, "/data/user_de/"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :none
    :user0
    const/4 v0, 0x1
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "0"
    aput-object v2, v0, v1
    return-object v0

    :none
    const/4 v0, 0x0
    return-object v0
.end method
'''
    if 'knownProtectedChildren(Ljava/lang/String;)[Ljava/lang/String;' in t:
        raise RuntimeError('knownProtectedChildren already exists')
    insert=t.find('.method private static listInternal(Ljava/lang/String;)[Ljava/lang/String;')
    if insert<0: raise RuntimeError('listInternal missing')
    t=t[:insert]+helper+'\n'+t[insert:]

    # If Java File.list() was denied, ask for the bounded known-child probe. The
    # existing row() loop uses Os.lstat() and silently drops candidates that do
    # not exist or are not stat-able, so returned entries remain truthful.
    old='''    invoke-virtual {v1}, Ljava/io/File;->list()[Ljava/lang/String;\n\n    move-result-object v2\n\n    .line 59\n    if-eqz v2, :cond_6\n'''
    new='''    invoke-virtual {v1}, Ljava/io/File;->list()[Ljava/lang/String;\n\n    move-result-object v2\n\n    if-nez v2, :dw_names_ready\n    invoke-static {p0}, Ldw/filemanager/shizuku/DwShizukuFsService;->knownProtectedChildren(Ljava/lang/String;)[Ljava/lang/String;\n    move-result-object v2\n    :dw_names_ready\n\n    .line 59\n    if-eqz v2, :cond_6\n'''
    if t.count(old)!=1: raise RuntimeError('listInternal File.list anchor count '+str(t.count(old)))
    t=t.replace(old,new,1)
    svc.write_text(t)

    # Expand the end-to-end probe to include the exact protected parent that
    # failed on-device, so the next diagnostic proves whether the fallback path
    # is active and how many stat-able entries it yields.
    pp=sm/'dw/filemanager/shizuku/DwFsPipelineProbe.smali'; pt=pp.read_text()
    # Java compilation emitted the path array in <perform>; simply add /data by
    # replacing the two-element allocation with three elements and a third store.
    anchor='''    const/4 v6, 0x2\n\n    new-array v6, v6, [Ljava/lang/String;'''
    if anchor in pt:
        pt=pt.replace(anchor,'''    const/4 v6, 0x3\n\n    new-array v6, v6, [Ljava/lang/String;''',1)
        store='''    const/4 v7, 0x1\n\n    const-string v8, "/data/local/tmp"\n\n    aput-object v8, v6, v7\n'''
        if store in pt:
            pt=pt.replace(store,store+'''\n    const/4 v7, 0x2\n\n    const-string v8, "/data"\n\n    aput-object v8, v6, v7\n''',1)
    pp.write_text(pt)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    out=svc.read_text()
    if 'knownProtectedChildren' not in out or ':dw_names_ready' not in out:
        raise RuntimeError('protected-parent Shizuku fallback missing after patch')
    print('stage21n: Shizuku shell protected-parent best-effort enumeration installed; /data uses stat-probed Android child candidates; vc='+VC)

if __name__=='__main__': main()
