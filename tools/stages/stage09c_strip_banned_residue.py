#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def method_span(text, signature_fragment):
    pos=text.index(signature_fragment)
    start=pos if signature_fragment.startswith('.method') else text.rfind('.method',0,pos+1)
    end=text.index('.end method',start)+len('.end method')
    if end < len(text) and text[end]=='\n': end+=1
    return start,end

def remove_method(path, signature_fragment):
    t=path.read_text(); a,b=method_span(t,signature_fragment); path.write_text(t[:a]+t[b:])

def remove_string_resource(root,name):
    for p in (root/'res').glob('values*/strings.xml'):
        t=p.read_text(); nt=re.sub(r'\s*<string\s+name="'+re.escape(name)+r'"(?:\s+[^>]*)?>.*?</string>\s*','\n',t,flags=re.S)
        if nt!=t:p.write_text(nt)
    pub=root/'res/values/public.xml'; t=pub.read_text()
    pub.write_text(re.sub(r'\s*<public type="string" name="'+re.escape(name)+r'" id="0x[0-9a-fA-F]+"\s*/>\s*','\n',t))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    q4=root/'smali/dw/filemanager/runtime/q4.smali'
    if not q4.exists(): raise RuntimeError('q4 billing enum already missing')
    q4.unlink()

    k2=root/'smali/dw/filemanager/runtime/k2.smali'; t=k2.read_text()
    t=t.replace('.field public static final e:Ldw/filemanager/runtime/k2;\n\n','')
    pat=re.compile(r'\n\s*new-instance v0, Ldw/filemanager/runtime/k2;.*?const/4 v1, 0x3.*?sput-object v0, Ldw/filemanager/runtime/k2;->e:Ldw/filemanager/runtime/k2;\n',re.S)
    t,n=pat.subn('\n',t,count=1)
    if n!=1: raise RuntimeError(f'k2 discriminator-3 init removal count={n}')
    if '        :pswitch_4\n' not in t: raise RuntimeError('k2 switch entry missing')
    t=t.replace('        :pswitch_4\n','        :pswitch_8\n',1)
    a=t.index('    :pswitch_4\n'); b=t.index('    :pswitch_5\n',a)
    t=t[:a]+t[b:]
    if 'Ldw/filemanager/runtime/q4;' in t: raise RuntimeError('q4 ref remains in k2')
    k2.write_text(t)

    m3=root/'smali/dw/filemanager/runtime/m3.smali'; t=m3.read_text()
    ms,me=method_span(t,'.method public static a(Ljava/lang/Object;)I')
    method=t[ms:me]; cut=method.index('    :cond_2\n')
    method=method[:cut]+'''    :cond_2
    invoke-virtual {p0}, Ljava/lang/Object;->hashCode()I
    move-result p0
    return p0
.end method'''
    m3.write_text(t[:ms]+method+t[me:])
    if 'Ldw/filemanager/runtime/q4;' in m3.read_text(): raise RuntimeError('q4 ref remains in m3')

    remove_method(root/'smali/e9/b.smali','.method public constructor <init>(Lorg/json/JSONObject;)V')
    remove_method(root/'smali/a7/b.smali','.method public static bridge synthetic r(Landroid/content/Context;Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)V')

    uc=root/'smali/uc/j.smali'; t=uc.read_text()
    a=t.index('    const-string v2, "com.android.vending.BILLING"\n')
    end_marker='    invoke-static {v1, v0, v3, v4, v2}, Luc/j;->b(Ljava/util/HashMap;Ljava/util/HashMap;Ljava/lang/String;I[Ljava/lang/String;)Luc/j;\n'
    b=t.index(end_marker,a)+len(end_marker)
    uc.write_text(t[:a]+t[b:])
    remove_string_resource(root,'synthetic_permission_group_payment')
    remove_string_resource(root,'about_item_time_remaining')

    j5=root/'smali/dw/filemanager/runtime/j5.smali'; t=j5.read_text()
    j5.write_text(t.replace('com.android.billingclient.util.concurrent.AbstractResolvableFuture','dw.filemanager.runtime.AbstractResolvableFuture'))

    comment_rx=re.compile(r'^\s*#.*\b(?:trial|billing|iab|purchase|upgrade|license)\b.*\n?',re.I|re.M)
    changed=0
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            t=p.read_text(errors='ignore'); nt=comment_rx.sub('',t)
            if nt!=t: p.write_text(nt); changed+=1

    bad_terms=['com.android.vending.BILLING','PLAY_BILLING_LIBRARY_BROADCAST','billingPeriod','billingCycleCount','PURCHASES_UPDATED_ACTION','LOCAL_PURCHASES_UPDATED_ACTION','ALTERNATIVE_BILLING_ACTION','about_item_time_remaining','synthetic_permission_group_payment']
    for term in bad_terms:
        hits=[]
        for sd in root.glob('smali*'):
            for p in sd.rglob('*.smali'):
                if term.lower() in p.read_text(errors='ignore').lower(): hits.append(str(p.relative_to(root)))
        for p in (root/'res').rglob('*.xml'):
            if term.lower() in p.read_text(errors='ignore').lower(): hits.append(str(p.relative_to(root)))
        if hits: raise RuntimeError(f'{term} remains: {hits[:8]}')
    wordtrial=re.compile(r'\btrial\b',re.I); hits=[]
    for sd in root.glob('smali*'):
      for p in sd.rglob('*.smali'):
        if wordtrial.search(p.read_text(errors='ignore')): hits.append(str(p.relative_to(root)))
    if hits: raise RuntimeError('whole-word trial remains: '+str(hits[:10]))
    print(f'stage09c stripped final app-owned commerce/state terminology residue; comments cleaned in {changed} files')
if __name__=='__main__': main()
