#!/usr/bin/env python3
from pathlib import Path
import argparse, re, shutil

IDENTIFIERS={
    'i144_fx_root':'i144_dw_root','i144_fx':'i144_dw',
    'i288_fx_root':'i288_dw_root','i288_fx':'i288_dw',
    'id144_fx_textedit':'id144_dw_textedit','id288_fx_textedit':'id288_dw_textedit',
    'logo_fx':'logo_dw','ic_splash_fx':'ic_splash_dw',
    'item_about_fx':'item_about_dw','item_fx_connect':'item_dw_connect','item_fx_textedit':'item_dw_textedit',
}
BRAND_REPLACEMENTS=[
    ('FX File Explorer','DW File Manager'),('FX [File Explorer]','DW File Manager'),
    ('FX Connect','DW Connect'),('FX TextEdit','DW TextEdit'),('FX Web Access','DW Web Access'),
    ('FX Binary Viewer','DW Binary Viewer'),('FX File Chooser','DW File Chooser'),
    ('FX Script Executor','DW Script Executor'),('FX Archive Extractor','DW Archive Extractor'),
    ('FX Image Viewer','DW Image Viewer'),('FX Media Player','DW Media Player'),
    ('FX Root Installer','DW Root Installer'),('FX Playlist Importer','DW Playlist Importer'),
    ('FX Text Viewer','DW Text Viewer'),
]

def ids(text):
    for old,new in IDENTIFIERS.items(): text=text.replace(old,new)
    return text

def brand(text):
    for old,new in BRAND_REPLACEMENTS: text=text.replace(old,new)
    return re.sub(r'\bFX\b','DW File Manager',text)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    repo=Path(__file__).resolve().parents[2]; icons=repo/'assets/dw-icons'
    required=['i144_dw.png','i144_dw_root.png','i288_dw.png','i288_dw_root.png','id144_dw_textedit.png','id288_dw_textedit.png','ic_splash_dw.png','ic_launcher_app_192.png','ic_launcher_app_144.png','ic_launcher_app_bg.png','ic_launcher_app_fg.png']
    missing=[x for x in required if not (icons/x).exists()]
    if missing: raise RuntimeError(f'missing generated DW icon assets: {missing}')

    for tr in (root/'res',root/'smali'):
        for p in tr.rglob('*'):
            if p.is_file() and p.suffix in {'.xml','.smali'}:
                try:t=p.read_text()
                except UnicodeDecodeError:continue
                nt=ids(t)
                if nt!=t:p.write_text(nt)
    manifest=root/'AndroidManifest.xml'; manifest.write_text(ids(brand(manifest.read_text())))
    for p in (root/'res').rglob('*.xml'):
        t=p.read_text(); nt=brand(t)
        if nt!=t:p.write_text(nt)

    renames=[
      ('res/drawable-nodpi/i144_fx.png','res/drawable-nodpi/i144_dw.png'),
      ('res/drawable-nodpi/i144_fx_root.png','res/drawable-nodpi/i144_dw_root.png'),
      ('res/drawable-nodpi/i288_fx.png','res/drawable-nodpi/i288_dw.png'),
      ('res/drawable-nodpi/i288_fx_root.png','res/drawable-nodpi/i288_dw_root.png'),
      ('res/drawable-nodpi/id144_fx_textedit.png','res/drawable-nodpi/id144_dw_textedit.png'),
      ('res/drawable-nodpi/id288_fx_textedit.png','res/drawable-nodpi/id288_dw_textedit.png'),
      ('res/drawable/logo_fx.xml','res/drawable/logo_dw.xml'),
      ('res/mipmap-xxxhdpi/ic_splash_fx.png','res/mipmap-xxxhdpi/ic_splash_dw.png'),
    ]
    for s,d in renames:
        src=root/s;dst=root/d
        if not src.exists():raise RuntimeError(f'missing branded resource {src}')
        src.rename(dst)

    copies={
      'i144_dw.png':'res/drawable-nodpi/i144_dw.png','i144_dw_root.png':'res/drawable-nodpi/i144_dw_root.png',
      'i288_dw.png':'res/drawable-nodpi/i288_dw.png','i288_dw_root.png':'res/drawable-nodpi/i288_dw_root.png',
      'id144_dw_textedit.png':'res/drawable-nodpi/id144_dw_textedit.png','id288_dw_textedit.png':'res/drawable-nodpi/id288_dw_textedit.png',
      'ic_splash_dw.png':'res/mipmap-xxxhdpi/ic_splash_dw.png','ic_launcher_app_192.png':'res/mipmap-xxxhdpi/ic_launcher_app.png',
      'ic_launcher_app_144.png':'res/mipmap-xxhdpi/ic_launcher_app.png','ic_launcher_app_bg.png':'res/mipmap-xxxhdpi/ic_launcher_app_bg.png',
      'ic_launcher_app_fg.png':'res/mipmap-xxxhdpi/ic_launcher_app_fg.png',
    }
    for src,dst in copies.items():shutil.copy2(icons/src,root/dst)
    (root/'res/drawable/logo_dw.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<bitmap xmlns:android="http://schemas.android.com/apk/res/android" android:gravity="center" android:src="@mipmap/ic_splash_dw" />\n')

    bad=[str(p) for p in (root/'res').rglob('*.xml') if re.search(r'\bFX\b|NextApp',p.read_text(errors='ignore'))]
    if bad:raise RuntimeError('branding remains in Android XML: '+str(bad[:10]))
    for old in IDENTIFIERS:
        for tr in (root/'res',root/'smali'):
            for p in tr.rglob('*'):
                if p.is_file() and p.suffix in {'.xml','.smali'}:
                    try:t=p.read_text()
                    except UnicodeDecodeError:continue
                    if old in t:raise RuntimeError(f'legacy identifier {old} remains in {p}')
    for p in (root/'res').rglob('*'):
        if p.is_file() and re.search(r'(^|_)(fx|nextapp)($|_)',p.stem,re.I):raise RuntimeError(f'legacy branded resource filename remains: {p}')
    print('stage08b Android branding/resources and polished DW artwork migrated')

if __name__=='__main__':main()
