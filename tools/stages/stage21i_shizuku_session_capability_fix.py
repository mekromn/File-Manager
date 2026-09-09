#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109032'

def replace_method(text,sig,new_method):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing method end '+sig)
    e+=len('\n.end method')
    return text[:s]+new_method+text[e:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # Device evidence from 9109030 is decisive: one-shot Shizuku newProcess()
    # works as uid=shell for id, / listing, /data/local/tmp read/write, and stat.
    # 9109031 still failed before its Shizuku-native directory branch because
    # ph/i only marks a root session `shizuku=true` after startShell() returns a
    # Process.  That bootstrap used a long-lived remote interactive shell, which
    # is unnecessary and is a different execution mode from the proven working
    # one-shot path.
    #
    # Make startShell() a *capability marker/bootstrap only*: when Shizuku is
    # authorized, return a harmless local /system/bin/sh Process so inherited DW
    # stream fields can be initialized and ph/i sets shizuku=true. All privileged
    # operations on such a session are already intercepted by stage21d/21h and
    # run through ShizukuBridge.startCommand() one-shot Binder processes. Thus no
    # directory access depends on su, app-private FIFOs, app-private BusyBox, or a
    # remote interactive shell. With no Shizuku grant, return null so DW retains
    # its original genuine-root/su fallback.
    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'; bt=bp.read_text()
    sig='.method public static startShell(Landroid/content/Context;)Ljava/lang/Process;'
    new=r'''.method public static startShell(Landroid/content/Context;)Ljava/lang/Process;
    .locals 3

    :try_start
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :none

    invoke-static {}, Ljava/lang/Runtime;->getRuntime()Ljava/lang/Runtime;
    move-result-object v0
    const-string v1, "/system/bin/sh"
    invoke-virtual {v0, v1}, Ljava/lang/Runtime;->exec(Ljava/lang/String;)Ljava/lang/Process;
    move-result-object v0
    return-object v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :none

    :none
    const/4 v0, 0x0
    return-object v0
.end method'''
    bt=replace_method(bt,sig,new); bp.write_text(bt)

    # Assert the actual root-session constructor still marks the session as
    # Shizuku when startShell() returns non-null, and that stage21h really routes
    # list/stat through its native Shizuku backend. These checks make a future
    # replay fail rather than silently regress to legacy su/BusyBox behavior.
    ip=sm/'ph/i.smali'; it=ip.read_text()
    for tok in (
        'ShizukuBridge;->startShell(Landroid/content/Context;)Ljava/lang/Process;',
        'iput-boolean v5, p0, Lph/i;->shizuku:Z'):
        if tok not in it: raise RuntimeError('ph/i Shizuku session marker missing '+tok)

    np=sm/'ph/n.smali'; nt=np.read_text()
    for tok in ('ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;',
                'ShizukuDirectoryLister;->stat(Ljava/lang/String;)Lph/e;'):
        if tok not in nt: raise RuntimeError('Shizuku-native filesystem route missing '+tok)

    # Verify the manifest integration is present in the same final decoded tree.
    # The build must not proceed if any required Shizuku client declaration is
    # absent. This answers the manifest question with a hard build-time gate.
    manifest=(root/'AndroidManifest.xml').read_text()
    for tok in ('moe.shizuku.manager.permission.API_V23',
                'moe.shizuku.client.V3_SUPPORT',
                'rikka.shizuku.ShizukuProvider',
                'com.mekromn.dwfilemanager.shizuku'):
        if tok not in manifest: raise RuntimeError('required Shizuku manifest declaration missing: '+tok)

    # Keep diagnostics semantically clear: a failed UID-0 test is not a failed
    # Shizuku capability test.
    strings=root/'res/values/strings.xml'; x=strings.read_text()
    x=x.replace('<string name="root_diag_test_result">Legacy su Root Shell Test</string>',
                '<string name="root_diag_test_result">Legacy UID-0 Root Test (Shizuku is separate)</string>')
    strings.write_text(x)

    y=root/'apktool.yml'; yt=y.read_text()
    yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    finalb=bp.read_text()
    if 'Runtime;->exec(Ljava/lang/String;)Ljava/lang/Process;' not in finalb:
        raise RuntimeError('local Shizuku session bootstrap missing')
    if 'ShizukuBridge;->isAuthorized()Z' not in finalb:
        raise RuntimeError('Shizuku authorization gate missing')
    print('stage21i: authorized Shizuku now marks DW root sessions without su or remote-interactive bootstrap; manifest hard-gated; vc='+VC)

if __name__=='__main__': main()
