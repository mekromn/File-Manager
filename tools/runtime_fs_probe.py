#!/usr/bin/env python3
"""Build an emulator-only instrumented copy. Never distribute its test signer."""
from pathlib import Path
import os, subprocess, zipfile, xml.etree.ElementTree as ET

def run(*args): subprocess.run([str(a) for a in args],check=True)
root=Path('runtime-work'); root.mkdir(exist_ok=True)
sdk=Path(os.environ['ANDROID_HOME'])
bt=sorted((sdk/'build-tools').iterdir(),key=lambda p:[int(x) for x in p.name.replace('-','.') .split('.') if x.isdigit()])[-1]
android=sdk/'platforms/android-36/android.jar'
apk=Path('runtime-input/DW-File-Manager-replay-unsigned.apk')
tool=Path('runtime-input/apktool.jar')
run('java','-jar',tool,'d','-f',apk,'-o',root/'decoded')
java=r'''package dw.filemanager.shizuku;
import android.app.Instrumentation;
import android.os.Bundle;
import android.content.Context;
import android.util.Log;
import java.io.*;
import java.lang.reflect.*;
import java.util.concurrent.CountDownLatch;

public final class DwFsProbe extends Instrumentation {
 private final StringBuilder report=new StringBuilder();
 private Context c;
 private synchronized void line(String s){report.append(s).append('\n'); Log.i("DWProbe",s);}
 private Object call(Object o,String n,Class<?>[] types,Object... args)throws Exception {
  try {Method m=o.getClass().getMethod(n,types);m.setAccessible(true);return m.invoke(o,args);}
  catch(InvocationTargetException e){Throwable t=e.getCause();if(t instanceof Exception)throw (Exception)t;throw (Error)t;}
 }
 private Object stat(String name,Class<?>[] types,Object... args)throws Exception{
  int p=name.lastIndexOf('#');Class<?> k=Class.forName(name.substring(0,p));
  try {Method m=k.getDeclaredMethod(name.substring(p+1),types);m.setAccessible(true);return m.invoke(null,args);}
  catch(InvocationTargetException e){Throwable t=e.getCause();if(t instanceof Exception)throw (Exception)t;throw (Error)t;}
 }
 private interface Check { Object run() throws Exception; }
 private void check(String n,Check f){try{Object x=f.run();line("PASS "+n+" :: "+String.valueOf(x));}catch(Throwable t){StringWriter w=new StringWriter();t.printStackTrace(new PrintWriter(w));line("FAIL "+n+" :: "+w);}}
 private Object node(String path)throws Exception{
  Class<?> k=Class.forName("dw.filemanager.dirimpl.shell.ShellCatalog");
  return call(k.getConstructor().newInstance(),"v",new Class[]{String.class},path);
 }
 @Override public void onCreate(Bundle args){super.onCreate(args); start();}
 @Override public void onStart(){
  c=getTargetContext();
  try{
   line("PACKAGE "+c.getPackageName()+" version="+c.getPackageManager().getPackageInfo(c.getPackageName(),0).getLongVersionCode());
   for(String cl:new String[]{"hc.e","hc.i","ph.i","ph.n","dw.filemanager.shizuku.DwShizukuFsClient","dw.filemanager.shizuku.DwShizukuFsService"}){
    final String x=cl;check("load "+cl,()->Class.forName(x));
   }
   for(int i=0;i<60;i++){if(Boolean.TRUE.equals(stat("dw.filemanager.shizuku.ShizukuBridge#hasBinder",new Class[]{})))break;Thread.sleep(200);}
   runOnMainSync(()->{try{stat("dw.filemanager.shizuku.ShizukuBridge#ensurePermission",new Class[]{Context.class},c);}catch(Exception e){line("permission request "+e);}});
   for(int i=0;i<150;i++){if(Boolean.TRUE.equals(stat("dw.filemanager.shizuku.ShizukuBridge#isAuthorized",new Class[]{})))break;Thread.sleep(200);}
   check("authorized",()->stat("dw.filemanager.shizuku.ShizukuBridge#isAuthorized",new Class[]{}));
   check("UserService selftest",()->stat("dw.filemanager.shizuku.DwShizukuFsClient#selfTest",new Class[]{Context.class},c));
   CountDownLatch done=new CountDownLatch(1);
   Runnable job=()->{try{
    for(String path:new String[]{"/","/data/local/tmp"}){
     check(path+" native toybox lister",()->((Object[])stat("dw.filemanager.shizuku.ShizukuDirectoryLister#list",new Class[]{String.class},path)).length);
     check(path+" metadata init",()->{Object n=node(path);call(n,"a",new Class[]{Context.class},c);return call(n,"getName",new Class[]{});});
     check(path+" REALPATH preflight hc.i.T",()->call(node(path),"T",new Class[]{Context.class},c));
     check(path+" mount table",()->stat("ph.l#f",new Class[]{}));
     for(int flag:new int[]{1,3,17,19}){
      final int f=flag;
      check(path+" F0 flags="+flag,()->{
       Object n=node(path);call(n,"a",new Class[]{Context.class},c);
       Object[] entries=(Object[])call(n,"F0",new Class[]{Context.class,int.class},c,f);
       for(Object e:entries){call(e,"a",new Class[]{Context.class},c);call(e,"getName",new Class[]{});call(e,"getType",new Class[]{});call(e,"getLastModified",new Class[]{});}
       return "count="+entries.length;
      });
     }
    }
   }finally{done.countDown();}};
   Thread worker=(Thread)Class.forName("bb.d").getConstructor(Class.class,String.class,Runnable.class).newInstance(DwFsProbe.class,"DW actual filesystem probe",job);
   worker.start();if(!done.await(100,java.util.concurrent.TimeUnit.SECONDS))line("FAIL worker timeout");
  }catch(Throwable t){line("PROBE ERROR "+Log.getStackTraceString(t));}
  finally{
   try{File f=new File(c.getFilesDir(),"runtime-fs-probe.txt");try(FileOutputStream o=new FileOutputStream(f)){o.write(report.toString().getBytes("UTF-8"));}}catch(Exception e){line("WRITE ERROR "+e);}
   Bundle b=new Bundle();b.putString("stream",report.toString());finish(-1,b);
  }
 }
}
'''
src=root/'DwFsProbe.java'; src.write_text(java)
classes=root/'classes'; classes.mkdir(exist_ok=True)
run('javac','-source','8','-target','8','-cp',android,'-d',classes,src)
dex=root/'dex'; dex.mkdir(exist_ok=True)
run(bt/'d8','--min-api','26','--lib',android,'--output',dex,*classes.rglob('*.class'))
A='{http://schemas.android.com/apk/res/android}';ET.register_namespace('android',A[1:-1])
mp=root/'decoded/AndroidManifest.xml'; tree=ET.parse(mp); m=tree.getroot();m.find('application').set(A+'debuggable','true')
ET.SubElement(m,'instrumentation',{A+'name':'dw.filemanager.shizuku.DwFsProbe',A+'targetPackage':'com.mekromn.dwfilemanager'})
tree.write(mp,encoding='utf-8',xml_declaration=True)
prep=root/'probe.apk';
with zipfile.ZipFile(prep,'w') as z:
 z.writestr('AndroidManifest.xml','<manifest package="dw.probe"/>');z.write(dex/'classes.dex','classes.dex')
run('java','-jar',tool,'d','-f','--no-res',prep,'-o',root/'probe-decoded')
import shutil
for p in (root/'probe-decoded/smali').rglob('*.smali'):
 dest=root/'decoded/smali'/p.relative_to(root/'probe-decoded/smali');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
run('java','-jar',tool,'b',root/'decoded','-o',root/'test-unsigned.apk')
run('keytool','-genkeypair','-keystore',root/'emulator-only.jks','-storepass','emulator-test','-keypass','emulator-test','-alias','emulator','-keyalg','RSA','-dname','CN=Emulator only','-validity','2')
run(bt/'zipalign','-f','4',root/'test-unsigned.apk',root/'test.apk')
run(bt/'apksigner','sign','--ks',root/'emulator-only.jks','--ks-pass','pass:emulator-test',root/'test.apk')
