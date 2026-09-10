#!/usr/bin/env python3
from pathlib import Path
import argparse,re

PACKAGE='com.mekromn.dwfilemanager'
VERSION_CODE='9109000'
VERSION_NAME='9.1.0.8'
TARGET_SDK='34'
LEGACY_COMPANION='nextapp.fx.rk'
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
    """Erase old feature-level companion decisions while retaining feature behavior.

    Stage02 historically rewrote vendor entitlement checks to Companion.present(Context).
    The modern DW fork no longer has a companion product dependency. Therefore every
    surviving feature path is normalized to the ordinary/available behavior directly,
    after which the Companion helper itself is deleted.
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

                lines[i]='    # obsolete companion check removed: DW feature is directly available'
                lines[j]='    # no companion result'

                if re.fullmatch(r'if-eqz\s+'+re.escape(reg)+r',\s*:[A-Za-z0-9_]+',use):
                    lines[k]='    # companion-missing skip removed: ordinary path always executes'
                    fallthrough+=1
                elif re.fullmatch(r'if-nez\s+'+re.escape(reg)+r',\s*:[A-Za-z0-9_]+',use):
                    label=use.split(',',1)[1].strip()
                    lines[k]=f'    goto {label}    # ordinary path; obsolete companion error branch bypassed'
                    direct_goto+=1
                elif re.fullmatch(r'sput-boolean\s+'+re.escape(reg)+r',\s*Ldw/filemanager/ext/ui/j;->a:Z',use):
                    # Preserve the existing home-model availability contract without deriving
                    # it from another APK.
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


def remove_companion_helper(root):
    helper=root/'smali/dw/filemanager/core/Companion.smali'
    if helper.exists():
        helper.unlink()
        return True
    # tolerate a future Stage02 that has already stopped creating it, but only if no call
    # sites remain after normalization.
    return False


def configure_visibility(root):
    """Remove the legacy companion package query.

    QUERY_ALL_PACKAGES remains because DW's Apps/package browsing is a separate retained
    feature and must not be coupled to the deleted companion requirement.
    """
    manifest=root/'AndroidManifest.xml'; mt=manifest.read_text()
    count=mt.count(LEGACY_COMPANION)
    if count > 1:
        raise RuntimeError(f'unexpected duplicate legacy companion manifest queries: {count}')
    if count == 1:
        mt,n=re.subn(r'\s*<package\s+android:name="'+re.escape(LEGACY_COMPANION)+r'"\s*/>\s*','\n',mt,count=1)
        if n!=1: raise RuntimeError('could not remove legacy companion package query')
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
    helper_deleted=remove_companion_helper(root)

    mt=(root/'AndroidManifest.xml').read_text()
    gms=list(root.glob('smali*/com/google/android/gms/**/*.smali'))
    if gms: raise RuntimeError('GMS classes remain: '+str([str(x.relative_to(root)) for x in gms[:10]]))

    literal_hits=[]; helper_calls=[]; helper_refs=[]; legacy=[]
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            txt=p.read_text(errors='ignore')
            c=txt.count(LEGACY_COMPANION)
            if c: literal_hits.append((str(p.relative_to(root)),c))
            c=txt.count(HELPER_CALL)
            if c: helper_calls.append((str(p.relative_to(root)),c))
            c=txt.count(HELPER_DESC)
            if c: helper_refs.append((str(p.relative_to(root)),c))
            if 'Llh/n;->j(Landroid/content/Context;)I' in txt or 'Llh/n;->l(Landroid/content/Context;)Z' in txt:
                legacy.append(str(p.relative_to(root)))
    for base in (root/'res',root/'assets'):
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            c=txt.count(LEGACY_COMPANION)
            if c: literal_hits.append((str(p.relative_to(root)),c))

    manifest_count=mt.count(LEGACY_COMPANION)
    total=sum(c for _,c in literal_hits)+manifest_count
    if total!=0:
        raise RuntimeError(f'legacy companion package literal must be physically absent; total={total}, hits={literal_hits}, manifest={manifest_count}')
    if helper_calls:
        raise RuntimeError('Companion.present call survived: '+str(helper_calls))
    if helper_refs:
        raise RuntimeError('Companion class reference survived: '+str(helper_refs))
    if (root/'smali/dw/filemanager/core/Companion.smali').exists():
        raise RuntimeError('obsolete Companion helper class survived')
    if legacy: raise RuntimeError('legacy companion/state checks remain: '+str(legacy[:20]))
    if mt.count(QUERY_PERMISSION)!=1:
        raise RuntimeError('QUERY_ALL_PACKAGES visibility permission must exist exactly once')

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
    print(f'stage10b normalized {removed} distributed legacy companion sites across {files} files: {fallthrough} ordinary fall-through, {direct_goto} direct ordinary jumps, {state_true} availability-state normalization')
    print(f'stage10b deleted obsolete Companion helper={helper_deleted}; FINAL companion literals=0 calls=0 refs=0')

if __name__=='__main__': main()
