#!/usr/bin/env python3
from pathlib import Path
import argparse,re,xml.etree.ElementTree as ET

VC='9109024'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'

    # Stage20c's createDocument catch range accidentally reused the same label for
    # both the beginning and end of the canonical-path try block. Smali requires
    # unique labels within a method. Repair only that exact generated sequence.
    p=sm/'dw/filemanager/provider/DwDocumentsProvider.smali'
    t=p.read_text()
    marker='''        return-object v0\n        :try_canon\n        .catch Ljava/io/IOException; {:try_canon .. :try_canon} :canon_fail'''
    replacement='''        return-object v0\n        :try_canon_end\n        .catch Ljava/io/IOException; {:try_canon .. :try_canon_end} :canon_fail'''
    if t.count(marker)!=1:
        raise RuntimeError('DwDocumentsProvider createDocument duplicate-label anchor changed: '+str(t.count(marker)))
    t=t.replace(marker,replacement,1)
    if t.count('\n        :try_canon\n')!=1 or t.count('\n        :try_canon_end\n')!=1:
        raise RuntimeError('DwDocumentsProvider canonical try labels are not unique after repair')
    p.write_text(t)

    # Make DW a generic Android "Browse" / content picker target in addition to
    # exposing its DocumentsProvider root to the system DocumentsUI.
    mp=root/'AndroidManifest.xml'; A='{http://schemas.android.com/apk/res/android}'
    ET.register_namespace('android','http://schemas.android.com/apk/res/android')
    tree=ET.parse(mp); mr=tree.getroot(); app=mr.find('application')
    chooser=next((x for x in app.findall('activity') if x.get(A+'name')=='dw.filemanager.ui.filechooser.ChooserActivity'),None)
    if chooser is None: raise RuntimeError('ChooserActivity manifest entry missing')
    chooser.set(A+'exported','true')
    has_get=False
    for f in chooser.findall('intent-filter'):
        actions={x.get(A+'name') for x in f.findall('action')}
        if 'android.intent.action.GET_CONTENT' in actions:
            has_get=True
            cats={x.get(A+'name') for x in f.findall('category')}
            if 'android.intent.category.DEFAULT' not in cats:
                ET.SubElement(f,'category',{A+'name':'android.intent.category.DEFAULT'})
            if 'android.intent.category.OPENABLE' not in cats:
                ET.SubElement(f,'category',{A+'name':'android.intent.category.OPENABLE'})
            if not any(x.get(A+'mimeType')=='*/*' for x in f.findall('data')):
                ET.SubElement(f,'data',{A+'mimeType':'*/*'})
            break
    if not has_get:
        f=ET.SubElement(chooser,'intent-filter')
        ET.SubElement(f,'action',{A+'name':'android.intent.action.GET_CONTENT'})
        ET.SubElement(f,'category',{A+'name':'android.intent.category.DEFAULT'})
        ET.SubElement(f,'category',{A+'name':'android.intent.category.OPENABLE'})
        ET.SubElement(f,'data',{A+'mimeType':'*/*'})
    ET.indent(tree,space='    '); tree.write(mp,encoding='utf-8',xml_declaration=True)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    mt=mp.read_text(); pt=p.read_text()
    for tok in ('android.intent.action.GET_CONTENT','android.intent.category.OPENABLE','android:mimeType="*/*"'):
        if tok not in mt: raise RuntimeError('generic Browse resolver integration missing '+tok)
    if '{:try_canon .. :try_canon} :canon_fail' in pt:
        raise RuntimeError('duplicate provider try label survived')
    print('stage21b repaired DW DocumentsProvider smali and added generic Android Browse resolver integration; vc='+VC)

if __name__=='__main__': main()
