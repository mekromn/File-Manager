#!/usr/bin/env python3
from pathlib import Path
import argparse,re

PACKAGE='com.mekromn.dwfilemanager'
VERSION_CODE='9109000'
VERSION_NAME='9.1.0.8-DW'
TARGET_SDK='34'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    # Freeze release metadata instead of inheriting accidental stage/build values.
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
    if mt.count('nextapp.fx.rk')!=1: raise RuntimeError(f'package visibility companion literal count={mt.count("nextapp.fx.rk")}')

    gms=list(root.glob('smali*/com/google/android/gms/**/*.smali'))
    if gms: raise RuntimeError('GMS classes remain: '+str([str(x.relative_to(root)) for x in gms[:10]]))

    # Companion package literal is permitted only once in code plus once in manifest query.
    code_hits=[]
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            txt=p.read_text(errors='ignore')
            if 'nextapp.fx.rk' in txt: code_hits.append((str(p.relative_to(root)),txt.count('nextapp.fx.rk')))
    if sum(c for _,c in code_hits)!=1 or len(code_hits)!=1:
        raise RuntimeError('companion code literal must occur exactly once: '+str(code_hits))
    if code_hits[0][0] != 'smali/dw/filemanager/core/Companion.smali':
        raise RuntimeError('companion literal escaped pure helper: '+str(code_hits))

    fx=[]
    for base in (root/'smali',root/'res',root/'assets'):
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            if 'fxconfig' in txt.lower(): fx.append(str(p.relative_to(root)))
    if fx: raise RuntimeError('legacy fxconfig remains: '+str(fx[:20]))

    mime=(root/'smali/ab/k.smali').read_text()
    export=(root/'smali/rf/a.smali').read_text()
    if mime.count('const-string v6, "dwconfig"')!=1: raise RuntimeError('dwconfig MIME mapping missing/duplicated')
    if export.count('const-string v0, ".dwconfig"')!=1: raise RuntimeError('dwconfig export extension missing/duplicated')
    if export.count('const-string v3, "DW_"')!=1: raise RuntimeError('DW_ export prefix missing/duplicated')

    print(f'stage10b release identity frozen: {PACKAGE} vc={VERSION_CODE} vn={VERSION_NAME} target={TARGET_SDK}')
    print(f'stage10b zero GMS classes; companion literal isolated to {code_hits[0][0]} + manifest query; dwconfig-only passed')

if __name__=='__main__': main()
