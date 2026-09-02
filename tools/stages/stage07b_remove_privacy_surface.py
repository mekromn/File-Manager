#!/usr/bin/env python3
from pathlib import Path
import argparse,xml.etree.ElementTree as ET
PRIV_NAMES={'pref_privacy_title','pref_privacy_summary'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'; res=root/'res'
    p=sm/'ph/m.smali'; lines=p.read_text().splitlines()
    hit=next(i for i,l in enumerate(lines) if 'new-instance v5, Lrf/h;' in l and any('const/4 v8, 0x2' in x for x in lines[i:i+10]))
    target='invoke-static/range {v0 .. v5}, Ltf/c;->a(Landroid/content/Context;Landroid/preference/PreferenceGroup;IIILandroid/preference/Preference$OnPreferenceClickListener;)Ldw/filemanager/maui/ui/preference/LabelPreference;'
    end=hit
    while end<len(lines) and target not in lines[end]: end+=1
    if end>=len(lines): raise RuntimeError('privacy preference tail not found')
    body='\n'.join(lines[hit:end+1])
    for tok in ('0x7f100610','0x7f10060f','Lrf/h;-><init>','const/4 v8, 0x2'):
        if tok not in body: raise RuntimeError(f'privacy preference block missing {tok}')

    # IMPORTANT: v8 is not private to the removed preference row. The original method
    # intentionally initializes it to 2 here and later reuses it as the Object[] length
    # for the About/version summary. Deleting the whole block made v8 Undefined on the
    # surviving path, which ART rejects with VerifyError when MainPrefActivity loads.
    # Remove the obsolete privacy preference construction but preserve the shared value.
    replacement=['    const/4 v8, 0x2    # retained shared register: later Object[2] version summary']
    p.write_text('\n'.join(lines[:hit]+replacement+lines[end+1:])+'\n')

    # Structural regression guard for the exact on-device VerifyError we fixed.
    method=p.read_text()
    sig='b(Ldw/filemanager/ui/fxsystem/MainPrefActivity;Landroid/preference/PreferenceGroup;)V'
    decl=next((l for l in method.splitlines() if l.startswith('.method') and sig in l),None)
    if decl is None: raise RuntimeError('ph/m method b declaration missing after privacy cut')
    ms=method.index(decl); me=method.index('.end method',ms); mb=method[ms:me]
    init=mb.find('const/4 v8, 0x2')
    use=mb.find('new-array v4, v8, [Ljava/lang/Object;')
    if init<0 or use<0 or init>use:
        raise RuntimeError('ph/m v8 definite initialization before version-summary array was lost')

    p=sm/'rf/h.smali'; lines=p.read_text().splitlines()
    dispatch=next(i for i,l in enumerate(lines) if 'packed-switch p1, :pswitch_data_0' in l)
    start=dispatch+1
    ps0=next(i for i,l in enumerate(lines[start:],start) if l.strip()==':pswitch_0')
    body='\n'.join(lines[start:ps0])
    for tok in ('dw.filemanager.intent.extra.privacy','dw.filemanager.ui.about.AboutActivity'):
        if tok not in body: raise RuntimeError(f'privacy listener arm missing {tok}')
    p.write_text('\n'.join(lines[:start]+['','    return v0','']+lines[ps0:])+'\n')

    for sp in res.glob('values*/strings.xml'):
        tree=ET.parse(sp); r=tree.getroot(); changed=False
        for e in list(r):
            name=e.attrib.get('name')
            if name in PRIV_NAMES:
                r.remove(e); changed=True
            elif name=='item_about_fx':
                e.text='About DW File Manager'; changed=True
            elif name=='pref_about_summary':
                e.text='Version and application information'; changed=True
        if changed:
            ET.indent(tree,space='    '); tree.write(sp,encoding='utf-8',xml_declaration=True)
    pub=res/'values/public.xml'; tree=ET.parse(pub); r=tree.getroot(); n=0
    for e in list(r):
        if e.attrib.get('type')=='string' and e.attrib.get('name') in PRIV_NAMES:
            r.remove(e); n+=1
    if n!=2: raise RuntimeError(f'expected 2 privacy public resources, removed {n}')
    ET.indent(tree,space='    '); tree.write(pub,encoding='utf-8',xml_declaration=True)

    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    for tok in ('0x7f100610','0x7f10060f','dw.filemanager.intent.extra.privacy'):
        if tok in corpus: raise RuntimeError(f'privacy executable residue remains: {tok}')
    for sp in res.glob('values*/strings.xml'):
        text=sp.read_text(errors='ignore')
        for name in PRIV_NAMES:
            if f'name="{name}"' in text: raise RuntimeError(f'{sp}: privacy resource remains {name}')
        if 'name="item_about_fx"' in text and 'About DW File Manager' not in text:
            raise RuntimeError(f'{sp}: old About value survives')
        if 'name="pref_about_summary"' in text and 'Version and application information' not in text:
            raise RuntimeError(f'{sp}: old About summary survives')
    print('stage07b obsolete app privacy settings surface removed; ph/m shared v8 register flow preserved')
if __name__=='__main__': main()
