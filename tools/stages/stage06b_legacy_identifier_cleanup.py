#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'; res=root/'res'
    for rel in ('dw/filemanager/runtime/j1.smali','dw/filemanager/runtime/j5.smali'):
        p=sm/rel; t=p.read_text()
        if ' (plus ' not in t: raise RuntimeError(f'{rel}: generic plus wording missing')
        p.write_text(t.replace(' (plus ',' (and '))
    sp=res/'values/strings.xml'; t=sp.read_text()
    if 'name="tutorial_selection_touch_select"' not in t: raise RuntimeError('selection tutorial resource missing')
    t=t.replace('Tap the \\"plus\\" button in the action bar to touch-select files.','Tap the add button in the action bar to touch-select files.')
    t=t.replace('Tap the &quot;plus&quot; button in the action bar to touch-select files.','Tap the add button in the action bar to touch-select files.')
    sp.write_text(t)
    t=sp.read_text()
    t=re.sub(r'(<string name="help_warning_secondary_storage_write_restricted_dev_message">).*?(</string>)',r'\1This problem may require superuser access or device-specific storage configuration. Please refer to documentation for your device and Android version.\2',t,count=1)
    t=re.sub(r'(<string name="viewer_error_invalid_intent">).*?(</string>)',r'\1Invalid intent sent to the file viewer. See Settings/Error Log for details.\2',t,count=1)
    sp.write_text(t)
    for old,new in (
        ('catalogs_plusui.xml','catalogs_extui.xml'),
        ('interactionhandlers_plusui.xml','interactionhandlers_extui.xml'),
        ('module_plusui.xml','module_extui.xml'),
        ('nextapp_fx_module.xml','dw_filemanager_module.xml'),
    ):
        src=res/'xml'/old; dst=res/'xml'/new
        if not src.exists(): raise RuntimeError(f'missing {old}')
        if dst.exists(): raise RuntimeError(f'target already exists {new}')
        src.rename(dst)
    icon=res/'xml/iconset_dynamic_ext.xml'; t=icon.read_text()
    nt,n=re.subn(r'\n\s*<composite-icon name="fx_plus">.*?</composite-icon>', '', t, count=1, flags=re.S)
    if n!=1: raise RuntimeError('fx_plus composite icon block not found')
    icon.write_text(nt)
    for name in ('i144_fx_overlay_plus.png','i288_fx_overlay_plus.png'):
        p=res/'drawable-nodpi'/name
        if not p.exists(): raise RuntimeError(f'missing obsolete overlay {name}')
        p.unlink()
    pub=res/'values/public.xml'; lines=pub.read_text().splitlines(); before=len(lines)
    lines=[l for l in lines if 'i144_fx_overlay_plus' not in l and 'i288_fx_overlay_plus' not in l]
    if len(lines)!=before-2: raise RuntimeError('expected two public overlay declarations')
    pub.write_text('\n'.join(lines)+'\n')
    app='\n'.join(p.read_text(errors='ignore') for p in (sm/'dw/filemanager').rglob('*.smali'))
    if re.search(r'plus',app,re.I):
        hits=[str(p.relative_to(sm)) for p in (sm/'dw/filemanager').rglob('*.smali') if re.search(r'plus',p.read_text(errors='ignore'),re.I)]
        raise RuntimeError(f'plus token remains in DW executable code: {hits[:20]}')
    rhits=[]
    for p in res.rglob('*'):
        if p.is_file():
            if 'plus' in p.name.lower(): rhits.append(str(p.relative_to(res)))
            try: text=p.read_text()
            except Exception: continue
            if re.search(r'plus',text,re.I): rhits.append(str(p.relative_to(res)))
    if rhits: raise RuntimeError(f'plus token remains in resources: {sorted(set(rhits))[:30]}')
    rtext='\n'.join(p.read_text(errors='ignore') for p in res.rglob('*.xml'))
    if 'NextApp' in rtext or 'nextapp' in rtext:
        hits=[str(p.relative_to(res)) for p in res.rglob('*.xml') if 'nextapp' in p.read_text(errors='ignore').lower()]
        raise RuntimeError(f'NextApp residue remains in resources: {hits[:20]}')
    print('stage06b legacy plus/resource/vendor identifier cleanup complete')

if __name__=='__main__': main()
