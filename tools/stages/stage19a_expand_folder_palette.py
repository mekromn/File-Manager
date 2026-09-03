#!/usr/bin/env python3
from pathlib import Path
import argparse, re, shutil, xml.etree.ElementTree as ET

# Stage19 is intentionally isolated from the active Stage13 picker branch. Give its
# device-test APK a safely higher code so it can be installed over all current tests.
VC = '9109019'

# Hue values are rotations from DW's own blue tint-base artwork. Saturation values
# use the app's existing transform convention. White and Dark Blue are handled by
# two tiny original DW bases because the runtime tint parser has no brightness/value
# transform -- only hue + saturation.
PALETTE = [
    ('blue',       'Blue',       0,    -55, 'procedural'),
    ('aqua',       'Aqua',      -30,   -45, 'procedural'),
    ('dark_blue',  'Dark Blue',  None, None, 'dark_static'),
    ('gray',       'Gray',       0,   -100, 'procedural'),
    ('copper',     'Copper',     170,  -75, 'procedural'),
    ('khaki',      'Khaki',     -150,  -85, 'procedural'),
    ('green',      'Green',      -60,  -50, 'procedural'),
    ('yellow',     'Yellow',    -150,  -35, 'procedural'),
    ('orange',     'Orange',     180,  -45, 'procedural'),
    ('red',        'Red',        150,  -55, 'procedural'),
    ('pink',       'Pink',       105,  -50, 'procedural'),
    ('violet',     'Violet',      60,  -55, 'procedural'),
    ('white',      'White',      None, None, 'white_static'),
    ('plain',      'Plain',      None, None, 'plain'),
]

PROCEDURAL = {name:(h,s) for name,_,h,s,kind in PALETTE if kind == 'procedural'}
COLOR_ALIAS_NAMES = [f'folder_c_{name}' for name,_,_,_,kind in PALETTE if name != 'plain']

# Existing category colors from Dynamic Blue. New color themes keep DW's useful
# category distinction for system/audio/image/misc special folders.
CATEGORY_TINTS = [
    ('folder_system', -50, -50),
    ('folder_system_internal', -60, -80),
    ('folder_audio', 170, -75),
    ('folder_image', -150, -85),
    ('folder_misc', 140, -75),
]


def tint_element(name, hue=None, saturation=None):
    e = ET.Element('tint', {'name': name})
    if hue is not None:
        e.set('hue', str(hue))
    if saturation is not None:
        e.set('saturation', str(saturation))
    return e


def dynamic_folder(name, source144='@drawable/id144_folder_tintbase', source288='@drawable/id288_folder_tintbase', tint=None):
    attrs = {'name': name, 'shape': 'round_rect'}
    if tint:
        attrs['tint'] = tint
    d = ET.Element('dynamic-icon', attrs)
    ET.SubElement(d, 'image', {'size':'144', 'value':source144})
    ET.SubElement(d, 'image', {'size':'288', 'value':source288})
    return d


def write_xml(path, root):
    ET.indent(root, space='    ')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def set_tints(iconset_path, base=None):
    tree = ET.parse(iconset_path); root = tree.getroot()
    # Keep includes/dynamic icons, but normalize all named tint definitions in one place.
    for e in list(root):
        if e.tag == 'tint' and (e.attrib.get('name','').startswith('folder_c_') or e.attrib.get('name') == 'folder_base'):
            root.remove(e)
    insert_at = 0
    if base is not None:
        h,s = base
        root.insert(insert_at, tint_element('folder_base', h, s)); insert_at += 1
    # Existing category tints follow folder_base when present. Do not disturb them.
    while insert_at < len(root) and root[insert_at].tag == 'tint':
        insert_at += 1
    for name,(h,s) in PROCEDURAL.items():
        root.insert(insert_at, tint_element(f'folder_c_{name}', h, s)); insert_at += 1
    write_xml(iconset_path, root)


def make_theme_iconset(path, base_hue=None, base_sat=None, include='@xml/iconset_dynamic_base_tintfoldercolor'):
    root = ET.Element('iconset', {'sizes':'144,288'})
    root.append(tint_element('folder_base', base_hue, base_sat))
    for name,h,s in CATEGORY_TINTS:
        root.append(tint_element(name,h,s))
    for name,(h,s) in PROCEDURAL.items():
        root.append(tint_element(f'folder_c_{name}', h, s))
    ET.SubElement(root, 'include', {'name':'@xml/iconset_dynamic_base'})
    ET.SubElement(root, 'include', {'name':include})
    write_xml(path, root)


def make_colorfolders_include(path):
    # Plain historically listed colored folders in kc/a but did not include the
    # tint-folder-color icon definitions. Fix that mismatch with a color-only include
    # which does NOT override Plain's normal folder or special-folder artwork.
    root = ET.Element('iconset', {'sizes':'144,288'})
    for name,_,_,_,kind in PALETTE:
        if name == 'plain':
            continue
        alias = f'folder_c_{name}'
        if kind == 'dark_static':
            root.append(dynamic_folder(alias, '@drawable/id144_folder_dw_dark_blue', '@drawable/id288_folder_dw_dark_blue'))
        elif kind == 'white_static':
            root.append(dynamic_folder(alias, '@drawable/id144_folder_dw_white', '@drawable/id288_folder_dw_white'))
        else:
            root.append(dynamic_folder(alias, tint=alias))
    write_xml(path, root)


def extend_tintfoldercolor(common_path):
    tree = ET.parse(common_path); root = tree.getroot()
    existing = {e.attrib.get('name') for e in root if e.tag == 'dynamic-icon'}
    for name,_,_,_,kind in PALETTE:
        if name == 'plain':
            continue
        alias=f'folder_c_{name}'
        if alias in existing:
            continue
        if kind == 'dark_static':
            root.insert(0, dynamic_folder(alias, '@drawable/id144_folder_dw_dark_blue', '@drawable/id288_folder_dw_dark_blue'))
        elif kind == 'white_static':
            root.insert(0, dynamic_folder(alias, '@drawable/id144_folder_dw_white', '@drawable/id288_folder_dw_white'))
        else:
            root.insert(0, dynamic_folder(alias, tint=alias))
    write_xml(common_path, root)


def make_luminance_variant_include(common_path, out_path, source144, source288):
    tree = ET.parse(common_path); root = tree.getroot()
    for d in root.findall('dynamic-icon'):
        name=d.attrib.get('name','')
        # Explicit color swatches remain absolute palette choices regardless of the
        # active folder theme. Only the ordinary/special folder family uses the light
        # or dark base.
        if name.startswith('folder_c_'):
            continue
        for im in d.findall('image'):
            if im.attrib.get('size') == '144': im.set('value', source144)
            elif im.attrib.get('size') == '288': im.set('value', source288)
    write_xml(out_path, root)


def patch_icon_chooser(smali_path):
    t=smali_path.read_text()
    start=t.find('    const-string v1, "folder"')
    alarm=t.find('    const-string v1, "folder_alarm"', start)
    if start < 0 or alarm < 0:
        raise RuntimeError('kc/a initial folder palette anchors missing')
    # Keep Plain first in the chooser, then the same palette order as Theme.
    # PALETTE is Theme order with Plain last, so explicitly reorder chooser entries.
    chooser=['plain']+[p[0] for p in PALETTE if p[0] != 'plain']
    block=[]
    for name in chooser:
        key='folder' if name == 'plain' else f'folder_c_{name}'
        block += [f'    const-string v1, "{key}"', '', '    invoke-virtual {v0, v1}, Ljava/util/ArrayList;->add(Ljava/lang/Object;)Z', '']
    smali_path.write_text(t[:start]+'\n'.join(block)+t[alarm:])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    res=root/'res'; xml=res/'xml'; values=res/'values'; sm=root/'smali'
    repo=Path(__file__).resolve().parents[2]

    # Original DW light/dark luminance bases generated from DW's own tintbase geometry.
    # aapt2 37.0.0 reproducibly crashes while crunching the 288px Dark Blue PNG, so
    # the canonical 288px Dark Blue asset is lossless WebP with the same resource
    # basename. XML continues to reference @drawable/id288_folder_dw_dark_blue.
    asset=repo/'assets/folder-palette'
    dst=res/'drawable-nodpi'; dst.mkdir(parents=True,exist_ok=True)
    for name in ('id144_folder_dw_dark_blue.png','id288_folder_dw_dark_blue.webp','id144_folder_dw_white.png','id288_folder_dw_white.png'):
        src=asset/name
        if not src.exists(): raise RuntimeError('missing Stage19 asset '+str(src))
        shutil.copy2(src,dst/name)

    # Add default-locale labels. Android locale fallback supplies them elsewhere.
    strings=values/'strings.xml'; tree=ET.parse(strings); sr=tree.getroot()
    existing={e.attrib.get('name') for e in sr if e.tag=='string'}
    for name,label,_,_,_ in PALETTE:
        key=f'icon_theme_dynamic_{name}_title'
        if key not in existing:
            e=ET.Element('string',{'name':key}); e.text=label; sr.append(e)
    write_xml(strings,sr)

    # Canonical tint aliases in every existing tint-capable dynamic theme.
    existing_theme_files={
        'blue': xml/'iconset_dynamic_blue.xml',
        'copper': xml/'iconset_dynamic_copper.xml',
        'khaki': xml/'iconset_dynamic_khaki.xml',
        'green': xml/'iconset_dynamic_green.xml',
    }
    existing_base={'blue':(0,-75),'copper':(170,-75),'khaki':(-150,-85),'green':(-50,-50)}
    for name,p in existing_theme_files.items():
        if not p.exists(): raise RuntimeError('missing existing dynamic iconset '+str(p))
        set_tints(p, existing_base[name])

    common=xml/'iconset_dynamic_base_tintfoldercolor.xml'
    extend_tintfoldercolor(common)
    make_colorfolders_include(xml/'iconset_dynamic_colorfolders.xml')

    # Fix Plain so every chooser color is available under Plain as well.
    plain=xml/'iconset_dynamic_plain.xml'; pt=ET.parse(plain); pr=pt.getroot()
    for e in list(pr):
        if e.tag=='tint' and e.attrib.get('name','').startswith('folder_c_'): pr.remove(e)
    idx=0
    for name,(h,s) in PROCEDURAL.items():
        pr.insert(idx,tint_element(f'folder_c_{name}',h,s)); idx+=1
    if not any(e.tag=='include' and e.attrib.get('name')=='@xml/iconset_dynamic_colorfolders' for e in pr):
        ET.SubElement(pr,'include',{'name':'@xml/iconset_dynamic_colorfolders'})
    write_xml(plain,pr)

    # Luminance-specific special-folder includes. Color-swatch aliases stay absolute.
    make_luminance_variant_include(common, xml/'iconset_dynamic_base_tintfoldercolor_dark_blue.xml', '@drawable/id144_folder_dw_dark_blue', '@drawable/id288_folder_dw_dark_blue')
    make_luminance_variant_include(common, xml/'iconset_dynamic_base_tintfoldercolor_white.xml', '@drawable/id144_folder_dw_white', '@drawable/id288_folder_dw_white')

    # Add the new whole-theme variants. Existing Blue/Copper/Khaki/Green/Plain files stay native.
    new_proc=['aqua','gray','yellow','orange','red','pink','violet']
    for name in new_proc:
        h,s=PROCEDURAL[name]
        make_theme_iconset(xml/f'iconset_dynamic_{name}.xml',h,s)
    make_theme_iconset(xml/'iconset_dynamic_dark_blue.xml',None,None,'@xml/iconset_dynamic_base_tintfoldercolor_dark_blue')
    make_theme_iconset(xml/'iconset_dynamic_white.xml',None,None,'@xml/iconset_dynamic_base_tintfoldercolor_white')

    # Rebuild Dynamic Material palette in one canonical order.
    module=xml/'dw_filemanager_module.xml'; mt=ET.parse(module); mr=mt.getroot()
    theme_set=next((e for e in mr if e.tag=='icon-theme-set' and e.attrib.get('id')=='fx_dynamic'),None)
    if theme_set is None: raise RuntimeError('fx_dynamic icon-theme-set missing')
    for e in list(theme_set):
        if e.tag=='icon-theme': theme_set.remove(e)
    for name,label,h,s,kind in PALETTE:
        attrs={'id':f'fx_dynamic_{name}','resource':f'@xml/iconset_dynamic_{name}','title':f'@string/icon_theme_dynamic_{name}_title','icon-fill':'true'}
        if kind=='plain':
            attrs['icon']='@drawable/id144_folder'
        elif kind=='dark_static':
            attrs['icon']='@drawable/id144_folder_dw_dark_blue'
        elif kind=='white_static':
            attrs['icon']='@drawable/id144_folder_dw_white'
        else:
            attrs['icon']='@drawable/id144_folder_tintbase'
            if h is not None: attrs['icon-hue']=str(h)
            if s is not None: attrs['icon-saturation']=str(s)
        theme_set.append(ET.Element('icon-theme',attrs))
    write_xml(module,mr)

    # Select Icon: same palette, then all existing special-folder choices.
    patch_icon_chooser(sm/'kc/a.smali')

    # Install cleanly over current test builds.
    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    # Durable guards.
    module_text=module.read_text()
    expected_ids=[f'fx_dynamic_{p[0]}' for p in PALETTE]
    found_ids=re.findall(r'<icon-theme\s+[^>]*id="([^"]+)"',module_text)
    if found_ids[:len(expected_ids)] != expected_ids:
        raise RuntimeError(f'Dynamic Material palette mismatch: {found_ids[:len(expected_ids)]}')
    kct=(sm/'kc/a.smali').read_text()
    for alias in ['folder']+COLOR_ALIAS_NAMES:
        if f'"{alias}"' not in kct: raise RuntimeError('Select Icon alias missing '+alias)
    for p in ('iconset_dynamic_aqua.xml','iconset_dynamic_dark_blue.xml','iconset_dynamic_gray.xml','iconset_dynamic_yellow.xml','iconset_dynamic_orange.xml','iconset_dynamic_red.xml','iconset_dynamic_pink.xml','iconset_dynamic_violet.xml','iconset_dynamic_white.xml','iconset_dynamic_colorfolders.xml'):
        if not (xml/p).exists(): raise RuntimeError('generated iconset missing '+p)
    for p in ('id144_folder_dw_dark_blue.png','id288_folder_dw_dark_blue.webp','id144_folder_dw_white.png','id288_folder_dw_white.png'):
        if not (dst/p).exists(): raise RuntimeError('generated folder base missing '+p)

    print('stage19a expanded original DW folder palette in Theme + Select Icon; no Apple-derived assets; vc='+VC)

if __name__=='__main__': main()
