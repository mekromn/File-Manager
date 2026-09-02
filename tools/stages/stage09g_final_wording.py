#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    p=root/'smali/ib/f.smali'; t=p.read_text()
    n=t.count('const-string v2, "_license"')+t.count('const-string v1, "_license"')
    if n!=2: raise RuntimeError(f'expected 2 root settings _license suffixes, found {n}')
    t=t.replace('const-string v2, "_license"','const-string v2, "_settings"')
    t=t.replace('const-string v1, "_license"','const-string v1, "_settings"')
    p.write_text(t)

    p=root/'assets/help/root.html'; t=p.read_text()
    old='Visit the "Upgrade" item on the Home Screen'
    if old not in t: raise RuntimeError('root help Upgrade sentence shape changed')
    t=t.replace(old,'Open Settings and enable root access in the Developer/Root section')
    p.write_text(t)

    for rel in ['assets/web/app/Resource.js','assets/web/WS.Base.js']:
        p=root/rel; t=p.read_text()
        t=t.replace('recommend you upgrade to a more modern browser if possible.',
                    'recommend using a more modern browser if possible.')
        p.write_text(t)

    pub=root/'res/values/public.xml'; pt=pub.read_text()
    rename={
      'network_db_upgrade_dialog_message':'network_db_changed_dialog_message',
      'network_db_upgrade_dialog_title':'network_db_changed_dialog_title',
    }
    for oldn,newn in rename.items():
        if f'name="{oldn}"' not in pt: raise RuntimeError(f'missing public resource {oldn}')
        pt=pt.replace(f'name="{oldn}"',f'name="{newn}"')
    pub.write_text(pt)
    for p in (root/'res').glob('values*/strings.xml'):
        t=p.read_text()
        for oldn,newn in rename.items(): t=t.replace(f'name="{oldn}"',f'name="{newn}"')
        t=t.replace('Network Database Upgrade','Network Database Changed')
        t=t.replace('database has been upgraded in this version','database format has changed in this version')
        t=t.replace('app having been recently upgraded by Android','app having been recently updated by Android')
        p.write_text(t)

    if '_license"' in (root/'smali/ib/f.smali').read_text(): raise RuntimeError('root settings _license suffix remains')
    if re.search(r'\bUpgrade\b', (root/'assets/help/root.html').read_text()): raise RuntimeError('Upgrade remains in root help')
    for rel in ['assets/web/app/Resource.js','assets/web/WS.Base.js']:
        if re.search(r'\brecommend you upgrade\b', (root/rel).read_text(),re.I): raise RuntimeError(f'old browser upgrade wording remains {rel}')
    if 'network_db_upgrade_dialog_' in (root/'res/values/public.xml').read_text(): raise RuntimeError('old network DB resource identifier remains')
    print('stage09g removed stale app-owned upgrade/license wording without touching OSS/protocol terminology')
if __name__=='__main__': main()
