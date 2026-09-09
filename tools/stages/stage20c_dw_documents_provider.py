#!/usr/bin/env python3
from pathlib import Path
import argparse,re,xml.etree.ElementTree as ET

VC='9109022'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'
    provider_dir=sm/'dw/filemanager/provider'; provider_dir.mkdir(parents=True, exist_ok=True)
    provider=r'''.class public final Ldw/filemanager/provider/DwDocumentsProvider;
    .super Landroid/provider/DocumentsProvider;
    .source "DWDocumentsProvider"

    .method public constructor <init>()V
        .locals 0
        invoke-direct {p0}, Landroid/provider/DocumentsProvider;-><init>()V
        return-void
    .end method

    .method private static rootFile()Ljava/io/File;
        .locals 1
        invoke-static {}, Landroid/os/Environment;->getExternalStorageDirectory()Ljava/io/File;
        move-result-object v0
        return-object v0
    .end method

    .method private static checked(Ljava/lang/String;)Ljava/io/File;
        .locals 5
        :try_start
        new-instance v0, Ljava/io/File;
        invoke-direct {v0, p0}, Ljava/io/File;-><init>(Ljava/lang/String;)V
        invoke-virtual {v0}, Ljava/io/File;->getCanonicalFile()Ljava/io/File;
        move-result-object v0
        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->rootFile()Ljava/io/File;
        move-result-object v1
        invoke-virtual {v1}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v1
        invoke-virtual {v0}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v2
        invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
        move-result v3
        if-nez v3, :ok
        new-instance v3, Ljava/lang/StringBuilder;
        invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
        invoke-virtual {v3, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
        const-string v4, "/"
        invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
        invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
        move-result-object v1
        invoke-virtual {v2, v1}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
        move-result v1
        if-eqz v1, :bad
        :ok
        return-object v0
        :bad
        new-instance v0, Ljava/io/FileNotFoundException;
        const-string v1, "Path is outside DW Main Storage root"
        invoke-direct {v0, v1}, Ljava/io/FileNotFoundException;-><init>(Ljava/lang/String;)V
        throw v0
        :try_end
        .catch Ljava/io/IOException; {:try_start .. :try_end} :io
        :io
        move-exception v0
        instance-of v1, v0, Ljava/io/FileNotFoundException;
        if-eqz v1, :wrap
        check-cast v0, Ljava/io/FileNotFoundException;
        throw v0
        :wrap
        new-instance v1, Ljava/io/FileNotFoundException;
        invoke-virtual {v0}, Ljava/lang/Throwable;->getMessage()Ljava/lang/String;
        move-result-object v0
        invoke-direct {v1, v0}, Ljava/io/FileNotFoundException;-><init>(Ljava/lang/String;)V
        throw v1
    .end method

    .method private static mime(Ljava/io/File;)Ljava/lang/String;
        .locals 2
        invoke-virtual {p0}, Ljava/io/File;->isDirectory()Z
        move-result v0
        if-eqz v0, :file
        const-string v0, "vnd.android.document/directory"
        return-object v0
        :file
        invoke-virtual {p0}, Ljava/io/File;->getName()Ljava/lang/String;
        move-result-object v0
        invoke-static {v0}, Ljava/net/URLConnection;->guessContentTypeFromName(Ljava/lang/String;)Ljava/lang/String;
        move-result-object v0
        if-nez v0, :done
        const-string v0, "application/octet-stream"
        :done
        return-object v0
    .end method

    .method private static addDocument(Landroid/database/MatrixCursor;Ljava/io/File;)V
        .locals 8
        invoke-virtual {p0}, Landroid/database/MatrixCursor;->newRow()Landroid/database/MatrixCursor$RowBuilder;
        move-result-object v0
        :try_start
        invoke-virtual {p1}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v1
        :try_end
        .catch Ljava/io/IOException; {:try_start .. :try_end} :canon_fail
        goto :canon_ok
        :canon_fail
        invoke-virtual {p1}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;
        move-result-object v1
        :canon_ok
        invoke-virtual {v0, v1}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;

        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->rootFile()Ljava/io/File;
        move-result-object v2
        :try_start2
        invoke-virtual {v2}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v2
        :try_end2
        .catch Ljava/io/IOException; {:try_start2 .. :try_end2} :root_fail
        goto :root_ok
        :root_fail
        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->rootFile()Ljava/io/File;
        move-result-object v3
        invoke-virtual {v3}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;
        move-result-object v2
        :root_ok
        invoke-virtual {v1, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
        move-result v2
        if-eqz v2, :normal_name
        const-string v3, "Main Storage"
        goto :name_ready
        :normal_name
        invoke-virtual {p1}, Ljava/io/File;->getName()Ljava/lang/String;
        move-result-object v3
        :name_ready
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;

        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->mime(Ljava/io/File;)Ljava/lang/String;
        move-result-object v3
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;

        invoke-virtual {p1}, Ljava/io/File;->isDirectory()Z
        move-result v3
        if-eqz v3, :file_flags
        const/16 v4, 0x8
        if-nez v2, :flags_ready
        or-int/lit8 v4, v4, 0x4
        or-int/lit8 v4, v4, 0x40
        goto :flags_ready
        :file_flags
        const/16 v4, 0x46
        :flags_ready
        invoke-static {v4}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
        move-result-object v4
        invoke-virtual {v0, v4}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;

        invoke-virtual {p1}, Ljava/io/File;->length()J
        move-result-wide v4
        invoke-static {v4, v5}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;
        move-result-object v4
        invoke-virtual {v0, v4}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;

        invoke-virtual {p1}, Ljava/io/File;->lastModified()J
        move-result-wide v4
        invoke-static {v4, v5}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;
        move-result-object v4
        invoke-virtual {v0, v4}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        return-void
    .end method

    .method private static deleteTree(Ljava/io/File;)Z
        .locals 5
        invoke-virtual {p0}, Ljava/io/File;->isDirectory()Z
        move-result v0
        if-eqz v0, :delete
        invoke-virtual {p0}, Ljava/io/File;->listFiles()[Ljava/io/File;
        move-result-object v0
        if-eqz v0, :delete
        array-length v1, v0
        const/4 v2, 0x0
        :loop
        if-ge v2, v1, :delete
        aget-object v3, v0, v2
        invoke-static {v3}, Ldw/filemanager/provider/DwDocumentsProvider;->deleteTree(Ljava/io/File;)Z
        move-result v4
        if-eqz v4, :fail
        add-int/lit8 v2, v2, 0x1
        goto :loop
        :delete
        invoke-virtual {p0}, Ljava/io/File;->delete()Z
        move-result v0
        return v0
        :fail
        const/4 v0, 0x0
        return v0
    .end method

    .method public onCreate()Z
        .locals 1
        const/4 v0, 0x1
        return v0
    .end method

    .method public queryRoots([Ljava/lang/String;)Landroid/database/Cursor;
        .locals 8
        const-string v0, "root_id"
        const-string v1, "document_id"
        const-string v2, "title"
        const-string v3, "summary"
        const-string v4, "flags"
        const-string v5, "icon"
        const-string v6, "available_bytes"
        const-string v7, "mime_types"
        filled-new-array/range {v0 .. v7}, [Ljava/lang/String;
        move-result-object v0
        new-instance v1, Landroid/database/MatrixCursor;
        invoke-direct {v1, v0}, Landroid/database/MatrixCursor;-><init>([Ljava/lang/String;)V
        invoke-virtual {v1}, Landroid/database/MatrixCursor;->newRow()Landroid/database/MatrixCursor$RowBuilder;
        move-result-object v0
        const-string v2, "main"
        invoke-virtual {v0, v2}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->rootFile()Ljava/io/File;
        move-result-object v2
        invoke-virtual {v2}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;
        move-result-object v3
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        const-string v3, "DW File Manager"
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        const-string v3, "Main Storage"
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        const/16 v3, 0x13
        invoke-static {v3}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
        move-result-object v3
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        const/4 v3, 0x0
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        invoke-virtual {v2}, Ljava/io/File;->getUsableSpace()J
        move-result-wide v3
        invoke-static {v3, v4}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;
        move-result-object v3
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        const-string v3, "*/*"
        invoke-virtual {v0, v3}, Landroid/database/MatrixCursor$RowBuilder;->add(Ljava/lang/Object;)Landroid/database/MatrixCursor$RowBuilder;
        return-object v1
    .end method

    .method private static columns()[Ljava/lang/String;
        .locals 6
        const-string v0, "document_id"
        const-string v1, "_display_name"
        const-string v2, "mime_type"
        const-string v3, "flags"
        const-string v4, "_size"
        const-string v5, "last_modified"
        filled-new-array/range {v0 .. v5}, [Ljava/lang/String;
        move-result-object v0
        return-object v0
    .end method

    .method public queryDocument(Ljava/lang/String;[Ljava/lang/String;)Landroid/database/Cursor;
        .locals 2
        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->columns()[Ljava/lang/String;
        move-result-object v0
        new-instance v1, Landroid/database/MatrixCursor;
        invoke-direct {v1, v0}, Landroid/database/MatrixCursor;-><init>([Ljava/lang/String;)V
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        invoke-static {v1, v0}, Ldw/filemanager/provider/DwDocumentsProvider;->addDocument(Landroid/database/MatrixCursor;Ljava/io/File;)V
        return-object v1
    .end method

    .method public queryChildDocuments(Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Landroid/database/Cursor;
        .locals 6
        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->columns()[Ljava/lang/String;
        move-result-object v0
        new-instance v1, Landroid/database/MatrixCursor;
        invoke-direct {v1, v0}, Landroid/database/MatrixCursor;-><init>([Ljava/lang/String;)V
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        invoke-virtual {v0}, Ljava/io/File;->listFiles()[Ljava/io/File;
        move-result-object v2
        if-eqz v2, :done
        array-length v3, v2
        const/4 v4, 0x0
        :loop
        if-ge v4, v3, :done
        aget-object v5, v2, v4
        invoke-static {v1, v5}, Ldw/filemanager/provider/DwDocumentsProvider;->addDocument(Landroid/database/MatrixCursor;Ljava/io/File;)V
        add-int/lit8 v4, v4, 0x1
        goto :loop
        :done
        return-object v1
    .end method

    .method public openDocument(Ljava/lang/String;Ljava/lang/String;Landroid/os/CancellationSignal;)Landroid/os/ParcelFileDescriptor;
        .locals 2
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        invoke-static {p2}, Landroid/os/ParcelFileDescriptor;->parseMode(Ljava/lang/String;)I
        move-result v1
        invoke-static {v0, v1}, Landroid/os/ParcelFileDescriptor;->open(Ljava/io/File;I)Landroid/os/ParcelFileDescriptor;
        move-result-object v0
        return-object v0
    .end method

    .method public createDocument(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
        .locals 4
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        new-instance v1, Ljava/io/File;
        invoke-direct {v1, v0, p3}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
        const-string v2, "vnd.android.document/directory"
        invoke-virtual {v2, p2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
        move-result v2
        if-eqz v2, :file
        invoke-virtual {v1}, Ljava/io/File;->mkdir()Z
        move-result v2
        if-eqz v2, :fail
        goto :ok
        :file
        :try_start
        invoke-virtual {v1}, Ljava/io/File;->createNewFile()Z
        move-result v2
        if-eqz v2, :fail
        :try_end
        .catch Ljava/io/IOException; {:try_start .. :try_end} :fail
        :ok
        :try_canon
        invoke-virtual {v1}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v0
        return-object v0
        :try_canon
        .catch Ljava/io/IOException; {:try_canon .. :try_canon} :canon_fail
        :canon_fail
        invoke-virtual {v1}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;
        move-result-object v0
        return-object v0
        :fail
        new-instance v0, Ljava/io/FileNotFoundException;
        const-string v1, "Unable to create document"
        invoke-direct {v0, v1}, Ljava/io/FileNotFoundException;-><init>(Ljava/lang/String;)V
        throw v0
    .end method

    .method public deleteDocument(Ljava/lang/String;)V
        .locals 2
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        invoke-static {}, Ldw/filemanager/provider/DwDocumentsProvider;->rootFile()Ljava/io/File;
        move-result-object v1
        invoke-virtual {v0, v1}, Ljava/io/File;->equals(Ljava/lang/Object;)Z
        move-result v1
        if-nez v1, :fail
        invoke-static {v0}, Ldw/filemanager/provider/DwDocumentsProvider;->deleteTree(Ljava/io/File;)Z
        move-result v1
        if-eqz v1, :fail
        return-void
        :fail
        new-instance v0, Ljava/io/FileNotFoundException;
        const-string v1, "Unable to delete document"
        invoke-direct {v0, v1}, Ljava/io/FileNotFoundException;-><init>(Ljava/lang/String;)V
        throw v0
    .end method

    .method public renameDocument(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
        .locals 4
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        invoke-virtual {v0}, Ljava/io/File;->getParentFile()Ljava/io/File;
        move-result-object v1
        if-eqz v1, :fail
        new-instance v2, Ljava/io/File;
        invoke-direct {v2, v1, p2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
        invoke-virtual {v0, v2}, Ljava/io/File;->renameTo(Ljava/io/File;)Z
        move-result v3
        if-eqz v3, :fail
        :try_start
        invoke-virtual {v2}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v0
        return-object v0
        :try_end
        .catch Ljava/io/IOException; {:try_start .. :try_end} :abs
        :abs
        invoke-virtual {v2}, Ljava/io/File;->getAbsolutePath()Ljava/lang/String;
        move-result-object v0
        return-object v0
        :fail
        new-instance v0, Ljava/io/FileNotFoundException;
        const-string v1, "Unable to rename document"
        invoke-direct {v0, v1}, Ljava/io/FileNotFoundException;-><init>(Ljava/lang/String;)V
        throw v0
    .end method

    .method public isChildDocument(Ljava/lang/String;Ljava/lang/String;)Z
        .locals 5
        :try_start
        invoke-static {p1}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v0
        invoke-static {p2}, Ldw/filemanager/provider/DwDocumentsProvider;->checked(Ljava/lang/String;)Ljava/io/File;
        move-result-object v1
        invoke-virtual {v0}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v2
        invoke-virtual {v1}, Ljava/io/File;->getCanonicalPath()Ljava/lang/String;
        move-result-object v3
        invoke-virtual {v2, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
        move-result v4
        if-nez v4, :yes
        new-instance v4, Ljava/lang/StringBuilder;
        invoke-direct {v4, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
        const-string v2, "/"
        invoke-virtual {v4, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
        invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
        move-result-object v2
        invoke-virtual {v3, v2}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z
        move-result v4
        return v4
        :yes
        const/4 v4, 0x1
        return v4
        :try_end
        .catch Ljava/lang/Throwable; {:try_start .. :try_end} :no
        :no
        const/4 v4, 0x0
        return v4
    .end method
    '''
    (provider_dir/'DwDocumentsProvider.smali').write_text(provider)

    mp=root/'AndroidManifest.xml'; A='{http://schemas.android.com/apk/res/android}'
    ET.register_namespace('android','http://schemas.android.com/apk/res/android')
    tree=ET.parse(mp); mr=tree.getroot(); app=mr.find('application')

    if not any(x.get(A+'name')=='android.permission.MANAGE_DOCUMENTS' for x in mr.findall('uses-permission')):
        ET.SubElement(mr,'uses-permission',{A+'name':'android.permission.MANAGE_DOCUMENTS'})

    if not any(x.get(A+'name')=='dw.filemanager.provider.DwDocumentsProvider' for x in app.findall('provider')):
        pr=ET.SubElement(app,'provider',{
            A+'name':'dw.filemanager.provider.DwDocumentsProvider',
            A+'authorities':'com.mekromn.dwfilemanager.documents',
            A+'exported':'true',
            A+'grantUriPermissions':'true',
            A+'permission':'android.permission.MANAGE_DOCUMENTS'
        })
        flt=ET.SubElement(pr,'intent-filter')
        ET.SubElement(flt,'action',{A+'name':'android.content.action.DOCUMENTS_PROVIDER'})

    chooser=next((x for x in app.findall('activity') if x.get(A+'name')=='dw.filemanager.ui.filechooser.ChooserActivity'),None)
    if chooser is None: raise RuntimeError('ChooserActivity manifest entry missing')
    has_pick=any(any(a.get(A+'name')=='android.intent.action.PICK' for a in f.findall('action')) for f in chooser.findall('intent-filter'))
    if not has_pick:
        f=ET.SubElement(chooser,'intent-filter')
        ET.SubElement(f,'action',{A+'name':'android.intent.action.PICK'})
        ET.SubElement(f,'category',{A+'name':'android.intent.category.DEFAULT'})
        ET.SubElement(f,'data',{A+'mimeType':'image/*'})
        ET.SubElement(f,'data',{A+'mimeType':'video/*'})

    ET.indent(tree,space='    '); tree.write(mp,encoding='utf-8',xml_declaration=True)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    mt=mp.read_text(); pt=(provider_dir/'DwDocumentsProvider.smali').read_text()
    for tok in ('android.content.action.DOCUMENTS_PROVIDER','com.mekromn.dwfilemanager.documents','android.intent.action.PICK'):
        if tok not in mt: raise RuntimeError('provider/browser manifest integration missing '+tok)
    for tok in ('queryRoots','queryDocument','queryChildDocuments','openDocument','createDocument','deleteDocument','renameDocument','isChildDocument'):
        if tok not in pt: raise RuntimeError('DocumentsProvider missing '+tok)
    print('stage20c added DW SAF DocumentsProvider + external image/video browse integration; vc='+VC)

if __name__=='__main__': main()
