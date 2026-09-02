#!/usr/bin/env python3
from pathlib import Path
import argparse,re

PACKAGE='com.mekromn.dwfilemanager'
VERSION_CODE='9109000'
VERSION_NAME='9.1.0.8-DW'
TARGET_SDK='34'
COMPANION='nextapp.fx.rk'
RESOURCE_NAME='dw_companion_package'

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

    # One companion package literal total. Store it once as a private string resource;
    # both the manifest visibility declaration and pure boolean helper resolve it.
    strings=root/'res/values/strings.xml'; st=strings.read_text()
    if f'name="{RESOURCE_NAME}"' in st:
        raise RuntimeError('companion resource unexpectedly exists before Stage10b')
    insert=f'    <string name="{RESOURCE_NAME}" translatable="false">{COMPANION}</string>\n'
    pos=st.index('>')+1
    strings.write_text(st[:pos]+'\n'+insert+st[pos:])

    manifest=root/'AndroidManifest.xml'; mt=manifest.read_text()
    if f'package="{PACKAGE}"' not in mt: raise RuntimeError('final package identity mismatch')
    if 'com.google.android.gms' in mt: raise RuntimeError('GMS manifest reference remains')
    if mt.count(COMPANION)!=1: raise RuntimeError(f'pre-consolidation manifest companion literal count={mt.count(COMPANION)}')
    mt=mt.replace(f'android:name="{COMPANION}"',f'android:name="@string/{RESOURCE_NAME}"',1)
    manifest.write_text(mt)

    helper=root/'smali/dw/filemanager/core/Companion.smali'; ht=helper.read_text()
    old='''    const-string v1, "nextapp.fx.rk"\n    const/16 v2, 0x40\n    invoke-virtual {v0, v1, v2}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;\n'''
    new='''    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;\n    move-result-object v1\n\n    const-string v2, "dw_companion_package"\n    const-string v3, "string"\n    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;\n    move-result-object v4\n    invoke-virtual {v1, v2, v3, v4}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I\n    move-result v1\n    if-eqz v1, :missing\n\n    invoke-virtual {p0, v1}, Landroid/content/Context;->getString(I)Ljava/lang/String;\n    move-result-object v1\n\n    const/16 v2, 0x40\n    invoke-virtual {v0, v1, v2}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;\n'''
    if ht.count(old)!=1: raise RuntimeError('Companion helper literal lookup shape changed')
    helper.write_text(ht.replace(old,new,1))

    gms=list(root.glob('smali*/com/google/android/gms/**/*.smali'))
    if gms: raise RuntimeError('GMS classes remain: '+str([str(x.relative_to(root)) for x in gms[:10]]))

    # Enforce exactly ONE literal occurrence across the packaged app tree.
    literal_hits=[]
    for base in (root/'smali',root/'res',root/'assets'):
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            c=txt.count(COMPANION)
            if c: literal_hits.append((str(p.relative_to(root)),c))
    manifest_count=manifest.read_text(errors='ignore').count(COMPANION)
    total=sum(c for _,c in literal_hits)+manifest_count
    if total!=1:
        raise RuntimeError(f'companion package literal must occur exactly once total; total={total}, hits={literal_hits}, manifest={manifest_count}')
    if literal_hits != [('res/values/strings.xml',1)]:
        raise RuntimeError('sole companion literal must live only in default strings.xml: '+str(literal_hits))
    if f'android:name="@string/{RESOURCE_NAME}"' not in manifest.read_text():
        raise RuntimeError('manifest companion visibility does not reference sole resource')
    h=helper.read_text()
    if f'const-string v2, "{RESOURCE_NAME}"' not in h or COMPANION in h:
        raise RuntimeError('Companion helper does not resolve sole resource correctly')

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
    print('stage10b zero GMS classes; EXACTLY ONE companion package literal total via shared private resource; dwconfig-only passed')

if __name__=='__main__': main()
