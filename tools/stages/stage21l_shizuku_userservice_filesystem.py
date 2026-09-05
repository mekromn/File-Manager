#!/usr/bin/env python3
from pathlib import Path
import argparse, os, re, shutil, subprocess, tempfile, zipfile

VC='9109035'

def run(*args,cwd=None):
    subprocess.run([str(x) for x in args],cwd=cwd,check=True)

def newest(base):
    ds=[p for p in Path(base).iterdir() if p.is_dir()]
    if not ds: raise RuntimeError('no SDK directories in '+str(base))
    def key(p):
        nums=re.findall(r'\d+',p.name)
        return tuple(int(x) for x in nums) if nums else (0,)
    return sorted(ds,key=key)[-1]

def method(text,sig):
    s=text.find(sig)
    if s<0: raise RuntimeError('missing method '+sig)
    e=text.find('\n.end method',s)
    if e<0: raise RuntimeError('missing method end '+sig)
    e+=len('\n.end method')
    return s,e,text[s:e]

def replace_one(text,old,new,label):
    n=text.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected one match, found {n}')
    return text.replace(old,new,1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; repo=Path.cwd(); sm=root/'smali'
    android_home=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not android_home: raise RuntimeError('ANDROID_HOME/ANDROID_SDK_ROOT required')
    bt=newest(Path(android_home)/'build-tools'); platform=newest(Path(android_home)/'platforms')
    d8=bt/'d8'; aapt2=bt/'aapt2'; android_jar=platform/'android.jar'; apktool=repo/'apktool.jar'
    for p in (d8,aapt2,android_jar,apktool):
        if not p.exists(): raise RuntimeError('required build tool missing: '+str(p))

    # The previous prototypes used Shizuku.newProcess() as a command transport.
    # The device self-test proved that transport works, but DW's legacy root graph
    # kept leaking into catalog acquisition/error handling.  This stage changes
    # the architecture: a dedicated Shizuku UserService is launched as uid=shell
    # and owns filesystem enumeration/stat.  The app process talks to it over a
    # tiny private Binder protocol.  No su, BusyBox, FIFO, shell parser, or root
    # SessionManager is involved in the Shizuku Explorer list/stat path.
    service_java=r'''package dw.filemanager.shizuku;

import android.content.Context;
import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.RemoteException;
import android.system.ErrnoException;
import android.system.Os;
import android.system.OsConstants;
import android.system.StructStat;
import android.util.Base64;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public final class DwShizukuFsService extends Binder {
    public static final String DESCRIPTOR="dw.filemanager.shizuku.IDwFs";
    public static final int TX_LIST=IBinder.FIRST_CALL_TRANSACTION;
    public static final int TX_STAT=IBinder.FIRST_CALL_TRANSACTION+1;
    public static final int TX_UID=IBinder.FIRST_CALL_TRANSACTION+2;

    public DwShizukuFsService(){ super(); }
    public DwShizukuFsService(Context ignored){ this(); }

    private static String b64(String s){
        if(s==null) s="";
        return Base64.encodeToString(s.getBytes(StandardCharsets.UTF_8),Base64.NO_WRAP|Base64.URL_SAFE);
    }

    private static int typeIndex(int mode){
        if(OsConstants.S_ISREG(mode)) return 0;
        if(OsConstants.S_ISDIR(mode)) return 1;
        if(OsConstants.S_ISLNK(mode)) return 2;
        if(OsConstants.S_ISFIFO(mode)) return 3;
        if(OsConstants.S_ISBLK(mode)) return 4;
        if(OsConstants.S_ISCHR(mode)) return 5;
        return 7;
    }

    private static String row(String full,String name) throws ErrnoException {
        StructStat st=Os.lstat(full);
        int type=typeIndex(st.st_mode);
        String target="";
        if(type==2){
            try { target=Os.readlink(full); } catch(Throwable ignored) {}
        }
        long mt=st.st_mtim==null?0L:st.st_mtim.tv_sec*1000L;
        return type+"|"+st.st_uid+"|"+st.st_gid+"|"+(st.st_mode & 07777)+"|"+st.st_size+"|"+mt+"|"+b64(name)+"|"+b64(target);
    }

    private static String[] listInternal(String path) throws IOException {
        if(path==null || path.length()==0) path="/";
        File dir=new File(path);
        String[] names=dir.list();
        if(names==null) throw new IOException("shell uid cannot enumerate "+path);
        ArrayList<String> out=new ArrayList<>(names.length);
        for(String name:names){
            if(name==null || name.length()==0) continue;
            String full="/".equals(path)?"/"+name:new File(dir,name).getPath();
            try { out.add(row(full,name)); }
            catch(ErrnoException ignored) { /* one unusual node must not kill the folder */ }
        }
        return out.toArray(new String[out.size()]);
    }

    private static String statInternal(String path) throws IOException {
        if(path==null || path.length()==0) path="/";
        String name="/".equals(path)?"/":new File(path).getName();
        try { return row(path,name); }
        catch(ErrnoException e){ throw new IOException("shell uid cannot stat "+path+": "+e.getMessage(),e); }
    }

    @Override protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) throws RemoteException {
        if(code==INTERFACE_TRANSACTION){ reply.writeString(DESCRIPTOR); return true; }
        try {
            data.enforceInterface(DESCRIPTOR);
            if(code==TX_LIST){
                String[] rows=listInternal(data.readString());
                reply.writeNoException(); reply.writeStringArray(rows); return true;
            }
            if(code==TX_STAT){
                String row=statInternal(data.readString());
                reply.writeNoException(); reply.writeString(row); return true;
            }
            if(code==TX_UID){
                reply.writeNoException(); reply.writeInt(android.os.Process.myUid()); return true;
            }
        } catch(Throwable t){
            reply.writeException(new IllegalStateException(t.getClass().getSimpleName()+": "+String.valueOf(t.getMessage())));
            return true;
        }
        return super.onTransact(code,data,reply,flags);
    }
}
'''

    client_java=r'''package dw.filemanager.shizuku;

import android.content.ComponentName;
import android.content.Context;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Parcel;
import android.util.Base64;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import rikka.shizuku.Shizuku;

public final class DwShizukuFsClient {
    private static final Object LOCK=new Object();
    private static volatile IBinder binder;
    private static volatile ServiceConnection connection;
    private static volatile Shizuku.UserServiceArgs args;

    private DwShizukuFsClient(){}

    private static Shizuku.UserServiceArgs args(Context c){
        Shizuku.UserServiceArgs a=args;
        if(a!=null) return a;
        synchronized(LOCK){
            if(args==null){
                args=new Shizuku.UserServiceArgs(new ComponentName(c.getApplicationContext(),DwShizukuFsService.class))
                    .daemon(false).tag("dw-filemanager-fs-v1").version(1).processNameSuffix("dwfs");
            }
            return args;
        }
    }

    private static IBinder live(){
        IBinder b=binder;
        if(b!=null && b.pingBinder()) return b;
        binder=null;
        return null;
    }

    private static IBinder service(final Context context) throws IOException {
        IBinder b=live(); if(b!=null) return b;
        if(!Shizuku.pingBinder()) throw new IOException("Shizuku Binder is not connected");
        if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED) throw new IOException("Shizuku permission is not granted");
        if(Looper.myLooper()==Looper.getMainLooper()) throw new IOException("Shizuku UserService initial bind requested on main thread");
        synchronized(LOCK){
            b=live(); if(b!=null) return b;
            final CountDownLatch latch=new CountDownLatch(1);
            final IBinder[] result=new IBinder[1];
            final ServiceConnection conn=new ServiceConnection(){
                @Override public void onServiceConnected(ComponentName name,IBinder service){
                    if(service!=null && service.pingBinder()){ binder=service; result[0]=service; }
                    latch.countDown();
                }
                @Override public void onServiceDisconnected(ComponentName name){ binder=null; }
            };
            connection=conn;
            final Shizuku.UserServiceArgs a=args(context);
            final Throwable[] bindError=new Throwable[1];
            Handler h=new Handler(Looper.getMainLooper());
            h.post(new Runnable(){ @Override public void run(){
                try { Shizuku.bindUserService(a,conn); }
                catch(Throwable t){ bindError[0]=t; latch.countDown(); }
            }});
            try {
                if(!latch.await(6000,TimeUnit.MILLISECONDS)) throw new IOException("Timed out binding Shizuku filesystem UserService");
            } catch(InterruptedException e){ Thread.currentThread().interrupt(); throw new IOException("Interrupted binding Shizuku filesystem UserService",e); }
            if(bindError[0]!=null) throw new IOException("Shizuku UserService bind failed: "+bindError[0],bindError[0]);
            b=result[0]!=null?result[0]:live();
            if(b==null) throw new IOException("Shizuku filesystem UserService returned no Binder");
            return b;
        }
    }

    private static String[] transactList(Context c,String path) throws IOException {
        IBinder b=service(c); Parcel d=Parcel.obtain(); Parcel r=Parcel.obtain();
        try {
            d.writeInterfaceToken(DwShizukuFsService.DESCRIPTOR); d.writeString(path);
            if(!b.transact(DwShizukuFsService.TX_LIST,d,r,0)) throw new IOException("Shizuku filesystem LIST transaction rejected");
            r.readException(); String[] rows=r.createStringArray();
            return rows==null?new String[0]:rows;
        } catch(Throwable t){ binder=null; if(t instanceof IOException) throw (IOException)t; throw new IOException("Shizuku filesystem LIST failed: "+t,t); }
        finally { r.recycle(); d.recycle(); }
    }

    private static String transactStat(Context c,String path) throws IOException {
        IBinder b=service(c); Parcel d=Parcel.obtain(); Parcel r=Parcel.obtain();
        try {
            d.writeInterfaceToken(DwShizukuFsService.DESCRIPTOR); d.writeString(path);
            if(!b.transact(DwShizukuFsService.TX_STAT,d,r,0)) throw new IOException("Shizuku filesystem STAT transaction rejected");
            r.readException(); return r.readString();
        } catch(Throwable t){ binder=null; if(t instanceof IOException) throw (IOException)t; throw new IOException("Shizuku filesystem STAT failed: "+t,t); }
        finally { r.recycle(); d.recycle(); }
    }

    private static String decode(String s){
        if(s==null || s.length()==0) return "";
        return new String(Base64.decode(s,Base64.NO_WRAP|Base64.URL_SAFE),StandardCharsets.UTF_8);
    }
    private static int integer(String s,int d){ try{return Integer.parseInt(s);}catch(Throwable t){return d;} }
    private static long lng(String s,long d){ try{return Long.parseLong(s);}catch(Throwable t){return d;} }

    private static ph.e parse(String row){
        if(row==null) return null;
        String[] a=row.split("\\|",8); if(a.length<8) return null;
        int ti=integer(a[0],7), uid=integer(a[1],-1), gid=integer(a[2],-1), mode=integer(a[3],0);
        long size=lng(a[4],0), mtime=lng(a[5],0);
        String name=decode(a[6]), target=decode(a[7]);
        ph.f[] types=ph.f.values(); ph.f type=(ti>=0 && ti<types.length)?types[ti]:ph.f.Z;
        boolean dir=ti==1;
        db.f owner=new db.f(uid,uid<0?null:String.valueOf(uid));
        db.f group=new db.f(gid,gid<0?null:String.valueOf(gid));
        ph.k perms=new ph.k(owner,group,mode);
        return new ph.e(name,target.length()==0?null:target,type,dir,perms,size,mtime);
    }

    private static ph.o failure(Throwable t){
        IOException e=t instanceof IOException?(IOException)t:new IOException(String.valueOf(t),t);
        return ph.n.k(e);
    }

    public static ph.e[] list(Context c,String path) throws ph.o {
        try {
            String[] rows=transactList(c,path); ArrayList<ph.e> out=new ArrayList<>(rows.length);
            for(String row:rows){ ph.e e=parse(row); if(e!=null) out.add(e); }
            return out.toArray(new ph.e[out.size()]);
        } catch(Throwable t){ throw failure(t); }
    }

    public static ph.e stat(Context c,String path) throws ph.o {
        try { ph.e e=parse(transactStat(c,path)); if(e==null) throw new IOException("Invalid Shizuku filesystem STAT response"); return e; }
        catch(Throwable t){ throw failure(t); }
    }

    public static String selfTest(Context c){
        try {
            IBinder b=service(c); Parcel d=Parcel.obtain(); Parcel r=Parcel.obtain(); int uid=-1;
            try { d.writeInterfaceToken(DwShizukuFsService.DESCRIPTOR); b.transact(DwShizukuFsService.TX_UID,d,r,0); r.readException(); uid=r.readInt(); }
            finally { r.recycle(); d.recycle(); }
            String[] root=transactList(c,"/"); String[] tmp=transactList(c,"/data/local/tmp");
            return "Shizuku UserService filesystem: uid="+uid+" rootCount="+root.length+" tmpCount="+tmp.length;
        } catch(Throwable t){ return "Shizuku UserService filesystem: FAIL :: "+t.getClass().getSimpleName()+": "+String.valueOf(t.getMessage()); }
    }
}
'''

    stubs={
      'rikka/shizuku/Shizuku.java':r'''package rikka.shizuku; import android.content.ComponentName; import android.content.ServiceConnection; public final class Shizuku { public static boolean pingBinder(){return false;} public static int checkSelfPermission(){return -1;} public static void bindUserService(UserServiceArgs a,ServiceConnection c){} public static void unbindUserService(UserServiceArgs a,ServiceConnection c,boolean r){} public static final class UserServiceArgs { public UserServiceArgs(ComponentName c){} public UserServiceArgs daemon(boolean b){return this;} public UserServiceArgs tag(String s){return this;} public UserServiceArgs version(int i){return this;} public UserServiceArgs processNameSuffix(String s){return this;} } }''',
      'db/f.java':r'''package db; public final class f { public f(int i,String s){} }''',
      'ph/f.java':r'''package ph; public final class f { public static f Z; public static f[] values(){return null;} }''',
      'ph/k.java':r'''package ph; public final class k { public k(db.f a,db.f b,int m){} }''',
      'ph/e.java':r'''package ph; public final class e { public e(String n,String l,ph.f t,boolean d,ph.k m,long s,long mt){} }''',
      'ph/o.java':r'''package ph; public final class o extends Exception { public o(){} }''',
      'ph/n.java':r'''package ph; public final class n { public static ph.o k(java.io.IOException e){return null;} }''',
    }

    temp=tempfile.TemporaryDirectory(prefix='dw-shizuku-userservice-'); w=Path(temp.name)
    try:
        src=w/'src'; pkg=src/'dw/filemanager/shizuku'; pkg.mkdir(parents=True)
        (pkg/'DwShizukuFsService.java').write_text(service_java)
        (pkg/'DwShizukuFsClient.java').write_text(client_java)
        for rel,txt in stubs.items():
            p=src/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(txt)
        stubclasses=w/'stubclasses'; classes=w/'classes'; stubclasses.mkdir(); classes.mkdir()
        stubfiles=[str(src/x) for x in stubs]
        run('javac','-source','8','-target','8','-cp',android_jar,'-d',stubclasses,*stubfiles)
        cp=str(android_jar)+os.pathsep+str(stubclasses)
        run('javac','-source','8','-target','8','-cp',cp,'-d',classes,pkg/'DwShizukuFsService.java',pkg/'DwShizukuFsClient.java')
        dexout=w/'dexout'; dexout.mkdir(); classfiles=[str(p) for p in classes.rglob('*.class')]
        run(d8,'--lib',android_jar,'--classpath',stubclasses,'--output',dexout,*classfiles)
        manifest=w/'AndroidManifest.xml'; manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dw.filemanager.shizukuuserserviceprep"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/><application android:theme="@android:style/Theme.Material.NoActionBar"/></manifest>''')
        prep=w/'userservice-prep.apk'; run(aapt2,'link','-o',prep,'--manifest',manifest,'-I',android_jar)
        with zipfile.ZipFile(prep,'a',compression=zipfile.ZIP_DEFLATED) as z: z.write(dexout/'classes.dex','classes.dex')
        dec=w/'decoded'; run('java','-jar',apktool,'d','-f',prep,'-o',dec)
        generated=dec/'smali/dw/filemanager/shizuku'; dest=sm/'dw/filemanager/shizuku'; dest.mkdir(parents=True,exist_ok=True)
        for stem in ('DwShizukuFsService','DwShizukuFsClient'):
            files=list(generated.glob(stem+'*.smali'))
            if not files: raise RuntimeError('compiled '+stem+' smali missing')
            for p in files: shutil.copy2(p,dest/p.name)
    finally:
        temp.cleanup()

    # Fix a semantic bug from the initial bridge: absence of a Binder is NOT
    # success. This method is only a permission/request helper; it must never tell
    # callers that Shizuku is usable when pingBinder() failed.
    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'; bt=bp.read_text()
    sig='.method public static ensurePermission(Landroid/content/Context;)Z'
    s,e,m=method(bt,sig)
    m=m.replace('''    if-nez v0, :cond_0\n\n    const/4 v0, 0x1\n\n    return v0''','''    if-nez v0, :cond_0\n\n    const/4 v0, 0x0\n\n    return v0''',1)
    # The catch fallback was also incorrectly "true".
    tail='''    :catch_0\n    const/4 v0, 0x1\n\n    return v0'''
    if tail in m: m=m.replace(tail,'''    :catch_0\n    const/4 v0, 0x0\n\n    return v0''',1)
    bt=bt[:s]+m+bt[e:]; bp.write_text(bt)

    # Explorer's concrete System loader now calls the UserService backend. The
    # existing ShizukuDirectoryLister one-shot process implementation remains in
    # the APK only as a diagnostic/compatibility fallback, not the primary path.
    ep=sm/'hc/e.smali'; et=ep.read_text(); sig='.method public final F0(Landroid/content/Context;I)[Lkh/j;'; s,e,m=method(et,sig)
    old='''    invoke-static {v12}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;'''
    new='''    invoke-static {v0, v12}, Ldw/filemanager/shizuku/DwShizukuFsClient;->list(Landroid/content/Context;Ljava/lang/String;)[Lph/e;'''
    if m.count(old)!=1: raise RuntimeError('Explorer Shizuku list hook count '+str(m.count(old)))
    m=m.replace(old,new,1); et=et[:s]+m+et[e:]; ep.write_text(et)

    ip=sm/'hc/i.smali'; it=ip.read_text()
    sig='.method public final a(Landroid/content/Context;)V'; s,e,m=method(it,sig)
    old='''    invoke-static {v1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->stat(Ljava/lang/String;)Lph/e;'''
    new='''    invoke-static {p1, v1}, Ldw/filemanager/shizuku/DwShizukuFsClient;->stat(Landroid/content/Context;Ljava/lang/String;)Lph/e;'''
    if m.count(old)!=1: raise RuntimeError('item Shizuku stat hook count '+str(m.count(old)))
    m=m.replace(old,new,1); it=it[:s]+m+it[e:]

    sig='.method public static U(Landroid/content/Context;Ljava/lang/String;)Lph/e;'; s,e,m=method(it,sig)
    old='''    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->stat(Ljava/lang/String;)Lph/e;'''
    new='''    invoke-static {p0, p1}, Ldw/filemanager/shizuku/DwShizukuFsClient;->stat(Landroid/content/Context;Ljava/lang/String;)Lph/e;'''
    if m.count(old)!=1: raise RuntimeError('direct Shizuku stat hook count '+str(m.count(old)))
    m=m.replace(old,new,1); it=it[:s]+m+it[e:]; ip.write_text(it)

    # Extend the built-in self-test with the *same UserService* backend Explorer
    # now uses. This makes the next device report decisive even if a later UI
    # layer is the remaining problem.
    dp=sm/'dw/filemanager/shizuku/ShizukuDiagnosticActivity.smali'; dt=dp.read_text(); sig='.method private perform()Ljava/lang/String;'; s,e,m=method(dt,sig)
    marker='''    const-string v1, "\\nRESULT: Review each line above. Any START_FAILED / nonzero rc identifies the exact failing Shizuku layer.\\n"\n'''
    probe='''    invoke-static {p0}, Ldw/filemanager/shizuku/DwShizukuFsClient;->selfTest(Landroid/content/Context;)Ljava/lang/String;\n    move-result-object v1\n    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    const/16 v1, 0xa\n    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;\n\n    const-string v1, "\\nRESULT: Review each line above. Any START_FAILED / nonzero rc identifies the exact failing Shizuku layer.\\n"\n'''
    if m.count(marker)!=1: raise RuntimeError('self-test RESULT marker count '+str(m.count(marker)))
    m=m.replace(marker,probe,1); dt=dt[:s]+m+dt[e:]; dp.write_text(dt)

    pref=root/'res/xml/pref_root.xml'; pt=pref.read_text()
    pt=pt.replace('Shizuku-native filesystem (Android toybox, no BusyBox/su); real root/su fallback',
                  'Shizuku UserService filesystem (shell UID, no BusyBox/su); real root/su fallback')
    pref.write_text(pt)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode missing')
    y.write_text(yt)

    # Build-time invariants: Explorer must reach the UserService before any legacy
    # ShellCatalog path, and the service/client classes must be physically present.
    fm=method(ep.read_text(),'.method public final F0(Landroid/content/Context;I)[Lkh/j;')[2]
    direct='DwShizukuFsClient;->list(Landroid/content/Context;Ljava/lang/String;)[Lph/e;'; legacy='ShellCatalog;->l(Landroid/content/Context;)Lhc/f;'
    if direct not in fm or legacy not in fm: raise RuntimeError('Explorer UserService/legacy structure incomplete')
    if fm.index(direct)>fm.index(legacy): raise RuntimeError('UserService directory listing is still behind ShellCatalog')
    for rel in ('DwShizukuFsService.smali','DwShizukuFsClient.smali'):
        if not (sm/'dw/filemanager/shizuku'/rel).exists(): raise RuntimeError('missing '+rel)
    bridge=bp.read_text(); es=method(bridge,'.method public static ensurePermission(Landroid/content/Context;)Z')[2]
    if 'if-nez v0' not in es: raise RuntimeError('ensurePermission binder check missing')
    print('stage21l: first-class Shizuku UserService filesystem backend installed; Explorer list/stat bypass root/su/BusyBox; vc='+VC)

if __name__=='__main__': main()
