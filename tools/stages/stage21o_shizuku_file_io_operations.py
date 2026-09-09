#!/usr/bin/env python3
from pathlib import Path
import argparse, ast, os, re, shutil, subprocess, tempfile, zipfile

VC='9109038'
NS='dw/filemanager/shizuku/'

def run(*args,cwd=None): subprocess.run([str(x) for x in args],cwd=cwd,check=True)
def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing method end '+sig)
    e+=len('\n.end method')
    return s,e,text[s:e]
def newest(path):
    ds=[p for p in path.iterdir() if p.is_dir()]
    if not ds: raise RuntimeError('no SDK directories under '+str(path))
    def key(p):
        nums=re.findall(r'\d+',p.name); return tuple(map(int,nums)) if nums else (0,)
    return max(ds,key=key)
def prepend(text,sig,code,label):
    s,e,m=method(text,sig)
    mm=re.search(r'(    \.locals \d+\n)',m)
    if not mm: raise RuntimeError(label+': .locals missing')
    m=m[:mm.end()]+"\n"+code.rstrip()+"\n"+m[mm.end():]
    return text[:s]+m+text[e:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'; repo=Path.cwd()
    sdk=Path(os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT',''))
    if not sdk.exists(): raise RuntimeError('ANDROID_HOME/ANDROID_SDK_ROOT required')
    bt=newest(sdk/'build-tools'); android=newest(sdk/'platforms')/'android.jar'; apktool=repo/'apktool.jar'
    for p in (bt/'d8',bt/'aapt2',android,apktool):
        if not p.exists(): raise RuntimeError('missing build tool '+str(p))

    tree=ast.parse((repo/'tools/stages/stage21l_shizuku_userservice_filesystem.py').read_text())
    stubs=None
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='stubs':
            stubs=ast.literal_eval(node.value); break
    if not isinstance(stubs,dict): raise RuntimeError('Stage21l stubs not found')

    service=r'''package dw.filemanager.shizuku;

import android.content.Context;
import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.ParcelFileDescriptor;
import android.os.Parcelable;
import android.os.RemoteException;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public final class DwShizukuIoService extends Binder {
    public static final String DESCRIPTOR="dw.filemanager.shizuku.IDwIo";
    public static final int TX_OPEN_READ=IBinder.FIRST_CALL_TRANSACTION;
    public static final int TX_OPEN_WRITE=IBinder.FIRST_CALL_TRANSACTION+1;
    public static final int TX_DELETE=IBinder.FIRST_CALL_TRANSACTION+2;
    public static final int TX_RENAME=IBinder.FIRST_CALL_TRANSACTION+3;
    public static final int TX_MKDIR=IBinder.FIRST_CALL_TRANSACTION+4;
    public static final int TX_SYMLINK=IBinder.FIRST_CALL_TRANSACTION+5;
    public static final int TX_CHMOD=IBinder.FIRST_CALL_TRANSACTION+6;
    public static final int TX_CHOWN=IBinder.FIRST_CALL_TRANSACTION+7;
    public static final int TX_UID=IBinder.FIRST_CALL_TRANSACTION+8;

    public DwShizukuIoService(){super();}
    public DwShizukuIoService(Context ignored){this();}

    private static String path(String p){
        if(p==null || !p.startsWith("/") || p.indexOf(0)>=0) throw new IllegalArgumentException("Expected absolute filesystem path");
        return p;
    }
    private static void copy(InputStream in,OutputStream out)throws IOException{
        byte[] b=new byte[32768];
        try{for(int n;(n=in.read(b))>=0;){if(n>0)out.write(b,0,n);}out.flush();}
        finally{try{in.close();}catch(Throwable ignored){} try{out.close();}catch(Throwable ignored){}}
    }
    private static ParcelFileDescriptor readPipe(final String p)throws IOException{
        final FileInputStream source=new FileInputStream(path(p));
        ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();
        final ParcelFileDescriptor write=pipe[1];
        Thread t=new Thread(new Runnable(){public void run(){
            try{copy(source,new ParcelFileDescriptor.AutoCloseOutputStream(write));}
            catch(Throwable ignored){try{source.close();}catch(Throwable ignored2){} try{write.close();}catch(Throwable ignored2){}}
        }},"DW Shizuku read pump");
        t.setDaemon(true); t.start(); return pipe[0];
    }
    private static ParcelFileDescriptor writePipe(final String p)throws IOException{
        final FileOutputStream target=new FileOutputStream(path(p),false);
        ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createPipe();
        final ParcelFileDescriptor read=pipe[0];
        Thread t=new Thread(new Runnable(){public void run(){
            try{copy(new ParcelFileDescriptor.AutoCloseInputStream(read),target);}
            catch(Throwable ignored){try{read.close();}catch(Throwable ignored2){} try{target.close();}catch(Throwable ignored2){}}
        }},"DW Shizuku write pump");
        t.setDaemon(true); t.start(); return pipe[1];
    }
    private static void deleteOne(String p,boolean recursive)throws IOException{
        p=path(p); File f=new File(p); final StructStat st;
        try{st=Os.lstat(p);}catch(ErrnoException e){throw new IOException(e);}
        if(OsConstants.S_ISDIR(st.st_mode)){
            if(recursive){
                String[] names=f.list();
                if(names==null)throw new IOException("shell uid cannot enumerate directory for recursive delete: "+p);
                for(String name:names){if(name!=null && name.length()>0)deleteOne(new File(f,name).getPath(),true);}
            }
            if(!f.delete())throw new IOException("shell uid could not delete directory: "+p);
        }else if(!f.delete())throw new IOException("shell uid could not delete file: "+p);
    }
    private static void rename(String a,String b)throws IOException{try{Os.rename(path(a),path(b));}catch(ErrnoException e){throw new IOException(e);}}
    private static void mkdir(String p,int mode)throws IOException{try{Os.mkdir(path(p),mode);}catch(ErrnoException e){throw new IOException(e);}}
    private static void symlink(String target,String link)throws IOException{try{Os.symlink(target,path(link));}catch(ErrnoException e){throw new IOException(e);}}
    private static void chmod(String p,int mode)throws IOException{try{Os.chmod(path(p),mode);}catch(ErrnoException e){throw new IOException(e);}}
    private static void chown(String p,int uid,int gid)throws IOException{try{Os.chown(path(p),uid,gid);}catch(ErrnoException e){throw new IOException(e);}}
    private static void writePfd(Parcel reply,ParcelFileDescriptor pfd)throws IOException{
        reply.writeNoException(); reply.writeInt(1); pfd.writeToParcel(reply,Parcelable.PARCELABLE_WRITE_RETURN_VALUE); pfd.close();
    }

    @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{
        if(code==16777115){System.exit(0);return true;}
        if(code==INTERFACE_TRANSACTION){reply.writeString(DESCRIPTOR);return true;}
        try{
            data.enforceInterface(DESCRIPTOR);
            if(code==TX_OPEN_READ){writePfd(reply,readPipe(data.readString()));return true;}
            if(code==TX_OPEN_WRITE){writePfd(reply,writePipe(data.readString()));return true;}
            if(code==TX_DELETE){deleteOne(data.readString(),data.readInt()!=0);reply.writeNoException();return true;}
            if(code==TX_RENAME){rename(data.readString(),data.readString());reply.writeNoException();return true;}
            if(code==TX_MKDIR){mkdir(data.readString(),data.readInt());reply.writeNoException();return true;}
            if(code==TX_SYMLINK){symlink(data.readString(),data.readString());reply.writeNoException();return true;}
            if(code==TX_CHMOD){chmod(data.readString(),data.readInt());reply.writeNoException();return true;}
            if(code==TX_CHOWN){chown(data.readString(),data.readInt(),data.readInt());reply.writeNoException();return true;}
            if(code==TX_UID){reply.writeNoException();reply.writeInt(android.os.Process.myUid());return true;}
        }catch(Throwable t){reply.writeException(new IllegalStateException(t.getClass().getSimpleName()+": "+String.valueOf(t.getMessage())));return true;}
        return super.onTransact(code,data,reply,flags);
    }
}
'''
    client=r'''package dw.filemanager.shizuku;

import android.content.ComponentName;
import android.content.Context;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Parcel;
import android.os.ParcelFileDescriptor;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import rikka.shizuku.Shizuku;

public final class DwShizukuIoClient {
    private static final Object LOCK=new Object();
    private static volatile IBinder binder;
    private static volatile ServiceConnection connection;
    private static volatile Shizuku.UserServiceArgs args;
    private DwShizukuIoClient(){}

    private static Shizuku.UserServiceArgs args(Context c){
        Shizuku.UserServiceArgs a=args;if(a!=null)return a;
        synchronized(LOCK){if(args==null)args=new Shizuku.UserServiceArgs(new ComponentName(c.getApplicationContext(),DwShizukuIoService.class))
            .daemon(false).tag("dw-filemanager-io-v1").version(1).processNameSuffix("dwio");return args;}
    }
    private static IBinder live(){IBinder b=binder;if(b!=null&&b.pingBinder())return b;binder=null;return null;}
    private static IBinder service(final Context context)throws IOException{
        IBinder b=live();if(b!=null)return b;
        if(!Shizuku.pingBinder())throw new IOException("Shizuku Binder is not connected");
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED)throw new IOException("Shizuku permission is not granted");
        if(Looper.myLooper()==Looper.getMainLooper())throw new IOException("Shizuku file I/O initial bind requested on main thread");
        synchronized(LOCK){
            b=live();if(b!=null)return b;
            final CountDownLatch latch=new CountDownLatch(1);final IBinder[] result=new IBinder[1];final Throwable[] err=new Throwable[1];
            final ServiceConnection conn=new ServiceConnection(){
                public void onServiceConnected(ComponentName n,IBinder s){if(s!=null&&s.pingBinder()){binder=s;result[0]=s;}latch.countDown();}
                public void onServiceDisconnected(ComponentName n){binder=null;connection=null;}
            };
            connection=conn;final Shizuku.UserServiceArgs a=args(context);
            new Handler(Looper.getMainLooper()).post(new Runnable(){public void run(){try{Shizuku.bindUserService(a,conn);}catch(Throwable t){err[0]=t;latch.countDown();}}});
            try{if(!latch.await(6000,TimeUnit.MILLISECONDS))throw new IOException("Timed out binding Shizuku file I/O UserService");}
            catch(InterruptedException e){Thread.currentThread().interrupt();throw new IOException("Interrupted binding Shizuku file I/O UserService",e);}
            if(err[0]!=null)throw new IOException("Shizuku file I/O UserService bind failed: "+err[0],err[0]);
            b=result[0]!=null?result[0]:live();if(b==null)throw new IOException("Shizuku file I/O UserService returned no Binder");return b;
        }
    }
    private static ParcelFileDescriptor open(Context c,String path,int tx)throws IOException{
        Parcel d=Parcel.obtain(),r=Parcel.obtain();
        try{
            IBinder b=service(c);d.writeInterfaceToken(DwShizukuIoService.DESCRIPTOR);d.writeString(path);
            if(!b.transact(tx,d,r,0))throw new IOException("Shizuku file I/O transaction rejected");
            r.readException();if(r.readInt()==0)throw new IOException("Shizuku file I/O returned no descriptor");
            return ParcelFileDescriptor.CREATOR.createFromParcel(r);
        }catch(Throwable t){binder=null;if(t instanceof IOException)throw(IOException)t;throw new IOException("Shizuku file I/O open failed: "+t,t);}
        finally{r.recycle();d.recycle();}
    }
    public static InputStream openRead(Context c,String path)throws IOException{return new ParcelFileDescriptor.AutoCloseInputStream(open(c,path,DwShizukuIoService.TX_OPEN_READ));}
    public static OutputStream openWrite(Context c,String path)throws IOException{return new ParcelFileDescriptor.AutoCloseOutputStream(open(c,path,DwShizukuIoService.TX_OPEN_WRITE));}

    private static ph.o failure(Throwable t){
        DwFsTrace.capture(t);IOException e=t instanceof IOException?(IOException)t:new IOException(String.valueOf(t),t);return ph.n.k(e);
    }
    private static void transactVoid(Context c,int tx,String a,String b,int x,int y)throws ph.o{
        Parcel d=Parcel.obtain(),r=Parcel.obtain();
        try{
            IBinder ib=service(c);d.writeInterfaceToken(DwShizukuIoService.DESCRIPTOR);
            if(a!=null)d.writeString(a);if(b!=null)d.writeString(b);
            if(x!=Integer.MIN_VALUE)d.writeInt(x);if(y!=Integer.MIN_VALUE)d.writeInt(y);
            if(!ib.transact(tx,d,r,0))throw new IOException("Shizuku file operation transaction rejected");r.readException();
        }catch(Throwable t){binder=null;throw failure(t);}finally{r.recycle();d.recycle();}
    }
    public static void delete(Context c,String path,boolean recursive)throws ph.o{transactVoid(c,DwShizukuIoService.TX_DELETE,path,null,recursive?1:0,Integer.MIN_VALUE);}
    public static void rename(Context c,String from,String to)throws ph.o{transactVoid(c,DwShizukuIoService.TX_RENAME,from,to,Integer.MIN_VALUE,Integer.MIN_VALUE);}
    public static void mkdir(Context c,String path,int mode)throws ph.o{transactVoid(c,DwShizukuIoService.TX_MKDIR,path,null,mode,Integer.MIN_VALUE);}
    public static void symlink(Context c,String target,String link)throws ph.o{transactVoid(c,DwShizukuIoService.TX_SYMLINK,target,link,Integer.MIN_VALUE,Integer.MIN_VALUE);}
    public static boolean chmod(Context c,String path,int mode)throws ph.o{transactVoid(c,DwShizukuIoService.TX_CHMOD,path,null,mode,Integer.MIN_VALUE);return true;}
    public static boolean chown(Context c,String path,int uid,int gid)throws ph.o{transactVoid(c,DwShizukuIoService.TX_CHOWN,path,null,uid,gid);return true;}

    public static String selfTest(Context c){
        String p="/data/local/tmp/dw-filemanager-io-selftest.txt",q=p+".renamed";
        try{
            OutputStream out=openWrite(c,p);out.write("DW_IO_OK".getBytes("UTF-8"));out.close();
            InputStream in=openRead(c,p);byte[] b=new byte[32];int n=in.read(b);in.close();String s=n>0?new String(b,0,n,"UTF-8"):"";
            rename(c,p,q);chmod(c,q,0600);delete(c,q,false);
            return "Shizuku file I/O: PASS uid="+uid(c)+" read="+s;
        }catch(Throwable t){return "Shizuku file I/O: FAIL :: "+t.getClass().getSimpleName()+": "+String.valueOf(t.getMessage());}
    }
    private static int uid(Context c)throws IOException{
        Parcel d=Parcel.obtain(),r=Parcel.obtain();try{IBinder b=service(c);d.writeInterfaceToken(DwShizukuIoService.DESCRIPTOR);b.transact(DwShizukuIoService.TX_UID,d,r,0);r.readException();return r.readInt();}finally{r.recycle();d.recycle();}
    }
}
'''

    with tempfile.TemporaryDirectory(prefix='dw-shizuku-io-') as td:
        w=Path(td); src=w/'src'; classes=w/'classes'; sc=w/'stubclasses'; classes.mkdir(); sc.mkdir()
        for rel,txt in stubs.items():
            p=src/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(txt)
        pkg=src/NS; pkg.mkdir(parents=True,exist_ok=True)
        (pkg/'DwShizukuIoService.java').write_text(service); (pkg/'DwShizukuIoClient.java').write_text(client)
        run('javac','-source','8','-target','8','-cp',android,'-d',sc,*[src/x for x in stubs])
        run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(sc),'-d',classes,pkg/'DwShizukuIoService.java',pkg/'DwShizukuIoClient.java')
        dex=w/'dex'; dex.mkdir(); run(bt/'d8','--min-api','26','--lib',android,'--classpath',sc,'--output',dex,*classes.rglob('*.class'))
        manifest=w/'AndroidManifest.xml'; manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dw.filemanager.shizukuioprep"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/><application/></manifest>')
        prep=w/'prep.apk'; run(bt/'aapt2','link','-o',prep,'--manifest',manifest,'-I',android)
        with zipfile.ZipFile(prep,'a',compression=zipfile.ZIP_DEFLATED) as z:z.write(dex/'classes.dex','classes.dex')
        dec=w/'decoded'; run('java','-jar',apktool,'d','-f',prep,'-o',dec)
        gen=dec/'smali'/NS; dest=sm/NS; dest.mkdir(parents=True,exist_ok=True)
        for stem in ('DwShizukuIoService','DwShizukuIoClient'):
            fs=list(gen.glob(stem+'*.smali'))
            if not fs:raise RuntimeError('compiled '+stem+' smali missing')
            for old in dest.glob(stem+'*.smali'):old.unlink()
            for p in fs:shutil.copy2(p,dest/p.name)

    hp=sm/'hc/h.smali'; ht=hp.read_text()
    ht=prepend(ht,'.method public final f(Landroid/content/Context;)Ljava/io/InputStream;',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_open_read
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    invoke-static {p1, v0}, Ldw/filemanager/shizuku/DwShizukuIoClient;->openRead(Landroid/content/Context;Ljava/lang/String;)Ljava/io/InputStream;
    move-result-object v0
    return-object v0
    :dw_legacy_open_read''','hc/h.f')
    ht=prepend(ht,'.method public final C0(Landroid/content/Context;J)Ljava/io/OutputStream;',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_open_write
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    invoke-static {p1, v0}, Ldw/filemanager/shizuku/DwShizukuIoClient;->openWrite(Landroid/content/Context;Ljava/lang/String;)Ljava/io/OutputStream;
    move-result-object v0
    return-object v0
    :dw_legacy_open_write''','hc/h.C0')
    ht=prepend(ht,'.method public final H(Landroid/content/Context;Z)V',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_delete_file
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    :try_start_dw_delete_file
    const/4 v1, 0x0
    invoke-static {p1, v0, v1}, Ldw/filemanager/shizuku/DwShizukuIoClient;->delete(Landroid/content/Context;Ljava/lang/String;Z)V
    :try_end_dw_delete_file
    .catch Lph/o; {:try_start_dw_delete_file .. :try_end_dw_delete_file} :dw_delete_file_error
    return-void
    :dw_delete_file_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_delete_file''','hc/h.H')
    hp.write_text(ht)

    ep=sm/'hc/e.smali'; et=ep.read_text()
    et=prepend(et,'.method public final H(Landroid/content/Context;Z)V',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_rmdir
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    :try_start_dw_rmdir
    const/4 v1, 0x0
    invoke-static {p1, v0, v1}, Ldw/filemanager/shizuku/DwShizukuIoClient;->delete(Landroid/content/Context;Ljava/lang/String;Z)V
    :try_end_dw_rmdir
    .catch Lph/o; {:try_start_dw_rmdir .. :try_end_dw_rmdir} :dw_rmdir_error
    return-void
    :dw_rmdir_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_rmdir''','hc/e.H')
    et=prepend(et,'.method public final Y(Landroid/content/Context;Z)V',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_recursive_delete
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    :try_start_dw_recursive_delete
    const/4 v1, 0x1
    invoke-static {p1, v0, v1}, Ldw/filemanager/shizuku/DwShizukuIoClient;->delete(Landroid/content/Context;Ljava/lang/String;Z)V
    :try_end_dw_recursive_delete
    .catch Lph/o; {:try_start_dw_recursive_delete .. :try_end_dw_recursive_delete} :dw_recursive_delete_error
    return-void
    :dw_recursive_delete_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_recursive_delete''','hc/e.Y')
    et=prepend(et,'.method public final w0(Landroid/content/Context;Ljava/lang/CharSequence;Z)Lkh/d;',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_mkdir
    new-instance v0, Lhh/f;
    iget-object v1, p0, Lhc/i;->i:Lhh/f;
    invoke-interface {p2}, Ljava/lang/CharSequence;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-direct {v0, v1, v2}, Lhh/f;-><init>(Lhh/f;Ljava/lang/String;)V
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v2
    :try_start_dw_mkdir
    const/16 v3, 0x1ed
    invoke-static {p1, v2, v3}, Ldw/filemanager/shizuku/DwShizukuIoClient;->mkdir(Landroid/content/Context;Ljava/lang/String;I)V
    invoke-static {p1, v2}, Lhc/i;->U(Landroid/content/Context;Ljava/lang/String;)Lph/e;
    move-result-object v2
    new-instance v3, Lhc/e;
    invoke-direct {v3, v0, v2}, Lhc/i;-><init>(Lhh/f;Lph/e;)V
    :try_end_dw_mkdir
    .catch Lph/o; {:try_start_dw_mkdir .. :try_end_dw_mkdir} :dw_mkdir_error
    return-object v3
    :dw_mkdir_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_mkdir''','hc/e.w0')
    et=prepend(et,'.method public final l0(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;)Lhc/i;',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_symlink
    new-instance v0, Lhh/f;
    iget-object v1, p0, Lhc/i;->i:Lhh/f;
    invoke-static {p3}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;
    move-result-object v2
    invoke-direct {v0, v1, v2}, Lhh/f;-><init>(Lhh/f;Ljava/lang/String;)V
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v1
    :try_start_dw_symlink
    invoke-static {p1, p2, v1}, Ldw/filemanager/shizuku/DwShizukuIoClient;->symlink(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;)V
    invoke-static {p1, v1}, Lhc/i;->U(Landroid/content/Context;Ljava/lang/String;)Lph/e;
    move-result-object v1
    iget-boolean v2, v1, Lph/e;->i:Z
    if-eqz v2, :dw_symlink_file
    new-instance v2, Lhc/e;
    invoke-direct {v2, v0, v1}, Lhc/e;-><init>(Lhh/f;Lph/e;)V
    return-object v2
    :dw_symlink_file
    new-instance v2, Lhc/h;
    invoke-direct {v2, v0, v1}, Lhc/i;-><init>(Lhh/f;Lph/e;)V
    :try_end_dw_symlink
    .catch Lph/o; {:try_start_dw_symlink .. :try_end_dw_symlink} :dw_symlink_error
    return-object v2
    :dw_symlink_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_symlink''','hc/e.l0')
    ep.write_text(et)

    ip=sm/'hc/i.smali'; it=ip.read_text()
    it=prepend(it,'.method public final a0(Landroid/content/Context;Lhh/f;)Z',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_rename
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    invoke-static {p2}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v1
    :try_start_dw_rename
    invoke-static {p1, v0, v1}, Ldw/filemanager/shizuku/DwShizukuIoClient;->rename(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;)V
    :try_end_dw_rename
    .catch Lph/o; {:try_start_dw_rename .. :try_end_dw_rename} :dw_rename_error
    const/4 v0, 0x1
    return v0
    :dw_rename_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_rename''','hc/i.a0')
    it=prepend(it,'.method public final O0(Landroid/content/Context;I)Z',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_chmod
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    :try_start_dw_chmod
    invoke-static {p1, v0, p2}, Ldw/filemanager/shizuku/DwShizukuIoClient;->chmod(Landroid/content/Context;Ljava/lang/String;I)Z
    move-result v0
    :try_end_dw_chmod
    .catch Lph/o; {:try_start_dw_chmod .. :try_end_dw_chmod} :dw_chmod_error
    return v0
    :dw_chmod_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_chmod''','hc/i.O0')
    it=prepend(it,'.method public final m0(Landroid/content/Context;Ldb/f;)Z',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_chown
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    iget v1, p2, Ldb/f;->i:I
    :try_start_dw_chown
    const/4 v2, -0x1
    invoke-static {p1, v0, v1, v2}, Ldw/filemanager/shizuku/DwShizukuIoClient;->chown(Landroid/content/Context;Ljava/lang/String;II)Z
    move-result v0
    :try_end_dw_chown
    .catch Lph/o; {:try_start_dw_chown .. :try_end_dw_chown} :dw_chown_error
    return v0
    :dw_chown_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_chown''','hc/i.m0')
    it=prepend(it,'.method public final p(Landroid/content/Context;Ldb/f;)Z',r'''    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_chgrp
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    iget v1, p2, Ldb/f;->i:I
    :try_start_dw_chgrp
    const/4 v2, -0x1
    invoke-static {p1, v0, v2, v1}, Ldw/filemanager/shizuku/DwShizukuIoClient;->chown(Landroid/content/Context;Ljava/lang/String;II)Z
    move-result v0
    :try_end_dw_chgrp
    .catch Lph/o; {:try_start_dw_chgrp .. :try_end_dw_chgrp} :dw_chgrp_error
    return v0
    :dw_chgrp_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_chgrp''','hc/i.p')
    s,e,m=method(it,'.method public final f0(Landroid/content/Context;)V')
    old='''    .locals 1\n\n    .line 1\n    const/4 v0, 0x0\n\n    .line 2\n    invoke-static {p1, v0}, Lph/r;->z(Landroid/content/Context;I)V'''
    new='''    .locals 1\n\n    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z\n    move-result v0\n    if-nez v0, :dw_shizuku_access_ok\n    const/4 v0, 0x0\n    invoke-static {p1, v0}, Lph/r;->z(Landroid/content/Context;I)V\n    :dw_shizuku_access_ok'''
    if m.count(old)!=1: raise RuntimeError('hc/i.f0 anchor count '+str(m.count(old)))
    m=m.replace(old,new,1); it=it[:s]+m+it[e:]
    ip.write_text(it)

    dp=sm/NS/'ShizukuDiagnosticActivity.smali'; dt=dp.read_text(); sig='.method private perform()Ljava/lang/String;'; s,e,m=method(dt,sig)
    needle='''    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;\n    move-result-object v0\n    return-object v0'''
    if m.count(needle)==1:
        repl='''    const-string v0, "\\n"\n    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-static {p0}, Ldw/filemanager/shizuku/DwShizukuIoClient;->selfTest(Landroid/content/Context;)Ljava/lang/String;\n    move-result-object v0\n    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    const-string v0, "\\n"\n    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;\n    move-result-object v0\n    return-object v0'''
        m=m.replace(needle,repl,1); dt=dt[:s]+m+dt[e:]; dp.write_text(dt)
    else:
        print('warning: ShizukuDiagnosticActivity perform wrapper shape changed; I/O self-test UI not appended')

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    checks={
      'hc/h.smali':['DwShizukuIoClient;->openRead','DwShizukuIoClient;->openWrite','dw_legacy_delete_file'],
      'hc/e.smali':['dw_legacy_rmdir','dw_legacy_recursive_delete','dw_legacy_mkdir','dw_legacy_symlink'],
      'hc/i.smali':['dw_legacy_rename','dw_legacy_chmod','dw_legacy_chown','dw_legacy_chgrp','dw_shizuku_access_ok'],
    }
    for rel,toks in checks.items():
        txt=(sm/rel).read_text()
        for tok in toks:
            if tok not in txt: raise RuntimeError(rel+' missing '+tok)
    for rel in ('DwShizukuIoService.smali','DwShizukuIoClient.smali'):
        if not (sm/NS/rel).exists(): raise RuntimeError('missing '+rel)
    print('stage21o: Shizuku shell file I/O + editor/viewer/copy/delete/rename/mkdir/symlink/permission operations installed; vc='+VC)

if __name__=='__main__': main()
