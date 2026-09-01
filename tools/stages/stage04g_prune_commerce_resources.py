#!/usr/bin/env python3
from pathlib import Path
import argparse,re,shutil

DELETE_NAMES = {
 'about_item_product_code','action_get_plus','error_google_iab_internal','error_google_iab_not_found',
 'error_plus_module_not_enabled','generic_iab_issue_google','home_catalog_update','home_catalog_update_desc',
 'item_upgrade','item_upgrade_fx','pref_banner_plus_description','pref_banner_plus_title',
 'pref_google_iab_disable_summary','pref_google_iab_disable_title','pref_upgrade_description','pref_upgrade_title',
 'update_chooser_description','update_chooser_option_description_apk','update_chooser_option_description_iab',
 'update_chooser_option_title_iab','update_chooser_title','update_plus_cloud','update_plus_description',
 'update_plus_media','update_plus_network','update_plus_sharing','update_plus_welcome_dialog_message',
 'update_plus_welcome_dialog_title','update_tab_plus','update_title'
}
RENAME = {
 'doc_help_section_plus': ('doc_help_section_media_network', 'Media, Network &amp; Sharing'),
 'sharing_connect_no_license': ('sharing_connect_companion_required', 'A device-to-device sharing session requires the companion app.'),
 'sharing_web_access_not_possible_no_plus': ('sharing_web_access_companion_required', 'Web access requires the companion app.'),
}

def remove_string(path:Path,name:str)->int:
    if not path.exists(): return 0
    t=path.read_text(); p=re.compile(r'\n?\s*<string\s+name="'+re.escape(name)+r'"(?:\s+[^>]*)?>.*?</string>',re.S)
    nt,n=p.subn('',t)
    if n: path.write_text(nt)
    return n

def rename_string(path:Path,old:str,new:str,new_value:str)->int:
    if not path.exists(): return 0
    t=path.read_text(); p=re.compile(r'(<string\s+name=")'+re.escape(old)+r'("(?:\s+[^>]*)?>).*?(</string>)',re.S)
    nt,n=p.subn(lambda m:m.group(1)+new+m.group(2)+new_value+m.group(3),t)
    if n: path.write_text(nt)
    return n

def public_id(pub:str,name:str):
    m=re.search(r'<public type="string" name="'+re.escape(name)+r'" id="(0x[0-9a-fA-F]+)" />',pub)
    return m.group(1) if m else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    pubp=root/'res/values/public.xml'; pub=pubp.read_text()
    banner=sm/'nextapp/fx/plus/ui/m.smali'
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    if 'Lnextapp/fx/plus/ui/m;' in corpus.replace(banner.read_text(errors='ignore'),''):
        raise RuntimeError('upgrade banner class still has an external caller')
    banner.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for name in sorted(DELETE_NAMES):
        rid=public_id(pub,name)
        if rid is None: raise RuntimeError(f'missing public string {name}')
        if rid in corpus: raise RuntimeError(f'refusing to delete live resource {name} {rid}')
    removed=0
    for vf in root.glob('res/values*'):
        sp=vf/'strings.xml'
        for name in DELETE_NAMES: removed += remove_string(sp,name)
        for old,(new,val) in RENAME.items(): rename_string(sp,old,new,val)
    pub=pubp.read_text()
    for name in sorted(DELETE_NAMES):
        pub,n=re.subn(r'^\s*<public type="string" name="'+re.escape(name)+r'" id="0x[0-9a-fA-F]+" />\n?','',pub,count=1,flags=re.M)
        if n!=1: raise RuntimeError(f'public declaration removal count {name}: {n}')
    for old,(new,_val) in RENAME.items():
        pub,n=re.subn(r'(<public type="string" name=")'+re.escape(old)+r'(" id="0x[0-9a-fA-F]+" />)',r'\1'+new+r'\2',pub,count=1)
        if n!=1: raise RuntimeError(f'public declaration rename count {old}: {n}')
    pubp.write_text(pub)
    allstrings='\n'.join(p.read_text(errors='ignore') for p in root.glob('res/values*/strings.xml'))
    for name in DELETE_NAMES:
        if f'name="{name}"' in allstrings: raise RuntimeError(f'dead commerce resource survives: {name}')
    for old in RENAME:
        if f'name="{old}"' in allstrings or f'name="{old}"' in pubp.read_text(): raise RuntimeError(f'old resource name survives: {old}')
    assert not banner.exists()
    print(f'stage04g commerce resource pruning complete; removed {removed} localized elements')

if __name__=='__main__': main()
