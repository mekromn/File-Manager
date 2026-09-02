#!/usr/bin/env python3
from pathlib import Path
import argparse,re

STRING_NAMES={
'update_chooser_option_title_apk','license_title','update_developer_root_description',
'update_developer_root_requirement_warning','update_developer_root_state_disabled',
'update_developer_root_state_enabled','update_developer_root_state_enabled_package',
'update_error_theme_loading','update_tab_developer','update_tab_theme','update_theme_set_button',
}
DRAWABLE_NAMES={'update_header_overlay'}
ALL=STRING_NAMES|DRAWABLE_NAMES

def remove_element(text,name):
    pat=re.compile(r'\s*<string\s+name="'+re.escape(name)+r'"(?:\s+[^>]*)?>.*?</string>\s*',re.S)
    return pat.sub('\n',text)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('decoded',type=Path);a=ap.parse_args();root=a.decoded
    public=root/'res/values/public.xml'; pt=public.read_text(); ids={}
    for name in ALL:
        m=re.search(r'<public type="([^"]+)" name="'+re.escape(name)+r'" id="(0x[0-9a-fA-F]+)"\s*/>',pt)
        if not m: raise RuntimeError(f'missing public declaration for {name}')
        ids[name]=(m.group(1),m.group(2).lower())
    for name,(typ,rid) in ids.items():
        for sd in root.glob('smali*'):
            for p in sd.rglob('*.smali'):
                if rid in p.read_text(errors='ignore').lower(): raise RuntimeError(f'{name} id {rid} still referenced by {p}')
        sym=re.compile(r'@(?:string|drawable|mipmap|xml|array|style|color|id)/'+re.escape(name)+r'\b')
        for p in (root/'res').rglob('*.xml'):
            if p==public or p.name=='strings.xml': continue
            if sym.search(p.read_text(errors='ignore')): raise RuntimeError(f'{name} still referenced by {p}')
    for p in (root/'res').glob('values*/strings.xml'):
        t=p.read_text(); nt=t
        for n in STRING_NAMES: nt=remove_element(nt,n)
        if nt!=t:p.write_text(nt)
    t=public.read_text(); nt=t
    for n in ALL:
        nt=re.sub(r'\s*<public type="[^"]+" name="'+re.escape(n)+r'" id="0x[0-9a-fA-F]+"\s*/>\s*','\n',nt)
    public.write_text(nt)
    f=root/'res/drawable-nodpi/update_header_overlay.webp'
    if not f.exists(): raise RuntimeError('missing update_header_overlay.webp')
    f.unlink()
    for n in ALL:
        if re.search(r'name="'+re.escape(n)+r'"',public.read_text()): raise RuntimeError(f'public {n} remained')
    for p in (root/'res').glob('values*/strings.xml'):
        for n in STRING_NAMES:
            if re.search(r'<string\s+name="'+re.escape(n)+r'"',p.read_text()):raise RuntimeError(f'{n} remained in {p}')
    print('stage09a pruned 12 graph-proven orphan resources')
if __name__=='__main__':main()
