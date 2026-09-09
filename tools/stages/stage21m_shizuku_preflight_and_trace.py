#!/usr/bin/env python3
"""Complete the read-only Explorer preflight; retain actionable local errors."""
from pathlib import Path
import argparse, ast, os, re, shutil, subprocess, tempfile, zipfile
VC='9109036'
NS='dw/filemanager/shizuku/'

def one(text,old,new,label):
    if text.count(old)!=1:raise RuntimeError(f'{label}: expected one anchor, found {text.count(old)}')
    return text.replace(old,new,1)

def method(text,sig):
    s=text.index(sig);e=text.index('\n.end method',s)+len('\n.end method')
    return s,e,text[s:e]

def newest(path):
    return max((p for p in path.iterdir() if p.is_dir()),key=lambda p:tuple(map(int,re.findall(r'\d+',p.name))))

def run(*args):subprocess.run([str(x) for x in args],check=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('decoded',type=Path);a=ap.parse_args()
    root=a.decoded;sm=root/'smali';repo=Path.cwd()
    tree=ast.parse((repo/'tools/stages/stage21l_shizuku_userservice_filesystem.py').read_text())
    source={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ('service_java','client_java','stubs'):source[name]=ast.literal_eval(node.value)
    if set(source)!={'service_java','client_java','stubs'}:raise RuntimeError('Stage21l Java sources not found')
    service=source['service_java'];client=source['client_java'];stubs=source['stubs']
    # New protocol version prevents reuse of the v1 service without REALPATH.
    client=one(client,'.tag("dw-filemanager-fs-v1").version(1)', '.tag("dw-filemanager-fs-v2").version(2)','protocol version')
    service=one(service,'    public DwShizukuFsService(){ super(); }','''    public static final int TX_REALPATH=IBinder.FIRST_CALL_TRANSACTION+3;
    public DwShizukuFsService(){ super(); }''','REALPATH transaction')
    service=one(service,'            if(code==TX_UID){','''            if(code==TX_REALPATH){
                String path=data.readString();
                if(path==null || !path.startsWith("/") || path.indexOf(0)>=0)
                    throw new IllegalArgumentException("Expected an absolute filesystem path");
                String canonical=Os.realpath(path);
                reply.writeNoException(); reply.writeString(canonical); return true;
            }
            if(code==TX_UID){''','service realpath')
    service=one(service,'        if(code==INTERFACE_TRANSACTION){','''        if(code==16777115){ System.exit(0); return true; }
        if(code==INTERFACE_TRANSACTION){''','UserService destroy')
    client=one(client,'    private static String decode(String s){','''    public static String realpath(Context c,String path) throws ph.o {
        Parcel d=Parcel.obtain(), r=Parcel.obtain();
        try {
            IBinder b=service(c);
            d.writeInterfaceToken(DwShizukuFsService.DESCRIPTOR); d.writeString(path);
            if(!b.transact(DwShizukuFsService.TX_REALPATH,d,r,0))
                throw new IOException("Shizuku filesystem REALPATH transaction rejected");
            r.readException(); String resolved=r.readString();
            if(resolved==null || !resolved.startsWith("/"))
                throw new IOException("Invalid Shizuku filesystem REALPATH response");
            return resolved;
        } catch(Throwable t){ throw failure(t); }
        finally { r.recycle(); d.recycle(); }
    }

    private static String decode(String s){''','client realpath')
    client=one(client,'    private static ph.o failure(Throwable t){','''    private static ph.o failure(Throwable t){
        DwFsTrace.capture(t);''','retain backend error')
    trace=r'''package dw.filemanager.shizuku;
import android.content.Context;
import android.os.Looper;
import android.util.Log;
import java.io.*;
import java.nio.charset.StandardCharsets;
/** Bounded, app-private error capture. No networking or periodic collection. */
public final class DwFsTrace {
 private static volatile Context context;
 private static volatile String last;
 private static final int LIMIT=32768;
 private DwFsTrace(){}
 public static void init(Context c){if(c!=null)context=c.getApplicationContext();}
 private static boolean relevant(Throwable t){
  for(int i=0;t!=null && i<8;i++,t=t.getCause())
   for(StackTraceElement e:t.getStackTrace()){
    String n=e.getClassName();
    if(n.startsWith("hc.")||n.startsWith("lf.")||n.startsWith("ph.")||n.startsWith("dw.filemanager.shizuku."))return true;
   }
  return false;
 }
 public static void capture(Throwable t){
  try{
   if(t==null || !relevant(t))return;
   String s="Time: "+new java.util.Date()+"\nThread: "+Thread.currentThread().getName()+"\n"+Log.getStackTraceString(t);
   if(s.length()>LIMIT)s=s.substring(0,LIMIT)+"\n[truncated]";
   last=s; Context c=context;
   if(c!=null && Looper.myLooper()!=Looper.getMainLooper()){
    synchronized(DwFsTrace.class){
     try(FileOutputStream o=c.openFileOutput("dw-filesystem-last-error.txt",Context.MODE_PRIVATE)){
      o.write(s.getBytes(StandardCharsets.UTF_8));
     }
    }
   }
  }catch(Throwable ignored){}
 }
 public static String snapshot(Context c){
  init(c);String s=last;if(s!=null)return s;
  try(InputStream in=c.openFileInput("dw-filesystem-last-error.txt")){
   ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[2048];
   for(int n;(n=in.read(buf))>0 && out.size()<LIMIT;)out.write(buf,0,Math.min(n,LIMIT-out.size()));
   return out.toString("UTF-8");
  }catch(Exception e){return "No filesystem exception captured in this installation yet.";}
 }
}
'''
    probe=r'''package dw.filemanager.shizuku;
import android.content.Context;
import android.util.Log;
import java.lang.reflect.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
public final class DwFsPipelineProbe {
 private DwFsPipelineProbe(){}
 private static Object call(Object o,String name,Class<?>[] types,Object... args)throws Exception {
  try{Method m=o.getClass().getMethod(name,types);m.setAccessible(true);return m.invoke(o,args);}
  catch(InvocationTargetException e){Throwable t=e.getCause();if(t instanceof Exception)throw (Exception)t;throw (Error)t;}
 }
 private static Object node(String path)throws Exception{
  Object catalog=Class.forName("dw.filemanager.dirimpl.shell.ShellCatalog").getConstructor().newInstance();
  return call(catalog,"v",new Class[]{String.class},path);
 }
 private static synchronized void append(StringBuilder b,String s){b.append(s).append('\n');}
 public static String perform(final Context context){
  final Context c=context.getApplicationContext();
  String previous=DwFsTrace.snapshot(c);
  final StringBuilder b=new StringBuilder("DW FILESYSTEM END-TO-END TEST\n");
  try{b.append("Installed version: ").append(c.getPackageManager().getPackageInfo(c.getPackageName(),0).versionCode).append('\n');}catch(Exception ignored){}
  b.append("\nLAST CAPTURED EXPLORER/BACKEND EXCEPTION\n").append(previous).append("\n\n");
  b.append(DwShizukuFsClient.selfTest(c)).append('\n');
  final CountDownLatch done=new CountDownLatch(1);
  Runnable job=new Runnable(){public void run(){try{
   for(String path:new String[]{"/","/data/local/tmp"}){
    String step="metadata";
    try{
     Object n=node(path);call(n,"a",new Class[]{Context.class},c);
     append(b,"PASS "+path+" metadata");
     step="realpath preflight";
     Object real=call(n,"T",new Class[]{Context.class},c);
     append(b,"PASS "+path+" realpath="+real);
     step="mount lookup";
     Object table=Class.forName("ph.l").getMethod("f").invoke(null);
     Object mount=call(table,"b",new Class[]{String.class,boolean.class},real,true);
     append(b,"PASS "+path+" mount lookup: "+(mount==null?"no matching mount":"matched"));
     for(int flags:new int[]{1,3,17,19}){
      step="Explorer F0 flags="+flags;
      Object folder=node(path);call(folder,"a",new Class[]{Context.class},c);
      Object[] items=(Object[])call(folder,"F0",new Class[]{Context.class,int.class},c,flags);
      if(items==null)throw new IllegalStateException("Null Explorer item array");
      for(Object item:items){
       call(item,"a",new Class[]{Context.class},c);
       if(call(item,"getName",new Class[]{})==null)throw new IllegalStateException("Null item name");
       call(item,"getType",new Class[]{});call(item,"getLastModified",new Class[]{});
      }
      append(b,"PASS "+path+" Explorer F0 flags="+flags+" entries="+items.length+" metadata/type/name checked");
     }
    }catch(Throwable t){DwFsTrace.capture(t);append(b,"FAIL "+path+" at "+step+"\n"+Log.getStackTraceString(t));}
   }
  }finally{done.countDown();}}};
  try{
   Thread t=(Thread)Class.forName("bb.d").getConstructor(Class.class,String.class,Runnable.class).newInstance(DwFsPipelineProbe.class,"DW filesystem pipeline self-test",job);
   t.start();if(!done.await(60,TimeUnit.SECONDS))append(b,"FAIL: filesystem worker timed out; no passing result claimed.");
  }catch(Throwable t){append(b,"FAIL creating DW filesystem worker\n"+Log.getStackTraceString(t));}
  synchronized(DwFsPipelineProbe.class){return b.toString();}
 }
}
'''
    java={'DwShizukuFsService':service,'DwShizukuFsClient':client,'DwFsTrace':trace,'DwFsPipelineProbe':probe}
    sdk=Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT']);bt=newest(sdk/'build-tools');android=newest(sdk/'platforms')/'android.jar'
    apktool=repo/'apktool.jar'
    if not apktool.exists():apktool=repo/'runtime-input/apktool.jar'
    with tempfile.TemporaryDirectory(prefix='dw-fs-preflight-') as temp:
        w=Path(temp);src=w/'src';classes=w/'classes';sc=w/'stubclasses';classes.mkdir();sc.mkdir()
        for rel,txt in stubs.items():
            p=src/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt)
        for name,txt in java.items():
            p=src/NS/(name+'.java');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt)
        run('javac','-source','8','-target','8','-cp',android,'-d',sc,*[src/x for x in stubs])
        run('javac','-source','8','-target','8','-cp',str(android)+os.pathsep+str(sc),'-d',classes,*[src/NS/(x+'.java') for x in java])
        dex=w/'dex';dex.mkdir()
        run(bt/'d8','--min-api','26','--lib',android,'--classpath',sc,'--output',dex,*classes.rglob('*.class'))
        prep=w/'prep.apk'
        with zipfile.ZipFile(prep,'w') as z:
            z.writestr('AndroidManifest.xml','<manifest package="dw.fs.preflight.prep"/>');z.write(dex/'classes.dex','classes.dex')
        dec=w/'decoded';run('java','-jar',apktool,'d','-f','--no-res',prep,'-o',dec)
        for stem in java:
            for old in (sm/NS).glob(stem+'*.smali'):old.unlink()
        for p in (dec/'smali'/NS).glob('*.smali'):shutil.copy2(p,sm/NS/p.name)
    # The UI calls hc.i.T before F0, including through mount/read-only checks.
    ip=sm/'hc/i.smali';it=ip.read_text();sig='.method public final T(Landroid/content/Context;)Ljava/lang/String;'
    s,e,m=method(it,sig)
    anchor='    :cond_0\n    invoke-static {p1}, Ldw/filemanager/dirimpl/shell/ShellCatalog;->l(Landroid/content/Context;)Lhc/f;'
    replacement='''    :cond_0
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_realpath
    :try_start_dw_realpath
    iget-object v0, p0, Lhc/i;->i:Lhh/f;
    invoke-static {v0}, Lhc/i;->z(Lhh/f;)Ljava/lang/String;
    move-result-object v0
    invoke-static {p1, v0}, Ldw/filemanager/shizuku/DwShizukuFsClient;->realpath(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    iput-object v0, p0, Lhc/i;->Y:Ljava/lang/String;
    :try_end_dw_realpath
    .catch Lph/o; {:try_start_dw_realpath .. :try_end_dw_realpath} :dw_realpath_error
    return-object v0
    :dw_realpath_error
    move-exception v0
    const/4 v1, 0x0
    invoke-static {v1, v0, p0, v1}, Lhc/i;->W(Lhc/f;Lph/o;Lhc/i;Ljava/lang/String;)Lhh/l;
    move-result-object v0
    throw v0
    :dw_legacy_realpath
    invoke-static {p1}, Ldw/filemanager/dirimpl/shell/ShellCatalog;->l(Landroid/content/Context;)Lhc/f;'''
    m=one(m,anchor,replacement,'hc.i.T UserService preflight');ip.write_text(it[:s]+m+it[e:])
    ep=sm/'dw/filemanager/ui/ExplorerActivity.smali';et=ep.read_text()
    s,e,m=method(et,'.method public final onCreate(Landroid/os/Bundle;)V')
    m,n=re.subn(r'(    \.locals \d+\n)',r'\1\n    invoke-static/range {p0 .. p0}, Ldw/filemanager/shizuku/DwFsTrace;->init(Landroid/content/Context;)V\n',m,count=1)
    if n!=1:raise RuntimeError('Explorer context hook not inserted')
    ep.write_text(et[:s]+m+et[e:])
    xp=sm/'hh/l.smali';xt=xp.read_text()
    s,e,m=method(xt,'.method public varargs constructor <init>(Lhh/j;Ljava/lang/Throwable;[Ljava/lang/Object;)V')
    m=one(m,'    return-void','    invoke-static {p0}, Ldw/filemanager/shizuku/DwFsTrace;->capture(Ljava/lang/Throwable;)V\n    return-void','error capture')
    xp.write_text(xt[:s]+m+xt[e:])
    dp=sm/NS/'ShizukuDiagnosticActivity.smali';dt=dp.read_text()
    sig='.method private perform()Ljava/lang/String;';s,e,m=method(dt,sig)
    m=one(m,sig,'.method private performTransport()Ljava/lang/String;','retain basic selftest');dt=dt[:s]+m+dt[e:]
    dt+='''
.method private perform()Ljava/lang/String;
    .locals 3
    invoke-static {p0}, Ldw/filemanager/shizuku/DwFsPipelineProbe;->perform(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0
    invoke-direct {p0}, Ldw/filemanager/shizuku/ShizukuDiagnosticActivity;->performTransport()Ljava/lang/String;
    move-result-object v1
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v0, "\\nTRANSPORT / LEGACY COMPARISON\\n"
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method
'''
    dp.write_text(dt)
    # Preserve mount protections and mutation/root authorization, unchanged.
    assert 'Lph/l;->f()Lab/n;' in (sm/'kh/a0.smali').read_text()
    assert 'Lph/r;->z(Landroid/content/Context;I)V' in method(ip.read_text(),'.method public final f0(Landroid/content/Context;)V')[2]
    expected={'db/f.smali':['<init>(ILjava/lang/String;)V'],'ph/k.smali':['<init>(Ldb/f;Ldb/f;I)V'],'ph/e.smali':['<init>(Ljava/lang/String;Ljava/lang/String;Lph/f;ZLph/k;JJ)V'],'ph/n.smali':['k(Ljava/io/IOException;)Lph/o;'],'bb/d.smali':['<init>(Ljava/lang/Class;Ljava/lang/String;Ljava/lang/Runnable;)V']}
    for rel,ds in expected.items():
        text=(sm/rel).read_text()
        for d in ds:
            if not re.search(r'^\.method[^\n]* '+re.escape(d)+r'$',text,re.M):raise RuntimeError('Real APK descriptor missing: '+rel+' '+d)
    y=root/'apktool.yml';yt,n=re.subn(r'(?m)^(\s*versionCode:\s*)[^\n]+',r'\g<1>'+VC,y.read_text(),count=1)
    if n!=1:raise RuntimeError('versionCode missing')
    y.write_text(yt)
    print('stage21m: Shizuku REALPATH preflight; mount protection retained; DW-worker pipeline selftest + local exception capture; vc='+VC)
if __name__=='__main__':main()
