#!/usr/bin/env python3
from pathlib import Path
import argparse,re

PACKAGE='com.mekromn.dwfilemanager'
VERSION_CODE='9109000'
VERSION_NAME='9.1.0.8'
TARGET_SDK='34'
COMPANION='nextapp.fx.rk'
RESOURCE_NAME='dw_companion_package'
HELPER_DESC='Ldw/filemanager/core/Companion;'
HELPER_CALL=HELPER_DESC+'->present(Landroid/content/Context;)Z'

def next_instruction(lines,start):
    for i in range(start+1,min(len(lines),start+12)):
        s=lines[i].strip()
        if not s or s.startswith('.line') or s.startswith('#'):
            continue
        return i,s
    return None,None

def flatten_distributed_checks(root):
    calls=0; files=0
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
                lines[i]=f'    const/4 {reg}, 0x1'
                lines[j]='    # old distributed companion gate removed; process startup gate already passed'
                calls+=1; local+=1; i=j+1
            if local:
                p.write_text('\n'.join(lines)+'\n'); files+=1
    if calls < 1:
        raise RuntimeError('expected distributed companion checks from Stage02, found none')
    return calls,files

def allocate_string_resource(root):
    strings=root/'res/values/strings.xml'; st=strings.read_text()
    if RESOURCE_NAME in st: raise RuntimeError('companion package resource already exists')
    st=st.replace('</resources>',f'    <string name="{RESOURCE_NAME}" translatable="false">{COMPANION}</string>\n</resources>',1)
    strings.write_text(st)

    public=root/'res/values/public.xml'; pt=public.read_text()
    ids=[int(m.group(1),16) for m in re.finditer(r'<public type="string" name="[^"]+" id="(0x[0-9a-fA-F]+)"\s*/>',pt)]
    if not ids: raise RuntimeError('no public string ids found')
    prefix=ids[0] & 0xffff0000
    if any((x & 0xffff0000)!=prefix for x in ids): raise RuntimeError('string resource id type prefix inconsistent')
    rid=max(ids)+1
    if (rid & 0xffff0000)!=prefix or (rid & 0xffff)==0: raise RuntimeError('no safe next public string id')
    all_ids={int(x,16) for x in re.findall(r'id="(0x[0-9a-fA-F]+)"',pt)}
    if rid in all_ids: raise RuntimeError('chosen companion resource id already used')
    pt=pt.replace('</resources>',f'    <public type="string" name="{RESOURCE_NAME}" id="0x{rid:08x}" />\n</resources>',1)
    public.write_text(pt)
    return rid

def replace_helper_with_minimal_boolean(root,rid):
    helper=root/'smali/dw/filemanager/core/Companion.smali'
    if not helper.exists(): raise RuntimeError('Stage02 Companion helper missing')
    helper.write_text(f'''.class public final Ldw/filemanager/core/Companion;\n.super Ljava/lang/Object;\n\n# The only companion check in DW. Package name only.\n.method public static present(Landroid/content/Context;)Z\n    .locals 3\n\n    :try_start_dw\n    invoke-virtual {{p0}}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;\n    move-result-object v0\n\n    const v1, 0x{rid:08x}\n    invoke-virtual {{p0, v1}}, Landroid/content/Context;->getString(I)Ljava/lang/String;\n    move-result-object v1\n\n    const/4 v2, 0x0\n    invoke-virtual {{v0, v1, v2}}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;\n\n    const/4 v0, 0x1\n    :try_end_dw\n    .catch Landroid/content/pm/PackageManager$NameNotFoundException; {{:try_start_dw .. :try_end_dw}} :missing\n    return v0\n\n    :missing\n    const/4 v0, 0x0\n    return v0\n.end method\n''')

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

    if mt.count(COMPANION)!=1: raise RuntimeError(f'pre-consolidation manifest companion literal count={mt.count(COMPANION)}')
    rid=allocate_string_resource(root)
    mt=mt.replace(f'android:name="{COMPANION}"',f'android:name="@string/{RESOURCE_NAME}"',1)
    manifest.write_text(mt)

    removed,files=flatten_distributed_checks(root)
    replace_helper_with_minimal_boolean(root,rid)
    add_one_appwide_gate(root)

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
    manifest_count=manifest.read_text(errors='ignore').count(COMPANION)
    total=sum(c for _,c in literal_hits)+manifest_count
    if total!=1 or literal_hits!=[('res/values/strings.xml',1)] or manifest_count!=0:
        raise RuntimeError(f'exactly one companion package literal required total; total={total}, hits={literal_hits}, manifest={manifest_count}')
    if helper_calls != [('smali/dw/filemanager/DWApplication.smali',1)]:
        raise RuntimeError('Companion.present must have exactly one caller, DWApplication.onCreate: '+str(helper_calls))
    if legacy: raise RuntimeError('legacy companion/state checks remain: '+str(legacy[:20]))

    h=(root/'smali/dw/filemanager/core/Companion.smali').read_text()
    banned=('MessageDigest','Base64','signatures','versionCode','installer','SharedPreferences','Broadcast','http://','https://')
    bad=[x for x in banned if x in h]
    if bad: raise RuntimeError('minimal companion helper contains forbidden logic: '+str(bad))
    if h.count('getPackageInfo(Ljava/lang/String;I)')!=1: raise RuntimeError('minimal helper must perform exactly one package lookup')

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
    print(f'stage10b removed {removed} distributed companion checks across {files} files')
    print('stage10b FINAL companion design: ONE app-wide caller; helper does ONE package-name lookup only; ONE package-name literal total')

if __name__=='__main__': main()
