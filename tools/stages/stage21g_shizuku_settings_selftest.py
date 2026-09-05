#!/usr/bin/env python3
from pathlib import Path
import argparse, os, re, shutil, subprocess, tempfile, zipfile
import xml.etree.ElementTree as ET

VC='9109030'

def run(*args,cwd=None):
    subprocess.run([str(x) for x in args],cwd=cwd,check=True)

def newest(base):
    ds=[p for p in Path(base).iterdir() if p.is_dir()]
    if not ds: raise RuntimeError('no SDK directories in '+str(base))
    def key(p):
        nums=re.findall(r'\d+',p.name)
        return tuple(int(x) for x in nums) if nums else (0,)
    return sorted(ds,key=key)[-1]

def one(text,old,new,label):
    n=text.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected 1 match, found {n}')
    return text.replace(old,new,1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args()
    root=a.decoded; repo=Path.cwd(); sm=root/'smali'

    # Extend the bridge with a cheap server-version query for the status UI.
    bp=sm/'dw/filemanager/shizuku/ShizukuBridge.smali'
    bt=bp.read_text()
    if 'serverVersion()I' not in bt:
        bt=bt.rstrip()+r'''

.method public static serverVersion()I
    .locals 1
    :try_start
    invoke-static {}, Ldw/filemanager/shizuku/ShizukuBridge;->hasBinder()Z
    move-result v0
    if-eqz v0, :none
    invoke-static {}, Lrikka/shizuku/Shizuku;->getVersion()I
    move-result v0
    return v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :none
    :none
    const/4 v0, -0x1
    return v0
.end method
'''
    bp.write_text(bt)

    # Put real Shizuku controls directly into Developer / root settings.
    pref=root/'res/xml/pref_root.xml'
    pt=pref.read_text()
    block='''    <PreferenceCategory android:title="Shizuku" android:key="shizuku_category">\n        <Preference android:title="Access Mode" android:key="shizukuMode" android:summary="Automatic: use Shizuku when available; keep real root/su as fallback" android:selectable="false" />\n        <Preference android:title="Shizuku Status" android:key="shizukuStatus" android:summary="Checking Shizuku server and permission…" android:selectable="false" />\n        <Preference android:title="Request / Refresh Shizuku Permission" android:key="shizukuPermission" android:summary="Grant DW File Manager shell access through Shizuku" />\n        <Preference android:title="Run Shizuku Self-Test" android:key="shizukuSelfTest" android:summary="Test Binder, permission, server UID, shell commands, /data/local/tmp and DW BusyBox" />\n    </PreferenceCategory>\n'''
    anchor='    <PreferenceCategory android:title="@string/pref_category_root_diagnostic" android:key="root_diagnostic_category">'
    if 'android:key="shizuku_category"' not in pt:
        pt=one(pt,anchor,block+anchor,'root preference Shizuku category')
    pref.write_text(pt)

    # Clarify that the old built-in shell result is specifically the legacy su path.
    sp=root/'res/values/strings.xml'; st=sp.read_text()
    st=st.replace('<string name="root_diag_test_result">Root Shell Test</string>',
                  '<string name="root_diag_test_result">Legacy su Root Shell Test</string>')
    st=st.replace('<string name="root_diag_title">Root Diagnostics</string>',
                  '<string name="root_diag_title">Root &amp; Shizuku Diagnostics</string>')
    st=st.replace('<string name="pref_root_diagnostic_summary">Troubleshoot root access issues</string>',
                  '<string name="pref_root_diagnostic_summary">Troubleshoot root and Shizuku access issues</string>')
    st=st.replace('<string name="pref_root_diagnostic_title">Root Access Diagnostics</string>',
                  '<string name="pref_root_diagnostic_title">Root &amp; Shizuku Diagnostics</string>')
    sp.write_text(st)

    android_home=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not android_home: raise RuntimeError('ANDROID_HOME/ANDROID_SDK_ROOT required')
    bt_dir=newest(Path(android_home)/'build-tools'); platform=newest(Path(android_home)/'platforms')
    d8=bt_dir/'d8'; aapt2=bt_dir/'aapt2'; android_jar=platform/'android.jar'; apktool=repo/'apktool.jar'
    for p in (d8,aapt2,android_jar,apktool):
        if not p.exists(): raise RuntimeError('required build tool missing: '+str(p))

    settings_java=r'''package dw.filemanager.shizuku;

import android.app.Activity;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.preference.Preference;
import android.preference.PreferenceActivity;
import android.view.ViewGroup;
import android.widget.Button;

public final class ShizukuSettings {
    private ShizukuSettings() {}

    private static String statusText() {
        boolean binder=ShizukuBridge.hasBinder();
        boolean auth=ShizukuBridge.isAuthorized();
        int uid=ShizukuBridge.serverUid();
        int ver=ShizukuBridge.serverVersion();
        String mode=uid==0?"root/Sui":(uid==2000?"shell/ADB":"uid="+uid);
        if(!binder) return "Server: not connected • Permission: unavailable";
        return "Server: connected (API "+ver+") • Permission: "+(auth?"granted":"not granted")+" • Identity: "+mode;
    }

    public static void refresh(PreferenceActivity a) {
        Preference s=a.findPreference("shizukuStatus");
        if(s!=null) s.setSummary(statusText());
    }

    public static void wire(final PreferenceActivity a) {
        refresh(a);
        Preference perm=a.findPreference("shizukuPermission");
        if(perm!=null) perm.setOnPreferenceClickListener(new Preference.OnPreferenceClickListener(){
            @Override public boolean onPreferenceClick(Preference p){
                ShizukuBridge.ensurePermission(a);
                refresh(a);
                Handler h=new Handler(Looper.getMainLooper());
                h.postDelayed(new Runnable(){ public void run(){ refresh(a); }},500);
                h.postDelayed(new Runnable(){ public void run(){ refresh(a); }},1500);
                return true;
            }
        });
        Preference test=a.findPreference("shizukuSelfTest");
        if(test!=null) test.setOnPreferenceClickListener(new Preference.OnPreferenceClickListener(){
            @Override public boolean onPreferenceClick(Preference p){
                a.startActivity(new Intent(a,ShizukuDiagnosticActivity.class));
                return true;
            }
        });
    }

    public static void addDiagnosticsButton(final Activity a, ViewGroup parent) {
        Button b=new Button(a);
        b.setText("Open Shizuku Diagnostics / Self-Test");
        b.setAllCaps(false);
        int pad=(int)(16*a.getResources().getDisplayMetrics().density+0.5f);
        b.setPadding(pad,pad,pad,pad);
        b.setOnClickListener(v -> a.startActivity(new Intent(a,ShizukuDiagnosticActivity.class)));
        parent.addView(b,new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
    }
}
'''

    diag_java=r'''package dw.filemanager.shizuku;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public final class ShizukuDiagnosticActivity extends Activity {
    private TextView result;
    private Button runButton;

    private int dp(int n){ return (int)(n*getResources().getDisplayMetrics().density+0.5f); }
    private TextView text(String s,float size){ TextView v=new TextView(this); v.setText(s); v.setTextSize(size); v.setPadding(dp(16),dp(10),dp(16),dp(10)); return v; }

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        setTitle("Shizuku Diagnostics");
        ScrollView scroll=new ScrollView(this);
        LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(8),dp(8),dp(8),dp(24));
        scroll.addView(box,new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        TextView title=text("Shizuku Diagnostics",24); title.setTypeface(Typeface.DEFAULT,Typeface.BOLD); box.addView(title);
        TextView intro=text("Built-in DW self-test for the exact Shizuku path used by System browsing. This does not require root.",15); box.addView(intro);
        Button permission=new Button(this); permission.setText("Request / Refresh Shizuku Permission"); permission.setAllCaps(false);
        permission.setOnClickListener(v -> { ShizukuBridge.ensurePermission(this); runSelfTest(); }); box.addView(permission);
        runButton=new Button(this); runButton.setText("Run Self-Test Again"); runButton.setAllCaps(false); runButton.setOnClickListener(v -> runSelfTest()); box.addView(runButton);
        Button copy=new Button(this); copy.setText("Copy Results"); copy.setAllCaps(false); copy.setOnClickListener(v -> {
            ClipboardManager cm=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
            cm.setPrimaryClip(ClipData.newPlainText("DW Shizuku diagnostics",result.getText()));
        }); box.addView(copy);
        result=text("Preparing self-test…",15); result.setTypeface(Typeface.MONOSPACE); result.setTextIsSelectable(true); result.setGravity(Gravity.START); box.addView(result);
        setContentView(scroll);
        runSelfTest();
    }

    private static String q(String s){ return "'"+s.replace("'","'\"'\"'")+"'"; }
    private static byte[] readAll(InputStream in) throws Exception { ByteArrayOutputStream o=new ByteArrayOutputStream(); byte[] b=new byte[8192]; for(int n;(n=in.read(b))>=0;)o.write(b,0,n); return o.toByteArray(); }
    private static String shortText(String s){ s=s==null?"":s.trim(); return s.length()>500?s.substring(0,500)+"…":s; }

    private String command(String cmd){
        Process p=null;
        try{
            p=ShizukuBridge.startCommand(cmd+" 2>&1");
            if(p==null) return "START_FAILED";
            String out=new String(readAll(p.getInputStream()),StandardCharsets.UTF_8);
            int rc=p.waitFor();
            return "rc="+rc+" :: "+shortText(out);
        }catch(Throwable t){ return "EXCEPTION :: "+t.getClass().getSimpleName()+": "+String.valueOf(t.getMessage()); }
        finally { if(p!=null)p.destroy(); }
    }

    private String perform(){
        StringBuilder s=new StringBuilder();
        boolean binder=ShizukuBridge.hasBinder(); boolean auth=ShizukuBridge.isAuthorized(); int uid=ShizukuBridge.serverUid(); int ver=ShizukuBridge.serverVersion();
        s.append("DW SHIZUKU SELF-TEST\n\n");
        s.append("Binder connected: ").append(binder).append('\n');
        s.append("Permission granted: ").append(auth).append('\n');
        s.append("Shizuku API/server version: ").append(ver).append('\n');
        s.append("Server UID: ").append(uid).append(uid==2000?" (ADB shell)":uid==0?" (root/Sui)":"").append("\n\n");
        if(!binder){ s.append("RESULT: FAIL — DW has not received a live Shizuku Binder.\n"); return s.toString(); }
        if(!auth){ s.append("RESULT: FAIL — Shizuku permission is not granted to DW.\n"); return s.toString(); }
        s.append("id: ").append(command("/system/bin/id")).append('\n');
        s.append("shell executable: ").append(command("test -x /system/bin/sh && echo OK")).append('\n');
        s.append("root listing: ").append(command("/system/bin/ls -1 / | /system/bin/toybox wc -l")).append('\n');
        s.append("/data/local/tmp listing: ").append(command("/system/bin/ls -1 /data/local/tmp | /system/bin/toybox wc -l")).append('\n');
        s.append("write/read /data/local/tmp: ").append(command("f=/data/local/tmp/dw-shizuku-selftest-$$; echo DW_SHIZUKU_OK > $f && cat $f && rm -f $f")).append('\n');
        s.append("toybox stat /: ").append(command("/system/bin/toybox stat -c '%A|%s|%Y|%n' -- /")).append('\n');
        try{
            File appBusy=new File(getDir("Exec",0),"busybox");
            String staged=ShizukuBridge.busyboxPath(this,appBusy.getAbsolutePath());
            s.append("DW app BusyBox: ").append(appBusy.getAbsolutePath()).append('\n');
            s.append("Shizuku BusyBox path: ").append(staged).append('\n');
            s.append("BusyBox executable/list: ").append(command("test -x "+q(staged)+" && "+q(staged)+" ls -1 / | /system/bin/toybox head -n 1")).append('\n');
        }catch(Throwable t){ s.append("BusyBox bridge: EXCEPTION :: ").append(t).append('\n'); }
        s.append("\nRESULT: Review each line above. Any START_FAILED / nonzero rc identifies the exact failing Shizuku layer.\n");
        return s.toString();
    }

    private void runSelfTest(){
        runButton.setEnabled(false); result.setText("Running Shizuku self-test…");
        new Thread(new Runnable(){ @Override public void run(){ final String r=perform(); runOnUiThread(new Runnable(){ @Override public void run(){ result.setText(r); runButton.setEnabled(true); }}); }},"DW-Shizuku-SelfTest").start();
    }
}
'''

    stub=r'''package dw.filemanager.shizuku;
import android.content.Context;
public final class ShizukuBridge {
  public static boolean hasBinder(){return false;}
  public static boolean isAuthorized(){return false;}
  public static int serverUid(){return -1;}
  public static int serverVersion(){return -1;}
  public static boolean ensurePermission(Context c){return false;}
  public static java.lang.Process startCommand(String s){return null;}
  public static String busyboxPath(Context c,String p){return p;}
}
'''

    temp=tempfile.TemporaryDirectory(prefix='dw-shizuku-ui-'); w=Path(temp.name)
    try:
        src=w/'src'; pkg=src/'dw/filemanager/shizuku'; pkg.mkdir(parents=True)
        (pkg/'ShizukuSettings.java').write_text(settings_java)
        (pkg/'ShizukuDiagnosticActivity.java').write_text(diag_java)
        (pkg/'ShizukuBridge.java').write_text(stub)
        stubs=w/'stubs'; stubs.mkdir(); classes=w/'classes'; classes.mkdir()
        run('javac','-source','8','-target','8','-cp',android_jar,'-d',stubs,pkg/'ShizukuBridge.java')
        cp=str(android_jar)+os.pathsep+str(stubs)
        run('javac','-source','8','-target','8','-cp',cp,'-d',classes,pkg/'ShizukuSettings.java',pkg/'ShizukuDiagnosticActivity.java')
        dexout=w/'dexout'; dexout.mkdir(); classfiles=[str(p) for p in classes.rglob('*.class')]
        run(d8,'--lib',android_jar,'--classpath',stubs,'--output',dexout,*classfiles)
        manifest=w/'AndroidManifest.xml'; manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="dw.filemanager.shizukuuiprep"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/><application android:theme="@android:style/Theme.Material.NoActionBar"/></manifest>''')
        prep=w/'ui-prep.apk'; run(aapt2,'link','-o',prep,'--manifest',manifest,'-I',android_jar)
        with zipfile.ZipFile(prep,'a',compression=zipfile.ZIP_DEFLATED) as z: z.write(dexout/'classes.dex','classes.dex')
        dec=w/'decoded'; run('java','-jar',apktool,'d','-f',prep,'-o',dec)
        generated=dec/'smali/dw/filemanager/shizuku'
        for name in ('ShizukuSettings.smali','ShizukuDiagnosticActivity.smali'):
            if not (generated/name).exists(): raise RuntimeError('compiled Shizuku UI smali missing '+name)
        for p in generated.glob('ShizukuSettings*.smali'):
            shutil.copy2(p,sm/'dw/filemanager/shizuku'/p.name)
        for p in generated.glob('ShizukuDiagnosticActivity*.smali'):
            shutil.copy2(p,sm/'dw/filemanager/shizuku'/p.name)
    finally:
        temp.cleanup()

    # Wire settings after the original RootPrefActivity has constructed its screen.
    rp=sm/'dw/filemanager/ui/fxsystem/RootPrefActivity.smali'; rt=rp.read_text()
    old='''    :cond_2\n    return-void\n.end method'''
    new='''    :cond_2\n    invoke-static {p0}, Ldw/filemanager/shizuku/ShizukuSettings;->wire(Landroid/preference/PreferenceActivity;)V\n    return-void\n.end method'''
    rt=one(rt,old,new,'RootPrefActivity Shizuku UI wire')
    rp.write_text(rt)

    # Add a visible Shizuku self-test entry directly to the existing Root Diagnostics screen.
    rd=sm/'dw/filemanager/ui/root/RootDiagnosticActivity.smali'; dt=rd.read_text()
    old='''    iget-object v0, p0, Ldw/filemanager/ui/root/RootDiagnosticActivity;->l2:Lgh/l;\n\n    .line 120\n    .line 121\n    invoke-virtual {p1, v0}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V\n\n    .line 122'''
    new='''    iget-object v0, p0, Ldw/filemanager/ui/root/RootDiagnosticActivity;->l2:Lgh/l;\n\n    .line 120\n    .line 121\n    invoke-virtual {p1, v0}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V\n    invoke-static {p0, p1}, Ldw/filemanager/shizuku/ShizukuSettings;->addDiagnosticsButton(Landroid/app/Activity;Landroid/view/ViewGroup;)V\n\n    .line 122'''
    dt=one(dt,old,new,'RootDiagnosticActivity self-test button')
    rd.write_text(dt)

    # Register the private diagnostics activity.
    mp=root/'AndroidManifest.xml'; A='{http://schemas.android.com/apk/res/android}'
    ET.register_namespace('android','http://schemas.android.com/apk/res/android')
    tree=ET.parse(mp); app=tree.getroot().find('application')
    if not any(x.get(A+'name')=='dw.filemanager.shizuku.ShizukuDiagnosticActivity' for x in app.findall('activity')):
        ET.SubElement(app,'activity',{A+'name':'dw.filemanager.shizuku.ShizukuDiagnosticActivity',A+'label':'Shizuku Diagnostics',A+'exported':'false'})
    ET.indent(tree,space='    '); tree.write(mp,encoding='utf-8',xml_declaration=True)

    y=root/'apktool.yml'; yt=y.read_text(); yt,n=re.subn(r'(?m)^\s*versionCode:\s*\d+\s*$',f'  versionCode: {VC}',yt,count=1)
    if n!=1: raise RuntimeError('versionCode anchor missing')
    y.write_text(yt)

    final_pref=pref.read_text(); final_rp=rp.read_text(); final_rd=rd.read_text(); final_manifest=mp.read_text(); final_bridge=bp.read_text()
    for tok in ('shizukuStatus','shizukuPermission','shizukuSelfTest'):
        if tok not in final_pref: raise RuntimeError('Shizuku settings UI missing '+tok)
    for tok in ('ShizukuSettings;->wire','ShizukuSettings;->addDiagnosticsButton'):
        if tok not in final_rp+final_rd: raise RuntimeError('Shizuku settings/diagnostics hook missing '+tok)
    if 'dw.filemanager.shizuku.ShizukuDiagnosticActivity' not in final_manifest: raise RuntimeError('Shizuku diagnostic activity manifest entry missing')
    if 'serverVersion()I' not in final_bridge: raise RuntimeError('Shizuku server version bridge missing')
    print('Stage21g: Shizuku settings section + permission control + built-in self-test + Root Diagnostics entry installed; versionCode',VC)

if __name__=='__main__': main()
