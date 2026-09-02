#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,re,shutil

EXTERNAL='nextapp.fx.rk'
PLACE='__DW_EXTERNAL_COMPANION__'

TEXT_REPL=[
    ('Lnextapp/fx/plus/','Ldw/filemanager/ext/'),
    ('nextapp.fx.plus.','dw.filemanager.ext.'),
    ('Lnextapp/fx/FX;','Ldw/filemanager/DWApplication;'),
    ('nextapp.fx.FX','dw.filemanager.DWApplication'),
    ('Lnextapp/xf/shell/NativeFileAccess;','Ldw/filemanager/NativeFileAccess;'),
    ('nextapp.xf.shell.NativeFileAccess','dw.filemanager.NativeFileAccess'),
    ('Lnextapp/fx/','Ldw/filemanager/'),
    ('nextapp.fx.','dw.filemanager.'),
    ('Lnextapp/xf/','Ldw/filemanager/xf/'),
    ('nextapp.xf.','dw.filemanager.xf.'),
    ('Lnextapp/maui/','Ldw/filemanager/maui/'),
    ('nextapp.maui.','dw.filemanager.maui.'),
    ('Lnextapp/echo/','Ldw/filemanager/echo/'),
    ('nextapp.echo.','dw.filemanager.echo.'),
    ('Lnextapp/cat/annotation/','Ldw/filemanager/annotation/'),
    ('nextapp.cat.annotation.','dw.filemanager.annotation.'),
    ('Lcom/google/android/gms/internal/play_billing/','Ldw/filemanager/runtime/'),
    ('com.google.android.gms.internal.play_billing.','dw.filemanager.runtime.'),
    ('nextapp.fx_preferences.xml','com.mekromn.dwfilemanager_preferences.xml'),
    ('nextapp_fx_module','dw_filemanager_module'),
    ('nextapp.fx','com.mekromn.dwfilemanager'),
    ('nextapp.maui','dw.filemanager.maui'),
    ('nextapp.xf','dw.filemanager.xf'),
    ('nextapp.cat','dw.filemanager.annotation'),
]

CLASS_REPL=[
    ('Ldw/filemanager/ext/ui/PlusRegistry$PlusHomeSection;','Ldw/filemanager/ext/ui/ExtRegistry$ExtHomeSection;'),
    ('Ldw/filemanager/ext/ui/PlusRegistry$1;','Ldw/filemanager/ext/ui/ExtRegistry$1;'),
    ('Ldw/filemanager/ext/ui/PlusRegistry;','Ldw/filemanager/ext/ui/ExtRegistry;'),
    ('Ldw/filemanager/ext/ui/PlusExtension;','Ldw/filemanager/ext/ui/ExtExtension;'),
    ('Ldw/filemanager/ext/ui/PlusHomeItem;','Ldw/filemanager/ext/ui/ExtHomeItem;'),
    ('Ldw/filemanager/ext/PlusCore;','Ldw/filemanager/ext/ExtCore;'),
    ('dw.filemanager.ext.ui.PlusRegistry$PlusHomeSection','dw.filemanager.ext.ui.ExtRegistry$ExtHomeSection'),
    ('dw.filemanager.ext.ui.PlusRegistry$1','dw.filemanager.ext.ui.ExtRegistry$1'),
    ('dw.filemanager.ext.ui.PlusRegistry','dw.filemanager.ext.ui.ExtRegistry'),
    ('dw.filemanager.ext.ui.PlusExtension','dw.filemanager.ext.ui.ExtExtension'),
    ('dw.filemanager.ext.ui.PlusHomeItem','dw.filemanager.ext.ui.ExtHomeItem'),
    ('dw.filemanager.ext.PlusCore','dw.filemanager.ext.ExtCore'),
    # The Apps list click handler constructs this Activity by dotted class name via
    # Intent.setClassName(). The implementation lives in the former plus/extension tree,
    # so the generic nextapp.fx -> dw.filemanager rewrite alone leaves a stale base path.
    ('dw.filemanager.ui.app.AppDetailsActivity','dw.filemanager.ext.ui.app.AppDetailsActivity'),
]

def rewrite(path:Path, replacements):
    text=path.read_text(errors='strict')
    old=text
    for a,b in replacements: text=text.replace(a,b)
    if text!=old: path.write_text(text)

def remove_vendor_package_map(sm:Path):
    p=sm/'kb/a.smali'; text=p.read_text()
    text=text.replace('const-string v2, "nextapp.fx"','const-string v2, "com.mekromn.dwfilemanager"',1)
    start=text.find('    const-string v2, "nextapp.fx.rk"')
    end_marker='    invoke-virtual {v1, v2, v0}, Ljava/util/HashMap;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;'
    if start<0: raise RuntimeError('kb/a external companion map block not found')
    end=text.find(end_marker,start)
    if end<0: raise RuntimeError('kb/a vendor-package map tail not found')
    end += len(end_marker)
    removed=text[start:end]
    for token in ('nextapp.fx.rk','nextapp.fx.rr','nextapp.sdfix'):
        if token not in removed: raise RuntimeError(f'kb/a block missing {token}')
    text=text[:start]+text[end:]
    p.write_text(text)

def move_dw_classes(sm:Path):
    moves=[]
    for p in list(sm.rglob('*.smali')):
        text=p.read_text(errors='ignore')
        m=re.search(r'^\.class[^\n]* (Ldw/filemanager/[^;]+;)',text,re.M)
        if not m: continue
        rel=m.group(1)[1:-1]+'.smali'
        target=sm/rel
        if p.resolve()==target.resolve(): continue
        if target.exists(): raise RuntimeError(f'class path collision: {p} -> {target}')
        moves.append((p,target))
    for p,target in moves:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(p),str(target))
    for d in sorted([p for p in sm.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
        try: d.rmdir()
        except OSError: pass
    return len(moves)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    remove_vendor_package_map(sm)
    companion=sm/'dw/filemanager/core/Companion.smali'; ct=companion.read_text()
    if ct.count(EXTERNAL)!=1: raise RuntimeError('Companion external package literal count changed')
    companion.write_text(ct.replace(EXTERNAL,PLACE))
    mf=root/'AndroidManifest.xml'; mt=mf.read_text()
    if mt.count(EXTERNAL)!=1: raise RuntimeError('manifest external package query count changed')
    mf.write_text(mt.replace(EXTERNAL,PLACE))
    for p in sm.rglob('*.smali'): rewrite(p,TEXT_REPL+CLASS_REPL)
    rewrite(mf,TEXT_REPL+CLASS_REPL)
    for p in (root/'res').rglob('*.xml'): rewrite(p,TEXT_REPL+CLASS_REPL)
    for p in [mf,*list((root/'res').rglob('*.xml'))]:
        text=p.read_text(); text=text.replace('/plusui','/extui').replace('plusui','extui'); p.write_text(text)
    companion.write_text(companion.read_text().replace(PLACE,EXTERNAL))
    mf.write_text(mf.read_text().replace(PLACE,EXTERNAL))
    moved=move_dw_classes(sm)
    smali_text='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    hits=[]
    for p in sm.rglob('*.smali'):
        t=p.read_text(errors='ignore').replace(EXTERNAL,'')
        if 'Lnextapp/' in t or re.search(r'const-string[^\n]*"nextapp\.',t):
            hits.append(str(p.relative_to(sm)))
    if hits: raise RuntimeError(f'old nextapp app descriptors/package literals remain: {hits[:20]}')
    if 'com/google/android/gms/internal/play_billing' in smali_text or 'com.google.android.gms.internal.play_billing' in smali_text:
        raise RuntimeError('old shaded play_billing namespace remains')
    if smali_text.count(EXTERNAL)!=1: raise RuntimeError(f'executable external companion literal count={smali_text.count(EXTERNAL)}')
    if mf.read_text().count(EXTERNAL)!=1: raise RuntimeError('manifest external companion query count != 1')
    if (sm/'nextapp').exists() and any((sm/'nextapp').rglob('*.smali')):
        raise RuntimeError('nextapp class files remain after descriptor migration')
    if (sm/'com/google/android/gms/internal/play_billing').exists() and any((sm/'com/google/android/gms/internal/play_billing').glob('*.smali')):
        raise RuntimeError('old shaded class files remain')
    for old in ('PlusCore','PlusExtension','PlusHomeItem','PlusRegistry'):
        if old in smali_text: raise RuntimeError(f'legacy class identifier remains: {old}')

    stale='dw.filemanager.ui.app.AppDetailsActivity'
    actual='dw.filemanager.ext.ui.app.AppDetailsActivity'
    if stale in smali_text: raise RuntimeError('stale AppDetailsActivity explicit class path remains')
    appdetails=sm/'dw/filemanager/ext/ui/app/AppDetailsActivity.smali'
    if not appdetails.exists(): raise RuntimeError('migrated AppDetailsActivity implementation missing')
    gf=(sm/'gf/c.smali').read_text()
    if gf.count(actual)!=1 or 'Intent;->setClassName' not in gf:
        raise RuntimeError('Apps click handler does not target migrated AppDetailsActivity exactly once')

    print(f'stage06a namespace migration complete; moved {moved} class files; AppDetails explicit target migrated')

if __name__=='__main__': main()
