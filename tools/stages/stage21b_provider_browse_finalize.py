#!/usr/bin/env python3
from pathlib import Path
import argparse,re,xml.etree.ElementTree as ET

VC='9109025'

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

    # Keep DW available as a generic content picker. More importantly, Android
    # file-manager "Browse with" resolvers (including App Manager) use exactly:
    # ACTION_VIEW + MIME resource/folder + a URI whose path is the directory.
    # Register ExplorerActivity for that contract so the resolver shows the
    # normal "DW File Manager" activity label/icon instead of File Chooser.
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

    explorer=next((x for x in app.findall('activity') if x.get(A+'name')=='dw.filemanager.ui.ExplorerActivity'),None)
    if explorer is None: raise RuntimeError('ExplorerActivity manifest entry missing')
    explorer.set(A+'exported','true')
    folder_types=('resource/folder','vnd.android.document/directory','inode/directory','application/x-directory')
    folder_filter=None
    for f in explorer.findall('intent-filter'):
        actions={x.get(A+'name') for x in f.findall('action')}
        if 'android.intent.action.VIEW' in actions and any(x.get(A+'mimeType')=='resource/folder' for x in f.findall('data')):
            folder_filter=f; break
    if folder_filter is None:
        folder_filter=ET.SubElement(explorer,'intent-filter')
        ET.SubElement(folder_filter,'action',{A+'name':'android.intent.action.VIEW'})
        ET.SubElement(folder_filter,'category',{A+'name':'android.intent.category.DEFAULT'})
    cats={x.get(A+'name') for x in folder_filter.findall('category')}
    if 'android.intent.category.DEFAULT' not in cats:
        ET.SubElement(folder_filter,'category',{A+'name':'android.intent.category.DEFAULT'})
    present={x.get(A+'mimeType') for x in folder_filter.findall('data')}
    for mime in folder_types:
        if mime not in present:
            ET.SubElement(folder_filter,'data',{A+'mimeType':mime})

    ET.indent(tree,space='    '); tree.write(mp,encoding='utf-8',xml_declaration=True)

    # ExplorerActivity already has a native y(Uri, shell) folder-opening method.
    # Route external ACTION_VIEW/resource-folder launches into it. Use the shell
    # catalog so /data, /system, etc. can use the Stage21 Shizuku-backed backend;
    # ensurePermission() requests Shizuku access when a server is available and
    # preserves the existing real-root/su fallback when it is not.
    ep=sm/'dw/filemanager/ui/ExplorerActivity.smali'
    et=ep.read_text()
    pat=re.compile(r'(\.method public final onCreate\(Landroid/os/Bundle;\)V\n)(.*?)(\n\.end method)',re.S)
    m=pat.search(et)
    if not m: raise RuntimeError('ExplorerActivity onCreate method missing')
    body=m.group(2)
    anchor='''    :cond_0\n    return-void\n'''
    if body.count(anchor)!=1:
        raise RuntimeError('ExplorerActivity onCreate return anchor changed: '+str(body.count(anchor)))
    hook=r'''    :cond_0
    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;
    move-result-object p1
    if-eqz p1, :dw_browse_done

    invoke-virtual {p1}, Landroid/content/Intent;->getAction()Ljava/lang/String;
    move-result-object v0
    const-string v1, "android.intent.action.VIEW"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :dw_browse_done

    invoke-virtual {p1}, Landroid/content/Intent;->getType()Ljava/lang/String;
    move-result-object v0
    const-string v1, "resource/folder"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :dw_browse_done

    invoke-virtual {p1}, Landroid/content/Intent;->getData()Landroid/net/Uri;
    move-result-object p1
    if-eqz p1, :dw_browse_done

    invoke-static {p0}, Ldw/filemanager/shizuku/ShizukuBridge;->ensurePermission(Landroid/content/Context;)Z
    move-result v0
    if-eqz v0, :dw_browse_done

    const/4 v0, 0x1
    invoke-virtual {p0, p1, v0}, Ldw/filemanager/ui/ExplorerActivity;->y(Landroid/net/Uri;Z)V

    :dw_browse_done
    return-void
'''
    body=body.replace(anchor,hook,1)
    et=et[:m.start(2)]+body+et[m.end(2):]
    ep.write_text(et)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    mt=mp.read_text(); pt=p.read_text(); xt=ep.read_text()
    for tok in ('android.intent.action.GET_CONTENT','android.intent.category.OPENABLE','android:mimeType="*/*"',
                'android.intent.action.VIEW','android:mimeType="resource/folder"'):
        if tok not in mt: raise RuntimeError('Browse resolver integration missing '+tok)
    for tok in ('android.intent.action.VIEW','resource/folder','ShizukuBridge;->ensurePermission','ExplorerActivity;->y(Landroid/net/Uri;Z)V'):
        if tok not in xt: raise RuntimeError('external folder open hook missing '+tok)
    if '{:try_canon .. :try_canon} :canon_fail' in pt:
        raise RuntimeError('duplicate provider try label survived')
    print('stage21b exact ACTION_VIEW resource/folder Browse resolver + requested-folder routing installed; vc='+VC)

if __name__=='__main__': main()
