#!/usr/bin/env python3
from pathlib import Path
import argparse,re

PACKAGE='com.mekromn.dwfilemanager'
VERSION_CODE='9109000'
VERSION_NAME='9.1.0.8'
TARGET_SDK='34'
COMPANION='nextapp.fx.rk'
HELPER_DESC='Ldw/filemanager/core/Companion;'
HELPER_CALL=HELPER_DESC+'->present(Landroid/content/Context;)Z'
QUERY_PERMISSION='android.permission.QUERY_ALL_PACKAGES'


def next_instruction(lines,start,limit=48):
    for i in range(start+1,min(len(lines),start+1+limit)):
        s=lines[i].strip()
        if not s or s.startswith('.line') or s.startswith('#'):
            continue
        return i,s
    return None,None


def find_first_register_use(lines,start,reg,limit=64):
    for i in range(start+1,min(len(lines),start+1+limit)):
        s=lines[i].strip()
        if not s or s.startswith('.line') or s.startswith('#'):
            continue
        if re.search(r'(?<![A-Za-z0-9_])'+re.escape(reg)+r'(?![A-Za-z0-9_])',s):
            return i,s
    return None,None


def normalize_distributed_companion_paths(root):
    """Erase every old feature-level companion decision.

    After the one process-wide startup gate succeeds, old companion-controlled code must
    take the ordinary/available path directly. We do not synthesize a companion boolean
    and leave conditional branches behind.
    """
    calls=0; files=0; fallthrough=0; direct_goto=0; state_true=0
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            lines=p.read_text(errors='ignore').splitlines()
            local=0; i=0
            while i < len(lines):
                if HELPER_CALL not in lines[i]:
                    i+=1; continue
                j,ins=next_instruction(lines,i)
                if j is None or not ins.startswith('move-result '):
                    raise RuntimeError(f'Companion.present without move-result: {p}:{i+1}')
                reg=ins.split()[-1]
                k,use=find_first_register_use(lines,j,reg)
                if k is None:
                    raise RuntimeError(f'cannot find first use of companion result {reg}: {p}:{j+1}')

                # Remove the call and move-result themselves in every feature path.
                lines[i]='    # distributed companion check removed: startup gate is authoritative'
                lines[j]='    # no per-feature companion result'

                if re.fullmatch(r'if-eqz\s+'+re.escape(reg)+r',\s*:[A-Za-z0-9_]+',use):
                    # Companion-present used to fall through into the real feature path.
                    # Delete the skip branch so ordinary execution always falls through.
                    lines[k]='    # companion-missing skip removed: ordinary path always executes'
                    fallthrough+=1
                elif re.fullmatch(r'if-nez\s+'+re.escape(reg)+r',\s*:[A-Za-z0-9_]+',use):
                    # Companion-present used to jump over an unavailable/error branch.
                    # Jump there directly; the unavailable branch is now unreachable.
                    label=use.split(',',1)[1].strip()
                    lines[k]=f'    goto {label}    # ordinary path; companion error branch bypassed'
                    direct_goto+=1
                elif re.fullmatch(r'sput-boolean\s+'+re.escape(reg)+r',\s*Ldw/filemanager/ext/ui/j;->a:Z',use):
                    # The old shared availability flag is no longer companion-derived.
                    # Keep the existing home-model contract but pin it to ordinary/available.
                    lines[i]=f'    const/4 {reg}, 0x1    # ordinary extension availability'
                    lines[k]=f'    sput-boolean {reg}, Ldw/filemanager/ext/ui/j;->a:Z'
                    state_true+=1
                else:
                    raise RuntimeError(f'unclassified companion-result use {use!r}: {p}:{k+1}')

                calls+=1; local+=1; i=max(j,k)+1
            if local:
                p.write_text('\n'.join(lines)+'\n'); files+=1
    if calls < 1:
        raise RuntimeError('expected distributed companion checks from Stage02, found none')
    if calls != fallthrough + direct_goto + state_true:
        raise RuntimeError('companion normalization accounting mismatch')
    return calls,files,fallthrough,direct_goto,state_true


def replace_helper_with_minimal_boolean(root):
    helper=root/'smali/dw/filemanager/core/Companion.smali'
    if not helper.exists(): raise RuntimeError('Stage02 Companion helper missing')
    helper.write_text(f'''.class public final Ldw/filemanager/core/Companion;\n.super Ljava/lang/Object;\n\n# The only companion check in DW. Package-name existence only.\n.method public static present(Landroid/content/Context;)Z\n    .locals 3\n\n    :try_start_dw\n    invoke-virtual {{p0}}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;\n    move-result-object v0\n\n    const-string v1, "{COMPANION}"\n    const/4 v2, 0x0\n    invoke-virtual {{v0, v1, v2}}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;\n\n    const/4 v0, 0x1\n    :try_end_dw\n    .catch Landroid/content/pm/PackageManager$NameNotFoundException; {{:try_start_dw .. :try_end_dw}} :missing\n    return v0\n\n    :missing\n    const/4 v0, 0x0\n    return v0\n.end method\n''')


def add_one_appwide_gate(root):
    app=root/'smali/dw/filemanager/DWApplication.smali'
    t=app.read_text()
    mm=re.search(r'(?m)^\.method[^\n]*\bonCreate\(\)V\s*$',t)
    if not mm: raise RuntimeError('DWApplication.onCreate method declaration not found')
    s=mm.start(); e=t.index('.end method',s)+len('.end method')
    m=t[s:e]
    decl=re.search(r'(?m)^\s*\.(locals|registers)\s+(\d+)\s*$',m)
    if not decl: raise RuntimeError('DWApplication.onCreate register declaration missing')
    kind=decl.group(1); count=int(decl.group(2))
    if kind=='locals' and count<1:
        m=m[:decl.start()]+'    .locals 1'+m[decl.end():]
    elif kind=='registers' and count<2:
        m=m[:decl.start()]+'    .registers 2'+m[decl.end():]
    decl2=re.search(r'(?m)^\s*\.(?:locals|registers)\s+\d+\s*\n',m)
    if not decl2: raise RuntimeError('DWApplication.onCreate register line not found after resize')
    gate='''\n    invoke-static {p0}, Ldw/filemanager/core/Companion;->present(Landroid/content/Context;)Z\n    move-result v0\n    if-nez v0, :dw_companion_ok\n\n    const/4 v0, 0x0\n    invoke-static {v0}, Ljava/lang/System;->exit(I)V\n    return-void\n\n    :dw_companion_ok\n'''
    m=m[:decl2.end()]+gate+m[decl2.end():]
    app.write_text(t[:s]+m+t[e:])


def configure_visibility(root):
    """Keep the companion package literal out of the manifest entirely."""
    manifest=root/'AndroidManifest.xml'; mt=manifest.read_text()
    if mt.count(COMPANION)!=1:
        raise RuntimeError(f'expected one legacy manifest companion query before final consolidation, got {mt.count(COMPANION)}')
    mt,n=re.subn(r'\s*<package\s+android:name="'+re.escape(COMPANION)+r'"\s*/>\s*','\n',mt,count=1)
    if n!=1: raise RuntimeError('could not remove companion package query')
    mt=re.sub(r'\s*<queries>\s*</queries>\s*','\n',mt)
    if QUERY_PERMISSION not in mt:
        pos=mt.find('>')+1
        mt=mt[:pos]+f'\n    <uses-permission android:name="{QUERY_PERMISSION}" />'+mt[pos:]
    manifest.write_text(mt)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    yml=root/'apktool.yml'; t=yml.read_text()
    t,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VERSION_CODE,t,count=1)
    if n!=1: raise RuntimeError('versionCode field not found')
    t,n=re.subn(r'(versionName:\s*)[^\n]+',r'\g<1>'+VERSION_NAME,t,count=1)
    if n!=1: raise RuntimeError('versionName field not found')
    t,n=re.subn(r'(targetSdkVersion:\s*)[^\n]+',r'\g<1>'+TARGET_SDK,t,count=1)
    if n!=1: raise RuntimeError('targetSdkVersion field not found')
    yml.write_text(t)

    manifest=root/'AndroidManifest.xml'; mt=manifest.read_text()
    if f'package="{PACKAGE}"' not in mt: raise RuntimeError('final package identity mismatch')
    if 'com.google.android.gms' in mt: raise RuntimeError('GMS manifest reference remains')

    configure_visibility(root)
    removed,files,fallthrough,direct_goto,state_true=normalize_distributed_companion_paths(root)
    replace_helper_with_minimal_boolean(root)
    add_one_appwide_gate(root)

    manifest=root/'AndroidManifest.xml'; mt=manifest.read_text()
    gms=list(root.glob('smali*/com/google/android/gms/**/*.smali'))
    if gms: raise RuntimeError('GMS classes remain: '+str([str(x.relative_to(root)) for x in gms[:10]]))

    literal_hits=[]; helper_calls=[]; legacy=[]
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            txt=p.read_text(errors='ignore')
            c=txt.count(COMPANION)
            if c: literal_hits.append((str(p.relative_to(root)),c))
            c=txt.count(HELPER_CALL)
            if c: helper_calls.append((str(p.relative_to(root)),c))
            if 'Llh/n;->j(Landroid/content/Context;)I' in txt or 'Llh/n;->l(Landroid/content/Context;)Z' in txt:
                legacy.append(str(p.relative_to(root)))
    for base in (root/'res',root/'assets'):
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            c=txt.count(COMPANION)
            if c: literal_hits.append((str(p.relative_to(root)),c))
    manifest_count=mt.count(COMPANION)
    total=sum(c for _,c in literal_hits)+manifest_count
    if total!=1 or literal_hits!=[('smali/dw/filemanager/core/Companion.smali',1)] or manifest_count!=0:
        raise RuntimeError(f'exactly one companion package literal required total; total={total}, hits={literal_hits}, manifest={manifest_count}')
    if helper_calls != [('smali/dw/filemanager/DWApplication.smali',1)]:
        raise RuntimeError('Companion.present must have exactly one caller, DWApplication.onCreate: '+str(helper_calls))
    if legacy: raise RuntimeError('legacy companion/state checks remain: '+str(legacy[:20]))
    if mt.count(QUERY_PERMISSION)!=1:
        raise RuntimeError('QUERY_ALL_PACKAGES visibility permission must exist exactly once')

    h=(root/'smali/dw/filemanager/core/Companion.smali').read_text()
    banned=('MessageDigest','Base64','signatures','versionCode','installer','SharedPreferences','Broadcast','http://','https://','getInstalledPackages','getInstalledApplications','queryIntentActivities')
    bad=[x for x in banned if x in h]
    if bad: raise RuntimeError('minimal companion helper contains forbidden logic: '+str(bad))
    if h.count('getPackageInfo(Ljava/lang/String;I)')!=1: raise RuntimeError('minimal helper must perform exactly one package lookup')
    if h.count('const-string v1, "'+COMPANION+'"')!=1: raise RuntimeError('minimal helper must contain sole package literal exactly once')

    # No feature-level companion conditional may survive Stage10b.
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            if p == root/'smali/dw/filemanager/DWApplication.smali':
                continue
            txt=p.read_text(errors='ignore')
            if HELPER_CALL in txt:
                raise RuntimeError('feature-level companion call survived: '+str(p.relative_to(root)))

    fx=[]
    for base in (root/'smali',root/'res',root/'assets'):
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            if 'fxconfig' in txt.lower(): fx.append(str(p.relative_to(root)))
    if fx: raise RuntimeError('legacy fxconfig remains: '+str(fx[:20]))
    mime=(root/'smali/ab/k.smali').read_text(); export=(root/'smali/rf/a.smali').read_text()
    if mime.count('const-string v6, "dwconfig"')!=1: raise RuntimeError('dwconfig MIME mapping missing/duplicated')
    if export.count('const-string v0, ".dwconfig"')!=1: raise RuntimeError('dwconfig export extension missing/duplicated')
    if export.count('const-string v3, "DW_"')!=1: raise RuntimeError('DW_ export prefix missing/duplicated')

    print(f'stage10b release identity frozen: {PACKAGE} vc={VERSION_CODE} vn={VERSION_NAME} target={TARGET_SDK}')
    print(f'stage10b normalized {removed} distributed companion sites across {files} files: {fallthrough} ordinary fall-through, {direct_goto} direct ordinary jumps, {state_true} availability-state normalization')
    print('stage10b FINAL companion design: ONE app-wide caller; ONE getPackageInfo(name,0); ONE package literal total; ALL former companion branches are ordinary paths')

if __name__=='__main__': main()
