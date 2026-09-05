#!/usr/bin/env python3
from pathlib import Path
import argparse, os, re, shutil, subprocess, tempfile, zipfile

VC='9109028'

def run(*args,cwd=None):
    subprocess.run([str(x) for x in args],cwd=cwd,check=True)

def newest(base):
    ds=[p for p in Path(base).iterdir() if p.is_dir()]
    if not ds: raise RuntimeError('no SDK directories in '+str(base))
    def key(p):
        nums=re.findall(r'\d+',p.name)
        return tuple(int(x) for x in nums) if nums else (0,)
    return sorted(ds,key=key)[-1]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; repo=Path.cwd(); sm=root/'smali'
    android_home=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not android_home: raise RuntimeError('ANDROID_HOME/ANDROID_SDK_ROOT required')
    bt=newest(Path(android_home)/'build-tools'); platform=newest(Path(android_home)/'platforms')
    d8=bt/'d8'; aapt2=bt/'aapt2'; android_jar=platform/'android.jar'; apktool=repo/'apktool.jar'
    for p in (d8,aapt2,android_jar,apktool):
        if not p.exists(): raise RuntimeError('required build tool missing: '+str(p))

    java=r'''package dw.filemanager.provider;

import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.CancellationSignal;
import android.os.Environment;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import android.webkit.MimeTypeMap;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import dw.filemanager.shizuku.ShizukuBridge;

public final class DwDocumentsProvider extends DocumentsProvider {
    private static final String ROOT_MAIN="main";
    private static final String ROOT_SYSTEM="system";
    private static final String MAIN_PREFIX="main:";
    private static final String SYS_PREFIX="sys:";
    private static final String DIR_MIME=DocumentsContract.Document.MIME_TYPE_DIR;
    private static final String[] DOC_COLUMNS={
            DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            DocumentsContract.Document.COLUMN_MIME_TYPE,
            DocumentsContract.Document.COLUMN_FLAGS,
            DocumentsContract.Document.COLUMN_SIZE,
            DocumentsContract.Document.COLUMN_LAST_MODIFIED
    };
    private static final String[] ROOT_COLUMNS={
            DocumentsContract.Root.COLUMN_ROOT_ID,
            DocumentsContract.Root.COLUMN_DOCUMENT_ID,
            DocumentsContract.Root.COLUMN_TITLE,
            DocumentsContract.Root.COLUMN_SUMMARY,
            DocumentsContract.Root.COLUMN_FLAGS,
            DocumentsContract.Root.COLUMN_ICON,
            DocumentsContract.Root.COLUMN_AVAILABLE_BYTES,
            DocumentsContract.Root.COLUMN_MIME_TYPES
    };

    private static final class Meta {
        String path; boolean dir; long size; long mtime;
        Meta(String p, boolean d, long s, long m){path=p;dir=d;size=s;mtime=m;}
    }

    private static String q(String s){ return "'"+s.replace("'", "'\"'\"'")+"'"; }
    private static File mainRoot(){ return Environment.getExternalStorageDirectory(); }
    private static String canonical(String p) throws FileNotFoundException {
        try { return new File(p).getCanonicalPath(); }
        catch(IOException e){ throw fnf(e.getMessage()); }
    }
    private static FileNotFoundException fnf(String m){ return new FileNotFoundException(m==null?"DW filesystem error":m); }
    private static String encodeMain(String p) throws FileNotFoundException { return MAIN_PREFIX+canonical(p); }
    private static String encodeSys(String p) throws FileNotFoundException { return SYS_PREFIX+canonical(p); }
    private static boolean isSys(String id){ return id!=null && id.startsWith(SYS_PREFIX); }
    private static String decode(String id) throws FileNotFoundException {
        if(id==null) throw fnf("Missing document id");
        if(id.startsWith(MAIN_PREFIX)){
            String p=canonical(id.substring(MAIN_PREFIX.length()));
            String r=canonical(mainRoot().getAbsolutePath());
            if(!p.equals(r) && !p.startsWith(r+File.separator)) throw fnf("Path outside Main Storage");
            return p;
        }
        if(id.startsWith(SYS_PREFIX)){
            String p=canonical(id.substring(SYS_PREFIX.length()));
            if(!p.startsWith(File.separator)) throw fnf("Invalid System path");
            return p;
        }
        throw fnf("Unknown document id");
    }
    private static String displayName(String p, boolean root, boolean sys){
        if(root) return sys?"System":"Main Storage";
        String n=new File(p).getName(); return n.length()==0?p:n;
    }
    private static String mime(String p, boolean dir){
        if(dir) return DIR_MIME;
        String n=new File(p).getName(); int dot=n.lastIndexOf('.');
        if(dot>=0 && dot+1<n.length()){
            String m=MimeTypeMap.getSingleton().getMimeTypeFromExtension(n.substring(dot+1).toLowerCase());
            if(m!=null) return m;
        }
        return "application/octet-stream";
    }
    private static void requireShizuku() throws FileNotFoundException {
        if(!ShizukuBridge.isAuthorized()) throw fnf("Grant DW File Manager Shizuku permission first");
    }
    private static Process start(String cmd) throws FileNotFoundException {
        requireShizuku(); Process p=ShizukuBridge.startCommand(cmd);
        if(p==null) throw fnf("Unable to start Shizuku shell command"); return p;
    }
    private static byte[] readFully(InputStream in) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream(); byte[] b=new byte[16384];
        for(int n;(n=in.read(b))>=0;) out.write(b,0,n); return out.toByteArray();
    }
    private static String run(String cmd) throws FileNotFoundException {
        Process p=start(cmd);
        try {
            byte[] out=readFully(p.getInputStream());
            byte[] err=readFully(p.getErrorStream());
            int rc=p.waitFor();
            String es=new String(err,StandardCharsets.UTF_8).trim();
            if(rc!=0) throw fnf(es.length()==0?"Shizuku shell command failed":es);
            return new String(out,StandardCharsets.UTF_8);
        } catch(Exception e){ if(e instanceof FileNotFoundException) throw (FileNotFoundException)e; throw fnf(e.getMessage()); }
        finally { p.destroy(); }
    }
    private static Meta parseStat(String line) throws FileNotFoundException {
        String[] a=line.split("\\t",4); if(a.length<4) throw fnf("Unable to parse System metadata: "+line);
        boolean d=a[0].length()>0 && a[0].charAt(0)=='d';
        long s=0,m=0; try{s=Long.parseLong(a[1]);}catch(Exception ignored){} try{m=Long.parseLong(a[2])*1000L;}catch(Exception ignored){}
        return new Meta(a[3],d,s,m);
    }
    private static Meta statSys(String path) throws FileNotFoundException {
        String o=run("/system/bin/toybox stat -c '%A\\t%s\\t%Y\\t%n' -- "+q(path));
        int nl=o.indexOf('\n'); if(nl>=0)o=o.substring(0,nl); return parseStat(o);
    }
    private static List<Meta> listSys(String path) throws FileNotFoundException {
        String cmd="/system/bin/toybox find "+q(path)+" -mindepth 1 -maxdepth 1 -exec /system/bin/toybox stat -c '%A\\t%s\\t%Y\\t%n' -- '{}' ';'";
        String o=run(cmd); List<Meta> out=new ArrayList<>();
        BufferedReader r=new BufferedReader(new InputStreamReader(new java.io.ByteArrayInputStream(o.getBytes(StandardCharsets.UTF_8)),StandardCharsets.UTF_8));
        try { for(String line;(line=r.readLine())!=null;) if(line.length()!=0) out.add(parseStat(line)); }
        catch(IOException e){ throw fnf(e.getMessage()); }
        return out;
    }
    private static void addMain(MatrixCursor c, File f, boolean root) throws FileNotFoundException {
        String p=canonical(f.getAbsolutePath()); int flags;
        if(f.isDirectory()) flags=DocumentsContract.Document.FLAG_DIR_SUPPORTS_CREATE|DocumentsContract.Document.FLAG_SUPPORTS_DELETE|DocumentsContract.Document.FLAG_SUPPORTS_RENAME;
        else flags=DocumentsContract.Document.FLAG_SUPPORTS_WRITE|DocumentsContract.Document.FLAG_SUPPORTS_DELETE|DocumentsContract.Document.FLAG_SUPPORTS_RENAME;
        if(root) flags=DocumentsContract.Document.FLAG_DIR_SUPPORTS_CREATE;
        c.newRow().add(encodeMain(p)).add(displayName(p,root,false)).add(mime(p,f.isDirectory())).add(flags).add(f.length()).add(f.lastModified());
    }
    private static void addSys(MatrixCursor c, Meta m, boolean root) throws FileNotFoundException {
        int flags=m.dir ? DocumentsContract.Document.FLAG_DIR_SUPPORTS_CREATE|DocumentsContract.Document.FLAG_SUPPORTS_DELETE|DocumentsContract.Document.FLAG_SUPPORTS_RENAME : DocumentsContract.Document.FLAG_SUPPORTS_WRITE|DocumentsContract.Document.FLAG_SUPPORTS_DELETE|DocumentsContract.Document.FLAG_SUPPORTS_RENAME;
        if(root) flags=DocumentsContract.Document.FLAG_DIR_SUPPORTS_CREATE;
        c.newRow().add(encodeSys(m.path)).add(displayName(m.path,root,true)).add(mime(m.path,m.dir)).add(flags).add(m.size).add(m.mtime);
    }

    @Override public boolean onCreate(){ return true; }

    @Override public Cursor queryRoots(String[] projection) throws FileNotFoundException {
        MatrixCursor c=new MatrixCursor(ROOT_COLUMNS);
        File m=mainRoot();
        int rf=DocumentsContract.Root.FLAG_SUPPORTS_CREATE|DocumentsContract.Root.FLAG_LOCAL_ONLY|DocumentsContract.Root.FLAG_SUPPORTS_IS_CHILD;
        c.newRow().add(ROOT_MAIN).add(encodeMain(m.getAbsolutePath())).add("DW File Manager").add("Main Storage").add(rf).add(0).add(m.getUsableSpace()).add("*/*");
        File slash=new File("/");
        String summary=ShizukuBridge.isAuthorized()?"System (Shizuku)":"System — grant Shizuku in DW first";
        c.newRow().add(ROOT_SYSTEM).add(encodeSys("/")).add("DW File Manager").add(summary).add(rf).add(0).add(slash.getUsableSpace()).add("*/*");
        return c;
    }

    @Override public Cursor queryDocument(String documentId,String[] projection) throws FileNotFoundException {
        MatrixCursor c=new MatrixCursor(DOC_COLUMNS); String p=decode(documentId);
        if(isSys(documentId)) addSys(c,statSys(p),"/".equals(p)); else addMain(c,new File(p),p.equals(canonical(mainRoot().getAbsolutePath())));
        return c;
    }

    @Override public Cursor queryChildDocuments(String parentDocumentId,String[] projection,String sortOrder) throws FileNotFoundException {
        MatrixCursor c=new MatrixCursor(DOC_COLUMNS); String p=decode(parentDocumentId);
        if(isSys(parentDocumentId)) for(Meta m:listSys(p)) addSys(c,m,false);
        else { File[] fs=new File(p).listFiles(); if(fs!=null) for(File f:fs) addMain(c,f,false); }
        return c;
    }

    @Override public ParcelFileDescriptor openDocument(String documentId,String mode,CancellationSignal signal) throws FileNotFoundException {
        final String p=decode(documentId);
        if(!isSys(documentId)) return ParcelFileDescriptor.open(new File(p),ParcelFileDescriptor.parseMode(mode));
        requireShizuku();
        try {
            if(mode!=null && mode.contains("w")){
                final ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();
                new Thread(new Runnable(){ public void run(){
                    Process proc=null; InputStream in=null; OutputStream out=null;
                    try { proc=start("cat > "+q(p)); in=new ParcelFileDescriptor.AutoCloseInputStream(pipe[0]); out=proc.getOutputStream(); byte[] b=new byte[16384]; for(int n;(n=in.read(b))>=0;)out.write(b,0,n); out.flush(); out.close(); readFully(proc.getErrorStream()); proc.waitFor(); }
                    catch(Exception ignored){} finally { try{if(in!=null)in.close();}catch(Exception ignored){} if(proc!=null)proc.destroy(); }
                }},"DW-Shizuku-Provider-Write").start();
                return pipe[1];
            } else {
                final ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();
                new Thread(new Runnable(){ public void run(){
                    Process proc=null; InputStream in=null; OutputStream out=null;
                    try { proc=start("cat -- "+q(p)); in=proc.getInputStream(); out=new ParcelFileDescriptor.AutoCloseOutputStream(pipe[1]); byte[] b=new byte[16384]; for(int n;(n=in.read(b))>=0;)out.write(b,0,n); out.flush(); out.close(); readFully(proc.getErrorStream()); proc.waitFor(); }
                    catch(Exception ignored){} finally { try{if(out!=null)out.close();}catch(Exception ignored){} if(proc!=null)proc.destroy(); }
                }},"DW-Shizuku-Provider-Read").start();
                return pipe[0];
            }
        } catch(IOException e){ throw fnf(e.getMessage()); }
    }

    @Override public String createDocument(String parentDocumentId,String mimeType,String displayName) throws FileNotFoundException {
        String parent=decode(parentDocumentId); String p=canonical(new File(parent,displayName).getAbsolutePath());
        if(isSys(parentDocumentId)){
            if(DIR_MIME.equals(mimeType)) run("mkdir -- "+q(p)); else run(": > "+q(p));
            return encodeSys(p);
        }
        File f=new File(p); try { if(DIR_MIME.equals(mimeType)){if(!f.mkdir())throw fnf("Unable to create directory");} else if(!f.createNewFile())throw fnf("Unable to create file"); }
        catch(IOException e){throw fnf(e.getMessage());} return encodeMain(p);
    }

    @Override public void deleteDocument(String documentId) throws FileNotFoundException {
        String p=decode(documentId); if("/".equals(p))throw fnf("Cannot delete System root");
        if(isSys(documentId)){ run("rm -rf -- "+q(p)); return; }
        File f=new File(p); if(!deleteTree(f))throw fnf("Unable to delete document");
    }
    private static boolean deleteTree(File f){ File[] kids=f.isDirectory()?f.listFiles():null; if(kids!=null)for(File k:kids)if(!deleteTree(k))return false; return f.delete(); }

    @Override public String renameDocument(String documentId,String displayName) throws FileNotFoundException {
        String p=decode(documentId); File old=new File(p), par=old.getParentFile(); if(par==null)throw fnf("Cannot rename root"); String np=canonical(new File(par,displayName).getAbsolutePath());
        if(isSys(documentId)){ run("mv -- "+q(p)+" "+q(np)); return encodeSys(np); }
        if(!old.renameTo(new File(np)))throw fnf("Unable to rename document"); return encodeMain(np);
    }

    @Override public boolean isChildDocument(String parentDocumentId,String documentId){
        try { if(isSys(parentDocumentId)!=isSys(documentId))return false; String p=decode(parentDocumentId), c=decode(documentId); return c.equals(p)||c.startsWith(p.endsWith("/")?p:p+"/"); }
        catch(Exception e){return false;}
    }
}
'''
    stub=r'''package dw.filemanager.shizuku;
public final class ShizukuBridge {
  public static boolean isAuthorized(){ return false; }
  public static java.lang.Process startCommand(String s){ return null; }
}
'''

    tmp=tempfile.TemporaryDirectory(prefix='dw-provider-'); w=Path(tmp.name)
    try:
        src=w/'src'; (src/'dw/filemanager/provider').mkdir(parents=True); (src/'dw/filemanager/shizuku').mkdir(parents=True)
        (src/'dw/filemanager/provider/DwDocumentsProvider.java').write_text(java)
        (src/'dw/filemanager/shizuku/ShizukuBridge.java').write_text(stub)
        stubs=w/'stubs'; stubs.mkdir(); classes=w/'classes'; classes.mkdir()
        run('javac','-source','8','-target','8','-cp',android_jar,'-d',stubs,src/'dw/filemanager/shizuku/ShizukuBridge.java')
        cp=str(android_jar)+os.pathsep+str(stubs)
        run('javac','-source','8','-target','8','-cp',cp,'-d',classes,src/'dw/filemanager/provider/DwDocumentsProvider.java')
        dexout=w/'dexout'; dexout.mkdir()
        classfiles=[str(p) for p in classes.rglob('*.class')]
        run(d8,'--lib',android_jar,'--classpath',stubs,'--output',dexout,*classfiles)
        manifest=w/'AndroidManifest.xml'; manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dw.filemanager.providerprep"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/><application android:theme="@android:style/Theme.Material.NoActionBar"/></manifest>''')
        prep=w/'provider-prep.apk'; run(aapt2,'link','-o',prep,'--manifest',manifest,'-I',android_jar)
        with zipfile.ZipFile(prep,'a',compression=zipfile.ZIP_DEFLATED) as z: z.write(dexout/'classes.dex','classes.dex')
        dec=w/'decoded'; run('java','-jar',apktool,'d','-f',prep,'-o',dec)
        generated=dec/'smali/dw/filemanager/provider'
        if not (generated/'DwDocumentsProvider.smali').exists(): raise RuntimeError('compiled provider smali missing')
        dest=sm/'dw/filemanager/provider'
        if dest.exists(): shutil.rmtree(dest)
        shutil.copytree(generated,dest)
    finally:
        tmp.cleanup()

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(yt)

    pt=(sm/'dw/filemanager/provider/DwDocumentsProvider.smali').read_text()
    for tok in ('System (Shizuku)','ShizukuBridge;->isAuthorized','ShizukuBridge;->startCommand','queryChildDocuments','openDocument','sys:'):
        if tok not in pt: raise RuntimeError('Shizuku DocumentsProvider missing '+tok)
    print('stage21e replaced Main-Storage-only provider with dual Main Storage + System (Shizuku) DocumentsUI roots and pipe-backed protected-file I/O; vc='+VC)

if __name__=='__main__': main()
