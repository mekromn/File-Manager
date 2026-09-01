#!/usr/bin/env python3
from pathlib import Path
import argparse

def replace_once(path: Path, old: str, new: str=''):
    t=path.read_text(); n=t.count(old)
    if n!=1: raise RuntimeError(f'{path}: expected one occurrence, got {n}: {old[:100]}')
    path.write_text(t.replace(old,new,1))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ns=ap.parse_args(); root=ns.decoded; web=root/'assets/web'
    up=web/'app/Upgrade.js'
    if not up.exists(): raise RuntimeError('Upgrade.js missing')
    if 'android.nextapp.com/websharing/upgrade/' not in up.read_text(): raise RuntimeError('unexpected Upgrade.js content')
    up.unlink()
    main=web/'app/Main.js'
    replace_once(main,',MODULE_UPGRADE:["app/Upgrade.js"]')
    ws=web/'app/Workspace.js'
    replace_once(ws,',upgrade:{libraries:WS.MODULE_UPGRADE,create:function(){return new WS.Upgrade();}}')
    replace_once(ws,'if(WS.lite){this._tabPane.add(new Echo.ContentPane({id:"upgrade",layoutData:{title:this._r.m["Tab.Upgrade"],icon:this._r.i["Tab.Upgrade"]}}));\n}')
    res=web/'app/Resource.js'
    replace_once(res,',"Tab.Upgrade":"UPGRADE"')
    base=web/'WS.Base.js'
    replace_once(base,',MODULE_UPGRADE:["app/Upgrade.js"]')
    replace_once(base,',"Tab.Upgrade":"UPGRADE"')
    corpus='\n'.join(p.read_text(errors='ignore') for p in web.rglob('*') if p.is_file())
    for tok in ('MODULE_UPGRADE','WS.Upgrade','Tab.Upgrade','websharing/upgrade/','id:"upgrade"'):
        if tok in corpus: raise RuntimeError(f'web upgrade token survives: {tok}')
    print('stage04d Web Access upgrade/promo module removed')
if __name__=='__main__': main()
