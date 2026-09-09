#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109034'

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

    # Root cause found by decoding the exact 9109033 final APK: hc/e.F0(), the
    # actual Explorer System directory loader, invokes ph/r.z(context, READ_ONLY)
    # before the Shizuku-native list branch. ph/r.z is DW's legacy UID-0 root
    # authentication gate; when no su/root session has authenticated it throws
    # hh/l("Internal error") before ShizukuDirectoryLister can ever run.
    #
    # Authorized Shizuku is itself the authorization for shell-identity browsing.
    # Skip the root-authentication gate only when Shizuku is authorized. Genuine
    # root/su browsing keeps the original gate unchanged.
    ep=sm/'hc/e.smali'; et=ep.read_text()
    sig='.method public final F0(Landroid/content/Context;I)[Lkh/j;'
    s,e,m=method(et,sig)
    old='''    const/4 v2, 0x1\n\n    .line 12\n    invoke-static {v0, v2}, Lph/r;->z(Landroid/content/Context;I)V\n'''
    new='''    const/4 v2, 0x1\n\n    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z\n    move-result v4\n    if-nez v4, :dw_shizuku_root_auth_ok\n\n    .line 12\n    invoke-static {v0, v2}, Lph/r;->z(Landroid/content/Context;I)V\n\n    :dw_shizuku_root_auth_ok\n'''
    if m.count(old)!=1: raise RuntimeError('F0 root auth anchor count '+str(m.count(old)))
    m=m.replace(old,new,1)
    et=et[:s]+m+et[e:]; ep.write_text(et)

    # F0 may request per-item attribute initialization (flag bit 0). hc/i.a()
    # repeats the same legacy root-auth gate before checking whether metadata is
    # already present. In Shizuku mode, trust the native metadata returned by the
    # lister; if metadata is absent, stat it directly through Shizuku rather than
    # acquiring ShellCatalog/root.
    ip=sm/'hc/i.smali'; it=ip.read_text()
    sig='.method public final a(Landroid/content/Context;)V'
    s,e,m=method(it,sig)
    anchor='''    :cond_0\n    invoke-static {}, Lhf/p0;->i()Lbb/d;\n\n    .line 7\n    .line 8\n    .line 9\n    move-result-object v0\n\n    .line 10\n    iget-boolean v0, v0, Lbb/d;->Z:Z\n\n    .line 11\n    .line 12\n    if-nez v0, :cond_2\n\n    .line 13\n    .line 14\n    const/4 v0, 0x1\n\n    .line 15\n    invoke-static {p1, v0}, Lph/r;->z(Landroid/content/Context;I)V\n'''
    replacement='''    :cond_0\n    invoke-static {}, Lhf/p0;->i()Lbb/d;\n\n    .line 7\n    .line 8\n    .line 9\n    move-result-object v0\n\n    .line 10\n    iget-boolean v0, v0, Lbb/d;->Z:Z\n\n    .line 11\n    .line 12\n    if-nez v0, :cond_2\n\n    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z\n    move-result v0\n    if-eqz v0, :dw_legacy_item_auth\n\n    const/4 v0, 0x1\n    iget-object v1, p0, Lhc/i;->X:Lph/e;\n    if-nez v1, :dw_shizuku_item_ready\n    iget-object v1, p0, Lhc/i;->i:Lhh/f;\n    invoke-static {v1}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;\n    move-result-object v1\n    invoke-static {v1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->stat(Ljava/lang/String;)Lph/e;\n    move-result-object v1\n    iput-object v1, p0, Lhc/i;->X:Lph/e;\n    :dw_shizuku_item_ready\n    iput-boolean v0, p0, Lhc/i;->Z:Z\n    return-void\n\n    :dw_legacy_item_auth\n    .line 13\n    .line 14\n    const/4 v0, 0x1\n\n    .line 15\n    invoke-static {p1, v0}, Lph/r;->z(Landroid/content/Context;I)V\n'''
    if m.count(anchor)!=1: raise RuntimeError('hc/i.a root auth anchor count '+str(m.count(anchor)))
    m=m.replace(anchor,replacement,1)
    it=it[:s]+m+it[e:]

    # Any direct metadata lookup for System entries must also use Shizuku first.
    # This keeps subsequent Explorer operations from falling back into ShellCatalog
    # merely to stat an entry that shell UID can already stat.
    sig='.method public static U(Landroid/content/Context;Ljava/lang/String;)Lph/e;'
    s,e,m=method(it,sig)
    old='''    .locals 3\n\n    .line 1\n    const-string v0, "Error loading directory: "\n'''
    new='''    .locals 3\n\n    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z\n    move-result v0\n    if-eqz v0, :dw_legacy_stat_lookup\n    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->stat(Ljava/lang/String;)Lph/e;\n    move-result-object v0\n    return-object v0\n\n    :dw_legacy_stat_lookup\n    .line 1\n    const-string v0, "Error loading directory: "\n'''
    if m.count(old)!=1: raise RuntimeError('hc/i.U direct stat anchor count '+str(m.count(old)))
    m=m.replace(old,new,1)
    it=it[:s]+m+it[e:]; ip.write_text(it)

    # Make diagnostics explicitly expose the exact native filesystem lister, not
    # just generic Shizuku commands. This adds a tiny helper called by the existing
    # self-test so if anything remains wrong the device report identifies it.
    dp=sm/'dw/filemanager/shizuku/ShizukuDiagnosticActivity.smali'; dt=dp.read_text()
    sig='.method private perform()Ljava/lang/String;'
    s,e,m=method(dt,sig)
    # Insert before the final RESULT text append. We can safely use existing local
    # registers because this method already has a generous register frame.
    marker='''    const-string v1, "\\nRESULT: Review each line above. Any START_FAILED / nonzero rc identifies the exact failing Shizuku layer.\\n"\n'''
    probe='''    const-string v1, "/"\n    :try_start_dw_exact_lister\n    invoke-static {v1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;\n    move-result-object v1\n    const-string v2, "exact DW ShizukuDirectoryLister(/): count="\n    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    array-length v1, v1\n    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;\n    const/16 v1, 0xa\n    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;\n    :try_end_dw_exact_lister\n    .catch Ljava/lang/Throwable; {:try_start_dw_exact_lister .. :try_end_dw_exact_lister} :catch_dw_exact_lister\n    goto :dw_exact_lister_done\n    :catch_dw_exact_lister\n    move-exception v1\n    const-string v2, "exact DW ShizukuDirectoryLister(/): EXCEPTION :: "\n    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {v1}, Ljava/lang/Object;->getClass()Ljava/lang/Class;\n    move-result-object v2\n    invoke-virtual {v2}, Ljava/lang/Class;->getName()Ljava/lang/String;\n    move-result-object v2\n    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    const-string v2, " :: "\n    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {v1}, Ljava/lang/Throwable;->getMessage()Ljava/lang/String;\n    move-result-object v1\n    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    const/16 v1, 0xa\n    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;\n    :dw_exact_lister_done\n\n    const-string v1, "\\nRESULT: Review each line above. Any START_FAILED / nonzero rc identifies the exact failing Shizuku layer.\\n"\n'''
    if m.count(marker)!=1:
        # Self-test implementation may compile with a different register assignment;
        # don't break the build just for the extra diagnostic. Core auth fix remains.
        print('warning: exact-lister self-test marker not found; skipping UI probe')
    else:
        m=m.replace(marker,probe,1); dt=dt[:s]+m+dt[e:]; dp.write_text(dt)

    y=root/'apktool.yml'; yt=y.read_text()
    yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    # Static invariants: Shizuku authorization check must precede the legacy root
    # auth call in the actual Explorer loader; the legacy call remains as fallback.
    ft=ep.read_text(); _,_,fm=method(ft,'.method public final F0(Landroid/content/Context;I)[Lkh/j;')
    auth='ShizukuBridge;->isAuthorized()Z'; gate='Lph/r;->z(Landroid/content/Context;I)V'; direct='ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;'
    if auth not in fm or gate not in fm or direct not in fm: raise RuntimeError('F0 Shizuku/root-auth structure incomplete')
    if fm.index(auth) > fm.index(gate): raise RuntimeError('legacy root auth still executes before Shizuku authorization check')
    if 'dw_shizuku_root_auth_ok' not in fm: raise RuntimeError('F0 Shizuku auth bypass label missing')
    iout=ip.read_text()
    if 'dw_legacy_item_auth' not in iout or 'ShizukuDirectoryLister;->stat' not in iout: raise RuntimeError('per-item Shizuku auth/stat bypass missing')
    print('stage21k: Shizuku browsing now bypasses DW legacy root-auth gate in F0 + item metadata; vc='+VC)

if __name__=='__main__': main()
