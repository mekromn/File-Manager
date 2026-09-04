#!/usr/bin/env python3
from pathlib import Path
import argparse, os, re, shutil, subprocess, tempfile, zipfile

VC='9109031'

def run(*args,cwd=None):
    subprocess.run([str(x) for x in args],cwd=cwd,check=True)

def newest(base):
    ds=[p for p in Path(base).iterdir() if p.is_dir()]
    if not ds: raise RuntimeError('no SDK directories in '+str(base))
    def key(p):
        nums=re.findall(r'\d+',p.name)
        return tuple(int(x) for x in nums) if nums else (0,)
    return sorted(ds,key=key)[-1]

def replace_method(text, signature, body):
    start=text.find(signature)
    if start < 0: raise RuntimeError('method not found: '+signature)
    end=text.find('\n.end method',start)
    if end < 0: raise RuntimeError('method end missing: '+signature)
    end += len('\n.end method')
    return text[:start]+body+text[end:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; repo=Path.cwd(); sm=root/'smali'
    android_home=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not android_home: raise RuntimeError('ANDROID_HOME/ANDROID_SDK_ROOT required')
    bt=newest(Path(android_home)/'build-tools'); platform=newest(Path(android_home)/'platforms')
    d8=bt/'d8'; aapt2=bt/'aapt2'; android_jar=platform/'android.jar'; apktool=repo/'apktool.jar'
    for p in (d8,aapt2,android_jar,apktool):
        if not p.exists(): raise RuntimeError('required build tool missing: '+str(p))

    # This is the actual Shizuku-aware directory engine.  Do not route uid=shell
    # through DW's historical root/su BusyBox parser.  Shizuku can enumerate and
    # stat files directly with Android toybox, so produce DW's native ph/e metadata
    # objects from structured stat output.  Real root/su continues using the old
    # implementation unchanged.
    java=r'''package dw.filemanager.shizuku;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public final class ShizukuDirectoryLister {
    private ShizukuDirectoryLister() {}

    private static final class Result {
        final int rc; final String text;
        Result(int r,String t){rc=r;text=t;}
    }

    private static String q(String s){ return "'"+s.replace("'", "'\"'\"'")+"'"; }

    private static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        byte[] b=new byte[16384];
        for(int n;(n=in.read(b))>=0;) out.write(b,0,n);
        return out.toByteArray();
    }

    private static Result run(String command) throws IOException {
        Process p=ShizukuBridge.startCommand(command+" 2>&1");
        if(p==null) throw new IOException("Shizuku command process could not be started");
        try {
            String out=new String(readAll(p.getInputStream()),StandardCharsets.UTF_8);
            int rc;
            try { rc=p.waitFor(); }
            catch(InterruptedException e){ Thread.currentThread().interrupt(); throw new IOException("Interrupted waiting for Shizuku",e); }
            return new Result(rc,out);
        } finally { p.destroy(); }
    }

    private static int num(String s,int fallback){ try{return Integer.parseInt(s);}catch(Throwable t){return fallback;} }
    private static long lng(String s,long fallback){ try{return Long.parseLong(s);}catch(Throwable t){return fallback;} }

    private static int modeFromPermissions(String p){
        if(p==null || p.length()<10) return 0;
        int m=0;
        if(p.charAt(1)=='r')m|=0400; if(p.charAt(2)=='w')m|=0200;
        char c=p.charAt(3); if(c=='x'||c=='s')m|=0100; if(c=='s'||c=='S')m|=04000;
        if(p.charAt(4)=='r')m|=0040; if(p.charAt(5)=='w')m|=0020;
        c=p.charAt(6); if(c=='x'||c=='s')m|=0010; if(c=='s'||c=='S')m|=02000;
        if(p.charAt(7)=='r')m|=0004; if(p.charAt(8)=='w')m|=0002;
        c=p.charAt(9); if(c=='x'||c=='t')m|=0001; if(c=='t'||c=='T')m|=01000;
        return m;
    }

    private static ph.f type(String permissions){
        if(permissions!=null && permissions.length()>0){
            char c=permissions.charAt(0);
            if(c=='d') return ph.f.X;
            if(c=='l') return ph.f.Y;
            if(c=='-') { ph.f[] all=ph.f.values(); if(all!=null && all.length>0)return all[0]; }
        }
        return ph.f.Z;
    }

    private static ph.e parse(String line){
        if(line==null || !line.startsWith("DWSTAT|")) return null;
        // marker | perms | uid | gid | size | mtimeSeconds | absolutePath
        String[] a=line.split("\\|",7);
        if(a.length<7) return null;
        String perms=a[1]; int uid=num(a[2],-1), gid=num(a[3],-1);
        long size=lng(a[4],0), mtime=lng(a[5],0)*1000L;
        String full=a[6]; String name=new File(full).getName();
        if(name.length()==0) name=full;
        ph.f t=type(perms); boolean dir=perms!=null && perms.length()>0 && perms.charAt(0)=='d';
        db.f owner=new db.f(uid,uid<0?null:String.valueOf(uid));
        db.f group=new db.f(gid,gid<0?null:String.valueOf(gid));
        ph.k mode=new ph.k(owner,group,modeFromPermissions(perms));
        return new ph.e(name,null,t,dir,mode,size,mtime);
    }

    private static ph.o failure(String message){
        return ph.n.k(new IOException(message==null?"Shizuku filesystem operation failed":message));
    }

    public static ph.e[] list(String path) throws ph.o {
        if(!ShizukuBridge.isAuthorized()) throw failure("Shizuku permission is not granted");
        String fmt="DWSTAT|%A|%u|%g|%s|%Y|%n";
        String cmd="/system/bin/toybox find "+q(path)+" -mindepth 1 -maxdepth 1 -exec /system/bin/toybox stat -c "+q(fmt)+" -- '{}' ';'";
        final Result r;
        try { r=run(cmd); } catch(IOException e){ throw ph.n.k(e); }
        ArrayList<ph.e> out=new ArrayList<>();
        String[] lines=r.text.split("\\r?\\n");
        for(String line:lines){ ph.e e=parse(line); if(e!=null)out.add(e); }
        // If stat produced useful children, keep them even if one unusual node made
        // toybox/find return nonzero.  If nothing was usable, surface the failure.
        if(out.isEmpty() && r.rc!=0) throw failure(r.text.trim().length()==0?"Shizuku could not list "+path:r.text.trim());
        return out.toArray(new ph.e[out.size()]);
    }

    public static ph.e stat(String path) throws ph.o {
        if(!ShizukuBridge.isAuthorized()) throw failure("Shizuku permission is not granted");
        String fmt="DWSTAT|%A|%u|%g|%s|%Y|%n";
        final Result r;
        try { r=run("/system/bin/toybox stat -c "+q(fmt)+" -- "+q(path)); }
        catch(IOException e){ throw ph.n.k(e); }
        for(String line:r.text.split("\\r?\\n")){ ph.e e=parse(line); if(e!=null)return e; }
        throw failure(r.text.trim().length()==0?"Shizuku could not stat "+path:r.text.trim());
    }
}
'''
    stubs={
      'dw/filemanager/shizuku/ShizukuBridge.java':r'''package dw.filemanager.shizuku; public final class ShizukuBridge { public static boolean isAuthorized(){return false;} public static java.lang.Process startCommand(String s){return null;} }''',
      'db/f.java':r'''package db; public final class f { public f(int i,String s){} }''',
      'ph/f.java':r'''package ph; public final class f { public static f X,Y,Z; public static f[] values(){return null;} }''',
      'ph/k.java':r'''package ph; public final class k { public k(db.f a,db.f b,int m){} }''',
      'ph/e.java':r'''package ph; public final class e { public e(String n,String l,ph.f t,boolean d,ph.k m,long s,long mt){} }''',
      'ph/o.java':r'''package ph; public final class o extends Exception { public o(){} }''',
      'ph/n.java':r'''package ph; public final class n { public static ph.o k(java.io.IOException e){return null;} }''',
    }

    temp=tempfile.TemporaryDirectory(prefix='dw-shizuku-dir-'); w=Path(temp.name)
    try:
        src=w/'src'; helper=src/'dw/filemanager/shizuku/ShizukuDirectoryLister.java'; helper.parent.mkdir(parents=True); helper.write_text(java)
        for rel,txt in stubs.items():
            p=src/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(txt)
        stubclasses=w/'stubclasses'; classes=w/'classes'; stubclasses.mkdir(); classes.mkdir()
        stubfiles=[str(src/x) for x in stubs]
        run('javac','-source','8','-target','8','-cp',android_jar,'-d',stubclasses,*stubfiles)
        cp=str(android_jar)+os.pathsep+str(stubclasses)
        run('javac','-source','8','-target','8','-cp',cp,'-d',classes,helper)
        dexout=w/'dexout'; dexout.mkdir(); classfiles=[str(p) for p in classes.rglob('*.class')]
        run(d8,'--lib',android_jar,'--classpath',stubclasses,'--output',dexout,*classfiles)
        manifest=w/'AndroidManifest.xml'; manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dw.filemanager.shizukudirprep"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/><application android:theme="@android:style/Theme.Material.NoActionBar"/></manifest>''')
        prep=w/'dir-prep.apk'; run(aapt2,'link','-o',prep,'--manifest',manifest,'-I',android_jar)
        with zipfile.ZipFile(prep,'a',compression=zipfile.ZIP_DEFLATED) as z: z.write(dexout/'classes.dex','classes.dex')
        dec=w/'decoded'; run('java','-jar',apktool,'d','-f',prep,'-o',dec)
        generated=dec/'smali/dw/filemanager/shizuku'
        if not (generated/'ShizukuDirectoryLister.smali').exists(): raise RuntimeError('compiled ShizukuDirectoryLister smali missing')
        dest=sm/'dw/filemanager/shizuku'; dest.mkdir(parents=True,exist_ok=True)
        for p in generated.glob('ShizukuDirectoryLister*.smali'): shutil.copy2(p,dest/p.name)
    finally: temp.cleanup()

    # The historic shell parser is now a genuine fallback only.  A shell session
    # whose process came from Shizuku bypasses BusyBox and the root-era ls parser.
    pn=sm/'ph/n.smali'; nt=pn.read_text()
    sig='.method public static e(Lte/a;Ljava/lang/String;)[Lph/e;'
    s=nt.find(sig); e=nt.find('\n.end method',s)
    if s<0 or e<0: raise RuntimeError('ph/n.e directory-list method missing')
    m=nt[s:e]
    anchor='''    .locals 6\n\n    .line 1\n    invoke-static {p0}, Lph/l;->e(Lph/i;)Lab/n;'''
    replacement='''    .locals 6\n\n    iget-boolean v0, p0, Lph/i;->shizuku:Z\n    if-eqz v0, :dw_legacy_directory_list\n    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->list(Ljava/lang/String;)[Lph/e;\n    move-result-object v0\n    return-object v0\n\n    :dw_legacy_directory_list\n    .line 1\n    invoke-static {p0}, Lph/l;->e(Lph/i;)Lab/n;'''
    if m.count(anchor)!=1: raise RuntimeError('ph/n.e insertion anchor changed')
    m=m.replace(anchor,replacement,1); nt=nt[:s]+m+nt[e:]

    sig='.method public static f(Lte/a;Ljava/lang/String;)Lph/e;'
    s=nt.find(sig); e=nt.find('\n.end method',s)
    if s<0 or e<0: raise RuntimeError('ph/n.f stat method missing')
    m=nt[s:e]
    anchor='''    .locals 3\n\n    .line 1\n    invoke-static {p1}, Lph/r;->v(Ljava/lang/String;)Ljava/lang/String;'''
    replacement='''    .locals 3\n\n    iget-boolean v0, p0, Lph/i;->shizuku:Z\n    if-eqz v0, :dw_legacy_stat\n    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuDirectoryLister;->stat(Ljava/lang/String;)Lph/e;\n    move-result-object v0\n    return-object v0\n\n    :dw_legacy_stat\n    .line 1\n    invoke-static {p1}, Lph/r;->v(Ljava/lang/String;)Ljava/lang/String;'''
    if m.count(anchor)!=1: raise RuntimeError('ph/n.f insertion anchor changed')
    m=m.replace(anchor,replacement,1); nt=nt[:s]+m+nt[e:]
    pn.write_text(nt)

    # Crucial capability fix: once Shizuku is authorized, do not obtain the
    # filesystem shell through the cached legacy root/su SessionManager entry.
    # Build a fresh ShellCatalog connection; ph/i marks it as Shizuku and the
    # native directory engine above handles listings/stats.  Genuine root still
    # follows the exact original cached SessionManager path below.
    sc=sm/'dw/filemanager/dirimpl/shell/ShellCatalog.smali'; st=sc.read_text()
    sig='.method public static l(Landroid/content/Context;)Lhc/f;'
    start=st.find(sig); end=st.find('\n.end method',start)
    if start<0 or end<0: raise RuntimeError('ShellCatalog.l missing')
    old=st[start:end+len('\n.end method')]
    legacy=old.split('\n',2)[2]
    # strip final .end method so it can sit under the :dw_legacy_root_session label
    legacy=legacy.rsplit('\n.end method',1)[0]
    new=r'''.method public static l(Landroid/content/Context;)Lhc/f;
    .locals 3

    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->isAuthorized()Z
    move-result v0
    if-eqz v0, :dw_legacy_root_session

    new-instance v0, Lhc/f;
    sget-object v1, Lph/q;->X1:Lph/q;
    invoke-direct {v0, p0, v1}, Lhc/f;-><init>(Landroid/content/Context;Lph/q;)V
    invoke-virtual {v0}, Lhc/f;->connect()V
    return-object v0

    :dw_legacy_root_session
'''+legacy+r'''
.end method'''
    st=st[:start]+new+st[end+len('\n.end method'):]; sc.write_text(st)

    # ShellCatalog's explicit Shizuku connections are intentionally not pooled by
    # the root SessionManager. Let the normal release call simply disconnect an
    # unmanaged connection instead of dereferencing a null session object.
    sp=sm/'dw/filemanager/xf/connection/SessionManager.smali'; smt=sp.read_text()
    sig='.method public static i(Ljh/a;)V'
    start=smt.find(sig); end=smt.find('\n.end method',start)
    if start<0 or end<0: raise RuntimeError('SessionManager.i missing')
    m=smt[start:end]
    anchor='''    invoke-virtual {p0}, Ljh/a;->getSession()Ljh/d;\n\n    .line 5\n    .line 6\n    .line 7\n    move-result-object v0\n\n    .line 8\n    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;'''
    replacement='''    invoke-virtual {p0}, Ljh/a;->getSession()Ljh/d;\n\n    .line 5\n    .line 6\n    .line 7\n    move-result-object v0\n\n    if-nez v0, :dw_managed_session_release\n    invoke-virtual {p0}, Ljh/a;->disconnect()V\n    return-void\n\n    :dw_managed_session_release\n    .line 8\n    invoke-virtual {v0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;'''
    if m.count(anchor)!=1: raise RuntimeError('SessionManager.i unmanaged anchor changed')
    m=m.replace(anchor,replacement,1); smt=smt[:start]+m+smt[end:]; sp.write_text(smt)

    # Make the settings language reflect the real backend instead of implying
    # Shizuku is merely pretending to be su/root.
    pref=root/'res/xml/pref_root.xml'; ptxt=pref.read_text()
    ptxt=ptxt.replace('Automatic: use Shizuku when available; keep real root/su as fallback',
                      'Shizuku-native filesystem when granted; real root/su is the fallback')
    pref.write_text(ptxt)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode anchor missing')
    y.write_text(yt)

    # Static proof that directory listing is no longer legacy-only.
    finaln=pn.read_text(); finals=sc.read_text(); finalsm=sp.read_text()
    for tok in ('ShizukuDirectoryLister;->list','ShizukuDirectoryLister;->stat','dw_legacy_directory_list'):
        if tok not in finaln: raise RuntimeError('native Shizuku directory hook missing '+tok)
    for tok in ('ShizukuBridge;->isAuthorized','dw_legacy_root_session','Lhc/f;->connect()V'):
        if tok not in finals: raise RuntimeError('ShellCatalog Shizuku capability path missing '+tok)
    if 'dw_managed_session_release' not in finalsm: raise RuntimeError('unmanaged Shizuku release guard missing')
    print('stage21h: directory listing/stat are now first-class Shizuku-native; legacy root BusyBox path retained only as fallback; vc='+VC)

if __name__=='__main__': main()
