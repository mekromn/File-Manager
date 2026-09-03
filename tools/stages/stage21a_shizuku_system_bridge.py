#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, os, re, shutil, subprocess, tempfile, urllib.request, zipfile
import xml.etree.ElementTree as ET

VC='9109023'
VERSION='13.1.5'
AARS={
    'aidl':'33fe7191cdd69fcb66d649264f3b0c47acb2f3d6343afc05b98dbbff6f221963',
    'shared':'4659642c9339be0a26e9c65bb8648f7ad6d8f4a465f557993ccbc78802381635',
    'api':'4def9bde498ef8626614c2fc5db9af4749c86f16f6c33e3f5658d35e70bab59b',
    'provider':'b0f18cd9812464ec171c53cac93a819fe411718a3965c311f01eb4de265381b3',
}
MIT_LICENSE='''MIT License

Copyright (c) 2021 RikkaW

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

def run(*args, cwd=None):
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def newest_dir(base):
    ds=[p for p in Path(base).iterdir() if p.is_dir()]
    if not ds: raise RuntimeError('no Android SDK directories under '+str(base))
    def ver(p):
        return tuple(int(x) if x.isdigit() else x for x in re.split(r'[.-]',p.name))
    return sorted(ds,key=ver)[-1]

def prepare_official_shizuku_smali(repo_root):
    android_home=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not android_home: raise RuntimeError('ANDROID_HOME/ANDROID_SDK_ROOT is required to prepare pinned Shizuku API')
    apktool=repo_root/'apktool.jar'
    if not apktool.exists(): raise RuntimeError('pinned apktool.jar missing from replay working directory')
    bt=newest_dir(Path(android_home)/'build-tools')
    platform=newest_dir(Path(android_home)/'platforms')
    d8=bt/'d8'; aapt2=bt/'aapt2'; android_jar=platform/'android.jar'
    for p in (d8,aapt2,android_jar):
        if not p.exists(): raise RuntimeError('Android SDK tool missing: '+str(p))

    temp=tempfile.TemporaryDirectory(prefix='dw-shizuku-')
    w=Path(temp.name); jars=[]
    for name,expected in AARS.items():
        aar=w/f'{name}.aar'
        url=f'https://repo1.maven.org/maven2/dev/rikka/shizuku/{name}/{VERSION}/{name}-{VERSION}.aar'
        urllib.request.urlretrieve(url,aar)
        got=sha256(aar)
        if got != expected: raise RuntimeError(f'Shizuku {name} AAR SHA-256 mismatch: {got}')
        x=w/name; x.mkdir()
        with zipfile.ZipFile(aar) as z: z.extractall(x)
        jar=x/'classes.jar'
        if not jar.exists(): raise RuntimeError('classes.jar missing from '+name)
        jars.append(jar)

    dexout=w/'dexout'; dexout.mkdir()
    run(d8,'--lib',android_jar,'--output',dexout,*jars)
    classes=dexout/'classes.dex'
    if not classes.exists(): raise RuntimeError('D8 did not produce Shizuku classes.dex')
    manifest=w/'AndroidManifest.xml'
    manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dw.filemanager.shizukuprep">\n  <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/>\n  <application android:theme="@android:style/Theme.Material.NoActionBar"/>\n</manifest>\n''')
    prep=w/'shizuku-prep.apk'
    run(aapt2,'link','-o',prep,'--manifest',manifest,'-I',android_jar)
    with zipfile.ZipFile(prep,'a',compression=zipfile.ZIP_DEFLATED) as z: z.write(classes,'classes.dex')
    decoded=w/'decoded'; run('java','-jar',apktool,'d','-f',prep,'-o',decoded)
    sm=decoded/'smali'
    if not (sm/'rikka/shizuku/Shizuku.smali').exists(): raise RuntimeError('prepared Shizuku smali missing API class')
    return temp,sm

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; sm=root/'smali'; repo_root=Path.cwd()
    temp,src=prepare_official_shizuku_smali(repo_root)
    try:
        for p in src.rglob('*.smali'):
            rel=p.relative_to(src); q=sm/rel; q.parent.mkdir(parents=True,exist_ok=True)
            if q.exists(): raise RuntimeError('Shizuku class collision: '+str(rel))
            shutil.copy2(p,q)
        sh=sm/'rikka/shizuku/Shizuku.smali'; t=sh.read_text()
        old='.method private static newProcess([Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Lrikka/shizuku/ShizukuRemoteProcess;'
        new='.method public static newProcess([Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Lrikka/shizuku/ShizukuRemoteProcess;'
        if t.count(old)!=1: raise RuntimeError('official Shizuku newProcess signature changed')
        sh.write_text(t.replace(old,new,1))
    finally:
        temp.cleanup()

    bridge=r'''.class public final Ldw/filemanager/shizuku/ShizukuBridge;
.super Ljava/lang/Object;
.source "DWShizukuBridge"

.method public static hasBinder()Z
    .locals 1
    :try_start
    invoke-static {}, Lrikka/shizuku/Shizuku;->pingBinder()Z
    move-result v0
    return v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :fail
    :fail
    const/4 v0, 0x0
    return v0
.end method

.method public static ensurePermission(Landroid/content/Context;)Z
    .locals 4
    :try_start
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->hasBinder()Z
    move-result v0
    if-nez v0, :binder
    const/4 v0, 0x1
    return v0
    :binder
    invoke-static {}, Lrikka/shizuku/Shizuku;->checkSelfPermission()I
    move-result v0
    if-nez v0, :request
    const/4 v0, 0x1
    return v0
    :request
    const/16 v0, 0x4457
    invoke-static {v0}, Lrikka/shizuku/Shizuku;->requestPermission(I)V
    const-string v1, "Grant DW File Manager Shizuku access, then tap System again."
    const/4 v2, 0x1
    invoke-static {p0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v3
    invoke-virtual {v3}, Landroid/widget/Toast;->show()V
    const/4 v0, 0x0
    return v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :fallback
    :fallback
    const/4 v0, 0x1
    return v0
.end method

.method public static startShell(Landroid/content/Context;)Ljava/lang/Process;
    .locals 5
    :try_start
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->hasBinder()Z
    move-result v0
    if-eqz v0, :none
    invoke-static {}, Lrikka/shizuku/Shizuku;->checkSelfPermission()I
    move-result v0
    if-nez v0, :none
    const/4 v0, 0x3
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "sh"
    aput-object v2, v0, v1
    const/4 v1, 0x1
    const-string v2, "-c"
    aput-object v2, v0, v1
    const/4 v1, 0x2
    const-string v2, "exec sh 2>&1"
    aput-object v2, v0, v1
    const/4 v1, 0x0
    invoke-static {v0, v1, v1}, Lrikka/shizuku/Shizuku;->newProcess([Ljava/lang/String;[Ljava/lang/String;Ljava/lang/String;)Lrikka/shizuku/ShizukuRemoteProcess;
    move-result-object v0
    return-object v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :none
    :none
    const/4 v0, 0x0
    return-object v0
.end method

.method public static serverUid()I
    .locals 1
    :try_start
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->hasBinder()Z
    move-result v0
    if-eqz v0, :none
    invoke-static {}, Lrikka/shizuku/Shizuku;->getUid()I
    move-result v0
    return v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :none
    :none
    const/4 v0, -0x1
    return v0
.end method
'''
    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'; bp.parent.mkdir(parents=True,exist_ok=True); bp.write_text(bridge)

    p=sm/'ph/i.smali'; t=p.read_text()
    pat=re.compile(r'\.method public constructor <init>\(Landroid/content/Context;Lph/q;\)V\n.*?\n\.end method',re.S)
    new_ctor=r'''.method public constructor <init>(Landroid/content/Context;Lph/q;)V
    .locals 6
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    const/4 v0, 0x0
    iput-boolean v0, p0, Lph/i;->e:Z
    iput-boolean v0, p0, Lph/i;->f:Z
    iput-object p1, p0, Lph/i;->d:Landroid/content/Context;
    sget-object v0, Lph/i;->g:Ljava/util/concurrent/atomic/AtomicLong;
    invoke-virtual {v0}, Ljava/util/concurrent/atomic/AtomicLong;->incrementAndGet()J

    iget-object v0, p2, Lph/q;->f:Ljava/lang/String;
    const-string v1, "su"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :native_process
    invoke-static {p1}, Ldw/filemanager/shizuku/ShizukuBridge;->startShell(Landroid/content/Context;)Ljava/lang/Process;
    move-result-object v2
    if-eqz v2, :native_process
    iput-object v2, p0, Lph/i;->a:Ljava/lang/Process;
    goto :streams

    :native_process
    iget-boolean v1, p2, Lph/q;->Y:Z
    if-eqz v1, :single
    new-instance v1, Ljava/lang/ProcessBuilder;
    const-string v3, "-mm"
    filled-new-array {v0, v3}, [Ljava/lang/String;
    move-result-object v3
    invoke-direct {v1, v3}, Ljava/lang/ProcessBuilder;-><init>([Ljava/lang/String;)V
    goto :builder
    :single
    new-instance v1, Ljava/lang/ProcessBuilder;
    filled-new-array {v0}, [Ljava/lang/String;
    move-result-object v3
    invoke-direct {v1, v3}, Ljava/lang/ProcessBuilder;-><init>([Ljava/lang/String;)V
    :builder
    const/4 v3, 0x1
    invoke-virtual {v1, v3}, Ljava/lang/ProcessBuilder;->redirectErrorStream(Z)Ljava/lang/ProcessBuilder;
    :try_start_native
    invoke-virtual {v1}, Ljava/lang/ProcessBuilder;->start()Ljava/lang/Process;
    move-result-object v2
    iput-object v2, p0, Lph/i;->a:Ljava/lang/Process;
    :try_end_native
    .catch Ljava/io/IOException; {:try_start_native .. :try_end_native} :io_fail

    :streams
    iget-object v2, p0, Lph/i;->a:Ljava/lang/Process;
    new-instance v0, Ljava/io/BufferedWriter;
    new-instance v1, Ljava/io/OutputStreamWriter;
    invoke-virtual {v2}, Ljava/lang/Process;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v3
    sget-object v4, Ljava/nio/charset/StandardCharsets;->UTF_8:Ljava/nio/charset/Charset;
    invoke-direct {v1, v3, v4}, Ljava/io/OutputStreamWriter;-><init>(Ljava/io/OutputStream;Ljava/nio/charset/Charset;)V
    invoke-direct {v0, v1}, Ljava/io/BufferedWriter;-><init>(Ljava/io/Writer;)V
    iput-object v0, p0, Lph/i;->b:Ljava/io/BufferedWriter;
    new-instance v0, Ljava/io/BufferedReader;
    new-instance v1, Ljava/io/InputStreamReader;
    invoke-virtual {v2}, Ljava/lang/Process;->getInputStream()Ljava/io/InputStream;
    move-result-object v2
    invoke-direct {v1, v2, v4}, Ljava/io/InputStreamReader;-><init>(Ljava/io/InputStream;Ljava/nio/charset/Charset;)V
    invoke-direct {v0, v1}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V
    iput-object v0, p0, Lph/i;->c:Ljava/io/BufferedReader;
    return-void

    :io_fail
    new-instance v0, Lph/h;
    invoke-direct {v0}, Lph/h;-><init>()V
    throw v0
.end method'''
    t,n=pat.subn(new_ctor,t,count=1)
    if n!=1: raise RuntimeError('shell process constructor anchor missing')
    p.write_text(t)

    p=sm/'af/d.smali'; t=p.read_text()
    needle='''    if-ne p1, v2, :cond_5\n\n    .line 82\n    .line 83\n    iget-object p1, v4, Leg/c;->X1:Lbh/a;'''
    repl='''    if-ne p1, v2, :cond_5\n\n    invoke-virtual {v4}, Landroid/view/View;->getContext()Landroid/content/Context;\n    move-result-object v0\n    invoke-static {v0}, Ldw/filemanager/shizuku/ShizukuBridge;->ensurePermission(Landroid/content/Context;)Z\n    move-result v0\n    if-eqz v0, :cond_5\n\n    .line 82\n    .line 83\n    iget-object p1, v4, Leg/c;->X1:Lbh/a;'''
    if t.count(needle)!=1: raise RuntimeError('System root click anchor missing')
    p.write_text(t.replace(needle,repl,1))

    mp=root/'AndroidManifest.xml'; A='{http://schemas.android.com/apk/res/android}'
    ET.register_namespace('android','http://schemas.android.com/apk/res/android')
    tree=ET.parse(mp); mr=tree.getroot(); app=mr.find('application')
    if not any(x.get(A+'name')=='moe.shizuku.manager.permission.API_V23' for x in mr.findall('uses-permission')):
        ET.SubElement(mr,'uses-permission',{A+'name':'moe.shizuku.manager.permission.API_V23'})
    if not any(x.get(A+'name')=='moe.shizuku.client.V3_SUPPORT' for x in app.findall('meta-data')):
        ET.SubElement(app,'meta-data',{A+'name':'moe.shizuku.client.V3_SUPPORT',A+'value':'true'})
    if not any(x.get(A+'name')=='rikka.shizuku.ShizukuProvider' for x in app.findall('provider')):
        ET.SubElement(app,'provider',{
          A+'name':'rikka.shizuku.ShizukuProvider',
          A+'authorities':'com.mekromn.dwfilemanager.shizuku',
          A+'enabled':'true',A+'exported':'true',A+'multiprocess':'false',
          A+'permission':'android.permission.INTERACT_ACROSS_USERS_FULL'
        })
    ET.indent(tree,space='    '); tree.write(mp,encoding='utf-8',xml_declaration=True)

    lic=root/'assets/licenses/shizuku-api-MIT.txt'; lic.parent.mkdir(parents=True,exist_ok=True); lic.write_text(MIT_LICENSE)
    yp=root/'apktool.yml'; yt=yp.read_text(); yt,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,yt,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    yp.write_text(yt)

    mt=mp.read_text(); ph=(sm/'ph/i.smali').read_text(); br=bp.read_text()
    for tok in ('moe.shizuku.manager.permission.API_V23','rikka.shizuku.ShizukuProvider','moe.shizuku.client.V3_SUPPORT'):
        if tok not in mt: raise RuntimeError('Shizuku manifest integration missing '+tok)
    for tok in ('ShizukuBridge;->startShell','new-instance v1, Ljava/lang/ProcessBuilder;'):
        if tok not in ph: raise RuntimeError('Shizuku/su process bridge missing '+tok)
    for tok in ('pingBinder','checkSelfPermission','requestPermission','newProcess','serverUid'):
        if tok not in br: raise RuntimeError('Shizuku bridge missing '+tok)
    print('stage21a integrated pinned Shizuku 13.1.5 into System/root Process backend with original su fallback; vc='+VC)

if __name__=='__main__': main()
