#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109033'

def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing end '+sig)
    return s,e,text[s:e]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # Device self-test proves Shizuku itself is healthy as uid=2000 and can list
    # /, list + write /data/local/tmp, and stat /.  The remaining failure happens
    # in DW's ShellCatalog acquisition before ph/n.e() can reach the Shizuku-native
    # list() branch.  Therefore do not acquire a legacy root/su session at all for
    # the normal directory-load path when Shizuku is authorized.
    #
    # hc/e.F0() is DW's concrete System filesystem directory enumerator used by
    # the Explorer UI.  Normal browsing calls it with flags 1/3, so the metrics
    # helpers that need a shell session are not involved.  For Shizuku, calculate
    # the requested path exactly as DW already does and feed it directly into the
    # first-class ShizukuDirectoryLister.  The old ShellCatalog/BusyBox/su block is
    # retained byte-for-byte as fallback when Shizuku is absent.
    p=sm/'hc/e.smali'; t=p.read_text()
    sig='.method public final F0(Landroid/content/Context;I)[Lkh/j;'
    s,e,m=method(t,sig)
    anchor='''    const/4 v11, 0x0\n\n    .line 60\n    if-nez v10, :cond_9\n\n    .line 61\n    .line 62\n    const-string v10, "Error loading directory: "'''
    replacement='''    const/4 v11, 0x0\n\n    .line 60\n    if-nez v10, :cond_9\n\n    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z\n    move-result v12\n    if-eqz v12, :dw_legacy_shell_directory_load\n\n    :try_start_dw_shizuku_directory_load\n    iget-object v12, v1, Lhc/i;->i:Lhh/f;\n    invoke-static {v12}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;\n    move-result-object v12\n    invoke-static {v12, v2}, Lab/o;->f(Ljava/lang/String;Z)Ljava/lang/String;\n    move-result-object v12\n    invoke-static {v12}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;\n    move-result-object v12\n    iput-object v12, v1, Lhc/e;->Z1:[Lph/e;\n    :try_end_dw_shizuku_directory_load\n    .catch Lph/o; {:try_start_dw_shizuku_directory_load .. :try_end_dw_shizuku_directory_load} :dw_shizuku_directory_load_error\n    goto :goto_a\n\n    :dw_shizuku_directory_load_error\n    move-exception v12\n    invoke-static {v11, v12, v1, v11}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;\n    move-result-object v12\n    throw v12\n\n    :dw_legacy_shell_directory_load\n    .line 61\n    .line 62\n    const-string v10, "Error loading directory: "'''
    if m.count(anchor)!=1: raise RuntimeError('hc/e F0 direct-list anchor count '+str(m.count(anchor)))
    m=m.replace(anchor,replacement,1)
    t=t[:s]+m+t[e:]
    p.write_text(t)

    # Make the settings wording match the architecture: the Shizuku browse path
    # does not use the bundled BusyBox or pretend to be uid-0 root.
    pref=root/'res/xml/pref_root.xml'; pt=pref.read_text()
    pt=pt.replace('Automatic: use Shizuku when available; keep real root/su as fallback',
                  'Shizuku-native filesystem when granted; real root/su is the fallback')
    pt=pt.replace('Shizuku-native filesystem when granted; real root/su is the fallback',
                  'Shizuku-native filesystem (Android toybox, no BusyBox/su); real root/su fallback')
    pref.write_text(pt)

    y=root/'apktool.yml'; yt=y.read_text()
    yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    # Hard proof: the direct Shizuku branch must occur before the first legacy
    # ShellCatalog acquisition in F0.  This prevents future replay stages from
    # silently putting Shizuku back behind the root-session gate.
    ft=p.read_text(); _,_,fm=method(ft,sig)
    direct='ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;'
    legacy='ShellCatalog;->l(Landroid/content/Context;)Lhc/f;'
    if direct not in fm: raise RuntimeError('direct Shizuku F0 list branch missing')
    if legacy not in fm: raise RuntimeError('legacy root fallback unexpectedly missing')
    if fm.index(direct) > fm.index(legacy): raise RuntimeError('Shizuku still gated behind ShellCatalog')
    if ':dw_legacy_shell_directory_load' not in fm: raise RuntimeError('explicit legacy fallback label missing')
    print('stage21j: Explorer System browsing now calls ShizukuDirectoryLister before any root/su/BusyBox session; vc='+VC)

if __name__=='__main__': main()
