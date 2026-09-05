#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109029'

def one(text, old, new, label):
    n=text.count(old)
    if n != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {n}')
    return text.replace(old,new,1)

def method_slice(text, sig):
    start=text.find(sig)
    if start < 0: raise RuntimeError('method not found: '+sig)
    end=text.find('\n.end method', start)
    if end < 0: raise RuntimeError('method end not found: '+sig)
    end += len('\n.end method')
    return start,end,text[start:end]

def patch_method(text,sig,old,new,label):
    start,end,m=method_slice(text,sig)
    m=one(m,old,new,label)
    return text[:start]+m+text[end:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # Use the Android shell by absolute path. Shizuku's remote process must not
    # depend on an inherited PATH; official rish ultimately executes
    # /system/bin/sh as well. This fixes a single common failure point used by
    # DW's internal System catalog, BusyBox staging, and the DocumentsProvider.
    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'
    bt=bp.read_text()
    n=bt.count('const-string v3, "sh"')
    if n != 2: raise RuntimeError(f'bridge v3 sh anchors: {n}')
    bt=bt.replace('const-string v3, "sh"','const-string v3, "/system/bin/sh"')
    n=bt.count('const-string v2, "sh"')
    if n != 1: raise RuntimeError(f'bridge v2 sh anchors: {n}')
    bt=bt.replace('const-string v2, "sh"','const-string v2, "/system/bin/sh"')
    bt=one(bt,'const-string v2, "exec sh 2>&1"','const-string v2, "exec /system/bin/sh 2>&1"','interactive shell exec')
    bp.write_text(bt)

    # Harden Android DocumentsUI's System (Shizuku) root.
    pp=sm/'dw/filemanager/provider/DwDocumentsProvider.smali'
    pt=pp.read_text()

    # toybox stat -c does not need C-style escape interpretation. Use a literal
    # field delimiter and split only the first three separators so filenames can
    # still contain the delimiter in the final field.
    pt=one(pt,'const-string v0, "\\\\t"','const-string v0, "\\\\|"','provider stat parser delimiter')
    n=pt.count('%A\\\\t%s\\\\t%Y\\\\t%n')
    if n != 2: raise RuntimeError(f'provider stat format anchors: {n}')
    pt=pt.replace('%A\\\\t%s\\\\t%Y\\\\t%n','%A|%s|%Y|%n')

    # Root-level find can legitimately encounter shell-inaccessible Android
    # nodes. Keep useful stdout instead of failing the entire DocumentsUI root
    # because one child produced a permission diagnostic / nonzero find status.
    old="const-string v0, \" -mindepth 1 -maxdepth 1 -exec /system/bin/toybox stat -c \\\'%A|%s|%Y|%n\\\' -- \\\'{}\\\' \\\';\\\'\""
    new="const-string v0, \" -mindepth 1 -maxdepth 1 -exec /system/bin/toybox stat -c \\\'%A|%s|%Y|%n\\\' -- \\\'{}\\\' \\\';\\\' 2>/dev/null || true\""
    pt=one(pt,old,new,'provider partial System listing')

    # System document IDs describe shell-visible absolute paths. Do not resolve
    # them with File.getCanonicalPath() in DW's ordinary app UID; doing so can
    # fail before the Shizuku shell ever sees a protected path. Main Storage
    # deliberately keeps canonical containment checks.
    sig='.method private static decode(Ljava/lang/String;)Ljava/lang/String;'
    s,e,m=method_slice(pt,sig)
    old='''    invoke-virtual {p0, v0}, Ljava/lang/String;->substring(I)Ljava/lang/String;\n\n    move-result-object p0\n\n    invoke-static {p0}, Ldw/filemanager/provider/DwDocumentsProvider;->canonical(Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object p0\n\n    .line 79\n    sget-object v0, Ljava/io/File;->separator:Ljava/lang/String;'''
    new='''    invoke-virtual {p0, v0}, Ljava/lang/String;->substring(I)Ljava/lang/String;\n\n    move-result-object p0\n\n    .line 79\n    sget-object v0, Ljava/io/File;->separator:Ljava/lang/String;'''
    m=one(m,old,new,'provider sys decode avoids app canonicalization')
    pt=pt[:s]+m+pt[e:]

    sig='.method private static encodeSys(Ljava/lang/String;)Ljava/lang/String;'
    s,e,m=method_slice(pt,sig)
    old='''    invoke-static {p0}, Ldw/filemanager/provider/DwDocumentsProvider;->canonical(Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object p0\n\n    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;'''
    new='''    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;'''
    m=one(m,old,new,'provider sys encode avoids app canonicalization')
    pt=pt[:s]+m+pt[e:]

    # Creation/rename still require canonicalization for Main Storage, but not
    # for a Shizuku System document. Add a tiny dispatcher so those operations
    # cannot regress protected-path browsing.
    helper=r'''
.method private static systemOrCanonical(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .locals 1
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/io/FileNotFoundException;
        }
    .end annotation

    invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->isSys(Ljava/lang/String;)Z
    move-result v0
    if-eqz v0, :main
    return-object p0
    :main
    invoke-static {p0}, Ldw/filemanager/provider/DwDocumentsProvider;->canonical(Ljava/lang/String;)Ljava/lang/String;
    move-result-object p0
    return-object p0
.end method
'''
    anchor='\n.method private static statSys(Ljava/lang/String;)Ldw/filemanager/provider/DwDocumentsProvider$Meta;'
    if anchor not in pt: raise RuntimeError('provider helper insertion anchor missing')
    pt=pt.replace(anchor,helper+anchor,1)

    pt=patch_method(pt,'.method public createDocument(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;',
        '    invoke-static {p3}, Ldw/filemanager/provider/DwDocumentsProvider;->canonical(Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object p3',
        '    invoke-static {p3, p1}, Ldw/filemanager/provider/DwDocumentsProvider;->systemOrCanonical(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object p3',
        'provider create System path')
    pt=patch_method(pt,'.method public renameDocument(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;',
        '    invoke-static {p2}, Ldw/filemanager/provider/DwDocumentsProvider;->canonical(Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object p2',
        '    invoke-static {p2, p1}, Ldw/filemanager/provider/DwDocumentsProvider;->systemOrCanonical(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object p2',
        'provider rename System path')
    pp.write_text(pt)

    y=root/'apktool.yml'; yt=y.read_text()
    yt2,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode anchor missing')
    y.write_text(yt2)
    print('Stage21f: absolute Shizuku shell + robust System provider browse applied; versionCode',VC)

if __name__=='__main__': main()
