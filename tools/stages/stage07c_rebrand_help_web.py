#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def rewrite_help(p:Path):
    t=p.read_text()
    t=re.sub(r'<p>If you have a question that can\'t be answered here, please e-mail <a href="mailto:android@nextapp\.com">android@nextapp\.com</a>\.\s*Please do not ask support questions in Play Store reviews, it\'s difficult to have a conversation there\.</p>', '<p>Use the local help topics and Settings/Error Log when troubleshooting.</p>',t,flags=re.S)
    t=re.sub(r'<p>Please e-mail bug reports to android@nextapp\.com\..*?</p>', '<p>For bug reports, include the Settings/Error Log and a clear description of the problem.</p>',t,flags=re.S)
    t=re.sub(r'<p>The FAQ is always under development, please feel free to suggest items to add to it based on your experience with the\s*product\. Send suggestions to android@nextapp\.com\.</p>', '<p>The FAQ documents common file-management and connectivity questions.</p>',t,flags=re.S)
    for old,new in [('FX File Explorer','DW File Manager'),('FX File Sharing','DW File Manager Web Access'),('FX Web Access','DW File Manager Web Access'),('FX Connect','DW Connect'),('FX TextEdit','DW TextEdit'),('FX keyring','DW keyring'),('FX Image Viewer','DW Image Viewer'),('FX','DW File Manager')]:
        t=t.replace(old,new)
    p.write_text(t)

def rebrand_js(p:Path):
    t=p.read_text()
    t=t.replace('LINK_URL_DOC:"http://android.nextapp.com/site/websharing/doc",LINK_URL_DOC_FAQ:"http://android.nextapp.com/site/websharing/doc/faq"','LINK_URL_DOC:null,LINK_URL_DOC_FAQ:null')
    t=re.sub(r'case"faq":window\.open\(WS\.LINK_URL_DOC_FAQ\);break;?', 'case"faq":break;', t)
    t=re.sub(r'case"doc":window\.open\(WS\.LINK_URL_DOC\);break;?', 'case"doc":break;', t)
    for old in ('image/branding/FXLogo96.png','image/branding/NextApp.png','image/branding/WelcomeTitle.png'):
        t=t.replace(old,'image/icon/im144_folder.png')
    t=t.replace('"Application.Provider":"NextApp"','"Application.Provider":"DW File Manager"')
    t=t.replace('"About.Title":"About FX File Sharing"','"About.Title":"About DW File Manager Web Access"')
    t=t.replace('"About.Copyright":"Copyright 2009-2018 NextApp, Inc."','"About.Copyright":"DW File Manager"')
    t=t.replace('WebSharing','Web Access')
    t=t.replace('FX File Sharing','DW File Manager Web Access').replace('FX Web Access','DW File Manager Web Access')
    p.write_text(t)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    for p in (root/'assets/help').glob('*.html'): rewrite_help(p)
    web=root/'assets/web'
    for rel in ('app/Main.js','app/WelcomeScreen.js','app/Workspace.js','app/Resource.js','WS.Base.js'):
        rebrand_js(web/rel)
    idx=web/'index.html'; idx.write_text(idx.read_text().replace('<title>FX Web Access</title>','<title>DW File Manager Web Access</title>'))
    branding=web/'image/branding'; expected={'NextApp.png','FXLogo96.png','WelcomeTitle.png','NLogo.png'}
    present={p.name for p in branding.glob('*') if p.is_file()}
    if not expected.issubset(present): raise RuntimeError(f'branding files changed: {present}')
    for p in branding.glob('*'):
        if p.is_file(): p.unlink()
    try: branding.rmdir()
    except OSError: pass
    offenders=[]
    for p in (root/'assets').rglob('*'):
        if not p.is_file(): continue
        try: t=p.read_text()
        except Exception: continue
        if re.search(r'nextapp|android@nextapp\.com|android\.nextapp\.com',t,re.I) or re.search(r'\bFX\b',t): offenders.append(str(p.relative_to(root/'assets')))
    if offenders: raise RuntimeError(f'vendor branding/support residue in assets: {offenders[:30]}')
    for rel in ('app/Main.js','app/WelcomeScreen.js','app/Workspace.js','WS.Base.js'):
        t=(web/rel).read_text()
        if 'window.open(WS.LINK_URL_DOC' in t or 'android.nextapp.com/site/websharing' in t: raise RuntimeError(f'external web docs action remains in {rel}')
    refs='\n'.join(p.read_text(errors='ignore') for p in web.rglob('*.js'))
    if 'image/branding/' in refs: raise RuntimeError('deleted branding image path still referenced')
    print('stage07c help/Web Access vendor branding and external support links removed')
if __name__=='__main__': main()
